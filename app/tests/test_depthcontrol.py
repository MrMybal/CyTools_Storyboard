"""Depth videos of 3D panels as Fun ControlNet controls, in the workflow and film exports."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


def frames_of(path):
    import imageio_ffmpeg
    reader = imageio_ffmpeg.read_frames(str(path))
    meta = next(reader)
    width, height = meta['size']
    return [np.frombuffer(f, np.uint8).reshape(height, width, 3)[..., 0] for f in reader]


class DepthControlTests(unittest.TestCase):
    def setUp(self):
        from storyboard import depthcontrol, layout, model
        self.dc, self.layout, self.model = depthcontrol, layout, model
        self.tmp = Path(tempfile.mkdtemp(prefix='story depth '))
        board = model.Storyboard.create(self.tmp, 'Depth')
        stage = layout.add_stage(board, 'Hall')
        layout.add_object(board, stage['id'], 'box', 'Wall', position=[0, 1.5, -3], scale=[6, 3, 0.4])
        self.person = layout.add_object(board, stage['id'], 'mannequin', 'Tom')
        self.push = board.add_panel(title='Push in', duration=4)
        layout.set_layout(board, self.push['id'], mode='3d', stage=stage['id'],
                          camera={'position': [0, 1.6, 9], 'target': [0, 1.2, 0], 'fov': 40},
                          cameraEnd={'position': [0, 1.6, 4], 'target': [0, 1.2, 0], 'fov': 40})
        self.still = board.add_panel(title='Still', duration=5)
        layout.set_layout(board, self.still['id'], mode='3d', stage=stage['id'],
                          camera={'position': [3, 1.6, 5], 'target': [0, 1.0, 0], 'fov': 35})
        self.flat = board.add_panel(title='Drawn', duration=4)
        layout.set_layout(board, self.flat['id'], mode='2d', drawing={'items': []})
        self.board, self.stage = board, stage

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_levels(self):
        self.assertIsNone(self.dc.settings({'depthControl': 'off'}))
        self.assertEqual(self.dc.settings({'depthControl': 'indicative'}),
                         {'strength': 0.35, 'start': 0.0, 'end': 0.35, 'blur': 'strong'})
        self.assertEqual(self.dc.settings({'depthControl': 'custom', 'controlStrength': 0.8, 'controlEnd': 0.5,
                                           'controlBlur': 'none'})['strength'], 0.8)
        for bad in ({'depthControl': 'loud'}, {'depthControl': 'custom', 'controlStrength': 0},
                    {'depthControl': 'custom', 'controlBlur': 'soft'}):
            with self.assertRaises(self.model.StoryboardError):
                self.dc.settings(bad)
        middle = self.dc.camera_at(self.push, 0.5)
        self.assertEqual(middle['position'], [0.0, 1.6, 6.5])
        self.assertEqual(self.dc.frame_count(4.0), 107)  # 96 frames asked, 17k + 5 = 107

    def test_video_follows_the_camera_with_one_depth_range(self):
        path = self.dc.write_video(self.board, self.dc.panel_samples(self.push, 107), self.tmp / 'push.mp4',
                                   (320, 180), 'none')
        frames = frames_of(path)
        self.assertEqual(len(frames), 107)
        wall = [float(f[40:60, 150:170].mean()) for f in (frames[0], frames[53], frames[-1])]
        self.assertLess(wall[0], wall[1])
        self.assertLess(wall[1], wall[2], 'the wall gets nearer (whiter) as the camera pushes in, no per-frame rescale')
        self.assertEqual(frames[-1][2, 2], 0, 'sky is far (black)')
        blurred = frames_of(self.dc.write_video(self.board, self.dc.panel_samples(self.push, 22), self.tmp / 'b.mp4',
                                                (320, 180), 'strong'))
        levels = len(np.unique((blurred[5] // 8)))
        sharp_levels = len(np.unique((frames[5] // 8)))
        self.assertLess(levels, sharp_levels, 'strong blur quantises the grey levels')
        with self.assertRaises(self.model.StoryboardError):
            self.dc.write_video(self.board, [(self.flat, 0.0)], self.tmp / 'x.mp4', (64, 36))

    def test_workflow_and_film_controls(self):
        from storyboard import h3film, h3workflow
        target = self.tmp / 'wf'
        result = h3workflow.export_workflow(self.board, target, {'depthControl': 'guided', 'shortEdge': 384,
                                                                     'controlSource': 'depth'})
        document = json.loads((target / 'workflow.json').read_text(encoding='utf-8'))
        steps = {s['id']: s for s in document['steps']}
        control = steps['p01_push_in']['params']['control']
        self.assertEqual({k: control[k] for k in ('preprocess', 'strength', 'start', 'end', 'version')},
                         {'preprocess': 'none', 'strength': 0.6, 'start': 0.0, 'end': 0.6, 'version': '2.0'})
        self.assertEqual(len(frames_of(target / control['video'])), self.dc.frame_count(4.0),
                         'one depth frame per generated frame')
        self.assertIn('control', steps['p02_still']['params'])
        self.assertNotIn('control', steps['p03_drawn']['params'], 'a 2D drawing has no depth')
        self.assertEqual([s['depthControl'] for s in result['shots']], [True, True, False])
        off = h3workflow.build(self.board, {'depthControl': 'off'}, preview=True)[0]
        self.assertFalse(any('control' in s['params'] for s in off['steps']))

        film_dir = self.tmp / 'film'
        exported = h3film.export_film(self.board, film_dir, {'shortEdge': 384, 'controlSource': 'depth'})
        film = json.loads((film_dir / 'film.json').read_text(encoding='utf-8'))
        windows = film['timeline']['segmentConfig']['segments']
        first, second = windows[0]['cytoolsControl'], windows[1]['cytoolsControl']
        self.assertEqual((first['strength'], first['end']), (0.35, 0.35))
        self.assertNotIn('cytoolsControl', windows[2])
        depth = frames_of(film_dir / second['file'])
        self.assertEqual(len(depth), windows[1]['endFrame'] - windows[1]['startFrame'])
        overlap = exported['segments'][1]['overlap']
        push_end = frames_of(film_dir / first['file'])[-1]
        self.assertLess(np.abs(depth[0].astype(int) - push_end.astype(int)).mean(), 25,
                        'the carried frames hold the end of the previous panel')
        self.assertGreater(np.abs(depth[overlap].astype(int) - depth[0].astype(int)).mean(), 5,
                           "then this panel's own camera")


    def test_pose_control(self):
        from storyboard import h3workflow, pose
        # Tom walks 3 m to the right during the push-in, arms raised at the end.
        self.layout.override_object(self.board, self.push['id'], self.person['id'], position=[-1.5, 0, 0],
                                    positionEnd=[1.5, 0, 0], poseEnd='arms raised')
        items = self.dc.characters_at(self.board, self.push, 0.5)
        self.assertEqual(len(items), 1)
        walking = items[0][0]['poseAngles']
        self.assertNotEqual(walking['r_leg'][0], 0.0, 'moving from a standing pose: a walking cycle')
        start, end = (pose.world_joints(i, t) for i, t in (self.dc.characters_at(self.board, self.push, 0.0)[0],
                                                           self.dc.characters_at(self.board, self.push, 1.0)[0]))
        self.assertAlmostEqual(end[1][0] - start[1][0], 3.0, places=5, msg='the neck moved with the character')
        self.assertGreater(end[pose.JOINTS.index('r_wrist')][1], end[pose.JOINTS.index('nose')][1], 'arms raised')
        self.assertEqual(self.dc.source_for(self.board, self.push, {'controlSource': 'auto'}), 'pose')
        self.layout.override_object(self.board, self.still['id'], self.person['id'], hidden=True)
        self.assertEqual(self.dc.source_for(self.board, self.still, {'controlSource': 'auto'}), 'depth')
        video = self.dc.write_video(self.board, self.dc.panel_samples(self.push, 22), self.tmp / 'pose.mp4',
                                    (320, 180), 'strong', 'pose')
        frames = frames_of(video)
        self.assertEqual(len(frames), 22)
        lit = [np.argwhere(f > 60) for f in (frames[0], frames[-1])]
        self.assertTrue(all(len(p) > 50 for p in lit), 'a skeleton is drawn')
        self.assertLess(lit[0][:, 1].mean(), lit[1][:, 1].mean(), 'it moves right across the frame')
        self.assertEqual(int(frames[0][2, 2]), 0, 'black background')
        target = self.tmp / 'wf_pose'
        result = h3workflow.export_workflow(self.board, target, {'shortEdge': 384})
        self.assertEqual([s['controlSource'] for s in result['shots']], ['pose', 'depth', ''])
        steps = json.loads((target / 'workflow.json').read_text(encoding='utf-8'))['steps']
        self.assertTrue(steps[0]['params']['control']['video'].startswith('media/pose_'))
        overlay = frames_of(self.dc.write_video(self.board, self.dc.panel_samples(self.push, 5), self.tmp / 'o.mp4',
                                                (320, 180), 'none', 'overlay'))
        self.assertGreater(len(np.unique(overlay[0])), 20, 'depth greys and skeleton colours together')
        with self.assertRaises(self.model.StoryboardError):
            self.layout.override_object(self.board, self.push['id'], self.person['id'], pose='dancing')


    def test_project_poses_joint_by_joint(self):
        from storyboard import pose, render3d
        waving = self.layout.add_pose(self.board, 'Waving', base='standing',
                                      angles={'r_arm': [20, 150, 60], 'head': [30, 20], 'twist': 15})
        self.assertEqual(waving['angles']['l_arm'], [0.0, 8.0, 5.0, 0.0], 'the other joints come from the base pose')
        self.layout.update_pose(self.board, waving['id'], angles={'lean': 200})
        self.assertEqual(self.layout.find_pose(self.board, 'Waving')['angles']['lean'], 90.0, 'angles are bounded')
        self.layout.update_pose(self.board, waving['id'], angles={'lean': 0})
        with self.assertRaises(self.model.StoryboardError):
            self.layout.update_pose(self.board, waving['id'], angles={'r_arm': [1, 2]})
        with self.assertRaises(self.model.StoryboardError):
            self.layout.add_pose(self.board, 'Bad', angles={'tail': 3})
        library = pose.library_of(self.layout.poses(self.board))
        standing = pose.skeleton(pose.params('standing'))
        custom = pose.skeleton(pose.params(waving['id'], 0.0, library))
        wrist, nose, neck = (pose.JOINTS.index(n) for n in ('r_wrist', 'nose', 'neck'))
        self.assertGreater(custom[wrist][1], standing[wrist][1] + 0.6, 'arm raised sideways, forearm up')
        self.assertGreater(custom[nose][0], standing[nose][0] + 0.02, 'head turned to its left (+X)')
        self.assertGreater(custom[nose][1] - custom[neck][1], standing[nose][1] - standing[neck][1],
                           'and tilted up')
        # Used as the end pose of a moving character: legs walk, arms follow the custom pose.
        self.layout.override_object(self.board, self.push['id'], self.person['id'], positionEnd=[2, 0, 0],
                                    poseEnd=waving['id'])
        item = self.dc.characters_at(self.board, self.push, 1.0)[0][0]
        self.assertAlmostEqual(item['poseAngles']['r_arm'][1], 150.0)
        self.assertNotEqual(item['poseAngles']['r_leg'], (0.0, 0.0, 0.0), 'walking legs while it moves')
        sitting = self.layout.add_pose(self.board, 'On a crate', base='sitting', angles={'seat': 0.7})
        self.assertFalse(pose.upright(sitting['id'], pose.library_of(self.layout.poses(self.board))),
                         'a seated pose does not walk')
        rendered = render3d.renderer().render(self.stage, self.dc.camera_at(self.push, 1.0), (160, 90),
                                              self.push['layout']['overrides'], t=1.0,
                                              poses=self.board.doc['poses'])
        self.assertEqual(rendered['color'].shape, (90, 160, 3))
        self.layout.remove_pose(self.board, waving['id'])
        self.assertNotIn('poseEnd', self.push['layout']['overrides'][self.person['id']])
        with self.assertRaises(self.model.StoryboardError):
            self.layout.override_object(self.board, self.push['id'], self.person['id'], pose=waving['id'])


if __name__ == '__main__':
    unittest.main()

"""Storyboard model, operations through the real runtime, and the three exports."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


def make_image(path, colour, size=(640, 360)):
    from PIL import Image
    Image.new('RGB', size, colour).save(path)
    return path


class ModelTests(unittest.TestCase):
    def setUp(self):
        from storyboard import model
        self.model = model
        self.tmp = Path(tempfile.mkdtemp(prefix='story model é '))
        self.board = model.Storyboard.create(self.tmp, 'Test: film?')
        self.red = make_image(self.tmp / 'red sketch.png', (200, 30, 30))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_project_folder_is_portable(self):
        self.assertTrue(self.board.folder.name.endswith('.cystory'))
        panel = self.board.add_panel(title='Opening', duration=6, images=[{'file': str(self.red), 'role': 'sketch'}])
        relative = panel['images'][0]['file']
        self.assertTrue(relative.startswith('assets/'))
        self.board.save()
        moved = self.tmp / 'elsewhere' / 'copy.cystory'
        shutil.copytree(self.board.folder, moved)
        again = self.model.Storyboard.load(moved)
        self.assertTrue((moved / again.panels()[0]['images'][0]['file']).is_file())
        self.assertEqual(again.doc['assetNames'][Path(relative).name], 'red sketch.png')

    def test_same_image_is_stored_once(self):
        a = self.board.import_asset(self.red)
        b = self.board.import_asset(shutil.copy(self.red, self.tmp / 'again.png'))
        self.assertEqual(a, b)

    def test_panels_move_between_sequences_and_timeline_counts_crossfades(self):
        first = self.board.add_panel(title='A', duration=4)
        second = self.board.add_panel(title='B', duration=6)
        self.board.update_panel(first['id'], transition={'type': 'crossfade', 'duration': 1.0})
        self.assertEqual(self.board.total_duration(), 9.0)
        sequence = self.board.add_sequence('Act 2')
        self.board.move_panel(second['id'], sequence['id'], 0)
        self.assertEqual([p['title'] for p in self.board.sequence(sequence['id'])['panels']], ['B'])
        copy = self.board.duplicate_panel(first['id'])
        self.assertEqual(copy['title'], 'A (copy)')
        self.assertEqual([p['title'] for p in self.board.panels()], ['A', 'A (copy)', 'B'])

    def test_library_references_and_removal(self):
        lea = self.board.add_library_item('character', 'Lea', 'a woman in a red coat', [self.red])
        panel = self.board.add_panel(references=[lea['id']],
                                     prompt={'dialogue': [{'speaker': lea['id'], 'line': 'We are late.'}]})
        with self.assertRaises(self.model.StoryboardError):
            self.board.update_panel(panel['id'], references=['nope'])
        self.board.remove_library_item(lea['id'])
        self.assertEqual(panel['references'], [])
        self.assertEqual(panel['prompt']['dialogue'][0]['speaker'], 'Lea')

    def test_validation_reports_problems(self):
        panel = self.board.add_panel(title='Too long', duration=20, images=[{'file': str(self.red), 'role': 'keyframe', 'time': 30}])
        self.board.add_panel(title='Empty', duration=0.5)
        (self.board.folder / panel['images'][0]['file']).unlink()
        messages = ' | '.join(i['message'] for i in self.board.validate())
        for fragment in ('split into several generations', 'shorter than', 'no image and no description',
                         'missing from the project', 'after the end of the panel'):
            self.assertIn(fragment, messages)

    def test_saves_are_atomic_and_backed_up(self):
        for index in range(8):
            self.board.doc['description'] = str(index)
            self.board.save()
        backups = list((self.board.folder / 'backups').glob('storyboard-*.json'))
        self.assertEqual(len(backups), self.model.BACKUPS)
        self.assertEqual(self.model.Storyboard.load(self.board.folder).doc['description'], '7')

    def test_old_documents_are_migrated(self):
        raw = json.loads((self.board.folder / 'storyboard.json').read_text(encoding='utf-8'))
        raw['sequences'][0]['panels'] = [{'id': 'p1', 'title': 'old', 'duration': 3, 'prompt': {'scene': 'x'}}]
        del raw['settings']['maxSegment']
        (self.board.folder / 'storyboard.json').write_text(json.dumps(raw), encoding='utf-8')
        board = self.model.Storyboard.load(self.board.folder)
        panel = board.panels()[0]
        self.assertEqual(panel['transition']['type'], 'cut')
        self.assertEqual(panel['prompt']['dialogue'], [])
        self.assertEqual(board.doc['settings']['maxSegment'], 15.0)


class OperationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix='story ops '))
        os.environ['CYTOOLS_STORYBOARD_PROJECTS'] = str(cls.tmp / 'projects')
        import importlib
        import tool
        cls.tool = importlib.reload(tool)
        cls.runtime = cls.tool.create_runtime(cls.tmp / 'jobs').start()
        cls.actor = cls.runtime.authenticate(cls.runtime.create_client('tests')['token'])
        cls.session = cls.runtime.create_session(cls.actor, temporary=False)['sessionId']
        cls.images = [make_image(cls.tmp / f'{name}.png', colour)
                      for name, colour in (('a', (200, 60, 60)), ('b', (60, 160, 90)), ('c', (60, 80, 200)))]

    @classmethod
    def tearDownClass(cls):
        cls.runtime.close()
        os.environ.pop('CYTOOLS_STORYBOARD_PROJECTS', None)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def call(self, operation, parameters, timeout=180):
        job = self.runtime.submit(self.actor, self.session, operation, parameters)
        job = self.runtime.wait(self.actor, job['jobId'], timeout=timeout)
        self.assertEqual(job['state'], 'Completed', job.get('error'))
        return job['outputs']

    def test_full_storyboard_and_exports(self):
        created = self.call('create_storyboard', {'title': 'Courtyard', 'aspect': '16:9'})
        project = created['project']
        lea = self.call('add_library_item', {'project': 'Courtyard', 'kind': 'character', 'name': 'Lea',
                                             'description': 'a woman in a red coat', 'files': [str(self.images[0])]})
        lea_id = lea['document']['library'][0]['id']
        out = self.call('add_panel', {'project': project, 'title': 'Arrival', 'duration': 6,
                                      'images': [{'file': str(self.images[0]), 'role': 'sketch'}],
                                      'prompt': {'scene': 'a quiet courtyard at dusk', 'action': 'Lea walks in.',
                                                 'shotSize': 'wide shot', 'cameraMove': 'push in', 'cameraSpeed': 'slow',
                                                 'dialogue': [{'speaker': lea_id, 'line': 'We are late.'}]},
                                      'references': [lea_id], 'transition': {'type': 'crossfade', 'duration': 0.5}})
        first = out['document']['sequences'][0]['panels'][0]['id']
        self.call('add_panel', {'project': project, 'title': 'Close-up', 'duration': 4,
                                'images': [{'file': str(self.images[1]), 'role': 'first'}],
                                'prompt': {'action': 'She looks up.'}})
        self.call('add_panel', {'project': project, 'title': 'No image yet', 'duration': 3,
                                'prompt': {'action': 'The bell rings.'}, 'transition': {'type': 'fade to black', 'duration': 1}})
        self.call('update_panel', {'project': project, 'panel': first, 'prompt': {'sound': 'Rain.'}, 'status': 'ready'})
        described = self.call('describe_storyboard', {'project': project})
        panel = described['document']['sequences'][0]['panels'][0]
        self.assertEqual(panel['prompt']['action'], 'Lea walks in.', 'prompt fields are merged, not replaced')
        self.assertEqual(panel['prompt']['sound'], 'Rain.')
        self.assertAlmostEqual(described['totalDuration'], 12.5)
        listed = self.call('list_storyboards', {})
        self.assertEqual(listed['projects'][0]['title'], 'Courtyard')

        sheet = self.call('export_contact_sheet', {'project': project, 'columns': 2})['file']
        from PIL import Image
        with Image.open(sheet) as image:
            self.assertGreater(image.width, 900)
        page = Path(self.call('export_summary', {'project': project, 'format': 'html'})['file']).read_text(encoding='utf-8')
        self.assertIn('Courtyard', page)
        self.assertIn('We are late.', page)
        self.assertIn('The camera pushes in at slow speed.', page)
        markdown = Path(self.call('export_summary', {'project': project, 'format': 'md'})['file']).read_text(encoding='utf-8')
        self.assertIn('### 1. Arrival - 6.0 s', markdown)
        animatic = self.call('export_animatic', {'project': project}, timeout=300)
        import imageio_ffmpeg
        import subprocess
        info = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-i', animatic['file']], capture_output=True, text=True).stderr
        import re
        h, m, s = re.search(r'Duration: (\d+):(\d+):([\d.]+)', info).groups()
        self.assertAlmostEqual(int(h) * 3600 + int(m) * 60 + float(s), 12.5, delta=0.2)

    def test_layout_operations(self):
        project = self.call('create_storyboard', {'title': 'Staged'})['project']
        panel = self.call('add_panel', {'project': project, 'title': 'Shot', 'duration': 5})['document']
        panel_id = panel['sequences'][0]['panels'][0]['id']
        stage_id = self.call('add_stage', {'project': project, 'name': 'Street'})['document']['stages'][0]['id']
        self.call('update_stage', {'project': project, 'stage': stage_id, 'sky': '#202840'})
        obj = self.tmp / 'pyramid.obj'
        obj.write_text('v 0 0 0\nv 1 0 0\nv 0 0 1\nv 0 1 0\nf 1 2 3\nf 1 2 4\nf 2 3 4\nf 1 3 4\n', encoding='utf-8')
        doc = self.call('add_object', {'project': project, 'stage': stage_id, 'shape': 'mesh', 'mesh': str(obj),
                                       'position': [1, 0, 0]})['document']
        mesh = doc['stages'][0]['objects'][0]
        self.assertEqual(mesh['name'], 'pyramid')
        self.assertTrue((Path(project) / mesh['mesh']).is_file(), 'the mesh is copied into the project')
        doc = self.call('add_object', {'project': project, 'stage': stage_id, 'shape': 'capsule', 'name': 'Tom'})['document']
        tom = doc['stages'][0]['objects'][1]['id']
        self.call('update_object', {'project': project, 'object': tom, 'color': '#3060c0'})
        copy_id = self.call('duplicate_object', {'project': project, 'object': tom})['document']['stages'][0]['objects'][2]['id']
        self.call('remove_object', {'project': project, 'object': copy_id})
        self.call('set_panel_layout', {'project': project, 'panel': panel_id, 'mode': '3d', 'stage': stage_id,
                                       'camera': {'position': [0, 1.6, 6], 'target': [0, 1, 0], 'fov': 40},
                                       'cameraEnd': {'position': [0, 1.6, 3], 'target': [0, 1, -3], 'fov': 40}})
        self.call('override_object', {'project': project, 'panel': panel_id, 'object': tom, 'position': [-1, 0.9, 0]})
        rendered = self.call('render_panel_layout', {'project': project, 'panel': panel_id})
        self.assertTrue(Path(rendered['render']).is_file() and Path(rendered['depth']).is_file())
        # animatic: the 3D panel plays its camera move, then crossfades into a held picture
        self.call('update_panel', {'project': project, 'panel': panel_id,
                                   'transition': {'type': 'crossfade', 'duration': 0.5}})
        self.call('add_panel', {'project': project, 'title': 'Held', 'duration': 2})
        animatic = self.call('export_animatic', {'project': project, 'motion_fps': 6}, timeout=300)
        import imageio_ffmpeg
        import numpy as np
        frames, seconds = imageio_ffmpeg.count_frames_and_secs(animatic['file'])
        self.assertAlmostEqual(seconds, 6.5, delta=0.1)
        reader = imageio_ffmpeg.read_frames(animatic['file'])
        size = next(reader)['size']
        pictures = [np.frombuffer(f, np.uint8) for f in reader]
        self.assertGreater(float(np.abs(pictures[2].astype(int) - pictures[90].astype(int)).mean()), 1.0,
                           'the camera moves during the 3D panel')
        still = self.call('export_animatic', {'project': project, 'motion': False}, timeout=300)
        self.assertAlmostEqual(imageio_ffmpeg.count_frames_and_secs(still['file'])[1], 6.5, delta=0.1)
        self.assertEqual(size[0] % 2, 0)
        move = self.call('suggest_camera_move', {'project': project, 'panel': panel_id, 'apply': True})
        self.assertEqual(move['cameraMove'], 'push in')
        described = self.call('describe_storyboard', {'project': project})
        shot = described['document']['sequences'][0]['panels'][0]
        self.assertEqual(shot['prompt']['cameraMove'], 'push in')
        self.assertEqual(shot['layout']['overrides'][tom]['position'], [-1, 0.9, 0])
        self.call('override_object', {'project': project, 'panel': panel_id, 'object': tom, 'clear': True})
        self.call('set_panel_layout', {'project': project, 'panel': panel_id, 'mode': '2d', 'drawing': {
            'items': [{'type': 'arrow', 'points': [[0.1, 0.5], [0.9, 0.5]]}]}})
        self.assertTrue(Path(self.call('render_panel_layout', {'project': project, 'panel': panel_id})['render']).is_file())
        self.call('remove_stage', {'project': project, 'stage': stage_id})
        job = self.runtime.submit(self.actor, self.session, 'add_object', {'project': project, 'stage': stage_id})
        job = self.runtime.wait(self.actor, job['jobId'], timeout=30)
        self.assertEqual(job['state'], 'Failed')
        self.assertIn('Unknown stage', job['error']['message'])

    def test_errors_are_reported(self):
        job = self.runtime.submit(self.actor, self.session, 'describe_storyboard', {'project': 'does-not-exist'})
        job = self.runtime.wait(self.actor, job['jobId'], timeout=30)
        self.assertEqual(job['state'], 'Failed')
        self.call('create_storyboard', {'title': 'Errors'})
        job = self.runtime.submit(self.actor, self.session, 'update_panel', {'project': 'Errors', 'panel': 'nope'})
        job = self.runtime.wait(self.actor, job['jobId'], timeout=30)
        self.assertEqual(job['state'], 'Failed')
        self.assertIn('Unknown panel', job['error']['message'])


if __name__ == '__main__':
    unittest.main()

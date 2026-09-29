"""Stages, objects, per-panel overrides, 2D/3D renders, and camera moves read from two cameras."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


class LayoutTests(unittest.TestCase):
    def setUp(self):
        from storyboard import layout, model
        self.layout, self.model = layout, model
        self.tmp = Path(tempfile.mkdtemp(prefix='story layout '))
        self.board = model.Storyboard.create(self.tmp, 'Layout')
        self.panel = self.board.add_panel(title='Shot')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def build_stage(self):
        L = self.layout
        stage = L.add_stage(self.board, 'Courtyard')
        wall = L.add_object(self.board, stage['id'], 'box', 'Wall', position=[0, 1.5, -3], scale=[6, 3, 0.4])
        lea = L.add_object(self.board, stage['id'], 'mannequin', 'Lea')
        return stage, wall, lea

    def test_objects_stand_on_the_floor_with_sensible_roles(self):
        stage, wall, lea = self.build_stage()
        self.assertEqual(lea['role'], 'character')
        self.assertEqual(wall['role'], 'set')
        capsule = self.layout.add_object(self.board, stage['id'], 'capsule')
        self.assertAlmostEqual(capsule['position'][1], 0.9)
        self.assertEqual(capsule['scale'], [0.5, 1.8, 0.5])
        copy = self.layout.duplicate_object(self.board, lea['id'])
        self.assertEqual(copy['position'][0], lea['position'][0] + 1)
        with self.assertRaises(self.model.StoryboardError):
            self.layout.add_object(self.board, stage['id'], 'teapot')

    def test_3d_render_becomes_the_panel_picture_with_depth(self):
        from PIL import Image
        stage, wall, lea = self.build_stage()
        self.layout.set_layout(self.board, self.panel['id'], mode='3d', stage=stage['id'],
                               camera={'position': [0, 1.6, 6], 'target': [0, 1.2, 0], 'fov': 40})
        rendered = self.layout.render_panel(self.board, self.panel['id'])
        picture = self.board.folder / rendered['render']
        depth = self.board.folder / rendered['depth']
        with Image.open(picture) as image:
            self.assertEqual(image.size, (1280, 720))
            colours = len(set(image.convert('RGB').resize((64, 36)).get_flattened_data()))
        self.assertGreater(colours, 20)
        with Image.open(depth) as image:
            lo, hi = image.convert('L').getextrema()
        self.assertGreater(hi - lo, 100, 'the depth map has contrast')
        from storyboard import export
        self.assertEqual(export.main_image(self.board, self.panel), picture)
        self.board.save()
        self.assertNotIn(picture, self.board.unused_assets())

    def test_overrides_move_an_object_in_one_panel_only(self):
        stage, wall, lea = self.build_stage()
        other = self.board.add_panel(title='Other')
        self.layout.override_object(self.board, self.panel['id'], lea['id'], position=[2, 0, 1])
        self.layout.override_object(self.board, other['id'], wall['id'], hidden=True)
        from storyboard.render3d import resolved_objects
        mine = {o['id']: o for o in resolved_objects(stage, self.panel['layout']['overrides'])}
        theirs = {o['id']: o for o in resolved_objects(stage, other['layout']['overrides'])}
        self.assertEqual(mine[lea['id']]['position'], [2, 0, 1])
        self.assertEqual(theirs[lea['id']]['position'], lea['position'])
        self.assertNotIn(wall['id'], theirs)
        self.layout.remove_object(self.board, lea['id'])
        self.assertNotIn(lea['id'], self.panel['layout']['overrides'])

    def test_2d_drawing_render(self):
        from PIL import Image
        drawing = {'background': '#ffffff', 'items': [
            {'type': 'rect', 'points': [[0.1, 0.1], [0.4, 0.5]], 'color': '#ff0000', 'fill': True},
            {'type': 'arrow', 'points': [[0.5, 0.8], [0.9, 0.8]], 'color': '#0000ff', 'width': 4},
            {'type': 'figure', 'points': [[0.7, 0.7]], 'color': '#000000', 'size': 0.08},
            {'type': 'stroke', 'points': [[0.1, 0.9], [0.2, 0.85], [0.3, 0.9]], 'color': '#00aa00'},
            {'type': 'text', 'points': [[0.05, 0.02]], 'text': 'Lea', 'color': '#000000'}]}
        self.layout.set_layout(self.board, self.panel['id'], mode='2d', drawing=drawing)
        rendered = self.layout.render_panel(self.board, self.panel['id'])
        with Image.open(self.board.folder / rendered['render']) as image:
            image = image.convert('RGB')
            self.assertEqual(image.getpixel((320, 216)), (255, 0, 0))
            self.assertEqual(image.getpixel((1200, 700)), (255, 255, 255))
        with self.assertRaises(self.model.StoryboardError):
            self.layout.set_layout(self.board, self.panel['id'], drawing={'items': [{'type': 'spiral'}]})

    def test_camera_moves_are_read_from_two_cameras(self):
        start = {'position': [0, 1.6, 8], 'target': [0, 1.2, 0], 'fov': 40}
        cases = {
            'push in': dict(start, position=[0, 1.6, 5], target=[0, 1.2, -3]),
            'truck right': dict(start, position=[3, 1.6, 8], target=[3, 1.2, 0]),
            'pan left': dict(start, target=[-5, 1.2, 1]),
            'zoom in': dict(start, fov=20),
            'arc shot': dict(start, position=[5, 1.6, 6], target=[0, 1.2, 0]),
        }
        self.panel['duration'] = 5
        layout = self.layout.ensure(self.panel)
        layout['camera'] = start
        for expected, end in cases.items():
            layout['cameraEnd'] = end
            with self.subTest(expected):
                self.assertEqual(self.layout.suggest_camera(self.panel)['cameraMove'], expected)
        layout['cameraEnd'] = None
        self.assertEqual(self.layout.suggest_camera(self.panel)['cameraMove'], 'static shot')

    def test_editor_camera_gestures(self):
        """The view and shot cameras orbit, pan and dolly around their target without drifting."""
        from gui.layout_editor import Orbit, orbit_camera
        camera = {'position': [3, 2, 7], 'target': [0, 1, 0], 'fov': 35, 'roll': 5}
        orbit = Orbit()
        orbit.set_from(camera)
        for a, b in zip(orbit.camera()['position'], camera['position']):
            self.assertAlmostEqual(a, b, places=5)
        import numpy as np
        distance = np.linalg.norm(np.subtract(camera['position'], camera['target']))
        turned = orbit_camera(camera, 120, 0)
        self.assertAlmostEqual(np.linalg.norm(np.subtract(turned['position'], turned['target'])), distance, places=5)
        self.assertEqual((turned['fov'], turned['roll']), (35, 5))
        panned = orbit_camera(camera, 50, 0, pan=True)
        self.assertAlmostEqual(np.linalg.norm(np.subtract(panned['position'], panned['target'])), distance, places=5)
        self.assertNotEqual(panned['target'], camera['target'])
        closer = orbit_camera(camera, 0, 0, zoom=2)
        self.assertLess(np.linalg.norm(np.subtract(closer['position'], closer['target'])), distance)

    def test_picking_finds_the_object_under_the_cursor(self):
        from storyboard import render3d
        stage, wall, lea = self.build_stage()
        camera = {'position': [0, 1.6, 6], 'target': [0, 1.2, 0], 'fov': 40}
        index, ids = render3d.renderer().render(stage, camera, (320, 180), want_ids=True)['ids']
        self.assertEqual(ids[index[90, 160]], lea['id'], 'Lea stands in the middle')
        self.assertEqual(ids[index[60, 100]], wall['id'])
        self.assertEqual(index[2, 2], -1, 'sky')

    def test_removing_a_stage_returns_panels_to_image_mode(self):
        stage, _, _ = self.build_stage()
        self.layout.set_layout(self.board, self.panel['id'], mode='3d', stage=stage['id'])
        self.layout.remove_stage(self.board, stage['id'])
        self.assertEqual(self.panel['layout']['mode'], 'image')


if __name__ == '__main__':
    unittest.main()

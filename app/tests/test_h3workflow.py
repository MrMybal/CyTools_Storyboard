"""Storyboard -> CyTools_MiniMaxH3 workflow: durations, parts, frames, chaining, references, prompts.

CyTools_MiniMaxH3's tests/test_storyboard_workflow.py runs an export of the sample project
through that Tool's real workflow runner and bridge.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


def image(path, colour):
    from PIL import Image
    Image.new('RGB', (64, 36), colour).save(path)
    return path


class WorkflowExportTests(unittest.TestCase):
    def setUp(self):
        from storyboard import h3workflow, model
        self.wf, self.model = h3workflow, model
        self.tmp = Path(tempfile.mkdtemp(prefix='story wf '))
        self.board = model.Storyboard.create(self.tmp, 'Robot')
        self.board.doc['settings']['style'] = 'Ultra-realistic science fiction'
        self.robot = self.board.add_library_item('character', 'Unit 7', 'ivory armour',
                                                 [image(self.tmp / 'face.png', (200, 200, 190))])
        self.room = self.board.add_library_item('location', 'Activation room', 'amber strips',
                                                [image(self.tmp / 'room.png', (90, 60, 20))])

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def panel(self, title, duration, refs=(), transition='cut', images=(), prompt=None):
        panel = self.board.add_panel(title=title, duration=duration, references=list(refs),
                                     prompt=prompt or {'action': f'{title} happens'},
                                     images=[dict({'file': str(f), 'role': r}, **extra) for f, r, *more in images
                                             for extra in [more[0] if more else {}]])
        self.board.update_panel(panel['id'], transition={'type': transition, 'duration': 0.5})
        return panel

    def steps(self, document):
        return {s['id']: s for s in document['steps']}

    def test_durations_parts_and_edit(self):
        self.panel('Wake', 2.5, [self.robot['id']], transition='crossfade')
        self.panel('Long walk', 32, [self.robot['id']], transition='fade to black')
        self.panel('End', 6.0)
        document, _, summary, warnings = self.wf.build(self.board)
        steps = self.steps(document)
        wake, walk, end = summary['shots']
        self.assertEqual((wake['generations'], wake['seconds'], wake['trimmed']), (1, 2.5, True))
        self.assertEqual(steps['p01_wake']['params']['duration'], 4.0, 'H3 generates 4 s at least')
        self.assertTrue(any('4 s at least' in w for w in warnings))
        self.assertEqual(walk['generations'], 3, '32 s = 3 chained parts of 10.67 s')
        self.assertEqual(steps['p02_long_walk_2']['params']['first_frame'], '${steps.p02_long_walk_1.lastFrame}')
        self.assertIn('The same shot continues without a cut.', steps['p02_long_walk_3']['params']['prompt'])
        self.assertEqual(steps['p02_long_walk_joined']['params']['videos'][2], '${steps.p02_long_walk_3.video}')
        self.assertEqual(steps['p02_long_walk_cut']['params'], {'video': '${steps.p02_long_walk_joined.video}',
                                                                'start': 0.0, 'end': 32.0})
        film = steps['film']['params']
        self.assertEqual(film['transitions'], [{'type': 'crossfade', 'duration': 0.5},
                                               {'type': 'fade to black', 'duration': 0.5}])
        self.assertEqual(film['videos'][0], '${steps.p01_wake_cut.video}')
        self.assertEqual(document['output'], 'film')
        self.assertAlmostEqual(summary['seconds'], 2.5 + 32 + 6 - 0.5 - 0.5)
        self.assertEqual(steps['p02_long_walk_1']['params']['first_frame'], '${steps.p01_wake_end.image}',
                         'after a crossfade the next shot starts on the trimmed last frame')
        self.assertNotIn('p03_end_end', steps, 'unused frame extractions are dropped')
        self.assertNotIn('p02_long_walk_end', steps, 'no chaining after a fade to black')
        exact = self.wf.build(self.board, {'exactDurations': False, 'shortPanels': 'extend'})[2]['shots']
        self.assertFalse(exact[2]['trimmed'])
        clamp = self.wf.build(self.board, {'longPanels': 'clamp'})[2]['shots'][1]
        self.assertEqual((clamp['generations'], clamp['seconds']), (1, 15.0))
        never = self.steps(self.wf.build(self.board, {'chain': 'never'})[0])
        self.assertNotIn('first_frame', never['p02_long_walk_1']['params'])

    def test_frames_guides_references_and_prompt(self):
        first, last, key = (image(self.tmp / n, c) for n, c in
                            (('first.png', (1, 2, 3)), ('last.png', (4, 5, 6)), ('key.png', (7, 8, 9))))
        sketch = image(self.tmp / 'sketch.png', (10, 20, 30))
        self.panel('Speech', 6, [self.robot['id'], self.room['id']],
                   images=[(first, 'first'), (last, 'last'), (key, 'keyframe', {'time': 2.5}), (sketch, 'sketch')],
                   prompt={'scene': 'the activation room', 'action': 'Unit 7 raises a hand.', 'shotSize': 'close-up',
                           'cameraMove': 'push in', 'sound': 'servos', 'dialogue': [
                               {'speaker': self.robot['id'], 'line': 'I am awake.', 'language': 'English'},
                               {'speaker': 'Narrator', 'line': 'It begins.', 'offScreen': True}]})
        self.panel('Empty', 5, prompt={'action': 'Dust falls.'})
        document, files, summary, _ = self.wf.build(self.board, {'acceleration': 'turbo8', 'referenceAcceleration': 'turbo4'})
        steps = self.steps(document)
        speech = steps['p01_speech']['params']
        self.assertTrue(speech['first_frame'].startswith('media/') and speech['last_frame'].startswith('media/'))
        self.assertEqual(speech['guides'], [{'kind': 'image', 'file': speech['guides'][0]['file'], 'time': 2.5}])
        self.assertEqual(len(speech['references']['images']), 3, 'identity, sketch, location (not the frames)')
        self.assertEqual(speech['acceleration'], 'turbo4')
        self.assertEqual(steps['p02_empty']['params'].get('acceleration'), 'turbo8', 'no references: 8-step turbo')
        prompt = speech['prompt']
        self.assertTrue(prompt.startswith('subject_definitions:\n<Subject 1> is Unit 7, ivory armour, in <Picture 1>.'))
        self.assertIn('[Shot 1] Ultra-realistic science fiction, the activation room.', prompt)
        self.assertIn('<Subject 1> raises a hand.', prompt)
        self.assertIn('The composition follows the sketch <Picture 2>.', prompt)
        self.assertIn('The place is Activation room (amber strips), as in <Picture 3>.', prompt)
        self.assertIn('<Subject 1> (S1) says: <d>[English] I am awake.</d>', prompt)
        self.assertIn('Narrator (S2) says in an off-screen voiceover: <d>[English] It begins.</d> while their lips '
                      'remain completely closed.', prompt)
        self.assertIn('overall_soundscape:\nservos', prompt)
        self.assertTrue(steps['p02_empty']['params']['prompt'].startswith('integrated_multimodal_description: [Shot 1]'))
        self.assertEqual(document['defaults']['seed_policy'], 'increment')
        self.assertTrue(all(name.startswith('media/') for name in files))
        target = self.tmp / 'export'
        result = self.wf.export_workflow(self.board, target)
        written = json.loads((target / 'workflow.json').read_text(encoding='utf-8'))
        self.assertEqual(written['schema'], 'cytools.minimax_h3.workflow/1')
        for step in written['steps']:
            for key in ('first_frame', 'last_frame'):
                value = step['params'].get(key)
                if value and not value.startswith('${'):
                    self.assertTrue((target / value).is_file())
        self.assertEqual(result['file'], str(target / 'workflow.json'))
        for bad in ({'chain': 'x'}, {'acceleration': 'turbo9'}, {'referenceAcceleration': 'turbo8'}, {'nope': 1}):
            with self.assertRaises(self.model.StoryboardError):
                self.wf.build(self.board, bad)

    def test_layout_render_as_first_frame(self):
        from storyboard import layout
        panel = self.panel('Staged', 5)
        layout.set_layout(self.board, panel['id'], mode='2d', drawing={'items': [
            {'type': 'rect', 'points': [[0.1, 0.1], [0.5, 0.5]], 'color': '#ff0000', 'fill': True}]})
        layout.render_panel(self.board, panel['id'])
        as_reference = self.steps(self.wf.build(self.board)[0])['p01_staged']['params']
        self.assertEqual(len(as_reference['references']['images']), 1)
        self.assertIn('follow <Picture 1>, a rough layout', as_reference['prompt'])
        as_first = self.steps(self.wf.build(self.board, {'layoutUse': 'first_frame'})[0])['p01_staged']['params']
        self.assertIn('first_frame', as_first)
        self.assertNotIn('references', as_first)


if __name__ == '__main__':
    unittest.main()

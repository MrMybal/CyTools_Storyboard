"""The window's document logic without a window: undo/redo, autosave, external changes."""
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
sys.path.insert(0, str(Path(__file__).resolve().parent))


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='story editor '))
        os.environ['CYTOOLS_STORYBOARD_PROJECTS'] = str(self.tmp)
        import importlib
        import tool
        importlib.reload(tool)
        import gui.main as main
        self.main = importlib.reload(main)
        self.main.RECENT = self.tmp / 'recent.json'
        import make_sample
        self.project = make_sample.build(self.tmp)
        self.runtime = tool.create_runtime(self.tmp / 'jobs').start()
        sys.argv.append(f'--ui-test-project={self.project}')
        self.editor = self.main.Editor(self.runtime)

    def tearDown(self):
        sys.argv[:] = [a for a in sys.argv if not a.startswith('--ui-test-project=')]
        self.runtime.close()
        os.environ.pop('CYTOOLS_STORYBOARD_PROJECTS', None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def settle(self):
        """Pretend a second went by, then run the per-frame bookkeeping."""
        self.editor.last_change -= 2.0
        self.editor.track()

    def test_edits_are_saved_and_undone(self):
        editor = self.editor
        panel = editor.board.panels()[0]
        panel['title'] = 'Opening'
        editor.track()
        self.assertTrue(editor.dirty)
        self.settle()
        self.assertFalse(editor.dirty)
        from storyboard import model
        self.assertEqual(model.Storyboard.load(self.project).panels()[0]['title'], 'Opening')
        editor.last_change -= 2.0
        panel = editor.board.panels()[0]
        panel['duration'] = 9.0
        editor.track()
        editor.undo_step()
        self.assertEqual(editor.board.panels()[0]['duration'], 6.0)
        self.assertEqual(editor.board.panels()[0]['title'], 'Opening')
        editor.redo_step()
        self.assertEqual(editor.board.panels()[0]['duration'], 9.0)
        editor.undo_step()
        editor.undo_step()
        self.assertEqual(editor.board.panels()[0]['title'], 'Establishing')

    def test_fast_typing_is_one_undo_step(self):
        editor = self.editor
        panel = editor.board.panels()[0]
        editor.last_change -= 2.0
        for text in ('E', 'Es', 'Est', 'Esta'):
            panel['notes'] = text
            editor.track()
        editor.undo_step()
        self.assertEqual(editor.board.panels()[0]['notes'], '')

    def test_changes_from_another_client_are_reloaded(self):
        from storyboard import model
        other = model.Storyboard.load(self.project)
        other.add_panel(title='Added by MCP')
        time.sleep(0.02)
        other.save()
        self.editor.frames = 59
        self.editor.frames += 1
        self.editor.track()
        self.assertIn('Added by MCP', [p['title'] for p in self.editor.board.panels()])

    def test_unsaved_window_edits_are_not_overwritten_by_a_reload(self):
        from storyboard import model
        self.editor.board.panels()[0]['title'] = 'Mine'
        self.editor.track()
        other = model.Storyboard.load(self.project)
        other.add_panel(title='Theirs')
        other.save()
        self.editor.frames = 60
        self.editor.track()
        self.assertEqual(self.editor.board.panels()[0]['title'], 'Mine')


if __name__ == '__main__':
    unittest.main()

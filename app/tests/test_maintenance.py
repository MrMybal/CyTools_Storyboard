"""Update streams with fixtures, on a private copy of the Tool (never on the real folder).

No real GitHub release of this Tool exists: GitHub and Hugging Face answers are simulated,
the archive checks, the activation at start-up and the rollback are the production code.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_in(root, code):
    env = dict(os.environ)
    env.pop('CYTOOLS_H3_DATA', None)
    # Like runtime/bootstrap.py: started from the Tool root, app/ on sys.path.
    code = 'import sys; sys.path.insert(0, %r); ' % str(root / 'app') + code
    result = subprocess.run([PYTHON, '-c', code], cwd=root, capture_output=True, text=True, env=env)
    if result.returncode:
        raise AssertionError(result.stderr[-2000:])
    return result.stdout.strip()


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='h3maint-'))
        shutil.copytree(APP, self.root / 'app', ignore=shutil.ignore_patterns('__pycache__', 'tests', 'Docs'))
        (self.root / 'data' / 'settings').mkdir(parents=True)
        (self.root / 'data' / 'inputs').mkdir()
        (self.root / 'data' / 'inputs' / 'keep.txt').write_text('user data')

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def stage(self, version, abi='cp311-win_amd64', tool_id='cy.tool.storyboard'):
        stage = self.root / 'runtime' / 'updates' / 'tool' / ('x' * 64) / 'unpacked'
        shutil.copytree(self.root / 'app', stage / 'app', ignore=shutil.ignore_patterns('__pycache__'))
        (stage / 'app' / 'release.json').write_text(json.dumps({'version': version, 'runtime_abi': abi}))
        manifest = json.loads((stage / 'app' / 'CyTool.json').read_text(encoding='utf-8'))
        manifest['id'] = tool_id
        (stage / 'app' / 'CyTool.json').write_text(json.dumps(manifest), encoding='utf-8')
        return stage / 'app'

    def test_staged_release_is_activated_then_rolled_back(self):
        current = json.loads((self.root / 'app' / 'release.json').read_text(encoding='utf-8-sig'))['version']
        candidate = self.stage('99.0.0')
        run_in(self.root, 'import maintenance, pathlib; maintenance.verify_staged_app(pathlib.Path(%r))' % str(candidate))
        (self.root / 'data' / 'settings' / 'tool-pending.json').write_text(json.dumps(
            {'app': str(candidate.relative_to(self.root)), 'version': '99.0.0'}))
        self.assertEqual(run_in(self.root, 'import maintenance; print(maintenance.apply_pending())'), 'True')
        self.assertEqual(json.loads((self.root / 'app' / 'release.json').read_text())['version'], '99.0.0')
        self.assertEqual((self.root / 'data' / 'inputs' / 'keep.txt').read_text(), 'user data')
        run_in(self.root, 'import maintenance; maintenance.rollback_tool()')
        self.assertEqual(run_in(self.root, 'import maintenance; print(maintenance.apply_pending())'), 'True')
        self.assertEqual(json.loads((self.root / 'app' / 'release.json').read_text(encoding='utf-8-sig'))['version'], current)
        self.assertEqual(run_in(self.root, 'import maintenance; print(maintenance.apply_pending())'), 'False')

    def test_wrong_identity_or_runtime_is_refused(self):
        for kwargs, fragment in (({'tool_id': 'cy.tool.other'}, 'another Tool'), ({'abi': 'cp312-linux'}, 'another runtime')):
            candidate = self.stage('0.3.0', **kwargs)
            with self.assertRaises(AssertionError) as caught:
                run_in(self.root, 'import maintenance, pathlib; maintenance.verify_staged_app(pathlib.Path(%r))' % str(candidate))
            self.assertIn(fragment, str(caught.exception))
            shutil.rmtree(candidate.parents[1])

    def test_unsafe_archives_are_refused(self):
        sys.path.insert(0, str(APP))
        import maintenance
        cases = {'traversal': ('app/../../evil.txt', 0), 'absolute': ('/etc/evil', 0),
                 'symlink': ('app/link', 0o120777 << 16)}
        for name, (member, attributes) in cases.items():
            archive = self.root / f'{name}.zip'
            with zipfile.ZipFile(archive, 'w') as bundle:
                info = zipfile.ZipInfo(member)
                info.external_attr = attributes
                bundle.writestr(info, 'x')
            with self.subTest(name), self.assertRaises(ValueError):
                maintenance.safe_extract(archive, self.root / f'out-{name}')
            self.assertFalse((self.root / 'evil.txt').exists())


if __name__ == '__main__':
    unittest.main()

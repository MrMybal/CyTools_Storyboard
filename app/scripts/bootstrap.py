"""Stable launcher, deliberately outside the replaceable application directory.

It applies a staged application update before anything imports from app/, then starts
the ImGui window, or the CLI with --cli (e.g. `CyTools_Storyboard.exe --cli describe`).
The source is app/scripts/bootstrap.py; releases and installations copy it to runtime/.
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / 'app'
sys.path.insert(0, str(APP))


def main():
    os.chdir(ROOT)
    logs = ROOT / 'data' / 'logs'
    logs.mkdir(parents=True, exist_ok=True)
    try:
        import maintenance
        if maintenance.apply_pending():
            (logs / 'update.log').write_text('Application updated at start-up.\n', encoding='utf-8')
    except Exception as exc:
        (logs / 'update.log').write_text(f'Update not applied: {exc}\n', encoding='utf-8')
    arguments = sys.argv[1:]
    cli = '--cli' in arguments
    if cli:
        arguments.remove('--cli')
    target = APP / ('tool.py' if cli else 'gui/main.py')
    if os.name == 'nt':
        name = 'python.exe' if cli else 'pythonw.exe'
        python = ROOT / 'runtime/python/Scripts' / name     # virtual environment
        if not python.is_file():
            python = ROOT / 'runtime/python' / name         # portable build (official NuGet Python)
    else:
        python = ROOT / 'runtime/python/bin/python'
    if cli:
        return subprocess.call([str(python), str(target), *arguments], cwd=ROOT)
    with (logs / 'interface.log').open('a', encoding='utf-8') as log:
        return subprocess.call([str(python), str(target), *arguments], cwd=ROOT, stdout=log, stderr=log,
                               creationflags=0x08000000 if os.name == 'nt' else 0)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        if os.name == 'nt':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, 'Start-up failed: ' + str(exc), 'CyTools Storyboard', 16)
        raise

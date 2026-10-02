"""Stable locations of the Tool's app/data/runtime folders. No side effects on import."""
from pathlib import Path
import sys

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
DATA = ROOT / 'data'
RUNTIME = ROOT / 'runtime'

MODELS = DATA / 'models'
SETTINGS = DATA / 'settings'
LOGS = DATA / 'logs'
ENGINES = RUNTIME / 'engines'
SOURCES = RUNTIME / 'sources'


def base_python():
    """Interpreter of the light application environment (runtime/python)."""
    if sys.platform == 'win32':
        candidates = (RUNTIME / 'python' / 'Scripts' / 'python.exe', RUNTIME / 'python' / 'python.exe')   # venv, or portable build
    else:
        candidates = (RUNTIME / 'python' / 'bin' / 'python',)
    return next((c for c in candidates if c.exists()), Path(sys.executable))

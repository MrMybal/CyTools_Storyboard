"""Application updates of CyTools_Storyboard (GitHub releases), staged and reversible.

This Tool has no engine and no model weights, so it has one update stream: the application
itself. The rules are the same as in the other CyTools: a verified release is staged in
runtime/updates, activated at the next start by runtime/bootstrap.py, data/ is never
touched, and the previous version can be restored.

Former header of the shared design, kept for reference:

* application - this Tool, from GitHub releases of a repository the user configures;
  staged in runtime/updates, verified (identity, runtime ABI, entry points, SHA-256,
  archive confinement), activated at the next start by runtime/bootstrap.py under the
  runtime lock, previous version kept for rollback. data/ is never part of it.
* engine      - the ComfyUI release the Colab bridge installs. Pinned in setup.py; a
  newer tag can be staged (resolved to its commit), which goes into the next exported
  notebook. The bridge re-checks every node and input the Tool uses against the new
  engine at start-up (health.engineCheck) before anything is generated.
* weights     - the Hugging Face revision of Comfy-Org/MiniMax-H3. Pinned in catalog.py;
  a newer revision can be staged with its sizes and SHA-256 fetched from the Hub, and
  the bridge then verifies every downloaded file against them.
"""
import json
import re
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

APP = Path(__file__).resolve().parent
ROOT = APP.parent
import sys  # noqa: E402
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))
SETTINGS = ROOT / 'data' / 'settings'

RUNTIME = ROOT / 'runtime'
UPDATES = RUNTIME / 'updates'
TOOL_ID = 'cy.tool.storyboard'
USER_AGENT = 'CyTools-Storyboard-Updater'
MAX_APP_ARCHIVE_BYTES = 256 * 1024 ** 2


def read_json(path, fallback=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (OSError, ValueError):
        return {} if fallback is None else fallback


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding='utf-8')
    temporary.replace(path)


def fetch_json(url):
    request = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError('Not found (HTTP 404): check the repository or revision.') from None
        if exc.code in (401, 403):
            raise RuntimeError('Access refused or API quota reached (HTTP %d).' % exc.code) from None
        raise RuntimeError(f'HTTP {exc.code}') from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f'Network unavailable: {exc.reason}') from None


def repository(value):
    value = (value or '').strip().removeprefix('https://github.com/').removesuffix('.git').rstrip('/')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*/[A-Za-z0-9_.-]+', value) or value.split('/')[-1] in ('.', '..'):
        raise ValueError('Use a GitHub repository written owner/name.')
    return value


def settings():
    value = read_json(SETTINGS / 'updates.json')
    value.setdefault('tool_repository', '')
    value.setdefault('auto_check', False)
    return value


def save_settings(value):
    write_json(SETTINGS / 'updates.json', value)


def ensure_idle():
    """Never swap the application while another instance owns the runtime (and its jobs)."""
    from cytools_core import CyToolError
    from cytools_core.storage import RuntimeLock
    jobs = ROOT / 'data' / 'jobs'
    jobs.mkdir(parents=True, exist_ok=True)
    try:
        RuntimeLock(jobs / 'runtime.lock.sqlite3').close()
    except CyToolError:
        raise RuntimeError('CyTools_Storyboard is already running: close it before an update is applied.') from None


# ------------------------------------------------------------------ application
def local_release():
    return read_json(APP / 'release.json', {'version': '0.0.0', 'runtime_abi': 'cp311-win_amd64'})


def check_tool():
    repo = repository(settings()['tool_repository'])
    release = fetch_json(f'https://api.github.com/repos/{repo}/releases/latest')
    local = local_release().get('version', '0.0.0')
    state = {'repository': repo, 'version': release['tag_name'], 'installed': local, 'url': release['html_url'],
             'assets': [{'name': a['name'], 'url': a['browser_download_url'], 'size': a['size']}
                        for a in release.get('assets', [])],
             'update_available': release['tag_name'].lstrip('v') != local.lstrip('v'),
             'checkedAt': time.strftime('%Y-%m-%dT%H:%M:%S')}
    write_json(SETTINGS / 'tool-update.json', state)
    return state


def safe_extract(archive, destination):
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        if sum(info.file_size for info in bundle.infolist()) > MAX_APP_ARCHIVE_BYTES:
            raise ValueError('Application archive too large.')
        for info in bundle.infolist():
            name = info.filename
            if name.startswith('/') or '\\' in name or '..' in Path(name).parts or Path(name).is_absolute():
                raise ValueError('Archive path refused: ' + name)
            if not (destination / name).resolve().is_relative_to(destination.resolve()):
                raise ValueError('Archive path refused: ' + name)
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Symbolic links are refused: ' + name)
        bundle.extractall(destination)
    return destination


def verify_staged_app(candidate):
    from cytools_core import load_manifest
    manifest = load_manifest(candidate / 'CyTool.json')
    if manifest['id'] != TOOL_ID:
        raise ValueError('The release is for another Tool.')
    release = read_json(candidate / 'release.json')
    if release.get('runtime_abi') != local_release().get('runtime_abi'):
        raise ValueError('This release needs another runtime: a full installation is required.')
    for required in ('tool.py', 'gui/main.py', 'storyboard/model.py'):
        if not (candidate / required).is_file():
            raise ValueError(f'{required} is missing from the release.')
    return manifest, release


def fetch_tool(progress=lambda done, total: None, cancelled=lambda: False):
    import hashlib
    state = check_tool()
    if not state['update_available']:
        return {'staged': False, 'message': 'The application is up to date.'}
    assets = {a['name']: a for a in state['assets']}
    name = 'cytools-app.zip'
    if name not in assets or name + '.sha256' not in assets:
        raise RuntimeError('The release must provide cytools-app.zip and cytools-app.zip.sha256 (see app/UPDATES.md).')
    prefix = f'https://github.com/{state["repository"]}/releases/download/'
    for asset in (assets[name], assets[name + '.sha256']):
        if not asset['url'].startswith(prefix):
            raise ValueError('Unexpected asset URL.')
    with urllib.request.urlopen(urllib.request.Request(assets[name + '.sha256']['url'],
                                                       headers={'User-Agent': USER_AGENT}), timeout=30) as response:
        digest = response.read(1024).decode('ascii').split()[0].lower()
    if not re.fullmatch('[a-f0-9]{64}', digest):
        raise ValueError('Invalid release checksum.')
    stage = UPDATES / 'tool' / digest
    stage.mkdir(parents=True, exist_ok=True)
    archive = stage / name
    hasher, done = hashlib.sha256(), 0
    with urllib.request.urlopen(urllib.request.Request(assets[name]['url'], headers={'User-Agent': USER_AGENT}),
                                timeout=60) as response, open(archive, 'wb') as handle:
        while True:
            if cancelled():
                raise RuntimeError('Cancelled.')
            block = response.read(1024 * 1024)
            if not block:
                break
            handle.write(block)
            hasher.update(block)
            done += len(block)
            progress(done, assets[name]['size'])
    if hasher.hexdigest() != digest:
        archive.unlink(missing_ok=True)
        raise ValueError('The downloaded archive does not match its published SHA-256.')
    safe_extract(archive, stage / 'unpacked')
    candidate = stage / 'unpacked' / 'app'
    verify_staged_app(candidate)
    write_json(SETTINGS / 'tool-pending.json', {'app': str(candidate.relative_to(ROOT)), 'version': state['version']})
    return {'staged': True, 'message': f'Version {state["version"]} verified; it will be activated at the next start.'}


def apply_pending():
    """Called by runtime/bootstrap.py before the application is imported."""
    pending = read_json(SETTINGS / 'tool-pending.json')
    if not pending:
        return False
    ensure_idle()
    source = (ROOT / pending['app']).resolve()
    if not source.is_relative_to(UPDATES.resolve()) or not (source / 'CyTool.json').is_file():
        raise ValueError('Invalid staged application.')
    verify_staged_app(source)
    backup = UPDATES / 'tool' / ('previous-' + str(time.time_ns()))
    backup.parent.mkdir(parents=True, exist_ok=True)
    import os
    if Path.cwd().resolve().is_relative_to(APP.resolve()):
        os.chdir(ROOT)  # Windows cannot rename the current directory of a process
    APP.rename(backup)
    try:
        source.rename(APP)
    except Exception:
        backup.rename(APP)
        raise
    write_json(SETTINGS / 'tool-previous.json', {'app': str(backup.relative_to(ROOT)),
                                                 'version': read_json(backup / 'release.json').get('version', '')})
    (SETTINGS / 'tool-pending.json').unlink(missing_ok=True)
    return True


def rollback_tool():
    previous = read_json(SETTINGS / 'tool-previous.json')
    if not previous:
        raise RuntimeError('No previous application to restore.')
    write_json(SETTINGS / 'tool-pending.json', previous)
    return {'message': 'The previous version will be restored at the next start.'}

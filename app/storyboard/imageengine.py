"""The image engine as seen by the Tool: one persistent worker that keeps the model loaded.

The application never imports torch. `ImageEngine` starts `workers/image_worker.py` with the
interpreter of the engine environment (runtime/engines/image); that worker owns a private
ComfyUI (runtime/sources/ComfyUI) and renders the graphs of storyboard/comfy_image_workflow.py,
one API prompt per picture. It stays alive between jobs with its model in memory, for
`keepLoadedMinutes` after the last picture (0: until the application closes or `unload`).
Cancelling a job interrupts ComfyUI at its next step and keeps the model. With the `server`
option the same prompts are sent to another ComfyUI (a Colab tunnel) instead.

Tests replace the worker through CYTOOLS_STORYBOARD_IMAGE_WORKER (a script run with the base
interpreter), so the whole chain is exercised without weights.
"""
import os
import threading
import time
from pathlib import Path

from cytools_core import CyToolError

from . import engines, imagemodels
from .paths import APP, DATA, LOGS, ROOT, RUNTIME, base_python
from .workerhost import WorkerHost

ENGINE = 'image'
KINDS = ('edit', 'text')     # edit: pictures from reference pictures; text: pictures from a prompt alone


def fake_worker():
    return os.environ.get('CYTOOLS_STORYBOARD_IMAGE_WORKER', '')


def lora_folder():
    """Where the user's LoRA files live: the loras folder of the shared model directory."""
    return imagemodels.MODELS / 'comfyui' / 'loras'


def lora_files():
    """LoRA files the user can switch on (the few-step LoRAs the catalogue installs for its own models are
    applied by fast mode and are not listed)."""
    managed = {Path(entry['path']).name for model in imagemodels.catalog().values() for entry in model['files']
               if entry.get('role') == 'lora'}
    folder = lora_folder()
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if p.suffix.lower() == '.safetensors' and p.name not in managed)


def check_loras(options):
    """On the private engine every LoRA switched on must be in the folder (another server has its own)."""
    from .imagegen import active_loras
    if (options.get('server') or '').strip() or fake_worker():
        return
    missing = [name for name, _ in active_loras(options) if not (lora_folder() / name).is_file()]
    if missing:
        raise CyToolError('MissingModel', 'LoRA file(s) not found in ' + str(lora_folder()) + ': ' + ', '.join(missing),
                          recoverable=True, details={'files': missing})


def is_installed(model):
    return bool(fake_worker()) or not imagemodels.missing_files(model)


def resolve_model(kind, wanted='', installed=True):
    """The catalogue entry used for `kind`: the one asked for, else the default installed one
    (with installed=False: the default one even when nothing is installed, for previews and
    exported workflows)."""
    if wanted:
        try:
            model = imagemodels.get(wanted)
        except KeyError:
            raise CyToolError('InvalidParameters', f'Unknown image model {wanted!r}.') from None
        if kind not in model.get('kinds', []):
            raise CyToolError('InvalidParameters', f'{model["name"]} cannot do "{kind}" generation.')
        if installed and not fake_worker():
            imagemodels.require_installed(wanted)
        return model
    candidates = [m for m in imagemodels.catalog().values() if kind in m.get('kinds', [])]
    candidates.sort(key=lambda m: (not m.get('default'), m['id']))
    for model in candidates:
        if is_installed(model):
            return model
    if candidates and not installed:
        return candidates[0]
    names = ', '.join(m['name'] for m in candidates) or 'none declared'
    raise CyToolError('MissingModel', f'No image model is installed for "{kind}" generation ({names}). Install one '
                      'from the Images tab > Installation.', recoverable=True, details={'kind': kind})


def control_model(model, server=''):
    """The ControlNet entry of a model when it can be used: installed here, or assumed present on
    another server. None when the model has none or it is not installed."""
    if not model.get('control'):
        return None
    try:
        patch = imagemodels.get(model['control'])
    except KeyError:
        return None
    return patch if server or is_installed(patch) else None


def describe(model, server=''):
    """What the graph builder and the worker need: family, file names by role (with the model's
    ControlNet as 'patch' when it is usable), defaults."""
    files = {role: Path(path).name for role, path in model['roles'].items()}
    patch = control_model(model, server)
    if patch is not None:
        files['patch'] = Path(patch['roles']['patch']).name
    return {'id': model['id'], 'name': model['name'], 'loader': model['loader'], 'license': model.get('license', {}),
            'defaults': model.get('defaults', {}), 'files_by_role': files}


def control_available(options):
    """Whether the model that renders pictures from references can take a control picture now."""
    try:
        model = resolve_model('edit', options.get('model', ''), installed=False)
    except CyToolError:
        return False
    return control_model(model, (options.get('server') or '').strip()) is not None


def render_controls(board, requests, folder):
    """Render the control picture (depth, pose) of every request that asks for one, at the size
    of its picture; sets request['control']['file']."""
    from . import depthcontrol
    done = {}
    for request in requests:
        control = request.get('control')
        if not control or control.get('file'):
            continue
        if board is None:
            raise CyToolError('InvalidParameters', 'A control picture needs the project of its shot.')
        key = (control['panel'], control['source'], control['blur'], request['width'], request['height'])
        if key not in done:
            _, _, panel = board.find(control['panel'])
            target = Path(folder) / f'control_{control["panel"]}_{control["source"]}_{request["width"]}x{request["height"]}.png'
            done[key] = str(depthcontrol.write_picture(board, panel, target, (request['width'], request['height']),
                                                       control['source'], control['blur']))
        control['file'] = done[key]


def reference_rules(options):
    """(most reference pictures, how the prompt names picture n) of the model that will render
    pictures from references, installed or not."""
    try:
        model = resolve_model('edit', options.get('model', ''), installed=False)
    except CyToolError:
        return 3, 'image {n}'
    defaults = model.get('defaults', {})
    return int(defaults.get('maxReferences', 3)), defaults.get('referenceToken', 'image {n}')


class ImageEngine:
    def __init__(self, runtime=None):
        self.runtime = runtime
        self.host = None
        self.lock = threading.RLock()
        self.last = {}     # last engine report (model, device, seconds per picture)

    def _host(self, private=True):
        with self.lock:
            if not fake_worker():
                # The worker only needs the engine's interpreter; its private server also needs ComfyUI.
                info = engines.status(ENGINE)
                if not info['pythonExists'] or (private and not info['installed']):
                    raise CyToolError('MissingDependency', 'The image engine is not installed. Install it from the Images '
                                      'tab > Installation.', recoverable=True, details={'engine': ENGINE, 'state': info['state']})
            if self.host is None:
                fake = fake_worker()
                if fake:
                    command, env = [str(base_python()), fake], engines.base_environment()
                else:
                    command = [str(engines.engine_python(ENGINE)), str(APP / 'workers' / 'image_worker.py')]
                    env = engines.worker_environment(ENGINE)
                self.host = WorkerHost('image', command, cwd=APP, env=env, log_path=LOGS / 'image-worker.log',
                                       idle_seconds=1800, startup_timeout=120)
                if self.runtime is not None:
                    try:
                        self.runtime.register_worker('worker-image', self.host)
                    except Exception:
                        pass
            return self.host

    def status(self):
        with self.lock:
            health = self.host.health() if self.host else {'state': 'Stopped', 'alive': False, 'resident': {}}
        return {'worker': {k: health.get(k) for k in ('state', 'alive', 'resident')}, 'last': dict(self.last)}

    def unload(self):
        with self.lock:
            if self.host is not None:
                self.host.stop()
        return self.status()

    def generate(self, context, requests, options, folder, board=None):
        """Render `requests` into `folder`; returns [{request fields..., 'file', 'seconds', 'engine'}] in order."""
        from . import comfy_image_workflow as graphs
        if not requests:
            return []
        server = (options.get('server') or '').strip()
        check_loras(options)
        host = self._host(private=not server)
        host.idle_seconds = int(options['keepLoadedMinutes']) * 60
        batches = {}
        for request in requests:
            batches.setdefault(request['mode'], []).append(request)
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        render_controls(board, requests, folder / 'controls')
        done, results = 0, {}
        for kind in KINDS:     # pictures from references first: one model load per kind at most
            batch = batches.get(kind)
            if not batch:
                continue
            model = resolve_model(kind, options['model'] if kind == 'edit' else options['textModel'],
                                  installed=not server)
            entry = describe(model, server)
            jobs = []
            for request in batch:
                files = list(request['references']) + ([request['control']['file']] if graphs.controlled(request, entry) else [])
                names = {path: graphs.reference_name(path) for path in files}
                workflow = graphs.build([request], entry, options, names, prefix='cytools_storyboard/picture')
                document = workflow.document()
                save = next(iter(graphs.save_nodes(document)))
                name = f'{request["key"]}_{request["variant"]:02d}_{request["seed"]}_{request["id"]}.png'
                jobs.append({'id': request['id'], 'label': request['label'], 'prompt': graphs.api_prompt(document),
                             'references': names, 'saveNode': save, 'file': str(folder / name)})
            cancel_file = folder / f'.cancel-{time.monotonic_ns()}'
            payload = {'model': entry, 'jobs': jobs, 'cancelFile': str(cancel_file), 'server': server,
                       'referenceFolder': graphs.REFERENCE_FOLDER,
                       'engine': {'comfy': str(engines.source_path('ComfyUI')), 'models': str(imagemodels.directory(model)),
                                  'data': str(DATA / 'imageengine'), 'log': str(LOGS / 'image-comfyui.log')}}
            try:
                answer = host.run_job(context, 'generate', payload, progress_offset=100.0 * done / len(requests),
                                      progress_scale=len(batch) / len(requests), cancel_file=cancel_file)
            finally:
                cancel_file.unlink(missing_ok=True)
            done += len(batch)
            settings = graphs.settings_for(entry, options, kind)
            self.last = {'model': model['id'], 'steps': settings['steps'], 'guidance': settings['guidance'],
                         'fast': settings['fast'],
                         **{k: answer.get(k) for k in ('device', 'secondsPerPicture', 'firstPictureSeconds', 'startSeconds',
                                                       'int8Kernels', 'server', 'comfyui', 'torch')}}
            for item in answer['pictures']:
                results[item['id']] = dict(item, engine=dict(self.last))
        return [dict(request, file=results[request['id']]['file'], seconds=results[request['id']].get('seconds'),
                     engine=results[request['id']]['engine'])
                for request in requests if request['id'] in results]

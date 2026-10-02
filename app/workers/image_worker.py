"""Image engine worker: owns the application's private ComfyUI and renders API prompts on it.

Started by storyboard/imageengine.py with the interpreter of the engine environment, it speaks
the JSON-lines protocol of storyboard/workerhost.py and stays alive between jobs. The first
`generate` starts ComfyUI (runtime/sources/ComfyUI, pinned) as a child process listening on
127.0.0.1 only, with no custom node and no API node, reading the models of data/models/comfyui
through an extra_model_paths file. ComfyUI keeps the model loaded between prompts, so the
second picture starts at once; `unload` frees it without stopping the process.

With a `server` address in the request, the same prompts go to that ComfyUI instead (a Colab
tunnel, another machine): reference pictures are uploaded, results downloaded.

Nothing is printed on stdout except the protocol; ComfyUI's own output goes to a log file.
"""
import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workers._protocol import WorkerError, serve  # noqa: E402

STATE = {'process': None, 'url': '', 'key': None, 'log': None, 'uploaded': set(), 'client': uuid.uuid4().hex,
         'model': None, 'external': False}
MODEL_INPUTS = ('unet_name', 'clip_name', 'vae_name', 'lora_name', 'name')


# ---------------------------------------------------------------------------- http
def call(path, body=None, timeout=60, raw=False, headers=None):
    data = None
    request_headers = dict(headers or {})
    if body is not None and not isinstance(body, bytes):
        data = json.dumps(body).encode('utf-8')
        request_headers['Content-Type'] = 'application/json'
    elif body is not None:
        data = body
    request = urllib.request.Request(STATE['url'] + path, data=data, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except urllib.error.HTTPError as error:
        payload = error.read()
        if raw:
            raise WorkerError('InferenceFailed', f'ComfyUI answered {error.code} on {path}') from None
        try:
            return json.loads(payload or b'{}')
        except ValueError:
            raise WorkerError('InferenceFailed', f'ComfyUI answered {error.code} on {path}: {payload[:300]!r}') from None
    if raw:
        return payload
    return json.loads(payload) if payload else {}


def upload(path, name, folder):
    boundary = uuid.uuid4().hex
    content = Path(path).read_bytes()
    parts = []
    for field, value in (('subfolder', folder), ('type', 'input'), ('overwrite', 'true')):
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{name}"\r\n'
                 f'Content-Type: application/octet-stream\r\n\r\n'.encode() + content + b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode())
    answer = call('/upload/image', b''.join(parts), timeout=300,
                  headers={'Content-Type': f'multipart/form-data; boundary={boundary}'})
    if answer.get('name') != name:
        raise WorkerError('InferenceFailed', f'ComfyUI did not store {name}: {answer}')


# ---------------------------------------------------------------------------- private ComfyUI
def free_port():
    with socket.socket() as handle:
        handle.bind(('127.0.0.1', 0))
        return handle.getsockname()[1]


def stop_server():
    process = STATE['process']
    STATE.update(process=None, url='', key=None, uploaded=set(), model=None)
    if process is None:
        return
    try:
        import psutil
        parent = psutil.Process(process.pid)
        children = parent.children(recursive=True)
        for item in children + [parent]:
            try:
                item.terminate()
            except psutil.NoSuchProcess:
                pass
        _, alive = psutil.wait_procs(children + [parent], timeout=8)
        for item in alive:
            try:
                item.kill()
            except psutil.NoSuchProcess:
                pass
    except Exception:
        process.kill()
    if STATE['log']:
        STATE['log'].close()
        STATE['log'] = None


def ensure_server(engine, server, reporter):
    """Point STATE['url'] at a live ComfyUI: the given address, or the private one (started here)."""
    if server:
        url = server.rstrip('/')
        if STATE['key'] != ('external', url):
            stop_server()
            STATE.update(url=url, key=('external', url), external=True, uploaded=set())
            try:
                call('/system_stats', timeout=30)
            except (OSError, WorkerError) as exc:
                STATE.update(url='', key=None)
                raise WorkerError('MissingRuntime', f'No ComfyUI answers at {url}: {exc}', recoverable=True) from None
        return
    key = ('private', engine['comfy'], engine['models'])
    process = STATE['process']
    if STATE['key'] == key and process is not None and process.poll() is None:
        return
    stop_server()
    comfy = Path(engine['comfy'])
    if not (comfy / 'main.py').is_file():
        raise WorkerError('MissingRuntime', f'ComfyUI is missing at {comfy}: install the image engine.', recoverable=True)
    data = Path(engine['data'])
    folders = {name: data / name for name in ('input', 'output', 'temp', 'user')}
    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)
    models = Path(engine['models'])
    config = data / 'extra_model_paths.yaml'
    config.write_text('cytools_storyboard:\n'
                      f'  base_path: {json.dumps(str(models))}\n'
                      '  diffusion_models: diffusion_models\n  text_encoders: text_encoders\n  vae: vae\n  loras: loras\n'
                      '  model_patches: model_patches\n',
                      encoding='utf-8')
    port = free_port()
    command = [sys.executable, 'main.py', '--listen', '127.0.0.1', '--port', str(port), '--disable-auto-launch',
               '--disable-all-custom-nodes', '--disable-api-nodes', '--extra-model-paths-config', str(config),
               '--input-directory', str(folders['input']), '--output-directory', str(folders['output']),
               '--temp-directory', str(folders['temp']), '--user-directory', str(folders['user'])]
    command += [str(x) for x in engine.get('arguments') or []]
    log_path = Path(engine['log'])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    STATE['log'] = open(log_path, 'a', encoding='utf-8', errors='replace')
    STATE['log'].write(f'\n=== ComfyUI started {time.strftime("%Y-%m-%d %H:%M:%S")} on port {port} ===\n')
    STATE['log'].flush()
    flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0
    reporter.progress(1, step='Starting the image engine')
    env = dict(os.environ)
    for name in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE'):
        env[name] = '1'
    env.pop('PYTHONPATH', None)      # ComfyUI must only see its own modules
    process = subprocess.Popen(command, cwd=str(comfy), stdin=subprocess.DEVNULL, stdout=STATE['log'],
                               stderr=subprocess.STDOUT, creationflags=flags, env=env)
    STATE.update(process=process, url=f'http://127.0.0.1:{port}', key=key, external=False, uploaded=set(), model=None)
    deadline = time.monotonic() + float(engine.get('startupSeconds', 300))
    while True:
        if process.poll() is not None:
            tail = log_path.read_text('utf-8', errors='replace')[-1500:]
            STATE.update(process=None, url='', key=None)
            raise WorkerError('WorkerCrashed', f'ComfyUI stopped while starting (code {process.returncode}).',
                              details={'log': str(log_path), 'tail': tail})
        try:
            call('/system_stats', timeout=5)
            break
        except (OSError, WorkerError):
            if time.monotonic() > deadline:
                stop_server()
                raise WorkerError('Timeout', 'ComfyUI did not start in time.', details={'log': str(log_path)}) from None
            time.sleep(1.0)


def device_report():
    try:
        stats = call('/system_stats', timeout=20)
    except (OSError, WorkerError):
        return {}
    devices = stats.get('devices') or [{}]
    system = stats.get('system') or {}
    return {'device': devices[0].get('name', ''), 'vramTotalBytes': devices[0].get('vram_total'),
            'vramFreeBytes': devices[0].get('vram_free'), 'comfyui': system.get('comfyui_version', ''),
            'torch': system.get('pytorch_version', '')}


# ---------------------------------------------------------------------------- progress events
class Events:
    """ComfyUI's websocket in a background thread; messages land in a queue. Optional: without
    it the job still completes (the history is polled), only the step counter is missing."""

    def __init__(self):
        self.queue = queue.Queue()
        self.thread = None
        self.url = None
        self.stop = threading.Event()

    def start(self):
        if self.thread is not None and self.thread.is_alive() and self.url == STATE['url']:
            return
        self.stop.set()
        self.stop = threading.Event()
        self.url = STATE['url']
        self.thread = threading.Thread(target=self._run, args=(self.url, self.stop), daemon=True, name='comfy-events')
        self.thread.start()

    def _run(self, url, stop):
        try:
            import asyncio
            import aiohttp
        except ImportError:
            return

        async def listen():
            address = url.replace('http', 'ws', 1) + '/ws?clientId=' + STATE['client']
            while not stop.is_set():
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.ws_connect(address, heartbeat=30, max_msg_size=0) as socket_:
                            while not stop.is_set():
                                try:
                                    message = await socket_.receive(timeout=1.0)
                                except asyncio.TimeoutError:
                                    continue
                                if message.type == aiohttp.WSMsgType.TEXT:
                                    try:
                                        self.queue.put(json.loads(message.data))
                                    except ValueError:
                                        pass
                                elif message.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR,
                                                      aiohttp.WSMsgType.CLOSE):
                                    break
                except Exception:
                    await asyncio.sleep(1.0)
        asyncio.run(listen())

    def drain(self):
        while True:
            try:
                yield self.queue.get_nowait()
            except queue.Empty:
                return


EVENTS = Events()


# ---------------------------------------------------------------------------- operations
def submit(job):
    answer = call('/prompt', {'prompt': job['prompt'], 'client_id': STATE['client']}, timeout=120)
    if 'prompt_id' in answer:
        return answer['prompt_id']
    problems = []
    missing = False
    for node_id, entry in (answer.get('node_errors') or {}).items():
        for error in entry.get('errors', []):
            problems.append(f'{entry.get("class_type", node_id)}: {error.get("details") or error.get("message")}')
            name = (error.get('extra_info') or {}).get('input_name')
            if error.get('type') == 'value_not_in_list' and name in MODEL_INPUTS:
                missing = True
    message = '; '.join(problems) or (answer.get('error') or {}).get('message') or str(answer)[:500]
    if missing:
        where = 'that ComfyUI server' if STATE['external'] else 'the application (Images tab > Installation)'
        raise WorkerError('MissingModel', f'A model file is not installed in {where}: {message}', recoverable=True)
    raise WorkerError('InvalidParameters', 'ComfyUI refused the workflow: ' + message)


def render(job, position, total, cancel_file, reporter):
    prompt_id = submit(job)
    started = time.monotonic()
    last_poll = 0.0
    interrupted = False
    base, share = 100.0 * position / total, 100.0 / total
    label = f'Picture {position + 1}/{total}'
    reporter.progress(base + share * 0.02, step=label, message=job.get('label', ''))
    while True:
        if not interrupted and Path(cancel_file).exists():
            call('/interrupt', {}, timeout=30)
            interrupted = True
        for message in EVENTS.drain():
            data = message.get('data') or {}
            if data.get('prompt_id') not in (None, prompt_id):
                continue
            if message.get('type') == 'progress' and data.get('max'):
                done = float(data['value']) / float(data['max'])
                reporter.progress(base + share * (0.05 + 0.9 * done), step=label,
                                  message=f'{job.get("label", "")} - step {data["value"]}/{data["max"]}')
            elif message.get('type') == 'executing' and data.get('node'):
                node = (job['prompt'].get(str(data['node'])) or {}).get('class_type', '')
                if node in ('UNETLoader', 'CLIPLoader', 'VAELoader'):
                    reporter.progress(base + share * 0.03, step=label, message='Loading the model')
        if time.monotonic() - last_poll > 0.7:
            last_poll = time.monotonic()
            history = call('/history/' + prompt_id, timeout=60).get(prompt_id)
            if history:
                status = history.get('status') or {}
                if status.get('status_str') == 'error' or interrupted:
                    error = next((m[1] for m in status.get('messages', []) if m[0] == 'execution_error'), {})
                    interrupt = any(m[0] == 'execution_interrupted' for m in status.get('messages', []))
                    if interrupted or interrupt:
                        raise WorkerError('Cancelled', 'Cancelled')
                    text = str(error.get('exception_message', 'ComfyUI failed'))[:1500]
                    code = 'InsufficientVRAM' if 'out of memory' in text.lower() or 'allocation' in text.lower() else \
                        'MissingModel' if 'header too small' in text.lower() or 'no such file' in text.lower() else 'InferenceFailed'
                    raise WorkerError(code, f'{error.get("node_type", "ComfyUI")}: {text}', recoverable=code != 'InferenceFailed',
                                      details={'node': error.get('node_type'), 'log': STATE['log'].name if STATE['log'] else ''})
                images = ((history.get('outputs') or {}).get(str(job['saveNode'])) or {}).get('images') or []
                if status.get('completed') or images:
                    if not images:
                        raise WorkerError('InferenceFailed', 'ComfyUI finished without a picture.')
                    image = images[0]
                    query = urllib.parse.urlencode({'filename': image['filename'], 'subfolder': image.get('subfolder', ''),
                                                    'type': image.get('type', 'output')})
                    content = call('/view?' + query, timeout=300, raw=True)
                    target = Path(job['file'])
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
                    seconds = time.monotonic() - started
                    reporter.progress(base + share, step=label, message=job.get('label', ''))
                    return {'id': job['id'], 'file': str(target), 'seconds': seconds}
        if STATE['process'] is not None and STATE['process'].poll() is not None:
            code = STATE['process'].returncode
            log = STATE['log'].name if STATE['log'] else ''
            stop_server()
            raise WorkerError('WorkerCrashed', f'ComfyUI stopped during the picture (code {code}).', details={'log': log})
        time.sleep(0.15)


def kernels_report(log_path):
    """Whether ComfyUI found its CUDA kernels for int8 models (it says so once in its log)."""
    try:
        text = Path(log_path).read_text('utf-8', errors='replace')[-200000:]
    except OSError:
        return None
    marker = text.rfind('Found comfy_kitchen backend cuda:')
    if marker < 0:
        return None
    return "'available': True" in text[marker:marker + 200]


def generate(request, reporter):
    jobs = request['jobs']
    engine = request.get('engine') or {}
    load_started = time.monotonic()
    ensure_server(engine, request.get('server', ''), reporter)
    EVENTS.start()
    folder = request.get('referenceFolder', 'cytools_images')
    for job in jobs:
        for path, name in (job.get('references') or {}).items():
            if not Path(path).is_file():
                raise WorkerError('InvalidParameters', f'Reference picture not found: {path}')
            if (folder, name) not in STATE['uploaded']:
                upload(path, name, folder)
                STATE['uploaded'].add((folder, name))
    pictures = []
    first_seconds = None
    for position, job in enumerate(jobs):
        if Path(request['cancelFile']).exists():
            raise WorkerError('Cancelled', 'Cancelled')
        picture = render(job, position, len(jobs), request['cancelFile'], reporter)
        picture['model'] = request['model']['id']
        if first_seconds is None:
            first_seconds = picture['seconds']
        pictures.append(picture)
        STATE['model'] = request['model']['id']
        reporter.resident(gpu=True, models=[request['model']['id']], server=STATE['url'] if STATE['external'] else 'private')
    later = [p['seconds'] for p in pictures[1:]] or [pictures[0]['seconds']]
    report = device_report()
    return {'pictures': pictures, 'secondsPerPicture': sum(later) / len(later), 'firstPictureSeconds': first_seconds,
            'startSeconds': time.monotonic() - load_started - sum(p['seconds'] for p in pictures),
            'int8Kernels': None if STATE['external'] else kernels_report(engine.get('log', '')),
            'server': 'external' if STATE['external'] else 'private', **report}


def unload(request, reporter):
    if STATE['url']:
        call('/free', {'unload_models': True, 'free_memory': True}, timeout=60)
    STATE['model'] = None
    reporter.resident(gpu=False, models=[])
    return {'unloaded': True}


def status(request, reporter):
    alive = STATE['process'] is not None and STATE['process'].poll() is None
    return {'server': STATE['url'], 'private': alive, 'external': STATE['external'], 'model': STATE['model'],
            **(device_report() if STATE['url'] else {})}


if __name__ == '__main__':
    try:
        code = serve({'generate': generate, 'unload': unload, 'status': status})
    finally:
        stop_server()
    raise SystemExit(code)

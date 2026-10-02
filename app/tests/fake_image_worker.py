"""Stand-in for workers/image_worker.py: same protocol and payload, pictures drawn with Pillow.

It reads each API prompt like ComfyUI would (loaders, reference pictures, text, sampler, size),
writes what it understood into the PNG's text chunks so the tests can check the whole chain,
keeps a "loaded model" between requests like the real worker, reports steps, and stops at its
next step when the cancellation file appears.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workers._protocol import WorkerError, serve  # noqa: E402

STATE = {'model': None, 'loads': 0}


def of_class(prompt, *kinds):
    return [node for node in prompt.values() if node['class_type'] in kinds]


def generate(request, reporter):
    from PIL import Image, PngImagePlugin
    model = request['model']
    if STATE['model'] != model['id']:
        STATE['model'] = model['id']
        STATE['loads'] += 1
        reporter.progress(1, step='Loading ' + model['name'])
    reporter.resident(gpu=False, models=[model['id']])
    delay = float(os.environ.get('FAKE_IMAGE_STEP_SECONDS', '0'))
    pictures = []
    jobs = request['jobs']
    for index, job in enumerate(jobs):
        prompt = job['prompt']
        for path in job['references']:
            if not Path(path).is_file():
                raise WorkerError('InvalidParameters', f'Reference picture not found: {path}')
        sampler = of_class(prompt, 'KSampler')[0]['inputs']
        latent = of_class(prompt, 'EmptyLatentImage', 'EmptySD3LatentImage')[0]['inputs']
        encoders = of_class(prompt, 'TextEncodeQwenImage21', 'TextEncodeQwenImageEditPlus', 'CLIPTextEncode')
        text = encoders[0]['inputs'].get('prompt') or encoders[0]['inputs'].get('text')
        loaded = sorted(node['inputs']['image'] for node in of_class(prompt, 'LoadImage'))
        if loaded != sorted(f'{request["referenceFolder"]}/{name}' for name in job['references'].values()):
            raise WorkerError('InvalidParameters', f'The prompt loads {loaded}, the job uploads {job["references"]}')
        steps = int(sampler['steps'])
        for step in range(steps):
            if Path(request['cancelFile']).exists():
                raise WorkerError('Cancelled', 'Cancelled')
            time.sleep(delay)
            reporter.progress(100.0 * (index + (step + 1) / steps) / len(jobs), step=f'Picture {index + 1}/{len(jobs)}',
                              message=f'step {step + 1}/{steps}')
        seed = int(sampler['seed'])
        image = Image.new('RGB', (latent['width'] // 8, latent['height'] // 8),
                          (seed * 37 % 256, seed * 91 % 256, len(job['references']) * 60 % 256))
        info = PngImagePlugin.PngInfo()
        for key, value in (('prompt', text), ('references', '|'.join(job['references'])), ('model', model['id']),
                           ('unet', of_class(prompt, 'UNETLoader')[0]['inputs']['unet_name']), ('steps', str(steps)),
                           ('cfg', str(sampler['cfg'])), ('lora', str(bool(of_class(prompt, 'LoraLoaderModelOnly'))))):
            info.add_text(key, value)
        target = Path(job['file'])
        target.parent.mkdir(parents=True, exist_ok=True)
        image.save(target, pnginfo=info)
        pictures.append({'id': job['id'], 'file': str(target), 'seconds': delay * steps, 'model': model['id']})
    return {'pictures': pictures, 'device': 'fake', 'secondsPerPicture': delay * steps, 'firstPictureSeconds': delay * steps,
            'startSeconds': 0.0, 'int8Kernels': None, 'server': request.get('server') or 'private',
            'loads': STATE['loads'], 'pid': os.getpid()}


def unload(request, reporter):
    STATE['model'] = None
    reporter.resident(gpu=False, models=[])
    return {'unloaded': True}


if __name__ == '__main__':
    raise SystemExit(serve({'generate': generate, 'unload': unload}))

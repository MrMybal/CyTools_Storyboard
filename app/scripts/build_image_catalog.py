"""Write app/models/catalog.json: the image models the application can install.

    runtime/python/Scripts/python.exe app/scripts/build_image_catalog.py

Sizes, SHA-256 and revisions are read from the Hugging Face API at the moment the script runs
and pinned in the catalogue (every download URL names its commit), so an installation is
checked against what was declared here, not against whatever the repository holds later.
All models share one ComfyUI-style folder (data/models/comfyui/<diffusion_models|text_encoders|
vae|loras|model_patches>/): a file used by two models (text encoder, VAE) is downloaded once.
"""
import json
import urllib.request
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
DIRECTORY = 'data/models/comfyui'
QWEN_RESEARCH = {'name': 'Qwen Research License (non-commercial)', 'commercialUse': 'forbidden', 'requiresAcceptance': False,
                 'url': 'https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE',
                 'notes': 'Research and evaluation only; a commercial licence is asked from Qwen.'}
APACHE = {'name': 'Apache-2.0', 'commercialUse': 'allowed', 'requiresAcceptance': False,
          'url': 'https://www.apache.org/licenses/LICENSE-2.0'}

MODELS = [
    {'id': 'qwen-image-2.1-int8', 'name': 'Qwen-Image 2.1 (int8)', 'loader': 'qwen21', 'kinds': ['edit', 'text'],
     'default': True, 'license': QWEN_RESEARCH, 'control': 'qwen-image-2.1-controlnet-int8',
     'summary': 'One model for pictures from a text and from up to 10 reference pictures.',
     'source': {'kind': 'huggingface', 'repository': 'Comfy-Org/Qwen-Image-2.1', 'gated': False,
                'url': 'https://huggingface.co/Qwen/Qwen-Image-2.1'},
     'roles': {'unet': ('Comfy-Org/Qwen-Image-2.1', 'diffusion_models/qwen_image_2.1_int8_convrot.safetensors'),
               'clip': ('Comfy-Org/Qwen-Image-2.1', 'text_encoders/qwen3vl_8b_int8_convrot.safetensors'),
               'vae': ('Comfy-Org/Qwen-Image-2.1', 'vae/qwen_image_2.1_vae_bf16.safetensors')},
     'defaults': {'steps': 25, 'guidance': 1.0, 'fastSteps': 25, 'fastGuidance': 1.0, 'sampler': 'euler',
                  'scheduler': 'simple', 'maxReferences': 10, 'referenceResolution': 1024, 'referenceToken': '<image{n}>',
                  'multiple': 32},
     'resources': {'vramBytes': 20 * 1024 ** 3, 'ramBytes': 32 * 1024 ** 3}},
    {'id': 'qwen-image-2.1-controlnet-int8', 'name': 'Qwen-Image 2.1 ControlNet (int8)', 'loader': 'patch', 'kinds': ['control'],
     'default': False, 'license': QWEN_RESEARCH,
     'summary': 'Structure guide for Qwen-Image 2.1: a shot follows the depth or the pose of its 3D staging.',
     'source': {'kind': 'huggingface', 'repository': 'Comfy-Org/Qwen-Image-2.1', 'gated': False,
                'url': 'https://huggingface.co/Comfy-Org/Qwen-Image-2.1'},
     'roles': {'patch': ('Comfy-Org/Qwen-Image-2.1', 'model_patches/qwen_image_2.1_fun_controlnet_union_int8_convrot.safetensors')},
     'defaults': {}, 'resources': {'vramBytes': 4 * 1024 ** 3, 'ramBytes': 8 * 1024 ** 3}},
    {'id': 'qwen-image-edit-2511-int8', 'name': 'Qwen-Image-Edit 2511 (int8)', 'loader': 'qwen_edit_plus', 'kinds': ['edit'],
     'default': False, 'license': APACHE,
     'summary': 'Pictures from 1 to 3 reference pictures; 4 steps with its Lightning LoRA.',
     'source': {'kind': 'huggingface', 'repository': 'Comfy-Org/Qwen-Image-Edit_ComfyUI', 'gated': False,
                'url': 'https://huggingface.co/Qwen/Qwen-Image-Edit-2511'},
     'roles': {'unet': ('Comfy-Org/Qwen-Image-Edit_ComfyUI', 'split_files/diffusion_models/qwen_image_edit_2511_int8_convrot.safetensors'),
               'clip': ('Comfy-Org/Qwen-Image_ComfyUI', 'split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors'),
               'vae': ('Comfy-Org/Qwen-Image_ComfyUI', 'split_files/vae/qwen_image_vae.safetensors'),
               'lora': ('lightx2v/Qwen-Image-Edit-2511-Lightning', 'Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors')},
     'defaults': {'steps': 40, 'guidance': 3.0, 'fastSteps': 4, 'fastGuidance': 1.0, 'shift': 3.1, 'sampler': 'euler',
                  'scheduler': 'simple', 'maxReferences': 3, 'referenceToken': 'image {n}', 'multiple': 16},
     'resources': {'vramBytes': 24 * 1024 ** 3, 'ramBytes': 48 * 1024 ** 3}},
    {'id': 'qwen-image-2512-fp8', 'name': 'Qwen-Image 2512 (fp8)', 'loader': 'qwen_t2i', 'kinds': ['text'],
     'default': False, 'license': APACHE,
     'summary': 'Pictures from a text only; 4 steps with its Lightning LoRA.',
     'source': {'kind': 'huggingface', 'repository': 'Comfy-Org/Qwen-Image_ComfyUI', 'gated': False,
                'url': 'https://huggingface.co/Qwen/Qwen-Image-2512'},
     'roles': {'unet': ('Comfy-Org/Qwen-Image_ComfyUI', 'split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors'),
               'clip': ('Comfy-Org/Qwen-Image_ComfyUI', 'split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors'),
               'vae': ('Comfy-Org/Qwen-Image_ComfyUI', 'split_files/vae/qwen_image_vae.safetensors'),
               'lora': ('lightx2v/Qwen-Image-2512-Lightning', 'Qwen-Image-2512-Lightning-4steps-V1.0-bf16.safetensors')},
     'defaults': {'steps': 50, 'guidance': 4.0, 'fastSteps': 4, 'fastGuidance': 1.0, 'shift': 3.1, 'sampler': 'euler',
                  'scheduler': 'simple', 'maxReferences': 0, 'referenceToken': 'image {n}', 'multiple': 16},
     'resources': {'vramBytes': 24 * 1024 ** 3, 'ramBytes': 48 * 1024 ** 3}},
]
FOLDERS = {'unet': 'diffusion_models', 'clip': 'text_encoders', 'vae': 'vae', 'lora': 'loras', 'patch': 'model_patches'}
_repos = {}


def repository(name):
    if name not in _repos:
        request = urllib.request.Request(f'https://huggingface.co/api/models/{name}?blobs=true',
                                         headers={'User-Agent': 'CyTools-Storyboard-catalog'})
        with urllib.request.urlopen(request, timeout=60) as response:
            info = json.load(response)
        _repos[name] = (info['sha'], {s['rfilename']: s for s in info['siblings']})
    return _repos[name]


def main():
    models = []
    for spec in MODELS:
        files, roles = [], {}
        for role, (repo, remote) in spec['roles'].items():
            revision, siblings = repository(repo)
            if remote not in siblings:
                raise SystemExit(f'{repo}: {remote} not found')
            entry = siblings[remote]
            local = f'{FOLDERS[role]}/{Path(remote).name}'
            files.append({'path': local, 'size': int(entry['size']), 'sha256': (entry.get('lfs') or {}).get('sha256'),
                          'url': f'https://huggingface.co/{repo}/resolve/{revision}/{remote}', 'role': role})
            roles[role] = local
        model = {k: v for k, v in spec.items() if k != 'roles'}
        model.update(backend='comfyui', family='image', directory=DIRECTORY, files=files, roles=roles,
                     downloadBytes=sum(f['size'] for f in files))
        model['source'] = dict(spec['source'], revision=repository(spec['source']['repository'])[0])
        models.append(model)
        print(f'{model["id"]}: {model["downloadBytes"] / 1e9:.2f} GB, {len(files)} files')
    target = APP / 'models' / 'catalog.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps({'schemaVersion': 1, 'models': models}, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()

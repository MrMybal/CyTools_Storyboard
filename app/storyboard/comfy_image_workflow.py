"""ComfyUI graphs for the pictures planned by storyboard/imagegen.py.

One builder, two outputs of the same graph:

- `document()`: the editor workflow (what the ComfyUI page loads by drag and drop), written
  by `export` next to the reference pictures, for people who render in their own ComfyUI;
- `api_prompt()`: the API form of that same graph, posted by the application's image engine
  to its private ComfyUI (workers/image_worker.py). What the application renders and what the
  exported workflow renders are therefore the same nodes with the same values.

Three model families, each with the nodes of its official ComfyUI template:

  qwen21          Qwen-Image 2.1: text-to-image and editing in one model, up to 10 reference
                  pictures (TextEncodeQwenImage21, QwenImage21Cache, KSampler euler/simple, cfg 1);
  qwen_edit_plus  Qwen-Image-Edit 2509/2511: 1 to 3 reference pictures (TextEncodeQwenImageEditPlus,
                  ModelSamplingAuraFlow, CFGNorm, optional Lightning LoRA);
  qwen_t2i        Qwen-Image / 2512: text only (CLIPTextEncode, ModelSamplingAuraFlow, optional
                  Lightning LoRA).

Loaders are shared by every picture of a workflow and keep the same node ids from one API
prompt to the next, so ComfyUI keeps the model loaded between pictures.
"""
import hashlib
import json
import shutil
from pathlib import Path

from .comfy_workflow import Workflow
from .model import StoryboardError

FAMILIES = ('qwen21', 'qwen_edit_plus', 'qwen_t2i')
# Widget names in the order the editor stores their values (None: a value the API does not take).
WIDGETS = {
    'UNETLoader': ['unet_name', 'weight_dtype'], 'CLIPLoader': ['clip_name', 'type', 'device'],
    'VAELoader': ['vae_name'], 'LoadImage': ['image', None], 'QwenImage21Cache': ['device', 'dtype'],
    'TextEncodeQwenImage21': ['prompt', 'negative_prompt', 'resolution'],
    'EmptyLatentImage': ['width', 'height', 'batch_size'], 'EmptySD3LatentImage': ['width', 'height', 'batch_size'],
    'KSampler': ['seed', None, 'steps', 'cfg', 'sampler_name', 'scheduler', 'denoise'],
    'VAEDecode': [], 'SaveImage': ['filename_prefix'], 'ModelSamplingAuraFlow': ['shift', 'sampling'],
    'CFGNorm': ['strength', 'pre_cfg'], 'LoraLoaderModelOnly': ['lora_name', 'strength_model'],
    'TextEncodeQwenImageEditPlus': ['prompt'], 'FluxKontextMultiReferenceLatentMethod': ['reference_latents_method'],
    'CLIPTextEncode': ['text'], 'MarkdownNote': [None], 'Note': [None],
    'ModelPatchLoader': ['name'], 'ZImageFunControlnet': ['strength', 'start_percent', 'end_percent'],
}
REFERENCE_FOLDER = 'cytools_images'


def settings_for(model, options, mode):
    """Steps, guidance and LoRA actually used for a model: the user's values, else the model's own
    (its fast LoRA settings when fast mode is on and the model has one)."""
    defaults = model.get('defaults') or {}
    files = model.get('files_by_role') or {}
    fast = bool(options.get('fast')) and bool(files.get('lora'))
    steps = int(options.get('steps') or 0) or int(defaults['fastSteps' if fast else 'steps'])
    guidance = float(options.get('guidance') or 0) or float(defaults['fastGuidance' if fast else 'guidance'])
    return {'steps': steps, 'guidance': guidance, 'fast': fast, 'sampler': defaults.get('sampler', 'euler'),
            'scheduler': defaults.get('scheduler', 'simple'), 'shift': float(defaults.get('shift', 3.1)),
            'referenceResolution': int(defaults.get('referenceResolution', 1024))}


def reference_name(path):
    """Name of a reference picture inside ComfyUI's input folder: content hash, so a changed
    picture never hides behind an old upload."""
    path = Path(path)
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            digest.update(block)
    return f'{digest.hexdigest()[:20]}{path.suffix.lower()}'


def controlled(request, model):
    """Whether a request's control picture is used: the model must be Qwen-Image 2.1 with its ControlNet."""
    return bool(request.get('control') and request['control'].get('file') and model['loader'] == 'qwen21'
                and model['files_by_role'].get('patch'))


def build(requests, model, options, names=None, folder=REFERENCE_FOLDER, prefix='cytools/picture'):
    """The Workflow of `requests` on `model` (a catalogue entry with files_by_role).
    names: {reference path: file name under `folder` in ComfyUI's input}; computed when omitted."""
    family = model['loader']
    if family not in FAMILIES:
        raise StoryboardError(f'Unknown image model family {family!r}.')
    files = model['files_by_role']
    limit = int((model.get('defaults') or {}).get('maxReferences', 3))
    w = Workflow()
    w.node(1, 'UNETLoader', (0, 0), [files['unet'], 'default'], outputs=[('MODEL', 'MODEL')], size=(420, 82))
    w.node(2, 'CLIPLoader', (0, 130), [files['clip'], 'qwen_image', 'default'], outputs=[('CLIP', 'CLIP')], size=(420, 106))
    w.node(3, 'VAELoader', (0, 280), [files['vae']], outputs=[('VAE', 'VAE')], size=(420, 60))
    modes = {('edit' if r['references'] else 'text') for r in requests}
    settings = {mode: settings_for(model, options, mode) for mode in modes}
    any_settings = next(iter(settings.values()))
    source = 1
    from .imagegen import active_loras
    for position, (name, strength) in enumerate(active_loras(options)):
        # the user's LoRAs sit right behind the model, before its own few-step LoRA and samplers
        w.node(40 + position, 'LoraLoaderModelOnly', (-460, 110 * position), [name, strength], inputs=[('model', 'MODEL')],
               outputs=[('MODEL', 'MODEL')], size=(420, 82), title=f'LoRA {position + 1}')
        w.connect(source, 0, 40 + position, 'model')
        source = 40 + position
    if family == 'qwen21':
        w.node(4, 'QwenImage21Cache', (0, 380), ['auto', 'default'], inputs=[('model', 'MODEL')],
               outputs=[('MODEL', 'MODEL')], size=(420, 82))
        w.connect(source, 0, 4, 'model')
        source = 4
    else:
        if any_settings['fast']:
            w.node(5, 'LoraLoaderModelOnly', (0, 380), [files['lora'], 1.0], inputs=[('model', 'MODEL')],
                   outputs=[('MODEL', 'MODEL')], size=(420, 82), title='Few-step LoRA')
            w.connect(source, 0, 5, 'model')
            source = 5
        w.node(6, 'ModelSamplingAuraFlow', (0, 500), [any_settings['shift'], 'flow'], inputs=[('model', 'MODEL')],
               outputs=[('MODEL', 'MODEL')], size=(420, 60))
        w.connect(source, 0, 6, 'model')
        source = 6
        if family == 'qwen_edit_plus':
            w.node(7, 'CFGNorm', (0, 600), [1.0, False], inputs=[('model', 'MODEL')],
                   outputs=[('patched_model', 'MODEL')], size=(420, 82))
            w.connect(source, 0, 7, 'model')
            source = 7

    if any(controlled(request, model) for request in requests):
        w.node(8, 'ModelPatchLoader', (0, 500), [files['patch']], outputs=[('MODEL_PATCH', 'MODEL_PATCH')], size=(420, 60),
               title='ControlNet (structure of the staging)')
    loaders = {}

    def load(path):
        if path not in loaders:
            node_id = 10 + len(loaders)
            name = (names or {}).get(path) or reference_name(path)
            w.node(node_id, 'LoadImage', (480, 330 * len(loaders)), [f'{folder}/{name}' if folder else name, 'image'],
                   outputs=[('IMAGE', 'IMAGE'), ('MASK', 'MASK')], size=(300, 300), title=Path(path).name)
            loaders[path] = node_id
        return loaders[path]

    for index, request in enumerate(requests):
        base = 100 * (index + 1)
        x, y = 840, 520 * index
        references = request['references']
        mode = 'edit' if references else 'text'
        if len(references) > limit:
            raise StoryboardError(f'{model["name"]} takes {limit} reference picture(s) at most ({len(references)} asked).')
        if mode == 'edit' and family == 'qwen_t2i':
            raise StoryboardError(f'{model["name"]} generates from a text only; it cannot use reference pictures.')
        if mode == 'text' and family == 'qwen_edit_plus':
            raise StoryboardError(f'{model["name"]} needs at least one reference picture.')
        s = settings[mode]
        title = f'{request["label"]}' + (f' #{request["variant"]}' if request.get('variant', 1) > 1 else '')
        negative = request.get('negative') or ''
        if family == 'qwen21':
            inputs = [('clip', 'CLIP')] + ([('vae', 'VAE')] if references else []) + \
                [(f'images.image_{n}', 'IMAGE') for n in range(1, len(references) + 1)]
            w.node(base + 1, 'TextEncodeQwenImage21', (x, y), [request['prompt'], negative, s['referenceResolution']],
                   inputs=inputs, outputs=[('positive', 'CONDITIONING'), ('negative', 'CONDITIONING'), ('latent', 'LATENT')],
                   size=(460, 300), title=title)
            w.connect(2, 0, base + 1, 'clip')
            if references:
                w.connect(3, 0, base + 1, 'vae')
            for n, path in enumerate(references, start=1):
                w.connect(load(path), 0, base + 1, f'images.image_{n}')
            positive, negative_source = (base + 1, 0), (base + 1, 1)
            latent_kind = 'EmptyLatentImage'
        elif family == 'qwen_edit_plus':
            inputs = [('clip', 'CLIP'), ('vae', 'VAE')] + [(f'image{n}', 'IMAGE') for n in range(1, len(references) + 1)]
            for offset, text, name in ((1, request['prompt'], title), (2, negative or ' ', 'negative')):
                w.node(base + offset, 'TextEncodeQwenImageEditPlus', (x, y + 170 * (offset - 1)), [text], inputs=inputs,
                       outputs=[('CONDITIONING', 'CONDITIONING')], size=(460, 150), title=name)
                w.connect(2, 0, base + offset, 'clip')
                w.connect(3, 0, base + offset, 'vae')
                for n, path in enumerate(references, start=1):
                    w.connect(load(path), 0, base + offset, f'image{n}')
                w.node(base + 2 + offset, 'FluxKontextMultiReferenceLatentMethod', (x, y + 340 + 70 * (offset - 1)),
                       ['index_timestep_zero'], inputs=[('conditioning', 'CONDITIONING')],
                       outputs=[('CONDITIONING', 'CONDITIONING')], size=(460, 60))
                w.connect(base + offset, 0, base + 2 + offset, 'conditioning')
            positive, negative_source = (base + 3, 0), (base + 4, 0)
            latent_kind = 'EmptySD3LatentImage'
        else:
            for offset, text, name in ((1, request['prompt'], title), (2, negative, 'negative')):
                w.node(base + offset, 'CLIPTextEncode', (x, y + 200 * (offset - 1)), [text], inputs=[('clip', 'CLIP')],
                       outputs=[('CONDITIONING', 'CONDITIONING')], size=(460, 180), title=name)
                w.connect(2, 0, base + offset, 'clip')
            positive, negative_source = (base + 1, 0), (base + 2, 0)
            latent_kind = 'EmptySD3LatentImage'
        w.node(base + 5, latent_kind, (x + 500, y), [request['width'], request['height'], 1],
               outputs=[('LATENT', 'LATENT')], size=(260, 106))
        # The editor keeps a 'control after generate' value behind the seed.
        w.node(base + 6, 'KSampler', (x + 500, y + 150), [int(request['seed']), 'fixed', s['steps'], s['guidance'],
                                                           s['sampler'], s['scheduler'], 1.0],
               inputs=[('model', 'MODEL'), ('positive', 'CONDITIONING'), ('negative', 'CONDITIONING'),
                       ('latent_image', 'LATENT')], outputs=[('LATENT', 'LATENT')], size=(280, 270))
        if controlled(request, model):
            control = request['control']
            w.node(base + 9, 'ZImageFunControlnet', (x + 500, y + 440), [control['strength'], 0.0, control['end']],
                   inputs=[('model', 'MODEL'), ('model_patch', 'MODEL_PATCH'), ('vae', 'VAE'), ('image', 'IMAGE')],
                   outputs=[('MODEL', 'MODEL')], size=(280, 150), title=f'{control["source"]} control')
            w.connect(source, 0, base + 9, 'model')
            w.connect(8, 0, base + 9, 'model_patch')
            w.connect(3, 0, base + 9, 'vae')
            w.connect(load(control['file']), 0, base + 9, 'image')
            w.connect(base + 9, 0, base + 6, 'model')
        else:
            w.connect(source, 0, base + 6, 'model')
        w.connect(positive[0], positive[1], base + 6, 'positive')
        w.connect(negative_source[0], negative_source[1], base + 6, 'negative')
        w.connect(base + 5, 0, base + 6, 'latent_image')
        w.node(base + 7, 'VAEDecode', (x + 820, y), [], inputs=[('samples', 'LATENT'), ('vae', 'VAE')],
               outputs=[('IMAGE', 'IMAGE')], size=(200, 60))
        w.connect(base + 6, 0, base + 7, 'samples')
        w.connect(3, 0, base + 7, 'vae')
        name = f'{prefix}_{request["key"]}' + (f'_{request["variant"]:02d}' if request.get('variant') else '')
        w.node(base + 8, 'SaveImage', (x + 820, y + 100), [name], inputs=[('images', 'IMAGE')], size=(380, 380),
               title=title)
        w.connect(base + 7, 0, base + 8, 'images')
    w.references = dict(loaders)
    return w


def api_prompt(document):
    """The API form of an editor workflow built here ({node id: {class_type, inputs}})."""
    links = {link[0]: link for link in document['links']}
    prompt = {}
    for node in document['nodes']:
        names = WIDGETS.get(node['type'])
        if names is None:
            raise StoryboardError(f'No widget table for ComfyUI node {node["type"]}.')
        if node['type'] in ('MarkdownNote', 'Note'):
            continue
        inputs = {name: value for name, value in zip(names, node.get('widgets_values') or []) if name}
        for entry in node.get('inputs', []):
            if entry.get('link') is not None:
                link = links[entry['link']]
                inputs[entry['name']] = [str(link[1]), link[2]]
        prompt[str(node['id'])] = {'class_type': node['type'], 'inputs': inputs,
                                   '_meta': {'title': node.get('title', node['type'])}}
    return prompt


def save_nodes(document):
    """{SaveImage node id (str): index of its request} for a workflow built here."""
    return {str(node['id']): node['id'] // 100 - 1 for node in document['nodes'] if node['type'] == 'SaveImage'}


def note(model, requests, settings_text, loras=None):
    files = model['files_by_role']
    folders = {'unet': 'diffusion_models', 'clip': 'text_encoders', 'vae': 'vae', 'lora': 'loras', 'patch': 'model_patches'}
    lines = [f'CyTools Storyboard - {len(requests)} picture(s) with {model["name"]}', '',
             'Copy the folder "cytools_images" (next to this workflow) into ComfyUI/input/.', '', 'Models (ComfyUI/models/):']
    lines += [f'- {folders[role]}/{name}' for role, name in files.items() if role in folders]
    lines += [f'- loras/{name} (strength {strength:g})' for name, strength in loras or []]
    lines += ['', settings_text, '', 'Licence: ' + (model.get('license') or {}).get('name', '')]
    return '\n'.join(lines)


def export(requests, options, target, name='', model=None, board=None):
    """Write the workflow(s) of a plan and its reference pictures into `target`:
    <name>.json (editor workflow), <name>_api.json (API prompt) and cytools_images/."""
    from . import imageengine
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    written, warnings = [], []
    imageengine.render_controls(board, requests, target / REFERENCE_FOLDER)
    groups = {}
    for request in requests:
        groups.setdefault('edit' if request['references'] else 'text', []).append(request)
    stem = name or (requests[0]['target'].get('kind', 'pictures') + '_' + requests[0]['key'] if requests else 'pictures')
    stem = ''.join(c if c.isalnum() or c in '-_' else '_' for c in stem)[:60] or 'pictures'
    for mode, batch in groups.items():
        chosen = model or imageengine.resolve_model(mode, options['model'] if mode == 'edit' else options['textModel'],
                                                    installed=False)
        entry = imageengine.describe(chosen, 'export')     # the workflow names the ControlNet even when it is not installed here
        names = {}
        for request in batch:
            for path in list(request['references']) + ([request['control']['file']] if controlled(request, entry) else []):
                if path not in names:
                    names[path] = reference_name(path)
                    (target / REFERENCE_FOLDER).mkdir(exist_ok=True)
                    if Path(path).resolve() != (target / REFERENCE_FOLDER / names[path]).resolve():
                        shutil.copyfile(path, target / REFERENCE_FOLDER / names[path])
        workflow = build(batch, entry, options, names, prefix='cytools/' + stem)
        for request in batch:
            original = Path((request.get('control') or {}).get('file') or '')
            if original.name.startswith('control_') and original.parent == target / REFERENCE_FOLDER:
                original.unlink(missing_ok=True)
        s = settings_for(entry, options, mode)
        text = f'{s["steps"]} steps, guidance {s["guidance"]:g}, {s["sampler"]} / {s["scheduler"]}' + \
            (', few-step LoRA' if s['fast'] else '')
        document = workflow.document()
        api = api_prompt(document)
        from .imagegen import active_loras
        workflow.node(9, 'MarkdownNote', (0, -330), [note(entry, batch, text, active_loras(options))], size=(420, 280),
                      title='Read me')
        document = workflow.document()
        suffix = '' if len(groups) == 1 else '_' + mode
        for file, data in ((f'{stem}{suffix}.json', document), (f'{stem}{suffix}_api.json', api)):
            (target / file).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
            written.append(str(target / file))
        if not imageengine.is_installed(chosen):
            warnings.append(f'{chosen["name"]} is not installed in this application; the workflow lists its files.')
    return {'folder': str(target), 'file': str(target), 'files': written, 'pictures': len(requests), 'warnings': warnings}

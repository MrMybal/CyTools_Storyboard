"""Turn a storyboard into a CyTools_MiniMaxH3 workflow (schema cytools.minimax_h3.workflow/1).

Where the H3 film export makes one continuous generation carried from segment to segment,
the workflow makes one H3 generation per panel, each with its own frames and references,
and edits them together at the end with the storyboard's transitions:

- panel duration: H3 generates 4 to 15 s. A shorter panel is generated at 4 s and trimmed;
  a longer one is split into chained parts (each part starts on the last frame of the
  previous one) then joined; every shot is trimmed to its exact duration because H3
  rounds up to its 5 + 17n frame grid;
- frames: the panel's first / last images become the first / last frame, keyframes become
  timed guides; the 2D/3D layout render is a reference picture (or the first frame);
- references: identity pictures of the characters, locations, objects, styles, reference
  videos, character voices and sounds (H3: 9 pictures, 3 videos, 3 sounds, 12 in all);
- chaining: a shot can start on the last frame of the previous shot (after crossfades by
  default, always or never);
- prompt: H3's structured layout (subject_definitions, summary, retention_analysis,
  detailed_description, overall_soundscape, non_diegetic_music), dialogue as
  <d>[Language] ...</d> with (S1), (S2) speakers; without characters, the integrated layout;
- depth control: a panel staged in 3D gets a depth video along its camera move as the
  Fun ControlNet control of its generation(s), at the chosen fidelity (see depthcontrol.py);
- the last step joins every shot with a transition per seam (cut, crossfade, fade to black).

Every choice is an option saved in the project. Files are copied next to workflow.json
(`media/`), with relative paths, so the folder can be moved or sent to another machine.
"""
import json
import math
import re
import shutil
from pathlib import Path

from . import depthcontrol, export
from .h3film import (AUDIO_SUFFIXES, MAX_AUDIOS, MAX_PICTURES, MAX_REFERENCES, MAX_VIDEOS, VIDEO_SUFFIXES,
                     _describe, _film_characters, _image_file, _media_file, _referenced, _slug, canvas, probe)
from .model import StoryboardError

SCHEMA = 'cytools.minimax_h3.workflow/1'
FPS = 24
MIN_SECONDS, MAX_SECONDS = 4.0, 15.0
MAX_GUIDES = 16
SHORT_EDGES = (384, 448, 512, 544, 576, 640, 704, 768)

DEFAULTS = {
    'shortEdge': 768, 'width': 0, 'height': 0,
    'seed': 42, 'seedPolicy': 'increment', 'steps': 0,
    'acceleration': 'none', 'referenceAcceleration': 'none',
    'chain': 'crossfades', 'longPanels': 'split', 'shortPanels': 'trim', 'exactDurations': True,
    'layoutUse': 'reference', 'identityScope': 'panel',
    'includeLocations': True, 'includeObjects': True, 'includeStyles': True, 'includeSketches': True,
    'includeVideos': True, 'videoSound': False, 'includeVoices': True, 'includeAudio': True,
    'maxReferenceSeconds': 15.0,
    'includeStyle': True, 'globalPrompt': '', 'promptLayout': 'auto',
    'layoutText': 'The framing, camera angle and placement of people and objects follow <Picture {n}>, a rough '
                  'layout (not its drawing style or its simple shapes).',
    'sketchText': 'The composition follows the sketch <Picture {n}>.',
    'referenceText': '<Picture {n}> is a visual reference for this shot.',
    'locationText': 'The place is {name}{description}, as in <Picture {n}>.',
    'objectText': '{name}{description} looks like <Picture {n}>.',
    'styleText': 'The visual style follows <Picture {n}>, {name}{description}.',
    'videoText': 'The movement, action and camera follow <Video {n}>, {name}{description}, not its appearance.',
    'audioText': 'The sound follows <Audio {n}>, {name}{description}.',
    'continuedText': 'The same shot continues without a cut.',
    'depthControl': 'indicative', 'controlSource': 'auto', 'controlStrength': 0.5, 'controlEnd': 0.5, 'controlBlur': 'medium',
    'controlVersion': '2.0', 'poseHands': True, 'poseFeet': True,
}
CHAIN = ('crossfades', 'always', 'never')
ACCELERATIONS = ('none', 'turbo4', 'turbo8')
REFERENCE_ACCELERATIONS = ('none', 'turbo4')


def options_for(board, overrides=None):
    saved = board.doc['settings'].get('h3workflow') or {}
    options = dict(DEFAULTS, **{k: v for k, v in saved.items() if k in DEFAULTS})
    for key, value in (overrides or {}).items():
        if key not in DEFAULTS:
            raise StoryboardError(f'Unknown workflow option {key!r}.')
        options[key] = value
    checks = (('seedPolicy', ('fixed', 'increment', 'random')), ('acceleration', ACCELERATIONS),
              ('referenceAcceleration', REFERENCE_ACCELERATIONS), ('chain', CHAIN),
              ('longPanels', ('split', 'clamp')), ('shortPanels', ('trim', 'extend')),
              ('layoutUse', ('reference', 'first_frame', 'none')), ('identityScope', ('panel', 'film')),
              ('promptLayout', ('auto', 'structured', 'integrated')), ('depthControl', depthcontrol.LEVELS),
              ('controlBlur', tuple(depthcontrol.BLUR)),
              ('controlSource', depthcontrol.SOURCES), ('controlVersion', ('2.0', '1.0')))
    for key, allowed in checks:
        if options[key] not in allowed:
            raise StoryboardError(f'{key} must be one of {", ".join(allowed)}.')
    if not 0 <= int(options['steps']) <= 100:
        raise StoryboardError('steps goes from 0 (default) to 100.')
    if not 2.0 <= float(options['maxReferenceSeconds']) <= 15.0:
        raise StoryboardError('maxReferenceSeconds goes from 2 to 15 seconds.')
    depthcontrol.settings(options)
    return options


def aligned_seconds(seconds):
    """What H3 really generates for a duration (17k + 5 frames, rounded up)."""
    frames = max(5, round(seconds * FPS))
    while frames % 17 != 5:
        frames += 1
    return frames / FPS


def _fill(template, number, values):
    try:
        return template.format(n=number, **values)
    except (KeyError, IndexError, ValueError) as exc:
        raise StoryboardError(f'Workflow text template {template[:40]!r}...: {exc}') from None


def _clean(text):
    return ' '.join(str(text or '').split())


# ---------------------------------------------------------------------------- one panel
def panel_media(board, panel, options, characters):
    """Frames, guides and references of one panel, with the reasons for what was left out."""
    warnings = []
    frames = {'first': None, 'last': None, 'guides': []}
    for entry in panel['images']:
        path = _image_file(board, entry['file'])
        if not path:
            continue
        if entry['role'] in ('first', 'last') and frames[entry['role']] is None:
            frames[entry['role']] = path
        elif entry['role'] == 'keyframe':
            frames['guides'].append((path, float(entry.get('time', 0.0))))
    layout = panel.get('layout') or {}
    render = _image_file(board, layout['render']) if layout.get('mode') in ('2d', '3d') and layout.get('render') else None
    if render and options['layoutUse'] == 'first_frame' and frames['first'] is None:
        frames['first'], render = render, None
    elif options['layoutUse'] != 'reference':
        render = None
    referenced = _referenced(board, panel)
    subjects = characters if options['identityScope'] == 'film' else \
        [i for i in referenced if i['kind'] == 'character' and i['files']]
    pictures = []                      # (path, kind, values)
    for item in subjects:
        path = _image_file(board, item['files'][0])
        if path:
            pictures.append((path, 'identity', {'name': item['name'], 'description': _describe(item), 'item': item}))
    if render:
        pictures.append((render, 'layout', {'label': f'{layout["mode"].upper()} layout'}))
    if options['includeSketches']:
        for entry in panel['images']:
            path = _image_file(board, entry['file'])
            if path and entry['role'] in ('sketch', 'reference'):
                pictures.append((path, 'sketch' if entry['role'] == 'sketch' else 'reference', {'label': entry['role']}))
    for kind, flag in (('location', 'includeLocations'), ('object', 'includeObjects'), ('style', 'includeStyles')):
        if options[flag]:
            for item in referenced:
                path = _image_file(board, item['files'][0]) if item['kind'] == kind and item['files'] else None
                if path:
                    pictures.append((path, kind, {'name': item['name'], 'description': _describe(item)}))
    seen, unique = set(), []
    for entry in pictures:
        if entry[0] not in seen and entry[0] not in (frames['first'], frames['last']):
            seen.add(entry[0])
            unique.append(entry)
    pictures = unique
    videos = []
    if options['includeVideos']:
        for item in referenced:
            path = _media_file(board, item, VIDEO_SUFFIXES) if item['kind'] == 'video' else None
            if path:
                videos.append((path, {'name': item['name'], 'description': _describe(item)}))
    audios = []                        # (path, kind, values)
    if options['includeVoices']:
        for item in subjects:
            path = _media_file(board, item, AUDIO_SUFFIXES)
            if path:
                audios.append((path, 'voice', {'name': item['name'], 'item': item}))
    if options['includeAudio']:
        for item in referenced:
            path = _media_file(board, item, AUDIO_SUFFIXES + VIDEO_SUFFIXES) if item['kind'] == 'audio' else None
            if path:
                audios.append((path, 'sound', {'name': item['name'], 'description': _describe(item)}))
    dropped = len(pictures[MAX_PICTURES:]) + len(videos[MAX_VIDEOS:]) + len(audios[MAX_AUDIOS:])
    pictures, videos, audios = pictures[:MAX_PICTURES], videos[:MAX_VIDEOS], audios[:MAX_AUDIOS]
    while len(pictures) + len(videos) + len(audios) > MAX_REFERENCES and len(pictures) > 1:
        pictures.pop()
        dropped += 1
    if dropped:
        warnings.append(f'{dropped} reference(s) left out (H3: {MAX_PICTURES} pictures, {MAX_VIDEOS} videos, '
                        f'{MAX_AUDIOS} sounds, {MAX_REFERENCES} in all).')
    if audios and not (pictures or videos):
        warnings.append('the sounds are left out: H3 needs a picture or a video next to a sound reference.')
        audios = []
    return frames, pictures, videos, audios, warnings


def _speaker_names(board):
    return {item['id']: item for item in board.doc['library']}


def compose_prompt(board, panel, options, pictures, videos, audios, part=None):
    """The H3 prompt of one shot (structured when characters are defined by pictures)."""
    prompt = panel['prompt']
    library = _speaker_names(board)
    subjects = [values['item'] for _, kind, values in pictures if kind == 'identity']
    subject_number = {item['id']: n for n, item in enumerate(subjects, start=1)}
    picture_number = {id(entry): n for n, entry in enumerate(pictures, start=1)}
    speakers = {}

    def speaker(key):
        return speakers.setdefault(key, len(speakers) + 1)

    style = _clean(board.doc['settings'].get('style')) if options['includeStyle'] else ''
    style = style or 'Cinematic, live-action'
    body = []
    scene = _clean(prompt.get('scene'))
    body.append(f'[Shot 1] {style.rstrip(".")}, {scene or panel["title"] or "the scene"}'.rstrip('.') + '.')
    if part and part[0] > 1:
        body.append(options['continuedText'])
    shot = ' '.join(x for x in (prompt.get('shotSize'), prompt.get('angle') and f'({prompt["angle"]})') if x)
    if shot:
        body.append(export.sentence(shot))
    for entry in pictures:
        path, kind, values = entry
        template = {'layout': 'layoutText', 'sketch': 'sketchText', 'reference': 'referenceText',
                    'location': 'locationText', 'object': 'objectText', 'style': 'styleText'}.get(kind)
        if template:
            body.append(_fill(options[template], picture_number[id(entry)], values))
    for number, (path, values) in enumerate(videos, start=1):
        body.append(_fill(options['videoText'], number, values))
    for number, (path, kind, values) in enumerate(audios, start=1):
        if kind == 'sound':
            body.append(_fill(options['audioText'], number, values))
    camera = export.describe_camera(prompt)
    if camera:
        body.append(camera)
    if _clean(prompt.get('action')):
        body.append(export.sentence(prompt['action']))
    if options['globalPrompt'].strip():
        body.append(export.sentence(options['globalPrompt']))
    if _clean(prompt.get('freeText')):
        body.append(export.sentence(prompt['freeText']))
    description = ' '.join(body)
    for item in subjects:  # characters are named by their subject label in the description
        description = re.sub(rf'\b{re.escape(item["name"])}\b', f'<Subject {subject_number[item["id"]]}>', description)
    lines = []
    for line in prompt.get('dialogue') or []:
        text = str(line.get('line', '')).strip()
        if not text:
            continue
        key = line.get('speaker') or 'narrator'
        item = library.get(key)
        if key in subject_number:
            who = f'<Subject {subject_number[key]}>'
        elif item:
            who = _clean(item.get('description')) or item['name']
        else:
            who = _clean(key) or 'a voice'
        language = _clean(line.get('language')) or board.doc['settings'].get('language') or 'English'
        verb = 'says in an off-screen voiceover' if line.get('offScreen') else _clean(line.get('delivery')) or 'says'
        sentence = f'{who[0].upper() + who[1:]} (S{speaker(key)}) {verb}: <d>[{language}] {text}</d>'
        if line.get('offScreen'):
            sentence += ' while their lips remain completely closed.'
        lines.append(sentence)
    if lines:
        description += ' ' + ' '.join(lines)
    sound = _clean(prompt.get('sound')) or 'N/A'
    music = _clean(prompt.get('music')) or 'N/A'
    structured = options['promptLayout'] == 'structured' or (options['promptLayout'] == 'auto' and subjects)
    if not structured:
        return ('integrated_multimodal_description: ' + description + '\n\noverall_soundscape: ' + sound +
                '\n\nnon_diegetic_music: ' + music)
    definitions = []
    for item in subjects:
        entry = next(e for e in pictures if e[1] == 'identity' and e[2]['item'] is item)
        what = _clean(item.get('description')) or item['name']
        definitions.append(f'<Subject {subject_number[item["id"]]}> is {item["name"]}, {what}, in '
                           f'<Picture {picture_number[id(entry)]}>.')
    retention = [f'<Subject {n}> (appears in [Shot 1]): fully_preserved - identity, clothing and proportions stay '
                 f'as in the reference.' for n in range(1, len(subjects) + 1)]
    for number, (path, kind, values) in enumerate(audios, start=1):
        if kind == 'voice':
            item = values['item']
            target = f'<Subject {subject_number[item["id"]]}> (S{speaker(item["id"])})'
            definitions.append(f'<Audio {number}> is the voice-timbre reference for {target}.')
            retention.append(f'<Audio {number}>: reference - the voice timbre is followed without copying the signal.')
    summary = export.sentence(' '.join(x for x in (scene, _clean(prompt.get('action'))) if x)) or \
        export.sentence(panel['title']) or 'A shot.'
    for item in subjects:
        summary = re.sub(rf'\b{re.escape(item["name"])}\b', f'<Subject {subject_number[item["id"]]}>', summary)
    return ('subject_definitions:\n' + '\n'.join(definitions) + '\n\nsummary:\n' + summary +
            '\n\nretention_analysis:\n' + '\n'.join(retention) + '\n\ndetailed_description:\n' + description +
            '\n\noverall_soundscape:\n' + sound + '\n\nnon_diegetic_music:\n' + music)


# ---------------------------------------------------------------------------- workflow
def build(board, overrides=None, preview=False, workdir=None):
    """(workflow document with paths relative to its folder, files to copy, summary, warnings).
    Depth videos are rendered into `workdir` (not in preview)."""
    options = options_for(board, overrides)
    control = depthcontrol.settings(options)
    width, height = canvas(board, dict(options, shortEdge=options['shortEdge']))
    characters = _film_characters(board)
    panels = board.panels()
    if not panels:
        raise StoryboardError('The storyboard has no panel.')
    files, steps, summary, warnings = {}, [], [], []
    limit = float(options['maxReferenceSeconds'])

    def local(path):
        name = 'media/' + (_digest(path, preview) + path.suffix.lower())
        files[name] = path
        return name

    clips, seams, previous_end = [], [], None
    for number, panel in enumerate(panels, start=1):
        label = f'Panel {number} "{panel["title"]}"'
        frames, pictures, videos, audios, notes = panel_media(board, panel, options, characters)
        warnings += [f'{label}: {note}' for note in notes]
        requested = float(panel['duration'])
        if requested > MAX_SECONDS and options['longPanels'] == 'split':
            count = math.ceil(requested / MAX_SECONDS)
        else:
            count = 1
        part_seconds = min(MAX_SECONDS, max(MIN_SECONDS, requested / count))
        if requested < MIN_SECONDS:
            warnings.append(f'{label}: {requested:.1f} s; H3 generates 4 s at least'
                            + (', trimmed to the panel duration.' if options['shortPanels'] == 'trim' else '.'))
        if requested > MAX_SECONDS and count == 1:
            warnings.append(f'{label}: {requested:.1f} s; clamped to 15 s (one H3 generation).')
        has_references = bool(pictures or videos or audios)
        acceleration = options['referenceAcceleration'] if has_references else options['acceleration']
        base_id = f'p{number:02d}_' + (_slug(panel['title']).lower()[:24] or 'shot')
        base_id = re.sub(r'[^A-Za-z0-9_-]', '_', base_id)
        chained_from = None
        if previous_end and not frames['first']:
            transition = panels[number - 2]['transition']['type']
            if options['chain'] == 'always' or (options['chain'] == 'crossfades' and transition == 'crossfade'):
                chained_from = previous_end
        references = {}
        if pictures:
            references['images'] = [local(path) for path, _, _ in pictures]
        if videos:
            references['videos'] = [{'file': local(path), 'with_audio': bool(options['videoSound'] and (preview or probe(path)[1]))}
                                    for path, _ in videos]
        if audios:
            references['audios'] = [local(path) for path, _, _ in audios]
        for path in [p for p, _ in videos] + [p for p, _, _ in audios]:
            duration = None if preview else probe(path)[0]
            if duration is not None and duration > limit:
                warnings.append(f'{label}: {path.name} lasts {duration:.1f} s; H3 references last 15 s at most '
                                f'(the Tool conforms longer ones).')
        depth = control if depthcontrol.staged(board, panel) is not None else None
        source = depthcontrol.source_for(board, panel, options) if depth else ''
        part_ids = []
        for part in range(1, count + 1):
            step_id = base_id if count == 1 else f'{base_id}_{part}'
            params = {'prompt': compose_prompt(board, panel, options, pictures, videos, audios, (part, count)),
                      'duration': round(part_seconds, 3)}
            if acceleration != 'none':
                params['acceleration'] = acceleration
            if depth:
                name = f'media/{source}_{panel["id"]}_{part}.mp4'
                if not preview:
                    if workdir is None:
                        raise StoryboardError('Rendering depth videos needs a working folder (use export_workflow).')
                    length = depthcontrol.frame_count(part_seconds)
                    samples = depthcontrol.panel_samples(panel, length, (part - 1) * requested / count)
                    files[name] = depthcontrol.write_video(board, samples, Path(workdir) / Path(name).name,
                                                           (width, height), depth['blur'], source,
                                                           hands=bool(options['poseHands']),
                                                           feet=bool(options['poseFeet']))
                params['control'] = {'video': name, 'preprocess': 'none', 'strength': depth['strength'],
                                     'start': depth['start'], 'end': depth['end'], 'version': options['controlVersion']}
            if references:
                params['references'] = references
            if part == 1:
                if frames['first']:
                    params['first_frame'] = local(frames['first'])
                elif chained_from:
                    params['first_frame'] = chained_from
                guides = [{'kind': 'image', 'file': local(path), 'time': round(min(time, part_seconds - 1 / FPS), 3)}
                          for path, time in sorted(frames['guides'], key=lambda g: g[1]) if time < part_seconds]
                if len(frames['guides']) > len(guides):
                    warnings.append(f'{label}: keyframes after {part_seconds:.1f} s are left out (the first '
                                    f'generation part ends there).')
                if guides:
                    params['guides'] = guides[:MAX_GUIDES]
            else:
                params['first_frame'] = '${steps.' + part_ids[-1] + '.lastFrame}'
            if part == count and frames['last']:
                params['last_frame'] = local(frames['last'])
            steps.append({'id': step_id, 'type': 'generate', 'params': params})
            part_ids.append(step_id)
        clip_id = part_ids[-1]
        if count > 1:
            clip_id = base_id + '_joined'
            steps.append({'id': clip_id, 'type': 'concat', 'params': {
                'videos': ['${steps.' + i + '.video}' for i in part_ids], 'transition': 'cut'}})
        generated = aligned_seconds(part_seconds) * count
        target = requested if (requested >= MIN_SECONDS or options['shortPanels'] == 'trim') else generated
        target = min(target, part_seconds * count)  # what was asked of H3 (it rounds up to its frame grid)
        trimmed = options['exactDurations'] and generated - target > 1 / FPS or \
            (requested < MIN_SECONDS and options['shortPanels'] == 'trim')
        if trimmed:
            trim_id = base_id + '_cut'
            steps.append({'id': trim_id, 'type': 'trim', 'params': {
                'video': '${steps.' + clip_id + '.video}', 'start': 0.0, 'end': round(target, 3)}})
            clip_id = trim_id
            # a trimmed clip's last frame, for the next shot to start on
            steps.append({'id': base_id + '_end', 'type': 'extract_frame',
                          'params': {'video': '${steps.' + clip_id + '.video}', 'frame': -1}})
            previous_end = '${steps.' + base_id + '_end.image}'
        else:
            previous_end = '${steps.' + clip_id + '.lastFrame}'
        clips.append('${steps.' + clip_id + '.video}')
        if number < len(panels):
            transition = panel['transition']
            seams.append({'type': transition['type'], 'duration': float(transition.get('duration', 0.5))})
        summary.append({'panel': panel['id'], 'number': number, 'title': panel['title'], 'requestedSeconds': requested,
                        'generations': count, 'generatedSeconds': round(generated, 3),
                        'seconds': round(target if trimmed else generated, 3), 'trimmed': bool(trimmed),
                        'firstFrame': 'image' if frames['first'] else ('previous shot' if chained_from else ''),
                        'lastFrame': bool(frames['last']), 'guides': len(frames['guides']),
                        'pictures': len(pictures), 'videos': len(videos), 'sounds': len(audios),
                        'acceleration': acceleration, 'steps': part_ids, 'depthControl': bool(depth), 'controlSource': source,
                        'prompt': steps[[s['id'] for s in steps].index(part_ids[0])]['params']['prompt']})
    # A trimmed shot's last frame is extracted for the next shot to start on; drop the ones
    # no later shot uses.
    used = json.dumps([s['params'] for s in steps])
    steps = [s for s in steps if s['type'] != 'extract_frame' or '${steps.' + s['id'] + '.image}' in used]
    output = clips[0][len('${steps.'):-len('.video}')]
    if len(clips) > 1:
        steps.append({'id': 'film', 'type': 'concat', 'params': {'videos': clips, 'transitions': seams}})
        output = 'film'
    defaults = {'width': width, 'height': height, 'seed': int(options['seed']), 'seed_policy': options['seedPolicy']}
    if int(options['steps']):
        defaults['steps'] = int(options['steps'])
    document = {'schema': SCHEMA, 'name': board.doc['title'],
                'description': f'Converted from the CyTools Storyboard project "{board.doc["title"]}": one H3 '
                               f'generation per panel ({len(panels)} panels), joined with the storyboard transitions.',
                'inputs': {}, 'defaults': defaults, 'steps': steps, 'output': output,
                'source': {'storyboard': str(board.folder), 'options': options}}
    total = sum(s['seconds'] for s in summary) - sum(s['duration'] for s in seams if s['type'] != 'cut')
    return document, files, {'shots': summary, 'width': width, 'height': height, 'seconds': round(total, 3),
                             'generations': sum(s['generations'] for s in summary), 'steps': len(steps)}, warnings


def _digest(path, preview):
    import hashlib
    if preview:
        return hashlib.sha256(str(path).encode()).hexdigest()[:16]
    h = hashlib.sha256()
    with open(path, 'rb') as handle:
        for block in iter(lambda: handle.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()[:16]


def default_folder(board):
    return board.folder / 'exports' / 'h3_workflow' / _slug(board.doc['title'])


def export_workflow(board, target_dir, overrides=None):
    import tempfile
    workdir = Path(tempfile.mkdtemp(prefix='cystory-depth-'))
    try:
        document, files, summary, warnings = build(board, overrides, workdir=workdir)
        target = Path(target_dir)
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        for name, source in files.items():
            (target / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target / name)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    path = target / 'workflow.json'
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False), encoding='utf-8')
    (target / 'LISEZ-MOI.txt').write_text(
        f'{board.doc["title"]} - workflow CyTools_MiniMaxH3 : {len(summary["shots"])} plans, '
        f'{summary["generations"]} générations H3, {summary["seconds"]:.1f} s, {summary["width"]}x{summary["height"]}.\n\n'
        'Dans CyTools_MiniMaxH3 : onglet Workflows > Ouvrir... > workflow.json, puis Lancer. Ou en ligne de commande :\n'
        '  runtime\\python\\Scripts\\python.exe app\\tool.py invoke run_workflow --params '
        '"{\\"workflow\\": \\"<ce dossier>\\\\workflow.json\\"}"\n\n'
        'Les chemins des images, vidéos et sons (media/) sont relatifs à ce dossier : il peut être déplacé.\n'
        + ('\nRemarques :\n' + '\n'.join('  - ' + w for w in warnings) + '\n' if warnings else ''), encoding='utf-8')
    return dict(summary, folder=str(target), file=str(path), warnings=warnings)

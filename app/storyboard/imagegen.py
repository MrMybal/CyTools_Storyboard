"""Plans for generating reference pictures: what to ask the image model, from which references.

Nothing here touches a GPU. A plan is a list of requests, each one a prompt, the reference
pictures it is conditioned on (none for text-to-image), a size and a seed; the image engine
(storyboard/imageengine.py, a worker that keeps the model loaded) renders them, and
storyboard/comfy_image_workflow.py writes the same plan as ComfyUI workflows.

Four recipes:

  character   a set of views of one character (front, profile, back, face...) from its
              reference pictures, or from its description alone when it has none;
  location    views of a place from its reference pictures, empty or with a character in it;
  panel       the picture of a shot: the staging render gives the framing, the characters and
              the place of the panel give the look, the panel text gives the action;
  free        any prompt, with or without references.

How many reference pictures a request may carry and how its prompt names them ("image 1",
"<image1>") depend on the model: the caller passes `limit` and `token` (imageengine.reference_rules).

Every sentence and every view is a setting (`DEFAULTS`, saved in the project under
settings.imagegen). A generated picture keeps its recipe (prompt, references, seed, model,
steps) in the project under `generations`, so it can be made again identically.
"""
import copy
import hashlib
import math
import random
from pathlib import Path

from .model import IMAGE_SUFFIXES, StoryboardError

RECIPES = ('character', 'location', 'panel', 'free')
MAX_REFERENCES = 3          # when the model is not known: Qwen-Image-Edit reads up to three pictures
CHARACTER_PICTURES = 4      # most pictures of one character sent as references (when the model takes more than 3)
MEGAPIXELS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
FORMATS = ('project', '1:1', '3:4', '4:3', '2:3', '3:2', '9:16', '16:9', '21:9', '2.39:1')
RATIOS = {'1:1': 1.0, '3:4': 3 / 4, '4:3': 4 / 3, '2:3': 2 / 3, '3:2': 3 / 2, '9:16': 9 / 16, '16:9': 16 / 9,
          '21:9': 21 / 9, '2.39:1': 2.39, '2:1': 2.0}

MAX_LORAS = 8
GUIDES = ('auto', 'control', 'layout', 'both', 'none')
CONTROL_SOURCES = ('depth', 'pose', 'overlay')

CHARACTER_VIEWS = [
    {'key': 'front', 'on': True, 'format': '3:4',
     'text': 'Full body, standing straight, facing the camera, arms slightly away from the body.'},
    {'key': 'three_quarter', 'on': True, 'format': '3:4',
     'text': 'Full body, standing, three-quarter view, the body turned to the left.'},
    {'key': 'profile', 'on': True, 'format': '3:4', 'text': 'Full body, standing, strict side profile facing left.'},
    {'key': 'back', 'on': True, 'format': '3:4',
     'text': 'Rear view, full body: the character stands with its back to the camera, facing away; we see the back '
             'of the head, the back and the heels, never the face or the chest.'},
    {'key': 'face', 'on': True, 'format': '1:1', 'text': 'Close-up portrait of the head and shoulders, facing the camera.'},
    {'key': 'face_three_quarter', 'on': True, 'format': '1:1',
     'text': 'Close-up portrait of the head and shoulders, three-quarter view.'},
    {'key': 'face_profile', 'on': False, 'format': '1:1', 'text': 'Close-up portrait of the head, strict side profile.'},
    {'key': 'bust', 'on': False, 'format': '3:4', 'text': 'Medium shot from the waist up, facing the camera.'},
    {'key': 'walking', 'on': False, 'format': '3:4', 'text': 'Full body, walking towards the camera, natural stride.'},
    {'key': 'sitting', 'on': False, 'format': '3:4', 'text': 'Full body, sitting on the floor, knees up.'},
    {'key': 'hands', 'on': False, 'format': '1:1', 'text': 'Close-up of both hands raised in front of the chest.'},
]
LOCATION_VIEWS = [
    {'key': 'wide', 'on': True, 'format': 'project', 'text': 'Wide establishing shot of the whole place.'},
    {'key': 'reverse', 'on': True, 'format': 'project',
     'text': 'The same place seen from the opposite side, reverse angle.'},
    {'key': 'left', 'on': False, 'format': 'project', 'text': 'The same place seen from its left side.'},
    {'key': 'high', 'on': True, 'format': 'project', 'text': 'High angle overview of the place, from above.'},
    {'key': 'low', 'on': False, 'format': 'project', 'text': 'Low angle from the floor, looking up.'},
    {'key': 'detail', 'on': True, 'format': 'project', 'text': 'Close detail of the most characteristic element.'},
    {'key': 'entrance', 'on': False, 'format': 'project', 'text': 'The entrance of the place, seen from inside.'},
]

DEFAULTS = {
    'model': '', 'textModel': '',                 # '' = the default installed model of each kind
    'steps': 0, 'guidance': 0.0,                  # 0 = the model's own default (4 or 8 steps with its fast LoRA)
    'fast': True,                                 # few-step LoRA when the model has one
    'megapixels': 1.0, 'count': 1, 'seed': 0, 'randomSeed': True,
    'negative': '',
    # LoRA files of the loras folder applied to the model, in order: [{'file', 'strength', 'on'}].
    # A LoRA is made for one model family; its trigger words go in the prompt (or in "added to every picture").
    'loras': [],
    'includeStyle': True,
    'keepLoadedMinutes': 30,                      # 0 = until the application closes or "Unload"
    'server': '',                                 # '' = the application's own engine; else a ComfyUI address
    'characterViews': CHARACTER_VIEWS, 'locationViews': LOCATION_VIEWS,
    'characterText': 'The same character as in {pictures}{description}. {view} Plain neutral grey studio '
                     'background, soft even light. Keep exactly the same face, body, proportions, materials, colours '
                     'and details.',
    'characterFromText': '{name}{description}. {view} Plain neutral grey studio background, soft even light.',
    'locationText': 'The same place as in {pictures}{description}. {view} Keep exactly the same '
                    'architecture, materials, colours and light. No people.',
    'locationFromText': '{name}{description}. {view} No people.',
    'locationWithCharacterText': 'The character of {character} is in the place of {place}'
                                 '{description}. {view} Keep exactly the same character and the same place.',
    'panelText': '{framing}{people}{place}{text}',
    'panelFramingText': '{picture} is only a rough 3D layout: grey mannequins stand in for the characters and plain '
                        'blocks for the set. Keep its framing, its camera angle and the position and pose of every '
                        'figure, but replace every mannequin and every block with the real thing described here; '
                        'nothing grey, untextured or mannequin-like may remain. ',
    'panelExtrasText': 'Every other mannequin of the layout is another {name}, identical to {picture}. ',
    'panelUnknownText': 'The other mannequins are the figures the text describes, not mannequins. ',
    'panelCrowdText': 'Every other figure of the shot is another {name}, identical to {picture}. ',
    'panelCharacterText': '{name} is the character of {picture}{description}; keep it identical, with the same '
                          'body proportions and size as in its full-body picture. ',
    'panelCharacterPictures': 3,                  # pictures of each character sent for a shot or a place
    # How a 3D-staged shot gets its framing: 'control' sends the depth or the pose of the staging to the
    # model's ControlNet (no mannequin is ever shown to the model), 'layout' sends the staging render as a
    # picture, 'both', 'none'; 'auto' = control when the model has an installed ControlNet, else layout.
    'panelGuide': 'auto', 'panelControlSource': 'depth', 'panelControlStrength': 0.8, 'panelControlEnd': 0.6,
    'panelControlBlur': 'none',
    'panelLocationText': 'The place is the one of {picture}{description}. ',
    'panelFormat': 'project', 'freeFormat': 'project',
}
TEXTS = ('characterText', 'characterFromText', 'locationText', 'locationFromText', 'locationWithCharacterText',
         'panelText', 'panelFramingText', 'panelCharacterText', 'panelExtrasText', 'panelUnknownText', 'panelCrowdText',
         'panelLocationText')


def options_for(board, overrides=None):
    saved = (board.doc['settings'].get('imagegen') or {}) if board is not None else {}
    options = copy.deepcopy(DEFAULTS)
    options.update({k: copy.deepcopy(v) for k, v in saved.items() if k in DEFAULTS})
    for key, value in (overrides or {}).items():
        if key not in DEFAULTS:
            raise StoryboardError(f'Unknown image option {key!r}.')
        options[key] = copy.deepcopy(value)
    loras = options['loras']
    if not isinstance(loras, list) or len(loras) > MAX_LORAS or not all(
            isinstance(entry, dict) and isinstance(entry.get('file'), str) and entry['file'].strip()
            and Path(entry['file']).name == entry['file'] and -4 <= float(entry.get('strength', 1.0)) <= 4 for entry in loras):
        raise StoryboardError(f'loras is a list of at most {MAX_LORAS} {{file, strength, on}}; file is a name inside the '
                              'loras folder and strength goes from -4 to 4.')
    if not 0 <= int(options['steps']) <= 100:
        raise StoryboardError('steps goes from 0 (model default) to 100.')
    if not 0 <= float(options['guidance']) <= 20:
        raise StoryboardError('guidance goes from 0 (model default) to 20.')
    if not 0.25 <= float(options['megapixels']) <= 4.0:
        raise StoryboardError('megapixels goes from 0.25 to 4.')
    if not 1 <= int(options['count']) <= 16:
        raise StoryboardError('count goes from 1 to 16 pictures per view.')
    if options['panelGuide'] not in GUIDES:
        raise StoryboardError('panelGuide must be one of ' + ', '.join(GUIDES) + '.')
    if options['panelControlSource'] not in CONTROL_SOURCES:
        raise StoryboardError('panelControlSource must be one of ' + ', '.join(CONTROL_SOURCES) + '.')
    if options['panelControlBlur'] not in ('none', 'medium', 'strong'):
        raise StoryboardError('panelControlBlur must be none, medium or strong.')
    if not 0 < float(options['panelControlStrength']) <= 2 or not 0 < float(options['panelControlEnd']) <= 1:
        raise StoryboardError('The control strength goes up to 2 and its end from 0 to 1 (share of the steps).')
    if not 1 <= int(options['panelCharacterPictures']) <= 6:
        raise StoryboardError('panelCharacterPictures goes from 1 to 6.')
    if not 0 <= int(options['keepLoadedMinutes']) <= 24 * 60:
        raise StoryboardError('keepLoadedMinutes goes from 0 (until closed) to 1440.')
    for name in ('characterViews', 'locationViews'):
        views = options[name]
        if not isinstance(views, list) or not all(isinstance(v, dict) and v.get('key') and 'text' in v for v in views):
            raise StoryboardError(f'{name} is a list of {{key, text, on, format}}.')
        for view in views:
            if view.get('format', 'project') not in FORMATS:
                raise StoryboardError(f'{name}: unknown format {view.get("format")!r}.')
    for name in ('panelFormat', 'freeFormat'):
        if options[name] not in FORMATS:
            raise StoryboardError(f'{name} must be one of {", ".join(FORMATS)}.')
    return options


# ---------------------------------------------------------------------------- sizes and seeds
def size_for(board, fmt, megapixels=1.0, multiple=32):
    """(width, height) of about `megapixels` million pixels in the given format, on the model's grid."""
    if fmt == 'project':
        fmt = board.doc['settings']['aspect'] if board is not None else '16:9'
    ratio = RATIOS.get(fmt)
    if ratio is None:
        raise StoryboardError(f'Unknown picture format {fmt!r}.')
    area = float(megapixels) * 1_000_000
    width = math.sqrt(area * ratio)
    height = width / ratio
    snap = lambda value: max(multiple * 16, int(round(value / multiple)) * multiple)  # noqa: E731
    return snap(width), snap(height)


def seeds_for(options, count):
    """One seed per picture: the chosen seed and the following ones, or fresh random ones."""
    if options['randomSeed']:
        return [random.SystemRandom().randrange(1, 2 ** 31) for _ in range(count)]
    return [int(options['seed']) + index for index in range(count)]


# ---------------------------------------------------------------------------- references
def active_loras(options):
    """[(file name, strength)] of the LoRAs switched on, in order."""
    return [(entry['file'], float(entry.get('strength', 1.0))) for entry in options.get('loras') or []
            if entry.get('on', True) and float(entry.get('strength', 1.0)) != 0.0]


def _describe(item):
    text = (item.get('description') or '').strip().rstrip('.')
    return f' ({text})' if text else ''


def item_pictures(board, item, limit=MAX_REFERENCES):
    """The image files of a library item, in their order (the first one is its main picture)."""
    result = []
    for relative in item.get('files') or []:
        path = board.folder / relative
        if path.suffix.lower() in IMAGE_SUFFIXES and path.is_file():
            result.append(path)
    return result[:limit] if limit else result


def pictures_phrase(token, first, count):
    """'image 1', 'image 1 and image 2', '<image1>, <image2> and <image3>': how the prompt names the
    reference pictures first .. first + count - 1 for the model in use."""
    names = [token.format(n=n) for n in range(first, first + count)]
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


VIEW_PRIORITY = ('front', 'face', 'three_quarter', 'profile', 'face_three_quarter', 'back')


def character_pictures(board, item, count):
    """The pictures that best define a character, `count` at most: its first picture (the identity
    the user chose), then the views generated for it in the order that says most about it (full
    body front for the proportions, face, three-quarter, profile...), then its other pictures."""
    files = item_pictures(board, item, 0)
    if not files:
        return []
    generations = board.doc.get('generations') or {}
    chosen = [files[0]]
    for view in VIEW_PRIORITY:
        match = next((p for p in files[1:] if p not in chosen and (generations.get(p.name) or {}).get('key') == view), None)
        if match is not None:
            chosen.append(match)
    chosen += [p for p in files[1:] if p not in chosen]
    return chosen[:max(1, int(count))]


def _tokens(token, numbers):
    names = [token.format(n=n) for n in numbers]
    return names[0] if len(names) == 1 else ', '.join(names[:-1]) + ' and ' + names[-1]


def _fill(template, **values):
    try:
        return ' '.join(template.format(**values).split())
    except (KeyError, IndexError, ValueError) as exc:
        raise StoryboardError(f'Image text template {template[:40]!r}...: {exc}') from None


def _style(board, options):
    style = (board.doc['settings'].get('style') or '').strip() if board is not None else ''
    return style.rstrip('.') + '. ' if style and options['includeStyle'] else ''


def _views(options, name, wanted=None):
    views = [v for v in options[name] if (v['key'] in wanted if wanted else v.get('on', True))]
    if wanted:
        unknown = set(wanted) - {v['key'] for v in options[name]}
        if unknown:
            raise StoryboardError(f'Unknown view(s): {", ".join(sorted(unknown))}.')
        views.sort(key=lambda v: list(wanted).index(v['key']))
    if not views:
        raise StoryboardError('No view is selected.')
    return views


def _request(board, options, key, label, prompt, references, fmt, target):
    width, height = size_for(board, fmt, options['megapixels'])
    return {'key': key, 'label': label, 'prompt': prompt, 'negative': options['negative'].strip(),
            'references': [str(p) for p in references], 'width': width, 'height': height, 'target': target}


# ---------------------------------------------------------------------------- recipes
def plan_character(board, item_id, options, views=None, extra='', limit=MAX_REFERENCES, token='image {n}'):
    item = board.library_item(item_id)
    if item['kind'] != 'character':
        raise StoryboardError(f'{item["name"]} is not a character.')
    pictures = item_pictures(board, item, min(limit, CHARACTER_PICTURES))
    requests = []
    for view in _views(options, 'characterViews', views):
        text = ' '.join(x for x in (view['text'].strip(), extra.strip()) if x)
        if pictures:
            prompt = _fill(options['characterText'], name=item['name'], description=_describe(item), view=text,
                           s='s' if len(pictures) > 1 else '', n=len(pictures),
                           pictures=pictures_phrase(token, 1, len(pictures)))
        else:
            prompt = _fill(options['characterFromText'], name=item['name'], description=_describe(item), view=text)
        requests.append(_request(board, options, view['key'], f'{item["name"]} - {view["key"]}',
                                 _style(board, options) + prompt, pictures, view.get('format', '3:4'),
                                 {'kind': 'library', 'item': item['id']}))
    return requests


def plan_location(board, item_id, options, views=None, character='', extra='', limit=MAX_REFERENCES, token='image {n}'):
    item = board.library_item(item_id)
    if item['kind'] != 'location':
        raise StoryboardError(f'{item["name"]} is not a location.')
    person = board.library_item(character) if character else None
    if person is not None and person['kind'] != 'character':
        raise StoryboardError(f'{person["name"]} is not a character.')
    person_pictures = character_pictures(board, person, max(1, min(int(options['panelCharacterPictures']), limit - 1))) \
        if person else []
    if person is not None and not person_pictures:
        raise StoryboardError(f'{person["name"]} has no picture: generate or add one first.')
    pictures = item_pictures(board, item, max(1, min(limit - len(person_pictures), CHARACTER_PICTURES)))
    requests = []
    for view in _views(options, 'locationViews', views):
        text = ' '.join(x for x in (view['text'].strip(), extra.strip()) if x)
        if person is not None:
            if not pictures:
                raise StoryboardError(f'{item["name"]} has no picture: generate the empty place first.')
            prompt = _fill(options['locationWithCharacterText'], name=item['name'], description=_describe(item),
                           view=text, character=pictures_phrase(token, len(pictures) + 1, len(person_pictures)),
                           place=pictures_phrase(token, 1, len(pictures)), characterName=person['name'])
        elif pictures:
            prompt = _fill(options['locationText'], name=item['name'], description=_describe(item), view=text,
                           s='s' if len(pictures) > 1 else '', n=len(pictures),
                           pictures=pictures_phrase(token, 1, len(pictures)))
        else:
            prompt = _fill(options['locationFromText'], name=item['name'], description=_describe(item), view=text)
        requests.append(_request(board, options, view['key'], f'{item["name"]} - {view["key"]}',
                                 _style(board, options) + prompt, pictures + person_pictures,
                                 view.get('format', 'project'), {'kind': 'library', 'item': item['id']}))
    return requests


def stage_figures(board, panel):
    """What the mannequins of a panel's 3D stage stand for: (library characters they reference,
    number of mannequins that reference nobody). Objects hidden in this panel are left out."""
    layout = panel.get('layout') or {}
    stage = next((s for s in board.doc.get('stages') or [] if s['id'] == layout.get('stage')), None)
    if layout.get('mode') != '3d' or stage is None:
        return [], 0
    library = {item['id']: item for item in board.doc['library']}
    overrides = layout.get('overrides') or {}
    known, unknown = [], 0
    for thing in stage['objects']:
        if thing.get('shape') != 'mannequin' or (overrides.get(thing['id']) or {}).get('hidden'):
            continue
        item = library.get(thing.get('reference') or '')
        if item is not None and item['kind'] == 'character':
            if item not in known:
                known.append(item)
        else:
            unknown += 1
    return known, unknown


def panel_guide(board, panel, options, control_available):
    """(send the control picture, send the layout render) for a shot, from the panelGuide option:
    control needs a 3D staging and a model with a ControlNet."""
    layout = panel.get('layout') or {}
    can_control = bool(control_available) and layout.get('mode') == '3d' and bool(layout.get('stage'))
    guide = options['panelGuide']
    if guide == 'none':
        return False, False
    if guide == 'auto':
        return (True, False) if can_control else (False, True)
    if guide in ('control', 'both') and not can_control:
        raise StoryboardError('The structure guide needs a shot staged in 3D and a model with an installed ControlNet '
                              '(Images tab > Installation); choose the staging picture instead.')
    return guide in ('control', 'both'), guide in ('layout', 'both')


def plan_panel(board, panel_id, options, extra='', limit=MAX_REFERENCES, token='image {n}', extras='', control=False):
    """The picture of a shot. Its framing comes from the 3D staging, as a control picture (depth or
    pose, rendered when the picture is generated) and/or as the layout render sent as a picture;
    then the pictures of its characters, then the place."""
    from . import export
    from .h3film import _referenced
    _, _, panel = board.find(panel_id)
    references, framing, people, place = [], '', '', ''
    layout = panel.get('layout') or {}
    use_control, use_layout = panel_guide(board, panel, options, control)
    render = board.folder / layout['render'] if layout.get('mode') in ('2d', '3d') and layout.get('render') else None
    if use_layout and render is not None and render.is_file():
        references.append(render)
        framing = _fill(options['panelFramingText'], n=len(references), picture=token.format(n=len(references)).capitalize()
                        if token[:1].isalpha() else token.format(n=len(references))) + ' '
    used = _referenced(board, panel)
    staged, unknown = stage_figures(board, panel) if framing or use_control else ([], 0)

    same = board.library_item(extras) if extras else None
    if same is not None and same['kind'] != 'character':
        raise StoryboardError(f'{same["name"]} is not a character.')
    # the characters of the shot: those the panel names, those its mannequins stand for, and the one
    # every other mannequin is said to be
    people_items = [item for item in used if item['kind'] == 'character'] + staged + ([same] if same else [])
    characters = []
    for item in people_items:
        if item not in characters and item_pictures(board, item, 1):
            characters.append(item)
    tokens_of = {}
    has_place = any(item['kind'] == 'location' and item_pictures(board, item, 1) for item in used)
    for position, item in enumerate(characters):
        # room is kept for the place and for one picture of each character still to come
        room = limit - len(references) - (1 if has_place else 0) - (len(characters) - position - 1)
        pictures = character_pictures(board, item, min(int(options['panelCharacterPictures']), room)) if room > 0 else []
        if pictures:
            numbers = list(range(len(references) + 1, len(references) + len(pictures) + 1))
            references += pictures
            tokens_of[item['id']] = _tokens(token, numbers)
            people += _fill(options['panelCharacterText'], n=numbers[0], name=item['name'],
                            description=_describe(item), picture=_tokens(token, numbers)) + ' '
    if unknown and same is not None and same['id'] in tokens_of:
        # with the layout picture the sentence is about its mannequins; with the control picture alone the
        # model never sees a mannequin, only figures
        people += _fill(options['panelExtrasText' if framing else 'panelCrowdText'], name=same['name'],
                        picture=tokens_of[same['id']], count=unknown) + ' '
    elif unknown and framing:
        people += _fill(options['panelUnknownText'], count=unknown) + ' '
    for item in used:
        if item['kind'] == 'location' and len(references) < limit:
            pictures = item_pictures(board, item, 1)
            if pictures:
                references.append(pictures[0])
                place = _fill(options['panelLocationText'], n=len(references), name=item['name'],
                              description=_describe(item), picture=token.format(n=len(references))) + ' '
                break
    prompt = panel['prompt']
    parts = []
    shot = ' '.join(x for x in (prompt.get('shotSize'), prompt.get('angle') and f'({prompt["angle"]})') if x)
    if shot:
        parts.append(shot[0].upper() + shot[1:] + '.')
    parts += [export.sentence(prompt[key]) for key in ('scene', 'action') if prompt.get(key)]
    if prompt.get('lens'):
        parts.append(export.sentence(prompt['lens']))
    if extra.strip():
        parts.append(extra.strip())
    text = _fill(options['panelText'], framing=framing, people=people, place=place, text=' '.join(parts))
    if not text:
        raise StoryboardError(f'Panel "{panel["title"]}" has no text and no picture to start from.')
    request = _request(board, options, 'panel', panel['title'] or 'Panel', _style(board, options) + text, references,
                       options['panelFormat'], {'kind': 'panel', 'panel': panel['id']})
    if use_control:
        request['control'] = {'panel': panel['id'], 'source': options['panelControlSource'],
                              'strength': float(options['panelControlStrength']), 'end': float(options['panelControlEnd']),
                              'blur': options['panelControlBlur']}
    return [request]


def plan_free(board, prompt, options, references=(), fmt='', label='', limit=MAX_REFERENCES):
    if not (prompt or '').strip():
        raise StoryboardError('The prompt is empty.')
    paths = []
    for value in references:
        path = Path(value)
        if board is not None and not path.is_absolute():
            try:
                item = board.library_item(value)
            except StoryboardError:
                item = None
            if item is not None:
                paths += item_pictures(board, item, 1)
                continue
            path = board.folder / value
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            raise StoryboardError(f'{value}: not a picture.')
        paths.append(path)
    if len(paths) > limit:
        raise StoryboardError(f'{limit} reference picture(s) at most with this model.')
    return [_request(board, options, 'free', label or 'Picture', _style(board, options) + ' '.join(prompt.split()),
                     paths, fmt or options['freeFormat'], {'kind': 'none'})]


def plan(board, recipe, options, limit=MAX_REFERENCES, token='image {n}', control=False, **arguments):
    """The requests of a recipe, each repeated `count` times with its own seed (key, variant).
    limit: most reference pictures the model takes; token: how its prompts name picture n;
    control: whether the model can take a control picture (ControlNet installed)."""
    limit = max(1, int(limit))
    if recipe == 'character':
        requests = plan_character(board, arguments['item'], options, arguments.get('views'), arguments.get('extra', ''),
                                  limit, token)
    elif recipe == 'location':
        requests = plan_location(board, arguments['item'], options, arguments.get('views'),
                                 arguments.get('character', ''), arguments.get('extra', ''), limit, token)
    elif recipe == 'panel':
        requests = plan_panel(board, arguments['panel'], options, arguments.get('extra', ''), limit, token,
                              arguments.get('extras', ''), control)
    elif recipe == 'free':
        requests = plan_free(board, arguments.get('prompt', ''), options, arguments.get('references') or (),
                             arguments.get('format', ''), arguments.get('label', ''), limit)
    else:
        raise StoryboardError(f'recipe must be one of {", ".join(RECIPES)}.')
    count = int(options['count'])
    seeds = seeds_for(options, count)
    result = []
    for request in requests:
        for variant in range(count):
            entry = dict(request, seed=seeds[variant], variant=variant + 1,
                         mode='edit' if request['references'] else 'text')
            if active_loras(options):
                entry['loras'] = [list(item) for item in active_loras(options)]
            entry['id'] = hashlib.sha256(f'{entry["key"]}|{entry["prompt"]}|{entry["seed"]}|{entry["width"]}x'
                                         f'{entry["height"]}|{"|".join(entry["references"])}|'
                                         f'{sorted((entry.get("control") or {}).items())}|{entry.get("loras")}'
                                         .encode()).hexdigest()[:12]
            result.append(entry)
    return result


# ---------------------------------------------------------------------------- keeping results
def keep(board, picture, request, engine=None, attach=True):
    """Import a generated picture into the project, remember its recipe, and attach it to its
    target: appended to the library item's files, or set as the panel's first image."""
    relative = board.import_asset(picture)
    references = []
    for value in request.get('references') or []:
        path = Path(value)
        try:
            references.append(path.resolve().relative_to(board.folder.resolve()).as_posix())
        except ValueError:
            references.append(board.import_asset(path))
    recipe = {k: request[k] for k in ('key', 'label', 'prompt', 'negative', 'width', 'height', 'seed', 'mode') if k in request}
    if request.get('control'):
        recipe['control'] = {k: v for k, v in request['control'].items() if k != 'file'}
    if request.get('loras'):
        recipe['loras'] = request['loras']
    recipe.update(references=references, target=request.get('target', {'kind': 'none'}), engine=engine or {})
    board.doc.setdefault('generations', {})[Path(relative).name] = recipe
    target = request.get('target') or {}
    if attach and target.get('kind') == 'library':
        item = board.library_item(target['item'])
        if relative not in item.setdefault('files', []):
            item['files'].append(relative)
    elif attach and target.get('kind') == 'panel':
        _, _, panel = board.find(target['panel'])
        panel['images'] = [e for e in panel['images'] if e.get('role') != 'first' or e.get('file') == relative]
        if not any(e.get('file') == relative for e in panel['images']):
            panel['images'].insert(0, {'file': relative, 'role': 'first', 'caption': ''})
    return relative

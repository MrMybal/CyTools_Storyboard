"""Turn a storyboard into a multi-segment MiniMax H3 film (CyTools film file + ComfyUI workflows).

The film is a MiniMax H3 Timeline Director timeline of generation windows. By default the
panels of a sequence are grouped into windows of about 20 seconds (`grouping`,
`maxSegmentSeconds`, `maxShotsPerSegment`): H3 cuts between the shots of one window itself,
which keeps characters, places and sound continuous, and the window's prompt describes its
shots in order with their times. `grouping: panel` gives one window per panel instead.
A window may start a few frames before the previous one ends; those overlap frames carry
the previous latent into the next window (Drift-Control) and are removed at assembly. By
default they are used where the picture really continues (crossfades), not across cuts.
Every window gets its own pictures, numbered from <Picture 1>:

  1. identity pictures of the characters (those the shots use, or every character of
     the film in every window), so a face stays the same from one window to the next;
  2. the locations the shots reference;
  3. each shot's own picture(s): the 2D/3D layout render or the imported images;
  4. the objects and styles the shots reference.

Its prompt is the global prompt, one short line per picture, then the shots. Every sentence
is a setting, not a fixed rule; the defaults stay short because H3 also derives the sound
from the prompt. H3 takes 9 pictures per window at most; extra ones are listed as warnings.
Frame counts follow H3's grid: windows are 5 + 17n frames, overlaps 1 or 5 + 17n.
"""
import copy
import hashlib
import math
import json
import re
import shutil
from pathlib import Path

from . import export
from .model import StoryboardError

FPS = 24
FORMAT = 'cytools-h3-film'
MAX_PICTURES = 9
MAX_VIDEOS = 3
MAX_AUDIOS = 3
MAX_REFERENCES = 12   # H3: 12 reference files at most, pictures, videos and sounds together
MIN_REFERENCE_SECONDS = 5 / 24
MAX_SEGMENT_FRAMES = 3592
H3_TRAINED_SECONDS = 15.0
OVERLAPS = (0, 1, 5, 22, 39, 56, 73)
UPSCALER = 'minimax_h3_latent_upscaler_3d_conv_v1_fp16.safetensors'
TURBO_MODEL = 'minimax_h3_fused_refdelta_r1024_turbo8_mystic07_int8_convrot.safetensors'
CONTROL_PATCH = 'minimax_h3_fun_controlnet_union_2.0_pruned_int8_convrot.safetensors'
SHORT_EDGES = (384, 448, 512, 544, 576, 640, 704, 768)
GROUPINGS = ('panel', 'sequence', 'film')
# How the prompt of a grouped window moves from one shot to the next (the transition out of the earlier shot).
SHOT_TRANSITIONS = {'cut': 'Cut.', 'crossfade': 'Dissolve.', 'fade to black': 'Fade to black.',
                    'fade from black': 'Fade in from black.'}

DEFAULTS = {
    'shortEdge': 544, 'width': 0, 'height': 0,
    'grouping': 'sequence', 'maxSegmentSeconds': 20.0, 'maxShotsPerSegment': 0,
    'overlapFrames': 39, 'overlapOnCuts': False, 'overlapOnFades': False,
    'globalPrompt': '', 'includeStyle': True, 'includeDescription': False,
    'referenceNote': '',
    'continuityText': 'It continues directly from the previous shot.',
    'shotText': 'Shot {shot} ({start:.1f}-{end:.1f} s):',
    'dialogueText': '{name}{how} says: "{line}"',
    'soundText': 'Sound: {text}',
    'musicText': 'Music: {text}',
    'identityScope': 'panel', 'identityPictures': 1,
    'identityText': '<Picture {n}> is {name}{description}.',
    'identityMoreText': '<Picture {n}> is {name} again, from another angle.',
    'shotPictures': 'main',
    'layoutText': '<Picture {n}> is the framing of shot {shot}.',
    'sketchText': '<Picture {n}> is a sketch of shot {shot}.',
    'firstText': '<Picture {n}> is the first frame of shot {shot}.',
    'lastText': '<Picture {n}> is the last frame of shot {shot}.',
    'keyframeText': '<Picture {n}> is shot {shot} at {time:.1f} s.',
    'referenceText': '<Picture {n}> is a visual reference for shot {shot}.',
    'includeLocations': True,
    'locationText': '<Picture {n}> is {name}{description}.',
    'includeObjects': True,
    'objectText': '<Picture {n}> is {name}{description}.',
    'includeStyles': True,
    'styleText': '<Picture {n}> gives the visual style, not the content.',
    'includeSound': True,
    'includeVideos': True,
    'videoText': '<Video {n}> is a motion reference for {name}: follow its movement and camera, not its look.',
    'includeVoices': True,
    'voiceText': '<Audio {n}> is the voice of {name}.',
    'includeAudio': True,
    'audioText': '<Audio {n}> is a sound reference: {name}.',
    'videoSound': False,
    'videoSoundText': '<Audio {n}> is the sound of <Video {video}> ({name}).',
    'maxReferenceSeconds': 15.0,
    'secondPass': True, 'secondPassModel': UPSCALER, 'secondPassHighSteps': 2,
    # Only for the ComfyUI workflow written next to film.json (ModelPatchLoader, films with controls).
    'controlPatchModel': CONTROL_PATCH,
    'generatedAudio': True,
    'depthControl': 'indicative', 'controlSource': 'auto', 'controlStrength': 0.5, 'controlEnd': 0.5, 'controlBlur': 'medium',
    'poseHands': True, 'poseFeet': True,
}


def options_for(board, overrides=None):
    saved = board.doc['settings'].get('h3film') or {}
    options = dict(DEFAULTS, **{k: v for k, v in saved.items() if k in DEFAULTS})
    for key, value in (overrides or {}).items():
        if key not in DEFAULTS:
            raise StoryboardError(f'Unknown film option {key!r}.')
        options[key] = value
    if int(options['overlapFrames']) not in OVERLAPS:
        raise StoryboardError('overlapFrames must be one of ' + ', '.join(map(str, OVERLAPS)) + ' (H3 frame grid).')
    if options['grouping'] not in GROUPINGS:
        raise StoryboardError('grouping must be one of ' + ', '.join(GROUPINGS) + '.')
    if not 2.0 <= float(options['maxSegmentSeconds']) <= MAX_SEGMENT_FRAMES / FPS:
        raise StoryboardError(f'maxSegmentSeconds goes from 2 to {MAX_SEGMENT_FRAMES // FPS} seconds.')
    if int(options['maxShotsPerSegment']) < 0:
        raise StoryboardError('maxShotsPerSegment is 0 (no limit) or more.')
    if options['identityScope'] not in ('panel', 'film'):
        raise StoryboardError('identityScope must be "panel" or "film".')
    if not 1 <= int(options['identityPictures']) <= 6:
        raise StoryboardError('identityPictures goes from 1 to 6 pictures per character.')
    if options['shotPictures'] not in ('main', 'all', 'none'):
        raise StoryboardError('shotPictures must be "main", "all" or "none".')
    if not 2.0 <= float(options['maxReferenceSeconds']) <= 15.0:
        raise StoryboardError('maxReferenceSeconds goes from 2 to 15 seconds (H3 references).')
    if not 1 <= int(options['secondPassHighSteps']) <= 50:
        raise StoryboardError('secondPassHighSteps must be between 1 and 50.')
    from . import depthcontrol
    depthcontrol.settings(options)
    if options['controlSource'] not in depthcontrol.SOURCES:
        raise StoryboardError('controlSource must be one of ' + ', '.join(depthcontrol.SOURCES) + '.')
    return options


# ---------------------------------------------------------------------------- frame grid
def valid_overlap(frames):
    """H3 guides are 1 frame or 5 + 17n frames (Timeline Director's _valid_guide_frames)."""
    frames = int(frames)
    if frames <= 0:
        return 0
    if frames < 5:
        return 1
    return frames - ((frames - 5) % 17)


def segment_length(frames):
    """Nearest 5 + 17n frame count."""
    n = max(0, round((max(5, frames) - 5) / 17))
    return 5 + 17 * n


def canvas(board, options):
    if options['width'] and options['height']:
        width, height = int(options['width']), int(options['height'])
    else:
        ratios = {'16:9': 16 / 9, '21:9': 21 / 9, '2.39:1': 2.39, '4:3': 4 / 3, '1:1': 1.0, '9:16': 9 / 16,
                  '3:4': 3 / 4, '2:1': 2.0}
        ratio = ratios.get(board.doc['settings']['aspect'], 16 / 9)
        short = int(options['shortEdge'])
        width, height = (short * ratio, short) if ratio >= 1 else (short, short / ratio)
        # H3 was trained up to 768 x 1344 pixels; keep the same area budget for the short edge chosen.
        budget = 768 * 1344 * (short / 768) ** 2
        if width * height > budget:
            scale = (budget / (width * height)) ** 0.5
            width, height = width * scale, height * scale
    width, height = max(32, round(width / 32) * 32), max(32, round(height / 32) * 32)
    return int(width), int(height)


def group_panels(board, options):
    """The panels of each window, in order: one per panel, or consecutive panels of a sequence
    (or of the whole film) filling windows of about maxSegmentSeconds, balanced so a sequence
    of 23 s gives two windows of 11-12 s rather than 20 + 3."""
    if options['grouping'] == 'panel':
        return [[panel] for panel in board.panels()]
    runs = [sequence['panels'] for sequence in board.doc['sequences'] if sequence['panels']]
    if options['grouping'] == 'film':
        runs = [board.panels()] if board.panels() else []
    limit = float(options['maxSegmentSeconds'])
    shots = int(options['maxShotsPerSegment'])
    groups = []
    for run in runs:
        total = sum(float(p['duration']) for p in run)
        parts = max(1, math.ceil(total / limit - 1e-9), math.ceil(len(run) / shots) if shots else 1)
        target = total / parts
        group, seconds = [], 0.0
        for panel in run:
            duration = float(panel['duration'])
            full = seconds + duration > limit + 1e-9 or (shots and len(group) >= shots)
            balanced = seconds + duration / 2 > target and parts > 1
            if group and (full or balanced):
                groups.append(group)
                parts -= 1
                group, seconds = [], 0.0
            group.append(panel)
            seconds += duration
        if group:
            groups.append(group)
    return groups


def plan_segments(board, options):
    """Frame windows: [{'panel' (first), 'panels', 'shots', 'overlap', 'start', 'end', 'length',
    'visible', 'requested'}]; shots are (panel, start s, end s) inside the visible part."""
    wanted = int(options['overlapFrames'])
    segments, warnings, long_ones = [], [], []
    previous = None
    for index, panels in enumerate(group_panels(board, options)):
        requested = sum(float(p['duration']) for p in panels)
        visible = max(1, round(requested * FPS))
        overlap = 0
        if previous is not None and wanted:
            transition = previous['panels'][-1]['transition']['type']
            fade = transition in ('fade to black', 'fade from black')
            if (transition == 'cut' and options['overlapOnCuts']) or transition == 'crossfade' or \
                    (fade and options['overlapOnFades']):
                overlap = valid_overlap(min(wanted, previous['length'] - 1))
        length = segment_length(overlap + visible)
        if length <= overlap:
            length = segment_length(overlap + 17)
        if length > MAX_SEGMENT_FRAMES:
            raise StoryboardError(f'Segment {index + 1} is too long for one H3 segment (150 s at most).')
        start = 0 if previous is None else previous['end'] - overlap
        real = (length - overlap) / FPS
        shots, at = [], 0.0
        for number, panel in enumerate(panels):
            end = real if number == len(panels) - 1 else min(real, at + float(panel['duration']))
            shots.append((panel, at, end))
            at = end
        segment = {'panel': panels[0], 'panels': panels, 'shots': shots, 'number': index + 1, 'overlap': overlap,
                   'start': start, 'end': start + length, 'length': length, 'visible': length - overlap,
                   'requested': requested}
        if length / FPS > H3_TRAINED_SECONDS + 0.05:
            long_ones.append(f'{index + 1} ({length / FPS:.1f} s)')
        segments.append(segment)
        previous = segment
    if not segments:
        raise StoryboardError('The storyboard has no panel.')
    if long_ones:
        warnings.append(f'Segments {", ".join(long_ones)} last longer than the {H3_TRAINED_SECONDS:.0f} s H3 was '
                        'trained on; lower the segment length if motion or faces degrade.')
    return segments, warnings


def segment_title(board, segment):
    panels = segment['panels']
    if len(panels) == 1:
        return panels[0]['title']
    for sequence in board.doc['sequences']:
        if [p['id'] for p in sequence['panels']] == [p['id'] for p in panels]:
            return sequence.get('title') or panels[0]['title']
    return f'{panels[0]["title"]} - {panels[-1]["title"]}'


# ---------------------------------------------------------------------------- pictures
def _describe(item):
    text = (item.get('description') or '').strip().rstrip('.')
    return f' ({text})' if text else ''


def _referenced(board, panel):
    ids = list(panel['references'])
    for line in panel['prompt'].get('dialogue') or []:
        if line.get('speaker') and line['speaker'] not in ids:
            ids.append(line['speaker'])
    library = {item['id']: item for item in board.doc['library']}
    return [library[i] for i in ids if i in library]


def _film_characters(board):
    seen, result = set(), []
    for panel in board.panels():
        for item in _referenced(board, panel):
            if item['kind'] == 'character' and item['id'] not in seen and item['files']:
                seen.add(item['id'])
                result.append(item)
    return result


def _image_file(board, relative):
    path = board.folder / relative
    return path if path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.bmp') and path.is_file() else None


def shot_pictures(board, panel, options, shot=1):
    """[(path, template, extra format values)] for the panel's own pictures (shot `shot` of its window)."""
    if options['shotPictures'] == 'none':
        return []
    result = []
    layout = panel.get('layout') or {}
    if layout.get('mode') in ('2d', '3d') and layout.get('render'):
        render = _image_file(board, layout['render'])
        if render:
            result.append((render, options['layoutText'], {'shot': shot,
                                                           'label': f'{layout["mode"].upper()} layout, shot {shot}'}))
    order = {'first': 0, 'sketch': 1, 'keyframe': 2, 'reference': 3, 'last': 4}
    images = sorted(panel['images'], key=lambda e: (order.get(e['role'], 9), e.get('time', 0)))
    for entry in images:
        path = _image_file(board, entry['file'])
        if not path:
            continue
        template = options[{'sketch': 'sketchText', 'first': 'firstText', 'last': 'lastText',
                            'keyframe': 'keyframeText', 'reference': 'referenceText'}[entry['role']]]
        result.append((path, template, {'shot': shot, 'time': float(entry.get('time', 0.0)),
                                        'label': f'{entry["role"]}, shot {shot}'}))
    # A real first frame (imported or generated from the layout) says more than the mannequin render.
    result.sort(key=lambda entry: 0 if entry[2]['label'].startswith('first') else 1)
    if options['shotPictures'] == 'main':
        return result[:1]
    return result


def _referenced_all(board, panels):
    seen, result = set(), []
    for panel in panels:
        for item in _referenced(board, panel):
            if item['id'] not in seen:
                seen.add(item['id'])
                result.append(item)
    return result


def segment_pictures(board, panels, options, characters):
    """Ordered [(path, sentence template, values)] of a window and the list of pictures left out."""
    wanted = []
    referenced = _referenced_all(board, panels)
    identities = characters if options['identityScope'] == 'film' else \
        [item for item in referenced if item['kind'] == 'character' and item['files']]

    def library(kind, flag, template):
        if not options[flag]:
            return
        for item in referenced:
            if item['kind'] == kind and item['files']:
                path = _image_file(board, item['files'][0])
                if path:
                    wanted.append((path, options[template], {'name': item['name'], 'description': _describe(item),
                                                             'label': item['name']}))

    for item in identities:
        # the first picture of a character is its identity; the following ones (other angles, generated
        # in the Images tab) are added when identityPictures asks for more than one
        from .imagegen import character_pictures
        paths = character_pictures(board, item, int(options['identityPictures']))
        for position, path in enumerate(paths):
            wanted.append((path, options['identityMoreText' if position else 'identityText'],
                           {'name': item['name'], 'description': _describe(item),
                            'label': item['name'] + (f' ({position + 1})' if position else '')}))
    library('location', 'includeLocations', 'locationText')
    for shot, panel in enumerate(panels, start=1):
        wanted += shot_pictures(board, panel, options, shot)
    library('object', 'includeObjects', 'objectText')
    library('style', 'includeStyles', 'styleText')
    seen, kept = set(), []
    for entry in wanted:
        if entry[0] not in seen:
            seen.add(entry[0])
            kept.append(entry)
    return kept[:MAX_PICTURES], kept[MAX_PICTURES:]


# ---------------------------------------------------------------------------- videos and sounds
VIDEO_SUFFIXES = ('.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v')
AUDIO_SUFFIXES = ('.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac')
_PROBES = {}


def probe(path):
    """(duration in seconds or None, has an audio stream) read from FFmpeg's banner; cached."""
    import subprocess
    path = Path(path)
    stat = path.stat()
    key = (str(path), stat.st_size, stat.st_mtime_ns)
    if key not in _PROBES:
        import imageio_ffmpeg
        text = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-i', str(path)],
                              capture_output=True, text=True, errors='replace').stderr
        match = re.search(r'Duration: (\d+):(\d+):([\d.]+)', text)
        duration = int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3]) if match else None
        _PROBES[key] = (duration, bool(re.search(r'Stream #\S+.*Audio:', text)))
    return _PROBES[key]


def _media_file(board, item, suffixes):
    for relative in item.get('files') or []:
        path = board.folder / relative
        if path.suffix.lower() in suffixes and path.is_file():
            return path
    return None


def segment_videos(board, panels, options):
    """[(path, template, values)] for the video references of a window (3 at most); values['shot']
    is the index of the first shot that uses the video."""
    if not options['includeVideos']:
        return [], []
    wanted, seen = [], set()
    for shot, panel in enumerate(panels):
        for item in _referenced(board, panel):
            if item['kind'] == 'video' and item['id'] not in seen:
                path = _media_file(board, item, VIDEO_SUFFIXES)
                if path:
                    seen.add(item['id'])
                    wanted.append((path, options['videoText'], {'name': item['name'], 'description': _describe(item),
                                                               'label': item['name'], 'shot': shot}))
    return wanted[:MAX_VIDEOS], wanted[MAX_VIDEOS:]


def segment_audios(board, panels, options, videos, preview=False):
    """[(path, template, values)] for the sound references of a window (3 at most): character
    voices first, then audio items, then (optionally) the sound of the reference videos."""
    wanted = []
    referenced = _referenced_all(board, panels)
    if options['includeVoices']:
        for item in referenced:
            if item['kind'] == 'character':
                path = _media_file(board, item, AUDIO_SUFFIXES)
                if path:
                    wanted.append((path, options['voiceText'], {'name': item['name'], 'description': _describe(item),
                                                               'label': f'voice of {item["name"]}'}))
    if options['includeAudio']:
        for item in referenced:
            if item['kind'] == 'audio':
                path = _media_file(board, item, AUDIO_SUFFIXES + VIDEO_SUFFIXES)
                if path:
                    wanted.append((path, options['audioText'], {'name': item['name'],
                                                               'description': _describe(item), 'label': item['name']}))
    if options['videoSound']:
        for number, (path, _, values) in enumerate(videos, start=1):
            if preview or probe(path)[1]:
                wanted.append((path, options['videoSoundText'], dict(values, video=number,
                                                                     label=f'sound of {values["name"]}')))
    seen, kept = set(), []
    for entry in wanted:
        if entry[0] not in seen:
            seen.add(entry[0])
            kept.append(entry)
    return kept[:MAX_AUDIOS], kept[MAX_AUDIOS:]


# ---------------------------------------------------------------------------- prompts
def global_prompt(board, options):
    parts = []
    if options['includeStyle'] and board.doc['settings'].get('style'):
        parts.append(board.doc['settings']['style'].strip().rstrip('.') + '.')
    if options['includeDescription'] and board.doc.get('description'):
        parts.append(board.doc['description'].strip())
    if options['globalPrompt'].strip():
        parts.append(options['globalPrompt'].strip())
    if options['referenceNote'].strip():
        parts.append(options['referenceNote'].strip())
    return ' '.join(parts)


def _fill(template, number, values):
    try:
        return template.format(n=number, **values)
    except (KeyError, IndexError, ValueError) as exc:
        raise StoryboardError(f'Film text template {template[:40]!r}...: {exc}') from None


def shot_text(board, panel, options):
    """One shot as prompt prose: framing, scene, action, camera, lines, free text, sound and music.
    Consecutive lines of one speaker are joined so the voice reads them as one speech."""
    prompt = panel['prompt']
    names = {item['id']: item['name'] for item in board.doc['library']}
    parts = []
    shot = ' '.join(x for x in (prompt.get('shotSize'), prompt.get('angle') and f'({prompt["angle"]})') if x)
    if shot:
        parts.append(shot[0].upper() + shot[1:] + '.')
    for key in ('scene', 'action'):
        if prompt.get(key):
            parts.append(export.sentence(prompt[key]))
    camera = export.describe_camera(prompt)
    if camera:
        parts.append(camera)
    speeches = []
    for line in prompt.get('dialogue') or []:
        text = (line.get('line') or '').strip()
        if not text:
            continue
        name = names.get(line.get('speaker'), line.get('speaker') or '')
        how = ', '.join(x for x in ('off screen' if line.get('offScreen') else '', (line.get('delivery') or '').strip()) if x)
        key = (name, how)
        if speeches and speeches[-1][0] == key:
            speeches[-1][1].append(text)
        else:
            speeches.append((key, [text]))
    for (name, how), lines in speeches:
        joined = ' '.join(lines)
        if name:
            parts.append(_fill(options['dialogueText'], 0, {'name': name, 'how': f' ({how})' if how else '',
                                                           'line': joined}))
        else:
            parts.append(f'"{joined}"')
    if prompt.get('freeText'):
        parts.append(export.sentence(prompt['freeText']))
    if options['includeSound']:
        for key, template in (('sound', 'soundText'), ('music', 'musicText')):
            if prompt.get(key) and options[template].strip():
                parts.append(_fill(options[template], 0, {'text': export.sentence(prompt[key])}))
    return ' '.join(parts)


def segment_prompt(board, segment, media, options, head):
    """media: {'pictures': [...], 'videos': [...], 'audios': [...]} of (path, template, values)."""
    parts = []
    if segment['overlap'] and options['continuityText'].strip():
        parts.append(_fill(options['continuityText'], 0, {'frames': segment['overlap'],
                                                         'seconds': segment['overlap'] / FPS}))
    for kind in ('pictures', 'videos', 'audios'):
        parts += [_fill(template, number, values) for number, (_, template, values)
                  in enumerate(media.get(kind) or [], start=1)]
    shots = segment['shots']
    lines = [' '.join(parts)] if parts else []
    for index, (panel, start, end) in enumerate(shots):
        text = shot_text(board, panel, options)
        if len(shots) > 1:
            header = _fill(options['shotText'], 0, {'shot': index + 1, 'start': start, 'end': end,
                                                    'title': panel['title']}) if options['shotText'].strip() else ''
            if index:
                header = (SHOT_TRANSITIONS.get(shots[index - 1][0]['transition']['type'], 'Cut.') + ' ' + header).strip()
            text = (header + ' ' + text).strip()
        if text:
            lines.append(text)
    body = '\n'.join(lines)
    return (head + '\n\n' + body).strip() if head else body


# ---------------------------------------------------------------------------- film
def _slug(text):
    return re.sub(r'[^\w\-]+', '_', text or 'film', flags=re.UNICODE).strip('_')[:60] or 'film'


def segment_depth_samples(board, segments, index):
    """Control frames of a film segment: its carried opening frames hold the end of the previous
    panel (when that one is staged in 3D, else this segment's first panel), then each shot's move
    for the shot's own frames."""
    from . import depthcontrol
    segment = segments[index]
    first = segment['panels'][0]
    previous = segments[index - 1]['panels'][-1] if index else None
    held = (previous, 1.0) if previous is not None and depthcontrol.staged(board, previous) is not None else (first, 0.0)
    samples = [held] * segment['overlap']
    visible = segment['length'] - segment['overlap']
    for number, (panel, start, end) in enumerate(segment['shots']):
        frames = visible - (len(samples) - segment['overlap']) if number == len(segment['shots']) - 1 else \
            max(0, round(end * FPS) - round(start * FPS))
        samples += depthcontrol.panel_samples(panel, frames)
    return samples


def segment_control_source(board, panels, options):
    """The control source of a window, or '' when one of its shots is not staged in 3D.
    auto: pose when every shot shows a character, depth when none does, overlay when mixed."""
    from . import depthcontrol
    if any(depthcontrol.staged(board, panel) is None for panel in panels):
        return ''
    if options.get('controlSource', 'auto') != 'auto' or len(panels) == 1:
        return depthcontrol.source_for(board, panels[0], options)
    sources = {depthcontrol.source_for(board, panel, options) for panel in panels}
    return sources.pop() if len(sources) == 1 else 'overlay'


def build(board, overrides=None, preview=False, workdir=None):
    """The film document (paths relative to its folder), the pictures to copy, a summary and warnings.
    `preview` skips reading the pictures (ids from their paths), for a live table in the window."""
    from PIL import Image
    from . import depthcontrol
    options = options_for(board, overrides)
    control = depthcontrol.settings(options)
    width, height = canvas(board, options)
    segments, warnings = plan_segments(board, options)
    head = global_prompt(board, options)
    characters = _film_characters(board)
    assets, files = {}, {}

    def digest_of(path):
        if preview:
            return hashlib.sha256(str(path).encode()).hexdigest()[:16]
        h = hashlib.sha256()
        with open(path, 'rb') as handle:
            for block in iter(lambda: handle.read(1 << 20), b''):
                h.update(block)
        return h.hexdigest()[:16]

    def asset(path):
        key = str(path)
        if key not in assets:
            digest = digest_of(path)
            if preview:
                size = (0, 0)
            else:
                with Image.open(path) as image:
                    size = image.size
            name = f'{digest}{path.suffix.lower()}'
            assets[key] = {'id': 'img-' + digest, 'file': 'images/' + name, 'name': path.stem,
                           'width': size[0], 'height': size[1]}
            files['images/' + name] = path
        return assets[key]

    limit = float(options['maxReferenceSeconds'])

    def media_file(path):
        name = 'media/' + digest_of(path) + path.suffix.lower()
        files[name] = path
        return name

    def sound(path, label):
        """A standalone reference sound (Timeline Director 'audios' asset), shared by segments."""
        key = str(path)
        if key not in sounds:
            duration = limit if preview else probe(path)[0]
            name = media_file(path)
            entry = {'id': 'aud-' + Path(name).stem, 'file': name, 'name': label, 'audioMode': 'reference',
                     'trimStart': 0.0}
            if duration is None or duration > limit:
                entry['duration'] = limit
            if duration is not None and duration < 2.0:
                warnings.append(f'{path.name}: {duration:.1f} s; H3 sound references should last 2 to 15 s.')
            sounds[key] = entry
        return sounds[key]['id']

    sounds, clips = {}, []
    timeline_segments, summary = [], []
    for segment in segments:
        panel, panels, number = segment['panel'], segment['panels'], segment['number']
        title = segment_title(board, segment)
        label = f'Segment {number} "{title}"'
        pictures, dropped = segment_pictures(board, panels, options, characters)
        videos, extra_videos = segment_videos(board, panels, options)
        audios, extra_audios = segment_audios(board, panels, options, videos, preview)
        # H3 takes 12 reference files at most: the least important pictures give way first.
        while len(pictures) + len(videos) + len(audios) > MAX_REFERENCES and len(pictures) > 1:
            dropped.append(pictures.pop())
        if dropped:
            warnings.append(f'{label}: {len(dropped)} picture(s) left out (H3 takes {MAX_PICTURES} pictures and '
                            f'{MAX_REFERENCES} references in all per segment).')
        if extra_videos or extra_audios:
            warnings.append(f'{label}: {len(extra_videos)} video(s) and {len(extra_audios)} sound(s) left out '
                            f'(H3 takes {MAX_VIDEOS} of each per segment).')
        if audios and not (pictures or videos):
            warnings.append(f'{label}: H3 needs a picture or a video next to a sound reference.')
        # A reference video sits inside its own segment on the timeline, after the carried
        # frames, marked with its segment so the film plan keeps it out of the other segments.
        kept_videos = []
        for index, (path, template, values) in enumerate(videos):
            # the clip starts with the first shot that uses it
            shot_start = segment['shots'][values.get('shot', 0)][1]
            start_seconds = (segment['start'] + segment['overlap']) / FPS + shot_start
            room = (segment['end'] - segment['start'] - segment['overlap']) / FPS - shot_start
            duration = limit if preview else (probe(path)[0] or limit)
            duration = min(duration, limit, room)
            if duration < MIN_REFERENCE_SECONDS:
                warnings.append(f'{label}: {path.name} is too short to be a video reference.')
                continue
            name = media_file(path)
            clips.append({'id': f'vid-{Path(name).stem}-s{number}-{index}', 'file': name, 'name': values['name'],
                          'start': round(start_seconds, 6),
                          # rounded down so the clip never ends past its segment
                          'duration': math.floor(min(duration, room - (round(start_seconds, 6) - start_seconds)) * 1e6) / 1e6,
                          'trimStart': 0.0,
                          'referenceMode': 'edit', 'hasAudio': False, 'cytoolsSegment': number})
            kept_videos.append((path, template, values))
        videos = kept_videos
        media = {'pictures': pictures, 'videos': videos, 'audios': audios}
        prompt = segment_prompt(board, segment, media, options, head)
        window = {'startFrame': segment['start'], 'endFrame': segment['end'],
                  'images': [asset(path)['id'] for path, _, _ in pictures],
                  'audios': [sound(path, values['label']) for path, _, values in audios], 'prompt': prompt}
        source = segment_control_source(board, panels, options) if control else ''
        if source:
            name = f'media/{source}_{panel["id"]}_s{number}.mp4'
            if not preview:
                if workdir is None:
                    raise StoryboardError('Rendering depth videos needs a working folder (use export_film).')
                files[name] = depthcontrol.write_video(board, segment_depth_samples(board, segments, number - 1),
                                                       Path(workdir) / Path(name).name, (width, height),
                                                       control['blur'], source, hands=bool(options['poseHands']),
                                                       feet=bool(options['poseFeet']))
            # Read by CyTools H3 Film Plan (Timeline Director ignores it): Fun ControlNet on this segment.
            window['cytoolsControl'] = {'file': name, 'strength': control['strength'], 'start': control['start'],
                                        'end': control['end']}
        timeline_segments.append(window)
        summary.append({'panel': panel['id'], 'panels': [p['id'] for p in panels], 'number': number, 'title': title,
                        'shots': [{'panel': p['id'], 'title': p['title'], 'start': round(s, 3), 'end': round(e, 3)}
                                  for p, s, e in segment['shots']],
                        'startFrame': segment['start'], 'endFrame': segment['end'], 'length': segment['length'],
                        'overlap': segment['overlap'], 'requestedSeconds': segment['requested'],
                        'seconds': segment['visible'] / FPS,
                        'pictures': [f'<Picture {n}> {values["label"]}' for n, (_, _, values) in
                                     enumerate(pictures, start=1)],
                        'videos': [f'<Video {n}> {values["label"]}' for n, (_, _, values) in
                                   enumerate(videos, start=1)],
                        'audios': [f'<Audio {n}> {values["label"]}' for n, (_, _, values) in
                                   enumerate(audios, start=1)], 'prompt': prompt,
                        'depthControl': 'cytoolsControl' in window, 'controlSource': source})
    total = segments[-1]['end']
    timeline = {
        'version': 9, 'fps': FPS, 'globalPrompt': head,
        'secondPass': bool(options['secondPass']), 'secondPassModel': options['secondPassModel'],
        'secondPassHighSteps': int(options['secondPassHighSteps']),
        'selection': {'start': 0, 'duration': total / FPS}, 'videoAudioEnabled': bool(options['generatedAudio']),
        'videoClips': clips, 'images': list(assets.values()), 'audios': list(sounds.values()),
        'segmentConfig': {'count': len(timeline_segments), 'activeIndex': 0, 'mode': 'timeline',
                          'segments': timeline_segments},
    }
    film = {'format': FORMAT, 'version': 1, 'title': board.doc['title'], 'fps': FPS, 'width': width,
            'height': height, 'frames': total, 'seconds': total / FPS, 'timeline': timeline, 'segments': summary,
            'source': {'storyboard': str(board.folder), 'options': options}}
    return film, files, warnings


def export_film(board, target_dir, overrides=None, workflows=True):
    """Write film.json, images/ and ComfyUI workflows into `target_dir` (replaced when it holds an
    earlier export; any other non-empty folder is refused, never emptied)."""
    import tempfile
    target = Path(target_dir)
    if target.is_dir() and any(target.iterdir()) and not (target / 'film.json').is_file():
        raise StoryboardError(f'{target} is not empty and holds no earlier film export: choose another folder '
                              '(each film is written into a folder of its own).')
    workdir = Path(tempfile.mkdtemp(prefix='cystory-depth-'))
    try:
        film, files, warnings = build(board, overrides, workdir=workdir)
        target = Path(target_dir)
        if target.exists():
            shutil.rmtree(target)
        (target / 'images').mkdir(parents=True)
        for name, source in files.items():
            (target / name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target / name)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    (target / 'film.json').write_text(json.dumps(film, indent=1, ensure_ascii=False), encoding='utf-8')
    written = [target / 'film.json']
    if workflows:
        from . import comfy_workflow
        folder = comfy_input_folder(target)
        disk = comfy_workflow.film_sampler_workflow(film, folder + '/film.json',
                                                    control_patch=options_for(board, overrides)['controlPatchModel'])
        stock = comfy_workflow.timeline_director_workflow(film, folder)
        for name, data in (('workflow_cytools_film.json', disk), ('workflow_timeline_director.json', stock)):
            (target / name).write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
            written.append(target / name)
        (target / 'LISEZ-MOI.txt').write_text(readme(film, target.name, warnings), encoding='utf-8')
    return {'folder': str(target), 'files': [str(p) for p in written], 'segments': film['segments'],
            'frames': film['frames'], 'seconds': film['seconds'], 'width': film['width'], 'height': film['height'],
            'warnings': warnings}


def comfy_input_folder(target):
    """Where the export sits for ComfyUI: its path under an `input` folder when it is written
    into one (ComfyUI/input/..., a Drive copy of it), else input/cytools_film/<name>."""
    parts = Path(target).resolve().parts
    for index in range(len(parts) - 1, -1, -1):
        if parts[index].lower() == 'input' and index < len(parts) - 1:
            return '/'.join(parts[index + 1:])
    return 'cytools_film/' + Path(target).name


def films_folder_target(board, films_folder):
    """The export folder of this board inside a chosen films folder (one folder per film)."""
    return Path(films_folder) / _slug(board.doc['title'])


def default_folder(board):
    return board.folder / 'exports' / 'h3_film' / _slug(board.doc['title'])


def readme(film, name, warnings):
    lines = [
        f'{film["title"]} - film MiniMax H3 en {len(film["segments"])} segments, {film["seconds"]:.1f} s, '
        f'{film["width"]}x{film["height"]}', '',
        'Avec CyTools_MiniMaxH3 : onglet Film, ouvrir film.json (le Tool envoie tout au GPU Colab).', '',
        'Dans ComfyUI :',
        f'  1. Copier ce dossier dans ComfyUI/input/cytools_film/ (il doit devenir input/cytools_film/{name}/).',
        '  2. Installer ComfyUI-MiniMaxH3-TimelineDirector et ComfyUI-CyTools-H3Film dans custom_nodes/.',
        f'  3. Modèles : diffusion_models/{TURBO_MODEL} (MATLOWAI/minimax-h3-fused-turbo-int8-convrot),',
        '     text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors, vae/minimax_h3_video_vae_fp16.safetensors,',
        '     vae/minimax_h3_audio_vae_fp32.safetensors (Comfy-Org/MiniMax-H3),',
        f'     latent_upscale_models/{UPSCALER} (LBH-123-AI/Minimax_h3_latent_Upscaler).',
        '  4. Charger workflow_cytools_film.json (rendu segment par segment sur disque, reprise, réutilisation des',
        '     segments inchangés) ou workflow_timeline_director.json (nœuds du pack TimelineDirector seulement ;',
        '     tout le film reste en mémoire).', '',
        'Licence : les poids MiniMax H3 suivent la MiniMax H3 Community License (territoire applicable : ni UE,',
        'ni Royaume-Uni, ni Corée du Sud, ni États-Unis sans licence séparée).',
    ]
    if film['timeline']['videoClips']:
        lines += ['', 'Vidéos de référence : chaque vidéo appartient à un seul segment. Seul le nœud CyTools H3 Film Plan',
                  "le respecte ; workflow_timeline_director.json est écrit sans elles (Timeline Director y verrait une",
                  'vidéo globale : images forcées dans les segments voisins).']
    if warnings:
        lines += ['', 'Remarques :'] + ['  - ' + w for w in warnings]
    return '\n'.join(lines) + '\n'

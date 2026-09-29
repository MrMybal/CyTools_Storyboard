"""Turn a storyboard into a multi-segment MiniMax H3 film (CyTools film file + ComfyUI workflows).

The film is a MiniMax H3 Timeline Director timeline: one generation window per panel, in
order, each one starting a few frames before the previous one ends. Those overlap frames
carry the previous segment's latent into the next one (Drift-Control), so places,
characters, light and sound continue across cuts; they are removed at assembly. Every
segment gets its own pictures, numbered from <Picture 1>:

  1. identity pictures of the characters (those the panel uses, or every character of
     the film in every segment), so a face stays the same from one segment to the next;
  2. the shot's own picture(s): the 2D/3D layout render or the imported images;
  3. the locations, objects and styles the panel references.

Its prompt is the global prompt, a sentence about the carried opening frames, one line per
picture saying what it is for, then the panel's text. Every sentence is a setting, not a
fixed rule. H3 takes 9 pictures per segment at most; extra ones are listed as warnings.
Frame counts follow H3's grid: segments are 5 + 17n frames, overlaps 1 or 5 + 17n.
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

DEFAULTS = {
    'shortEdge': 544, 'width': 0, 'height': 0,
    'overlapFrames': 39, 'overlapOnCuts': True, 'overlapOnFades': False,
    'globalPrompt': '', 'includeStyle': True, 'includeDescription': False,
    'referenceNote': 'Reference pictures are visual guides, not frozen frames; generate natural movement. '
                     'Keep every character, place and object consistent across the whole film.',
    'continuityText': 'The first {frames} frames continue the preceding segment and serve as overlap context; '
                      'they will be removed from this segment in the final edit. After this prefix, perform the '
                      'new shot described below.',
    'identityScope': 'panel',
    'identityText': '<Picture {n}> defines the exact identity of {name}: face, body, clothing and distinguishing '
                    'marks{description}. It takes precedence over any other picture for {name}.',
    'shotPictures': 'main',
    'layoutText': '<Picture {n}> is a rough layout of this shot: follow its framing, camera angle and the placement '
                  'of people and objects, not its drawing style or its simple shapes.',
    'sketchText': '<Picture {n}> is a sketch of this shot: follow its composition, not its drawing style.',
    'firstText': '<Picture {n}> shows how this shot begins.',
    'lastText': '<Picture {n}> shows how this shot ends.',
    'keyframeText': '<Picture {n}> shows this shot at {time:.1f} s.',
    'referenceText': '<Picture {n}> is a visual reference for this shot.',
    'includeLocations': True,
    'locationText': '<Picture {n}> shows {name}{description}; keep this place identical whenever it appears.',
    'includeObjects': True,
    'objectText': '<Picture {n}> shows {name}{description}.',
    'includeStyles': True,
    'styleText': '<Picture {n}> gives the visual style ({name}{description}), not the content.',
    'includeSound': True,
    'includeVideos': True,
    'videoText': '<Video {n}> is a motion reference, {name}{description}: follow its movement, action and camera, '
                 'not its exact appearance.',
    'includeVoices': True,
    'voiceText': "<Audio {n}> is the voice of {name}; use it for {name}'s lines.",
    'includeAudio': True,
    'audioText': '<Audio {n}> is a sound reference: {name}{description}.',
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
    if options['identityScope'] not in ('panel', 'film'):
        raise StoryboardError('identityScope must be "panel" or "film".')
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


def plan_segments(board, options):
    """Frame windows: [{'panel', 'overlap', 'start', 'end', 'length', 'visible', 'requested'}]."""
    panels = board.panels()
    wanted = int(options['overlapFrames'])
    segments, warnings = [], []
    previous = None
    for index, panel in enumerate(panels):
        visible = max(1, round(float(panel['duration']) * FPS))
        overlap = 0
        if previous is not None and wanted:
            transition = previous['panel']['transition']['type']
            fade = transition in ('fade to black', 'fade from black')
            if (transition == 'cut' and options['overlapOnCuts']) or transition == 'crossfade' or \
                    (fade and options['overlapOnFades']):
                overlap = valid_overlap(min(wanted, previous['length'] - 1))
        length = segment_length(overlap + visible)
        if length <= overlap:
            length = segment_length(overlap + 17)
        if length > MAX_SEGMENT_FRAMES:
            raise StoryboardError(f'Panel {index + 1} is too long for one H3 segment (150 s at most).')
        start = 0 if previous is None else previous['end'] - overlap
        segment = {'panel': panel, 'number': index + 1, 'overlap': overlap, 'start': start, 'end': start + length,
                   'length': length, 'visible': length - overlap, 'requested': float(panel['duration'])}
        if length / FPS > H3_TRAINED_SECONDS + 0.05:
            warnings.append(f'Panel {index + 1} "{panel["title"]}": its segment lasts {length / FPS:.1f} s, beyond '
                            f'the {H3_TRAINED_SECONDS:.0f} s H3 was trained on; split the panel if motion degrades.')
        segments.append(segment)
        previous = segment
    if not segments:
        raise StoryboardError('The storyboard has no panel.')
    return segments, warnings


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


def shot_pictures(board, panel, options):
    """[(path, template, extra format values)] for the panel's own pictures."""
    if options['shotPictures'] == 'none':
        return []
    result = []
    layout = panel.get('layout') or {}
    if layout.get('mode') in ('2d', '3d') and layout.get('render'):
        render = _image_file(board, layout['render'])
        if render:
            result.append((render, options['layoutText'], {'label': f'{layout["mode"].upper()} layout'}))
    order = {'first': 0, 'sketch': 1, 'keyframe': 2, 'reference': 3, 'last': 4}
    images = sorted(panel['images'], key=lambda e: (order.get(e['role'], 9), e.get('time', 0)))
    for entry in images:
        path = _image_file(board, entry['file'])
        if not path:
            continue
        template = options[{'sketch': 'sketchText', 'first': 'firstText', 'last': 'lastText',
                            'keyframe': 'keyframeText', 'reference': 'referenceText'}[entry['role']]]
        result.append((path, template, {'time': float(entry.get('time', 0.0)), 'label': entry['role']}))
    if options['shotPictures'] == 'main':
        return result[:1]
    return result


def segment_pictures(board, panel, options, characters):
    """Ordered [(path, sentence template, values)] and the list of pictures left out."""
    wanted = []
    referenced = _referenced(board, panel)
    identities = characters if options['identityScope'] == 'film' else \
        [item for item in referenced if item['kind'] == 'character' and item['files']]
    for item in identities:
        path = _image_file(board, item['files'][0])
        if path:
            wanted.append((path, options['identityText'], {'name': item['name'], 'description': _describe(item),
                                                           'label': item['name']}))
    wanted += shot_pictures(board, panel, options)
    for kind, flag, template in (('location', 'includeLocations', 'locationText'),
                                 ('object', 'includeObjects', 'objectText'),
                                 ('style', 'includeStyles', 'styleText')):
        if not options[flag]:
            continue
        for item in referenced:
            if item['kind'] == kind and item['files']:
                path = _image_file(board, item['files'][0])
                if path:
                    wanted.append((path, options[template], {'name': item['name'], 'description': _describe(item),
                                                             'label': item['name']}))
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


def segment_videos(board, panel, options):
    """[(path, template, values)] for the video references of a panel (3 at most)."""
    if not options['includeVideos']:
        return [], []
    wanted = []
    for item in _referenced(board, panel):
        if item['kind'] == 'video':
            path = _media_file(board, item, VIDEO_SUFFIXES)
            if path:
                wanted.append((path, options['videoText'], {'name': item['name'], 'description': _describe(item),
                                                           'label': item['name']}))
    return wanted[:MAX_VIDEOS], wanted[MAX_VIDEOS:]


def segment_audios(board, panel, options, videos, preview=False):
    """[(path, template, values)] for the sound references of a panel (3 at most): character
    voices first, then audio items, then (optionally) the sound of the reference videos."""
    wanted = []
    referenced = _referenced(board, panel)
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


def segment_prompt(board, segment, media, options, head):
    """media: {'pictures': [...], 'videos': [...], 'audios': [...]} of (path, template, values)."""
    panel = segment['panel']
    parts = []
    if segment['overlap'] and options['continuityText'].strip():
        parts.append(_fill(options['continuityText'], 0, {'frames': segment['overlap'],
                                                         'seconds': segment['overlap'] / FPS}))
    for kind in ('pictures', 'videos', 'audios'):
        parts += [_fill(template, number, values) for number, (_, template, values)
                  in enumerate(media.get(kind) or [], start=1)]
    text = export.panel_text(board, panel)
    if text:
        parts.append(text)
    if options['includeSound']:
        for key, label in (('sound', 'Sound'), ('music', 'Music')):
            if panel['prompt'].get(key):
                parts.append(f'{label}: {export.sentence(panel["prompt"][key])}')
    body = ' '.join(parts)
    return (head + '\n\n' + body).strip() if head else body


# ---------------------------------------------------------------------------- film
def _slug(text):
    return re.sub(r'[^\w\-]+', '_', text or 'film', flags=re.UNICODE).strip('_')[:60] or 'film'


def segment_depth_samples(board, segments, index):
    """Depth frames of a film segment: its carried opening frames hold the end of the previous
    panel (when that one is staged in 3D, else this panel's start), then this panel's move."""
    from . import depthcontrol
    segment = segments[index]
    panel = segment['panel']
    previous = segments[index - 1]['panel'] if index else None
    held = (previous, 1.0) if previous is not None and depthcontrol.staged(board, previous) is not None else (panel, 0.0)
    return [held] * segment['overlap'] + depthcontrol.panel_samples(panel, segment['length'] - segment['overlap'])


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
        panel, number = segment['panel'], segment['number']
        label = f'Panel {number} "{panel["title"]}"'
        pictures, dropped = segment_pictures(board, panel, options, characters)
        videos, extra_videos = segment_videos(board, panel, options)
        audios, extra_audios = segment_audios(board, panel, options, videos, preview)
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
        start_seconds = (segment['start'] + segment['overlap']) / FPS
        room = (segment['end'] - segment['start'] - segment['overlap']) / FPS
        kept_videos = []
        for index, (path, template, values) in enumerate(videos):
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
        source = ''
        if control and depthcontrol.staged(board, panel) is not None:
            source = depthcontrol.source_for(board, panel, options)
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
        summary.append({'panel': panel['id'], 'number': number, 'title': panel['title'],
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

"""The storyboard document: sequences of timed panels, a reference library, portable assets.

A project is a folder `<Title>.cystory/` holding `storyboard.json` (schema
`cytools.storyboard/1`) and `assets/`, where every imported image, sound or video is copied
under its content hash. The folder can be moved or sent as it is: nothing in it points
outside itself. Saving is atomic and keeps a few rotating backups, because a storyboard is
hours of work and a crash in the middle of a write must never lose it.

The format is deliberately independent of any video model: a panel describes a moment of
the film (images, duration, camera, action, dialogue, sound, references). Converting it to
a workflow of a given generator is a later, separate step.
"""
import copy
import hashlib
import json
import re
import shutil
import time
import uuid
from pathlib import Path

SCHEMA = 'cytools.storyboard/1'
SUFFIX = '.cystory'
KINDS = ('character', 'location', 'object', 'style', 'image', 'audio', 'video')
IMAGE_ROLES = ('sketch', 'first', 'last', 'keyframe', 'reference')
STATUSES = ('idea', 'draft', 'ready', 'generated')
SHOT_SIZES = ('', 'extreme wide shot', 'wide shot', 'full shot', 'medium wide shot', 'medium shot',
              'medium close-up', 'close-up', 'extreme close-up', 'insert shot', 'over-the-shoulder shot')
ANGLES = ('', 'eye level', 'high angle', 'low angle', "bird's-eye view", "worm's-eye view", 'dutch angle', 'POV')
CAMERA_MOVES = ('', 'static shot', 'push in', 'pull out', 'zoom in', 'zoom out', 'pan left', 'pan right',
                'truck left', 'truck right', 'tilt up', 'tilt down', 'pedestal up', 'pedestal down', 'arc shot',
                'tracking shot', 'handheld', 'shake slightly', 'shake strongly', 'roll clockwise', 'roll counterclockwise')
AMPLITUDES = ('', 'small', 'large')
SPEEDS = ('', 'slow', 'fast')
TRANSITIONS = ('cut', 'crossfade', 'fade to black', 'fade from black')
ASPECTS = ('16:9', '21:9', '4:3', '1:1', '3:4', '9:16', '2.39:1')
IMAGE_SUFFIXES = ('.png', '.jpg', '.jpeg', '.webp', '.bmp')
AUDIO_SUFFIXES = ('.wav', '.mp3', '.flac', '.ogg', '.m4a', '.aac')
VIDEO_SUFFIXES = ('.mp4', '.mov', '.webm', '.mkv', '.avi', '.m4v')
BACKUPS = 5


class StoryboardError(ValueError):
    pass


def now():
    return time.strftime('%Y-%m-%dT%H:%M:%S')


def new_id(prefix):
    return f'{prefix}_{uuid.uuid4().hex[:10]}'


def empty_prompt():
    return {'scene': '', 'action': '', 'shotSize': '', 'angle': '', 'cameraMove': '', 'cameraAmplitude': '',
            'cameraSpeed': '', 'lens': '', 'sound': '', 'music': '', 'dialogue': [], 'freeText': ''}


def new_panel(title='', duration=5.0):
    from .layout import default_layout
    return {'id': new_id('panel'), 'title': title, 'duration': float(duration), 'status': 'idea', 'color': '',
            'images': [], 'prompt': empty_prompt(), 'references': [],
            'transition': {'type': 'cut', 'duration': 0.5}, 'notes': '', 'layout': default_layout()}


def new_sequence(title='Sequence 1'):
    return {'id': new_id('seq'), 'title': title, 'color': '', 'notes': '', 'panels': []}


def new_document(title, aspect='16:9', fps=24, default_duration=5.0):
    return {'schema': SCHEMA, 'id': new_id('story'), 'title': title, 'description': '', 'createdAt': now(),
            'updatedAt': now(),
            'settings': {'aspect': aspect, 'fps': int(fps), 'defaultDuration': float(default_duration),
                         'minSegment': 1.0, 'maxSegment': 15.0, 'style': '', 'language': 'English'},
            'library': [], 'stages': [], 'poses': [], 'sequences': [new_sequence()]}


def _safe_name(title):
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', '_', title).strip(' .') or 'Storyboard'
    return name[:80]


class Storyboard:
    """A loaded project. Every mutation goes through a method so it stays consistent."""

    def __init__(self, folder, document):
        self.folder = Path(folder)
        self.doc = document

    # ------------------------------------------------------------------ files
    @classmethod
    def create(cls, parent, title, **settings):
        folder = Path(parent) / (_safe_name(title) + SUFFIX)
        if folder.exists():
            raise StoryboardError(f'{folder} already exists.')
        (folder / 'assets').mkdir(parents=True)
        board = cls(folder, new_document(title, **settings))
        board.save()
        return board

    @classmethod
    def load(cls, path):
        path = Path(path)
        folder = path.parent if path.name == 'storyboard.json' else path
        try:
            document = json.loads((folder / 'storyboard.json').read_text(encoding='utf-8-sig'))
        except OSError as exc:
            raise StoryboardError(f'Cannot read {folder}: {exc}') from None
        except ValueError as exc:
            raise StoryboardError(f'storyboard.json is damaged ({exc}); backups are in {folder / "backups"}.') from None
        if document.get('schema') != SCHEMA:
            raise StoryboardError(f'{folder} is not a storyboard ({SCHEMA}).')
        return cls(folder, migrate(document))

    def save(self):
        self.doc['updatedAt'] = now()
        target = self.folder / 'storyboard.json'
        self.folder.mkdir(parents=True, exist_ok=True)
        if target.is_file():
            backups = self.folder / 'backups'
            backups.mkdir(exist_ok=True)
            shutil.copyfile(target, backups / f'storyboard-{time.strftime("%Y%m%d-%H%M%S")}-{uuid.uuid4().hex[:4]}.json')
            for old in sorted(backups.glob('storyboard-*.json'))[:-BACKUPS]:
                old.unlink(missing_ok=True)
        temporary = target.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.doc, indent=1, ensure_ascii=False), encoding='utf-8')
        temporary.replace(target)
        return target

    def snapshot(self):
        return copy.deepcopy(self.doc)

    def restore(self, document):
        self.doc = copy.deepcopy(document)

    # ------------------------------------------------------------------ assets
    def import_asset(self, source):
        """Copy a file into assets/ under its content hash; return its path relative to the project."""
        source = Path(source)
        if not source.is_absolute():
            candidate = self.folder / source
            if candidate.is_file() and candidate.resolve().is_relative_to(self.folder.resolve()):
                return candidate.relative_to(self.folder).as_posix()
        if not source.is_file():
            raise StoryboardError(f'{source} does not exist.')
        suffix = source.suffix.lower()
        if suffix not in IMAGE_SUFFIXES + AUDIO_SUFFIXES + VIDEO_SUFFIXES:
            raise StoryboardError(f'{source.name}: unsupported file type {suffix!r}.')
        digest = hashlib.sha256()
        with open(source, 'rb') as handle:
            for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
                digest.update(block)
        target = self.folder / 'assets' / (digest.hexdigest()[:24] + suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file():
            shutil.copyfile(source, target)
            names = self.doc.setdefault('assetNames', {})
            names[target.name] = source.name
        return target.relative_to(self.folder).as_posix()

    def import_image_data(self, image, name='pasted.png'):
        """An image from the clipboard (PIL image) saved as an asset."""
        temporary = self.folder / 'assets' / f'.paste-{uuid.uuid4().hex}.png'
        temporary.parent.mkdir(parents=True, exist_ok=True)
        image.save(temporary)
        try:
            relative = self.import_asset(temporary)
        finally:
            temporary.unlink(missing_ok=True)
        self.doc.setdefault('assetNames', {})[Path(relative).name] = name
        return relative

    def asset(self, relative):
        return self.folder / relative if relative else None

    def unused_assets(self):
        used = set()
        for item in self.doc['library']:
            used |= set(item.get('files') or [])
        for panel in self.panels():
            used |= {image['file'] for image in panel['images']}
            layout = panel.get('layout') or {}
            used |= {layout.get('render'), layout.get('depth')}
        for stage in self.doc.get('stages', []):
            used |= {obj.get('mesh') for obj in stage.get('objects', [])}
        return [p for p in (self.folder / 'assets').glob('*') if p.is_file()
                and p.relative_to(self.folder).as_posix() not in used and not p.name.startswith('.')]

    # ------------------------------------------------------------------ structure
    def sequences(self):
        return self.doc['sequences']

    def panels(self):
        return [panel for sequence in self.doc['sequences'] for panel in sequence['panels']]

    def find(self, panel_id):
        for sequence in self.doc['sequences']:
            for index, panel in enumerate(sequence['panels']):
                if panel['id'] == panel_id:
                    return sequence, index, panel
        raise StoryboardError(f'Unknown panel {panel_id!r}.')

    def sequence(self, sequence_id=''):
        if not sequence_id:
            return self.doc['sequences'][-1]
        for sequence in self.doc['sequences']:
            if sequence['id'] == sequence_id or sequence['title'] == sequence_id:
                return sequence
        raise StoryboardError(f'Unknown sequence {sequence_id!r}.')

    def add_sequence(self, title='', after=''):
        sequence = new_sequence(title or f'Sequence {len(self.doc["sequences"]) + 1}')
        index = len(self.doc['sequences'])
        if after:
            index = next(i for i, s in enumerate(self.doc['sequences']) if s['id'] == after) + 1
        self.doc['sequences'].insert(index, sequence)
        return sequence

    def remove_sequence(self, sequence_id):
        sequence = self.sequence(sequence_id)
        if len(self.doc['sequences']) == 1:
            raise StoryboardError('A storyboard keeps at least one sequence.')
        self.doc['sequences'].remove(sequence)
        return sequence

    def add_panel(self, sequence_id='', after='', **fields):
        sequence = self.sequence(sequence_id)
        panel = new_panel(duration=self.doc['settings']['defaultDuration'])
        panel['title'] = fields.pop('title', '') or f'Shot {len(self.panels()) + 1}'
        index = len(sequence['panels'])
        if after:
            owner, position, _ = self.find(after)
            sequence, index = owner, position + 1
        sequence['panels'].insert(index, panel)
        if fields:
            self.update_panel(panel['id'], **fields)
        return panel

    def duplicate_panel(self, panel_id):
        sequence, index, panel = self.find(panel_id)
        copy_ = copy.deepcopy(panel)
        copy_['id'] = new_id('panel')
        copy_['title'] = panel['title'] + ' (copy)'
        sequence['panels'].insert(index + 1, copy_)
        return copy_

    def remove_panel(self, panel_id):
        sequence, index, panel = self.find(panel_id)
        sequence['panels'].pop(index)
        return panel

    def move_panel(self, panel_id, sequence_id='', index=None):
        source, position, panel = self.find(panel_id)
        target = self.sequence(sequence_id) if sequence_id else source
        source['panels'].pop(position)
        index = len(target['panels']) if index is None else max(0, min(int(index), len(target['panels'])))
        target['panels'].insert(index, panel)
        return panel

    def update_panel(self, panel_id, **fields):
        _, _, panel = self.find(panel_id)
        for key, value in fields.items():
            if key == 'prompt':
                merged = {**empty_prompt(), **panel['prompt'], **(value or {})}
                panel['prompt'] = merged
            elif key == 'images':
                panel['images'] = [self._image(item) for item in value or []]
            elif key == 'references':
                known = {item['id'] for item in self.doc['library']}
                unknown = [ref for ref in value or [] if ref not in known]
                if unknown:
                    raise StoryboardError('Unknown library items: ' + ', '.join(unknown))
                panel['references'] = list(dict.fromkeys(value or []))
            elif key == 'transition':
                transition = {**panel['transition'], **(value or {})}
                if transition['type'] not in TRANSITIONS:
                    raise StoryboardError(f'Unknown transition {transition["type"]!r}.')
                transition['duration'] = max(0.0, float(transition.get('duration', 0.5)))
                panel['transition'] = transition
            elif key == 'duration':
                duration = float(value)
                if not 0.1 <= duration <= 600:
                    raise StoryboardError('A panel lasts between 0.1 and 600 seconds.')
                panel['duration'] = round(duration, 3)
            elif key == 'status':
                if value not in STATUSES:
                    raise StoryboardError(f'Unknown status {value!r}.')
                panel['status'] = value
            elif key in ('title', 'notes', 'color'):
                panel[key] = str(value or '')
            elif key == 'layout':
                from .layout import set_layout
                set_layout(self, panel_id, **(value or {}))
            else:
                raise StoryboardError(f'Unknown panel field {key!r}.')
        return panel

    def _image(self, item):
        item = {'file': item} if isinstance(item, str) else dict(item)
        role = item.get('role', 'sketch')
        if role not in IMAGE_ROLES:
            raise StoryboardError(f'Unknown image role {role!r}.')
        result = {'file': self.import_asset(item['file']), 'role': role, 'caption': str(item.get('caption', ''))}
        if role == 'keyframe':
            result['time'] = max(0.0, float(item.get('time', 0.0)))
        return result

    # ------------------------------------------------------------------ library
    def add_library_item(self, kind, name, description='', files=(), tags=()):
        if kind not in KINDS:
            raise StoryboardError(f'Unknown library kind {kind!r}; use one of {", ".join(KINDS)}.')
        item = {'id': new_id(kind), 'kind': kind, 'name': name or kind.title(), 'description': description,
                'files': [self.import_asset(f) for f in files], 'tags': [str(t) for t in tags]}
        self.doc['library'].append(item)
        return item

    def update_library_item(self, item_id, **fields):
        item = self.library_item(item_id)
        for key, value in fields.items():
            if key == 'files':
                item['files'] = [self.import_asset(f) for f in value or []]
            elif key == 'tags':
                item['tags'] = [str(t) for t in value or []]
            elif key in ('name', 'description'):
                item[key] = str(value or '')
            elif key == 'kind':
                if value not in KINDS:
                    raise StoryboardError(f'Unknown library kind {value!r}.')
                item['kind'] = value
            else:
                raise StoryboardError(f'Unknown library field {key!r}.')
        return item

    def remove_library_item(self, item_id):
        item = self.library_item(item_id)
        self.doc['library'].remove(item)
        for panel in self.panels():
            panel['references'] = [r for r in panel['references'] if r != item_id]
            for line in panel['prompt'].get('dialogue', []):
                if line.get('speaker') == item_id:
                    line['speaker'] = item['name']
        return item

    def library_item(self, item_id):
        for item in self.doc['library']:
            if item['id'] == item_id:
                return item
        raise StoryboardError(f'Unknown library item {item_id!r}.')

    # ------------------------------------------------------------------ time
    def timeline(self):
        """Start and end of every panel; crossfades overlap the previous panel."""
        rows, clock = [], 0.0
        panels = self.panels()
        for index, panel in enumerate(panels):
            overlap = 0.0
            if index and panels[index - 1]['transition']['type'] == 'crossfade':
                overlap = min(panels[index - 1]['transition']['duration'], panel['duration'] / 2,
                              panels[index - 1]['duration'] / 2)
            start = max(0.0, clock - overlap)
            rows.append({'id': panel['id'], 'start': round(start, 3), 'end': round(start + panel['duration'], 3)})
            clock = start + panel['duration']
        return rows

    def total_duration(self):
        rows = self.timeline()
        return rows[-1]['end'] if rows else 0.0

    # ------------------------------------------------------------------ checks
    def validate(self):
        """Problems worth showing; nothing here blocks saving."""
        settings = self.doc['settings']
        issues = []
        known = {item['id'] for item in self.doc['library']}
        for number, panel in enumerate(self.panels(), start=1):
            label = f'#{number} {panel["title"]}'
            if panel['duration'] < settings['minSegment']:
                issues.append({'panel': panel['id'], 'level': 'warning',
                               'message': f'{label}: {panel["duration"]:.1f} s is shorter than {settings["minSegment"]:.1f} s.'})
            if panel['duration'] > settings['maxSegment']:
                issues.append({'panel': panel['id'], 'level': 'info',
                               'message': f'{label}: {panel["duration"]:.1f} s is longer than {settings["maxSegment"]:.0f} s; '
                                          'it will be split into several generations.'})
            prompt = panel['prompt']
            if not any(prompt.get(k) for k in ('scene', 'action', 'freeText')) and not panel['images']:
                issues.append({'panel': panel['id'], 'level': 'warning',
                               'message': f'{label}: no image and no description yet.'})
            for image in panel['images']:
                if not (self.folder / image['file']).is_file():
                    issues.append({'panel': panel['id'], 'level': 'error',
                                   'message': f'{label}: image {image["file"]} is missing from the project.'})
                if image['role'] == 'keyframe' and image.get('time', 0) > panel['duration']:
                    issues.append({'panel': panel['id'], 'level': 'warning',
                                   'message': f'{label}: a keyframe is placed after the end of the panel.'})
            roles = [i['role'] for i in panel['images']]
            for role in ('first', 'last'):
                if roles.count(role) > 1:
                    issues.append({'panel': panel['id'], 'level': 'warning',
                                   'message': f'{label}: more than one {role} frame.'})
            for ref in panel['references']:
                if ref not in known:
                    issues.append({'panel': panel['id'], 'level': 'error', 'message': f'{label}: unknown reference {ref}.'})
            for line in prompt.get('dialogue', []):
                if not str(line.get('line', '')).strip():
                    issues.append({'panel': panel['id'], 'level': 'warning', 'message': f'{label}: an empty dialogue line.'})
        for item in self.doc['library']:
            for file in item.get('files') or []:
                if not (self.folder / file).is_file():
                    issues.append({'panel': '', 'level': 'error',
                                   'message': f'Library item {item["name"]}: {file} is missing from the project.'})
        return issues


def migrate(document):
    """Fill fields added after a document was written, so old projects keep opening."""
    document.setdefault('library', [])
    document.setdefault('stages', [])
    document.setdefault('poses', [])
    document.setdefault('sequences', [new_sequence()])
    settings = document.setdefault('settings', {})
    for key, value in new_document('x')['settings'].items():
        settings.setdefault(key, value)
    for sequence in document['sequences']:
        for panel in sequence.setdefault('panels', []):
            base = new_panel()
            for key, value in base.items():
                panel.setdefault(key, value)
            panel['prompt'] = {**empty_prompt(), **panel['prompt']}
    return document


def describe_camera(prompt):
    """'The camera pushes in with small amplitude at slow speed.' from the structured fields."""
    verbs = {'static shot': 'holds a static shot', 'push in': 'pushes in', 'pull out': 'pulls out',
             'zoom in': 'zooms in', 'zoom out': 'zooms out', 'pan left': 'pans left', 'pan right': 'pans right',
             'truck left': 'trucks left', 'truck right': 'trucks right', 'tilt up': 'tilts up', 'tilt down': 'tilts down',
             'pedestal up': 'pedestals up', 'pedestal down': 'pedestals down', 'arc shot': 'arcs around the subject',
             'tracking shot': 'tracks the subject', 'handheld': 'is handheld', 'shake slightly': 'shakes slightly',
             'shake strongly': 'shakes strongly', 'roll clockwise': 'rolls clockwise',
             'roll counterclockwise': 'rolls counterclockwise'}
    move = prompt.get('cameraMove') or ''
    if not move:
        return ''
    text = 'The camera ' + verbs.get(move, move)
    if move not in ('static shot', 'tracking shot', 'handheld'):
        if prompt.get('cameraAmplitude'):
            text += f' with {prompt["cameraAmplitude"]} amplitude'
        if prompt.get('cameraSpeed'):
            text += f' at {prompt["cameraSpeed"]} speed'
    return text + '.'

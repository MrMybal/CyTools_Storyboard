"""How a panel shows its shot: an imported image, a 2D drawing, or a view of a 3D stage.

Stages belong to the storyboard, not to a panel, so several panels can look at the same
place from different cameras and the space stays consistent from one shot to the next.
A panel in 3D mode keeps its own camera (and an optional end camera for a camera move),
and may override where objects are for that shot only (a character walks from panel to
panel while the walls stay put). The picture a 2D drawing or a 3D view produces is saved
in the project and becomes the panel's image; a 3D view also saves a depth map, kept for
motion control later.
"""
import copy
import math
import uuid
from pathlib import Path

from .model import StoryboardError, new_id

MODES = ('image', '2d', '3d')
ROLES = ('set', 'character', 'object', 'location')
MESH_FORMATS = ('.glb', '.gltf', '.obj', '.ply', '.stl', '.off')   # what trimesh reads without extras
DRAW_TYPES = ('rect', 'ellipse', 'line', 'arrow', 'stroke', 'text', 'figure')
RENDER_SIZE = {'16:9': (1280, 720), '21:9': (1680, 720), '2.39:1': (1720, 720), '4:3': (960, 720),
               '1:1': (720, 720), '3:4': (720, 960), '9:16': (720, 1280)}
DEFAULT_ROLE = {'mannequin': 'character', 'capsule': 'character', 'plane': 'set', 'box': 'set'}


def default_layout():
    from .render3d import default_camera
    return {'mode': 'image', 'stage': '', 'camera': default_camera(), 'cameraEnd': None, 'overrides': {},
            'drawing': {'background': '#e9e6df', 'items': []}, 'render': '', 'depth': ''}


def ensure(panel):
    layout = panel.setdefault('layout', default_layout())
    for key, value in default_layout().items():
        layout.setdefault(key, copy.deepcopy(value))
    return layout


# ------------------------------------------------------------------ stages
def stages(board):
    return board.doc.setdefault('stages', [])


def stage(board, stage_id):
    for item in stages(board):
        if item['id'] == stage_id or item['name'] == stage_id:
            return item
    raise StoryboardError(f'Unknown stage {stage_id!r}.')


def add_stage(board, name=''):
    item = {'id': new_id('stage'), 'name': name or f'Stage {len(stages(board)) + 1}', 'sky': '#9aa7b8',
            'ground': True, 'groundColour': '#8a8f96', 'objects': []}
    stages(board).append(item)
    return item


def update_stage(board, stage_id, **fields):
    item = stage(board, stage_id)
    for key, value in fields.items():
        if key not in ('name', 'sky', 'ground', 'groundColour'):
            raise StoryboardError(f'Unknown stage field {key!r}.')
        item[key] = value
    return item


def remove_stage(board, stage_id):
    item = stage(board, stage_id)
    stages(board).remove(item)
    for panel in board.panels():
        layout = ensure(panel)
        if layout['stage'] == item['id']:
            layout['stage'] = ''
            if layout['mode'] == '3d':
                layout['mode'] = 'image'
    return item


def add_object(board, stage_id, shape='box', name='', color='', position=None, rotation=None, scale=None,
               role='', reference='', mesh=''):
    from .render3d import BASE_OFFSET, DEFAULT_SCALE, SHAPES
    if shape not in SHAPES:
        raise StoryboardError(f'Unknown shape {shape!r}; use one of {", ".join(SHAPES)}.')
    item = stage(board, stage_id)
    obj = {'id': new_id('obj'), 'name': name or shape.title(), 'shape': shape,
           'color': color or {'mannequin': '#b85c4a', 'capsule': '#4a78b8'}.get(shape, '#a7a39c'),
           'position': list(position) if position else [0.0, BASE_OFFSET[shape], 0.0],
           'rotation': list(rotation) if rotation else [0.0, 0.0, 0.0],
           'scale': list(scale) if scale else list(DEFAULT_SCALE[shape]),
           'role': role or DEFAULT_ROLE.get(shape, 'object'), 'reference': reference or '', 'mesh': ''}
    if obj['role'] not in ROLES:
        raise StoryboardError(f'Unknown role {obj["role"]!r}.')
    if shape == 'mesh':
        if not mesh:
            raise StoryboardError('A mesh object needs a mesh file (' + ', '.join(MESH_FORMATS) + ').')
        obj['mesh'] = import_mesh(board, mesh)
        obj['name'] = name or Path(mesh).stem
    item['objects'].append(obj)
    return obj


def import_mesh(board, path):
    import hashlib
    import shutil
    path = Path(path)
    if not path.is_absolute() and (board.folder / path).is_file():
        return path.as_posix()
    if not path.is_file():
        raise StoryboardError(f'{path} does not exist.')
    if path.suffix.lower() not in MESH_FORMATS:
        raise StoryboardError(f'{path.name}: unsupported mesh format.')
    digest = hashlib.sha256(path.read_bytes()).hexdigest()[:24]
    target = board.folder / 'assets' / 'meshes' / (digest + path.suffix.lower())
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.is_file():
        shutil.copyfile(path, target)
        if path.suffix.lower() == '.obj':          # keep its material and textures next to it
            for sibling in path.parent.iterdir():
                if sibling.suffix.lower() in ('.mtl', '.png', '.jpg', '.jpeg') and not (target.parent / sibling.name).exists():
                    shutil.copyfile(sibling, target.parent / sibling.name)
    return target.relative_to(board.folder).as_posix()


def find_object(board, object_id):
    for item in stages(board):
        for obj in item['objects']:
            if obj['id'] == object_id:
                return item, obj
    raise StoryboardError(f'Unknown object {object_id!r}.')


def update_object(board, object_id, **fields):
    _, obj = find_object(board, object_id)
    for key, value in fields.items():
        if key in ('position', 'rotation', 'scale'):
            if len(value) != 3:
                raise StoryboardError(f'{key} needs three numbers.')
            obj[key] = [float(v) for v in value]
        elif key == 'role':
            if value not in ROLES:
                raise StoryboardError(f'Unknown role {value!r}.')
            obj['role'] = value
        elif key == 'reference':
            if value and value not in {i['id'] for i in board.doc['library']}:
                raise StoryboardError(f'Unknown library item {value!r}.')
            obj['reference'] = value or ''
        elif key in ('name', 'color'):
            obj[key] = str(value)
        elif key == 'pose':
            _check_pose(value, board)
            obj['pose'] = value or 'standing'
        else:
            raise StoryboardError(f'Unknown object field {key!r}.')
    return obj


def duplicate_object(board, object_id):
    item, obj = find_object(board, object_id)
    copy_ = copy.deepcopy(obj)
    copy_['id'] = new_id('obj')
    copy_['name'] = obj['name'] + ' copy'
    copy_['position'] = [obj['position'][0] + 1.0, obj['position'][1], obj['position'][2]]
    item['objects'].append(copy_)
    return copy_


def remove_object(board, object_id):
    item, obj = find_object(board, object_id)
    item['objects'].remove(obj)
    for panel in board.panels():
        ensure(panel)['overrides'].pop(object_id, None)
    return obj


# ------------------------------------------------------------------ panel layout
def set_layout(board, panel_id, **fields):
    _, _, panel = board.find(panel_id)
    layout = ensure(panel)
    for key, value in fields.items():
        if key == 'mode':
            if value not in MODES:
                raise StoryboardError(f'Unknown layout mode {value!r}.')
            layout['mode'] = value
        elif key == 'stage':
            if value:
                stage(board, value)
            layout['stage'] = value
        elif key in ('camera', 'cameraEnd'):
            layout[key] = None if value is None else _camera(value)
        elif key == 'overrides':
            layout['overrides'] = dict(value or {})
        elif key == 'drawing':
            layout['drawing'] = _drawing(value)
        else:
            raise StoryboardError(f'Unknown layout field {key!r}.')
    return layout


def _camera(value):
    camera = {'position': [float(v) for v in value['position']], 'target': [float(v) for v in value['target']],
              'fov': float(value.get('fov', 40.0)), 'roll': float(value.get('roll', 0.0))}
    if not 5 <= camera['fov'] <= 150:
        raise StoryboardError('The camera field of view goes from 5 to 150 degrees.')
    return camera


def _drawing(value):
    items = []
    for item in value.get('items') or []:
        if item.get('type') not in DRAW_TYPES:
            raise StoryboardError(f'Unknown drawing element {item.get("type")!r}.')
        items.append({'type': item['type'], 'points': [[float(x), float(y)] for x, y in item.get('points') or []],
                      'color': item.get('color', '#202020'), 'width': float(item.get('width', 3)),
                      'fill': bool(item.get('fill', False)), 'text': str(item.get('text', '')),
                      'size': float(item.get('size', 0.05))})
    return {'background': value.get('background', '#e9e6df'), 'items': items}


def override_object(board, panel_id, object_id, **fields):
    """Move, turn, resize or hide an object for this panel only."""
    _, _, panel = board.find(panel_id)
    find_object(board, object_id)
    entry = ensure(panel)['overrides'].setdefault(object_id, {})
    for key, value in fields.items():
        if key in ('position', 'rotation', 'scale'):
            entry[key] = [float(v) for v in value]
        elif key in ('positionEnd', 'rotationEnd'):
            if value is None:
                entry.pop(key, None)
            else:
                entry[key] = [float(v) for v in value]
        elif key == 'hidden':
            entry['hidden'] = bool(value)
        elif key in ('pose', 'poseEnd'):
            _check_pose(value, board)
            if value:
                entry[key] = value
            else:
                entry.pop(key, None)
        else:
            raise StoryboardError(f'Unknown override field {key!r}.')
    return entry


def _check_pose(value, board=None):
    from .pose import NAMES
    custom = {p['id'] for p in (board.doc.get('poses') or [])} if board is not None else set()
    if value and value not in NAMES and value not in custom:
        raise StoryboardError(f'Unknown pose {value!r}; use one of {", ".join(NAMES)} or a project pose id.')


# ------------------------------------------------------------------ project poses
def poses(board):
    return board.doc.setdefault('poses', [])


def find_pose(board, pose_id):
    for entry in poses(board):
        if entry['id'] == pose_id or entry['name'] == pose_id:
            return entry
    raise StoryboardError(f'Unknown project pose {pose_id!r}.')


def add_pose(board, name='', base='standing', angles=None, walks=True):
    """A project pose, starting from a preset or another project pose, then `angles` on top."""
    from . import pose
    _check_pose(base, board)
    start = pose.params(base, 0.0, pose.library_of(poses(board)))
    try:
        values = pose.clean_angles(dict(start, **(angles or {})))
    except ValueError as exc:
        raise StoryboardError(str(exc)) from None
    entry = {'id': new_id('pose'), 'name': name or f'Pose {len(poses(board)) + 1}',
             'angles': _jsonable(values), 'walks': bool(walks)}
    poses(board).append(entry)
    return entry


def update_pose(board, pose_id, name=None, angles=None, walks=None):
    """Rename, change some angles (the others stay), or whether it walks when moving."""
    from . import pose
    entry = find_pose(board, pose_id)
    if name is not None:
        entry['name'] = str(name) or entry['name']
    if angles:
        try:
            entry['angles'] = _jsonable(pose.clean_angles(dict(pose.clean_angles(entry['angles']), **angles)))
        except ValueError as exc:
            raise StoryboardError(str(exc)) from None
    if walks is not None:
        entry['walks'] = bool(walks)
    return entry


def remove_pose(board, pose_id):
    """Delete a project pose; the characters that used it go back to standing."""
    entry = find_pose(board, pose_id)
    poses(board).remove(entry)
    for item in stages(board):
        for obj in item['objects']:
            if obj.get('pose') == entry['id']:
                obj['pose'] = 'standing'
    for panel in board.panels():
        for override in ensure(panel)['overrides'].values():
            for key in ('pose', 'poseEnd'):
                if override.get(key) == entry['id']:
                    override.pop(key)
    return entry


def _jsonable(angles):
    return {k: list(v) if isinstance(v, tuple) else v for k, v in angles.items()}


def clear_override(board, panel_id, object_id):
    _, _, panel = board.find(panel_id)
    ensure(panel)['overrides'].pop(object_id, None)


# ------------------------------------------------------------------ rendering
def render_size(board, width=None):
    size = RENDER_SIZE.get(board.doc['settings']['aspect'], (1280, 720))
    if width:
        return int(width), int(width * size[1] / size[0])
    return size


def render_panel(board, panel_id, which='camera'):
    """Render a 2D or 3D layout into the project and make it the panel's picture."""
    from PIL import Image
    _, _, panel = board.find(panel_id)
    layout = ensure(panel)
    folder = board.folder / 'assets' / 'renders'
    folder.mkdir(parents=True, exist_ok=True)
    stamp = uuid.uuid4().hex[:6]
    for key in ('render', 'depth'):
        old = layout.get(key)
        if old and (board.folder / old).is_file() and old.startswith('assets/renders/'):
            (board.folder / old).unlink(missing_ok=True)
    if layout['mode'] == '2d':
        image = draw_image(layout['drawing'], render_size(board))
        target = folder / f'{panel["id"]}_2d_{stamp}.png'
        image.save(target)
        layout['render'], layout['depth'] = target.relative_to(board.folder).as_posix(), ''
    elif layout['mode'] == '3d':
        from . import render3d
        if not layout['stage']:
            raise StoryboardError('Choose a stage for this panel first.')
        camera = layout['camera'] if which == 'camera' or not layout.get('cameraEnd') else layout['cameraEnd']
        result = render3d.renderer().render(stage(board, layout['stage']), camera, render_size(board),
                                            layout['overrides'], folder=board.folder, want_depth=True,
                                            poses=board.doc.get('poses'))
        target = folder / f'{panel["id"]}_3d_{stamp}.png'
        depth = folder / f'{panel["id"]}_depth_{stamp}.png'
        Image.fromarray(result['color']).save(target)
        Image.fromarray(render3d.depth_image(result['depth'])).save(depth)
        layout['render'] = target.relative_to(board.folder).as_posix()
        layout['depth'] = depth.relative_to(board.folder).as_posix()
    else:
        raise StoryboardError('This panel shows an imported image; switch it to 2D or 3D first.')
    return layout


def draw_image(drawing, size):
    """The 2D drawing as a picture (coordinates are 0-1 of the frame)."""
    from PIL import Image, ImageDraw
    from .export import _font
    width, height = size
    image = Image.new('RGB', size, drawing.get('background', '#e9e6df'))
    draw = ImageDraw.Draw(image)
    scale = max(1.0, width / 640)
    for item in drawing.get('items') or []:
        points = [(x * width, y * height) for x, y in item['points']]
        colour, line = item['color'], max(1, int(item['width'] * scale))
        if item['type'] in ('rect', 'ellipse') and len(points) >= 2:
            (x0, y0), (x1, y1) = points[0], points[-1]
            box = [min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)]
            shape = draw.rectangle if item['type'] == 'rect' else draw.ellipse
            shape(box, outline=colour, width=line, fill=colour if item['fill'] else None)
        elif item['type'] in ('line', 'stroke') and len(points) >= 2:
            draw.line(points, fill=colour, width=line, joint='curve')
        elif item['type'] == 'arrow' and len(points) >= 2:
            (x0, y0), (x1, y1) = points[0], points[-1]
            draw.line([(x0, y0), (x1, y1)], fill=colour, width=line)
            angle = math.atan2(y1 - y0, x1 - x0)
            head = 14 * scale
            for side in (-0.45, 0.45):
                draw.line([(x1, y1), (x1 - head * math.cos(angle + side), y1 - head * math.sin(angle + side))],
                          fill=colour, width=line)
        elif item['type'] == 'text' and points:
            draw.text(points[0], item['text'], fill=colour, font=_font(max(10, int(item['size'] * height))))
        elif item['type'] == 'figure' and points:
            x, y = points[0]                       # the feet
            h = item['size'] * height * 4          # size is a quarter of the figure height
            head = h * 0.12
            draw.ellipse([x - head, y - h, x + head, y - h + 2 * head], outline=colour, width=line)
            draw.line([(x, y - h + 2 * head), (x, y - h * 0.45)], fill=colour, width=line)
            draw.line([(x - h * 0.22, y - h * 0.7), (x + h * 0.22, y - h * 0.7)], fill=colour, width=line)
            draw.line([(x, y - h * 0.45), (x - h * 0.15, y)], fill=colour, width=line)
            draw.line([(x, y - h * 0.45), (x + h * 0.15, y)], fill=colour, width=line)
    return image


# ------------------------------------------------------------------ camera language
def suggest_camera(panel):
    """Camera move, amplitude and speed from the start and end cameras of a 3D panel."""
    layout = ensure(panel)
    start, end = layout.get('camera'), layout.get('cameraEnd')
    if not start or not end:
        return {'cameraMove': 'static shot', 'cameraAmplitude': '', 'cameraSpeed': ''}
    import numpy as np
    from .render3d import look_at
    view = look_at(start['position'], start['target'])
    right, up, back = view[0, :3], view[1, :3], view[2, :3]
    move = np.asarray(end['position'], float) - np.asarray(start['position'], float)
    along, lateral, vertical = float(-back @ move), float(right @ move), float(move[1])

    def heading(camera):
        d = np.asarray(camera['target'], float) - np.asarray(camera['position'], float)
        return math.degrees(math.atan2(d[0], d[2])), math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))
    (yaw0, pitch0), (yaw1, pitch1) = heading(start), heading(end)
    yaw = (yaw1 - yaw0 + 180) % 360 - 180
    pitch = pitch1 - pitch0
    fov = end.get('fov', 40) - start.get('fov', 40)
    distance = max(float(np.linalg.norm(np.asarray(start['target'], float) - np.asarray(start['position'], float))), 1.0)
    candidates = [(abs(along) / distance, 'push in' if along > 0 else 'pull out'),
                  (abs(lateral) / distance, 'truck right' if lateral > 0 else 'truck left'),
                  (abs(vertical) / distance, 'pedestal up' if vertical > 0 else 'pedestal down'),
                  (abs(yaw) / 45, 'pan left' if yaw > 0 else 'pan right'),
                  (abs(pitch) / 30, 'tilt up' if pitch > 0 else 'tilt down'),
                  (abs(fov) / 20, 'zoom in' if fov < 0 else 'zoom out')]
    if abs(lateral) / distance > 0.2 and abs(yaw) > 10 and (yaw > 0) == (lateral > 0):
        candidates.append((abs(yaw) / 45 + abs(lateral) / distance, 'arc shot'))
    magnitude, move_name = max(candidates)
    if magnitude < 0.05:
        return {'cameraMove': 'static shot', 'cameraAmplitude': '', 'cameraSpeed': ''}
    amplitude = 'small' if magnitude < 0.25 else 'large' if magnitude > 1.0 else ''
    rate = float(np.linalg.norm(move)) / max(panel['duration'], 0.1)
    speed = 'slow' if rate < 0.4 else 'fast' if rate > 2.5 else ''
    return {'cameraMove': move_name, 'cameraAmplitude': amplitude, 'cameraSpeed': speed}

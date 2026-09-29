"""Offscreen rendering of the 3D stages of a storyboard (moderngl, no window).

A stage is a set of simple shapes (box, sphere, cylinder, cone, capsule, plane, a mannequin
that shows which way it faces) and imported meshes, each with a colour and a transform.
A panel looks at a stage through its own camera. The same code renders the interactive
view of the editor, the picture that becomes the panel's image, the depth map kept for
later motion control, and the id buffer used to pick an object with the mouse.

Conventions: metres, Y up, a camera looks at its target; object rotation is the Euler
triple [x, y, z] in degrees of ImGuizmo's components (applied X, then Y, then Z).
"""
import math
import threading
from pathlib import Path

import numpy as np

SHAPES = ('box', 'sphere', 'cylinder', 'cone', 'capsule', 'plane', 'mannequin', 'mesh')
DEFAULT_SCALE = {'box': [1, 1, 1], 'sphere': [1, 1, 1], 'cylinder': [1, 1, 1], 'cone': [1, 1, 1],
                 'capsule': [0.5, 1.8, 0.5], 'plane': [4, 1, 4], 'mannequin': [1, 1, 1], 'mesh': [1, 1, 1]}
# Height of the origin above the ground so a new shape stands on the floor.
BASE_OFFSET = {'box': 0.5, 'sphere': 0.5, 'cylinder': 0.5, 'cone': 0.5, 'capsule': 0.9, 'plane': 0.0,
               'mannequin': 0.0, 'mesh': 0.0}

VERTEX = """
#version 330
uniform mat4 mvp; uniform mat4 model;
in vec3 position; in vec3 normal;
out vec3 world_normal; out vec3 world_pos;
void main(){
    vec4 w = model * vec4(position, 1.0);
    world_pos = w.xyz;
    world_normal = mat3(model) * normal;
    gl_Position = mvp * vec4(position, 1.0);
}
"""
FRAGMENT = """
#version 330
uniform vec3 colour; uniform float highlight; uniform vec3 sun; uniform int ground;
in vec3 world_normal; in vec3 world_pos;
out vec4 fragment;
void main(){
    vec3 n = normalize(world_normal);
    if (!gl_FrontFacing) n = -n;
    float light = 0.45 + 0.55 * max(dot(n, normalize(sun)), 0.0);
    float sky = 0.6 + 0.4 * n.y;
    vec3 c = colour * (0.62 * light + 0.38 * sky);
    if (ground == 1) {
        vec2 g = abs(fract(world_pos.xz) - 0.5);
        float line = step(0.485, max(g.x, g.y));
        vec2 g5 = abs(fract(world_pos.xz / 5.0) - 0.5);
        line = max(line, step(0.494, max(g5.x, g5.y)) * 1.0);
        c = mix(colour, colour * 0.6, line * 0.6);
        float fade = clamp(length(world_pos.xz) / 60.0, 0.0, 1.0);
        c = mix(c, vec3(0.62, 0.66, 0.72), fade);
    }
    c = mix(c, vec3(1.0, 0.78, 0.25), highlight * 0.35);
    fragment = vec4(c, 1.0);
}
"""
ID_FRAGMENT = """
#version 330
uniform float object_id;
out vec4 fragment;
void main(){ fragment = vec4(object_id / 255.0, 0.0, 0.0, 1.0); }
"""
LINE_VERTEX = """
#version 330
uniform mat4 mvp; in vec3 position;
void main(){ gl_Position = mvp * vec4(position, 1.0); }
"""
LINE_FRAGMENT = """
#version 330
uniform vec3 colour; out vec4 fragment;
void main(){ fragment = vec4(colour, 1.0); }
"""


# ------------------------------------------------------------------ maths

def rotation_matrix(rotation):
    """ImGuizmo's RecomposeMatrixFromComponents order (row-vector X*Y*Z), as a column-vector matrix."""
    rx, ry, rz = (math.radians(a) for a in rotation)
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return z @ y @ x


def model_matrix(position, rotation, scale):
    matrix = np.eye(4)
    matrix[:3, :3] = rotation_matrix(rotation) @ np.diag(scale)
    matrix[:3, 3] = position
    return matrix


def look_at(eye, target, roll=0.0):
    eye, target = np.asarray(eye, float), np.asarray(target, float)
    forward = target - eye
    forward /= max(np.linalg.norm(forward), 1e-9)
    up = np.array([0.0, 1.0, 0.0])
    if abs(forward @ up) > 0.999:
        up = np.array([0.0, 0.0, 1.0])
    right = np.cross(forward, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, forward)
    if roll:
        angle = math.radians(roll)
        right, up = right * math.cos(angle) + up * math.sin(angle), up * math.cos(angle) - right * math.sin(angle)
    view = np.eye(4)
    view[0, :3], view[1, :3], view[2, :3] = right, up, -forward
    view[:3, 3] = -view[:3, :3] @ eye
    return view


def perspective(fov, aspect, near=0.05, far=500.0):
    f = 1.0 / math.tan(math.radians(fov) / 2)
    matrix = np.zeros((4, 4))
    matrix[0, 0], matrix[1, 1] = f / aspect, f
    matrix[2, 2], matrix[2, 3] = (far + near) / (near - far), 2 * far * near / (near - far)
    matrix[3, 2] = -1.0
    return matrix


def camera_matrices(camera, aspect):
    view = look_at(camera['position'], camera['target'], camera.get('roll', 0.0))
    return view, perspective(camera.get('fov', 40.0), aspect)


def default_camera():
    return {'position': [0.0, 1.6, 8.0], 'target': [0.0, 1.0, 0.0], 'fov': 40.0, 'roll': 0.0}


# ------------------------------------------------------------------ primitives

def _box():
    faces = []
    for axis in range(3):
        for sign in (-1, 1):
            n = np.zeros(3)
            n[axis] = sign
            u, v = np.roll(np.eye(3), 1, axis=0)[axis], np.roll(np.eye(3), 2, axis=0)[axis]
            corners = [n * 0.5 + (a * u + b * v) * 0.5 for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            faces.append((corners, n))
    vertices, normals, indices = [], [], []
    for corners, n in faces:
        base = len(vertices)
        vertices += corners
        normals += [n] * 4
        indices += [base, base + 1, base + 2, base, base + 2, base + 3]
    return np.array(vertices), np.array(normals), np.array(indices)


def _lathe(profile, segments=32):
    """Revolve (radius, height) points around Y; normals from the profile."""
    vertices, normals, indices = [], [], []
    rows = len(profile)
    for i, (radius, height, nr, ny) in enumerate(profile):
        for j in range(segments + 1):
            a = 2 * math.pi * j / segments
            vertices.append([radius * math.sin(a), height, radius * math.cos(a)])
            normals.append([nr * math.sin(a), ny, nr * math.cos(a)])
    for i in range(rows - 1):
        for j in range(segments):
            a, b = i * (segments + 1) + j, (i + 1) * (segments + 1) + j
            indices += [a, b, a + 1, a + 1, b, b + 1]
    return np.array(vertices, float), np.array(normals, float), np.array(indices)


def _sphere(rings=16):
    profile = []
    for i in range(rings + 1):
        phi = math.pi * i / rings
        profile.append((0.5 * math.sin(phi), -0.5 * math.cos(phi), math.sin(phi), -math.cos(phi)))
    return _lathe(profile)


def _cylinder():
    return _lathe([(0.0, -0.5, 0, -1), (0.5, -0.5, 0, -1), (0.5, -0.5, 1, 0), (0.5, 0.5, 1, 0),
                   (0.5, 0.5, 0, 1), (0.0, 0.5, 0, 1)])


def _cone():
    slope = 1 / math.sqrt(5)
    return _lathe([(0.0, -0.5, 0, -1), (0.5, -0.5, 0, -1), (0.5, -0.5, 2 * slope, slope), (0.0, 0.5, 2 * slope, slope)])


def _capsule(rings=8):
    """1 unit tall, 1 wide, rounded ends a quarter of the height each; scaled to 1.8 m by default."""
    profile = []
    for i in range(rings + 1):                      # bottom cap, from the pole to the equator
        phi = math.pi / 2 * i / rings
        profile.append((0.5 * math.sin(phi), -0.5 + 0.25 * (1 - math.cos(phi)), math.sin(phi), -math.cos(phi)))
    for i in range(rings + 1):                      # top cap, from the equator to the pole
        phi = math.pi / 2 + math.pi / 2 * i / rings
        profile.append((0.5 * math.sin(phi), 0.25 - 0.25 * math.cos(phi), math.sin(phi), -math.cos(phi)))
    return _lathe(profile)


def _plane():
    vertices = np.array([[-0.5, 0, -0.5], [0.5, 0, -0.5], [0.5, 0, 0.5], [-0.5, 0, 0.5]], float)
    return vertices, np.tile([0.0, 1.0, 0.0], (4, 1)), np.array([0, 2, 1, 0, 3, 2])


def _merge(parts):
    vertices, normals, indices, offset = [], [], [], 0
    for (v, n, i), matrix in parts:
        v = (np.c_[v, np.ones(len(v))] @ matrix.T)[:, :3]
        n = n @ np.linalg.inv(matrix[:3, :3])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        vertices.append(v)
        normals.append(n)
        indices.append(i + offset)
        offset += len(v)
    return np.vstack(vertices), np.vstack(normals), np.concatenate(indices)


def _mannequin():
    """A 1.8 m figure standing on y=0, facing +Z (a small visor marks the front)."""
    capsule, sphere, box = _capsule(), _sphere(), _box()
    m = lambda p, r, s: model_matrix(p, r, s)  # noqa: E731
    return _merge([
        (capsule, m([0, 1.18, 0], [0, 0, 0], [0.36, 0.62, 0.24])),     # torso
        (sphere, m([0, 1.63, 0], [0, 0, 0], [0.24, 0.26, 0.24])),      # head
        (box, m([0, 1.65, 0.11], [0, 0, 0], [0.16, 0.05, 0.05])),      # visor: the front
        (capsule, m([-0.24, 1.18, 0], [0, 0, 8], [0.1, 0.62, 0.1])),   # arms
        (capsule, m([0.24, 1.18, 0], [0, 0, -8], [0.1, 0.62, 0.1])),
        (capsule, m([-0.1, 0.44, 0], [0, 0, 0], [0.14, 0.88, 0.14])),  # legs
        (capsule, m([0.1, 0.44, 0], [0, 0, 0], [0.14, 0.88, 0.14])),
        (box, m([-0.1, 0.03, 0.06], [0, 0, 0], [0.12, 0.06, 0.24])),   # feet
        (box, m([0.1, 0.03, 0.06], [0, 0, 0], [0.12, 0.06, 0.24])),
    ])


def _segment(a, b, width, depth=None):
    """Matrix placing the unit capsule between two points (its caps reach past them)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    axis = b - a
    length = float(np.linalg.norm(axis)) or 1e-6
    y = axis / length
    reference = np.array([0.0, 0.0, 1.0]) if abs(y[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    x = np.cross(y, reference)
    x /= np.linalg.norm(x)
    z = np.cross(x, y)
    matrix = np.eye(4)
    matrix[:3, 0], matrix[:3, 1], matrix[:3, 2] = x * width, y * (length + width), z * (depth or width)
    matrix[:3, 3] = (a + b) / 2
    return matrix


def _posed_mannequin(joints, hands=None, feet=None):
    """The mannequin built on a posed skeleton (storyboard.pose.JOINTS order, local metres), with
    its hands when given ({'r': (21, 3), 'l': ...} in the OpenPose hand order) and its feet
    ({'r': (4, 3) ankle, heel, ball, toe tips, ...}; a flat box under each ankle otherwise)."""
    from .pose import JOINTS
    j = {name: joints[i] for i, name in enumerate(JOINTS)}
    capsule, sphere, box = _capsule(), _sphere(), _box()
    pelvis = (j['r_hip'] + j['l_hip']) / 2
    head = (j['r_ear'] + j['l_ear']) / 2
    up = j['neck'] - pelvis
    up /= max(np.linalg.norm(up), 1e-6)
    left = j['l_ear'] - j['r_ear']
    left /= max(np.linalg.norm(left), 1e-6)
    face = np.cross(left, up)                       # +Z when standing: the front
    parts = [(capsule, _segment(pelvis + up * 0.02, j['neck'] - up * 0.05, 0.36, 0.24)),     # torso
             (sphere, model_matrix(head + up * 0.02, [0, 0, 0], [0.24, 0.26, 0.24]))]      # head
    visor = np.eye(4)
    visor[:3, 0], visor[:3, 1], visor[:3, 2] = left * 0.16, up * 0.05, face * 0.05
    visor[:3, 3] = head + up * 0.04 + face * 0.11
    parts.append((box, visor))
    hips_left = j['l_hip'] - j['r_hip']
    forward = np.cross(hips_left, [0.0, 1.0, 0.0])
    forward /= max(np.linalg.norm(forward), 1e-6)
    for side in ('r', 'l'):
        parts.append((capsule, _segment(j[f'{side}_shoulder'], j[f'{side}_elbow'], 0.1)))
        parts.append((capsule, _segment(j[f'{side}_elbow'], j[f'{side}_wrist'], 0.09)))
        parts.append((capsule, _segment(j[f'{side}_hip'], j[f'{side}_knee'], 0.15)))
        parts.append((capsule, _segment(j[f'{side}_knee'], j[f'{side}_ankle'], 0.12)))
        if feet and side in feet:
            _, heel, ball, tip = feet[side][:4]
            along = ball - heel
            length = float(np.linalg.norm(along)) or 1e-6
            z = along / length
            across = np.cross([0.0, 1.0, 0.0], z)
            across = across / max(np.linalg.norm(across), 1e-6) if np.linalg.norm(across) > 1e-6 else np.array([1.0, 0, 0])
            y = np.cross(z, across)
            sole = np.eye(4)            # heel to ball, from the sole up to the ankle
            sole[:3, 0], sole[:3, 1], sole[:3, 2] = across * 0.11, y * 0.075, z * (length + 0.03)
            sole[:3, 3] = (heel + ball) / 2 + y * 0.0375
            parts.append((box, sole))
            toes = tip - ball
            toe_length = float(np.linalg.norm(toes)) or 1e-6
            tz = toes / toe_length
            ty = np.cross(tz, across)
            toe = np.eye(4)
            toe[:3, 0], toe[:3, 1], toe[:3, 2] = across * 0.1, ty * 0.035, tz * toe_length
            toe[:3, 3] = (ball + tip) / 2 + ty * 0.0175
            parts.append((box, toe))
        else:
            foot = np.eye(4)
            foot[:3, 0], foot[:3, 1], foot[:3, 2] = np.cross([0.0, 1.0, 0.0], forward) * 0.12, [0, 0.06, 0], forward * 0.24
            foot[:3, 3] = j[f'{side}_ankle'] + np.array([0.0, -0.04, 0.0]) + forward * 0.06
            parts.append((box, foot))
    from .pose import HAND_LIMBS
    for points in (hands or {}).values():
        wrist, knuckles = points[0], (points[5] + points[17]) / 2
        along = knuckles - wrist
        length = float(np.linalg.norm(along)) or 1e-6
        y = along / length
        across = points[5] - points[17]
        z = across - (across @ y) * y
        z /= max(np.linalg.norm(z), 1e-6)
        palm = np.eye(4)
        palm[:3, 0], palm[:3, 1], palm[:3, 2] = np.cross(y, z) * 0.03, y * length * 1.05, z * (np.linalg.norm(across) + 0.022)
        palm[:3, 3] = wrist + along * 0.52
        parts.append((box, palm))
        for a, b in HAND_LIMBS:
            if a != 0:      # the palm covers the bones from the wrist
                parts.append((capsule, _segment(points[a], points[b], 0.02 if b <= 4 else 0.017)))
    return _merge(parts)


BUILDERS = {'box': _box, 'sphere': _sphere, 'cylinder': _cylinder, 'cone': _cone, 'capsule': _capsule,
            'plane': _plane, 'mannequin': _mannequin}


def _vertex_normals(vertices, faces):
    # Area-weighted face normals summed per vertex (trimesh's own path wants scipy).
    face = np.cross(vertices[faces[:, 1]] - vertices[faces[:, 0]], vertices[faces[:, 2]] - vertices[faces[:, 0]])
    normals = np.zeros_like(vertices)
    for corner in range(3):
        np.add.at(normals, faces[:, corner], face)
    length = np.linalg.norm(normals, axis=1, keepdims=True)
    return normals / np.where(length > 0, length, 1)


def load_mesh(path):
    import trimesh
    scene = trimesh.load(str(path), force='scene', process=False)
    parts = []
    for node in scene.graph.nodes_geometry:
        transform, name = scene.graph[node]
        mesh = scene.geometry[name]
        if not hasattr(mesh, 'faces') or not len(mesh.faces):
            continue
        vertices, faces = np.asarray(mesh.vertices, float), np.asarray(mesh.faces)
        parts.append(((vertices, _vertex_normals(vertices, faces), faces.ravel()), np.asarray(transform, float)))
    if not parts:
        raise ValueError(f'{Path(path).name} contains no triangle mesh.')
    return _merge(parts)


# ------------------------------------------------------------------ stage helpers

def resolved_objects(stage, overrides=None, t=0.0, poses=None):
    """Objects of a stage with a panel's overrides applied (position/rotation/scale/hidden, pose),
    at t in [0, 1] of the panel: an object with an end placement moves there during the panel."""
    from . import pose
    overrides = overrides or {}
    library = pose.library_of(poses)
    t = min(1.0, max(0.0, float(t)))
    result = []
    for item in stage.get('objects', []):
        merged = {**item, **(overrides.get(item['id']) or {})}
        if merged.get('hidden'):
            continue
        start = {'position': list(merged['position']), 'rotation': list(merged['rotation'])}
        for key, end_key in (('position', 'positionEnd'), ('rotation', 'rotationEnd')):
            if merged.get(end_key):
                merged[key] = [a + (b - a) * t for a, b in zip(merged[key], merged[end_key])]
        if merged.get('shape') == 'mannequin' or pose.is_character(merged):
            merged['poseAngles'] = pose.pose_of(dict(merged, **start), t, library)
            merged['start'] = start
        result.append(merged)
    return result


def colour_of(value, fallback=(0.7, 0.7, 0.72)):
    try:
        value = value.lstrip('#')
        return tuple(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except (AttributeError, ValueError):
        return fallback


def frustum_lines(camera, aspect, length=0.9):
    view = look_at(camera['position'], camera['target'], camera.get('roll', 0.0))
    inverse = np.linalg.inv(view)
    half_h = math.tan(math.radians(camera.get('fov', 40.0)) / 2) * length
    half_w = half_h * aspect
    corners = [inverse @ np.array([x, y, -length, 1.0]) for x, y in ((-half_w, -half_h), (half_w, -half_h),
                                                                    (half_w, half_h), (-half_w, half_h))]
    eye = inverse @ np.array([0, 0, 0, 1.0])
    top = inverse @ np.array([0, half_h * 1.35, -length, 1.0])
    points = []
    for c in corners:
        points += [eye[:3], c[:3]]
    for a, b in zip(corners, corners[1:] + corners[:1]):
        points += [a[:3], b[:3]]
    points += [corners[3][:3], top[:3], top[:3], corners[2][:3]]   # a roof marks "up"
    return np.array(points, 'f4')


# ------------------------------------------------------------------ renderer

class Renderer:
    """One GL context per renderer; not thread-safe, keep it on one thread."""

    def __init__(self):
        import moderngl
        self.gl = moderngl
        self.ctx = moderngl.create_standalone_context(require=330)
        self.shaded = self.ctx.program(vertex_shader=VERTEX, fragment_shader=FRAGMENT)
        self.ids = self.ctx.program(vertex_shader=VERTEX, fragment_shader=ID_FRAGMENT)
        self.lines = self.ctx.program(vertex_shader=LINE_VERTEX, fragment_shader=LINE_FRAGMENT)
        self.meshes = {}
        self.fbo, self.size = None, None
        self.ground = self._upload('ground', *_scaled_plane())

    def _upload(self, key, vertices, normals, indices):
        data = np.column_stack((vertices, normals)).astype('f4')
        vbo = self.ctx.buffer(data.tobytes())
        ibo = self.ctx.buffer(np.asarray(indices, 'u4').tobytes())
        shaded = self.ctx.vertex_array(self.shaded, [(vbo, '3f 3f', 'position', 'normal')], ibo)
        ids = self.ctx.vertex_array(self.ids, [(vbo, '3f 3x4', 'position')], ibo)
        self.meshes[key] = (shaded, ids)
        return self.meshes[key]

    def mesh(self, item, folder=None):
        shape = item.get('shape', 'box')
        if shape == 'mannequin' and item.get('poseAngles'):
            from .pose import skeleton
            angles = item['poseAngles']
            key = ('mannequin', json_key(angles))
            if key not in self.meshes:
                if len(self.meshes) > 400:  # walking cycles make many poses; keep the cache bounded
                    for old in [k for k in self.meshes if isinstance(k, tuple) and k[0] == 'mannequin'][:200]:
                        for vao in self.meshes.pop(old):
                            vao.release()
                self._upload(key, *_posed_mannequin(*skeleton(angles, 1.8, hands=True, feet=True)))
            return self.meshes[key]
        if shape == 'mesh':
            path = Path(folder or '.') / item.get('mesh', '')
            key = ('mesh', str(path))
            if key not in self.meshes:
                try:
                    return self._upload(key, *load_mesh(path))
                except Exception:
                    return self.mesh({'shape': 'box'})
            return self.meshes[key]
        if shape not in self.meshes:
            self._upload(shape, *BUILDERS.get(shape, _box)())
        return self.meshes[shape]

    def _target(self, size):
        if self.size != size:
            if self.fbo:
                self.fbo.release()
            self.fbo = self.ctx.framebuffer([self.ctx.texture(size, 4)], self.ctx.depth_texture(size))
            self.size = size
        return self.fbo

    def render(self, stage, camera, size, overrides=None, selected=None, folder=None, grid=True,
               cameras=(), want_depth=False, want_ids=False, t=0.0, poses=None):
        """Return {'color': HxWx3 uint8, 'depth': HxW float (metres) or None, 'ids': HxW int or None}."""
        gl = self.gl
        size = (max(16, int(size[0])), max(16, int(size[1])))
        fbo = self._target(size)
        fbo.use()
        self.ctx.viewport = (0, 0, *size)
        self.ctx.enable(gl.DEPTH_TEST)
        sky = colour_of(stage.get('sky', '#9aa7b8'))
        fbo.clear(*sky, 1.0, depth=1.0)
        view, projection = camera_matrices(camera, size[0] / size[1])
        view_projection = projection @ view
        objects = resolved_objects(stage, overrides, t, poses)
        self.shaded['sun'].value = (0.45, 0.8, 0.6)
        if grid and stage.get('ground', True):
            ground = model_matrix([0, -0.004, 0], [0, 0, 0], [1, 1, 1])
            self._draw(self.ground[0], view_projection, ground, colour_of(stage.get('groundColour', '#8a8f96')), 0, 1)
        for item in objects:
            matrix = model_matrix(item['position'], item['rotation'], item['scale'])
            self._draw(self.mesh(item, folder)[0], view_projection, matrix, colour_of(item.get('color')),
                       1.0 if item['id'] == selected else 0.0, 0)
        for camera_lines, colour in cameras:
            data = self.ctx.buffer(camera_lines.tobytes())
            vao = self.ctx.vertex_array(self.lines, [(data, '3f', 'position')])
            self.lines['mvp'].write(view_projection.T.astype('f4').tobytes())
            self.lines['colour'].value = colour
            vao.render(gl.LINES)
            vao.release()
            data.release()
        color = np.flipud(np.frombuffer(fbo.read(components=3, alignment=1), np.uint8).reshape(size[1], size[0], 3)).copy()
        depth = None
        if want_depth:
            raw = np.flipud(np.frombuffer(fbo.depth_attachment.read(), np.float32).reshape(size[1], size[0]))
            near, far = 0.05, 500.0
            ndc = raw * 2 - 1
            depth = (2 * near * far / (far + near - ndc * (far - near))).astype(np.float32)
            depth[raw >= 1.0] = np.inf
        ids = None
        if want_ids:
            fbo.clear(0, 0, 0, 1.0, depth=1.0)
            for index, item in enumerate(objects[:254]):
                matrix = model_matrix(item['position'], item['rotation'], item['scale'])
                self.ids['mvp'].write((view_projection @ matrix).T.astype('f4').tobytes())
                if 'model' in self.ids:  # the id shader does not need it; drivers may drop it
                    self.ids['model'].write(matrix.T.astype('f4').tobytes())
                self.ids['object_id'].value = float(index + 1)
                self.mesh(item, folder)[1].render(gl.TRIANGLES)
            raw = np.flipud(np.frombuffer(fbo.read(components=3, alignment=1), np.uint8).reshape(size[1], size[0], 3))
            # (index image, ids): pixel value k >= 0 is objects[k], -1 is background.
            ids = (raw[..., 0].astype(int) - 1, [o['id'] for o in objects])
        return {'color': color, 'depth': depth, 'ids': ids}

    def _draw(self, vao, view_projection, matrix, colour, highlight, ground):
        self.shaded['mvp'].write((view_projection @ matrix).T.astype('f4').tobytes())
        self.shaded['model'].write(matrix.T.astype('f4').tobytes())
        self.shaded['colour'].value = colour
        self.shaded['highlight'].value = highlight
        self.shaded['ground'].value = ground
        vao.render(self.gl.TRIANGLES)

    def release(self):
        self.ctx.release()


def json_key(angles):
    """A hashable, rounded key for a pose (poses closer than 0.5 degree share a mesh)."""
    parts = [round(angles['lean'] * 2) / 2, round(angles.get('bend', 0.0) * 2) / 2, round(angles.get('tilt', 0.0) * 2) / 2, None if angles['seat'] is None else round(angles['seat'], 3),
             round(angles.get('twist', 0.0) * 2) / 2, *[round(v * 2) / 2 for v in angles.get('head', (0, 0))]]
    for key in ('r_arm', 'l_arm', 'r_leg', 'l_leg'):
        parts += [round(v * 2) / 2 for v in angles[key]]
    for key in ('r_hand', 'l_hand', 'r_foot', 'l_foot'):
        parts += [round(v) for v in angles.get(key) or ()]
    return tuple(parts)


def _scaled_plane():
    vertices, normals, indices = _plane()
    return vertices * np.array([400, 1, 400]), normals, indices


def depth_image(depth):
    """Depth in metres -> 8-bit, near = white, far = black (the usual depth ControlNet convention)."""
    finite = depth[np.isfinite(depth)]
    if not finite.size:
        return np.zeros(depth.shape, np.uint8)
    # The ground runs to the horizon: a range from the far percentile would flatten every
    # object into white. Use the part of the scene where things are.
    near = np.percentile(finite, 1)
    median = np.percentile(finite, 50)
    far = min(np.percentile(finite, 97), near + 3.0 * max(median - near, 0.5))
    far = max(far, near + 0.1)
    value = np.clip((far - np.nan_to_num(depth, posinf=far)) / (far - near), 0, 1)
    return (value * 255).astype(np.uint8)


_local = threading.local()


def renderer():
    """One renderer per thread (GL contexts are bound to the thread that made them)."""
    if getattr(_local, 'renderer', None) is None:
        _local.renderer = Renderer()
    return _local.renderer

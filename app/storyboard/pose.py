"""Poses of the stage characters: an 18-joint skeleton (OpenPose / COCO-18 order) posed by a few
angles, preset poses, motion during a panel, and the OpenPose drawing used as pose control.

Local frame of a character: standing on y = 0, facing +Z, its right hand on -X. A pose is a
small set of angles (degrees): torso lean and twist, head turn and tilt, shoulder raise
forwards / sideways, elbow bend, hip raise forwards / sideways, knee bend, and how the pelvis
is placed (on the ground from the feet, or at a seat height). Besides the presets, a project
keeps its own poses (`board.doc['poses']`: id, name, angles, walks) made joint by joint. Walking and running are cycles driven by a phase; a character
that moves during a panel walks with a phase given by the distance it covers.
"""
import math

import numpy as np

JOINTS = ('nose', 'neck', 'r_shoulder', 'r_elbow', 'r_wrist', 'l_shoulder', 'l_elbow', 'l_wrist', 'r_hip',
          'r_knee', 'r_ankle', 'l_hip', 'l_knee', 'l_ankle', 'r_eye', 'l_eye', 'r_ear', 'l_ear')
# OpenPose body limbs (0-based joint pairs) and their standard colours.
LIMBS = ((1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (1, 8), (8, 9), (9, 10), (1, 11), (11, 12), (12, 13),
         (1, 0), (0, 14), (14, 16), (0, 15), (15, 17))
COLOURS = ((255, 0, 0), (255, 85, 0), (255, 170, 0), (255, 255, 0), (170, 255, 0), (85, 255, 0), (0, 255, 0),
           (0, 255, 85), (0, 255, 170), (0, 255, 255), (0, 170, 255), (0, 85, 255), (0, 0, 255), (85, 0, 255),
           (170, 0, 255), (255, 0, 255), (255, 0, 170), (255, 0, 85))
UPPER_ARM, FOREARM, THIGH, SHIN = 0.29, 0.27, 0.43, 0.44
ANKLE_HEIGHT = 0.07
STRIDE = 1.4          # metres per walking cycle (two steps)

# bend: the upper body tilted to its left side; tilt: the pelvis tilted, left hip up (the legs
# hang from the pelvis, the upper body stays as it is); head: (turn left, tilt up)
REST = {'lean': 0.0, 'twist': 0.0, 'bend': 0.0, 'tilt': 0.0, 'head': (0.0, 0.0), 'seat': None,
        # (raise forwards, raise sideways, elbow bend, turn of the arm about itself: forearm outwards)
        'r_arm': (0.0, 8.0, 5.0, 0.0), 'l_arm': (0.0, 8.0, 5.0, 0.0),
        # (raise forwards, sideways, knee bend, turn of the leg about itself: knee outwards)
        'r_leg': (0.0, 0.0, 0.0, 0.0), 'l_leg': (0.0, 0.0, 0.0, 0.0),
        # (curl of the thumb, index, middle, ring and little finger in %, spread of the fingers, wrist
        # bent towards the palm, wrist bent towards the thumb side - degrees)
        'r_hand': (15.0, 15.0, 15.0, 15.0, 15.0, 8.0, 0.0, 0.0),
        'l_hand': (15.0, 15.0, 15.0, 15.0, 15.0, 8.0, 0.0, 0.0),
        # (foot pitched toes down - on tiptoe when positive -, toes bent up - degrees). The foot is
        # flat on the ground at 0 whatever the leg does, and points where the leg points.
        'r_foot': (0.0, 0.0), 'l_foot': (0.0, 0.0)}
PRESETS = {
    'standing': {},
    'walking': {'cycle': 'walk'},
    'running': {'cycle': 'run', 'lean': 12.0},
    'sitting': {'seat': 0.48, 'r_leg': (90.0, 6.0, 90.0), 'l_leg': (90.0, 6.0, 90.0),
                'r_arm': (25.0, 8.0, 50.0), 'l_arm': (25.0, 8.0, 50.0)},
    'crouching': {'lean': 35.0, 'r_leg': (110.0, 10.0, 135.0), 'l_leg': (110.0, 10.0, 135.0),
                  'r_arm': (45.0, 10.0, 40.0), 'l_arm': (45.0, 10.0, 40.0)},
    'arms raised': {'r_arm': (170.0, 10.0, 5.0), 'l_arm': (170.0, 10.0, 5.0)},
    'pointing': {'r_arm': (85.0, 5.0, 0.0), 'r_hand': (70.0, 0.0, 95.0, 95.0, 95.0, 4.0)},
}
NAMES = tuple(PRESETS)
UPRIGHT = {'standing', 'walking', 'arms raised', 'pointing'}
LIMITS = {'lean': (-45.0, 90.0), 'twist': (-90.0, 90.0), 'bend': (-45.0, 45.0), 'tilt': (-25.0, 25.0), 'head': ((-80.0, 80.0), (-45.0, 60.0)),
          'arm': ((-60.0, 180.0), (-20.0, 180.0), (0.0, 150.0), (-90.0, 90.0)),
          'leg': ((-45.0, 130.0), (-30.0, 60.0), (0.0, 150.0), (-45.0, 45.0)),
          'hand': ((0.0, 100.0),) * 5 + ((0.0, 30.0), (-70.0, 80.0), (-25.0, 35.0)),
          'foot': ((-30.0, 60.0), (-40.0, 70.0)),
          'seat': (0.2, 1.2)}
LIMBS_KEYS = ('r_arm', 'l_arm', 'r_leg', 'l_leg')
HAND_KEYS = ('r_hand', 'l_hand')
FOOT_KEYS = ('r_foot', 'l_foot')
# The foot, from the ankle (unit-height metres, x across, y up, z forwards): heel, ball, then the
# toes from the ball. Its sole is ANKLE_HEIGHT below the ankle.
HEEL, BALL, TOES = (0.0, -0.07, -0.055), (0.0, -0.07, 0.135), 0.06
FOOT_POINTS = ('ankle', 'heel', 'ball', 'toes', 'big_toe', 'small_toe')
BIG_TOE, SMALL_TOE = 0.025, 0.035      # across the foot from its middle, towards and away from the body
# OpenPose BODY_25 feet: ankle to heel, ankle to big toe, big to small toe; each foot's render colour.
FOOT_COLOURS = {'l': (0, 0, 255), 'r': (0, 255, 255)}


def foot_frames(shin, pitch, toes):
    """(foot rotation, toes rotation): flat on the ground, pointing where the shin points (its
    across axis made horizontal), then pitched toes down and the toes bent up."""
    across = shin @ np.array([1.0, 0.0, 0.0])
    across[1] = 0.0
    if np.linalg.norm(across) < 1e-3:
        across = np.array([1.0, 0.0, 0.0])
    across /= np.linalg.norm(across)
    up = np.array([0.0, 1.0, 0.0])
    flat = np.column_stack([across, up, np.cross(across, up)])
    foot = flat @ _rx(pitch)
    return foot, foot @ _rx(-toes)

# The hand (OpenPose hand order: wrist, then thumb, index, middle, ring, little - 4 points each).
# In the forearm's frame, unit-height metres: y along the forearm (down when hanging), z to the
# front (the thumb side), the palm facing the body's midline.
FINGERS = ('thumb', 'index', 'middle', 'ring', 'little')
FINGER_BASES = {'thumb': (0.012, -0.025, 0.028), 'index': (0.0, -0.09, 0.028), 'middle': (0.0, -0.094, 0.009),
                'ring': (0.0, -0.09, -0.01), 'little': (0.0, -0.082, -0.027)}   # x: towards the palm
FINGER_BONES = {'thumb': (0.042, 0.032, 0.027), 'index': (0.045, 0.027, 0.02), 'middle': (0.05, 0.031, 0.022),
                'ring': (0.047, 0.029, 0.021), 'little': (0.037, 0.022, 0.018)}
FINGER_SPREAD = {'thumb': 0.5, 'index': 0.6, 'middle': 0.1, 'ring': -0.35, 'little': -0.8}
CURL = {'thumb': (35.0, 50.0, 60.0), 'finger': (85.0, 100.0, 70.0)}   # joint angles at 100 %
HAND_LIMBS = tuple((0 if j == 0 else 1 + f * 4 + j - 1, 1 + f * 4 + j) for f in range(5) for j in range(4))


def hand_rotation(forearm, sign, flex, deviation):
    """The hand's frame: the forearm's, bent at the wrist towards the palm, then towards the thumb."""
    return forearm @ _rz(-sign * flex) @ _rx(-deviation)


def finger_chain(forearm, wrist, k, sign, finger, curl, spread):
    """Four points of one finger (base, two joints, tip) from the hand rotation and the wrist."""
    palm = -sign            # the palm faces the body's midline: -x for the left hand
    base = np.array(FINGER_BASES[finger]) * [palm, 1, 1]
    points = [wrist + forearm @ base * k]
    if finger == 'thumb':
        start = np.array([0.35 * palm, -0.75, 0.55])
        start = _rx(-FINGER_SPREAD['thumb'] * spread) @ (start / np.linalg.norm(start))
        total = 0.0
        for bone, share in zip(FINGER_BONES['thumb'], CURL['thumb']):
            total += share * curl / 100.0
            direction = _ry(-sign * total) @ start
            points.append(points[-1] + forearm @ direction * bone * k)
        return points
    rotation = forearm @ _rx(-FINGER_SPREAD[finger] * spread)
    for bone, share in zip(FINGER_BONES[finger], CURL['finger']):
        rotation = rotation @ _rz(-sign * share * curl / 100.0)
        points.append(points[-1] + rotation @ np.array([0.0, -1.0, 0.0]) * bone * k)
    return points


def clean_angles(values):
    """A complete, bounded set of pose angles (missing values from the rest pose)."""
    result = dict(REST)
    for key, value in (values or {}).items():
        if key not in REST:
            raise ValueError(f'Unknown pose angle {key!r}.')
        result[key] = value

    def bound(value, low_high):
        return max(low_high[0], min(low_high[1], float(value)))
    angles = {'lean': bound(result['lean'], LIMITS['lean']), 'twist': bound(result['twist'], LIMITS['twist']),
              'bend': bound(result['bend'], LIMITS['bend']), 'tilt': bound(result['tilt'], LIMITS['tilt']),
              'head': tuple(bound(v, lim) for v, lim in zip(result['head'], LIMITS['head'])),
              'seat': None if result['seat'] in (None, '') else bound(result['seat'], LIMITS['seat'])}
    for key in LIMBS_KEYS:
        limits = LIMITS['arm' if key.endswith('arm') else 'leg']
        values = tuple(result[key])
        if len(values) == 3:          # poses saved before the turn angle existed
            values += (0.0,)
        if len(values) != 4:
            raise ValueError(f'{key} needs three or four angles.')
        angles[key] = tuple(bound(v, lim) for v, lim in zip(values, limits))
    for key in HAND_KEYS:
        values = tuple(result[key])
        if len(values) == 6:          # poses saved before the wrist could bend
            values += (0.0, 0.0)
        if len(values) != 8:
            raise ValueError(f'{key} needs five finger curls (%), the spread and, optionally, the two wrist '
                             'angles (towards the palm, towards the thumb).')
        angles[key] = tuple(bound(v, lim) for v, lim in zip(values, LIMITS['hand']))
    for key in FOOT_KEYS:
        values = tuple(result[key])
        if len(values) != 2:
            raise ValueError(f'{key} needs two angles: the foot pitched toes down and the toes bent up.')
        angles[key] = tuple(bound(v, lim) for v, lim in zip(values, LIMITS['foot']))
    return angles


def library_of(poses):
    """{id: pose} from a project's pose list."""
    return {p['id']: p for p in poses or [] if isinstance(p, dict) and p.get('id')}


def label(name, library=None):
    entry = (library or {}).get(name)
    return entry['name'] if entry else name


def _rx(degrees):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def _ry(degrees):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _rz(degrees):
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def params(name, phase=0.0, library=None):
    """The angles of a pose: a preset (walking or running at a phase in radians) or one of the
    project's own poses."""
    if library and name in library:
        return clean_angles(library[name]['angles'])
    if name not in PRESETS:
        raise ValueError(f'Unknown pose {name!r}; use one of {", ".join(NAMES)} or a project pose.')
    values = dict(REST, **{k: v for k, v in PRESETS[name].items() if k != 'cycle'})
    cycle = PRESETS[name].get('cycle')
    if cycle:
        swing, knee, arm, elbow = (25.0, 35.0, 20.0, 15.0) if cycle == 'walk' else (40.0, 70.0, 45.0, 85.0)
        s = math.sin(phase)
        values['r_leg'] = (swing * s, 0.0, knee * max(0.0, -math.sin(phase + 0.6)))
        values['l_leg'] = (-swing * s, 0.0, knee * max(0.0, math.sin(phase + 0.6)))
        values['r_arm'] = (-arm * s, 8.0, elbow)
        values['l_arm'] = (arm * s, 8.0, elbow)
    return clean_angles(values)


def blend(a, b, t):
    """Angles between two poses (t in [0, 1])."""
    if t <= 0:
        return a
    if t >= 1:
        return b
    mix = lambda x, y: x + (y - x) * t  # noqa: E731
    result = {'lean': mix(a['lean'], b['lean']), 'twist': mix(a['twist'], b['twist']),
              'bend': mix(a.get('bend', 0.0), b.get('bend', 0.0)), 'tilt': mix(a.get('tilt', 0.0), b.get('tilt', 0.0)),
              'head': tuple(mix(x, y) for x, y in zip(a['head'], b['head']))}
    seats = [s for s in (a['seat'], b['seat']) if s is not None]
    result['seat'] = mix(a['seat'] if a['seat'] is not None else seats[0],
                         b['seat'] if b['seat'] is not None else seats[0]) if seats else None
    a, b = clean_angles(a), clean_angles(b)
    for key in ('r_arm', 'l_arm', 'r_leg', 'l_leg') + HAND_KEYS + FOOT_KEYS:
        result[key] = tuple(mix(x, y) for x, y in zip(a[key], b[key]))
    return result


def torso_of(angles):
    """Rotation of the upper body about the pelvis: twist (to its left), then lean (forwards),
    then bend (tilted to its left side)."""
    return _ry(angles.get('twist', 0.0)) @ _rx(angles['lean']) @ _rz(-angles.get('bend', 0.0))


def pelvis_of(angles):
    """Rotation of the pelvis, hence of the legs: tilted so that the left hip rises."""
    return _rz(angles.get('tilt', 0.0))


def hip_offset(sign):
    """A hip seen from the centre of the pelvis, before the tilt (unit-height metres)."""
    return np.array([0.1 * sign, -0.03, 0.0])


def lift_of(angles, height=1.8):
    """How high skeleton() raises the pelvis: the seat, or the lowest point of a sole on the ground."""
    if angles['seat'] is not None:
        return angles['seat'] * height / 1.8
    return float(skeleton(angles, height)[0][1] - skeleton(dict(angles, seat=0.0), height)[0][1])


def skeleton(angles, height=1.8, hands=False, feet=False):
    """18 joints (local metres, standing on y = 0, facing +Z) for a figure of `height` metres.
    With hands=True: (joints, {'r': (21, 3) hand points, 'l': ...}) in the OpenPose hand order;
    with feet=True: (joints, {'r': (4, 3) ankle, heel, ball, toe tips, 'l': ...}); with both:
    (joints, hands, feet)."""
    k = height / 1.8
    # a lean tips the upper body forwards (+Z), a twist turns it to its left, a bend tilts it
    torso = torso_of(angles)
    pelvis = np.zeros(3)
    joints = {}

    def up(point):
        return pelvis + torso @ (np.asarray(point, float) * k)

    joints['neck'] = up([0, 0.50, 0])
    turn, tilt = angles.get('head', (0.0, 0.0))
    head = torso @ _ry(turn) @ _rx(-tilt)

    def face(point):  # relative to the neck, turned and tilted with the head
        return joints['neck'] + head @ ((np.asarray(point, float) - [0, 0.50, 0]) * k)
    joints['nose'] = face([0, 0.68, 0.11])
    joints['r_eye'], joints['l_eye'] = face([-0.035, 0.71, 0.10]), face([0.035, 0.71, 0.10])
    joints['r_ear'], joints['l_ear'] = face([-0.08, 0.68, 0.0]), face([0.08, 0.68, 0.0])
    down = np.array([0.0, -1.0, 0.0])
    forearms, soles = {}, {}
    for side, sign in (('r', -1), ('l', 1)):
        forwards, sideways, elbow, turn = (tuple(angles[f'{side}_arm']) + (0.0,))[:4]
        shoulder = up([0.19 * sign, 0.48, 0])
        upper = torso @ _rz(sign * sideways) @ _rx(-forwards) @ _ry(sign * turn)
        elbow_joint = shoulder + upper @ down * UPPER_ARM * k
        forearm = upper @ _rx(-elbow)
        wrist = elbow_joint + forearm @ down * FOREARM * k
        forearms[side] = (forearm, sign)
        joints[f'{side}_shoulder'], joints[f'{side}_elbow'], joints[f'{side}_wrist'] = shoulder, elbow_joint, wrist
        forwards, sideways, knee, turn = (tuple(angles[f'{side}_leg']) + (0.0,))[:4]
        hips = pelvis_of(angles)
        hip = pelvis + hips @ hip_offset(sign) * k
        thigh = hips @ _rz(sign * sideways) @ _rx(-forwards) @ _ry(sign * turn)
        knee_joint = hip + thigh @ down * THIGH * k
        shin = thigh @ _rx(knee)
        ankle = knee_joint + shin @ down * SHIN * k
        joints[f'{side}_hip'], joints[f'{side}_knee'], joints[f'{side}_ankle'] = hip, knee_joint, ankle
        pitch, toes = tuple(angles.get(f'{side}_foot') or (0.0, 0.0))
        foot, toe = foot_frames(shin, pitch, toes)
        ball = ankle + foot @ np.array(BALL) * k
        inwards = -sign        # towards the body's middle, across the foot
        soles[side] = np.array([ankle, ankle + foot @ np.array(HEEL) * k, ball,
                                ball + toe @ np.array([0.0, 0.0, TOES]) * k,
                                ball + toe @ np.array([BIG_TOE * inwards, 0.0, TOES]) * k,
                                ball + toe @ np.array([-SMALL_TOE * inwards, 0.0, TOES * 0.6]) * k])
    points = np.array([joints[name] for name in JOINTS])
    lowest = min(float(sole[1:, 1].min()) for sole in soles.values())
    lift = angles['seat'] * k if angles['seat'] is not None else -lowest
    points[:, 1] += lift
    for sole in soles.values():
        sole[:, 1] += lift
    if not hands:
        return (points, soles) if feet else points
    built = {}
    for side, (forearm, sign) in forearms.items():
        values = tuple(angles.get(f'{side}_hand') or REST[f'{side}_hand']) + (0.0, 0.0)
        wrist = points[JOINTS.index(f'{side}_wrist')]
        hand = hand_rotation(forearm, sign, values[6], values[7])
        chain = [wrist]
        for index, finger in enumerate(FINGERS):
            chain += finger_chain(hand, wrist, k, sign, finger, values[index], values[5])
        built[side] = np.array(chain)
    return (points, built, soles) if feet else (points, built)


def upright(name, library=None):
    """Poses whose legs walk when the character moves."""
    entry = (library or {}).get(name)
    if entry:
        return bool(entry.get('walks', True)) and clean_angles(entry['angles'])['seat'] is None
    return name in UPRIGHT


def pose_of(item, t=0.0, library=None):
    """Angles of a stage object at t in [0, 1] of the panel: its pose, towards its end pose,
    and a walking cycle when it moves while standing or walking."""
    start = item.get('pose') or 'standing'
    end = item.get('poseEnd') or start
    distance = 0.0
    if item.get('positionEnd'):
        a, b = np.asarray(item['position'], float), np.asarray(item['positionEnd'], float)
        distance = float(np.linalg.norm((b - a)[[0, 2]])) * min(1.0, max(0.0, t))
    phase = 2 * math.pi * distance / STRIDE
    angles = params(start, phase, library) if start == end else \
        blend(params(start, phase, library), params(end, phase, library), t)
    if distance > 0 and upright(start, library) and upright(end, library):
        # Moving while upright: the legs walk; the arms walk too unless the pose uses them.
        walk = params('walking', phase)
        angles = dict(angles, r_leg=walk['r_leg'], l_leg=walk['l_leg'])
        if {start, end} <= {'standing', 'walking'}:
            angles.update(r_arm=walk['r_arm'], l_arm=walk['l_arm'])
    return angles


# ---------------------------------------------------------------------------- reaching (IK)
HANDLES = {'r_wrist': ('reach', 'r_arm'), 'l_wrist': ('reach', 'l_arm'),
           'r_ankle': ('reach', 'r_leg'), 'l_ankle': ('reach', 'l_leg'),
           'r_elbow': ('swivel', 'r_arm'), 'l_elbow': ('swivel', 'l_arm'),
           'r_knee': ('swivel', 'r_leg'), 'l_knee': ('swivel', 'l_leg'),
           'head': ('look', None),
           'r_shoulder': ('lean_to', None), 'l_shoulder': ('lean_to', None),
           'r_hip': ('tilt_pelvis', None), 'l_hip': ('tilt_pelvis', None),
           'neck': ('lean_to', None), 'pelvis': ('shift_pelvis', None)}   # pelvis: between the hips
HANDLES.update({f'{side}_{finger}': ('curl', f'{side}_hand') for side in 'rl' for finger in FINGERS})
FINGER_HANDLES = tuple(joint for joint, (kind, _) in HANDLES.items() if kind == 'curl')
HANDLES.update({'r_palm': ('bend_wrist', 'r_hand'), 'l_palm': ('bend_wrist', 'l_hand')})   # at the knuckles
HANDLES.update({'r_toes': ('bend_toes', 'r_foot'), 'l_toes': ('bend_toes', 'l_foot')})     # at the toe tips
REACHABLE = {joint: limb for joint, (kind, limb) in HANDLES.items() if kind == 'reach'}
LOOK_DISTANCE = 0.45       # the head handle floats this far in front of the face (metres)


def height_of(item):
    scale = item.get('scale') or [1, 1, 1]
    return 1.8 * float(scale[1]) if item.get('shape') == 'mannequin' else float(scale[1])


def _object_matrix(item, height):
    from .render3d import model_matrix
    position = list(item['position'])
    if item.get('shape') == 'capsule':   # a capsule's origin is its centre, not its feet
        position[1] -= height / 2
    return model_matrix(position, item['rotation'], [1, 1, 1])


def _wrap(value):
    return (value + 180.0) % 360.0 - 180.0


def _bound(values, limits):
    return tuple(max(lo, min(hi, v)) for v, (lo, hi) in zip(values, limits))


class _Frame:
    """What the IK needs of one character: body-local coordinates, torso, limb roots."""

    def __init__(self, item, angles):
        self.height = height_of(item)
        self.k = self.height / 1.8
        self.inverse = np.linalg.inv(_object_matrix(item, self.height))
        self.angles = clean_angles(angles)

    def local(self, world):
        return (self.inverse @ np.append(np.asarray(world, float), 1.0))[:3]

    def unlifted(self, angles, local):
        return local - np.array([0.0, lift_of(angles, self.height), 0.0])

    def limb_frame(self, angles, limb):
        """(root of the limb, rotation of its parent) in unlifted body coordinates."""
        side, kind = limb.split('_')
        sign = -1 if side == 'r' else 1
        if kind == 'arm':
            torso = torso_of(angles)
            return torso @ (np.array([0.19 * sign, 0.48, 0.0]) * self.k), torso
        hips = pelvis_of(angles)
        return hips @ hip_offset(sign) * self.k, hips


def _angles_from_directions(upper, lower, sign, kind, rotation_hint):
    """(forwards, sideways, bend, rotation) whose bones point along `upper` then `lower` (unit
    vectors in the limb's parent frame). Inverse of skeleton(): upper = Rz(s*side) Rx(-fwd) Ry(s*rot)."""
    forwards = math.degrees(math.asin(max(-1.0, min(1.0, upper[2]))))
    c = math.cos(math.radians(forwards))
    psi = math.degrees(math.atan2(upper[0], -upper[1])) if c > 1e-6 else 0.0
    base = _rz(psi) @ _rx(-forwards)
    local = base.T @ lower        # = Ry(s*rot) Rx(-/+bend) (0, -1, 0)
    bend = math.degrees(math.acos(max(-1.0, min(1.0, -local[1]))))
    if bend < 0.5:
        rotation = rotation_hint
    else:
        # arm: Rx(-e) down = (0, -cos e, sin e); leg: Rx(+e) down = (0, -cos e, -sin e)
        spin = math.degrees(math.atan2(local[0], local[2]) if kind == 'arm'
                            else math.atan2(-local[0], -local[2]))
        rotation = sign * spin
    return (_wrap(forwards), _wrap(sign * psi), bend, _wrap(rotation))


def _solve(frame, angles, limb, joint, local_target, candidates_of):
    """Pick, among candidate angle sets for one limb, the one that puts `joint` closest to the
    target (then the smallest change); three rounds let the feet settle the ground."""
    kind = limb.split('_')[1]
    best = angles
    for _ in range(3):
        target = frame.unlifted(best, local_target)
        root, parent = frame.limb_frame(best, limb)
        options = []
        for values in candidates_of(best, (parent.T @ (target - root)) / frame.k):
            trial = dict(best, **{limb: _bound(values, LIMITS[kind])})
            error = float(np.linalg.norm(skeleton(trial, frame.height)[JOINTS.index(joint)] - local_target))
            change = sum(abs(x - y) for x, y in zip(trial[limb], angles[limb]))
            options.append((round(error, 4), change, trial))
        best = min(options, key=lambda o: (o[0], o[1]))[2]
    return best


def _reach_candidates(limb):
    """For one limb: a function (current angles, target of its end relative to its root in the
    parent frame, in unit-height metres) -> angle sets putting the end there (two-bone IK)."""
    side, kind = limb.split('_')
    sign = -1 if side == 'r' else 1
    first, second = (UPPER_ARM, FOREARM) if kind == 'arm' else (THIGH, SHIN)

    def candidates(current, d):
        rotation = current[limb][3]
        r = min(max(float(np.linalg.norm(d)), abs(first - second) + 1e-4), first + second - 1e-4)
        bend = math.degrees(math.pi - math.acos(max(-1.0, min(1.0, (first ** 2 + second ** 2 - r ** 2)
                                                           / (2 * first * second)))))
        # the end of the limb in its own frame (bend, then the turn about the upper bone)
        bent = _rx(-bend if kind == 'arm' else bend) @ np.array([0.0, -1.0, 0.0])
        v = np.array([0.0, -first, 0.0]) + _ry(sign * rotation) @ bent * second
        v = v / np.linalg.norm(v)
        target = d / max(float(np.linalg.norm(d)), 1e-9)
        # find Rz(psi) Rx(phi) mapping v onto the target: Rx keeps x, Rz keeps z
        a, b = v[1], v[2]
        radius = math.hypot(a, b)
        results = []
        if radius > 1e-9:
            alpha = math.atan2(b, a)
            ratio = max(-1.0, min(1.0, target[2] / radius))
            for base in (math.asin(ratio), math.pi - math.asin(ratio)):
                phi = base - alpha
                y = a * math.cos(phi) - b * math.sin(phi)
                psi = math.atan2(target[1], target[0]) - math.atan2(y, v[0])
                results.append((_wrap(-math.degrees(phi)), _wrap(sign * math.degrees(psi)), bend, rotation))
        return results
    return candidates


def reach(item, angles, joint, world_target):
    """New angles moving one wrist or ankle towards a world point (two-bone IK: shoulder or
    hip, elbow or knee). Only that limb changes; its turn about its own axis is kept; the result
    stays within the joint limits and is the solution closest to the current pose."""
    if joint not in REACHABLE:
        raise ValueError(f'{joint} cannot be moved directly; use a wrist or an ankle.')
    limb = REACHABLE[joint]
    frame = _Frame(item, angles)
    return _solve(frame, frame.angles, limb, joint, frame.local(world_target), _reach_candidates(limb))


def swivel(item, angles, joint, world_target):
    """Turn an arm (or leg) about the shoulder-wrist (hip-ankle) line so that its elbow (knee)
    comes as close as possible to a world point, the hand (foot) staying where it is."""
    kind_, limb = HANDLES.get(joint, (None, None))
    if kind_ != 'swivel':
        raise ValueError(f'{joint} is not an elbow or a knee.')
    side, kind = limb.split('_')
    sign = -1 if side == 'r' else 1
    first, second = (UPPER_ARM, FOREARM) if kind == 'arm' else (THIGH, SHIN)
    frame = _Frame(item, angles)
    end_joint = f'{side}_wrist' if kind == 'arm' else f'{side}_ankle'
    points = skeleton(frame.angles, frame.height)
    end_local = points[JOINTS.index(end_joint)]
    wanted = frame.local(world_target)

    def candidates(current, _):
        root, parent = frame.limb_frame(current, limb)
        end = parent.T @ (frame.unlifted(current, end_local) - root) / frame.k
        pull = parent.T @ (frame.unlifted(current, wanted) - root) / frame.k
        distance = float(np.linalg.norm(end))
        axis = end / max(distance, 1e-9)
        along = (first ** 2 - second ** 2 + distance ** 2) / (2 * max(distance, 1e-9))
        radius = math.sqrt(max(first ** 2 - along ** 2, 0.0))
        side_vector = pull - along * axis
        side_vector -= (side_vector @ axis) * axis
        if np.linalg.norm(side_vector) < 1e-9:
            return [current[limb]]
        elbow = along * axis + radius * side_vector / np.linalg.norm(side_vector)
        upper = elbow / np.linalg.norm(elbow)
        lower = (end - elbow) / max(np.linalg.norm(end - elbow), 1e-9)
        return [_angles_from_directions(upper, lower, sign, kind, current[limb][3])]
    solved = _solve(frame, frame.angles, limb, joint, wanted, candidates)
    return solved


def look(item, angles, world_target):
    """Head turn and tilt so that the face looks at a world point."""
    frame = _Frame(item, angles)
    current = frame.angles
    target = frame.local(world_target)
    torso = torso_of(current)
    for _ in range(6):   # the head turns about the neck, so its centre moves a little each time
        points = skeleton(current, frame.height)
        head = (points[JOINTS.index('r_ear')] + points[JOINTS.index('l_ear')]) / 2
        d = torso.T @ (target - head)
        if np.linalg.norm(d) < 1e-6:
            break
        turn = math.degrees(math.atan2(d[0], d[2]))
        tilt = math.degrees(math.atan2(d[1], math.hypot(d[0], d[2])))
        current = dict(current, head=_bound((turn, tilt), LIMITS['head']))
    return current


def handle_point(points, joint):
    """Where a handle sits among skeleton points (the pelvis lies between the hips)."""
    if joint == 'pelvis':
        return (points[JOINTS.index('r_hip')] + points[JOINTS.index('l_hip')]) / 2
    return points[JOINTS.index(joint)]


def lean_to(item, angles, joint, world_target):
    """Lean, twist and bend the upper body so that a shoulder comes as close as possible to a
    world point (the arms and the head follow the upper body; the legs do not move). For the
    neck, only lean and bend change: the twist does not move it."""
    if HANDLES.get(joint, (None,))[0] != 'lean_to':
        raise ValueError(f'{joint} is not a shoulder or the neck.')
    frame = _Frame(item, angles)
    current = frame.angles
    if joint == 'neck':
        rest, keys = np.array([0.0, 0.50, 0.0]) * frame.k, ('lean', 'bend')
    else:
        sign = -1 if joint.startswith('r_') else 1
        rest, keys = np.array([0.19 * sign, 0.48, 0.0]) * frame.k, ('lean', 'twist', 'bend')
    # (rest: the joint seen from the pelvis)
    wanted = frame.unlifted(current, frame.local(world_target))  # the legs, hence the lift, stay
    if np.linalg.norm(wanted) < 1e-6:
        return current
    wanted = wanted / np.linalg.norm(wanted) * np.linalg.norm(rest)   # reachable: on that sphere
    limits = [LIMITS[key] for key in keys]
    x = np.array([current[key] for key in keys], float)

    def residual(values):
        return torso_of(dict(current, **dict(zip(keys, values)))) @ rest - wanted
    x = _least_squares(residual, x, limits)
    return dict(current, **dict(zip(keys, (float(v) for v in x))))


def _plant_legs(frame, current, result, feet):
    """Legs of `result` re-solved so that the ankles are at `feet` (unlifted, seen from the pelvis)."""
    for side in ('r', 'l'):
        limb, ankle = f'{side}_leg', f'{side}_ankle'
        root, parent = frame.limb_frame(result, limb)
        options = []
        for values in _reach_candidates(limb)(result, (parent.T @ (feet[side] - root)) / frame.k):
            trial = dict(result, **{limb: _bound(values, LIMITS['leg'])})
            raw = skeleton(dict(trial, seat=0.0), frame.height)[JOINTS.index(ankle)]   # pelvis at y = 0
            error = float(np.linalg.norm(raw - feet[side]))
            change = sum(abs(a - b) for a, b in zip(trial[limb], current[limb]))
            options.append((round(error, 4), change, trial))
        if options:
            result = min(options, key=lambda o: (o[0], o[1]))[2]
    return result


def tilt_pelvis(item, angles, joint, world_target):
    """Tilt the pelvis about the other hip so that the dragged hip rises or drops towards a world
    point (seen from the front of the body); the feet stay where they are and the upper body
    keeps its angles (it only rises or comes down with the pelvis). When a straight leg can no
    longer reach its foot, the body comes down just enough (the other knee bends), the way a hip
    is raised standing. Seated, the seat height follows."""
    if HANDLES.get(joint, (None,))[0] != 'tilt_pelvis':
        raise ValueError(f'{joint} is not a hip.')
    frame = _Frame(item, angles)
    current = frame.angles
    points = skeleton(current, frame.height)
    sign = -1 if joint.startswith('r_') else 1
    other = frame.unlifted(current, points[JOINTS.index(('l' if sign < 0 else 'r') + '_hip')])
    wanted = frame.unlifted(current, frame.local(world_target)) - other
    across = hip_offset(sign) - hip_offset(-sign)             # from the other hip, untilted
    tilt = math.degrees(math.atan2(wanted[1], wanted[0]) - math.atan2(across[1], across[0]))
    tilt = _bound((_wrap(tilt),), (LIMITS['tilt'],))[0]
    tilted = pelvis_of({'tilt': tilt})
    # the pelvis centre rises (or drops) so that the other hip stays where it was
    rise = other[1] - (tilted @ hip_offset(-sign) * frame.k)[1]
    feet = {side: frame.unlifted(current, points[JOINTS.index(f'{side}_ankle')]) for side in ('r', 'l')}
    result = dict(current, tilt=tilt)
    if current['seat'] is not None:
        result['seat'] = _bound((current['seat'] + rise / frame.k,), (LIMITS['seat'],))[0]
        rise = (result['seat'] - current['seat']) * frame.k
    else:
        reach_length = (THIGH + SHIN) * frame.k * 0.9999
        for side in ('r', 'l'):     # the feet come first
            c = feet[side] - tilted @ hip_offset(-1 if side == 'r' else 1) * frame.k
            flat = c[0] ** 2 + c[2] ** 2
            if flat < reach_length ** 2:
                rise = min(rise, c[1] + math.sqrt(reach_length ** 2 - flat))
    feet = {side: foot - np.array([0.0, rise, 0.0]) for side, foot in feet.items()}
    return _plant_legs(frame, current, result, feet)


def shift_pelvis(item, angles, world_target, joint='pelvis'):
    """Move the pelvis with the feet kept where they are: the legs bend or straighten (never
    beyond their length: the pelvis then stays lower than the point), a seated figure changes its
    seat height. Returns (angles, world shift): the character's position must move by that
    horizontal shift for the feet to stay put."""
    if HANDLES.get(joint, (None,))[0] != 'shift_pelvis':
        raise ValueError(f'{joint} is not the pelvis.')
    frame = _Frame(item, angles)
    current = frame.angles
    points = skeleton(current, frame.height)
    delta = frame.local(world_target) - handle_point(points, joint)
    # The feet come first: a pelvis too high for a leg to reach its foot comes down just enough.
    reach_length = (THIGH + SHIN) * frame.k * 0.9999
    for side in ('r', 'l'):
        root, _ = frame.limb_frame(current, f'{side}_leg')
        c = frame.unlifted(current, points[JOINTS.index(f'{side}_ankle')]) - root - [delta[0], 0.0, delta[2]]
        flat = c[0] ** 2 + c[2] ** 2
        if flat < reach_length ** 2:
            delta[1] = min(delta[1], c[1] + math.sqrt(reach_length ** 2 - flat))
    result = dict(current)
    if current['seat'] is not None:
        result['seat'] = _bound((current['seat'] + delta[1] / frame.k,), (LIMITS['seat'],))[0]
    feet = {side: frame.unlifted(current, points[JOINTS.index(f'{side}_ankle')]) - delta for side in ('r', 'l')}
    result = _plant_legs(frame, current, result, feet)
    rotation = _object_matrix(item, frame.height)[:3, :3]
    shift = rotation @ np.array([delta[0], 0.0, delta[2]])
    return result, np.array([shift[0], 0.0, shift[2]])


def curl(item, angles, joint, world_target):
    """Curl one finger (only its own curl changes) so that its tip comes as close as possible to
    a world point."""
    if HANDLES.get(joint, (None,))[0] != 'curl':
        raise ValueError(f'{joint} is not a finger.')
    side, finger = joint.split('_')
    index = FINGERS.index(finger)
    frame = _Frame(item, angles)
    current = frame.angles
    target = frame.local(world_target)
    key = f'{side}_hand'

    def with_curl(value):
        values = list(current[key])
        values[index] = float(value)
        return dict(current, **{key: tuple(values)})

    def distance(value):
        return float(np.linalg.norm(skeleton(with_curl(value), frame.height, hands=True)[1][side][4 + index * 4]
                                    - target))
    values = np.linspace(0.0, 100.0, 41)
    best = min(values, key=distance)
    low, high = max(0.0, best - 2.5), min(100.0, best + 2.5)
    for _ in range(30):     # golden-section refinement around the best sample
        a, b = low + (high - low) * 0.382, low + (high - low) * 0.618
        if distance(a) < distance(b):
            high = b
        else:
            low = a
    return with_curl((low + high) / 2)


def bend_wrist(item, angles, joint, world_target):
    """Bend a wrist (towards the palm or the back of the hand, towards the thumb or the little
    finger) so that the hand points at a world point; the fingers keep their curl."""
    if HANDLES.get(joint, (None,))[0] != 'bend_wrist':
        raise ValueError(f'{joint} is not a palm.')
    side = joint[0]
    key = f'{side}_hand'
    frame = _Frame(item, angles)
    current = frame.angles
    _, hands = skeleton(current, frame.height, hands=True)
    wrist = hands[side][0]
    reach_length = float(np.linalg.norm(hands[side][9] - wrist))     # the knuckles stay at their distance
    wanted = frame.local(world_target) - wrist
    if np.linalg.norm(wanted) < 1e-6:
        return current
    wanted = wanted / np.linalg.norm(wanted) * reach_length

    def with_wrist(values):
        hand = list(current[key])
        hand[6], hand[7] = float(values[0]), float(values[1])
        return dict(current, **{key: tuple(hand)})

    def residual(values):
        points = skeleton(with_wrist(values), frame.height, hands=True)[1][side]
        return points[9] - points[0] - wanted
    x = _least_squares(residual, [current[key][6], current[key][7]], LIMITS['hand'][6:8])
    return with_wrist(x)


def _least_squares(residual, start, limits, iterations=80):
    """Levenberg-Marquardt within bounds, from the current values: the nearest solution wins."""
    x = np.array(start, float)
    size = len(x)
    damping = 1e-3
    error = residual(x)
    for _ in range(iterations):
        if np.linalg.norm(error) < 1e-8:
            break
        jacobian = np.stack([(residual(x + step) - error) / 1e-5 for step in np.eye(size) * 1e-5], axis=1)
        step = np.linalg.solve(jacobian.T @ jacobian + damping * np.eye(size), -jacobian.T @ error)
        trial = np.array(_bound(x + step, limits))
        trial_error = residual(trial)
        if np.linalg.norm(trial_error) < np.linalg.norm(error):
            x, error, damping = trial, trial_error, max(damping / 3, 1e-9)
        else:
            damping *= 10
            if damping > 1e6:
                break
    return x


def bend_toes(item, angles, joint, world_target):
    """Bend the toes of one foot (up, or curled down) so that their tips come as close as
    possible to a world point; the rest of the pose is kept."""
    if HANDLES.get(joint, (None,))[0] != 'bend_toes':
        raise ValueError(f'{joint} are not toes.')
    side = joint[0]
    key = f'{side}_foot'
    frame = _Frame(item, angles)
    current = frame.angles
    target = frame.local(world_target)

    def with_toes(value):
        return dict(current, **{key: (current[key][0], float(value))})

    def distance(value):
        return float(np.linalg.norm(skeleton(with_toes(value), frame.height, feet=True)[1][side][3] - target))
    low, high = LIMITS['foot'][1]
    best = min(np.linspace(low, high, 45), key=distance)
    step = (high - low) / 44
    low, high = max(low, best - step), min(high, best + step)
    for _ in range(30):     # golden-section refinement around the best sample
        a, b = low + (high - low) * 0.382, low + (high - low) * 0.618
        if distance(a) < distance(b):
            high = b
        else:
            low = a
    return with_toes((low + high) / 2)


def world_feet(item, t=0.0, library=None):
    """{'r': (4, 3), 'l': (4, 3)}: ankle, heel, ball and toe tips of a character in world space."""
    angles = item.get('poseAngles') or pose_of(item, t, library)
    height = height_of(item)
    _, soles = skeleton(angles, height, feet=True)
    matrix = _object_matrix(item, height)
    return {side: (np.c_[points, np.ones(len(points))] @ matrix.T)[:, :3] for side, points in soles.items()}


def world_hands(item, t=0.0, library=None):
    """{'r': (21, 3), 'l': (21, 3)}: the hand points of a character in world space at t."""
    from .render3d import model_matrix
    angles = item.get('poseAngles') or pose_of(item, t, library)
    height = height_of(item)
    _, hands = skeleton(angles, height, hands=True)
    matrix = _object_matrix(item, height)
    return {side: (np.c_[points, np.ones(len(points))] @ matrix.T)[:, :3] for side, points in hands.items()}


def look_point(item, angles, t=0.0):
    """Where the head handle sits: in front of the face, along where it looks."""
    joints = world_joints(dict(item, poseAngles=angles), t)
    head = (joints[JOINTS.index('r_ear')] + joints[JOINTS.index('l_ear')]) / 2
    face = joints[JOINTS.index('nose')] - head
    face /= max(np.linalg.norm(face), 1e-9)
    return head + face * LOOK_DISTANCE * height_of(item) / 1.8


def world_joints(item, t=0.0, height=None, library=None):
    """The 18 joints of a character object in world space at t."""
    from .render3d import model_matrix
    angles = item.get('poseAngles') or pose_of(item, t, library)
    scale = item.get('scale') or [1, 1, 1]
    if height is None:
        height = 1.8 * float(scale[1]) if item.get('shape') == 'mannequin' else float(scale[1])
    local = skeleton(angles, height)
    matrix = model_matrix(item['position'], item['rotation'], [1, 1, 1])
    if item.get('shape') == 'capsule':   # a capsule's origin is its centre, not its feet
        matrix = model_matrix([item['position'][0], item['position'][1] - height / 2, item['position'][2]],
                              item['rotation'], [1, 1, 1])
    return (np.c_[local, np.ones(len(local))] @ matrix.T)[:, :3]


def is_character(item):
    return item.get('role') == 'character' and item.get('shape') in ('mannequin', 'capsule')


def draw(characters, camera, size, stroke=None, hands=True, feet=True):
    """OpenPose picture (RGB uint8) of the given characters [(item, t)] seen by `camera`; with
    hands=True the hands are drawn too (OpenPose hand model: 21 points, rainbow bones); with feet=True
    the feet (OpenPose BODY_25: heel, big toe and small toe from each ankle)."""
    import colorsys
    from PIL import Image, ImageDraw
    from .render3d import camera_matrices
    width, height = size
    image = Image.new('RGB', size, (0, 0, 0))
    canvas = ImageDraw.Draw(image)
    view, projection = camera_matrices(camera, width / height)
    stroke = stroke or max(2, round(4 * min(width, height) / 512))
    eye = np.asarray(camera['position'], float)
    for item, t in characters:
        joints = world_joints(item, t)
        clip = (np.c_[joints, np.ones(len(joints))] @ (projection @ view).T)
        visible = clip[:, 3] > 0.05
        screen = np.zeros((len(joints), 2))
        screen[visible, 0] = (clip[visible, 0] / clip[visible, 3] * 0.5 + 0.5) * width
        screen[visible, 1] = (0.5 - clip[visible, 1] / clip[visible, 3] * 0.5) * height
        # Seen from behind, OpenPose finds no nose or eyes: leave them out.
        facing = joints[JOINTS.index('nose')] - (joints[JOINTS.index('r_ear')] + joints[JOINTS.index('l_ear')]) / 2
        if float(facing @ (eye - joints[JOINTS.index('nose')])) < 0:
            for name in ('nose', 'r_eye', 'l_eye'):
                visible[JOINTS.index(name)] = False
        for (a, b), colour in zip(LIMBS, COLOURS):
            if a == 1 and b == 0 and not visible[0]:
                continue
            if visible[a] and visible[b]:
                canvas.line([tuple(screen[a]), tuple(screen[b])], fill=tuple(int(c * 0.6) for c in colour),
                            width=stroke)
        for index, colour in enumerate(COLOURS):
            if visible[index]:
                x, y = screen[index]
                canvas.ellipse([x - stroke, y - stroke, x + stroke, y + stroke], fill=colour)
        if feet:
            for side, points in world_feet(item, t).items():
                points = points[[0, 1, 4, 5]]        # ankle, heel, big toe, small toe
                clip = (np.c_[points, np.ones(len(points))] @ (projection @ view).T)
                if (clip[:4, 3] <= 0.05).any():
                    continue
                flat = np.c_[(clip[:, 0] / clip[:, 3] * 0.5 + 0.5) * width, (0.5 - clip[:, 1] / clip[:, 3] * 0.5) * height]
                if np.linalg.norm(flat[1] - flat[2]) < 4:   # too small to read
                    continue
                colour = FOOT_COLOURS[side]
                for a, b in ((0, 1), (0, 2), (2, 3)):
                    canvas.line([tuple(flat[a]), tuple(flat[b])], fill=tuple(int(c * 0.6) for c in colour), width=stroke)
                for x, y in flat[1:4]:
                    canvas.ellipse([x - stroke, y - stroke, x + stroke, y + stroke], fill=colour)
        if not hands:
            continue
        for points in world_hands(item, t).values():
            clip = (np.c_[points, np.ones(len(points))] @ (projection @ view).T)
            if (clip[:, 3] <= 0.05).any():
                continue
            flat = np.c_[(clip[:, 0] / clip[:, 3] * 0.5 + 0.5) * width, (0.5 - clip[:, 1] / clip[:, 3] * 0.5) * height]
            if np.linalg.norm(flat[0] - flat[12]) < 6:   # too small to read: OpenPose would find nothing
                continue
            thin = max(1, stroke // 2)
            for number, (a, b) in enumerate(HAND_LIMBS):
                red, green, blue = colorsys.hsv_to_rgb(number / len(HAND_LIMBS), 1.0, 1.0)
                canvas.line([tuple(flat[a]), tuple(flat[b])], fill=(int(red * 255), int(green * 255), int(blue * 255)),
                            width=thin)
            for x, y in flat:
                canvas.ellipse([x - thin, y - thin, x + thin, y + thin], fill=(0, 0, 255))
    return np.asarray(image)

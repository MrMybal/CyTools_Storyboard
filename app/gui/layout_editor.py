"""Layout tab: stage a panel in 3D (simple shapes, cameras) or draw it in 2D.

3D views are rendered by a worker thread that owns its own offscreen GL context: creating
one on the window's thread would replace the context ImGui draws with. The window sends the
latest request (a copy of the stage, the camera, the size) and shows the last finished
image; ImGuizmo draws the move/rotate/scale gizmo on top of it with the same matrices.
"""
import copy
import json
import math
import sys
import threading
import time

import numpy as np
from imgui_bundle import hello_imgui, imgui as native, imguizmo

from ui_common import imgui, tr
from gui.common import colour, dialogs, hex_colour
from storyboard import layout, model, render3d
from storyboard.model import StoryboardError

G = imguizmo.im_guizmo
SHAPE_BUTTONS = [('Box', 'box'), ('Sphere', 'sphere'), ('Cylinder', 'cylinder'), ('Cone', 'cone'),
                 ('Capsule', 'capsule'), ('Plane', 'plane'), ('Mannequin', 'mannequin')]
TOOLS = ['select', 'rect', 'ellipse', 'line', 'arrow', 'stroke', 'figure', 'text']
TOOL_LABELS = ['Select', 'Rectangle', 'Ellipse', 'Line', 'Arrow', 'Pen', 'Figure', 'Text']
MESH_FILTER = ['Meshes', '*.glb *.gltf *.obj *.ply *.stl *.off']



TOE_HANDLES_FROM = 22       # pixels from the ankle to the toe tips before the toes get a handle
PALM_HANDLES_FROM = 30      # pixels from the wrist to the middle fingertip before the palm gets a handle
FINGER_HANDLES_FROM = 45    # pixels from the wrist to the middle fingertip before the fingers get handles
FINGER_COLOURS = ((255, 90, 90), (255, 200, 60), (90, 220, 90), (80, 180, 255), (200, 110, 255))
HIP_GEARING = 4     # default: a hip handle moves four times less than the mouse
_test_gearing = None  # set by --ui-test-layout=...,gearing:N (not saved)


def hip_gearing():
    """Hip handle gearing (1 = direct), kept in the UI preferences."""
    from ui_common import preferences
    if _test_gearing is not None:
        return _test_gearing
    try:
        return min(10, max(1, int(preferences.values.get('hip_gearing', HIP_GEARING))))
    except (TypeError, ValueError):
        return HIP_GEARING


def set_hip_gearing(value):
    from ui_common import preferences
    preferences.values['hip_gearing'] = min(10, max(1, int(value)))
    preferences.save()

class RenderWorker:
    """Latest-request-wins rendering on a thread with its own GL context."""

    def __init__(self):
        self._lock = threading.Condition()
        self._request = None
        self._stop = False
        self.result = None           # (key, color, ids)
        self.error = ''
        self.panel_jobs = []         # (board folder, doc copy, panel id) -> results
        self.panel_results = []
        self.thread = threading.Thread(target=self._run, daemon=True, name='storyboard-3d')
        self.thread.start()

    def request(self, key, stage, camera, size, overrides, selected, folder, cameras, want_ids, t=0.0, poses=None):
        with self._lock:
            self._request = (key, copy.deepcopy(stage), dict(camera), size, copy.deepcopy(overrides), selected,
                             folder, cameras, want_ids, t, copy.deepcopy(poses))
            self._lock.notify()

    def render_panel(self, board, panel_id):
        with self._lock:
            self.panel_jobs.append((board.folder, copy.deepcopy(board.doc), panel_id))
            self._lock.notify()

    def close(self):
        with self._lock:
            self._stop = True
            self._lock.notify()

    def _run(self):
        while True:
            with self._lock:
                self._lock.wait_for(lambda: self._stop or self._request or self.panel_jobs)
                if self._stop:
                    return
                request, self._request = self._request, None
                jobs, self.panel_jobs = self.panel_jobs, []
            try:
                renderer = render3d.renderer()
                if request:
                    key, stage, camera, size, overrides, selected, folder, cameras, want_ids, t, poses = request
                    out = renderer.render(stage, camera, size, overrides, selected, folder, True, cameras, False,
                                          want_ids, t=t, poses=poses)
                    self.result = (key, out['color'], out['ids'])
                for folder, doc, panel_id in jobs:
                    board = model.Storyboard(folder, doc)
                    rendered = layout.render_panel(board, panel_id)
                    self.panel_results.append((panel_id, rendered['render'], rendered['depth']))
                self.error = ''
            except Exception as exc:  # shown in the tab, never kills the thread
                self.error = f'{type(exc).__name__}: {exc}'


class Orbit:
    """The editor's own view camera, orbiting a target."""

    def __init__(self):
        self.target = np.array([0.0, 1.0, 0.0])
        self.yaw, self.pitch, self.distance = 30.0, 22.0, 11.0
        self.fov = 45.0

    def camera(self):
        yaw, pitch = math.radians(self.yaw), math.radians(self.pitch)
        offset = np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch)])
        return {'position': list(self.target + offset * self.distance), 'target': list(self.target),
                'fov': self.fov, 'roll': 0.0}

    def set_from(self, camera):
        position, target = np.asarray(camera['position'], float), np.asarray(camera['target'], float)
        delta = position - target
        self.distance = max(float(np.linalg.norm(delta)), 0.2)
        self.target = target
        self.pitch = math.degrees(math.asin(max(-1.0, min(1.0, delta[1] / self.distance))))
        self.yaw = math.degrees(math.atan2(delta[0], delta[2]))
        self.fov = camera.get('fov', self.fov)


def orbit_camera(camera, dx, dy, pan=False, zoom=0.0):
    """Move a shot camera with the same gestures as the view (orbit, pan, dolly)."""
    orbit = Orbit()
    orbit.set_from(camera)
    if pan:
        view = render3d.look_at(camera['position'], camera['target'])
        right, up = view[0, :3], view[1, :3]
        shift = (-right * dx + up * dy) * orbit.distance * 0.0015
        orbit.target = orbit.target + shift
    else:
        orbit.yaw -= dx * 0.3
        orbit.pitch = max(-85.0, min(85.0, orbit.pitch + dy * 0.3))
    if zoom:
        orbit.distance = max(0.3, orbit.distance * (0.9 ** zoom))
    result = orbit.camera()
    result['fov'] = camera.get('fov', 40.0)
    result['roll'] = camera.get('roll', 0.0)
    return result


class LayoutEditor:
    def __init__(self, editor):
        self.editor = editor
        self.worker = RenderWorker()
        self.orbits = {}
        self.pilot = 0               # 0 view, 1 start camera, 2 end camera
        self.selected_object = None
        self.operation = 0
        self.panel_only = True
        self.texture = None
        self.texture_key = None
        self.last_key = None
        self.pending_pick = None
        self.last_layout_hash = {}
        self.changed_at = {}
        self.tool = 0
        self.draw_colour = [0.1, 0.1, 0.12]
        self.draw_width = 3.0
        self.draw_fill = False
        self.stroke = None
        self.selected_item = None
        self.drag_origin = None
        self.message = ''
        self.moment = 0.0          # 0..1 of the panel, for moving characters and poses
        self.edit_end = False      # the gizmo moves the end placement of the selected object
        self.joint_target = 'pose'  # which pose the joint sliders edit: 'pose' or 'poseEnd'
        self.symmetric = False
        self.show_handles = True   # hand and foot handles of the selected character in the 3D view
        self.show_fingers = True   # fingertip handles (shown when the hand is large enough on screen)
        self.dragging = None
        self.drag_depth = None
        self.drag_start = None     # pose at the start of a geared (hip) drag
        # UI checks: --ui-test-layout=panel:4,select:Lea,pilot:1
        self.test = dict(part.split(':', 1) for part in next(
            (a.split('=', 1)[1] for a in sys.argv if a.startswith('--ui-test-layout=')), '').split(',') if ':' in part)

    def apply_test(self):
        if not self.test or not self.board:
            return
        test, self.test = self.test, {}
        panels = self.board.panels()
        if 'panel' in test:
            self.editor.selected = panels[int(test['panel']) - 1]['id']
        if 'pilot' in test:
            self.pilot = int(test['pilot'])
        if 'moment' in test:
            self.moment = float(test['moment'])
        self.open_joints = 'joints' in test
        self.test_orbit = test.get('orbit')
        if 'gearing' in test:
            global _test_gearing
            _test_gearing = int(test['gearing'])
        if 'drag' in test:  # drag:<joint>/<dx>/<dy> - a simulated mouse drag of a hand or foot handle
            joint, dx, dy = test['drag'].split('/')
            self.test_drag = {'joint': joint, 'offset': (float(dx), float(dy)), 'frame': 0}
        if 'select' in test:
            for stage in layout.stages(self.board):
                for obj in stage['objects']:
                    if obj['name'] == test['select']:
                        self.selected_object = obj['id']
        if 'item' in test:
            self.selected_item = int(test['item'])

    @property
    def board(self):
        return self.editor.board

    def panel(self):
        if not self.board or not self.editor.selected:
            return None
        try:
            return self.board.find(self.editor.selected)[2]
        except StoryboardError:
            return None

    # ------------------------------------------------------------------ per-frame upkeep
    def poll(self):
        """Apply finished panel renders and start new ones when a layout settled."""
        while self.worker.panel_results:
            panel_id, render, depth = self.worker.panel_results.pop(0)
            try:
                _, _, panel = self.board.find(panel_id)
            except (StoryboardError, AttributeError):
                continue
            state = layout.ensure(panel)
            state['render'], state['depth'] = render, depth
        if not self.board:
            return
        now = time.monotonic()
        for panel in self.board.panels():
            state = layout.ensure(panel)
            if state['mode'] == 'image':
                continue
            stage = {}
            if state['mode'] == '3d' and state['stage']:
                try:
                    stage = layout.stage(self.board, state['stage'])
                except StoryboardError:
                    stage = {}
            digest = json.dumps([state['mode'], state['stage'], state['camera'], state['overrides'], state['drawing'],
                                 stage, self.board.doc['settings']['aspect']], sort_keys=True)
            known = self.last_layout_hash.get(panel['id'])
            if known != digest:
                self.last_layout_hash[panel['id']] = digest
                # A layout seen for the first time with its picture already made needs no render.
                if known is not None or not (state.get('render') and (self.board.folder / state['render']).is_file()):
                    self.changed_at[panel['id']] = now
            elif panel['id'] in self.changed_at and now - self.changed_at[panel['id']] > 1.2:
                del self.changed_at[panel['id']]
                if state['mode'] == '2d' or state['stage']:
                    self.worker.render_panel(self.board, panel['id'])

    # ------------------------------------------------------------------ summary in the inspector
    def summary(self, panel):
        state = layout.ensure(panel)
        modes = ['Image', '2D drawing', '3D stage']
        index = layout.MODES.index(state['mode'])
        for position, label in enumerate(modes):
            if position:
                native.same_line()
            if native.radio_button(tr(label) + f'##mode{position}', index == position):
                state['mode'] = layout.MODES[position]
                if state['mode'] == '3d' and not state['stage'] and layout.stages(self.board):
                    state['stage'] = layout.stages(self.board)[0]['id']
        native.same_line()
        if imgui.small_button('Edit the layout'):
            self.editor.select_tab = 'Layout'
        if state['mode'] != 'image' and state.get('render'):
            native.push_text_wrap_pos(0.0)
            native.text_disabled(tr('The layout picture is the panel image; it updates a second after a change.'))
            native.pop_text_wrap_pos()

    # ------------------------------------------------------------------ tab
    def draw(self):
        board = self.board
        panel = self.panel()
        if not board or panel is None:
            native.text_wrapped(tr('Select a panel in the Storyboard tab first.'))
            return
        self.apply_test()
        self.poll()
        panel = self.panel()
        panels = board.panels()
        ids = [p['id'] for p in panels]
        index = ids.index(panel['id'])
        if imgui.small_button('<') and index:
            self.editor.selected = ids[index - 1]
        native.same_line()
        native.set_next_item_width(260)
        changed, index = native.combo('##panel', index, [f'{i + 1}. {p["title"]}' for i, p in enumerate(panels)])
        if changed:
            self.editor.selected = ids[index]
        native.same_line()
        if imgui.small_button('>') and index + 1 < len(ids):
            self.editor.selected = ids[index + 1]
        native.same_line()
        self.summary(panel)
        if self.worker.error:
            native.text_colored(native.ImVec4(1, .4, .35, 1), self.worker.error)
        if self.message:
            native.text_colored(native.ImVec4(1, .7, .35, 1), self.message)
        state = layout.ensure(panel)
        if state['mode'] == '3d':
            self.draw_3d(panel, state)
        elif state['mode'] == '2d':
            self.draw_2d(panel, state)
        else:
            native.text_wrapped(tr('This panel uses its imported images. Choose 2D drawing or 3D stage above to stage it.'))

    # ------------------------------------------------------------------ 3D
    def draw_3d(self, panel, state):
        board = self.board
        stages = layout.stages(board)
        avail = native.get_content_region_avail()
        native.begin_child('stage-side', native.ImVec2(310, avail.y), native.ChildFlags_.borders)
        names = [s['name'] for s in stages]
        current = next((i for i, s in enumerate(stages) if s['id'] == state['stage']), -1)
        native.set_next_item_width(180)
        changed, current = native.combo(tr('Stage') + '##stage', max(current, 0), names or ['-'])
        if changed and stages:
            state['stage'] = stages[current]['id']
        native.same_line()
        if imgui.small_button('New##stage'):
            new = layout.add_stage(board)
            state['stage'] = new['id']
        stage = None
        if state['stage']:
            try:
                stage = layout.stage(board, state['stage'])
            except StoryboardError:
                state['stage'] = ''
        if stage is None:
            native.text_wrapped(tr('Create a stage (New) to place shapes and cameras.'))
            native.end_child()
            return
        native.set_next_item_width(-1)
        _, stage['name'] = imgui.input_text('##stagename', stage['name'])
        used_by = sum(1 for p in board.panels() if layout.ensure(p)['stage'] == stage['id'])
        native.text_disabled(f'{tr("Used by")} {used_by} {tr("panels")}')
        _, stage['ground'] = imgui.checkbox('Ground', bool(stage.get('ground', True)))
        native.same_line()
        value = colour(stage.get('sky', '#9aa7b8'))
        changed, picked = native.color_edit3(tr('Sky') + '##sky', [value.x, value.y, value.z], native.ColorEditFlags_.no_inputs)
        if changed:
            stage['sky'] = hex_colour(picked)
        native.separator_text(tr('Add'))
        for position, (label, shape) in enumerate(SHAPE_BUTTONS):
            if position % 4:
                native.same_line()
            if imgui.small_button(label):
                obj = layout.add_object(board, stage['id'], shape)
                obj['position'][0], obj['position'][2] = float(self._view(stage).target[0]), float(self._view(stage).target[2])
                self.selected_object = obj['id']
        if imgui.small_button('Import a mesh...'):
            dialogs.open('mesh', 'Import a mesh', MESH_FILTER)
        chosen = dialogs.result('mesh')
        if chosen:
            try:
                obj = layout.add_object(board, stage['id'], 'mesh', mesh=chosen[0])
                self.selected_object = obj['id']
            except StoryboardError as exc:
                self.message = str(exc)
        native.separator_text(tr('Objects'))
        overrides = state['overrides']
        for obj in stage['objects']:
            marker = ' *' if obj['id'] in overrides else ''
            if native.selectable(f'{obj["name"]} ({tr(obj["shape"])}){marker}##{obj["id"]}',
                                 self.selected_object == obj['id'])[0]:
                self.selected_object = obj['id']
        native.text_disabled(tr('* moved in this panel only'))
        self.object_panel(stage, state)
        native.end_child()
        native.same_line()
        native.begin_child('stage-view', native.ImVec2(0, avail.y), native.ChildFlags_.borders)
        self.camera_bar(panel, state, stage)
        self.viewport(panel, state, stage)
        native.end_child()

    def _view(self, stage):
        if stage['id'] not in self.orbits and getattr(self, 'test_orbit', None):
            # UI checks: orbit:<x>/<y>/<z>/<distance>/<yaw>/<pitch> - where the view looks from the start
            x, y, z, distance, yaw, pitch = (float(v) for v in self.test_orbit.split('/'))
            view = Orbit()
            view.target, view.distance, view.yaw, view.pitch = np.array([x, y, z]), distance, yaw, pitch
            self.orbits[stage['id']] = view
        return self.orbits.setdefault(stage['id'], Orbit())

    def object_panel(self, stage, state):
        board = self.board
        obj = next((o for o in stage['objects'] if o['id'] == self.selected_object), None)
        if obj is None:
            return
        native.separator_text(tr('Selected object'))
        native.set_next_item_width(-1)
        _, obj['name'] = imgui.input_text('##objname', obj['name'])
        roles = list(layout.ROLES)
        native.set_next_item_width(120)
        _, role = imgui.combo('Role', roles.index(obj['role']), roles)
        obj['role'] = roles[role]
        value = colour(obj.get('color'))
        native.same_line()
        changed, picked = native.color_edit3('##objcolour', [value.x, value.y, value.z], native.ColorEditFlags_.no_inputs)
        if changed:
            obj['color'] = hex_colour(picked)
        library = board.doc['library']
        options = ['-'] + [f'{i["name"]} ({i["kind"]})' for i in library]
        ids = [''] + [i['id'] for i in library]
        current = ids.index(obj.get('reference', '')) if obj.get('reference', '') in ids else 0
        native.set_next_item_width(-1)
        changed, current = native.combo('##reference', current, options)
        if changed:
            obj['reference'] = ids[current]
            if ids[current] and obj['name'] in (obj['shape'].title(), ''):
                obj['name'] = library[current - 1]['name']
        native.text_disabled(tr('Reference: what this shape stands for.'))
        _, self.panel_only = imgui.checkbox('Move in this panel only', self.panel_only)
        target = self._transform_target(obj, state, end=False)
        for key, speed in (('position', 0.02), ('rotation', 0.5), ('scale', 0.01)):
            native.set_next_item_width(-80)
            changed, values = native.drag_float3(tr(key.title()) + f'##{key}', list(target[key]), speed)
            if changed:
                self._write_transform(obj, state, key, values, end=False)
        override = state['overrides'].get(obj['id'], {})
        if obj['role'] == 'character' and obj['shape'] in ('mannequin', 'capsule'):
            self.pose_panel(obj, state, override)
        changed, hidden = imgui.checkbox('Hidden in this panel', bool(override.get('hidden')))
        if changed:
            layout.override_object(board, self.editor.selected, obj['id'], hidden=hidden)
        if obj['id'] in state['overrides'] and imgui.small_button('Back to the stage placement'):
            layout.clear_override(board, self.editor.selected, obj['id'])
        if imgui.small_button('Duplicate##obj'):
            self.selected_object = layout.duplicate_object(board, obj['id'])['id']
        native.same_line()
        if imgui.small_button('Delete##obj'):
            layout.remove_object(board, obj['id'])
            self.selected_object = None

    def pose_panel(self, obj, state, override):
        """Pose of a character, its end pose and its move during the panel."""
        from storyboard import pose
        native.separator_text(tr('Pose'))
        library = pose.library_of(layout.poses(self.board))
        names = list(pose.NAMES) + list(library)
        labels = [tr(n) for n in pose.NAMES] + [library[i]['name'] for i in library]
        current = override.get('pose') or obj.get('pose') or 'standing'
        if current not in names:
            current = 'standing'
        native.set_next_item_width(150)
        changed, index = native.combo(tr('Pose') + '##pose', names.index(current), labels)
        if changed:
            self._set_pose(obj, 'pose', names[index])
        native.same_line()
        ends = [''] + names
        end = override.get('poseEnd', '') if override.get('poseEnd', '') in ends else ''
        native.set_next_item_width(150)
        changed, index = native.combo(tr('At the end') + '##poseend', ends.index(end), [tr('same pose')] + labels)
        if changed:
            layout.override_object(self.board, self.editor.selected, obj['id'], poseEnd=ends[index])
        if getattr(self, 'open_joints', False):
            native.set_next_item_open(True)
        if native.tree_node(tr('Joints') + '###joints'):
            self.joints_panel(obj, current, end, library)
            native.tree_pop()
        moving = bool(override.get('positionEnd'))
        changed, moving = imgui.checkbox('Moves during the panel', moving)
        if changed:
            placed = self._transform_target(obj, state, end=False)
            layout.override_object(self.board, self.editor.selected, obj['id'],
                                   positionEnd=[placed['position'][0] + 2.0, *placed['position'][1:]] if moving else None,
                                   rotationEnd=list(placed['rotation']) if moving else None)
            self.edit_end = moving
        if moving:
            native.same_line()
            _, self.edit_end = imgui.checkbox('Gizmo on the end placement', self.edit_end)
            for key in ('positionEnd', 'rotationEnd'):
                native.set_next_item_width(-80)
                label = 'End position' if key == 'positionEnd' else 'End rotation'
                changed, values = native.drag_float3(tr(label) + f'##{key}', list(override[key]),
                                                     0.02 if key == 'positionEnd' else 0.5)
                if changed:
                    layout.override_object(self.board, self.editor.selected, obj['id'], **{key: values})
            native.text_disabled(tr('A standing character that moves walks; use the Moment slider to watch it.'))

    def _set_pose(self, obj, which, value):
        if which == 'pose' and not self.panel_only:
            obj['pose'] = value
        else:
            layout.override_object(self.board, self.editor.selected, obj['id'], **{which: value})

    def joints_panel(self, obj, start, end, library):
        """Joint by joint: the start or end pose of the selected character. A preset is copied into
        a project pose (named after the character) the first time one of its joints moves."""
        from storyboard import pose
        which = self.joint_target if end else 'pose'
        if end:
            for position, (key, label) in enumerate((('pose', 'Start pose'), ('poseEnd', 'End pose'))):
                if position:
                    native.same_line()
                if native.radio_button(tr(label) + f'##jt{key}', which == key):
                    self.joint_target = which = key
        name = start if which == 'pose' else end
        entry = library.get(name)
        angles = pose.params(name, 0.0, library)
        edited = {}
        _, self.symmetric = imgui.checkbox('Symmetric (right = left)', self.symmetric)

        def slider(label, value, low, high, key=None):
            native.set_next_item_width(-150)
            changed, value = imgui.slider_float(label, float(value), low, high, '%.0f')
            return changed, value
        for key, label in (('lean', 'Lean forwards'), ('twist', 'Twist (to its left)'),
                           ('bend', 'Bend sideways (to its left)'), ('tilt', 'Pelvis tilt (left hip up)')):
            changed, value = slider(label + f'##j{key}', angles[key], *pose.LIMITS[key])
            if changed:
                edited[key] = value
        head = list(angles['head'])
        for position, label in enumerate(('Head turn (to its left)', 'Head tilt (up)')):
            changed, value = slider(label + f'##jhead{position}', head[position], *pose.LIMITS['head'][position])
            if changed:
                head[position] = value
                edited['head'] = tuple(head)
        seated = angles['seat'] is not None
        changed, seated = imgui.checkbox('Seated (pelvis at a height)', seated)
        if changed:
            edited['seat'] = 0.48 if seated else None
        if seated:
            native.same_line()
            native.set_next_item_width(120)
            changed, value = imgui.slider_float('Seat height (m)##jseat', float(angles['seat'] or 0.48), 0.2, 1.2, '%.2f')
            if changed:
                edited['seat'] = value
        for limb, titles in (('arm', ('Raise forwards', 'Raise sideways', 'Elbow bend', 'Turn the forearm outwards')),
                             ('leg', ('Raise forwards', 'Raise sideways', 'Knee bend', 'Turn the knee outwards')),
                             ('hand', ('Thumb curl (%)', 'Index curl (%)', 'Middle finger curl (%)', 'Ring finger curl (%)',
                                       'Little finger curl (%)', 'Finger spread', 'Wrist bend (towards the palm)',
                                       'Wrist towards the thumb')),
                             ('foot', ('Foot pitch (toes down)', 'Toes bent up'))):
            for side, side_label in (('r', 'Right'), ('l', 'Left')):
                key = f'{side}_{limb}'
                if self.symmetric and side == 'l':
                    continue
                both = {'foot': 'Both feet'}.get(limb, f'Both {limb}s')
                native.text(tr(f'{side_label} {limb}' if not self.symmetric else both))
                values = list(angles[key])
                for position, title in enumerate(titles):
                    changed, value = slider(tr(title) + f'##j{key}{position}', values[position],
                                            *pose.LIMITS[limb][position])
                    if changed:
                        values[position] = value
                        edited[key] = tuple(values)
                        if self.symmetric:
                            edited[f'l_{limb}'] = tuple(values)
        if entry:
            native.set_next_item_width(200)
            changed, new_name = imgui.input_text('Pose name##jname', entry['name'])
            if changed:
                layout.update_pose(self.board, entry['id'], name=new_name)
            _, walks = imgui.checkbox('Walks when the character moves', bool(entry.get('walks', True)))
            if walks != bool(entry.get('walks', True)):
                layout.update_pose(self.board, entry['id'], walks=walks)
            if imgui.small_button('Delete this project pose'):
                layout.remove_pose(self.board, entry['id'])
                return
        else:
            native.text_disabled(tr('A preset: moving a joint makes an editable copy of it for this project.'))
        if edited:
            self._edit_pose(obj, which, name, edited)

    def _edit_pose(self, obj, which, name, edited):
        """Change some angles of a character's start or end pose; a preset is copied first."""
        from storyboard import pose
        entry = pose.library_of(layout.poses(self.board)).get(name)
        if entry is None:
            entry = layout.add_pose(self.board, f'{obj["name"]} - {tr(name)}', base=name)
            self._set_pose(obj, which, entry['id'])
        layout.update_pose(self.board, entry['id'], angles=edited)

    def _pose_being_edited(self, obj, state):
        """('pose' or 'poseEnd', its name): the one the joint sliders and the hand handles change."""
        override = state['overrides'].get(obj['id'], {})
        end = override.get('poseEnd', '')
        which = self.joint_target if end else 'pose'
        start = override.get('pose') or obj.get('pose') or 'standing'
        return which, (start if which == 'pose' else end)

    def limb_handles(self, obj, state, stage, view_camera, origin, hovered):
        """Handles on the selected character, dragged in the plane facing the camera: wrists and
        ankles (the arm or leg follows, two-bone IK), elbows and knees (the limb turns about itself,
        the hand or foot staying put) and a gaze point in front of the face (the head looks at it).
        Returns True while a handle is used."""
        from storyboard import pose
        if not self.show_handles or not pose.is_character(obj) or self.texture is None:
            self.dragging = None
            return False
        which, name = self._pose_being_edited(obj, state)
        moment = 1.0 if which == 'poseEnd' else 0.0
        moving = bool(state['overrides'].get(obj['id'], {}).get('positionEnd'))
        item = next((o for o in render3d.resolved_objects(stage, state['overrides'], moment, layout.poses(self.board))
                     if o['id'] == obj['id']), None)
        if item is None:
            return False
        width, height = self.texture.width, self.texture.height
        view, projection = render3d.camera_matrices(view_camera, width / height)
        matrix = projection @ view
        joints = pose.world_joints(item, moment)
        io = native.get_io()
        mouse = np.array([io.mouse_pos.x - origin.x, io.mouse_pos.y - origin.y])
        simulated = getattr(self, 'test_drag', None)
        draw = native.get_window_draw_list()
        shown, places = {}, {}

        def on_screen(world):
            clip = matrix @ np.append(world, 1.0)
            if clip[3] <= 0.05:
                return None
            return np.array([(clip[0] / clip[3] * 0.5 + 0.5) * width, (0.5 - clip[1] / clip[3] * 0.5) * height])
        hands = pose.world_hands(item, moment)
        feet = pose.world_feet(item, moment)
        gaze = pose.look_point(item, item.get('poseAngles') or pose.pose_of(item, moment, pose.library_of(layout.poses(self.board))), moment)
        for joint in pose.HANDLES:
            if moving and (joint.endswith('ankle') or joint.endswith('knee') or joint.endswith('hip')
                           or joint == 'pelvis'):
                continue  # a moving character walks: its legs follow the walking cycle
            if joint == 'head':
                places[joint] = gaze
                nose = on_screen(joints[pose.JOINTS.index('nose')])
                point = on_screen(gaze)
                if point is not None and nose is not None:
                    draw.add_line(native.ImVec2(origin.x + nose[0], origin.y + nose[1]),
                                  native.ImVec2(origin.x + point[0], origin.y + point[1]),
                                  native.get_color_u32(native.ImVec4(1, 1, 1, 0.6)), 1.5)
            elif joint.endswith('_toes'):
                side = joint[0]
                ankle, tip = on_screen(feet[side][0]), on_screen(feet[side][3])
                if ankle is None or tip is None or np.linalg.norm(ankle - tip) < TOE_HANDLES_FROM:
                    continue    # too close to the ankle handle on screen: zoom in
                places[joint] = feet[side][3]
                point = on_screen(places[joint])
            elif joint.endswith('_palm'):
                side = joint[0]
                wrist, middle = on_screen(hands[side][0]), on_screen(hands[side][12])
                if wrist is None or middle is None or np.linalg.norm(wrist - middle) < PALM_HANDLES_FROM:
                    continue    # too close to the wrist handle on screen: zoom in
                places[joint] = hands[side][9]
                point = on_screen(places[joint])
            elif joint in pose.FINGER_HANDLES:
                side, finger = joint.split('_')
                if not self.show_fingers:
                    continue
                wrist, middle = on_screen(hands[side][0]), on_screen(hands[side][12])
                if wrist is None or middle is None or np.linalg.norm(wrist - middle) < FINGER_HANDLES_FROM:
                    continue    # too small on screen to aim at a finger: zoom in
                places[joint] = hands[side][4 + 4 * pose.FINGERS.index(finger)]
                point = on_screen(places[joint])
            else:
                places[joint] = pose.handle_point(joints, joint)
                point = on_screen(places[joint])
            if point is None:
                continue
            shown[joint] = point
            small = joint in pose.FINGER_HANDLES
            if joint.endswith('_palm'):
                colour = (235, 235, 235)
            elif joint.endswith('_toes'):
                colour = (255, 150, 40)
            elif small:
                colour = FINGER_COLOURS[pose.FINGERS.index(joint.split('_')[1])]
            else:
                colour = pose.COLOURS[pose.JOINTS.index({'head': 'nose', 'pelvis': 'r_hip'}.get(joint, joint))]
            active = self.dragging == joint or (self.dragging is None and np.linalg.norm(mouse - point) < (6 if small else 10))
            radius = (6 if active else 4) if small else (9 if active else 6)
            centre = native.ImVec2(origin.x + point[0], origin.y + point[1])
            draw.add_circle_filled(centre, radius, native.get_color_u32(
                native.ImVec4(colour[0] / 255, colour[1] / 255, colour[2] / 255, 0.95)))
            draw.add_circle(centre, radius + 1, native.get_color_u32(native.ImVec4(1, 1, 1, 0.9)), 0, 1.5)
        if simulated and simulated['joint'] in shown:
            simulated['frame'] += 1
            if simulated['frame'] == 1:
                simulated['start'] = shown[simulated['joint']].copy()
            share = min(1.0, simulated['frame'] / 20)
            mouse = simulated['start'] + np.array(simulated['offset']) * share
            if simulated['frame'] == 1:
                self.dragging, self.moment = simulated['joint'], moment
                self.drag_depth = places[simulated['joint']]
                self.drag_start = None
            elif simulated['frame'] > 22:
                self.test_drag, self.dragging = None, None
                return False
        elif self.dragging is None and hovered and native.is_mouse_clicked(0):
            near = min(shown.items(), key=lambda kv: np.linalg.norm(mouse - kv[1]), default=None)
            if near and np.linalg.norm(mouse - near[1]) < (6 if near[0] in pose.FINGER_HANDLES else 10):
                self.dragging = near[0]
                self.moment = moment        # show exactly the pose being changed
                self.drag_depth = places[near[0]]
                self.drag_start = None
        if self.dragging and not simulated and not native.is_mouse_down(0):
            self.dragging = None
        if not self.dragging:
            return False
        # The point under the mouse on the plane through the joint, facing the camera.
        inverse = np.linalg.inv(matrix)
        ndc = np.array([mouse[0] / width * 2 - 1, 1 - mouse[1] / height * 2])
        near_point = inverse @ np.array([ndc[0], ndc[1], -1.0, 1.0])
        far_point = inverse @ np.array([ndc[0], ndc[1], 1.0, 1.0])
        near_point, far_point = near_point[:3] / near_point[3], far_point[:3] / far_point[3]
        direction = far_point - near_point
        normal = np.asarray(view_camera['target'], float) - np.asarray(view_camera['position'], float)
        normal /= max(np.linalg.norm(normal), 1e-9)
        denominator = float(direction @ normal)
        if abs(denominator) > 1e-9:
            target = near_point + direction * float((self.drag_depth - near_point) @ normal) / denominator
            current = pose.params(name, 0.0, pose.library_of(layout.poses(self.board)))
            gesture, limb = pose.HANDLES[self.dragging]
            shift = None
            if gesture == 'look':
                solved, keys = pose.look(item, current, target), ('head',)
            elif gesture == 'lean_to':
                solved, keys = pose.lean_to(item, current, self.dragging, target), ('lean', 'twist', 'bend')
            elif gesture == 'tilt_pelvis':
                # Geared: a hip is only 10 cm from the pelvis centre, so the handle moves N times
                # less than the mouse; solved from the pose at the start of the drag.
                if self.drag_start is None:
                    self.drag_start = current
                gearing = hip_gearing()
                geared = self.drag_depth + (target - self.drag_depth) / gearing
                solved = pose.tilt_pelvis(item, self.drag_start, self.dragging, geared)
                keys = ('tilt', 'r_leg', 'l_leg', 'seat')
            elif gesture == 'shift_pelvis':
                (solved, shift), keys = pose.shift_pelvis(item, current, target, self.dragging), ('r_leg', 'l_leg', 'seat')
            else:
                solved, keys = getattr(pose, gesture)(item, current, self.dragging, target), (limb,)

            def rounded(value):
                return None if value is None else tuple(round(v, 2) for v in np.atleast_1d(value))
            changed = {key: solved[key] for key in keys if rounded(solved[key]) != rounded(current[key])}
            if changed:
                self._edit_pose(obj, which, name, changed)
            if shift is not None and np.linalg.norm(shift) > 1e-5:
                # the feet stay planted: the character moves under its pelvis in this panel
                position = state['overrides'].get(obj['id'], {}).get('position') or obj['position']
                layout.override_object(self.board, self.editor.selected, obj['id'],
                                       position=list(np.asarray(position, float) + shift))
        return True

    def _transform_target(self, obj, state, end=None):
        override = state['overrides'].get(obj['id'], {})
        target = {key: override.get(key, obj[key]) for key in ('position', 'rotation', 'scale')}
        if (self.edit_end if end is None else end) and override.get('positionEnd'):
            target['position'] = override['positionEnd']
            target['rotation'] = override.get('rotationEnd') or target['rotation']
        return target

    def _write_transform(self, obj, state, key, values, end=None):
        values = [float(v) for v in values]
        override = state['overrides'].get(obj['id'], {})
        if (self.edit_end if end is None else end) and override.get('positionEnd') and key in ('position', 'rotation'):
            layout.override_object(self.board, self.editor.selected, obj['id'], **{key + 'End': values})
            return
        if self.panel_only:
            layout.override_object(self.board, self.editor.selected, obj['id'], **{key: values})
        else:
            obj[key] = values
            state['overrides'].get(obj['id'], {}).pop(key, None)

    def camera_bar(self, panel, state, stage):
        pilots = ['Free view', 'Shot camera (start)', 'Shot camera (end)']
        native.set_next_item_width(190)
        _, self.pilot = imgui.combo('Look through', self.pilot, pilots)
        if self.pilot == 2 and not state.get('cameraEnd'):
            state['cameraEnd'] = copy.deepcopy(state['camera'])
        native.same_line()
        if imgui.small_button('Start = this view'):
            state['camera'] = self._current_camera(state, stage)
        native.same_line()
        if imgui.small_button('End = this view'):
            state['cameraEnd'] = self._current_camera(state, stage)
        native.same_line()
        if state.get('cameraEnd') and imgui.small_button('No end camera'):
            state['cameraEnd'] = None
            if self.pilot == 2:
                self.pilot = 1
        native.same_line()
        operations = ['Move (W)', 'Rotate (E)', 'Scale (R)']
        native.set_next_item_width(110)
        _, self.operation = imgui.combo('##op', self.operation, operations)
        camera = state['camera'] if self.pilot != 2 else state['cameraEnd']
        native.set_next_item_width(160)
        focal = 12.0 / math.tan(math.radians(camera['fov']) / 2)
        changed, focal = imgui.slider_float('Focal (mm, 24x36)', focal, 12.0, 200.0, '%.0f mm')
        if changed:
            camera['fov'] = math.degrees(2 * math.atan(12.0 / focal))
        native.same_line()
        native.set_next_item_width(110)
        _, camera['roll'] = imgui.slider_float('Roll', float(camera.get('roll', 0.0)), -45.0, 45.0, '%.0f')
        native.same_line()
        if imgui.small_button('Suggest the camera move'):
            suggestion = layout.suggest_camera(panel)
            panel['prompt'].update(suggestion)
            self.message = tr('Prompt camera set to: ') + ' '.join(v for v in suggestion.values() if v)
        native.set_next_item_width(220)
        _, self.moment = imgui.slider_float('Moment in the panel', float(self.moment), 0.0, 1.0, '%.2f')
        native.same_line()
        _, self.show_handles = imgui.checkbox('Pose handles in the view', self.show_handles)
        if self.show_handles:
            native.same_line()
            _, self.show_fingers = imgui.checkbox('Fingers', self.show_fingers)
            if native.is_item_hovered():
                native.set_tooltip(tr('Fingertip handles, shown when a hand is large enough on screen: zoom in on it.'))
            native.same_line()
            native.set_next_item_width(110)
            changed, value = imgui.slider_int('Hip gearing##hipgearing', hip_gearing(), 1, 10, '1:%d')
            if native.is_item_hovered():
                native.set_tooltip(tr('A hip handle moves this many times less than the mouse (1:1 = direct).'))
            if changed:
                set_hip_gearing(value)
        native.same_line()
        native.text_disabled(f'{self.moment * float(panel["duration"]):.1f} s / {float(panel["duration"]):.1f} s')
        native.text_disabled(tr('Right drag: orbit - middle drag: pan - wheel: zoom - click: select - W/E/R: '
                                'move/rotate/scale. With a shot camera selected, the gestures move that camera.'))

    def _current_camera(self, state, stage):
        if self.pilot == 1:
            return copy.deepcopy(state['camera'])
        if self.pilot == 2 and state.get('cameraEnd'):
            return copy.deepcopy(state['cameraEnd'])
        camera = self._view(stage).camera()
        camera['fov'] = state['camera'].get('fov', 40.0)
        return camera

    def viewport(self, panel, state, stage):
        board = self.board
        avail = native.get_content_region_avail()
        width = max(64, int(avail.x))
        aspect_size = layout.render_size(board)
        aspect = aspect_size[0] / aspect_size[1]
        height = max(64, int(min(avail.y - 8, width / aspect if self.pilot else avail.y - 8)))
        if self.pilot:
            width = int(min(width, height * aspect))
        view_camera = self._view(stage).camera() if self.pilot == 0 else (
            state['camera'] if self.pilot == 1 else state['cameraEnd'])
        frustums = []
        if self.pilot == 0:
            frustums.append((render3d.frustum_lines(state['camera'], aspect), (1.0, 0.85, 0.2)))
            if state.get('cameraEnd'):
                frustums.append((render3d.frustum_lines(state['cameraEnd'], aspect), (1.0, 0.45, 0.15)))
            for other in board.panels():
                other_state = layout.ensure(other)
                if other['id'] != panel['id'] and other_state['mode'] == '3d' and other_state['stage'] == stage['id']:
                    frustums.append((render3d.frustum_lines(other_state['camera'], aspect, 0.5), (0.55, 0.6, 0.7)))
        key = json.dumps([stage, view_camera, state['overrides'], self.selected_object, width, height,
                          self.pilot, [f[1] for f in frustums], round(self.moment, 3), board.doc.get('poses')],
                         sort_keys=True, default=str)
        if key != self.last_key:
            self.last_key = key
            self.worker.request(key, stage, view_camera, (width, height), state['overrides'], self.selected_object,
                                board.folder, frustums, True, self.moment, board.doc.get('poses'))
        result = self.worker.result
        if result and result[0] != self.texture_key:
            rgba = np.dstack([result[1], np.full(result[1].shape[:2], 255, np.uint8)])
            self.texture = hello_imgui.create_texture_gpu_from_rgba_data(np.ascontiguousarray(rgba))
            self.texture_key = result[0]
            self.ids = result[2]
        origin = native.get_cursor_screen_pos()
        if self.texture is not None:
            native.image(native.ImTextureRef(self.texture.texture_id()), native.ImVec2(self.texture.width, self.texture.height))
        else:
            native.dummy(native.ImVec2(width, height))
        hovered = native.is_item_hovered()
        io = native.get_io()
        # Gizmo on the selected object, with the matrices the image was rendered with.
        obj = next((o for o in stage['objects'] if o['id'] == self.selected_object), None)
        using_gizmo = False
        using_handle = obj is not None and self.limb_handles(obj, state, stage, view_camera, origin, hovered)
        G.enable(not using_handle)
        if using_handle:
            using_gizmo = True
        elif obj is not None and self.texture is not None:
            view, projection = render3d.camera_matrices(view_camera, self.texture.width / self.texture.height)
            G.set_orthographic(False)
            G.set_drawlist()
            G.set_rect(origin.x, origin.y, self.texture.width, self.texture.height)
            target = self._transform_target(obj, state)
            matrix = G.Matrix16(list(render3d.model_matrix(target['position'], target['rotation'],
                                                           target['scale']).T.ravel()))
            operation = [G.OPERATION.translate, G.OPERATION.rotate, G.OPERATION.scale][self.operation]
            if G.manipulate(G.Matrix16(list(view.T.ravel())), G.Matrix16(list(projection.T.ravel())), operation,
                            G.MODE.world, matrix):
                components = G.decompose_matrix_to_components(matrix)
                for name, values in (('position', components.translation.values), ('rotation', components.rotation.values),
                                     ('scale', components.scale.values)):
                    if [round(v, 5) for v in values] != [round(v, 5) for v in target[name]]:
                        self._write_transform(obj, state, name, list(values))
            using_gizmo = G.is_using() or G.is_over()
        if hovered and not using_gizmo:
            if not io.want_text_input:
                for key_code, op in ((native.Key.w, 0), (native.Key.e, 1), (native.Key.r, 2)):
                    if native.is_key_pressed(key_code):
                        self.operation = op
            dx, dy = io.mouse_delta.x, io.mouse_delta.y
            if native.is_mouse_dragging(1) or native.is_mouse_dragging(2) or io.mouse_wheel:
                pan = native.is_mouse_dragging(2)
                zoom = io.mouse_wheel
                if self.pilot == 0:
                    orbit = self._view(stage)
                    if pan:
                        view = render3d.look_at(orbit.camera()['position'], orbit.target)
                        orbit.target = orbit.target + (-view[0, :3] * dx + view[1, :3] * dy) * orbit.distance * 0.0015
                    elif native.is_mouse_dragging(1):
                        orbit.yaw -= dx * 0.3
                        orbit.pitch = max(-85.0, min(85.0, orbit.pitch + dy * 0.3))
                    if zoom:
                        orbit.distance = max(0.3, orbit.distance * (0.9 ** zoom))
                else:
                    key_name = 'camera' if self.pilot == 1 else 'cameraEnd'
                    if native.is_mouse_dragging(1) or pan or zoom:
                        state[key_name] = orbit_camera(state[key_name], dx if (native.is_mouse_dragging(1) or pan) else 0,
                                                       dy if (native.is_mouse_dragging(1) or pan) else 0, pan, zoom)
            if native.is_mouse_clicked(0) and self.texture is not None and getattr(self, 'ids', None):
                index, object_ids = self.ids
                x = int(io.mouse_pos.x - origin.x)
                y = int(io.mouse_pos.y - origin.y)
                if 0 <= y < index.shape[0] and 0 <= x < index.shape[1]:
                    hit = index[y, x]
                    self.selected_object = object_ids[hit] if 0 <= hit < len(object_ids) else None
                    if self.selected_object:
                        picked = next(o for o in stage['objects'] if o['id'] == self.selected_object)
                        self.panel_only = picked['role'] in ('character', 'object')

    # ------------------------------------------------------------------ 2D
    def draw_2d(self, panel, state):
        drawing = state['drawing']
        avail = native.get_content_region_avail()
        native.begin_child('draw-side', native.ImVec2(250, avail.y), native.ChildFlags_.borders)
        for position, label in enumerate(TOOL_LABELS):
            if native.radio_button(tr(label) + f'##tool{position}', self.tool == position):
                self.tool = position
        _, self.draw_colour = native.color_edit3(tr('Colour') + '##drawcolour', self.draw_colour, native.ColorEditFlags_.no_inputs)
        native.set_next_item_width(120)
        _, self.draw_width = imgui.slider_float('Width', self.draw_width, 1.0, 20.0, '%.0f')
        _, self.draw_fill = imgui.checkbox('Filled', self.draw_fill)
        value = colour(drawing.get('background', '#e9e6df'))
        changed, picked = native.color_edit3(tr('Background') + '##bg', [value.x, value.y, value.z], native.ColorEditFlags_.no_inputs)
        if changed:
            drawing['background'] = hex_colour(picked)
        if self.selected_item is not None and self.selected_item < len(drawing['items']):
            item = drawing['items'][self.selected_item]
            native.separator_text(tr('Selected element'))
            if item['type'] == 'text':
                _, item['text'] = imgui.input_text('Text##text', item['text'])
            if item['type'] in ('text', 'figure'):
                native.set_next_item_width(120)
                _, item['size'] = imgui.slider_float('Size', item['size'], 0.02, 0.3, '%.2f')
            itemc = colour(item['color'])
            changed, picked = native.color_edit3('##itemcolour', [itemc.x, itemc.y, itemc.z], native.ColorEditFlags_.no_inputs)
            if changed:
                item['color'] = hex_colour(picked)
            if imgui.small_button('Delete##item') or (native.is_key_pressed(native.Key.delete) and not native.get_io().want_text_input):
                drawing['items'].pop(self.selected_item)
                self.selected_item = None
        if imgui.small_button('Clear the drawing'):
            drawing['items'] = []
            self.selected_item = None
        native.text_disabled(tr('Figures stand on the point you click; arrows show movement.'))
        native.end_child()
        native.same_line()
        native.begin_child('draw-canvas', native.ImVec2(0, avail.y), native.ChildFlags_.borders)
        size = layout.render_size(self.board)
        area = native.get_content_region_avail()
        scale = min(area.x / size[0], (area.y - 4) / size[1])
        width, height = size[0] * scale, size[1] * scale
        origin = native.get_cursor_screen_pos()
        native.invisible_button('canvas', native.ImVec2(max(width, 1), max(height, 1)), native.ButtonFlags_.mouse_button_left)
        draw = native.get_window_draw_list()
        draw.add_rect_filled(origin, native.ImVec2(origin.x + width, origin.y + height),
                             native.get_color_u32(colour(drawing.get('background', '#e9e6df'))))
        to_screen = lambda p: native.ImVec2(origin.x + p[0] * width, origin.y + p[1] * height)  # noqa: E731
        mouse = native.get_io().mouse_pos
        point = [min(1, max(0, (mouse.x - origin.x) / width)), min(1, max(0, (mouse.y - origin.y) / height))]
        for index, item in enumerate(drawing['items']):
            self._draw_item(draw, item, to_screen, width, height, index == self.selected_item)
        if self.stroke:
            self._draw_item(draw, self.stroke, to_screen, width, height, False)
        tool = TOOLS[self.tool]
        if native.is_item_activated():
            if tool == 'select':
                self.selected_item = self._hit(drawing['items'], point)
                self.drag_origin = point
            elif tool in ('figure', 'text'):
                drawing['items'].append({'type': tool, 'points': [point], 'color': hex_colour(self.draw_colour),
                                         'width': self.draw_width, 'fill': False,
                                         'text': 'Text' if tool == 'text' else '', 'size': 0.06 if tool == 'text' else 0.08})
                self.selected_item = len(drawing['items']) - 1
            else:
                self.stroke = {'type': tool, 'points': [point, point], 'color': hex_colour(self.draw_colour),
                               'width': self.draw_width, 'fill': self.draw_fill, 'text': '', 'size': 0.05}
        if native.is_item_active():
            if self.stroke:
                if tool == 'stroke':
                    if math.dist(self.stroke['points'][-1], point) > 0.004:
                        self.stroke['points'].append(point)
                else:
                    self.stroke['points'][-1] = point
            elif tool == 'select' and self.selected_item is not None and self.drag_origin:
                dx, dy = point[0] - self.drag_origin[0], point[1] - self.drag_origin[1]
                item = drawing['items'][self.selected_item]
                item['points'] = [[x + dx, y + dy] for x, y in item['points']]
                self.drag_origin = point
        if native.is_item_deactivated() and self.stroke:
            if len(self.stroke['points']) >= 2 and math.dist(self.stroke['points'][0], self.stroke['points'][-1]) > 0.005:
                drawing['items'].append(layout._drawing({'items': [self.stroke]})['items'][0])
                self.selected_item = len(drawing['items']) - 1
            self.stroke = None
        native.end_child()

    @staticmethod
    def _hit(items, point):
        for index in range(len(items) - 1, -1, -1):
            xs = [p[0] for p in items[index]['points']]
            ys = [p[1] for p in items[index]['points']]
            margin = 0.02 + (items[index]['size'] * 4 if items[index]['type'] == 'figure' else 0)
            if min(xs) - margin <= point[0] <= max(xs) + margin and min(ys) - margin - (
                    items[index]['size'] * 4 if items[index]['type'] == 'figure' else 0) <= point[1] <= max(ys) + margin:
                return index
        return None

    @staticmethod
    def _draw_item(draw, item, to_screen, width, height, selected):
        col = native.get_color_u32(colour(item['color']))
        thickness = max(1.0, item['width'] * width / 640)
        points = [to_screen(p) for p in item['points']]
        kind = item['type']
        if kind in ('rect', 'ellipse') and len(points) >= 2:
            a, b = points[0], points[-1]
            p0, p1 = native.ImVec2(min(a.x, b.x), min(a.y, b.y)), native.ImVec2(max(a.x, b.x), max(a.y, b.y))
            if kind == 'rect':
                if item['fill']:
                    draw.add_rect_filled(p0, p1, col)
                else:
                    draw.add_rect(p0, p1, col, thickness=thickness)
            else:
                centre = native.ImVec2((p0.x + p1.x) / 2, (p0.y + p1.y) / 2)
                radius = native.ImVec2(max(1, (p1.x - p0.x) / 2), max(1, (p1.y - p0.y) / 2))
                if item['fill']:
                    draw.add_ellipse_filled(centre, radius, col)
                else:
                    draw.add_ellipse(centre, radius, col, thickness=thickness)
        elif kind in ('line', 'stroke') and len(points) >= 2:
            draw.add_polyline(points, col, 0, thickness)
        elif kind == 'arrow' and len(points) >= 2:
            a, b = points[0], points[-1]
            draw.add_line(a, b, col, thickness)
            angle = math.atan2(b.y - a.y, b.x - a.x)
            head = 14 * width / 640
            for side in (-0.45, 0.45):
                draw.add_line(b, native.ImVec2(b.x - head * math.cos(angle + side), b.y - head * math.sin(angle + side)),
                              col, thickness)
        elif kind == 'text' and points:
            draw.add_text(native.get_font(), max(10.0, item['size'] * height), points[0], col, item['text'])
        elif kind == 'figure' and points:
            x, y = points[0].x, points[0].y
            h = item['size'] * height * 4
            head = h * 0.12
            draw.add_circle(native.ImVec2(x, y - h + head), head, col, 0, thickness)
            draw.add_line(native.ImVec2(x, y - h + 2 * head), native.ImVec2(x, y - h * 0.45), col, thickness)
            draw.add_line(native.ImVec2(x - h * 0.22, y - h * 0.7), native.ImVec2(x + h * 0.22, y - h * 0.7), col, thickness)
            draw.add_line(native.ImVec2(x, y - h * 0.45), native.ImVec2(x - h * 0.15, y), col, thickness)
            draw.add_line(native.ImVec2(x, y - h * 0.45), native.ImVec2(x + h * 0.15, y), col, thickness)
        if selected and points:
            xs, ys = [p.x for p in points], [p.y for p in points]
            wide = item['size'] * height if kind == 'figure' else 0
            draw.add_rect(native.ImVec2(min(xs) - 6 - wide, min(ys) - 6 - wide * 4),
                          native.ImVec2(max(xs) + 6 + wide, max(ys) + 6), native.get_color_u32(native.ImVec4(1, .6, .1, 1)),
                          thickness=1.0)

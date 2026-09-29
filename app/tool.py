import sys
from installation_ui import configure as configure_storage
configure_storage()
import os
from pathlib import Path

from cytools_core import CyToolError, Runtime, load_manifest
from cytools_core.transports.cli import run_cli

APP = Path(__file__).resolve().parent
ROOT = APP.parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from storyboard import export, h3film, h3workflow, layout, model  # noqa: E402

PROJECTS = Path(os.environ.get('CYTOOLS_STORYBOARD_PROJECTS') or ROOT / 'data' / 'projects')


def _open(parameters):
    value = parameters['project']
    path = Path(value)
    if not path.is_absolute() and not path.exists():
        candidate = PROJECTS / value
        path = candidate if candidate.exists() else PROJECTS / (value + model.SUFFIX)
    try:
        return model.Storyboard.load(path)
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None


def _describe(board):
    return {'project': str(board.folder), 'document': board.doc, 'timeline': board.timeline(),
            'totalDuration': board.total_duration(), 'issues': board.validate()}


def _edit(parameters, change):
    """Load, change, save: every mutating operation goes through here."""
    board = _open(parameters)
    try:
        change(board)
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    board.save()
    return _describe(board)


def _fields(parameters, names):
    return {k: parameters[k] for k in names if k in parameters}


PANEL_KEYS = ('title', 'duration', 'status', 'color', 'images', 'prompt', 'references', 'transition', 'notes')


def create_storyboard(context, p):
    try:
        board = model.Storyboard.create(p.get('folder') or PROJECTS, p['title'], aspect=p.get('aspect', '16:9'),
                                        fps=p.get('fps', 24), default_duration=p.get('default_duration', 5))
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    return _describe(board)


def list_storyboards(context, p):
    folder = Path(p.get('folder') or PROJECTS)
    projects = []
    for path in sorted(folder.glob('*' + model.SUFFIX)):
        try:
            board = model.Storyboard.load(path)
            projects.append({'project': str(path), 'title': board.doc['title'], 'panels': len(board.panels()),
                             'duration': board.total_duration(), 'updatedAt': board.doc.get('updatedAt')})
        except model.StoryboardError as exc:
            projects.append({'project': str(path), 'error': str(exc)})
    return {'projects': projects}


def describe_storyboard(context, p):
    return _describe(_open(p))


def update_storyboard(context, p):
    def change(board):
        for key in ('title', 'description'):
            if key in p:
                board.doc[key] = p[key]
        board.doc['settings'].update(p.get('settings') or {})
    return _edit(p, change)


def add_panel(context, p):
    return _edit(p, lambda b: b.add_panel(p.get('sequence', ''), p.get('after', ''), **_fields(p, PANEL_KEYS)))


def update_panel(context, p):
    return _edit(p, lambda b: b.update_panel(p['panel'], **_fields(p, PANEL_KEYS)))


def duplicate_panel(context, p):
    return _edit(p, lambda b: b.duplicate_panel(p['panel']))


def move_panel(context, p):
    return _edit(p, lambda b: b.move_panel(p['panel'], p.get('sequence', ''), p.get('index')))


def remove_panel(context, p):
    return _edit(p, lambda b: b.remove_panel(p['panel']))


def add_sequence(context, p):
    return _edit(p, lambda b: b.add_sequence(p.get('title', ''), p.get('after', '')))


def update_sequence(context, p):
    def change(board):
        sequence = board.sequence(p['sequence'])
        sequence.update(_fields(p, ('title', 'color', 'notes')))
    return _edit(p, change)


def remove_sequence(context, p):
    return _edit(p, lambda b: b.remove_sequence(p['sequence']))


def add_library_item(context, p):
    return _edit(p, lambda b: b.add_library_item(p['kind'], p['name'], p.get('description', ''),
                                                 p.get('files') or [], p.get('tags') or []))


def update_library_item(context, p):
    return _edit(p, lambda b: b.update_library_item(p['item'], **_fields(p, ('kind', 'name', 'description', 'files', 'tags'))))


def remove_library_item(context, p):
    return _edit(p, lambda b: b.remove_library_item(p['item']))


def validate_storyboard(context, p):
    return _describe(_open(p))


def _exports(board, name):
    target = board.folder / 'exports' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    return target


def export_contact_sheet(context, p):
    board = _open(p)
    try:
        path = export.contact_sheet(board, _exports(board, 'contact_sheet.png'), p.get('columns', 4), p.get('cell_width', 480))
    except export.ExportError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    return {'file': str(path)}


def export_summary(context, p):
    board = _open(p)
    kind = p.get('format', 'html')
    return {'file': str(export.summary(board, _exports(board, 'storyboard.' + kind), kind))}


def export_animatic(context, p):
    board = _open(p)
    try:
        path = export.animatic(board, _exports(board, 'animatic.mp4'), p.get('captions', True), p.get('fps', 24),
                               cancelled=context.cancellation.event.is_set,
                               progress=lambda f, text: context.progress(round(100 * f, 1), currentStep=text),
                               motion=p.get('motion', True), motion_fps=p.get('motion_fps', 12))
    except export.ExportError as exc:
        context.cancellation.check()
        raise CyToolError('ExportFailed', str(exc)) from None
    return {'file': str(path), 'duration': board.total_duration()}


OBJECT_KEYS = ('name', 'color', 'position', 'rotation', 'scale', 'role', 'reference', 'pose')


def add_stage(context, p):
    return _edit(p, lambda b: layout.add_stage(b, p.get('name', '')))


def update_stage(context, p):
    return _edit(p, lambda b: layout.update_stage(b, p['stage'], **_fields(p, ('name', 'sky', 'ground', 'groundColour'))))


def remove_stage(context, p):
    return _edit(p, lambda b: layout.remove_stage(b, p['stage']))


def add_object(context, p):
    def change(board):
        fields = _fields(p, OBJECT_KEYS)
        reference = fields.pop('reference', '')
        chosen_pose = fields.pop('pose', '')
        obj = layout.add_object(board, p['stage'], p.get('shape', 'box'), mesh=p.get('mesh', ''), **fields)
        if reference:
            layout.update_object(board, obj['id'], reference=reference)
        if chosen_pose:
            layout.update_object(board, obj['id'], pose=chosen_pose)
    return _edit(p, change)


def update_object(context, p):
    return _edit(p, lambda b: layout.update_object(b, p['object'], **_fields(p, OBJECT_KEYS)))


def duplicate_object(context, p):
    return _edit(p, lambda b: layout.duplicate_object(b, p['object']))


def remove_object(context, p):
    return _edit(p, lambda b: layout.remove_object(b, p['object']))


def add_pose(context, p):
    return _edit(p, lambda b: layout.add_pose(b, p.get('name', ''), p.get('base', 'standing'), p.get('angles'),
                                              p.get('walks', True)))


def update_pose(context, p):
    return _edit(p, lambda b: layout.update_pose(b, p['pose'], p.get('name'), p.get('angles'), p.get('walks')))


def remove_pose(context, p):
    return _edit(p, lambda b: layout.remove_pose(b, p['pose']))


def set_panel_layout(context, p):
    return _edit(p, lambda b: layout.set_layout(b, p['panel'], **_fields(p, ('mode', 'stage', 'camera', 'cameraEnd',
                                                                           'drawing'))))


def override_object(context, p):
    def change(board):
        if p.get('clear'):
            layout.clear_override(board, p['panel'], p['object'])
        else:
            layout.override_object(board, p['panel'], p['object'], **_fields(
                p, ('position', 'rotation', 'scale', 'hidden', 'positionEnd', 'rotationEnd', 'pose', 'poseEnd')))
    return _edit(p, change)


def render_panel_layout(context, p):
    board = _open(p)
    try:
        result = layout.render_panel(board, p['panel'], 'end' if p.get('camera') == 'end' else 'camera')
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    board.save()
    return {'project': str(board.folder), 'render': str(board.folder / result['render']),
            'depth': str(board.folder / result['depth']) if result.get('depth') else ''}


def suggest_camera_move(context, p):
    board = _open(p)
    try:
        _, _, panel = board.find(p['panel'])
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    suggestion = layout.suggest_camera(panel)
    if p.get('apply'):
        panel['prompt'].update(suggestion)
        board.save()
    return suggestion


def export_h3_film(context, p):
    board = _open(p)
    options = p.get('options') or {}
    try:
        target = Path(p['folder']) if p.get('folder') else h3film.default_folder(board)
        context.progress(10, currentStep='planning segments')
        result = h3film.export_film(board, target, options, workflows=p.get('workflows', True))
        if p.get('save_options', True):
            board.doc['settings']['h3film'] = h3film.options_for(board, options)
            board.save()
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    context.progress(100, currentStep='done')
    return dict(result, file=result['folder'])


def preview_h3_film(context, p):
    board = _open(p)
    try:
        film, _, warnings = h3film.build(board, p.get('options') or {}, preview=True)
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    return {'segments': film['segments'], 'frames': film['frames'], 'seconds': film['seconds'],
            'width': film['width'], 'height': film['height'], 'globalPrompt': film['timeline']['globalPrompt'],
            'warnings': warnings, 'options': film['source']['options']}


def export_h3_workflow(context, p):
    board = _open(p)
    options = p.get('options') or {}
    try:
        target = Path(p['folder']) if p.get('folder') else h3workflow.default_folder(board)
        context.progress(10, currentStep='converting panels')
        result = h3workflow.export_workflow(board, target, options)
        if p.get('save_options', True):
            board.doc['settings']['h3workflow'] = h3workflow.options_for(board, options)
            board.save()
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    context.progress(100, currentStep='done')
    return result


def preview_h3_workflow(context, p):
    board = _open(p)
    try:
        document, _, summary, warnings = h3workflow.build(board, p.get('options') or {}, preview=True)
    except model.StoryboardError as exc:
        raise CyToolError('InvalidParameters', str(exc)) from None
    return dict(summary, warnings=warnings, workflow=document)


HANDLERS = {name: globals()[name] for name in (
    'create_storyboard', 'list_storyboards', 'describe_storyboard', 'update_storyboard', 'add_panel', 'update_panel',
    'duplicate_panel', 'move_panel', 'remove_panel', 'add_sequence', 'update_sequence', 'remove_sequence',
    'add_library_item', 'update_library_item', 'remove_library_item', 'validate_storyboard', 'export_contact_sheet',
    'export_summary', 'export_animatic', 'add_stage', 'update_stage', 'remove_stage', 'add_object', 'update_object',
    'duplicate_object', 'remove_object', 'add_pose', 'update_pose', 'remove_pose', 'set_panel_layout', 'override_object', 'render_panel_layout',
    'suggest_camera_move', 'export_h3_film', 'preview_h3_film', 'export_h3_workflow', 'preview_h3_workflow')}


def create_runtime(data_dir, **options):
    runtime = Runtime(load_manifest(APP / 'CyTool.json'), data_dir, **options)
    runtime.configure_inputs(ROOT / 'data/inputs', fields={})
    for name, handler in HANDLERS.items():
        runtime.register(name, handler)
    from cytools_core.shared_installation import register_operations
    register_operations(runtime, ROOT)
    return runtime


if __name__ == '__main__':
    argv = sys.argv[1:]
    if '--data-dir' not in argv:
        argv = ['--data-dir', str(ROOT / 'data/jobs'), *argv]
    raise SystemExit(run_cli(create_runtime, argv))

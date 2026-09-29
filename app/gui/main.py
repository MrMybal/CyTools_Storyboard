"""CyTools_Storyboard desktop application (Dear ImGui).

The window edits the storyboard in memory and writes it to disk a second after every
change (and before any export), so the operations - which read the project from disk -
always see what the window shows. Changes made to the project by another client (CLI,
MCP) are picked up when the window has nothing unsaved. Undo/redo keeps whole snapshots.
"""
import copy
import json
import sys
import threading
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from imgui_bundle import hello_imgui, imgui as native  # noqa: E402

from ui_common import configure_generation, imgui, run, tr  # noqa: E402
from gui.common import IMAGE_FILTER, MEDIA_FILTER, colour, dialogs, hex_colour, image, open_local  # noqa: E402
from storyboard import export, model  # noqa: E402
from tool import PROJECTS, create_runtime  # noqa: E402

RECENT = ROOT / 'data' / 'settings' / 'recent.json'
STATUS_COLOURS = {'idea': (0.55, 0.55, 0.6, 1), 'draft': (0.95, 0.7, 0.25, 1), 'ready': (0.35, 0.8, 0.45, 1),
                  'generated': (0.35, 0.6, 0.95, 1)}
KIND_LABELS = {'character': 'Characters', 'location': 'Locations', 'object': 'Objects', 'style': 'Styles',
               'image': 'Images', 'audio': 'Audio', 'video': 'Video'}


def recent():
    try:
        return [p for p in json.loads(RECENT.read_text(encoding='utf-8')) if Path(p).is_dir()][:12]
    except (OSError, ValueError):
        return []


def remember(folder):
    items = [str(folder)] + [p for p in recent() if p != str(folder)]
    RECENT.parent.mkdir(parents=True, exist_ok=True)
    RECENT.write_text(json.dumps(items[:12], indent=1), encoding='utf-8')


class Editor:
    def __init__(self, runtime):
        self.runtime = runtime
        self.actor = runtime.authenticate(runtime.create_client('ImGui')['token'])
        self.session = runtime.create_session(self.actor, temporary=False)['sessionId']
        self.board = None
        self.selected = None
        self.selected_item = None
        self.undo, self.redo = [], []
        self.last_state = ''
        self.last_change = 0.0
        self.dirty = False
        self.saved_mtime = 0
        self.message = ''
        self.new_title = ''
        self.zoom = 200.0
        self.px_per_second = 40.0
        self.kind_filter = 0
        self.job = None
        self.play = None
        self.drop_ids = {}
        self.issues = []
        self._issues_at = 0.0
        self.frames = 0
        self.new_item = {'kind': 0, 'name': ''}
        self.select_tab = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--ui-test-tab=')), '')
        from gui.layout_editor import LayoutEditor
        from gui.film_export import FilmExportWindow
        self.layout = LayoutEditor(self)
        self.film = FilmExportWindow(self)
        from gui.workflow_export import WorkflowExportWindow
        self.workflow = WorkflowExportWindow(self)
        test = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--ui-test-project=')), '')
        if test:
            self.open(test)
        elif recent():
            try:
                self.open(recent()[0])
            except model.StoryboardError:
                pass

    # ------------------------------------------------------------------ document state
    def open(self, path):
        self.board = model.Storyboard.load(path)
        self.selected = self.board.panels()[0]['id'] if self.board.panels() else None
        self.undo, self.redo = [], []
        self.last_state = json.dumps(self.board.doc, sort_keys=True)
        self.saved_mtime = (self.board.folder / 'storyboard.json').stat().st_mtime_ns
        self.dirty = False
        remember(self.board.folder)

    def track(self):
        """Called once per frame: record undo steps, autosave, reload external edits."""
        if not self.board:
            return
        state = json.dumps(self.board.doc, sort_keys=True)
        now = time.monotonic()
        if state != self.last_state:
            # Typing in a field produces a change per frame: group changes closer than 1 s.
            if not self.undo or now - self.last_change > 1.0:
                self.undo.append(self.last_state)
                self.undo = self.undo[-200:]
            self.redo.clear()
            self.last_state = state
            self.last_change = now
            self.dirty = True
        if self.dirty and now - self.last_change > 1.0:
            self.save()
        if not self.dirty and self.frames % 60 == 0:
            try:
                mtime = (self.board.folder / 'storyboard.json').stat().st_mtime_ns
            except OSError:
                return
            if mtime != self.saved_mtime:
                selected = self.selected
                self.open(self.board.folder)
                self.selected = selected
                self.message = tr('The project was changed outside the window and has been reloaded.')

    def save(self):
        if self.board:
            self.board.save()
            self.saved_mtime = (self.board.folder / 'storyboard.json').stat().st_mtime_ns
            self.dirty = False

    def undo_step(self):
        if self.undo:
            self.redo.append(self.last_state)
            self.last_state = self.undo.pop()
            self.board.restore(json.loads(self.last_state))
            self.dirty, self.last_change = True, time.monotonic()

    def redo_step(self):
        if self.redo:
            self.undo.append(self.last_state)
            self.last_state = self.redo.pop()
            self.board.restore(json.loads(self.last_state))
            self.dirty, self.last_change = True, time.monotonic()

    def act(self, function, *args, **kwargs):
        try:
            return function(*args, **kwargs)
        except model.StoryboardError as exc:
            self.message = str(exc)

    def submit(self, operation, parameters):
        self.save()
        try:
            self.job = self.runtime.submit(self.actor, self.session, operation, parameters)
        except Exception as exc:
            self.message = getattr(exc, 'message', str(exc))

    # ------------------------------------------------------------------ toolbar
    def toolbar(self):
        if imgui.button('New'):
            native.open_popup('new-storyboard')
        if native.begin_popup('new-storyboard'):
            native.set_next_item_width(260)
            _, self.new_title = imgui.input_text('Title', self.new_title)
            if imgui.button('Create') and self.new_title.strip():
                try:
                    board = model.Storyboard.create(PROJECTS, self.new_title.strip())
                    self.open(board.folder)
                    self.new_title = ''
                    native.close_current_popup()
                except model.StoryboardError as exc:
                    self.message = str(exc)
            native.end_popup()
        native.same_line()
        if imgui.button('Open...'):
            dialogs.open('open', 'Open a storyboard', ['Storyboard', 'storyboard.json'], PROJECTS)
        chosen = dialogs.result('open')
        if chosen:
            try:
                self.save()
                self.open(chosen[0])
            except model.StoryboardError as exc:
                self.message = str(exc)
        native.same_line()
        if imgui.button('Recent'):
            native.open_popup('recent-list')
        if native.begin_popup('recent-list'):
            for path in recent():
                if native.selectable(Path(path).name, False)[0]:
                    self.save()
                    self.open(path)
            if not recent():
                native.text_disabled(tr('Nothing yet.'))
            native.end_popup()
        if not self.board:
            return
        native.same_line()
        native.begin_disabled(not self.undo)
        if imgui.button('Undo') or (native.get_io().key_ctrl and native.is_key_pressed(native.Key.z) and not native.get_io().want_text_input):
            self.undo_step()
        native.end_disabled()
        native.same_line()
        native.begin_disabled(not self.redo)
        if imgui.button('Redo') or (native.get_io().key_ctrl and native.is_key_pressed(native.Key.y) and not native.get_io().want_text_input):
            self.redo_step()
        native.end_disabled()
        native.same_line()
        if imgui.button('Add panel'):
            after = self.selected if self.selected else ''
            panel = self.act(self.board.add_panel, '', after)
            if panel:
                self.selected = panel['id']
        native.same_line()
        if imgui.button('Add sequence'):
            self.act(self.board.add_sequence)
        native.same_line()
        if imgui.button('Play animatic'):
            self.play = {'start': time.monotonic(), 'paused': 0.0}
        native.same_line()
        if imgui.button('Export'):
            native.open_popup('export-menu')
        if native.begin_popup('export-menu'):
            if native.selectable(tr('Contact sheet (PNG)'), False)[0]:
                self.submit('export_contact_sheet', {'project': str(self.board.folder)})
            if native.selectable(tr('Script (HTML)'), False)[0]:
                self.submit('export_summary', {'project': str(self.board.folder), 'format': 'html'})
            if native.selectable(tr('Script (Markdown)'), False)[0]:
                self.submit('export_summary', {'project': str(self.board.folder), 'format': 'md'})
            if native.selectable(tr('Animatic (MP4)'), False)[0]:
                self.submit('export_animatic', {'project': str(self.board.folder)})
            native.separator()
            if native.selectable(tr('MiniMax H3 film (ComfyUI / Colab)...'), False)[0]:
                self.film.show()
            if native.selectable(tr('MiniMax H3 workflow (one generation per panel)...'), False)[0]:
                self.workflow.show()
            native.end_popup()
        native.same_line()
        if imgui.button('Project folder'):
            open_local(self.board.folder)
        native.same_line()
        native.set_next_item_width(140)
        _, self.zoom = imgui.slider_float('Card size', self.zoom, 120.0, 360.0, '%.0f')
        total = self.board.total_duration()
        native.same_line()
        native.text(f'{self.board.doc["title"]}  -  {len(self.board.panels())} {tr("panels")}  -  '
                    f'{int(total // 60)}:{total % 60:04.1f}' + ('  *' if self.dirty else ''))
        if self.job:
            job = self.runtime.get_job(self.actor, self.job['jobId'])
            self.job = job
            if job['state'] == 'Completed':
                file = job['outputs'].get('file')
                native.text(tr('Exported: ') + str(file))
                native.same_line()
                if imgui.small_button('Open'):
                    open_local(file)
                native.same_line()
                if imgui.small_button('Dismiss'):
                    self.job = None
            elif job['state'] == 'Failed':
                native.text_colored(native.ImVec4(1, .4, .35, 1), job['error']['message'])
            else:
                progress = job.get('progress') or {}
                native.progress_bar((progress.get('percent') or 0) / 100, native.ImVec2(300, 0),
                                    progress.get('currentStep') or tr(job['state']))
        if self.message:
            native.text_colored(native.ImVec4(1, .7, .35, 1), self.message)
            native.same_line()
            if imgui.small_button('OK##msg'):
                self.message = ''

    # ------------------------------------------------------------------ library
    def library(self):
        board = self.board
        native.text(tr('References'))
        kinds = ['all', *model.KINDS]
        native.set_next_item_width(-1)
        _, self.kind_filter = imgui.combo('##kind', self.kind_filter, ['All'] + [KIND_LABELS[k] for k in model.KINDS])
        native.set_next_item_width(110)
        _, self.new_item['kind'] = imgui.combo('##newkind', self.new_item['kind'], list(model.KINDS))
        native.same_line()
        native.set_next_item_width(-60)
        _, self.new_item['name'] = imgui.input_text('##newname', self.new_item['name'])
        native.same_line()
        if imgui.small_button('Add##lib') and self.new_item['name'].strip():
            item = self.act(board.add_library_item, model.KINDS[self.new_item['kind']], self.new_item['name'].strip())
            if item:
                self.selected_item, self.new_item['name'] = item['id'], ''
        native.separator()
        for item in board.doc['library']:
            if self.kind_filter and item['kind'] != kinds[self.kind_filter]:
                continue
            imgui.push_id('lib' + item['id'])
            first = board.folder / item['files'][0] if item.get('files') else None
            if first and first.suffix.lower() in model.IMAGE_SUFFIXES:
                image(first, 48, 48, 128)
                native.same_line()
            opened = native.selectable(f"{item['name']}\n{tr(item['kind'])}", self.selected_item == item['id'],
                                       0, native.ImVec2(0, 44))[0]
            if opened:
                self.selected_item = item['id'] if self.selected_item != item['id'] else None
            if native.begin_drag_drop_source():
                self.drop_ids[hash(item['id']) & 0x7fffffff] = item['id']
                native.set_drag_drop_payload_py_id('LIBRARY', hash(item['id']) & 0x7fffffff)
                native.text(item['name'])
                native.end_drag_drop_source()
            if self.selected_item == item['id']:
                self.library_item(item)
            imgui.pop_id()

    def library_item(self, item):
        board = self.board
        native.indent()
        native.set_next_item_width(-1)
        _, item['name'] = imgui.input_text('##name', item['name'])
        index = model.KINDS.index(item['kind'])
        native.set_next_item_width(-1)
        changed, index = imgui.combo('##itemkind', index, list(model.KINDS))
        if changed:
            item['kind'] = model.KINDS[index]
        _, item['description'] = imgui.input_text_multiline('##desc', item.get('description', ''), native.ImVec2(-1, 60))
        tags = ', '.join(item.get('tags') or [])
        native.set_next_item_width(-1)
        changed, tags = imgui.input_text('Tags##tags', tags)
        if changed:
            item['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
        for position, file in enumerate(list(item.get('files') or [])):
            path = board.folder / file
            if path.suffix.lower() in model.IMAGE_SUFFIXES:
                image(path, 150, 90, 256)
            else:
                native.text(board.doc.get('assetNames', {}).get(Path(file).name, Path(file).name))
            native.same_line()
            if imgui.small_button(f'Remove##file{position}'):
                item['files'].pop(position)
        if imgui.small_button('Add files...'):
            dialogs.open('libfiles' + item['id'], 'Reference files', MEDIA_FILTER, multiple=True)
        chosen = dialogs.result('libfiles' + item['id'])
        for path in chosen or []:
            relative = self.act(board.import_asset, path)
            if relative:
                item.setdefault('files', []).append(relative)
        native.same_line()
        if imgui.small_button('Paste image'):
            self.paste_into(lambda relative: item.setdefault('files', []).append(relative))
        native.same_line()
        if imgui.small_button('Delete reference'):
            self.act(board.remove_library_item, item['id'])
            self.selected_item = None
        native.unindent()

    def paste_into(self, add):
        try:
            from PIL import ImageGrab
            data = ImageGrab.grabclipboard()
        except Exception as exc:
            self.message = str(exc)
            return
        if isinstance(data, list):
            for path in data:
                relative = self.act(self.board.import_asset, path)
                if relative:
                    add(relative)
        elif data is not None:
            add(self.board.import_image_data(data))
        else:
            self.message = tr('The clipboard holds no image.')

    # ------------------------------------------------------------------ board
    def card(self, panel, number):
        board = self.board
        width = self.zoom
        height = width * 9 / 16 + 58
        selected = panel['id'] == self.selected
        native.begin_group()
        start = native.get_cursor_screen_pos()
        draw = native.get_window_draw_list()
        border = native.get_color_u32(native.ImVec4(1, 0.8, 0.3, 1) if selected else native.ImVec4(0.3, 0.3, 0.35, 1))
        native.invisible_button('card', native.ImVec2(width, height))
        clicked = native.is_item_clicked()
        if native.begin_drag_drop_source():
            key = hash(panel['id']) & 0x7fffffff
            self.drop_ids[key] = panel['id']
            native.set_drag_drop_payload_py_id('PANEL', key)
            native.text(f'{number}. {panel["title"]}')
            native.end_drag_drop_source()
        if native.begin_drag_drop_target():
            payload = native.accept_drag_drop_payload_py_id('PANEL')
            if payload is not None:
                moved = self.drop_ids.get(payload.data_id)
                if moved and moved != panel['id']:
                    sequence, index, _ = board.find(panel['id'])
                    self.act(board.move_panel, moved, sequence['id'], index)
            payload = native.accept_drag_drop_payload_py_id('LIBRARY')
            if payload is not None:
                item = self.drop_ids.get(payload.data_id)
                if item and item not in panel['references']:
                    panel['references'].append(item)
            native.end_drag_drop_target()
        if native.begin_popup_context_item('cardmenu'):
            if native.menu_item(tr('Duplicate'), '', False)[0]:
                self.act(board.duplicate_panel, panel['id'])
            if native.menu_item(tr('Add a panel after'), '', False)[0]:
                new = self.act(board.add_panel, '', panel['id'])
                if new:
                    self.selected = new['id']
            if native.menu_item(tr('Delete'), '', False)[0]:
                self.act(board.remove_panel, panel['id'])
                if self.selected == panel['id']:
                    self.selected = None
            native.end_popup()
        end = native.ImVec2(start.x + width, start.y + height)
        draw.add_rect_filled(start, end, native.get_color_u32(native.ImVec4(0.12, 0.12, 0.14, 1)), 6)
        picture = export.main_image(board, panel)
        thumb_h = width * 9 / 16
        if picture:
            from gui.common import textures
            texture = textures.get(picture, 384)
            if texture:
                scale = min((width - 8) / texture.width, (thumb_h - 8) / texture.height)
                w, h = texture.width * scale, texture.height * scale
                x0 = start.x + (width - w) / 2
                y0 = start.y + 4 + (thumb_h - 8 - h) / 2
                draw.add_image(native.ImTextureRef(texture.texture_id()), native.ImVec2(x0, y0), native.ImVec2(x0 + w, y0 + h))
        else:
            draw.add_rect_filled(native.ImVec2(start.x + 4, start.y + 4), native.ImVec2(end.x - 4, start.y + thumb_h - 4),
                                 native.get_color_u32(colour(panel.get('color') or '#2d3a52')), 4)
            draw.add_text(native.ImVec2(start.x + 12, start.y + thumb_h / 2 - 8), native.get_color_u32(native.ImVec4(1, 1, 1, .8)),
                          tr('no image'))
        status = native.get_color_u32(native.ImVec4(*STATUS_COLOURS.get(panel['status'], (0.5, 0.5, 0.5, 1))))
        draw.add_circle_filled(native.ImVec2(end.x - 12, start.y + 12), 6, status)
        text = native.get_color_u32(native.ImVec4(1, 1, 1, 1))
        draw.add_text(native.ImVec2(start.x + 8, start.y + thumb_h + 4), text, f'{number}. {panel["title"][:40]}')
        detail = f'{panel["duration"]:.1f} s'
        if panel['references']:
            detail += f'   {len(panel["references"])} ref'
        if panel['prompt'].get('dialogue'):
            detail += '   ' + tr('dialogue')
        draw.add_text(native.ImVec2(start.x + 8, start.y + thumb_h + 24), native.get_color_u32(native.ImVec4(.75, .75, .8, 1)), detail)
        if panel.get('color'):
            draw.add_rect_filled(native.ImVec2(start.x, end.y - 4), end, native.get_color_u32(colour(panel['color'])), 2)
        draw.add_rect(start, end, border, rounding=6, thickness=3 if selected else 1)
        native.end_group()
        if clicked:
            self.selected = panel['id']

    def board_view(self):
        board = self.board
        number = 0
        available = native.get_content_region_avail().x
        per_row = max(1, int(available // (self.zoom + 12)))
        for sequence in list(board.sequences()):
            imgui.push_id('seq' + sequence['id'])
            native.set_next_item_width(260)
            _, sequence['title'] = imgui.input_text('##title', sequence['title'])
            if native.begin_drag_drop_target():
                payload = native.accept_drag_drop_payload_py_id('PANEL')
                if payload is not None and self.drop_ids.get(payload.data_id):
                    self.act(board.move_panel, self.drop_ids[payload.data_id], sequence['id'], None)
                native.end_drag_drop_target()
            native.same_line()
            duration = sum(p['duration'] for p in sequence['panels'])
            native.text_disabled(f'{len(sequence["panels"])} {tr("panels")}, {duration:.1f} s')
            native.same_line()
            if imgui.small_button('Add panel here'):
                panel = self.act(board.add_panel, sequence['id'])
                if panel:
                    self.selected = panel['id']
            native.same_line()
            if len(board.sequences()) > 1 and imgui.small_button('Delete sequence'):
                native.open_popup('confirm-seq')
            if native.begin_popup('confirm-seq'):
                native.text(tr('Delete this sequence and its panels?'))
                if imgui.button('Delete'):
                    self.act(board.remove_sequence, sequence['id'])
                    native.close_current_popup()
                native.same_line()
                if imgui.button('Keep'):
                    native.close_current_popup()
                native.end_popup()
            for index, panel in enumerate(sequence['panels']):
                number += 1
                if index % per_row:
                    native.same_line()
                imgui.push_id(panel['id'])
                self.card(panel, number)
                imgui.pop_id()
            if not sequence['panels']:
                native.text_disabled(tr('Empty: add a panel or drop one on the title.'))
            native.separator()
            imgui.pop_id()

    # ------------------------------------------------------------------ timeline
    def timeline(self):
        board = self.board
        rows = {row['id']: row for row in board.timeline()}
        total = board.total_duration()
        native.set_next_item_width(160)
        _, self.px_per_second = imgui.slider_float('Timeline zoom', self.px_per_second, 5.0, 200.0, '%.0f px/s')
        native.same_line()
        native.text_disabled(tr('Drag the right edge of a panel to change its duration.'))
        native.begin_child('timeline-strip', native.ImVec2(0, 0), native.ChildFlags_.none,
                           native.WindowFlags_.horizontal_scrollbar)
        origin = native.get_cursor_screen_pos()
        draw = native.get_window_draw_list()
        scale = self.px_per_second
        ruler = native.get_color_u32(native.ImVec4(.6, .6, .65, 1))
        step = 1 if scale > 30 else 5 if scale > 8 else 10
        for second in range(0, int(total) + 2, step):
            x = origin.x + second * scale
            draw.add_line(native.ImVec2(x, origin.y), native.ImVec2(x, origin.y + 8), ruler)
            draw.add_text(native.ImVec2(x + 2, origin.y), ruler, f'{second}s')
        top = origin.y + 18
        for number, panel in enumerate(board.panels(), start=1):
            row = rows[panel['id']]
            x0, x1 = origin.x + row['start'] * scale, origin.x + row['end'] * scale
            fill = colour(panel.get('color') or '#34507a')
            if panel['id'] == self.selected:
                fill = native.ImVec4(min(1, fill.x + .25), min(1, fill.y + .25), min(1, fill.z + .15), 1)
            draw.add_rect_filled(native.ImVec2(x0, top), native.ImVec2(x1 - 1, top + 46), native.get_color_u32(fill), 4)
            draw.add_text(native.ImVec2(x0 + 4, top + 4), native.get_color_u32(native.ImVec4(1, 1, 1, 1)),
                          f'{number}. {panel["title"]}'[:max(1, int((x1 - x0) / 7))])
            draw.add_text(native.ImVec2(x0 + 4, top + 24), native.get_color_u32(native.ImVec4(1, 1, 1, .7)),
                          f'{panel["duration"]:.1f}s')
            native.set_cursor_screen_pos(native.ImVec2(x0, top))
            native.invisible_button('tl' + panel['id'], native.ImVec2(max(4, x1 - x0 - 8), 46))
            if native.is_item_clicked():
                self.selected = panel['id']
            native.set_cursor_screen_pos(native.ImVec2(x1 - 8, top))
            native.invisible_button('edge' + panel['id'], native.ImVec2(8, 46))
            if native.is_item_hovered() or native.is_item_active():
                native.set_mouse_cursor(native.MouseCursor_.resize_ew)
            if native.is_item_active() and native.is_mouse_dragging(0):
                delta = native.get_io().mouse_delta.x / scale
                panel['duration'] = round(max(0.1, min(600.0, panel['duration'] + delta)), 2)
        if self.play:
            elapsed = self.play_time()
            x = origin.x + elapsed * scale
            draw.add_line(native.ImVec2(x, origin.y), native.ImVec2(x, top + 50),
                          native.get_color_u32(native.ImVec4(1, .3, .3, 1)), 2)
        native.set_cursor_screen_pos(native.ImVec2(origin.x, top + 52))
        native.dummy(native.ImVec2(max(total * scale + 40, 10), 1))
        native.end_child()

    # ------------------------------------------------------------------ inspector
    def inspector(self):
        board = self.board
        try:
            _, _, panel = board.find(self.selected) if self.selected else (None, None, None)
        except model.StoryboardError:
            panel, self.selected = None, None
        if panel is None:
            native.text_wrapped(tr('Select a panel to edit it.'))
            self.settings()
            return
        number = [p['id'] for p in board.panels()].index(panel['id']) + 1
        native.text(f'{tr("Panel")} {number}')
        native.set_next_item_width(-1)
        _, panel['title'] = imgui.input_text('##title', panel['title'])
        native.set_next_item_width(160)
        changed, duration = imgui.drag_float('Duration (s)', panel['duration'], 0.05, 0.1, 600.0, '%.2f')
        if changed:
            panel['duration'] = round(max(0.1, duration), 2)
        for preset in (4, 5, 8, 10, 15):
            native.same_line()
            if imgui.small_button(f'{preset}s'):
                panel['duration'] = float(preset)
        native.set_next_item_width(140)
        index = model.STATUSES.index(panel['status'])
        _, index = imgui.combo('Status', index, list(model.STATUSES))
        panel['status'] = model.STATUSES[index]
        native.same_line()
        value = colour(panel.get('color') or '#34507a')
        changed, picked = native.color_edit3('##colour', [value.x, value.y, value.z], native.ColorEditFlags_.no_inputs)
        if changed:
            panel['color'] = hex_colour(picked)
        native.same_line()
        if imgui.small_button('No colour'):
            panel['color'] = ''
        if native.collapsing_header(tr('Layout'), native.TreeNodeFlags_.default_open):
            self.layout.summary(panel)
        self.images(panel)
        self.prompt(panel)
        self.references(panel)
        if native.collapsing_header(tr('Transition and notes'), native.TreeNodeFlags_.default_open):
            transition = panel['transition']
            native.set_next_item_width(160)
            index = model.TRANSITIONS.index(transition['type'])
            _, index = imgui.combo('Transition to next', index, list(model.TRANSITIONS))
            transition['type'] = model.TRANSITIONS[index]
            if transition['type'] != 'cut':
                native.same_line()
                native.set_next_item_width(100)
                _, transition['duration'] = imgui.drag_float('s##trans', float(transition['duration']), 0.05, 0.0, 10.0, '%.2f')
            _, panel['notes'] = imgui.input_text_multiline('##notes', panel['notes'], native.ImVec2(-1, 70))
        own = [i for i in self.issues if i['panel'] == panel['id']]
        for issue in own:
            native.text_colored(native.ImVec4(1, .7, .3, 1) if issue['level'] != 'error' else native.ImVec4(1, .4, .35, 1),
                                issue['message'])

    def images(self, panel):
        board = self.board
        if not native.collapsing_header(tr('Images'), native.TreeNodeFlags_.default_open):
            return
        for position, entry in enumerate(list(panel['images'])):
            imgui.push_id(f'img{position}')
            image(board.folder / entry['file'], 120, 68, 256)
            native.same_line()
            native.begin_group()
            native.set_next_item_width(110)
            index = model.IMAGE_ROLES.index(entry['role'])
            changed, index = imgui.combo('##role', index, list(model.IMAGE_ROLES))
            if changed:
                entry['role'] = model.IMAGE_ROLES[index]
                if entry['role'] == 'keyframe':
                    entry.setdefault('time', round(panel['duration'] / 2, 2))
            if entry['role'] == 'keyframe':
                native.same_line()
                native.set_next_item_width(80)
                _, entry['time'] = imgui.drag_float('s##time', float(entry.get('time', 0.0)), 0.05, 0.0, panel['duration'], '%.2f')
            native.set_next_item_width(200)
            _, entry['caption'] = imgui.input_text('##caption', entry.get('caption', ''))
            if imgui.small_button('Up') and position:
                panel['images'][position - 1], panel['images'][position] = panel['images'][position], panel['images'][position - 1]
            native.same_line()
            if imgui.small_button('Open'):
                open_local(board.folder / entry['file'])
            native.same_line()
            if imgui.small_button('Remove'):
                panel['images'].pop(position)
            native.end_group()
            imgui.pop_id()
        if imgui.small_button('Add images...'):
            dialogs.open('images' + panel['id'], 'Images for this panel', IMAGE_FILTER, multiple=True)
        chosen = dialogs.result('images' + panel['id'])
        for path in chosen or []:
            relative = self.act(board.import_asset, path)
            if relative:
                role = 'sketch' if not panel['images'] else 'reference'
                panel['images'].append({'file': relative, 'role': role, 'caption': ''})
        native.same_line()
        if imgui.small_button('Paste image##panel'):
            self.paste_into(lambda relative: panel['images'].append(
                {'file': relative, 'role': 'sketch' if not panel['images'] else 'reference', 'caption': ''}))
        native.text_disabled(tr('Roles: sketch (what the shot looks like), first / last frame, keyframe at a time, reference.'))

    def prompt(self, panel):
        board = self.board
        prompt = panel['prompt']
        if not native.collapsing_header(tr('Prompt'), native.TreeNodeFlags_.default_open):
            return
        native.text(tr('Scene'))
        _, prompt['scene'] = imgui.input_text_multiline('##scene', prompt['scene'], native.ImVec2(-1, 50))
        native.text(tr('Action'))
        _, prompt['action'] = imgui.input_text_multiline('##action', prompt['action'], native.ImVec2(-1, 80))
        rows = ((('shotSize', model.SHOT_SIZES, 'Shot size', 180),), (('angle', model.ANGLES, 'Angle', 180),),
                (('cameraMove', model.CAMERA_MOVES, 'Camera', 180),),
                (('cameraAmplitude', model.AMPLITUDES, 'Amplitude', 100), ('cameraSpeed', model.SPEEDS, 'Speed', 100)))
        for row in rows:
            for position, (key, values, label, width) in enumerate(row):
                if position:
                    native.same_line()
                native.set_next_item_width(width)
                index = values.index(prompt.get(key, '')) if prompt.get(key, '') in values else 0
                _, index = imgui.combo(label, index, [v if v else '-' for v in values])
                prompt[key] = values[index]
        native.set_next_item_width(200)
        _, prompt['lens'] = imgui.input_text('Lens', prompt.get('lens', ''))
        native.text(tr('Dialogue'))
        characters = [i for i in board.doc['library'] if i['kind'] == 'character']
        for position, line in enumerate(list(prompt['dialogue'])):
            imgui.push_id(f'dlg{position}')
            options = [c['name'] for c in characters] + ['(free name)']
            ids = [c['id'] for c in characters]
            current = ids.index(line.get('speaker')) if line.get('speaker') in ids else len(ids)
            native.set_next_item_width(120)
            changed, current = imgui.combo('##speaker', current, options)
            if changed:
                line['speaker'] = ids[current] if current < len(ids) else ''
            if current == len(ids):
                native.same_line()
                native.set_next_item_width(100)
                _, line['speaker'] = imgui.input_text('##free', line.get('speaker', ''))
            native.same_line()
            native.set_next_item_width(90)
            _, line['language'] = imgui.input_text('##lang', line.get('language', 'English'))
            native.set_next_item_width(-110)
            _, line['line'] = imgui.input_text('##line', line.get('line', ''))
            native.same_line()
            _, line['offScreen'] = imgui.checkbox('off', bool(line.get('offScreen')))
            native.same_line()
            if imgui.small_button('x'):
                prompt['dialogue'].pop(position)
            imgui.pop_id()
        if imgui.small_button('Add a line'):
            prompt['dialogue'].append({'speaker': characters[0]['id'] if characters else '', 'language':
                                       board.doc['settings'].get('language', 'English'), 'line': '', 'offScreen': False})
        native.set_next_item_width(-80)
        _, prompt['sound'] = imgui.input_text('Sound##sound', prompt['sound'])
        native.set_next_item_width(-80)
        _, prompt['music'] = imgui.input_text('Music##music', prompt['music'])
        native.text(tr('Free text'))
        _, prompt['freeText'] = imgui.input_text_multiline('##free', prompt['freeText'], native.ImVec2(-1, 60))

    def references(self, panel):
        board = self.board
        if not native.collapsing_header(tr('References'), native.TreeNodeFlags_.default_open):
            return
        if not board.doc['library']:
            native.text_disabled(tr('Add characters, locations or images in the left column, then tick them here '
                                    '(or drag them onto a card).'))
        for item in board.doc['library']:
            ticked = item['id'] in panel['references']
            changed, ticked = native.checkbox(f"{item['name']} ({tr(item['kind'])})##ref{item['id']}", ticked)
            if changed:
                if ticked:
                    panel['references'].append(item['id'])
                else:
                    panel['references'].remove(item['id'])

    def settings(self):
        board = self.board
        if not native.collapsing_header(tr('Storyboard settings'), native.TreeNodeFlags_.default_open):
            return
        native.set_next_item_width(-1)
        _, board.doc['title'] = imgui.input_text('##storytitle', board.doc['title'])
        _, board.doc['description'] = imgui.input_text_multiline('##storydesc', board.doc.get('description', ''),
                                                                 native.ImVec2(-1, 60))
        settings = board.doc['settings']
        native.set_next_item_width(120)
        index = model.ASPECTS.index(settings['aspect']) if settings['aspect'] in model.ASPECTS else 0
        _, index = imgui.combo('Aspect', index, list(model.ASPECTS))
        settings['aspect'] = model.ASPECTS[index]
        native.set_next_item_width(120)
        _, settings['defaultDuration'] = imgui.drag_float('Default duration', float(settings['defaultDuration']), 0.1, 0.1, 600, '%.1f s')
        native.set_next_item_width(120)
        _, settings['maxSegment'] = imgui.drag_float('Longest generation', float(settings['maxSegment']), 0.1, 1, 600, '%.1f s')
        native.set_next_item_width(-1)
        _, settings['style'] = imgui.input_text('Style##style', settings.get('style', ''))
        native.set_next_item_width(160)
        _, settings['language'] = imgui.input_text('Dialogue language', settings.get('language', 'English'))
        errors = [i for i in self.issues if i['level'] == 'error']
        native.text(f'{len(self.issues)} {tr("remarks")}, {len(errors)} {tr("errors")}')
        for issue in self.issues[:20]:
            native.bullet_text(issue['message'])

    # ------------------------------------------------------------------ animatic player
    def play_time(self):
        if not self.play:
            return 0.0
        if self.play.get('paused_at') is not None:
            return self.play['paused_at']
        return time.monotonic() - self.play['start']

    def player(self):
        board = self.board
        elapsed = self.play_time()
        rows = board.timeline()
        total = board.total_duration()
        if elapsed >= total:
            self.play['paused_at'] = total
            elapsed = total
        current = next((r for r in rows if r['start'] <= elapsed < r['end']), rows[-1] if rows else None)
        native.set_next_window_size(native.ImVec2(960, 640), native.Cond_.first_use_ever)
        opened, keep = native.begin(tr('Animatic') + '###animatic', True)
        if opened and current:
            _, _, panel = board.find(current['id'])
            number = [p['id'] for p in board.panels()].index(panel['id']) + 1
            area = native.get_content_region_avail()
            picture = export.main_image(board, panel)
            if picture:
                image(picture, area.x, area.y - 90, 1280)
            else:
                native.dummy(native.ImVec2(area.x, area.y - 90))
            native.text(f'{number}. {panel["title"]}  -  {elapsed:.1f} / {total:.1f} s')
            native.text_wrapped(export.panel_text(board, panel)[:300])
            paused = self.play.get('paused_at') is not None
            if imgui.button('Play' if paused else 'Pause'):
                if paused:
                    start = self.play['paused_at'] if self.play['paused_at'] < total else 0.0
                    self.play = {'start': time.monotonic() - start}
                else:
                    self.play['paused_at'] = elapsed
            native.same_line()
            native.set_next_item_width(-1)
            changed, value = native.slider_float('##scrub', elapsed, 0.0, max(total, 0.01), '%.1f s')
            if changed:
                self.play = {'start': time.monotonic() - value, 'paused_at': value}
                self.selected = current['id']
        native.end()
        if not keep:
            self.play = None

    # ------------------------------------------------------------------ frame
    def draw(self):
        self.frames += 1
        self.toolbar()
        if not self.board:
            native.text_wrapped(tr('Create a storyboard (New) or open one to start.'))
            return
        if time.monotonic() - self._issues_at > 1.0:
            self.issues, self._issues_at = self.board.validate(), time.monotonic()
        avail = native.get_content_region_avail()
        native.begin_child('library', native.ImVec2(260, avail.y - 150), native.ChildFlags_.borders)
        self.library()
        native.end_child()
        native.same_line()
        native.begin_child('board', native.ImVec2(avail.x - 260 - 440 - 16, avail.y - 150), native.ChildFlags_.borders)
        self.board_view()
        native.end_child()
        native.same_line()
        native.begin_child('inspector', native.ImVec2(0, avail.y - 150), native.ChildFlags_.borders)
        self.inspector()
        native.end_child()
        native.begin_child('timeline', native.ImVec2(0, 0), native.ChildFlags_.borders)
        self.timeline()
        native.end_child()
        if self.play:
            self.player()
        self.layout.poll()
        self.track()


def main():
    smoke = '--smoke-test' in sys.argv
    tab = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--ui-test-tab=')), '')
    runner = hello_imgui.RunnerParams()
    runner.app_window_params.window_title = 'CyTools Storyboard'
    runner.app_window_params.window_geometry.size = (1600, 980)
    (ROOT / 'data/settings').mkdir(parents=True, exist_ok=True)
    runner.ini_filename = str(ROOT / 'data/settings/imgui.ini')
    runner.fps_idling.enable_idling = True
    with create_runtime(ROOT / 'data/jobs') as runtime:
        editor = Editor(runtime)
        from gui.updates import UpdatesTab
        updates = UpdatesTab()

        def capture():
            return {'operationId': 'describe_storyboard',
                    'parameters': {'project': str(editor.board.folder) if editor.board else ''}}

        def restore(value):
            project = value.get('parameters', {}).get('project')
            if project:
                editor.open(project)

        configure_generation(runtime, capture, restore)

        def gui():
            if imgui.begin_tab_bar('###story-tabs'):
                opened, _ = imgui.begin_tab_item('Storyboard###tab-board')
                if opened:
                    try:
                        editor.draw()
                    except Exception:
                        import traceback
                        from ui_common import journal
                        journal.write(traceback.format_exc(), 'ERROR')
                        raise
                    imgui.end_tab_item()
                flags = native.TabItemFlags_.set_selected if editor.select_tab == 'Layout' else 0
                opened, _ = imgui.begin_tab_item('Layout###tab-layout', None, flags)
                if opened:
                    editor.select_tab = ''
                    try:
                        editor.toolbar()
                        editor.layout.draw()
                        editor.frames += 1
                        editor.track()
                    except Exception:
                        import traceback
                        from ui_common import journal
                        journal.write(traceback.format_exc(), 'ERROR')
                        raise
                    imgui.end_tab_item()
                opened, _ = imgui.begin_tab_item('Updates###tab-updates')
                if opened:
                    updates.draw()
                    imgui.end_tab_item()
                imgui.end_tab_bar()
            if editor.board and '--ui-test-film' in sys.argv and not editor.film.open and editor.frames < 5:
                editor.film.show()
            editor.film.draw()
            if editor.board and '--ui-test-workflow' in sys.argv and not editor.workflow.open and editor.frames < 5:
                editor.workflow.show()
            editor.workflow.draw()
            if smoke and editor.frames > (160 if tab else 40):
                runner.app_shall_exit = True

        runner.callbacks.show_gui = gui
        try:
            run(runner)
        finally:
            editor.save()
            editor.layout.worker.close()
        if smoke:
            from standalone_log import save_screenshot
            from ui_common import preferences
            reports = ROOT / 'data/reports'
            reports.mkdir(parents=True, exist_ok=True)
            save_screenshot(reports / f'ui-storyboard{"-" + tab.lower() if tab else ""}{"-film" if "--ui-test-film" in sys.argv else ""}{"-workflow" if "--ui-test-workflow" in sys.argv else ""}-{preferences.values["language"]}.png',
                            hello_imgui.final_app_window_screenshot())


if __name__ == '__main__':
    main()

"""CyTools_Storyboard desktop application (Dear ImGui).

The window edits the storyboard in memory and writes it to disk a second after every
change (and before any export), so the operations - which read the project from disk -
always see what the window shows. Changes made to the project by another client (CLI,
MCP) are picked up when the window has nothing unsaved. Undo/redo keeps whole snapshots.
"""
import copy
import json
import os
import sys
import threading
import time
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

from imgui_bundle import hello_imgui, imgui as native  # noqa: E402

import cyui  # noqa: E402
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
        self.actor = runtime.authenticate(runtime.create_client('ImGui', permissions=('network',))['token'])
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
        self.library_search = ''
        self.confirm_sequence = ''
        self.select_tab = next((a.split('=', 1)[1] for a in sys.argv if a.startswith('--ui-test-tab=')), '')
        from gui.layout_editor import LayoutEditor
        from gui.film_export import FilmExportWindow
        self.layout = LayoutEditor(self)
        self.film = FilmExportWindow(self)
        from gui.workflow_export import WorkflowExportWindow
        self.workflow = WorkflowExportWindow(self)
        from gui.images_tab import ImagesTab
        self.image_tab = ImagesTab(self)
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
    def _tool(self, glyph, tip, active=False):
        """An icon button of the toolbar, on the same line as the previous one."""
        native.same_line(0, cyui.dp(2))
        return cyui.icon_button(glyph, tr(tip), active)

    def toolbar(self):
        ic = cyui.icon
        cyui.begin_toolbar('##maintoolbar')
        if cyui.icon_button(ic.add, tr('New storyboard')):
            native.open_popup('new-storyboard')
        if native.begin_popup('new-storyboard'):
            cyui.section_title(tr('New storyboard'))
            native.set_next_item_width(cyui.dp(260))
            _, self.new_title = imgui.input_text('Title', self.new_title)
            if cyui.primary_button(tr('Create')) and self.new_title.strip():
                try:
                    board = model.Storyboard.create(PROJECTS, self.new_title.strip())
                    self.open(board.folder)
                    self.new_title = ''
                    native.close_current_popup()
                    cyui.notify(tr('Storyboard created'), 'success')
                except model.StoryboardError as exc:
                    self.message = str(exc)
            native.end_popup()
        if self._tool(ic.open_file, 'Open a storyboard...'):
            dialogs.open('open', 'Open a storyboard', ['Storyboard', 'storyboard.json'], PROJECTS)
        chosen = dialogs.result('open')
        if chosen:
            try:
                self.save()
                self.open(chosen[0])
            except model.StoryboardError as exc:
                self.message = str(exc)
        if self._tool(ic.clock, 'Recent storyboards'):
            native.open_popup('recent-list')
        if native.begin_popup('recent-list'):
            cyui.section_title(tr('Recent'))
            for path in recent():
                if native.selectable(Path(path).name, False)[0]:
                    self.save()
                    self.open(path)
            if not recent():
                cyui.text_faint(tr('Nothing yet.'))
            native.end_popup()
        if not self.board:
            cyui.end_toolbar()
            return
        if self._tool(ic.save, 'Save as... (a copy under another title)'):
            self.new_title = self.board.doc['title'] + ' 2'
            native.open_popup('save-as')
        if native.begin_popup('save-as'):
            cyui.section_title(tr('Save as...'))
            native.push_text_wrap_pos(cyui.dp(320))
            cyui.text_dim(tr('The project is saved by itself after every change. This makes a copy under '
                             'another title and opens it.'))
            native.pop_text_wrap_pos()
            native.set_next_item_width(cyui.dp(260))
            _, self.new_title = imgui.input_text('Title of the copy', self.new_title)
            if cyui.primary_button(tr('Save the copy')) and self.new_title.strip():
                try:
                    self.save()
                    duplicate = self.board.save_as(self.board.folder.parent, self.new_title.strip())
                    self.open(duplicate.folder)
                    self.new_title = ''
                    native.close_current_popup()
                    cyui.notify(tr('Copy saved and opened'), 'success')
                except (model.StoryboardError, OSError) as exc:
                    self.message = str(exc)
            native.end_popup()
        cyui.toolbar_separator()
        keys = native.get_io()
        with cyui.scoped_disabled(not self.undo):
            if cyui.icon_button(ic.undo, tr('Undo (Ctrl+Z)')) or (keys.key_ctrl and native.is_key_pressed(native.Key.z)
                                                               and not keys.want_text_input and self.undo):
                self.undo_step()
        native.same_line(0, cyui.dp(2))
        with cyui.scoped_disabled(not self.redo):
            if cyui.icon_button(ic.redo, tr('Redo (Ctrl+Y)')) or (keys.key_ctrl and native.is_key_pressed(native.Key.y)
                                                               and not keys.want_text_input and self.redo):
                self.redo_step()
        cyui.toolbar_separator()
        if cyui.icon_text_button(ic.add, tr('Panel'), 'ghost'):
            after = self.selected if self.selected else ''
            panel = self.act(self.board.add_panel, '', after)
            if panel:
                self.selected = panel['id']
        cyui.tooltip(tr('Add a panel after the selected one'))
        native.same_line(0, cyui.dp(2))
        if cyui.icon_text_button(ic.library, tr('Sequence'), 'ghost'):
            self.act(self.board.add_sequence)
        cyui.tooltip(tr('Add a sequence at the end'))
        cyui.toolbar_separator()
        if cyui.icon_button(ic.play, tr('Play the animatic'), bool(self.play)):
            self.play = {'start': time.monotonic(), 'paused': 0.0}
        native.same_line(0, cyui.dp(2))
        if cyui.icon_text_button(ic.export_file, tr('Export'), 'ghost'):
            native.open_popup('export-menu')
        cyui.tooltip(tr('Contact sheet, script, animatic, MiniMax H3 film and workflow'))
        if native.begin_popup('export-menu'):
            cyui.overline(tr('DOCUMENTS'))
            if native.selectable(tr('Contact sheet (PNG)'), False)[0]:
                self.submit('export_contact_sheet', {'project': str(self.board.folder)})
            if native.selectable(tr('Script (HTML)'), False)[0]:
                self.submit('export_summary', {'project': str(self.board.folder), 'format': 'html'})
            if native.selectable(tr('Script (Markdown)'), False)[0]:
                self.submit('export_summary', {'project': str(self.board.folder), 'format': 'md'})
            if native.selectable(tr('Animatic (MP4)'), False)[0]:
                self.submit('export_animatic', {'project': str(self.board.folder)})
            cyui.space(4)
            cyui.overline('MINIMAX H3')
            if native.selectable(tr('MiniMax H3 film (ComfyUI / Colab)...'), False)[0]:
                self.film.show()
            if native.selectable(tr('MiniMax H3 workflow (one generation per panel)...'), False)[0]:
                self.workflow.show()
            native.end_popup()
        native.same_line(0, cyui.dp(2))
        if cyui.icon_button(ic.folder, tr('Open the project folder')):
            open_local(self.board.folder)
        cyui.toolbar_separator()
        self._job_line()
        # right side: the project, its state and the card size
        total = self.board.total_duration()
        title = self.board.doc['title']
        detail = f'{len(self.board.panels())} {tr("panels")}  -  {int(total // 60)}:{total % 60:04.1f}'
        width = cyui.dp(150) + native.calc_text_size(title).x + native.calc_text_size(detail).x + cyui.dp(150)
        native.same_line()
        cyui.align_right(width)
        with cyui.scoped_font(cyui.bold_font(), 1.0):
            native.text(title)
        if native.is_item_hovered():
            cyui.tooltip(str(self.board.folder))
        native.same_line()
        cyui.text_dim(detail)
        native.same_line()
        cyui.badge(tr('saving...' if self.dirty else 'saved'), 'warning' if self.dirty else 'success')
        native.same_line(0, cyui.dp(12))
        native.set_next_item_width(cyui.dp(140))
        changed, self.zoom = cyui.slider_bar('##cardsize', self.zoom, 120.0, 360.0, tr('cards') + ' %.0f')
        cyui.tooltip(tr('Card size'))
        cyui.end_toolbar()
        if self.message:
            cyui.notify(self.message, 'warning', 6.0)
            self.message = ''

    def _job_line(self):
        """The export in progress, or its result, next to the toolbar buttons."""
        if not self.job:
            return
        job = self.runtime.get_job(self.actor, self.job['jobId'])
        self.job = job
        native.same_line()
        if job['state'] == 'Completed':
            file = job['outputs'].get('file')
            if not self.job.get('_told'):
                cyui.notify(tr('Exported: ') + Path(str(file)).name, 'success')
                self.job['_told'] = True
            if cyui.icon_text_button(cyui.icon.open_file, tr('Open the export'), 'outline'):
                open_local(file)
            cyui.tooltip(str(file))
            native.same_line(0, cyui.dp(2))
            if cyui.icon_button(cyui.icon.close, tr('Dismiss')):
                self.job = None
        elif job['state'] in ('Failed', 'Cancelled'):
            cyui.notify((job.get('error') or {}).get('message') or tr(job['state']), 'error', 8.0)
            self.job = None
        else:
            progress = job.get('progress') or {}
            cyui.progress_bar((progress.get('percent') or 0) / 100, (cyui.dp(220), native.get_frame_height()),
                              progress.get('currentStep') or tr(job['state']))

    # ------------------------------------------------------------------ library
    def library(self):
        board = self.board
        cyui.overline(tr('REFERENCES'))
        native.same_line()
        cyui.badge(str(len(board.doc['library'])))
        cyui.space(2)
        _, self.library_search = cyui.search_field('##libsearch', self.library_search, tr('Search'), -1)
        kinds = ['all', *model.KINDS]
        native.set_next_item_width(-1)
        _, self.kind_filter = imgui.combo('##kind', self.kind_filter, ['All'] + [KIND_LABELS[k] for k in model.KINDS])
        native.set_next_item_width(cyui.dp(100))
        _, self.new_item['kind'] = imgui.combo('##newkind', self.new_item['kind'], list(model.KINDS))
        native.same_line(0, cyui.dp(4))
        _, self.new_item['name'] = cyui.text_field('##newname', self.new_item['name'], tr('New reference'),
                                                   -(native.get_frame_height() + cyui.dp(4)))
        native.same_line(0, cyui.dp(4))
        if cyui.icon_button(cyui.icon.add, tr('Add this reference to the library')) and self.new_item['name'].strip():
            item = self.act(board.add_library_item, model.KINDS[self.new_item['kind']], self.new_item['name'].strip())
            if item:
                self.selected_item, self.new_item['name'] = item['id'], ''
        cyui.divider(3)
        if not board.doc['library']:
            cyui.empty_state(tr('No reference yet'), tr('Add characters, places, objects...'), cyui.icon.library)
            return
        search = self.library_search.strip().casefold()
        shown = 0
        for item in board.doc['library']:
            if self.kind_filter and item['kind'] != kinds[self.kind_filter]:
                continue
            if search and search not in item['name'].casefold() and search not in (item.get('description') or '').casefold():
                continue
            shown += 1
            imgui.push_id('lib' + item['id'])
            first = next((board.folder / f for f in item.get('files') or []
                          if (board.folder / f).suffix.lower() in model.IMAGE_SUFFIXES), None)
            row = native.get_cursor_screen_pos()
            opened = native.selectable('##row', self.selected_item == item['id'], 0, native.ImVec2(0, cyui.dp(44)))[0]
            if opened:
                self.selected_item = item['id'] if self.selected_item != item['id'] else None
            if native.begin_drag_drop_source():
                self.drop_ids[hash(item['id']) & 0x7fffffff] = item['id']
                native.set_drag_drop_payload_py_id('LIBRARY', hash(item['id']) & 0x7fffffff)
                native.text(item['name'])
                native.end_drag_drop_source()
            cyui.tooltip(tr('Drag it onto a card to use it in that panel'))
            after = native.get_cursor_screen_pos()
            native.set_cursor_screen_pos(native.ImVec2(row.x + cyui.dp(2), row.y + cyui.dp(2)))
            if first is not None:
                image(first, cyui.dp(40), cyui.dp(40), 128)
            else:
                native.dummy(native.ImVec2(cyui.dp(40), cyui.dp(40)))
            native.set_cursor_screen_pos(native.ImVec2(row.x + cyui.dp(50), row.y + cyui.dp(4)))
            native.text(item['name'])
            native.set_cursor_screen_pos(native.ImVec2(row.x + cyui.dp(50), row.y + cyui.dp(22)))
            files = len(item.get('files') or [])
            cyui.text_faint(tr(item['kind']) + (f'  -  {files} ' + tr('file(s)') if files else ''))
            native.set_cursor_screen_pos(after)
            native.dummy(native.ImVec2(0, 0))
            if self.selected_item == item['id']:
                self.library_item(item)
            imgui.pop_id()
        if not shown:
            cyui.text_faint(tr('Nothing matches the search.'))

    def library_item(self, item):
        board = self.board
        cyui.begin_card('##libitem')
        if cyui.begin_properties('##libprops', 70):
            cyui.property(tr('Name'))
            _, item['name'] = imgui.input_text('##name', item['name'])
            cyui.property(tr('Kind'))
            index = model.KINDS.index(item['kind'])
            changed, index = imgui.combo('##itemkind', index, list(model.KINDS))
            if changed:
                item['kind'] = model.KINDS[index]
            cyui.property(tr('Description'))
            _, item['description'] = imgui.input_text_multiline('##desc', item.get('description', ''),
                                                                native.ImVec2(-1, cyui.dp(60)))
            cyui.property(tr('Tags'))
            tags = ', '.join(item.get('tags') or [])
            changed, tags = cyui.text_field('##tags', tags, tr('comma separated'), -1)
            if changed:
                item['tags'] = [t.strip() for t in tags.split(',') if t.strip()]
            cyui.end_properties()
        files = list(item.get('files') or [])
        if files:
            cyui.section_title(tr('Files'))
        for position, file in enumerate(files):
            path = board.folder / file
            if path.suffix.lower() in model.IMAGE_SUFFIXES:
                image(path, cyui.dp(150), cyui.dp(90), 256)
            else:
                cyui.text_dim(board.doc.get('assetNames', {}).get(Path(file).name, Path(file).name))
            native.same_line()
            if cyui.icon_button(cyui.icon.close, tr('Take this file out of the reference') + f'##file{position}'):
                item['files'].pop(position)
        if cyui.icon_text_button(cyui.icon.add, tr('Add files...')):
            dialogs.open('libfiles' + item['id'], 'Reference files', MEDIA_FILTER, multiple=True)
        chosen = dialogs.result('libfiles' + item['id'])
        for path in chosen or []:
            relative = self.act(board.import_asset, path)
            if relative:
                item.setdefault('files', []).append(relative)
        native.same_line()
        if cyui.icon_text_button(cyui.icon.paste, tr('Paste image')):
            self.paste_into(lambda relative: item.setdefault('files', []).append(relative))
        if cyui.button(tr('Delete reference'), 'danger', small=True):
            self.act(board.remove_library_item, item['id'])
            self.selected_item = None
        cyui.end_card()

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
        p = cyui.palette()
        width = self.zoom
        thumb_h = width * 9 / 16
        height = thumb_h + cyui.dp(52)
        selected = panel['id'] == self.selected
        native.begin_group()
        start = native.get_cursor_screen_pos()
        draw = native.get_window_draw_list()
        native.invisible_button('card', native.ImVec2(width, height))
        clicked = native.is_item_clicked()
        hovered = native.is_item_hovered()
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
            native.separator()
            if native.menu_item(tr('Delete'), '', False)[0]:
                self.act(board.remove_panel, panel['id'])
                if self.selected == panel['id']:
                    self.selected = None
            native.end_popup()
        end = native.ImVec2(start.x + width, start.y + height)
        rounding = cyui.dp(cyui.metrics().rounding_large)
        draw.add_rect_filled(start, end, p.bg3 if hovered and not selected else p.bg2, rounding)
        inset = cyui.dp(4)
        picture = export.main_image(board, panel)
        thumb_min = native.ImVec2(start.x + inset, start.y + inset)
        thumb_max = native.ImVec2(end.x - inset, start.y + thumb_h - inset)
        draw.add_rect_filled(thumb_min, thumb_max, p.bg0, cyui.dp(cyui.metrics().rounding))
        texture = None
        if picture:
            from gui.common import textures
            texture = textures.get(picture, 384)
        if texture:
            scale = min((thumb_max.x - thumb_min.x) / texture.width, (thumb_max.y - thumb_min.y) / texture.height)
            w, h = texture.width * scale, texture.height * scale
            x0 = thumb_min.x + (thumb_max.x - thumb_min.x - w) / 2
            y0 = thumb_min.y + (thumb_max.y - thumb_min.y - h) / 2
            draw.add_image(native.ImTextureRef(texture.texture_id()), native.ImVec2(x0, y0), native.ImVec2(x0 + w, y0 + h))
        else:
            if panel.get('color'):
                draw.add_rect_filled(thumb_min, thumb_max, cyui.alpha(native.get_color_u32(colour(panel['color'])), 0.55),
                                     cyui.dp(cyui.metrics().rounding))
            cyui.centred_text(draw, thumb_min, thumb_max, p.textFaint, tr('no image'))
        status = {'idea': p.textFaint, 'draft': p.warning, 'ready': p.success, 'generated': p.info}.get(panel['status'],
                                                                                                         p.textFaint)
        draw.add_circle_filled(native.ImVec2(end.x - cyui.dp(13), start.y + cyui.dp(13)), cyui.dp(7), p.bg0)
        draw.add_circle_filled(native.ImVec2(end.x - cyui.dp(13), start.y + cyui.dp(13)), cyui.dp(5), status)
        cyui.clipped_text(draw, native.ImVec2(start.x + cyui.dp(8), start.y + thumb_h + cyui.dp(4)), width - cyui.dp(16),
                          p.text, f'{number}. {panel["title"]}')
        detail = f'{panel["duration"]:.1f} s'
        if panel['references']:
            detail += f'   {len(panel["references"])} ref'
        if panel['prompt'].get('dialogue'):
            detail += '   ' + tr('dialogue')
        cyui.clipped_text(draw, native.ImVec2(start.x + cyui.dp(8), start.y + thumb_h + cyui.dp(24)), width - cyui.dp(16),
                          p.textDim, detail)
        if panel.get('color'):
            draw.add_rect_filled(native.ImVec2(start.x + rounding, end.y - cyui.dp(3)), native.ImVec2(end.x - rounding, end.y),
                                 native.get_color_u32(colour(panel['color'])), cyui.dp(2))
        if selected:
            draw.add_rect(start, end, p.accent, rounding, cyui.dp(2))
        else:
            draw.add_rect(start, end, p.line, rounding)
        native.end_group()
        if hovered:
            cyui.tooltip(tr('Click to edit, drag to move, right click for more. Drop a reference on it to use it.'))
        if clicked:
            self.selected = panel['id']

    def board_view(self):
        board = self.board
        number = 0
        available = native.get_content_region_avail().x
        per_row = max(1, int(available // (self.zoom + native.get_style().item_spacing.x)))
        for sequence in list(board.sequences()):
            imgui.push_id('seq' + sequence['id'])
            with cyui.scoped_font(cyui.bold_font(), 1.05):
                native.set_next_item_width(cyui.dp(260))
                _, sequence['title'] = imgui.input_text('##title', sequence['title'])
            if native.begin_drag_drop_target():
                payload = native.accept_drag_drop_payload_py_id('PANEL')
                if payload is not None and self.drop_ids.get(payload.data_id):
                    self.act(board.move_panel, self.drop_ids[payload.data_id], sequence['id'], None)
                native.end_drag_drop_target()
            native.same_line()
            duration = sum(p['duration'] for p in sequence['panels'])
            native.align_text_to_frame_padding()
            cyui.text_dim(f'{len(sequence["panels"])} {tr("panels")}  -  {duration:.1f} s')
            native.same_line()
            if cyui.icon_button(cyui.icon.add, tr('Add a panel to this sequence')):
                panel = self.act(board.add_panel, sequence['id'])
                if panel:
                    self.selected = panel['id']
            if len(board.sequences()) > 1:
                native.same_line(0, cyui.dp(2))
                if cyui.icon_button(cyui.icon.trash, tr('Delete this sequence')):
                    self.confirm_sequence = sequence['id']
            for index, panel in enumerate(sequence['panels']):
                number += 1
                if index % per_row:
                    native.same_line()
                imgui.push_id(panel['id'])
                self.card(panel, number)
                imgui.pop_id()
            if not sequence['panels']:
                cyui.callout('neutral', tr('Empty: add a panel or drop one on the title.'))
            cyui.divider(6)
            imgui.pop_id()
        if self.confirm_sequence:
            shown, keep = cyui.begin_modal(tr('Delete this sequence?') + '###confirmseq', True)
            if shown:
                try:
                    sequence = board.sequence(self.confirm_sequence)
                    native.text_wrapped(f'« {sequence["title"]} » - {len(sequence["panels"])} ' + tr('panels'))
                except model.StoryboardError:
                    sequence = None
                answer = cyui.modal_buttons(tr('Delete'), tr('Keep'), True)
                if answer == 1 and sequence is not None:
                    self.act(board.remove_sequence, sequence['id'])
                if answer or not keep:
                    self.confirm_sequence = ''
                cyui.end_modal()
            else:
                self.confirm_sequence = ''

    # ------------------------------------------------------------------ timeline
    def timeline(self):
        from gui.modular_views import TimelineView
        if not hasattr(self,'_timeline_view'):self._timeline_view=TimelineView()
        self._timeline_view.draw(self)

    # ------------------------------------------------------------------ inspector
    def inspector(self):
        board = self.board
        try:
            sequence, _, panel = board.find(self.selected) if self.selected else (None, None, None)
        except model.StoryboardError:
            panel, self.selected = None, None
        if panel is None:
            cyui.panel_header(tr('Storyboard'), tr('Select a panel to edit it.'))
            cyui.divider()
            self.settings()
            return
        number = [p['id'] for p in board.panels()].index(panel['id']) + 1
        cyui.panel_header(f'{tr("Panel")} {number}', sequence['title'])
        cyui.space(4)
        from gui.modular_views import PanelInspector, transaction
        if not hasattr(self,'_panel_inspector'):self._panel_inspector=PanelInspector()
        self._panel_inspector.draw(self,panel)
        for preset in (4,5,8,10,15):
            if preset!=4:native.same_line(0,cyui.dp(2))
            if cyui.button(f'{preset}s##dur{preset}','primary' if panel['duration']==preset else 'ghost',small=True):
                transaction(self,lambda:panel.update(duration=float(preset)))
        if cyui.begin_properties('##panelprops',90):
            cyui.property(tr('Colour'))
            value = colour(panel.get('color') or '#34507a')
            changed, picked = native.color_edit3('##colour', [value.x, value.y, value.z], native.ColorEditFlags_.no_inputs)
            if changed:
                panel['color'] = hex_colour(picked)
            native.same_line()
            if panel.get('color') and cyui.ghost_button(tr('No colour')):
                panel['color'] = ''
            cyui.end_properties()
        own = [i for i in self.issues if i['panel'] == panel['id']]
        for issue in own:
            cyui.callout('error' if issue['level'] == 'error' else 'warning', issue['message'])
        cyui.space(4)
        if cyui.begin_section(tr('Layout') + '###sec-layout'):
            self.layout.summary(panel)
            cyui.end_section()
        self.images(panel)
        self.prompt(panel)
        self.references(panel)
        if cyui.begin_section(tr('Transition and notes') + '###sec-transition'):
            transition = panel['transition']
            if cyui.begin_properties('##transprops', 90):
                cyui.property(tr('Transition to next'))
                index = model.TRANSITIONS.index(transition['type'])
                _, index = imgui.combo('##transition', index, list(model.TRANSITIONS))
                transition['type'] = model.TRANSITIONS[index]
                if transition['type'] != 'cut':
                    cyui.property(tr('Length'))
                    _, transition['duration'] = imgui.drag_float('##trans', float(transition['duration']), 0.05, 0.0, 10.0,
                                                                 '%.2f s')
                cyui.property(tr('Notes'))
                _, panel['notes'] = imgui.input_text_multiline('##notes', panel['notes'], native.ImVec2(-1, cyui.dp(70)))
                cyui.end_properties()
            cyui.end_section()

    def images(self, panel):
        board = self.board
        if not cyui.begin_section(tr('Images') + f' ({len(panel["images"])})###sec-images'):
            return
        if not panel['images']:
            cyui.text_faint(tr('No image yet: add a sketch, a first frame, a keyframe or a reference.'))
        for position, entry in enumerate(list(panel['images'])):
            imgui.push_id(f'img{position}')
            image(board.folder / entry['file'], cyui.dp(120), cyui.dp(68), 256)
            native.same_line()
            native.begin_group()
            native.set_next_item_width(cyui.dp(140))
            index = model.IMAGE_ROLES.index(entry['role'])
            changed, index = imgui.combo('##role', index, list(model.IMAGE_ROLES))
            if changed:
                entry['role'] = model.IMAGE_ROLES[index]
                if entry['role'] == 'keyframe':
                    entry.setdefault('time', round(panel['duration'] / 2, 2))
            if entry['role'] == 'keyframe':
                native.same_line()
                native.set_next_item_width(cyui.dp(80))
                _, entry['time'] = imgui.drag_float('##time', float(entry.get('time', 0.0)), 0.05, 0.0, panel['duration'],
                                                    '%.2f s')
            _, entry['caption'] = cyui.text_field('##caption', entry.get('caption', ''), tr('Caption'), cyui.dp(200))
            with cyui.scoped_disabled(position == 0):
                if cyui.icon_button(cyui.icon.chevron_up, tr('Move up')) and position:
                    panel['images'][position - 1], panel['images'][position] = panel['images'][position], panel['images'][position - 1]
            native.same_line(0, cyui.dp(2))
            if cyui.icon_button(cyui.icon.open_file, tr('Open the file')):
                open_local(board.folder / entry['file'])
            native.same_line(0, cyui.dp(2))
            if cyui.icon_button(cyui.icon.trash, tr('Remove from this panel')):
                panel['images'].pop(position)
            native.end_group()
            imgui.pop_id()
        if cyui.icon_text_button(cyui.icon.add, tr('Add images...')):
            dialogs.open('images' + panel['id'], 'Images for this panel', IMAGE_FILTER, multiple=True)
        chosen = dialogs.result('images' + panel['id'])
        for path in chosen or []:
            relative = self.act(board.import_asset, path)
            if relative:
                role = 'sketch' if not panel['images'] else 'reference'
                panel['images'].append({'file': relative, 'role': role, 'caption': ''})
        native.same_line()
        if cyui.icon_text_button(cyui.icon.paste, tr('Paste image') + '##panel'):
            self.paste_into(lambda relative: panel['images'].append(
                {'file': relative, 'role': 'sketch' if not panel['images'] else 'reference', 'caption': ''}))
        cyui.help_marker(tr('Roles: sketch (what the shot looks like), first / last frame, keyframe at a time, reference.'))
        cyui.end_section()

    def prompt(self, panel):
        board = self.board
        prompt = panel['prompt']
        if not cyui.begin_section(tr('Prompt') + '###sec-prompt'):
            return
        if cyui.begin_properties('##promptprops', 90):
            cyui.property(tr('Scene'))
            _, prompt['scene'] = imgui.input_text_multiline('##scene', prompt['scene'], native.ImVec2(-1, cyui.dp(50)))
            cyui.property(tr('Action'))
            _, prompt['action'] = imgui.input_text_multiline('##action', prompt['action'], native.ImVec2(-1, cyui.dp(80)))
            for key, values, label in (('shotSize', model.SHOT_SIZES, 'Shot size'), ('angle', model.ANGLES, 'Angle'),
                                       ('cameraMove', model.CAMERA_MOVES, 'Camera'),
                                       ('cameraAmplitude', model.AMPLITUDES, 'Amplitude'),
                                       ('cameraSpeed', model.SPEEDS, 'Speed')):
                cyui.property(tr(label))
                index = values.index(prompt.get(key, '')) if prompt.get(key, '') in values else 0
                _, index = imgui.combo('##' + key, index, [v if v else '-' for v in values])
                prompt[key] = values[index]
            cyui.property(tr('Lens'))
            _, prompt['lens'] = cyui.text_field('##lens', prompt.get('lens', ''), '50mm, anamorphic...', -1)
            cyui.property(tr('Sound'))
            _, prompt['sound'] = cyui.text_field('##sound', prompt['sound'], tr('what we hear'), -1)
            cyui.property(tr('Music'))
            _, prompt['music'] = cyui.text_field('##music', prompt['music'], '', -1)
            cyui.property(tr('Free text'))
            _, prompt['freeText'] = imgui.input_text_multiline('##free', prompt['freeText'], native.ImVec2(-1, cyui.dp(60)))
            cyui.end_properties()
        cyui.section_title(tr('Dialogue'))
        characters = [i for i in board.doc['library'] if i['kind'] == 'character']
        for position, line in enumerate(list(prompt['dialogue'])):
            imgui.push_id(f'dlg{position}')
            options = [c['name'] for c in characters] + ['(free name)']
            ids = [c['id'] for c in characters]
            current = ids.index(line.get('speaker')) if line.get('speaker') in ids else len(ids)
            native.set_next_item_width(cyui.dp(120))
            changed, current = imgui.combo('##speaker', current, options)
            if changed:
                line['speaker'] = ids[current] if current < len(ids) else ''
            if current == len(ids):
                native.same_line()
                native.set_next_item_width(cyui.dp(100))
                _, line['speaker'] = imgui.input_text('##free', line.get('speaker', ''))
            native.same_line()
            native.set_next_item_width(cyui.dp(90))
            _, line['language'] = imgui.input_text('##lang', line.get('language', 'English'))
            native.same_line()
            _, line['offScreen'] = cyui.toggle_switch(tr('off screen') + '##off', bool(line.get('offScreen')))
            native.same_line()
            if cyui.icon_button(cyui.icon.trash, tr('Remove this line')):
                prompt['dialogue'].pop(position)
            _, line['line'] = cyui.text_field('##line', line.get('line', ''), tr('What is said'), -1)
            cyui.space(2)
            imgui.pop_id()
        if cyui.icon_text_button(cyui.icon.add, tr('Add a line'), 'ghost'):
            prompt['dialogue'].append({'speaker': characters[0]['id'] if characters else '', 'language':
                                       board.doc['settings'].get('language', 'English'), 'line': '', 'offScreen': False})
        cyui.end_section()

    def references(self, panel):
        board = self.board
        if not cyui.begin_section(tr('References') + f' ({len(panel["references"])})###sec-refs'):
            return
        if not board.doc['library']:
            cyui.text_faint(tr('Add characters, locations or images in the left column, then tick them here '
                               '(or drag them onto a card).'))
        for item in board.doc['library']:
            ticked = item['id'] in panel['references']
            changed, ticked = native.checkbox(f"{item['name']}##ref{item['id']}", ticked)
            native.same_line()
            cyui.text_faint(tr(item['kind']))
            if changed:
                if ticked:
                    panel['references'].append(item['id'])
                else:
                    panel['references'].remove(item['id'])
        cyui.end_section()

    def settings(self):
        board = self.board
        if not cyui.begin_section(tr('Storyboard settings') + '###sec-settings'):
            return
        settings = board.doc['settings']
        if cyui.begin_properties('##storyprops', 120):
            cyui.property(tr('Title'))
            _, board.doc['title'] = imgui.input_text('##storytitle', board.doc['title'])
            cyui.property(tr('Description'))
            _, board.doc['description'] = imgui.input_text_multiline('##storydesc', board.doc.get('description', ''),
                                                                     native.ImVec2(-1, cyui.dp(60)))
            cyui.property(tr('Aspect'))
            index = model.ASPECTS.index(settings['aspect']) if settings['aspect'] in model.ASPECTS else 0
            _, index = imgui.combo('##aspect', index, list(model.ASPECTS))
            settings['aspect'] = model.ASPECTS[index]
            cyui.property(tr('Default duration'))
            _, settings['defaultDuration'] = imgui.drag_float('##defdur', float(settings['defaultDuration']), 0.1, 0.1, 600, '%.1f s')
            cyui.property(tr('Longest generation'))
            _, settings['maxSegment'] = imgui.drag_float('##maxseg', float(settings['maxSegment']), 0.1, 1, 600, '%.1f s')
            cyui.property(tr('Style'), tr('Added to the prompts of the exports and of the generated pictures.'))
            _, settings['style'] = imgui.input_text_multiline('##style', settings.get('style', ''), native.ImVec2(-1, cyui.dp(60)))
            cyui.property(tr('Dialogue language'))
            _, settings['language'] = imgui.input_text('##dlglang', settings.get('language', 'English'))
            cyui.end_properties()
        cyui.end_section()
        errors = [i for i in self.issues if i['level'] == 'error']
        if not self.issues:
            cyui.callout('success', tr('No problem found.'))
        elif cyui.begin_section(f'{len(self.issues)} {tr("remarks")}, {len(errors)} {tr("errors")}###sec-issues'):
            for issue in self.issues[:20]:
                cyui.callout('error' if issue['level'] == 'error' else 'warning', issue['message'])
            cyui.end_section()

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
                image(picture, area.x, area.y - cyui.dp(96), 1280)
            else:
                native.dummy(native.ImVec2(area.x, area.y - cyui.dp(96)))
            cyui.heading(f'{number}. {panel["title"]}', 3)
            native.same_line()
            cyui.text_dim(f'{elapsed:.1f} / {total:.1f} s')
            native.push_text_wrap_pos(0.0)
            cyui.text_dim(export.panel_text(board, panel)[:300])
            native.pop_text_wrap_pos()
            paused = self.play.get('paused_at') is not None
            if cyui.icon_button(cyui.icon.play if paused else cyui.icon.pause, tr('Play') if paused else tr('Pause'),
                                not paused):
                if paused:
                    start = self.play['paused_at'] if self.play['paused_at'] < total else 0.0
                    self.play = {'start': time.monotonic() - start}
                else:
                    self.play['paused_at'] = elapsed
            native.same_line()
            changed, value = cyui.slider_bar('##scrub', elapsed, 0.0, max(total, 0.01), '%.1f s', -1)
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
            cyui.empty_state(tr('No storyboard open'), tr('Create one (+) or open one from the toolbar.'),
                             cyui.icon.document)
            return
        if time.monotonic() - self._issues_at > 1.0:
            self.issues, self._issues_at = self.board.validate(), time.monotonic()
        avail = native.get_content_region_avail()
        side, inspector, strip = cyui.dp(270), cyui.dp(460), cyui.dp(160)
        gap = native.get_style().item_spacing.x
        native.begin_child('library', native.ImVec2(side, avail.y - strip - gap), native.ChildFlags_.borders)
        self.library()
        native.end_child()
        native.same_line()
        native.begin_child('board', native.ImVec2(avail.x - side - inspector - gap * 2, avail.y - strip - gap),
                           native.ChildFlags_.borders)
        self.board_view()
        native.end_child()
        native.same_line()
        native.begin_child('inspector', native.ImVec2(0, avail.y - strip - gap), native.ChildFlags_.borders)
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
    from branding import configure as configure_branding
    configure_branding('Cyberalien.CyTools_Storyboard')
    runner = hello_imgui.RunnerParams()
    runner.app_window_params.window_title = 'CyTools Storyboard'
    runner.app_window_params.window_geometry.size = (1600, 980)
    (ROOT / 'data/settings').mkdir(parents=True, exist_ok=True)
    runner.ini_filename = str(ROOT / 'data/settings/imgui.ini')
    runner.fps_idling.enable_idling = True
    # CYTOOLS_STORYBOARD_JOBS: another jobs folder, so a test window can run next to the real one
    with create_runtime(Path(os.environ.get('CYTOOLS_STORYBOARD_JOBS') or ROOT / 'data/jobs')) as runtime:
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
                flags = native.TabItemFlags_.set_selected if editor.select_tab == 'Images' else 0
                opened, _ = imgui.begin_tab_item('Images###tab-images', None, flags)
                if opened:
                    editor.select_tab = ''
                    try:
                        editor.toolbar()
                        editor.image_tab.draw()
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

"""Window: convert the storyboard into a CyTools_MiniMaxH3 workflow (one H3 generation per panel).

Every choice is an option saved in the project. The table shows, live, for each panel:
how many generations, what H3 really generates and what is kept after trimming, where
the first frame comes from, the references and the exact prompt.
"""
import json
import sys
import time

from imgui_bundle import imgui as native

from ui_common import imgui, tr
from gui.common import open_local
from gui.film_export import depth_controls
from storyboard import h3workflow
from storyboard.model import StoryboardError

CHAIN_LABELS = ['after crossfades', 'always', 'never']
LAYOUT_USES = ['reference', 'first_frame', 'none']
LAYOUT_LABELS = ['a reference picture', 'the first frame', 'unused']
PROMPT_LAYOUTS = ['auto', 'structured', 'integrated']
PROMPT_LABELS = ['auto (structured when characters have pictures)', 'structured (subjects)', 'integrated']
TEMPLATES = [('layoutText', 'Layout render ({n})'), ('sketchText', 'Sketch ({n})'),
             ('referenceText', 'Shot reference ({n})'), ('locationText', 'Location ({n}, {name}, {description})'),
             ('objectText', 'Object ({n}, {name}, {description})'), ('styleText', 'Style ({n}, {name}, {description})'),
             ('videoText', 'Reference video ({n}, {name}, {description})'),
             ('audioText', 'Reference sound ({n}, {name}, {description})'),
             ('continuedText', 'Next part of a long panel')]


class WorkflowExportWindow:
    def __init__(self, editor):
        self.editor = editor
        self.open = False
        self.options = None
        self.preview = None
        self.error = ''
        self.key = None
        self.checked_at = 0.0
        self.expanded = set()

    def show(self):
        self.options = h3workflow.options_for(self.editor.board)
        self.open, self.key = True, None
        if '--ui-test-workflow' in sys.argv:
            self.expanded = {2}

    def _refresh(self):
        board = self.editor.board
        key = json.dumps([self.options, board.doc], sort_keys=True, default=str)
        if key == self.key and time.monotonic() - self.checked_at < 2.0:
            return
        self.key, self.checked_at = key, time.monotonic()
        try:
            _, _, summary, warnings = h3workflow.build(board, self.options, preview=True)
            self.preview, self.error = (summary, warnings), ''
        except StoryboardError as exc:
            self.preview, self.error = None, str(exc)

    def draw(self):
        if not self.open or not self.editor.board:
            return
        native.set_next_window_size(native.ImVec2(1180, 820), native.Cond_.first_use_ever)
        visible, self.open = native.begin(tr('MiniMax H3 workflow') + '###h3workflow', self.open)
        if visible:
            try:
                self._body()
            finally:
                native.end()
        else:
            native.end()

    def _combo(self, label, key, values, labels, width=220):
        native.set_next_item_width(width)
        index = values.index(self.options[key]) if self.options[key] in values else 0
        changed, index = native.combo(tr(label) + f'##{key}', index, [tr(x) for x in labels])
        if changed:
            self.options[key] = values[index]

    def _body(self):
        o = self.options
        native.text_wrapped(tr('One MiniMax H3 generation per panel, with its own frames and references, then one '
                               'edit with the storyboard transitions. Open workflow.json in CyTools_MiniMaxH3 '
                               '(Workflows tab) to run it on the Colab GPU.'))
        native.separator_text(tr('Picture and sampling'))
        edges = list(h3workflow.SHORT_EDGES)
        self._combo('Short edge', 'shortEdge', edges, [f'{e} px' for e in edges], 120)
        native.same_line()
        native.set_next_item_width(90)
        _, o['width'] = imgui.input_int('Width (0 = auto)', int(o['width']), 32)
        native.same_line()
        native.set_next_item_width(90)
        _, o['height'] = imgui.input_int('Height', int(o['height']), 32)
        o['width'], o['height'] = max(0, o['width']), max(0, o['height'])
        native.set_next_item_width(140)
        _, o['seed'] = imgui.input_int('Seed', int(o['seed']))
        o['seed'] = max(0, o['seed'])
        native.same_line()
        self._combo('Seeds', 'seedPolicy', ['fixed', 'increment', 'random'],
                    ['same for every shot', '+1 per shot', 'random'], 180)
        native.same_line()
        native.set_next_item_width(90)
        _, o['steps'] = imgui.input_int('Steps (0 = default)', int(o['steps']))
        o['steps'] = max(0, min(100, o['steps']))
        self._combo('Turbo (shots without references)', 'acceleration', list(h3workflow.ACCELERATIONS),
                    ['none', '4 steps', '8 steps'], 120)
        native.same_line()
        self._combo('Turbo (shots with references)', 'referenceAcceleration',
                    list(h3workflow.REFERENCE_ACCELERATIONS), ['none', '4 steps'], 120)

        depth_controls(o, 'wf')

        native.separator_text(tr('Shots'))
        self._combo('Start on the previous shot\'s last frame', 'chain', list(h3workflow.CHAIN), CHAIN_LABELS, 230)
        native.same_line()
        self._combo('Layout render', 'layoutUse', LAYOUT_USES, LAYOUT_LABELS, 180)
        self._combo('Panels over 15 s', 'longPanels', ['split', 'clamp'], ['chained parts', '15 s'], 160)
        native.same_line()
        self._combo('Panels under 4 s', 'shortPanels', ['trim', 'extend'], ['4 s trimmed', 'keep 4 s'], 140)
        native.same_line()
        _, o['exactDurations'] = imgui.checkbox('Trim to the panel durations', bool(o['exactDurations']))

        native.separator_text(tr('References per shot'))
        self._combo('Character identity', 'identityScope', ['panel', 'film'],
                    ['characters the panel uses', 'every character, in every segment'], 300)
        for key, label in (('includeSketches', 'Sketches'), ('includeLocations', 'Locations'),
                           ('includeObjects', 'Objects'), ('includeStyles', 'Styles'),
                           ('includeVideos', 'Reference videos'), ('videoSound', 'Sound of the reference videos'),
                           ('includeVoices', 'Character voices'), ('includeAudio', 'Reference sounds')):
            _, o[key] = imgui.checkbox(label, bool(o[key]))
            if key not in ('includeStyles', 'includeAudio'):
                native.same_line()

        native.separator_text(tr('Prompt'))
        self._combo('Prompt layout', 'promptLayout', PROMPT_LAYOUTS, PROMPT_LABELS, 400)
        native.same_line()
        _, o['includeStyle'] = imgui.checkbox('Project style', bool(o['includeStyle']))
        native.text(tr('Added to every shot'))
        _, o['globalPrompt'] = imgui.input_text_multiline('##wfglobal', o['globalPrompt'], native.ImVec2(-1, 44))
        if native.tree_node(tr('Sentences') + '###wfsentences'):
            for key, label in TEMPLATES:
                native.text(tr(label))
                _, o[key] = imgui.input_text_multiline(f'##wf{key}', o[key], native.ImVec2(-1, 38))
            if imgui.small_button('Default sentences'):
                for key, _ in TEMPLATES:
                    o[key] = h3workflow.DEFAULTS[key]
            native.tree_pop()

        self._refresh()
        native.separator()
        if self.error:
            native.text_colored(native.ImVec4(1, .4, .35, 1), self.error)
        elif self.preview:
            self._table(*self.preview)
        native.separator()
        native.begin_disabled(bool(self.error) or bool(self.editor.job and self.editor.job['state'] in ('Queued', 'Running')))
        if imgui.button('Convert to a workflow'):
            self.editor.submit('export_h3_workflow', {'project': str(self.editor.board.folder), 'options': dict(o)})
        native.end_disabled()
        native.same_line()
        if imgui.button('Open the export folder##wf'):
            folder = h3workflow.default_folder(self.editor.board)
            open_local(folder if folder.exists() else self.editor.board.folder)
        native.same_line()
        if imgui.button('Default options##wf'):
            self.options = dict(h3workflow.DEFAULTS)

    def _table(self, summary, warnings):
        native.text(f'{len(summary["shots"])} {tr("shots")} - {summary["generations"]} {tr("H3 generations")} - '
                    f'{summary["steps"]} {tr("workflow steps")} - {summary["seconds"]:.2f} s - '
                    f'{summary["width"]}x{summary["height"]}')
        for warning in warnings:
            native.text_colored(native.ImVec4(1, .7, .3, 1), warning)
        flags = native.TableFlags_.borders | native.TableFlags_.row_bg | native.TableFlags_.resizable
        columns = (('#', 26), ('Panel', 170), ('Asked', 56), ('Generated', 76), ('Kept', 56), ('Generations', 80),
                   ('First frame', 100), ('Guides', 50), ('Pictures / videos / sounds', 150), ('Control', 60),
                   ('Turbo', 0))
        if native.begin_table('h3workflowshots2', len(columns), flags):
            for label, width in columns:
                native.table_setup_column(tr(label), native.TableColumnFlags_.width_fixed if width else
                                          native.TableColumnFlags_.width_stretch, width)
            native.table_headers_row()
            for shot in summary['shots']:
                native.table_next_row()
                native.table_next_column()
                if native.selectable(f'{shot["number"]}##wfshot{shot["number"]}', shot['number'] in self.expanded,
                                     native.SelectableFlags_.span_all_columns)[0]:
                    self.expanded ^= {shot['number']}
                for value in (shot['title'], f'{shot["requestedSeconds"]:.2f} s', f'{shot["generatedSeconds"]:.2f} s',
                              f'{shot["seconds"]:.2f} s', str(shot['generations']), tr(shot['firstFrame'] or '-'),
                              str(shot['guides']), f'{shot["pictures"]} / {shot["videos"]} / {shot["sounds"]}',
                              tr(shot.get('controlSource') or '-'), tr(shot['acceleration'])):
                    native.table_next_column()
                    native.text(value)
                if shot['number'] in self.expanded:
                    native.table_next_row()
                    native.table_set_column_index(1)
                    native.text_disabled(', '.join(shot['steps']))
                    native.table_set_column_index(len(columns) - 1)
                    native.push_text_wrap_pos(0.0)
                    native.text_disabled(shot['prompt'])
                    native.pop_text_wrap_pos()
            native.end_table()
        native.text_disabled(tr('Click a row to read its prompt. H3 generates 4 to 15 s on a 5 + 17n frame grid; '
                                'each shot is trimmed back to its panel duration.'))

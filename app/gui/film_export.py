"""Window: export the storyboard as a multi-segment MiniMax H3 film (CyTools film + ComfyUI).

Every choice is an option saved in the project; the table under them shows, live, the
segment windows, overlaps, real durations (H3's 5 + 17n frame grid), pictures and the
exact prompt of every segment before anything is written.
"""
import json
import sys
import time

from imgui_bundle import imgui as native

from ui_common import imgui, tr
from gui.common import dialogs, open_local
from storyboard import h3film
from storyboard.model import StoryboardError

TEMPLATES = [('continuityText', 'Carried opening frames ({frames}, {seconds})'),
             ('identityText', 'Character identity ({n}, {name}, {description})'),
             ('layoutText', 'Layout render ({n})'), ('sketchText', 'Sketch ({n})'), ('firstText', 'First frame ({n})'),
             ('lastText', 'Last frame ({n})'), ('keyframeText', 'Keyframe ({n}, {time})'),
             ('referenceText', 'Shot reference ({n})'), ('locationText', 'Location ({n}, {name}, {description})'),
             ('objectText', 'Object ({n}, {name}, {description})'), ('styleText', 'Style ({n}, {name}, {description})'),
             ('videoText', 'Reference video ({n}, {name}, {description})'),
             ('voiceText', 'Character voice ({n}, {name}, {description})'),
             ('audioText', 'Reference sound ({n}, {name}, {description})'),
             ('videoSoundText', 'Sound of a reference video ({n}, {video}, {name})')]
OVERLAP_LABELS = {0: '0 - independent segments', 1: '1 frame', 5: '5 frames (0.2 s)', 22: '22 frames (0.9 s)',
                  39: '39 frames (1.6 s)', 56: '56 frames (2.3 s)', 73: '73 frames (3.0 s)'}


def depth_controls(o, key_suffix=''):
    """Depth control (Fun ControlNet) of the panels staged in 3D; shared by both export windows."""
    from storyboard import depthcontrol
    levels = list(depthcontrol.LEVELS)
    labels = ['off', 'indicative (0.35, blurred)', 'guided (0.6)', 'strict (1.0, sharp)', 'custom']
    o.setdefault('controlSource', 'auto')
    native.set_next_item_width(240)
    changed, index = native.combo(tr('Depth control of 3D panels') + '##depth' + key_suffix,
                                  levels.index(o['depthControl']), [tr(x) for x in labels])
    if changed:
        o['depthControl'] = levels[index]
    if o['depthControl'] != 'off':
        native.same_line()
        sources = list(depthcontrol.SOURCES)
        source_labels = ['auto (pose when a character is in frame)', 'depth of the set', 'pose of the characters',
                         'pose over depth (experimental)']
        native.set_next_item_width(280)
        changed, index = native.combo(tr('Control') + '##src' + key_suffix, sources.index(o['controlSource']),
                                      [tr(x) for x in source_labels])
        if changed:
            o['controlSource'] = sources[index]
        if o['controlSource'] != 'depth':
            native.same_line()
            _, o['poseHands'] = imgui.checkbox('Hands in the pose##ph' + key_suffix, bool(o.get('poseHands', True)))
            native.same_line()
            _, o['poseFeet'] = imgui.checkbox('Feet in the pose##pf' + key_suffix, bool(o.get('poseFeet', True)))
    if o['depthControl'] == 'custom':
        native.same_line()
        native.set_next_item_width(110)
        _, o['controlStrength'] = imgui.slider_float('Strength##cs' + key_suffix, float(o['controlStrength']), 0.05, 2.0, '%.2f')
        native.same_line()
        native.set_next_item_width(110)
        _, o['controlEnd'] = imgui.slider_float('Until (share of the steps)##ce' + key_suffix, float(o['controlEnd']),
                                                0.05, 1.0, '%.2f')
        native.same_line()
        blurs = list(depthcontrol.BLUR)
        native.set_next_item_width(110)
        changed, index = native.combo(tr('Blur') + '##cb' + key_suffix, blurs.index(o['controlBlur']), [tr(b) for b in blurs])
        if changed:
            o['controlBlur'] = blurs[index]
    native.push_text_wrap_pos(0.0)
    native.text_disabled(tr('A control video along the camera move of each panel staged in 3D guides the generation '
                            '(Fun ControlNet Union): the depth of the set, or the pose of the characters (OpenPose '
                            'skeletons, with their poses and moves). The blur applies to the depth only.'))
    native.pop_text_wrap_pos()


def films_folder():
    """The folder the films are exported into (one folder per film), kept in the UI preferences;
    empty = inside each project."""
    from ui_common import preferences
    return str(preferences.values.get('h3film_films_folder') or '')


def set_films_folder(value):
    from ui_common import preferences
    preferences.values['h3film_films_folder'] = str(value or '')
    preferences.save()


class FilmExportWindow:
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
        board = self.editor.board
        self.options = h3film.options_for(board)
        self.open, self.key = True, None
        if '--ui-test-film' in sys.argv:
            self.expanded = {2}

    def _refresh(self):
        board = self.editor.board
        key = json.dumps([self.options, board.doc], sort_keys=True, default=str)
        if key == self.key and time.monotonic() - self.checked_at < 2.0:
            return
        self.key, self.checked_at = key, time.monotonic()
        try:
            film, _, warnings = h3film.build(board, self.options, preview=True)
            self.preview, self.error = (film, warnings), ''
        except StoryboardError as exc:
            self.preview, self.error = None, str(exc)

    def draw(self):
        if not self.open or not self.editor.board:
            return
        native.set_next_window_size(native.ImVec2(1180, 820), native.Cond_.first_use_ever)
        visible, self.open = native.begin(tr('MiniMax H3 film') + '###h3film', self.open)
        if visible:
            try:
                self._body()
            finally:
                native.end()
        else:
            native.end()

    def _body(self):
        o = self.options
        native.text_wrapped(tr('One H3 segment per panel. Each segment starts a few frames before the previous one ends: '
                               'those frames carry places, characters, light and sound across the cut, then are '
                               'removed. The same film runs in CyTools_MiniMaxH3 (Colab) or in ComfyUI.'))
        native.separator_text(tr('Picture'))
        edges = list(h3film.SHORT_EDGES)
        native.set_next_item_width(120)
        index = edges.index(o['shortEdge']) if o['shortEdge'] in edges else edges.index(544)
        changed, index = native.combo(tr('Short edge') + '##edge', index, [f'{e} px' for e in edges])
        if changed:
            o['shortEdge'], o['width'], o['height'] = edges[index], 0, 0
        native.same_line()
        native.set_next_item_width(90)
        _, o['width'] = imgui.input_int('Width (0 = auto)', int(o['width']), 32)
        native.same_line()
        native.set_next_item_width(90)
        _, o['height'] = imgui.input_int('Height', int(o['height']), 32)
        o['width'], o['height'] = max(0, o['width']), max(0, o['height'])

        native.separator_text(tr('Continuity between segments'))
        overlaps = list(h3film.OVERLAPS)
        native.set_next_item_width(220)
        changed, index = native.combo(tr('Overlap') + '##overlap', overlaps.index(int(o['overlapFrames'])),
                                      [tr(OVERLAP_LABELS[x]) for x in overlaps])
        if changed:
            o['overlapFrames'] = overlaps[index]
        native.same_line()
        _, o['overlapOnCuts'] = imgui.checkbox('Across cuts', bool(o['overlapOnCuts']))
        native.same_line()
        _, o['overlapOnFades'] = imgui.checkbox('Across fades to black', bool(o['overlapOnFades']))
        native.text_disabled(tr('Crossfades always carry continuity. Without overlap, segments are generated independently.'))

        native.separator_text(tr('Pictures per segment (9 at most)'))
        scopes = ['panel', 'film']
        native.set_next_item_width(330)
        changed, index = native.combo(tr('Character identity') + '##scope', scopes.index(o['identityScope']),
                                      [tr('characters the panel uses'), tr('every character, in every segment')])
        if changed:
            o['identityScope'] = scopes[index]
        native.same_line()
        shots = ['main', 'all', 'none']
        native.set_next_item_width(260)
        changed, index = native.combo(tr('Shot pictures') + '##shots', shots.index(o['shotPictures']),
                                      [tr('main (layout render first)'), tr('all the panel images'), tr('none')])
        if changed:
            o['shotPictures'] = shots[index]
        _, o['includeLocations'] = imgui.checkbox('Locations', bool(o['includeLocations']))
        native.same_line()
        _, o['includeObjects'] = imgui.checkbox('Objects', bool(o['includeObjects']))
        native.same_line()
        _, o['includeStyles'] = imgui.checkbox('Styles', bool(o['includeStyles']))

        native.separator_text(tr('Videos and sounds per segment (3 of each, 12 references in all)'))
        _, o['includeVideos'] = imgui.checkbox('Reference videos', bool(o['includeVideos']))
        native.same_line()
        _, o['includeVoices'] = imgui.checkbox('Character voices', bool(o['includeVoices']))
        native.same_line()
        _, o['includeAudio'] = imgui.checkbox('Reference sounds', bool(o['includeAudio']))
        native.same_line()
        _, o['videoSound'] = imgui.checkbox('Sound of the reference videos', bool(o['videoSound']))
        native.set_next_item_width(160)
        _, o['maxReferenceSeconds'] = imgui.slider_float('Longest reference (s)', float(o['maxReferenceSeconds']),
                                                         2.0, 15.0, '%.1f')
        native.text_disabled(tr('Videos: library items of kind video used by the panel. Voices: an audio file in a '
                                "character's files. Sounds: library items of kind audio used by the panel."))

        native.separator_text(tr('Prompt'))
        _, o['includeStyle'] = imgui.checkbox('Project style', bool(o['includeStyle']))
        native.same_line()
        _, o['includeDescription'] = imgui.checkbox('Project description', bool(o['includeDescription']))
        native.same_line()
        _, o['includeSound'] = imgui.checkbox('Sound and music lines', bool(o['includeSound']))
        native.text(tr('Added to every segment'))
        _, o['globalPrompt'] = imgui.input_text_multiline('##global', o['globalPrompt'], native.ImVec2(-1, 54))
        native.text(tr('Note about the pictures'))
        _, o['referenceNote'] = imgui.input_text_multiline('##note', o['referenceNote'], native.ImVec2(-1, 40))
        if native.tree_node(tr('Sentences') + '###sentences'):
            for key, label in TEMPLATES:
                native.text(tr(label))
                _, o[key] = imgui.input_text_multiline(f'##{key}', o[key], native.ImVec2(-1, 38))
            if imgui.small_button('Default sentences'):
                for key, _ in TEMPLATES:
                    o[key] = h3film.DEFAULTS[key]
            native.tree_pop()

        native.separator_text(tr('Sampling'))
        _, o['secondPass'] = imgui.checkbox('Two-stage sampling (latent upscaler)', bool(o['secondPass']))
        if o['secondPass']:
            native.same_line()
            native.set_next_item_width(100)
            _, o['secondPassHighSteps'] = imgui.slider_int('High-resolution steps', int(o['secondPassHighSteps']), 1, 8)
            native.set_next_item_width(-1)
            _, o['secondPassModel'] = imgui.input_text('##upscaler', o['secondPassModel'])
        _, o['generatedAudio'] = imgui.checkbox('Generate sound', bool(o['generatedAudio']))
        depth_controls(o, 'film')
        if o['depthControl'] != 'off':
            native.set_next_item_width(-260)
            _, o['controlPatchModel'] = imgui.input_text('ControlNet file (ComfyUI workflow)', o['controlPatchModel'])

        native.separator_text(tr('Where the film goes'))
        films = films_folder()
        target = h3film.films_folder_target(self.editor.board, films) if films else h3film.default_folder(self.editor.board)
        native.text(tr('Films folder') + ': ' + (films or tr('the project (exports/h3_film)')))
        native.same_line()
        if imgui.small_button('Choose...'):
            dialogs.folder('films', 'Films folder (for example ComfyUI/input/cytools_film on your Drive)', films)
        chosen = dialogs.result('films')
        if chosen:
            set_films_folder(chosen[0])
        if films:
            native.same_line()
            if imgui.small_button('Back to the project folder'):
                set_films_folder('')
        native.text_disabled(tr('This film') + ': ' + str(target) + '  -  ' + tr('in the ComfyUI workflow') + ': '
                             + h3film.comfy_input_folder(target) + '/film.json')

        self._refresh()
        native.separator()
        if self.error:
            native.text_colored(native.ImVec4(1, .4, .35, 1), self.error)
        elif self.preview:
            self._table(*self.preview)
        native.separator()
        native.begin_disabled(bool(self.error) or bool(self.editor.job and self.editor.job['state'] in ('Queued', 'Running')))
        if imgui.button('Export the film'):
            params = {'project': str(self.editor.board.folder), 'options': dict(o)}
            if films:
                params['folder'] = str(target)
            self.editor.submit('export_h3_film', params)
        native.end_disabled()
        native.same_line()
        if imgui.button('Open the export folder'):
            films = films_folder()
            folder = h3film.films_folder_target(self.editor.board, films) if films else h3film.default_folder(self.editor.board)
            open_local(folder if folder.exists() else self.editor.board.folder)
        native.same_line()
        if imgui.button('Default options'):
            self.options = dict(h3film.DEFAULTS)

    def _table(self, film, warnings):
        native.text(f'{len(film["segments"])} {tr("segments")} - {film["seconds"]:.2f} s ({film["frames"]} '
                    f'{tr("frames")}) - {film["width"]}x{film["height"]}')
        for warning in warnings:
            native.text_colored(native.ImVec4(1, .7, .3, 1), warning)
        flags = native.TableFlags_.borders | native.TableFlags_.row_bg | native.TableFlags_.resizable
        if native.begin_table('h3filmsegments2', 10, flags):
            for label, width in (('#', 26), ('Panel', 180), ('Asked', 60), ('Real', 60), ('Frames', 110),
                                 ('Overlap', 60), ('Pictures', 60), ('Videos', 55), ('Sounds', 55), ('Control', 0)):
                native.table_setup_column(tr(label), native.TableColumnFlags_.width_fixed if width else
                                          native.TableColumnFlags_.width_stretch, width)
            native.table_headers_row()
            for segment in film['segments']:
                native.table_next_row()
                native.table_next_column()
                opened = native.selectable(f'{segment["number"]}##seg{segment["number"]}',
                                           segment['number'] in self.expanded,
                                           native.SelectableFlags_.span_all_columns)[0]
                if opened:
                    self.expanded ^= {segment['number']}
                native.table_next_column()
                native.text(segment['title'])
                native.table_next_column()
                native.text(f'{segment["requestedSeconds"]:.2f} s')
                native.table_next_column()
                real = segment['seconds']
                colour = native.ImVec4(1, .75, .35, 1) if abs(real - segment['requestedSeconds']) > 0.3 else \
                    native.ImVec4(.8, .8, .8, 1)
                native.text_colored(colour, f'{real:.2f} s')
                native.table_next_column()
                native.text(f'{segment["startFrame"]}-{segment["endFrame"]}')
                native.table_next_column()
                native.text(str(segment['overlap']))
                native.table_next_column()
                native.text(str(len(segment['pictures'])))
                native.table_next_column()
                native.text(str(len(segment.get('videos') or [])))
                native.table_next_column()
                native.text(str(len(segment.get('audios') or [])))
                native.table_next_column()
                native.text(tr(segment.get('controlSource') or '-'))
                if segment['number'] in self.expanded:
                    native.table_next_row()
                    native.table_set_column_index(1)
                    native.push_text_wrap_pos(0.0)
                    native.text_disabled(', '.join(segment['pictures'] + segment.get('videos', []) +
                                                   segment.get('audios', [])) or tr('no picture'))
                    native.pop_text_wrap_pos()
                    native.table_set_column_index(9)
                    native.push_text_wrap_pos(0.0)
                    native.text_disabled(segment['prompt'])
                    native.pop_text_wrap_pos()
            native.end_table()
        native.text_disabled(tr('Click a row to read its prompt. Real durations follow the 5 + 17n frame grid of H3.'))

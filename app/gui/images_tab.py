"""Images tab: generate reference pictures in the application (characters, places, shots, free
prompts), keep the good ones in the project, install the engine and the models.

The tab only builds requests and shows results; pictures are rendered by the `generate_images`
operation on the persistent image engine, the same one the CLI and MCP use.
"""
import copy
import sys
import time
import webbrowser
from pathlib import Path

from imgui_bundle import imgui as native

import cyui
from ui_common import imgui, preferences, tr
from gui.common import IMAGE_FILTER, dialogs, image, open_local
from gui.jobs import Jobs
from storyboard import imagegen, model

RECIPES = [('character', 'Character'), ('location', 'Place'), ('panel', 'Shot'), ('free', 'Free prompt')]
STATE_COLOUR = {'Installed': (0.5, 0.9, 0.5, 1.0), 'Downloading': (0.95, 0.8, 0.3, 1.0), 'Verifying': (0.95, 0.8, 0.3, 1.0),
                'Partial': (0.95, 0.7, 0.3, 1.0), 'Interrupted': (0.95, 0.6, 0.3, 1.0), 'Failed': (1.0, 0.45, 0.4, 1.0),
                'AccessRequired': (1.0, 0.55, 0.4, 1.0), 'LicenseAcceptanceRequired': (0.95, 0.7, 0.3, 1.0),
                'Cancelled': (0.8, 0.8, 0.8, 1.0), 'NotInstalled': (0.7, 0.7, 0.75, 1.0)}
TEXT_LABELS = {'characterText': 'Character from its pictures ({pictures}, {description}, {view}, {name})',
               'characterFromText': 'Character from its description ({name}, {description}, {view})',
               'locationText': 'Place from its pictures ({pictures}, {description}, {view}, {name})',
               'locationFromText': 'Place from its description ({name}, {description}, {view})',
               'locationWithCharacterText': 'Character in a place ({character}, {place}, {description}, {view})',
               'panelText': 'Shot ({framing}, {people}, {place}, {text})',
               'panelFramingText': 'Shot: layout picture ({picture})',
               'panelCharacterText': 'Shot: character picture ({picture}, {name}, {description})',
               'panelExtrasText': 'Shot: the other mannequins are a character ({name}, {picture}, {count})',
               'panelUnknownText': 'Shot: the other mannequins have no reference ({count})',
               'panelCrowdText': 'Shot: the other figures are a character, structure guide ({name}, {picture}, {count})',
               'panelLocationText': 'Shot: place picture ({picture}, {name}, {description})'}


def gb(value):
    return f'{(value or 0) / 1e9:.1f} GB'


def note(text):
    """A dimmed explanation that wraps at the edge of its panel."""
    native.push_text_wrap_pos(0.0)
    native.text_disabled(text)
    native.pop_text_wrap_pos()


class ImagesTab:
    def __init__(self, editor):
        self.editor = editor
        self.jobs = Jobs(editor.runtime, editor.actor, editor.session)
        self.recipe = 0
        self.item = {'character': '', 'location': ''}
        self.with_character = ''
        self.extras = ''
        self.extra = ''
        self.prompt = ''
        self.references = []
        self.options = None
        self.board_id = None
        self.results = []          # [{picture..., 'kept': asset or ''}]
        self.plan = None           # (requests, error)
        self.plan_key = None
        self.status = None
        self.status_at = 0.0
        self.limit = imagegen.MAX_REFERENCES
        self.lora_names = []
        self.scroll_pictures = False
        self.control = False
        self.message = ''
        self.message_tone = 'warning'
        self.test = '--ui-test-images' in sys.argv

    # ------------------------------------------------------------------ state
    def _options(self):
        board = self.editor.board
        if self.options is None or self.board_id != board.doc['id']:
            self.options = imagegen.options_for(board)
            self.board_id = board.doc['id']
            self.results, self.plan_key = [], None
        return self.options

    def _items(self, kind):
        return [item for item in self.editor.board.doc['library'] if item['kind'] == kind]

    def _arguments(self):
        recipe = RECIPES[self.recipe][0]
        if recipe == 'character':
            return recipe, {'item': self.item['character'], 'extra': self.extra}
        if recipe == 'location':
            return recipe, {'item': self.item['location'], 'character': self.with_character, 'extra': self.extra}
        if recipe == 'panel':
            return recipe, {'panel': self.editor.selected or '', 'extra': self.extra, 'extras': self.extras}
        return recipe, {'prompt': self.prompt, 'references': list(self.references)}

    def _refresh_plan(self):
        recipe, arguments = self._arguments()
        key = repr((recipe, arguments, {k: v for k, v in self.options.items() if k not in ('seed', 'randomSeed')},
                    self.editor.last_state if recipe != 'free' else ''))
        if key == self.plan_key:
            return
        self.plan_key = key
        try:
            from storyboard import imageengine
            options = dict(self.options, count=1, randomSeed=False)
            self.limit, token = imageengine.reference_rules(options)
            self.control = imageengine.control_available(options)
            self.plan = (imagegen.plan(self.editor.board, recipe, imagegen.options_for(self.editor.board, options),
                                       self.limit, token, self.control, **arguments), '')
        except (model.StoryboardError, KeyError) as exc:
            self.plan = ([], str(exc) if isinstance(exc, model.StoryboardError) else tr('Choose what to generate.'))

    def _refresh_status(self, force=False):
        busy = self.jobs.is_running()
        if force or time.monotonic() - self.status_at > (1.0 if busy else 5.0):
            self.status_at = time.monotonic()
            try:
                from storyboard import engines, imageengine, imagemodels
                engine = getattr(self.editor.runtime, 'image_engine', None)
                self.status = {'engine': engines.status(imageengine.ENGINE), 'models': imagemodels.status_all(),
                               **(engine.status() if engine else {'worker': {}, 'last': {}})}
            except Exception as exc:
                self.message = str(exc)

    # ------------------------------------------------------------------ actions
    def generate(self):
        recipe, arguments = self._arguments()
        parameters = {'project': str(self.editor.board.folder), 'recipe': recipe, 'options': copy.deepcopy(self.options),
                      **arguments}
        # The window owns the project while it is open: it remembers the options itself. A job that saved
        # the project when it ends would write back the state it read at its start and undo what was kept
        # in the meantime.
        self.editor.board.doc['settings']['imagegen'] = copy.deepcopy(self.options)
        self.editor.save()
        self.jobs.submit('generate_images', parameters, self._finished, tr('Pictures'))

    def _finished(self, job):
        if job['state'] != 'Completed':
            return
        new = [dict(picture, kept='') for picture in job['outputs']['pictures']]
        self.results = new + self.results
        self._refresh_status(force=True)

    def keep(self, result):
        board = self.editor.board
        try:
            result['kept'] = imagegen.keep(board, result['file'], result, result.get('engine'))
            self.scroll_pictures = True        # show the picture that has just joined the item
            target = result.get('target') or {}
            self.message_tone = 'success'
            if target.get('kind') == 'library':
                self.message = tr('Added to the pictures of') + ' ' + board.library_item(target['item'])['name'] + '.'
            elif target.get('kind') == 'panel':
                self.message = tr('Set as the first image of the shot') + ' « ' + board.find(target['panel'])[2]['title'] + ' ».'
        except (model.StoryboardError, OSError) as exc:
            self.message = str(exc)

    # ------------------------------------------------------------------ drawing
    def draw(self):
        board = self.editor.board
        if not board:
            cyui.empty_state(tr('No storyboard open'), tr('Create one (+) or open one from the toolbar.'),
                             cyui.icon.document)
            return
        o = self._options()
        self.jobs.poll()
        self._refresh_status()
        if self.message:
            cyui.notify(self.message, self.message_tone)
            self.message, self.message_tone = '', 'warning'
        if self.jobs.error:
            cyui.notify(self.jobs.error[:400], 'error', 8.0)
            self.jobs.error = ''
        avail = native.get_content_region_avail()
        left, actions = cyui.dp(580), cyui.dp(118)
        gap = native.get_style().item_spacing.y
        native.begin_group()
        native.begin_child('img-left', native.ImVec2(left, avail.y - actions - gap), native.ChildFlags_.borders)
        self._request_panel(o)
        native.end_child()
        native.begin_child('img-actions', native.ImVec2(left, 0), native.ChildFlags_.borders)
        self._actions(o)
        native.end_child()
        native.end_group()
        native.same_line()
        native.begin_child('img-right', native.ImVec2(0, avail.y), native.ChildFlags_.borders)
        self._engine_line()
        self._results()
        native.end_child()

    def _request_panel(self, o):
        board = self.editor.board
        cyui.panel_header(tr('Pictures'), tr('Generate the pictures MiniMax H3 needs, from your reference pictures or from a '
                                             'text. The pictures you keep go into the project.'))
        cyui.space(6)
        changed, self.recipe = cyui.segmented('##recipe', [tr(label) for _, label in RECIPES], self.recipe, -1)
        cyui.space(6)
        recipe = RECIPES[self.recipe][0]
        if recipe in ('character', 'location'):
            self._item_combo(recipe)
            item = next((i for i in self._items(recipe) if i['id'] == self.item[recipe]), None)
            if item:
                used = min(self.limit, imagegen.CHARACTER_PICTURES)
                if imagegen.item_pictures(board, item, 1):
                    self._item_pictures(item, used)
                else:
                    cyui.callout('info', tr('No picture yet: the views are generated from the description alone.'))
                if cyui.begin_properties('##itemprops', 110):
                    cyui.property(tr('Description'))
                    _, item['description'] = imgui.input_text_multiline('##itemdesc', item.get('description', ''),
                                                                        native.ImVec2(-1, cyui.dp(54)))
                    if recipe == 'location':
                        characters = self._items('character')
                        names = [tr('nobody (empty place)')] + [c['name'] for c in characters]
                        ids = [''] + [c['id'] for c in characters]
                        cyui.property(tr('Character in the place'))
                        index = ids.index(self.with_character) if self.with_character in ids else 0
                        changed, index = native.combo('##withchar', index, names)
                        if changed:
                            self.with_character = ids[index]
                    cyui.property(tr('Added to every picture'))
                    _, self.extra = cyui.text_field('##extra', self.extra, tr('e.g. wet armour, night'), -1)
                    cyui.end_properties()
                if cyui.icon_text_button(cyui.icon.add, tr('Add reference pictures...'), 'ghost'):
                    dialogs.open('imgrefs' + item['id'], 'Reference pictures', IMAGE_FILTER, multiple=True)
                for path in dialogs.result('imgrefs' + item['id']) or []:
                    relative = self.editor.act(board.import_asset, path)
                    if relative:
                        item.setdefault('files', []).append(relative)
            self._views(o, 'characterViews' if recipe == 'character' else 'locationViews')
        elif recipe == 'panel':
            try:
                _, _, panel = board.find(self.editor.selected) if self.editor.selected else (None, None, None)
            except model.StoryboardError:
                panel = None
            panels = board.panels()
            names = [f'{n + 1}. {p["title"]}' for n, p in enumerate(panels)]
            index = next((n for n, p in enumerate(panels) if p['id'] == self.editor.selected), 0)
            native.set_next_item_width(-1)
            changed, index = native.combo('##imgpanel', index, names)
            if changed and panels:
                self.editor.selected = panels[index]['id']
            cyui.text_faint(tr('The kept picture becomes the first image of the shot.'))
            cyui.space(4)
            if cyui.begin_properties('##shotprops', 150):
                guides = list(imagegen.GUIDES)
                labels = ['automatic (structure guide when its model is installed)', 'structure guide (depth or pose, ControlNet)',
                          'staging picture', 'both', 'none (text and references only)']
                cyui.property(tr('Framing from the 3D staging'),
                              tr('Structure guide: the depth or the pose of the staging guides the picture, the model '
                                 'never sees a mannequin. Staging picture: the mannequin render is sent as a picture.'))
                changed, index = native.combo('##guide', guides.index(o['panelGuide']), [tr(x) for x in labels])
                if changed:
                    o['panelGuide'] = guides[index]
                if o['panelGuide'] in ('auto', 'control', 'both'):
                    sources = list(imagegen.CONTROL_SOURCES)
                    cyui.property(tr('Guide'))
                    changed, index = cyui.segmented('##ctlsrc', [tr(x) for x in sources], sources.index(o['panelControlSource']), -1)
                    if changed:
                        o['panelControlSource'] = sources[index]
                    cyui.property(tr('Strength##imgctl').split('##')[0])
                    _, o['panelControlStrength'] = cyui.slider_bar('##ctlstrength', float(o['panelControlStrength']), 0.05, 2.0,
                                                                   '%.2f', -1)
                    cyui.property(tr('Until (share of the steps)##imgctl').split('##')[0])
                    _, o['panelControlEnd'] = cyui.slider_bar('##ctlend', float(o['panelControlEnd']), 0.05, 1.0, '%.2f', -1)
                if panel is not None:
                    staged, unknown = imagegen.stage_figures(board, panel)
                    if unknown:
                        characters = [c for c in self._items('character') if imagegen.item_pictures(board, c, 1)]
                        ids = [''] + [c['id'] for c in characters]
                        names = [tr('what the text describes')] + [c['name'] for c in characters]
                        cyui.property(f'{unknown} ' + tr('mannequin(s) without a reference are'))
                        index = ids.index(self.extras) if self.extras in ids else 0
                        changed, index = native.combo('##extras', index, names)
                        if changed:
                            self.extras = ids[index]
                cyui.property(tr('Pictures per character'))
                _, o['panelCharacterPictures'] = native.slider_int('##pcp', int(o['panelCharacterPictures']), 1, 6)
                self._format_property(o, 'panelFormat')
                cyui.property(tr('Added to every picture'))
                _, self.extra = cyui.text_field('##extra', self.extra, '', -1)
                cyui.end_properties()
            if o['panelGuide'] in ('auto', 'control', 'both') and not self.control:
                cyui.callout('warning', tr('The ControlNet of the model is not installed (Installation): the staging '
                                           'picture is used instead.') if o['panelGuide'] == 'auto' else
                             tr('The ControlNet of the model is not installed (Installation).'))
        else:
            cyui.section_title(tr('Prompt'))
            _, self.prompt = imgui.input_text_multiline('##freeprompt', self.prompt, native.ImVec2(-1, cyui.dp(110)))
            cyui.section_title(tr('Reference pictures (none: from the text alone)') + f'  -  {self.limit} max')
            for position, path in enumerate(list(self.references)):
                image(path, cyui.dp(90), cyui.dp(90), 256)
                native.same_line()
                if cyui.icon_button(cyui.icon.close, tr('Remove') + f'##ref{position}'):
                    self.references.pop(position)
                native.same_line()
            native.new_line()
            if len(self.references) < self.limit and cyui.icon_text_button(cyui.icon.add, tr('Add pictures...'), 'ghost'):
                dialogs.open('freerefs', 'Reference pictures', IMAGE_FILTER, multiple=True)
            for path in dialogs.result('freerefs') or []:
                if len(self.references) < self.limit:
                    self.references.append(path)
            if cyui.begin_properties('##freeprops', 110):
                self._format_property(o, 'freeFormat')
                cyui.end_properties()

        cyui.space(4)
        if cyui.begin_section(tr('Generation') + '###sec-gen'):
            if cyui.begin_properties('##genprops', 170):
                cyui.property(tr('Pictures per view'))
                _, o['count'] = native.slider_int('##count', int(o['count']), 1, 8)
                cyui.property(tr('Size'))
                sizes = list(imagegen.MEGAPIXELS)
                index = sizes.index(o['megapixels']) if o['megapixels'] in sizes else 2
                changed, index = native.combo('##mp', index, [f'{m:g} MP' for m in sizes])
                if changed:
                    o['megapixels'] = sizes[index]
                cyui.property(tr('Random seed'))
                _, o['randomSeed'] = cyui.toggle_switch('##randomseed', bool(o['randomSeed']))
                if not o['randomSeed']:
                    cyui.property(tr('Seed'))
                    _, o['seed'] = native.input_int('##seed', int(o['seed']), 1)
                cyui.property(tr('Fast mode (few steps)'), tr('Uses the few-step LoRA of the model when it has one.'))
                _, o['fast'] = cyui.toggle_switch('##fast', bool(o['fast']))
                cyui.property(tr('Steps (0 = auto)'))
                _, o['steps'] = native.slider_int('##steps', int(o['steps']), 0, 50)
                cyui.property(tr('Guidance (0 = auto)'))
                _, o['guidance'] = cyui.slider_bar('##guidance', float(o['guidance']), 0.0, 10.0, '%.1f', -1)
                cyui.property(tr('Project style in the prompt'))
                _, o['includeStyle'] = cyui.toggle_switch('##style', bool(o['includeStyle']))
                cyui.property(tr('Negative prompt'))
                _, o['negative'] = cyui.text_field('##negative', o['negative'], '', -1)
                self._model_properties(o)
                cyui.property(tr('Keep the model loaded (minutes, 0 = until closed)'))
                _, o['keepLoadedMinutes'] = native.slider_int('##keep', int(o['keepLoadedMinutes']), 0, 240)
                cyui.end_properties()
            cyui.end_section()
        if cyui.begin_section('LoRA' + '###sec-lora', False):
            self._loras(o)
            cyui.end_section()
        requests = self.plan[0] if self.plan else []
        if requests and cyui.begin_section(tr('What will be asked') + f' ({len(requests)})###imgplan', False):
            for request in requests:
                cyui.text_dim(f'{request["label"]}  -  {request["width"]}x{request["height"]}  -  '
                              f'{len(request["references"])} {tr("reference(s)")}')
                native.push_text_wrap_pos(0.0)
                cyui.text_faint(request['prompt'])
                native.pop_text_wrap_pos()
                cyui.space(4)
            cyui.end_section()
        if cyui.begin_section(tr('Sentences') + '###imgsentences', False):
            for key in imagegen.TEXTS:
                cyui.text_dim(tr(TEXT_LABELS[key]))
                _, o[key] = imgui.input_text_multiline(f'##{key}', o[key], native.ImVec2(-1, cyui.dp(40)))
            if cyui.ghost_button(tr('Default sentences##img')):
                for key in imagegen.TEXTS:
                    o[key] = imagegen.DEFAULTS[key]
            cyui.end_section()

    def _actions(self, o):
        board = self.editor.board
        self._refresh_plan()
        requests, error = self.plan
        running = self.jobs.running('generate_images')
        if error:
            cyui.callout('warning', error)
        with cyui.scoped_disabled(bool(error) or bool(running)):
            label = (cyui.icon.photo + '  ' if cyui.icons_available() else '') + tr('Generate')
            if cyui.primary_button(label + '###generate', (cyui.dp(170), native.get_frame_height() + cyui.dp(6))) or \
                    (self.test and self.editor.frames == 12 and not error):
                self.generate()
        native.same_line()
        with cyui.scoped_disabled(bool(error)):
            if cyui.icon_text_button(cyui.icon.export_file, tr('ComfyUI workflows...'), 'outline',
                                     (0, native.get_frame_height() + cyui.dp(6))):
                recipe, arguments = self._arguments()
                self.editor.save()
                self.jobs.submit('export_image_workflows', {'project': str(board.folder), 'recipe': recipe,
                                                            'options': copy.deepcopy(o), **arguments},
                                 lambda job: job['state'] == 'Completed' and open_local(job['outputs']['folder']),
                                 tr('ComfyUI workflows'))
            cyui.tooltip(tr('The same graph as a ComfyUI workflow, with its reference pictures'))
        if requests:
            native.same_line()
            native.align_text_to_frame_padding()
            cyui.badge(f'{len(requests) * int(o["count"])} {tr("picture(s)")}', 'accent')
        for job in running:
            progress = job.get('progress') or {}
            cyui.progress_bar(float(progress.get('percent') or 0) / 100.0, (-native.get_frame_height() - cyui.dp(8), 0),
                              self.jobs.progress_text(job)[:90])
            native.same_line()
            if cyui.icon_button(cyui.icon.stop, tr('Cancel') + ' (' + tr('the model stays loaded') + ')'):
                self.jobs.cancel(job['jobId'])

    def _item_pictures(self, item, used):
        """Every picture of the item, the references first: the first `used` ones are sent to the model
        when its views are generated. A picture can be put first, or taken out of the item."""
        board = self.editor.board
        p = cyui.palette()
        files = [f for f in item.get('files') or [] if (board.folder / f).suffix.lower() in model.IMAGE_SUFFIXES
                 and (board.folder / f).is_file()]
        generations = board.doc.get('generations') or {}
        cyui.section_title(f'{len(files)} ' + tr('picture(s). The first ones are the references sent to the model')
                           + f' ({min(used, len(files))})')
        cyui.help_marker(tr('"First" puts a picture at the head of the list; kept pictures are added at the end.'))
        size = cyui.dp(92)
        columns = max(1, int(native.get_content_region_avail().x // (size + cyui.dp(10))))
        rows = min(3, -(-len(files) // columns))
        with cyui.scoped_color(native.Col_.child_bg, p.bg0):
            native.begin_child('itempics' + item['id'], native.ImVec2(0, rows * (size + cyui.dp(52)) + cyui.dp(10)),
                               native.ChildFlags_.borders)
        for index, relative in enumerate(list(files)):
            if index % columns:
                native.same_line()
            native.begin_group()
            native.push_id(f'pic{index}')
            corner = native.get_cursor_screen_pos()
            drawn = image(board.folder / relative, size, size, 256)
            if not drawn[0]:
                native.dummy(native.ImVec2(size, size))
            if index < used:
                native.get_window_draw_list().add_rect(corner, native.ImVec2(corner.x + drawn[0], corner.y + drawn[1]),
                                                       p.accent, cyui.dp(3), cyui.dp(1.5))
            key = (generations.get(Path(relative).name) or {}).get('key', '')
            with cyui.scoped_font(None, 0.86):
                if index < used:
                    cyui.text_coloured(p.accent, tr('reference') + f' {index + 1}')
                else:
                    cyui.text_faint((tr(key) if key else tr('picture'))[:14])
            if index and cyui.icon_button(cyui.icon.chevron_left, tr('First') + ' - ' + tr('make it a reference')):
                item['files'].remove(relative)
                item['files'].insert(0, relative)
            if index:
                native.same_line(0, cyui.dp(2))
            if cyui.icon_button(cyui.icon.close, tr('Take this picture out of the item (the file stays in the project)')):
                item['files'].remove(relative)
            native.pop_id()
            native.end_group()
        if self.scroll_pictures:
            native.set_scroll_here_y(1.0)
            self.scroll_pictures = False
        native.end_child()

    def _item_combo(self, kind):
        items = self._items(kind)
        if not items:
            cyui.callout('info', tr('The library has none yet: add one in the Storyboard tab (References), with a description.'))
            return
        ids = [i['id'] for i in items]
        if self.item[kind] not in ids:
            self.item[kind] = ids[0]
        native.set_next_item_width(-1)
        changed, index = native.combo(f'##imgitem{kind}', ids.index(self.item[kind]), [i['name'] for i in items])
        if changed:
            self.item[kind] = ids[index]

    def _views(self, o, name):
        on = sum(1 for view in o[name] if view.get('on', True))
        if not cyui.begin_section(tr('Views') + f' ({on}/{len(o[name])})###views-{name}'):
            return
        for index, view in enumerate(o[name]):
            native.push_id(f'{name}{index}')
            _, view['on'] = native.checkbox('##on', bool(view.get('on', True)))
            native.same_line()
            native.set_next_item_width(cyui.dp(80))
            formats = list(imagegen.FORMATS)
            current = formats.index(view.get('format', 'project')) if view.get('format', 'project') in formats else 0
            changed, current = native.combo('##fmt', current, [tr(f) for f in formats])
            if changed:
                view['format'] = formats[current]
            native.same_line()
            with cyui.scoped_disabled(not view.get('on', True)):
                native.set_next_item_width(-1)
                _, view['text'] = native.input_text('##text', view['text'])
            native.pop_id()
        if cyui.icon_text_button(cyui.icon.add, tr('Add a view') + f'##{name}', 'ghost'):
            o[name].append({'key': f'view{len(o[name]) + 1}', 'on': True, 'format': o[name][0].get('format', 'project'),
                            'text': ''})
        native.same_line()
        if cyui.ghost_button(tr('Default views') + f'##{name}'):
            o[name] = copy.deepcopy(imagegen.DEFAULTS[name])
        cyui.end_section()

    def _format_property(self, o, key):
        formats = list(imagegen.FORMATS)
        cyui.property(tr('Format'))
        changed, index = native.combo('##' + key, formats.index(o[key]), [tr(f) for f in formats])
        if changed:
            o[key] = formats[index]

    def _loras(self, o):
        import shutil
        from storyboard import imageengine
        if time.monotonic() - getattr(self, 'loras_at', 0.0) > 2.0:
            self.loras_at, self.lora_names = time.monotonic(), imageengine.lora_files()
        chosen = {entry['file']: entry for entry in o['loras']}
        for name in self.lora_names + [n for n in chosen if n not in self.lora_names]:
            native.push_id('lora' + name)
            entry = chosen.get(name)
            changed, on = cyui.toggle_switch('##on', bool(entry and entry.get('on', True)))
            if changed:
                if entry is None:
                    entry = {'file': name, 'strength': 1.0, 'on': True}
                    o['loras'].append(entry)
                entry['on'] = on
            native.same_line()
            strength = float(entry.get('strength', 1.0)) if entry else 1.0
            changed, strength = cyui.slider_bar('##strength', strength, -2.0, 2.0, '%.2f', cyui.dp(110))
            if changed:
                if entry is None:
                    entry = {'file': name, 'strength': strength, 'on': False}
                    o['loras'].append(entry)
                entry['strength'] = round(strength, 2)
            native.same_line()
            native.align_text_to_frame_padding()
            if name in self.lora_names:
                native.text(name)
            else:
                cyui.text_coloured(cyui.palette().error, name + '  - ' + tr('file not found'))
                native.same_line()
                if cyui.ghost_button(tr('Forget')):
                    o['loras'].remove(entry)
            native.pop_id()
        if not self.lora_names and not chosen:
            native.push_text_wrap_pos(0.0)
            cyui.text_faint(tr('No LoRA yet. A LoRA is made for one model (Qwen-Image 2.1, Qwen-Image-Edit 2511 or Qwen-Image 2512); '
                               'its trigger words go in the prompt or in "Added to every picture".'))
            native.pop_text_wrap_pos()
        if cyui.icon_text_button(cyui.icon.add, tr('Add LoRA files...'), 'ghost'):
            dialogs.open('lorafiles', 'LoRA files', ['LoRA', '*.safetensors'], multiple=True)
        for path in dialogs.result('lorafiles') or []:
            try:
                imageengine.lora_folder().mkdir(parents=True, exist_ok=True)
                target = imageengine.lora_folder() / Path(path).name
                if not target.exists():
                    shutil.copyfile(path, target)
                self.loras_at = 0.0
            except OSError as exc:
                self.message = str(exc)
        native.same_line()
        if cyui.icon_text_button(cyui.icon.folder, tr('Open the LoRA folder'), 'ghost'):
            imageengine.lora_folder().mkdir(parents=True, exist_ok=True)
            open_local(imageengine.lora_folder())

    def _model_properties(self, o):
        models = (self.status or {}).get('models') or []
        for key, kind, label in (('model', 'edit', 'Model for pictures from references'),
                                 ('textModel', 'text', 'Model for pictures from a text')):
            candidates = [m for m in models if kind in m.get('kinds', [])]
            ids = [''] + [m['id'] for m in candidates]
            names = [tr('automatic (installed default)')] + \
                [m['name'] + ('' if m['installed'] else '  - ' + tr('not installed')) for m in candidates]
            cyui.property(tr(label))
            index = ids.index(o[key]) if o[key] in ids else 0
            changed, index = native.combo('##' + key, index, names)
            if changed:
                o[key] = ids[index]

    # ------------------------------------------------------------------ engine and installation
    def _engine_line(self):
        status = self.status or {}
        engine = status.get('engine') or {}
        worker = status.get('worker') or {}
        last = status.get('last') or {}
        p = cyui.palette()
        resident = ', '.join((worker.get('resident') or {}).get('models') or [])
        cyui.begin_toolbar('##enginebar')
        if worker.get('alive'):
            cyui.status_dot(p.success, tr('Model in memory'))
            native.same_line()
            native.align_text_to_frame_padding()
            native.text(tr('Model in memory') + (': ' + resident if resident else ''))
            native.same_line()
            if cyui.icon_text_button(cyui.icon.power, tr('Unload'), 'ghost'):
                self.jobs.submit('unload_image_model', {}, lambda job: self._refresh_status(force=True), tr('Unload'))
            cyui.tooltip(tr('Give the memory of the model back now'))
        else:
            cyui.status_dot(p.textFaint)
            native.same_line()
            native.align_text_to_frame_padding()
            cyui.text_dim(tr('No model in memory (loaded at the first picture).'))
        if last.get('secondsPerPicture'):
            native.same_line()
            cyui.toolbar_separator()
            native.align_text_to_frame_padding()
            cyui.text_faint(f'{last.get("device", "")}  -  {last["secondsPerPicture"]:.1f} s / {tr("picture")}'
                            + (f'  ({last["steps"]} {tr("steps")})' if last.get('steps') else ''))
        cyui.end_toolbar()
        if last.get('int8Kernels') is False:
            cyui.callout('warning', tr('The engine did not find its CUDA kernels for int8 models: pictures are slower. '
                                       'Repair the engine (Installation).'))
        models = status.get('models') or []
        ready = engine.get('installed') and any(m['installed'] for m in models)
        if not ready:
            cyui.callout('info', tr('Install the engine and a model below before generating.'))
        if cyui.begin_section(tr('Installation (engine and models)') + '###imginstall', not ready or self.test):
            self._installation(engine, models)
            cyui.end_section()

    def _installation(self, engine, models):
        jobs = self.jobs
        p = cyui.palette()
        cyui.begin_card('##enginecard', tr(engine.get('label', 'Image engine')))
        native.align_text_to_frame_padding()
        cyui.badge(tr(engine.get('state', 'NotInstalled')), 'success' if engine.get('installed') else 'warning')
        native.same_line()
        cyui.text_dim((f"torch {engine['torch']}, {engine['device']}  -  " if engine.get('torch') else '')
                      + f"~{gb(engine.get('estimatedBytes'))}")
        native.push_text_wrap_pos(0.0)
        cyui.text_faint(tr('A private Python environment with PyTorch under runtime/engines/image, created at its '
                           'final path and checked by import before use.'))
        native.pop_text_wrap_pos()
        running = jobs.running('install_image_engine')
        with cyui.scoped_disabled(bool(running)):
            if cyui.icon_text_button(cyui.icon.repair, tr('Install or repair the engine (GPU)'),
                                     'outline' if engine.get('installed') else 'primary'):
                jobs.submit('install_image_engine', {}, lambda job: self._refresh_status(force=True), tr('Image engine'))
        for job in running:
            cyui.progress_bar(-1.0, (-native.get_frame_height() - cyui.dp(8), 0), jobs.progress_text(job)[:110])
            native.same_line()
            if cyui.icon_button(cyui.icon.stop, tr('Cancel') + '##eng'):
                jobs.cancel(job['jobId'])
        cyui.space(4)
        cyui.section_title(tr('Where the pictures are rendered'))
        o = self.options
        _, o['server'] = cyui.text_field('##imgserver', o['server'], tr('Other ComfyUI (address, empty = this computer)'), -1)
        native.push_text_wrap_pos(0.0)
        cyui.text_faint(tr('Empty: the engine of this application, on this computer. An address (for example the '
                           'tunnel of a Colab ComfyUI): the same pictures are rendered there; its models must be '
                           'in its own folders.'))
        native.pop_text_wrap_pos()
        cyui.end_card()
        cyui.space(4)
        cyui.section_title(tr('Models'))
        for entry in models:
            native.push_id(entry['id'])
            tone = {'Installed': 'success', 'Downloading': 'info', 'Verifying': 'info', 'Failed': 'error',
                    'AccessRequired': 'error'}.get(entry['state'], 'warning' if entry['presentBytes'] else 'neutral')
            cyui.begin_card('##model')
            with cyui.scoped_font(cyui.bold_font(), 1.0):
                native.text(entry['name'])
            native.same_line()
            cyui.badge(tr(entry['state']), tone)
            native.same_line()
            cyui.text_faint(gb(entry['downloadBytes'])
                            + (f"  ({gb(entry['presentBytes'])} {tr('present')})" if 0 < entry['presentBytes'] < entry['downloadBytes'] else ''))
            license_info = entry.get('license') or {}
            native.push_text_wrap_pos(0.0)
            cyui.text_dim(tr(entry.get('summary', '')))
            cyui.text_faint(f"{tr('Licence')}: {license_info.get('name', '?')}"
                            + (f"  -  VRAM ~{gb(entry['resources']['vramBytes'])}" if (entry.get('resources') or {}).get('vramBytes') else ''))
            native.pop_text_wrap_pos()
            if entry.get('error'):
                cyui.callout('error', str(entry['error'])[:300])
            active = [j for j in jobs.running('install_image_model', 'verify_image_model', 'remove_image_model')
                      if j['parameters'].get('model') == entry['id']]
            if active:
                progress = active[0].get('progress') or {}
                cyui.progress_bar(float(progress.get('percent') or 0) / 100.0, (-native.get_frame_height() - cyui.dp(8), 0),
                                  jobs.progress_text(active[0])[:100])
                native.same_line()
                if cyui.icon_button(cyui.icon.stop, tr('Cancel')):
                    jobs.cancel(active[0]['jobId'])
            else:
                refresh = lambda job: self._refresh_status(force=True)  # noqa: E731
                if entry['state'] in ('Downloading', 'Verifying'):
                    # no job of this window: another client (CLI, MCP) is installing it right now
                    progress = entry.get('progress') or {}
                    cyui.text_faint(tr('Being downloaded by another client')
                                    + (f": {gb(progress.get('doneBytes'))} / {gb(progress.get('totalBytes'))}" if progress else ''))
                elif not entry['installed']:
                    label = 'Repair' if entry['state'] in ('Failed', 'Partial') else \
                        'Resume' if entry['state'] in ('Interrupted', 'Cancelled') else 'Download'
                    if cyui.icon_text_button(cyui.icon.download, tr(label), 'outline'):
                        jobs.submit('install_image_model', {'model': entry['id'], 'accept_license': True,
                                                            'repair': entry['state'] in ('Failed', 'Partial')},
                                    refresh, tr('Download') + ' ' + entry['name'])
                    native.same_line()
                if entry['presentBytes'] > 0:
                    if cyui.icon_button(cyui.icon.check, tr('Verify files')):
                        jobs.submit('verify_image_model', {'model': entry['id']}, refresh, tr('Verify files'))
                    native.same_line(0, cyui.dp(2))
                    if cyui.icon_button(cyui.icon.trash, tr('Remove')):
                        jobs.submit('remove_image_model', {'model': entry['id']}, refresh, tr('Remove'))
                    native.same_line(0, cyui.dp(2))
                url = (entry.get('source') or {}).get('url')
                if url and cyui.icon_button(cyui.icon.globe, tr('Official page')):
                    webbrowser.open(url)
            cyui.end_card()
            native.pop_id()

    # ------------------------------------------------------------------ results
    def _results(self):
        if not self.results:
            cyui.empty_state(tr('No picture yet'), tr('Choose what to generate on the left, then Generate.'), cyui.icon.photo)
            return
        pending = [r for r in self.results if not r['kept']]
        cyui.overline(tr('RESULTS'))
        native.same_line()
        cyui.badge(str(len(self.results)))
        native.same_line()
        with cyui.scoped_disabled(not pending):
            if cyui.icon_text_button(cyui.icon.check, tr('Keep all'), 'ghost'):
                for result in pending:
                    self.keep(result)
        native.same_line()
        if cyui.icon_text_button(cyui.icon.close, tr('Clear the list'), 'ghost'):
            self.results = [r for r in self.results if False]
        size = float(preferences.values.get('image_thumb', 260))
        native.same_line()
        cyui.align_right(cyui.dp(150))
        changed, size = cyui.slider_bar('##thumbs', size, 140.0, 520.0, tr('Thumbnails') + ' %.0f', cyui.dp(150))
        if changed:
            preferences.values['image_thumb'] = size
        cyui.space(4)
        width = native.get_content_region_avail().x
        columns = max(1, int(width // (size + cyui.dp(16))))
        p = cyui.palette()
        for index, result in enumerate(list(self.results)):
            if index % columns:
                native.same_line()
            native.begin_group()
            native.push_id(f'res{result["id"]}{index}')
            corner = native.get_cursor_screen_pos()
            drawn = image(result['file'], size, size, 768)
            if not drawn[0]:
                native.dummy(native.ImVec2(size, size * 0.6))
            elif result['kept']:
                native.get_window_draw_list().add_rect(corner, native.ImVec2(corner.x + drawn[0], corner.y + drawn[1]),
                                                       p.success, cyui.dp(3), cyui.dp(2))
            native.push_text_wrap_pos(native.get_cursor_pos().x + size)
            native.text(f'{result["label"]}' + (f' #{result["variant"]}' if result.get('variant', 1) > 1 else ''))
            cyui.text_faint(f'{result["width"]}x{result["height"]}  seed {result["seed"]}')
            native.pop_text_wrap_pos()
            if result['kept']:
                cyui.badge(tr('Kept in the project'), 'success')
            else:
                if cyui.button(tr('Keep') + '##keep', 'primary', small=True):
                    self.keep(result)
                native.same_line(0, cyui.dp(2))
                if cyui.icon_button(cyui.icon.close, tr('Discard')):
                    self.results.remove(result)
            native.same_line(0, cyui.dp(2))
            if cyui.icon_button(cyui.icon.open_file, tr('Open')):
                open_local(result['file'])
            native.same_line(0, cyui.dp(2))
            if cyui.icon_button(cyui.icon.refresh, tr('Use this seed for the next pictures'),
                                not self.options['randomSeed'] and int(self.options['seed']) == int(result['seed'])):
                self.options['randomSeed'] = False
                self.options['seed'] = int(result['seed'])
            native.pop_id()
            native.end_group()

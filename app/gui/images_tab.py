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
            native.text_wrapped(tr('Create a storyboard (New) or open one to start.'))
            return
        o = self._options()
        self.jobs.poll()
        self._refresh_status()
        avail = native.get_content_region_avail()
        native.begin_group()
        native.begin_child('img-left', native.ImVec2(560, avail.y - 150), native.ChildFlags_.borders)
        self._request_panel(o)
        native.end_child()
        native.begin_child('img-actions', native.ImVec2(560, 0), native.ChildFlags_.borders)
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
        native.text_wrapped(tr('Generate the pictures MiniMax H3 needs, from your reference pictures or from a text. '
                               'The pictures you keep go into the project: a character or a place gets new reference '
                               'pictures, a shot gets its first image.'))
        for index, (_, label) in enumerate(RECIPES):
            if index:
                native.same_line()
            if native.radio_button(tr(label) + f'##recipe{index}', self.recipe == index):
                self.recipe = index
        recipe = RECIPES[self.recipe][0]
        native.separator()
        if recipe in ('character', 'location'):
            self._item_combo(recipe)
            item = next((i for i in self._items(recipe) if i['id'] == self.item[recipe]), None)
            if item:
                used = min(self.limit, imagegen.CHARACTER_PICTURES)
                if imagegen.item_pictures(board, item, 1):
                    self._item_pictures(item, used)
                else:
                    native.text_colored(native.ImVec4(1, .75, .35, 1),
                                        tr('No picture yet: the views are generated from the description alone.'))
                native.text(tr('Description'))
                _, item['description'] = imgui.input_text_multiline('##itemdesc', item.get('description', ''),
                                                                    native.ImVec2(-1, 54))
                if imgui.small_button('Add reference pictures...'):
                    dialogs.open('imgrefs' + item['id'], 'Reference pictures', IMAGE_FILTER, multiple=True)
                for path in dialogs.result('imgrefs' + item['id']) or []:
                    relative = self.editor.act(board.import_asset, path)
                    if relative:
                        item.setdefault('files', []).append(relative)
            if recipe == 'location':
                characters = self._items('character')
                names = [tr('nobody (empty place)')] + [c['name'] for c in characters]
                ids = [''] + [c['id'] for c in characters]
                native.set_next_item_width(300)
                index = ids.index(self.with_character) if self.with_character in ids else 0
                changed, index = native.combo(tr('Character in the place') + '##withchar', index, names)
                if changed:
                    self.with_character = ids[index]
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
            note(tr('The staging render gives the framing, the characters and the place of the shot '
                    'give the look. The kept picture becomes the first image of the shot.'))
            if panel is not None:
                staged, unknown = imagegen.stage_figures(board, panel)
                if unknown:
                    characters = [c for c in self._items('character') if imagegen.item_pictures(board, c, 1)]
                    ids = [''] + [c['id'] for c in characters]
                    names = [tr('what the text describes')] + [c['name'] for c in characters]
                    native.set_next_item_width(260)
                    index = ids.index(self.extras) if self.extras in ids else 0
                    changed, index = native.combo(f'{unknown} ' + tr('mannequin(s) without a reference are') + '##extras',
                                                  index, names)
                    if changed:
                        self.extras = ids[index]
            guides = list(imagegen.GUIDES)
            labels = ['automatic (structure guide when its model is installed)', 'structure guide (depth or pose, ControlNet)',
                      'staging picture', 'both', 'none (text and references only)']
            native.set_next_item_width(380)
            changed, index = native.combo(tr('Framing from the 3D staging') + '##guide', guides.index(o['panelGuide']),
                                          [tr(x) for x in labels])
            if changed:
                o['panelGuide'] = guides[index]
            if o['panelGuide'] in ('auto', 'control', 'both'):
                if not self.control:
                    native.text_colored(native.ImVec4(1, .75, .35, 1),
                                        tr('The ControlNet of the model is not installed (Installation): the staging '
                                           'picture is used instead.') if o['panelGuide'] == 'auto' else
                                        tr('The ControlNet of the model is not installed (Installation).'))
                sources = list(imagegen.CONTROL_SOURCES)
                native.set_next_item_width(110)
                changed, index = native.combo(tr('Guide') + '##ctlsrc', sources.index(o['panelControlSource']),
                                              [tr(x) for x in sources])
                if changed:
                    o['panelControlSource'] = sources[index]
                native.same_line()
                native.set_next_item_width(90)
                _, o['panelControlStrength'] = imgui.slider_float('Strength##imgctl', float(o['panelControlStrength']),
                                                                  0.05, 2.0, '%.2f')
                native.same_line()
                native.set_next_item_width(90)
                _, o['panelControlEnd'] = imgui.slider_float('Until (share of the steps)##imgctl', float(o['panelControlEnd']),
                                                             0.05, 1.0, '%.2f')
            self._format_combo(o, 'panelFormat')
            native.same_line()
            native.set_next_item_width(90)
            _, o['panelCharacterPictures'] = imgui.slider_int('Pictures per character', int(o['panelCharacterPictures']), 1, 6)
        else:
            native.text(tr('Prompt'))
            _, self.prompt = imgui.input_text_multiline('##freeprompt', self.prompt, native.ImVec2(-1, 110))
            native.text(tr('Reference pictures (none: from the text alone)') + f'  -  {self.limit} max')
            for position, path in enumerate(list(self.references)):
                image(path, 90, 90, 256)
                native.same_line()
                if imgui.small_button(f'Remove##ref{position}'):
                    self.references.pop(position)
            if len(self.references) < self.limit and imgui.small_button('Add pictures...'):
                dialogs.open('freerefs', 'Reference pictures', IMAGE_FILTER, multiple=True)
            for path in dialogs.result('freerefs') or []:
                if len(self.references) < self.limit:
                    self.references.append(path)
            self._format_combo(o, 'freeFormat')
        if recipe != 'free':
            native.text(tr('Added to every picture'))
            native.set_next_item_width(-1)
            _, self.extra = imgui.input_text('##extra', self.extra)

        native.separator_text(tr('Generation'))
        native.set_next_item_width(90)
        _, o['count'] = imgui.slider_int('Pictures per view', int(o['count']), 1, 8)
        native.same_line()
        sizes = list(imagegen.MEGAPIXELS)
        native.set_next_item_width(110)
        index = sizes.index(o['megapixels']) if o['megapixels'] in sizes else 2
        changed, index = native.combo(tr('Size') + '##mp', index, [f'{m:g} MP' for m in sizes])
        if changed:
            o['megapixels'] = sizes[index]
        _, o['randomSeed'] = imgui.checkbox('Random seed', bool(o['randomSeed']))
        if not o['randomSeed']:
            native.same_line()
            native.set_next_item_width(160)
            _, o['seed'] = imgui.input_int('Seed', int(o['seed']), 1)
        _, o['fast'] = imgui.checkbox('Fast mode (few steps)', bool(o['fast']))
        native.same_line()
        native.set_next_item_width(90)
        _, o['steps'] = imgui.slider_int('Steps (0 = auto)', int(o['steps']), 0, 50)
        native.same_line()
        native.set_next_item_width(90)
        _, o['guidance'] = imgui.slider_float('Guidance (0 = auto)', float(o['guidance']), 0.0, 10.0, '%.1f')
        _, o['includeStyle'] = imgui.checkbox('Project style in the prompt', bool(o['includeStyle']))
        native.text(tr('Negative prompt'))
        native.set_next_item_width(-1)
        _, o['negative'] = imgui.input_text('##negative', o['negative'])
        self._loras(o)
        self._model_combos(o)
        native.set_next_item_width(140)
        _, o['keepLoadedMinutes'] = imgui.slider_int('Keep the model loaded (minutes, 0 = until closed)',
                                                     int(o['keepLoadedMinutes']), 0, 240)
        requests = self.plan[0] if self.plan else []
        if requests and native.tree_node(tr('What will be asked') + '###imgplan'):
            for request in requests:
                native.bullet_text(f'{request["label"]}  -  {request["width"]}x{request["height"]}  -  '
                                   f'{len(request["references"])} {tr("reference(s)")}')
                native.push_text_wrap_pos(0.0)
                native.text_disabled(request['prompt'])
                native.pop_text_wrap_pos()
            native.tree_pop()
        if native.tree_node(tr('Sentences') + '###imgsentences'):
            for key in imagegen.TEXTS:
                native.text(tr(TEXT_LABELS[key]))
                _, o[key] = imgui.input_text_multiline(f'##{key}', o[key], native.ImVec2(-1, 40))
            if imgui.small_button('Default sentences##img'):
                for key in imagegen.TEXTS:
                    o[key] = imagegen.DEFAULTS[key]
            native.tree_pop()

    def _actions(self, o):
        board = self.editor.board
        self._refresh_plan()
        requests, error = self.plan
        if error:
            native.text_colored(native.ImVec4(1, .6, .35, 1), error)
        running = self.jobs.running('generate_images')
        native.begin_disabled(bool(error) or bool(running))
        if imgui.button('Generate') or (self.test and self.editor.frames == 12 and not error):
            self.generate()
        native.end_disabled()
        native.same_line()
        native.begin_disabled(bool(error))
        if imgui.button('ComfyUI workflows...'):
            recipe, arguments = self._arguments()
            self.editor.save()
            self.jobs.submit('export_image_workflows', {'project': str(board.folder), 'recipe': recipe,
                                                        'options': copy.deepcopy(o), **arguments},
                             lambda job: job['state'] == 'Completed' and open_local(job['outputs']['folder']),
                             tr('ComfyUI workflows'))
        native.end_disabled()
        if requests:
            native.same_line()
            native.text_disabled(f'{len(requests) * int(o["count"])} {tr("picture(s)")}')
        for job in running:
            progress = job.get('progress') or {}
            native.progress_bar(float(progress.get('percent') or 0) / 100.0, native.ImVec2(-90, 0),
                                self.jobs.progress_text(job)[:90])
            native.same_line()
            if imgui.small_button('Cancel##gen'):
                self.jobs.cancel(job['jobId'])
        if self.jobs.error:
            native.text_colored(native.ImVec4(1, .45, .4, 1), self.jobs.error[:400])
        if self.message:
            native.text_colored(native.ImVec4(1, .7, .35, 1), self.message[:300])

    def _item_pictures(self, item, used):
        """Every picture of the item, the references first: the first `used` ones are sent to the model
        when its views are generated. A picture can be put first, or taken out of the item."""
        board = self.editor.board
        files = [f for f in item.get('files') or [] if (board.folder / f).suffix.lower() in model.IMAGE_SUFFIXES
                 and (board.folder / f).is_file()]
        generations = board.doc.get('generations') or {}
        note(f'{len(files)} ' + tr('picture(s). The first ones are the references sent to the model') + f' ({min(used, len(files))}). '
             + tr('"First" puts a picture at the head of the list; kept pictures are added at the end.'))
        size = 92.0
        columns = max(1, int(native.get_content_region_avail().x // (size + 10)))
        native.begin_child('itempics' + item['id'], native.ImVec2(0, min(3, -(-len(files) // columns)) * (size + 48) + 8),
                           native.ChildFlags_.borders)
        for index, relative in enumerate(list(files)):
            if index % columns:
                native.same_line()
            native.begin_group()
            native.push_id(f'pic{index}')
            drawn = image(board.folder / relative, size, size, 256)
            if not drawn[0]:
                native.dummy(native.ImVec2(size, size))
            key = (generations.get(Path(relative).name) or {}).get('key', '')
            if index < used:
                native.text_colored(native.ImVec4(.5, .9, .5, 1), tr('reference') + (f' {index + 1}'))
            else:
                native.text_disabled((tr(key) if key else tr('picture'))[:13])
            if index and imgui.small_button('First'):
                item['files'].remove(relative)
                item['files'].insert(0, relative)
            if index:
                native.same_line()
            if imgui.small_button('x'):
                item['files'].remove(relative)
            if native.is_item_hovered():
                native.set_tooltip(tr('Take this picture out of the item (the file stays in the project)'))
            native.pop_id()
            native.end_group()
        if self.scroll_pictures:
            native.set_scroll_here_y(1.0)
            self.scroll_pictures = False
        native.end_child()

    def _item_combo(self, kind):
        items = self._items(kind)
        if not items:
            native.text_colored(native.ImVec4(1, .75, .35, 1), tr('The library has none yet: add one in the Storyboard tab '
                                                                   '(References), with a description.'))
            return
        ids = [i['id'] for i in items]
        if self.item[kind] not in ids:
            self.item[kind] = ids[0]
        native.set_next_item_width(-1)
        changed, index = native.combo(f'##imgitem{kind}', ids.index(self.item[kind]), [i['name'] for i in items])
        if changed:
            self.item[kind] = ids[index]

    def _views(self, o, name):
        native.separator_text(tr('Views'))
        for index, view in enumerate(o[name]):
            native.push_id(f'{name}{index}')
            _, view['on'] = native.checkbox('##on', bool(view.get('on', True)))
            native.same_line()
            native.set_next_item_width(76)
            formats = list(imagegen.FORMATS)
            current = formats.index(view.get('format', 'project')) if view.get('format', 'project') in formats else 0
            changed, current = native.combo('##fmt', current, [tr(f) for f in formats])
            if changed:
                view['format'] = formats[current]
            native.same_line()
            native.set_next_item_width(-1)
            _, view['text'] = native.input_text('##text', view['text'])
            native.pop_id()
        if imgui.small_button(f'Add a view##{name}'):
            o[name].append({'key': f'view{len(o[name]) + 1}', 'on': True, 'format': o[name][0].get('format', 'project'),
                            'text': ''})
        native.same_line()
        if imgui.small_button(f'Default views##{name}'):
            o[name] = copy.deepcopy(imagegen.DEFAULTS[name])

    def _format_combo(self, o, key):
        formats = list(imagegen.FORMATS)
        native.set_next_item_width(140)
        changed, index = native.combo(tr('Format') + '##' + key, formats.index(o[key]), [tr(f) for f in formats])
        if changed:
            o[key] = formats[index]

    def _loras(self, o):
        import shutil
        from storyboard import imageengine
        native.separator_text('LoRA')
        if time.monotonic() - getattr(self, 'loras_at', 0.0) > 2.0:
            self.loras_at, self.lora_names = time.monotonic(), imageengine.lora_files()
        chosen = {entry['file']: entry for entry in o['loras']}
        for name in self.lora_names + [n for n in chosen if n not in self.lora_names]:
            native.push_id('lora' + name)
            entry = chosen.get(name)
            changed, on = native.checkbox('##on', bool(entry and entry.get('on', True)))
            if changed:
                if entry is None:
                    entry = {'file': name, 'strength': 1.0, 'on': True}
                    o['loras'].append(entry)
                entry['on'] = on
            native.same_line()
            native.set_next_item_width(110)
            strength = float(entry.get('strength', 1.0)) if entry else 1.0
            changed, strength = native.slider_float('##strength', strength, -2.0, 2.0, '%.2f')
            if changed:
                if entry is None:
                    entry = {'file': name, 'strength': strength, 'on': False}
                    o['loras'].append(entry)
                entry['strength'] = round(strength, 2)
            native.same_line()
            if name in self.lora_names:
                native.text(name)
            else:
                native.text_colored(native.ImVec4(1, .5, .4, 1), name + '  - ' + tr('file not found'))
                native.same_line()
                if imgui.small_button('Forget'):
                    o['loras'].remove(entry)
            native.pop_id()
        if not self.lora_names and not chosen:
            note(tr('No LoRA yet. A LoRA is made for one model (Qwen-Image 2.1, Qwen-Image-Edit 2511 or Qwen-Image 2512); '
                    'its trigger words go in the prompt or in "Added to every picture".'))
        if imgui.small_button('Add LoRA files...'):
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
        if imgui.small_button('Open the LoRA folder'):
            imageengine.lora_folder().mkdir(parents=True, exist_ok=True)
            open_local(imageengine.lora_folder())

    def _model_combos(self, o):
        models = (self.status or {}).get('models') or []
        for key, kind, label in (('model', 'edit', 'Model for pictures from references'),
                                 ('textModel', 'text', 'Model for pictures from a text')):
            candidates = [m for m in models if kind in m.get('kinds', [])]
            ids = [''] + [m['id'] for m in candidates]
            names = [tr('automatic (installed default)')] + \
                [m['name'] + ('' if m['installed'] else '  - ' + tr('not installed')) for m in candidates]
            native.set_next_item_width(330)
            index = ids.index(o[key]) if o[key] in ids else 0
            changed, index = native.combo(tr(label) + '##' + key, index, names)
            if changed:
                o[key] = ids[index]

    # ------------------------------------------------------------------ engine and installation
    def _engine_line(self):
        status = self.status or {}
        engine = status.get('engine') or {}
        worker = status.get('worker') or {}
        last = status.get('last') or {}
        resident = ', '.join((worker.get('resident') or {}).get('models') or [])
        if worker.get('alive'):
            native.text_colored(native.ImVec4(.5, .9, .5, 1), tr('Model in memory') + (': ' + resident if resident else ''))
            native.same_line()
            if imgui.small_button('Unload'):
                self.jobs.submit('unload_image_model', {}, lambda job: self._refresh_status(force=True), tr('Unload'))
        else:
            native.text_disabled(tr('No model in memory (loaded at the first picture).'))
        if last.get('secondsPerPicture'):
            native.same_line()
            native.text_disabled(f'{last.get("device", "")}  -  {last["secondsPerPicture"]:.1f} s / {tr("picture")}'
                                 + (f'  ({last["steps"]} {tr("steps")})' if last.get('steps') else ''))
        if last.get('int8Kernels') is False:
            native.text_colored(native.ImVec4(1, .7, .35, 1), tr('The engine did not find its CUDA kernels for int8 models: '
                                                                 'pictures are slower. Repair the engine (Installation).'))
        models = status.get('models') or []
        ready = engine.get('installed') and any(m['installed'] for m in models)
        flags = 0 if ready and not self.test else native.TreeNodeFlags_.default_open
        if native.collapsing_header(tr('Installation (engine and models)') + '###imginstall', flags):
            self._installation(engine, models)
        native.separator()

    def _installation(self, engine, models):
        jobs = self.jobs
        colour = STATE_COLOUR['Installed'] if engine.get('installed') else STATE_COLOUR['NotInstalled']
        native.text_colored(native.ImVec4(*colour), tr(engine.get('state', 'NotInstalled')))
        native.same_line()
        native.text(tr(engine.get('label', 'Image engine'))
                    + (f"  (torch {engine['torch']}, {engine['device']})" if engine.get('torch') else '')
                    + f"  ~{gb(engine.get('estimatedBytes'))}")
        note(tr('A private Python environment with PyTorch under runtime/engines/image, created at its '
                'final path and checked by import before use.'))
        running = jobs.running('install_image_engine')
        native.begin_disabled(bool(running))
        if imgui.button('Install or repair the engine (GPU)'):
            jobs.submit('install_image_engine', {}, lambda job: self._refresh_status(force=True), tr('Image engine'))
        native.end_disabled()
        for job in running:
            native.progress_bar(0.5, native.ImVec2(-90, 0), jobs.progress_text(job)[:110])
            native.same_line()
            if imgui.small_button('Cancel##eng'):
                jobs.cancel(job['jobId'])
        native.separator_text(tr('Where the pictures are rendered'))
        o = self.options
        native.text(tr('Other ComfyUI (address, empty = this computer)'))
        native.set_next_item_width(-1)
        _, o['server'] = imgui.input_text('##imgserver', o['server'])
        note(tr('Empty: the engine of this application, on this computer. An address (for example the '
                'tunnel of a Colab ComfyUI): the same pictures are rendered there; its models must be '
                'in its own folders.'))
        native.separator_text(tr('Models'))
        for entry in models:
            native.push_id(entry['id'])
            colour = STATE_COLOUR.get(entry['state'], STATE_COLOUR['NotInstalled'])
            native.text_colored(native.ImVec4(*colour), tr(entry['state']))
            native.same_line()
            native.text(f"{entry['name']}  -  {gb(entry['downloadBytes'])}"
                        + (f"  ({gb(entry['presentBytes'])} {tr('present')})" if 0 < entry['presentBytes'] < entry['downloadBytes'] else ''))
            license_info = entry.get('license') or {}
            note(f"{tr(entry.get('summary', ''))}  {tr('Licence')}: {license_info.get('name', '?')}"
                 + (f"  -  VRAM ~{gb(entry['resources']['vramBytes'])}" if (entry.get('resources') or {}).get('vramBytes') else ''))
            if entry.get('error'):
                native.text_colored(native.ImVec4(1, .45, .4, 1), str(entry['error'])[:300])
            active = [j for j in jobs.running('install_image_model', 'verify_image_model', 'remove_image_model')
                      if j['parameters'].get('model') == entry['id']]
            if active:
                progress = active[0].get('progress') or {}
                native.progress_bar(float(progress.get('percent') or 0) / 100.0, native.ImVec2(-90, 0),
                                    jobs.progress_text(active[0])[:100])
                native.same_line()
                if imgui.small_button('Cancel'):
                    jobs.cancel(active[0]['jobId'])
            else:
                refresh = lambda job: self._refresh_status(force=True)  # noqa: E731
                if entry['state'] in ('Downloading', 'Verifying'):
                    # no job of this window: another client (CLI, MCP) is installing it right now
                    progress = entry.get('progress') or {}
                    native.text_disabled(tr('Being downloaded by another client')
                                         + (f": {gb(progress.get('doneBytes'))} / {gb(progress.get('totalBytes'))}" if progress else ''))
                elif not entry['installed']:
                    label = 'Repair' if entry['state'] in ('Failed', 'Partial') else \
                        'Resume' if entry['state'] in ('Interrupted', 'Cancelled') else 'Download'
                    if imgui.small_button(label):
                        jobs.submit('install_image_model', {'model': entry['id'], 'accept_license': True,
                                                            'repair': entry['state'] in ('Failed', 'Partial')},
                                    refresh, tr('Download') + ' ' + entry['name'])
                    native.same_line()
                if entry['presentBytes'] > 0:
                    if imgui.small_button('Verify files'):
                        jobs.submit('verify_image_model', {'model': entry['id']}, refresh, tr('Verify files'))
                    native.same_line()
                    if imgui.small_button('Remove'):
                        jobs.submit('remove_image_model', {'model': entry['id']}, refresh, tr('Remove'))
                    native.same_line()
                url = (entry.get('source') or {}).get('url')
                if url and imgui.small_button('Official page'):
                    webbrowser.open(url)
                elif not url:
                    native.new_line()
            native.pop_id()

    # ------------------------------------------------------------------ results
    def _results(self):
        if not self.results:
            note(tr('The generated pictures appear here. Keep the ones you like: they are copied into '
                    'the project with their recipe (prompt, references, seed), the others stay in the job folder.'))
            return
        pending = [r for r in self.results if not r['kept']]
        native.begin_disabled(not pending)
        if imgui.button('Keep all'):
            for result in pending:
                self.keep(result)
        native.end_disabled()
        native.same_line()
        if imgui.button('Clear the list'):
            self.results = [r for r in self.results if False]
        size = float(preferences.values.get('image_thumb', 260))
        native.same_line()
        native.set_next_item_width(140)
        changed, size = imgui.slider_float('Thumbnails', size, 140.0, 520.0, '%.0f')
        if changed:
            preferences.values['image_thumb'] = size
        width = native.get_content_region_avail().x
        columns = max(1, int(width // (size + 16)))
        for index, result in enumerate(list(self.results)):
            if index % columns:
                native.same_line()
            native.begin_group()
            native.push_id(f'res{result["id"]}{index}')
            drawn = image(result['file'], size, size, 768)
            if not drawn[0]:
                native.dummy(native.ImVec2(size, size * 0.6))
            native.push_text_wrap_pos(native.get_cursor_pos().x + size)
            native.text(f'{result["label"]}' + (f' #{result["variant"]}' if result.get('variant', 1) > 1 else ''))
            native.text_disabled(f'{result["width"]}x{result["height"]}  seed {result["seed"]}')
            native.pop_text_wrap_pos()
            if result['kept']:
                native.text_colored(native.ImVec4(.5, .9, .5, 1), tr('Kept in the project'))
            else:
                if imgui.small_button('Keep'):
                    self.keep(result)
                native.same_line()
                if imgui.small_button('Discard'):
                    self.results.remove(result)
            native.same_line()
            if imgui.small_button('Open'):
                open_local(result['file'])
            native.same_line()
            if imgui.small_button('Again'):
                self.options['randomSeed'] = False
                self.options['seed'] = int(result['seed'])
            if native.is_item_hovered():
                native.set_tooltip(tr('Use this seed for the next pictures'))
            native.pop_id()
            native.end_group()

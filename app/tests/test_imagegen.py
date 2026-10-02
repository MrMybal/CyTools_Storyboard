"""Picture generation: plans, ComfyUI graphs, and the whole chain through the real runtime with a
stand-in worker (tests/fake_image_worker.py speaks the protocol of workers/image_worker.py and
reads each API prompt; no model, no GPU). What a real model renders is not tested here.
"""
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


def picture(path, colour, size=(320, 200)):
    from PIL import Image
    Image.new('RGB', size, colour).save(path)
    return path


def png_text(path):
    from PIL import Image
    with Image.open(path) as image:
        return dict(image.text), image.size


class Project(unittest.TestCase):
    def setUp(self):
        from storyboard import comfy_image_workflow, imageengine, imagegen, imagemodels, model
        self.graphs, self.engine, self.gen, self.models, self.model = comfy_image_workflow, imageengine, imagegen, imagemodels, model
        self.tmp = Path(tempfile.mkdtemp(prefix='story images '))
        board = model.Storyboard.create(self.tmp, 'Robot')
        board.doc['settings'].update(style='Ultra-realistic science fiction', aspect='2.39:1')
        self.robot = board.add_library_item('character', 'Unit 7', 'ivory armour, black joints',
                                            [picture(self.tmp / 'face.png', (200, 200, 190)),
                                             picture(self.tmp / 'body.png', (180, 190, 200))])
        self.nobody = board.add_library_item('character', 'Ghost', 'a pale figure')
        self.room = board.add_library_item('location', 'Activation room', 'amber strips',
                                           [picture(self.tmp / 'room.png', (90, 60, 20))])
        self.panel = board.add_panel(title='Wake', duration=4, references=[self.robot['id'], self.room['id']],
                                     prompt={'action': 'the robot opens its eyes', 'shotSize': 'close-up'})
        self.board = board
        self.options = imagegen.options_for(board, {'randomSeed': False, 'seed': 7})

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def entry(self, model_id):
        return self.engine.describe(self.models.get(model_id))


class PlanTests(Project):
    def test_character_views_from_pictures_and_from_a_description(self):
        plan = self.gen.plan(self.board, 'character', self.options, 10, '<image{n}>', item=self.robot['id'])
        on = [v['key'] for v in self.gen.CHARACTER_VIEWS if v['on']]
        self.assertEqual([r['key'] for r in plan], on)
        first = plan[0]
        self.assertEqual(len(first['references']), 2)
        self.assertEqual(first['mode'], 'edit')
        self.assertIn('Ultra-realistic science fiction. The same character as in <image1> and <image2> '
                      '(ivory armour, black joints).', first['prompt'])
        self.assertIn('facing the camera', first['prompt'])
        self.assertEqual((first['width'] % 32, first['height'] % 32), (0, 0))
        self.assertLess(first['width'], first['height'], 'full body views are upright')
        self.assertEqual(first['target'], {'kind': 'library', 'item': self.robot['id']})
        other = self.gen.plan(self.board, 'character', self.options, 3, 'image {n}', item=self.robot['id'], views=['back'])
        self.assertIn('as in image 1 and image 2', other[0]['prompt'])
        ghost = self.gen.plan(self.board, 'character', self.options, item=self.nobody['id'], views=['face'])
        self.assertEqual((ghost[0]['mode'], ghost[0]['references']), ('text', []))
        self.assertIn('Ghost (a pale figure). Close-up portrait', ghost[0]['prompt'])
        with self.assertRaises(self.model.StoryboardError):
            self.gen.plan(self.board, 'character', self.options, item=self.room['id'])
        with self.assertRaises(self.model.StoryboardError):
            self.gen.plan(self.board, 'character', self.options, item=self.robot['id'], views=['nope'])

    def test_counts_seeds_and_sizes(self):
        options = self.gen.options_for(self.board, {'randomSeed': False, 'seed': 40, 'count': 3, 'megapixels': 0.5})
        plan = self.gen.plan(self.board, 'character', options, item=self.robot['id'], views=['front', 'face'])
        self.assertEqual([(r['key'], r['variant'], r['seed']) for r in plan],
                         [('front', 1, 40), ('front', 2, 41), ('front', 3, 42), ('face', 1, 40), ('face', 2, 41), ('face', 3, 42)])
        self.assertEqual(len({r['id'] for r in plan}), 6)
        self.assertAlmostEqual(plan[0]['width'] * plan[0]['height'] / 1e6, 0.5, delta=0.06)
        self.assertEqual(self.gen.size_for(self.board, 'project', 1.0), (1536, 640))
        random_plan = self.gen.plan(self.board, 'character', self.gen.options_for(self.board, {'count': 2}),
                                    item=self.robot['id'], views=['front'])
        self.assertNotEqual(random_plan[0]['seed'], random_plan[1]['seed'])
        for bad in ({'count': 0}, {'megapixels': 9}, {'nope': 1}, {'characterViews': [{'text': 'x'}]}, {'freeFormat': '5:1'}):
            with self.assertRaises(self.model.StoryboardError):
                self.gen.options_for(self.board, bad)

    def test_place_with_and_without_a_character(self):
        empty = self.gen.plan(self.board, 'location', self.options, 10, '<image{n}>', item=self.room['id'], views=['wide'])[0]
        self.assertEqual(len(empty['references']), 1)
        self.assertIn('The same place as in <image1> (amber strips). Wide establishing shot', empty['prompt'])
        self.assertIn('No people', empty['prompt'])
        self.assertGreater(empty['width'], empty['height'] * 2, 'places use the project format')
        lived = self.gen.plan(self.board, 'location', self.options, 10, '<image{n}>', item=self.room['id'], views=['wide'],
                              character=self.robot['id'])[0]
        self.assertEqual([Path(p).name for p in lived['references']],
                         [Path(self.room['files'][0]).name] + [Path(f).name for f in self.robot['files']])
        self.assertIn('The character of <image2> and <image3> is in the place of <image1>', lived['prompt'])
        self.assertNotIn('No people', lived['prompt'])
        tight = self.gen.plan(self.board, 'location', self.options, 3, 'image {n}', item=self.room['id'], views=['wide'],
                              character=self.robot['id'])[0]
        self.assertEqual(len(tight['references']), 3)
        with self.assertRaises(self.model.StoryboardError):
            self.gen.plan(self.board, 'location', self.options, item=self.room['id'], character=self.nobody['id'])

    def test_shot_picture_uses_layout_character_and_place(self):
        render = picture(self.board.folder / 'assets' / 'layout.png', (120, 120, 120))
        self.panel['layout'].update(mode='3d', render='assets/layout.png')
        shot = self.gen.plan(self.board, 'panel', self.options, 10, '<image{n}>', panel=self.panel['id'])[0]
        self.assertEqual([Path(p).name for p in shot['references']],
                         [render.name] + [Path(f).name for f in self.robot['files']] + [Path(self.room['files'][0]).name])
        self.assertIn('<image1> is only a rough 3D layout: grey mannequins stand in', shot['prompt'])
        self.assertIn('Unit 7 is the character of <image2> and <image3> (ivory armour, black joints); keep it identical, '
                      'with the same body proportions', shot['prompt'])
        self.assertIn('The place is the one of <image4> (amber strips).', shot['prompt'])
        self.assertIn('replace every mannequin and every block', shot['prompt'])
        # a crowd of mannequins: the one that references a character brings its pictures without being
        # named by the panel; the others are said to be a chosen character, or what the text describes
        from storyboard import layout
        stage = layout.add_stage(self.board, 'Hall')
        layout.add_object(self.board, stage['id'], shape='mannequin', name='Hero', role='character', reference=self.robot['id'])
        for index in range(3):
            layout.add_object(self.board, stage['id'], shape='mannequin', name=f'Dormant {index}', role='object')
        crowd = self.board.add_panel(title='Hall', duration=4, prompt={'action': 'rows of dormant robots'})
        crowd['layout'].update(mode='3d', stage=stage['id'], render='assets/layout.png')
        self.assertEqual(self.gen.stage_figures(self.board, crowd), ([self.robot], 3))
        alone = self.gen.plan(self.board, 'panel', self.options, 10, '<image{n}>', panel=crowd['id'])[0]
        self.assertEqual(len(alone['references']), 3, 'layout and the two pictures of the staged character')
        self.assertIn('The other mannequins are the figures the text describes, not mannequins.', alone['prompt'])
        same = self.gen.plan(self.board, 'panel', self.options, 10, '<image{n}>', panel=crowd['id'], extras=self.robot['id'])[0]
        self.assertIn('Every other mannequin of the layout is another Unit 7, identical to <image2> and <image3>.', same['prompt'])
        self.assertNotIn('the figures the text describes', same['prompt'])
        tight = self.gen.plan(self.board, 'panel', self.options, 3, 'image {n}', panel=self.panel['id'])[0]
        self.assertEqual(len(tight['references']), 3, 'layout, one picture of the character, the place')
        self.assertIn('the character of image 2 (', tight['prompt'])
        # generated views come right after the identity picture, the full body first
        face = picture(self.board.folder / 'assets' / 'gen_face.png', (1, 2, 3))
        front = picture(self.board.folder / 'assets' / 'gen_front.png', (4, 5, 6))
        self.robot['files'] += ['assets/gen_face.png', 'assets/gen_front.png']
        self.board.doc['generations'] = {face.name: {'key': 'face'}, front.name: {'key': 'front'}}
        chosen = self.gen.character_pictures(self.board, self.robot, 3)
        self.assertEqual([p.name for p in chosen], [Path(self.robot['files'][0]).name, 'gen_front.png', 'gen_face.png'])
        self.assertIn('Close-up. The robot opens its eyes.', shot['prompt'])
        self.assertEqual(shot['target'], {'kind': 'panel', 'panel': self.panel['id']})
        self.assertEqual((shot['width'], shot['height']), (1536, 640))

    def test_free_prompt(self):
        text = self.gen.plan(None, 'free', self.gen.options_for(None, {'randomSeed': False}), prompt='a red door', format='1:1')[0]
        self.assertEqual((text['mode'], text['references'], text['width'], text['height']), ('text', [], 992, 992))
        refs = self.gen.plan(self.board, 'free', self.options, prompt='the robot at night',
                             references=[self.robot['id'], str(self.tmp / 'room.png')])[0]
        self.assertEqual(len(refs['references']), 2)
        with self.assertRaises(self.model.StoryboardError):
            self.gen.plan(self.board, 'free', self.options, prompt='  ')
        with self.assertRaises(self.model.StoryboardError):
            self.gen.plan(self.board, 'free', self.options, 1, prompt='x', references=[self.robot['id'], self.room['id']])


class GraphTests(Project):
    def test_qwen21_graph_from_references_and_from_text(self):
        plan = self.gen.plan(self.board, 'character', self.options, 10, '<image{n}>', item=self.robot['id'], views=['front', 'face'])
        entry = self.entry('qwen-image-2.1-int8')
        document = self.graphs.build(plan, entry, self.options).document()
        prompt = self.graphs.api_prompt(document)
        kinds = [n['class_type'] for n in prompt.values()]
        self.assertEqual(kinds.count('LoadImage'), 2, 'one loader per reference picture, shared by the views')
        self.assertEqual((kinds.count('TextEncodeQwenImage21'), kinds.count('KSampler'), kinds.count('SaveImage')), (2, 2, 2))
        self.assertEqual(prompt['1']['inputs'], {'unet_name': 'qwen_image_2.1_int8_convrot.safetensors', 'weight_dtype': 'default'})
        self.assertEqual(prompt['2']['inputs']['type'], 'qwen_image')
        encode = prompt['101']['inputs']
        self.assertEqual((encode['clip'], encode['vae'], encode['images.image_1'], encode['images.image_2']),
                         (['2', 0], ['3', 0], ['10', 0], ['11', 0]))
        self.assertEqual(encode['prompt'], plan[0]['prompt'])
        sampler = prompt['106']['inputs']
        self.assertEqual((sampler['seed'], sampler['steps'], sampler['cfg'], sampler['sampler_name'], sampler['scheduler']),
                         (7, 25, 1.0, 'euler', 'simple'))
        self.assertEqual((sampler['model'], sampler['positive'], sampler['negative'], sampler['latent_image']),
                         (['4', 0], ['101', 0], ['101', 1], ['105', 0]))
        self.assertEqual(prompt['105'], {'class_type': 'EmptyLatentImage', '_meta': {'title': 'EmptyLatentImage'},
                                         'inputs': {'width': plan[0]['width'], 'height': plan[0]['height'], 'batch_size': 1}})
        self.assertTrue(prompt['10']['inputs']['image'].startswith('cytools_images/'))
        self.assertEqual(self.graphs.save_nodes(document), {'108': 0, '208': 1})
        text = self.gen.plan(self.board, 'character', self.options, item=self.nobody['id'], views=['face'])
        text_prompt = self.graphs.api_prompt(self.graphs.build(text, entry, self.options).document())
        self.assertNotIn('vae', text_prompt['101']['inputs'])
        self.assertFalse(any(n['class_type'] == 'LoadImage' for n in text_prompt.values()))
        custom = self.graphs.api_prompt(self.graphs.build(text, entry, dict(self.options, steps=12, guidance=2.5)).document())
        self.assertEqual((custom['106']['inputs']['steps'], custom['106']['inputs']['cfg']), (12, 2.5))

    def test_edit_plus_and_text_families(self):
        plan = self.gen.plan(self.board, 'character', self.options, 3, 'image {n}', item=self.robot['id'], views=['front'])
        edit = self.entry('qwen-image-edit-2511-int8')
        fast = self.graphs.api_prompt(self.graphs.build(plan, edit, self.options).document())
        self.assertEqual(fast['5']['inputs']['lora_name'], 'Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors')
        self.assertEqual((fast['6']['class_type'], fast['6']['inputs']['shift'], fast['7']['class_type']),
                         ('ModelSamplingAuraFlow', 3.1, 'CFGNorm'))
        self.assertEqual((fast['106']['inputs']['steps'], fast['106']['inputs']['cfg'], fast['106']['inputs']['model']),
                         (4, 1.0, ['7', 0]))
        self.assertEqual(fast['101']['inputs']['image2'], ['11', 0])
        self.assertEqual(fast['103']['inputs'], {'reference_latents_method': 'index_timestep_zero', 'conditioning': ['101', 0]})
        self.assertEqual((fast['106']['inputs']['positive'], fast['106']['inputs']['negative']), (['103', 0], ['104', 0]))
        slow = self.graphs.api_prompt(self.graphs.build(plan, edit, dict(self.options, fast=False)).document())
        self.assertNotIn('5', slow)
        self.assertEqual((slow['106']['inputs']['steps'], slow['106']['inputs']['cfg'], slow['6']['inputs']['model']),
                         (40, 3.0, ['1', 0]))
        text = self.gen.plan(self.board, 'character', self.options, item=self.nobody['id'], views=['face'])
        base = self.graphs.api_prompt(self.graphs.build(text, self.entry('qwen-image-2512-fp8'), self.options).document())
        self.assertEqual((base['101']['class_type'], base['105']['class_type'], base['106']['inputs']['model']),
                         ('CLIPTextEncode', 'EmptySD3LatentImage', ['6', 0]))
        with self.assertRaises(self.model.StoryboardError):
            self.graphs.build(plan, self.entry('qwen-image-2512-fp8'), self.options)
        with self.assertRaises(self.model.StoryboardError):
            self.graphs.build(text, edit, self.options)
        many = [dict(plan[0], references=plan[0]['references'] * 2)]
        with self.assertRaises(self.model.StoryboardError):
            self.graphs.build(many, edit, self.options)

    def test_shot_follows_the_staging_through_the_controlnet(self):
        from storyboard import layout
        stage = layout.add_stage(self.board, 'Room')
        layout.add_object(self.board, stage['id'], shape='box', name='Wall', role='set', position=[0, 1, -2], scale=[4, 2, 0.2])
        layout.add_object(self.board, stage['id'], shape='mannequin', name='Hero', role='character', reference=self.robot['id'])
        layout.set_layout(self.board, self.panel['id'], mode='3d', stage=stage['id'])
        picture(self.board.folder / 'assets' / 'layout.png', (120, 120, 120))
        self.panel['layout']['render'] = 'assets/layout.png'
        # no ControlNet: automatic falls back to the staging picture; asking for the guide is refused
        fallback = self.gen.plan(self.board, 'panel', self.options, 10, '<image{n}>', False, panel=self.panel['id'])[0]
        self.assertNotIn('control', fallback)
        self.assertIn('rough 3D layout', fallback['prompt'])
        with self.assertRaises(self.model.StoryboardError):
            self.gen.plan(self.board, 'panel', dict(self.options, panelGuide='control'), 10, '<image{n}>', False,
                          panel=self.panel['id'])
        shot = self.gen.plan(self.board, 'panel', self.options, 10, '<image{n}>', True, panel=self.panel['id'])[0]
        self.assertEqual(shot['control'], {'panel': self.panel['id'], 'source': 'depth', 'strength': 0.8, 'end': 0.6,
                                           'blur': 'none'})
        self.assertNotIn('layout', shot['prompt'].lower(), 'no mannequin picture, no sentence about mannequins')
        self.assertEqual([Path(p).name for p in shot['references']],
                         [Path(f).name for f in self.robot['files']] + [Path(self.room['files'][0]).name])
        self.assertIn('Unit 7 is the character of <image1> and <image2>', shot['prompt'])
        both = self.gen.plan(self.board, 'panel', dict(self.options, panelGuide='both'), 10, '<image{n}>', True,
                             panel=self.panel['id'])[0]
        self.assertTrue('control' in both and 'rough 3D layout' in both['prompt'])
        # the control picture is rendered from the stage, then wired through ModelPatchLoader + ZImageFunControlnet
        self.engine.render_controls(self.board, [shot], self.tmp / 'controls')
        from PIL import Image
        with Image.open(shot['control']['file']) as image:
            self.assertEqual(image.size, (shot['width'], shot['height']))
            self.assertGreater(len(image.convert('L').getcolors(65536)), 2, 'a depth picture, not a flat one')
        entry = self.entry('qwen-image-2.1-int8')
        entry['files_by_role'].pop('patch', None)      # as on a machine where the ControlNet is not installed
        plain = self.graphs.api_prompt(self.graphs.build([shot], entry, self.options).document())
        self.assertFalse(any(n['class_type'] == 'ZImageFunControlnet' for n in plain.values()))
        entry = self.engine.describe(self.models.get('qwen-image-2.1-int8'), 'http://elsewhere')
        prompt = self.graphs.api_prompt(self.graphs.build([shot], entry, self.options).document())
        self.assertEqual(prompt['8'], {'class_type': 'ModelPatchLoader', '_meta': {'title': 'ControlNet (structure of the staging)'},
                                       'inputs': {'name': 'qwen_image_2.1_fun_controlnet_union_int8_convrot.safetensors'}})
        control = prompt['109']['inputs']
        self.assertEqual((control['strength'], control['start_percent'], control['end_percent']), (0.8, 0.0, 0.6))
        self.assertEqual((control['model'], control['model_patch'], control['vae']), (['4', 0], ['8', 0], ['3', 0]))
        self.assertEqual(prompt[control['image'][0]]['class_type'], 'LoadImage')
        self.assertEqual(prompt['106']['inputs']['model'], ['109', 0])
        other = self.graphs.api_prompt(self.graphs.build(
            [dict(shot, references=shot['references'][:3])], self.entry('qwen-image-edit-2511-int8'), self.options).document())
        self.assertFalse(any(n['class_type'] == 'ZImageFunControlnet' for n in other.values()), 'only Qwen-Image 2.1 has one')

    def test_loras_are_chained_behind_the_model(self):
        options = self.gen.options_for(self.board, {'randomSeed': False, 'seed': 7, 'loras': [
            {'file': 'style.safetensors', 'strength': 0.8}, {'file': 'off.safetensors', 'on': False},
            {'file': 'detail.safetensors', 'strength': -0.5, 'on': True}]})
        self.assertEqual(self.gen.active_loras(options), [('style.safetensors', 0.8), ('detail.safetensors', -0.5)])
        plan = self.gen.plan(self.board, 'character', options, 10, '<image{n}>', item=self.robot['id'], views=['front'])
        self.assertEqual(plan[0]['loras'], [['style.safetensors', 0.8], ['detail.safetensors', -0.5]])
        plain = self.gen.plan(self.board, 'character', self.options, 10, '<image{n}>', item=self.robot['id'], views=['front'])
        self.assertNotEqual(plan[0]['id'], plain[0]['id'])
        prompt = self.graphs.api_prompt(self.graphs.build(plan, self.entry('qwen-image-2.1-int8'), options).document())
        self.assertEqual(prompt['40']['inputs'], {'lora_name': 'style.safetensors', 'strength_model': 0.8, 'model': ['1', 0]})
        self.assertEqual(prompt['41']['inputs'], {'lora_name': 'detail.safetensors', 'strength_model': -0.5, 'model': ['40', 0]})
        self.assertEqual(prompt['4']['inputs']['model'], ['41', 0], 'then the cache node, then the sampler')
        edit = self.graphs.api_prompt(self.graphs.build(
            self.gen.plan(self.board, 'character', options, 3, 'image {n}', item=self.robot['id'], views=['front']),
            self.entry('qwen-image-edit-2511-int8'), options).document())
        self.assertEqual(edit['5']['inputs']['model'], ['41', 0], 'the few-step LoRA comes after the user LoRAs')
        for bad in ([{'file': '../x.safetensors'}], [{'file': 'a.safetensors', 'strength': 9}], [{'strength': 1}], 'x',
                    [{'file': f'{n}.safetensors'} for n in range(9)]):
            with self.assertRaises(self.model.StoryboardError):
                self.gen.options_for(self.board, {'loras': bad})
        # on the private engine a LoRA that is not in the folder is refused before anything starts
        from cytools_core import CyToolError
        saved = os.environ.pop('CYTOOLS_STORYBOARD_IMAGE_WORKER', None)
        try:
            with self.assertRaises(CyToolError) as caught:
                self.engine.check_loras(options)
            self.assertEqual(caught.exception.code, 'MissingModel')
            self.engine.check_loras(dict(options, server='http://elsewhere'))
        finally:
            if saved is not None:
                os.environ['CYTOOLS_STORYBOARD_IMAGE_WORKER'] = saved

    def test_catalogue_is_consistent(self):
        catalogue = self.models.catalog()
        self.assertEqual([m['id'] for m in catalogue.values() if m.get('default')], ['qwen-image-2.1-int8'])
        for entry in catalogue.values():
            self.assertIn(entry['loader'], self.graphs.FAMILIES + ('patch',))
            self.assertEqual(set(entry['roles'].values()), {f['path'] for f in entry['files']})
            for file in entry['files']:
                self.assertTrue(file['url'].startswith('https://huggingface.co/') and '/resolve/' in file['url'])
                self.assertRegex(file['url'].split('/resolve/')[1].split('/')[0], r'^[0-9a-f]{40}$', 'pinned to a commit')
                self.assertEqual(len(file['sha256']), 64)
            self.assertEqual(entry['downloadBytes'], sum(f['size'] for f in entry['files']))
        shared = {f['path'] for f in catalogue['qwen-image-edit-2511-int8']['files']} & \
            {f['path'] for f in catalogue['qwen-image-2512-fp8']['files']}
        self.assertEqual(shared, {'text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors', 'vae/qwen_image_vae.safetensors'})
        self.assertEqual(self.engine.reference_rules({'model': ''}), (10, '<image{n}>'))
        self.assertEqual(self.engine.reference_rules({'model': 'qwen-image-edit-2511-int8'}), (3, 'image {n}'))


class RemoveSharedFilesTests(unittest.TestCase):
    def test_remove_keeps_files_another_installed_model_uses(self):
        from storyboard import imagemodels
        tmp = Path(tempfile.mkdtemp(prefix='story models '))
        saved = (imagemodels.CATALOG_PATH, imagemodels.ROOT, imagemodels.MODELS, imagemodels.STATE_DIR, dict(imagemodels._cache))
        try:
            files = {'a': ['unet/a.bin', 'vae/shared.bin'], 'b': ['unet/b.bin', 'vae/shared.bin']}
            catalogue = {'models': [{'id': key, 'backend': 'comfyui', 'family': 'image', 'name': key, 'directory': 'data/models/comfyui',
                                     'files': [{'path': p, 'size': 4, 'sha256': None} for p in paths], 'downloadBytes': 8}
                                    for key, paths in files.items()]}
            (tmp / 'catalog.json').write_text(json.dumps(catalogue), encoding='utf-8')
            imagemodels.CATALOG_PATH, imagemodels.ROOT = tmp / 'catalog.json', tmp
            imagemodels.MODELS, imagemodels.STATE_DIR = tmp / 'data' / 'models', tmp / 'state'
            imagemodels._cache.clear()
            root = tmp / 'data/models/comfyui'
            for path in ('unet/a.bin', 'unet/b.bin', 'vae/shared.bin'):
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_bytes(b'1234')
            self.assertTrue(imagemodels.status('a')['installed'] and imagemodels.status('b')['installed'])
            result = imagemodels.remove('a')
            self.assertEqual((result['freedBytes'], result['keptShared']), (4, ['vae/shared.bin']))
            self.assertTrue(imagemodels.status('b')['installed'])
            self.assertEqual(imagemodels.status('a')['state'], 'Partial')
            self.assertEqual(imagemodels.remove('b')['freedBytes'], 8)
            self.assertFalse((root / 'vae/shared.bin').exists())
        finally:
            imagemodels.CATALOG_PATH, imagemodels.ROOT, imagemodels.MODELS, imagemodels.STATE_DIR = saved[:4]
            imagemodels._cache.clear()
            imagemodels._cache.update(saved[4])
            shutil.rmtree(tmp, ignore_errors=True)


class StateFileTests(unittest.TestCase):
    def test_state_survives_a_reader_holding_the_file(self):
        """On Windows a state file open for reading cannot be replaced: the writer waits for the
        reader, and a progress tick is dropped instead of failing the download."""
        from storyboard import imagemodels
        tmp = Path(tempfile.mkdtemp(prefix='story state '))
        saved = imagemodels.STATE_DIR
        try:
            imagemodels.STATE_DIR = tmp
            imagemodels.write_state('m', state='Downloading')
            handle = open(imagemodels.state_path('m'), 'r', encoding='utf-8')
            released = threading.Timer(0.3, handle.close)
            released.start()
            imagemodels.write_state('m', _essential=False, progress={'doneBytes': 1})     # never raises
            imagemodels.write_state('m', state='Installed')                                # waits for the reader
            released.join()
            self.assertEqual(imagemodels.read_state('m')['state'], 'Installed')
            self.assertEqual(list(tmp.glob('*.tmp*')), [], 'no temporary file is left behind')
        finally:
            imagemodels.STATE_DIR = saved
            shutil.rmtree(tmp, ignore_errors=True)


class EngineTests(unittest.TestCase):
    """The operations through the real runtime and a real worker process (the stand-in)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix='story engine '))
        os.environ['CYTOOLS_STORYBOARD_PROJECTS'] = str(cls.tmp / 'projects')
        os.environ['CYTOOLS_STORYBOARD_IMAGE_WORKER'] = str(APP / 'tests' / 'fake_image_worker.py')
        import importlib
        import tool
        cls.tool = importlib.reload(tool)
        cls.runtime = cls.tool.create_runtime(cls.tmp / 'jobs').start()
        cls.actor = cls.runtime.authenticate(cls.runtime.create_client('tests')['token'])
        cls.session = cls.runtime.create_session(cls.actor, temporary=False)['sessionId']
        from storyboard import model
        board = model.Storyboard.create(cls.tmp / 'projects', 'Robot')
        cls.robot = board.add_library_item('character', 'Unit 7', 'ivory armour',
                                           [picture(cls.tmp / 'face.png', (200, 200, 190))])
        cls.room = board.add_library_item('location', 'Room', 'amber strips')
        cls.panel = board.add_panel(title='Wake', duration=4, references=[cls.robot['id']],
                                    prompt={'action': 'the robot opens its eyes'})
        board.save()
        cls.project = str(board.folder)

    @classmethod
    def tearDownClass(cls):
        cls.runtime.close()
        for name in ('CYTOOLS_STORYBOARD_PROJECTS', 'CYTOOLS_STORYBOARD_IMAGE_WORKER', 'FAKE_IMAGE_STEP_SECONDS'):
            os.environ.pop(name, None)
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def call(self, operation, parameters, timeout=120):
        job = self.runtime.submit(self.actor, self.session, operation, parameters)
        job = self.runtime.wait(self.actor, job['jobId'], timeout=timeout)
        self.assertEqual(job['state'], 'Completed', job.get('error'))
        return job['outputs']

    def board(self):
        from storyboard import model
        return model.Storyboard.load(self.project)

    def test_1_character_sheet_kept_in_the_project_and_model_kept_loaded(self):
        options = {'randomSeed': False, 'seed': 11, 'megapixels': 0.5}
        first = self.call('generate_images', {'project': self.project, 'recipe': 'character', 'item': self.robot['id'],
                                              'views': ['front', 'face'], 'options': options})
        self.assertEqual([p['key'] for p in first['pictures']], ['front', 'face'])
        self.assertEqual(first['kept'], [], 'nothing enters the project unless asked')
        text, size = png_text(first['pictures'][0]['file'])
        self.assertEqual(size, (first['pictures'][0]['width'] // 8, first['pictures'][0]['height'] // 8))
        self.assertIn('The same character as in <image1> (ivory armour)', text['prompt'])
        self.assertEqual((text['model'], text['unet'], text['steps'], text['cfg']),
                         ('qwen-image-2.1-int8', 'qwen_image_2.1_int8_convrot.safetensors', '25', '1.0'))
        self.assertTrue(Path(first['pictures'][0]['file'] + '.json').is_file())
        status = self.call('image_engine_status', {})
        self.assertTrue(status['worker']['alive'])
        self.assertEqual(status['worker']['resident']['models'], ['qwen-image-2.1-int8'])
        self.assertEqual({m['id'] for m in status['models']},
                         {'qwen-image-2.1-int8', 'qwen-image-2.1-controlnet-int8', 'qwen-image-edit-2511-int8',
                          'qwen-image-2512-fp8'})
        pid = self.runtime.image_engine.host.process.pid
        second = self.call('generate_images', {'project': self.project, 'recipe': 'character', 'item': self.robot['id'],
                                               'views': ['back'], 'options': options, 'keep': True})
        self.assertEqual(self.runtime.image_engine.host.process.pid, pid, 'the same worker served both jobs')
        board = self.board()
        robot = board.library_item(self.robot['id'])
        self.assertEqual(len(robot['files']), 2)
        self.assertEqual(second['kept'], [robot['files'][1]])
        recipe = board.doc['generations'][Path(robot['files'][1]).name]
        self.assertEqual((recipe['seed'], recipe['key'], recipe['mode'], recipe['target']),
                         (11, 'back', 'edit', {'kind': 'library', 'item': self.robot['id']}))
        self.assertEqual(recipe['references'], [robot['files'][0]], 'references are stored relative to the project')
        self.assertEqual(recipe['engine']['model'], 'qwen-image-2.1-int8')
        kept = self.call('keep_generated_image', {'project': self.project, 'file': first['pictures'][1]['file']})
        self.assertEqual(len(self.board().library_item(self.robot['id'])['files']), 3)
        self.assertEqual(kept['target']['item'], self.robot['id'])

    def test_1b_a_job_does_not_undo_what_was_kept_while_it_ran(self):
        """The window keeps pictures while another generation runs; when that job ends (even one that
        remembers its options) the project must still hold them."""
        os.environ['FAKE_IMAGE_STEP_SECONDS'] = '0.05'
        self.runtime.image_engine.unload()
        try:
            job = self.runtime.submit(self.actor, self.session, 'generate_images', {
                'project': self.project, 'recipe': 'character', 'item': self.robot['id'], 'views': ['profile'],
                'options': {'randomSeed': False, 'megapixels': 0.5}, 'save_options': True})
            time.sleep(0.3)
            board = self.board()
            board.library_item(self.robot['id'])['description'] = 'changed while the job ran'
            board.save()
            ended = self.runtime.wait(self.actor, job['jobId'], timeout=60)
            self.assertEqual(ended['state'], 'Completed', ended.get('error'))
            after = self.board()
            self.assertEqual(after.library_item(self.robot['id'])['description'], 'changed while the job ran')
            self.assertEqual(after.doc['settings']['imagegen']['megapixels'], 0.5)
        finally:
            os.environ.pop('FAKE_IMAGE_STEP_SECONDS', None)
            self.runtime.image_engine.unload()

    def test_2_shot_picture_text_picture_and_other_models(self):
        shot = self.call('generate_images', {'project': self.project, 'recipe': 'panel', 'panel': self.panel['id'],
                                             'keep': True, 'options': {'randomSeed': False}})
        board = self.board()
        panel = board.find(self.panel['id'])[2]
        self.assertEqual(panel['images'][0], {'file': shot['kept'][0], 'role': 'first', 'caption': ''})
        from storyboard import h3film
        film = h3film.build(board, {'grouping': 'panel'}, preview=True)[0]
        self.assertEqual(film['segments'][0]['pictures'][1], '<Picture 2> first, shot 1', 'H3 gets the generated frame')
        place = self.call('generate_images', {'project': self.project, 'recipe': 'location', 'item': self.room['id'],
                                              'views': ['wide'], 'options': {'randomSeed': False}})
        self.assertEqual(place['pictures'][0]['mode'], 'text', 'a place without a picture is made from its description')
        self.assertEqual(png_text(place['pictures'][0]['file'])[0]['references'], '')
        fast = self.call('generate_images', {'recipe': 'free', 'prompt': 'a red door',
                                             'options': {'textModel': 'qwen-image-2512-fp8', 'randomSeed': False}})
        text = png_text(fast['pictures'][0]['file'])[0]
        self.assertEqual((text['unet'], text['steps'], text['lora']), ('qwen_image_2512_fp8_e4m3fn.safetensors', '4', 'True'))
        self.assertEqual(fast['project'], '')
        job = self.runtime.submit(self.actor, self.session, 'generate_images',
                                  {'recipe': 'free', 'prompt': 'x', 'references': [str(self.tmp / 'face.png')],
                                   'options': {'model': 'qwen-image-2512-fp8'}})
        failed = self.runtime.wait(self.actor, job['jobId'], timeout=60)
        self.assertEqual((failed['state'], failed['error']['code']), ('Failed', 'InvalidParameters'))
        job = self.runtime.submit(self.actor, self.session, 'generate_images', {'recipe': 'character', 'item': 'x'})
        self.assertEqual(self.runtime.wait(self.actor, job['jobId'], timeout=60)['error']['code'], 'InvalidParameters')

    def test_3_cancel_keeps_the_worker_and_unload_stops_it(self):
        self.call('generate_images', {'recipe': 'free', 'prompt': 'warm up'})
        pid = self.runtime.image_engine.host.process.pid
        os.environ['FAKE_IMAGE_STEP_SECONDS'] = '0.2'
        self.runtime.image_engine.unload()      # a new worker reads the slower pace
        job = self.runtime.submit(self.actor, self.session, 'generate_images',
                                  {'recipe': 'free', 'prompt': 'slow', 'options': {'count': 4}})
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            state = self.runtime.get_job(self.actor, job['jobId'])
            if (state.get('progress') or {}).get('percent', 0) > 3:
                break
            time.sleep(0.05)
        slow_pid = self.runtime.image_engine.host.process.pid
        self.assertNotEqual(slow_pid, pid)
        self.runtime.cancel(self.actor, job['jobId'])
        ended = self.runtime.wait(self.actor, job['jobId'], timeout=60)
        self.assertEqual(ended['state'], 'Cancelled')
        host = self.runtime.image_engine.host
        self.assertTrue(host.process is not None and host.process.poll() is None and host.process.pid == slow_pid,
                        'cancelling stops the picture, not the engine')
        os.environ.pop('FAKE_IMAGE_STEP_SECONDS')
        after = self.call('unload_image_model', {})
        self.assertFalse(after['worker']['alive'])

    def test_4_workflows_for_comfyui(self):
        target = self.tmp / 'out' / 'comfy'
        result = self.call('export_image_workflows', {'project': self.project, 'recipe': 'character', 'item': self.robot['id'],
                                                      'views': ['front', 'back'], 'folder': str(target), 'name': 'unit7',
                                                      'options': {'randomSeed': False, 'seed': 3}})
        self.assertEqual(sorted(Path(f).name for f in result['files']), ['unit7.json', 'unit7_api.json'])
        document = json.loads((target / 'unit7.json').read_text(encoding='utf-8'))
        api = json.loads((target / 'unit7_api.json').read_text(encoding='utf-8'))
        loads = [n for n in document['nodes'] if n['type'] == 'LoadImage']
        self.assertTrue(all((target / n['widgets_values'][0]).is_file() for n in loads), 'reference pictures are next to it')
        self.assertEqual(sum(n['type'] == 'KSampler' for n in document['nodes']), 2)
        self.assertTrue(any(n['type'] == 'MarkdownNote' and 'diffusion_models/qwen_image_2.1_int8_convrot.safetensors'
                            in n['widgets_values'][0] for n in document['nodes']))
        self.assertEqual(api['106']['inputs']['seed'], 3)
        self.assertNotIn('9', api, 'the note is not part of the prompt')
        plan = self.call('plan_images', {'project': self.project, 'recipe': 'character', 'item': self.robot['id'],
                                         'views': ['front'], 'options': {'randomSeed': False, 'seed': 3}})
        self.assertEqual(plan['requests'][0]['prompt'], api['101']['inputs']['prompt'])


if __name__ == '__main__':
    unittest.main()

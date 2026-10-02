"""MiniMax H3 film export: frame grid, continuity, pictures per segment, prompts, workflows.

The frame rules are those of Timeline Director's _prepare_timeline_segments (checked here
the same way); tests/film_real_check in CyTools_MiniMaxH3 runs the real planner on an export.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))


# one segment per panel, continuity across cuts: the rules these tests were written for
PER_PANEL = {'grouping': 'panel', 'overlapOnCuts': True}


def image(path, colour):
    from PIL import Image
    Image.new('RGB', (64, 36), colour).save(path)
    return path


def timeline_director_rules(timeline):
    """Mirror of Timeline Director's window validation (commit a81f13b)."""
    config = timeline['segmentConfig']
    assert config['mode'] == 'timeline' and 1 <= config['count'] <= 64 and len(config['segments']) == config['count']
    previous_start = previous_end = 0
    lengths = []
    for index, segment in enumerate(config['segments']):
        start, end = segment['startFrame'], segment['endFrame']
        length = end - start
        assert start >= 0 and length >= 5 and (length - 5) % 17 == 0 and length <= 3592, (index, length)
        overlap = previous_end - start if index else 0
        if index:
            valid = 1 if overlap < 5 else overlap - ((overlap - 5) % 17)
            assert start > previous_start and end > previous_end and 0 <= overlap < min(length, lengths[-1])
            assert not overlap or valid == overlap, overlap
        else:
            assert start == 0
        assert segment['prompt'].strip()
        assert len(segment['images']) <= 9
        lengths.append(length)
        previous_start, previous_end = start, end
    known = {asset['id'] for asset in timeline['images']}
    assert all(i in known for s in config['segments'] for i in s['images'])


class FilmExportTests(unittest.TestCase):
    def setUp(self):
        from storyboard import h3film, model
        self.h3film, self.model = h3film, model
        self.tmp = Path(tempfile.mkdtemp(prefix='story film '))
        board = model.Storyboard.create(self.tmp, 'Robot')
        board.doc['settings']['style'] = 'Ultra-realistic science fiction'
        self.robot = board.add_library_item('character', 'Unit 7', 'ivory armour, black joints',
                                            [image(self.tmp / 'face.png', (200, 200, 190))])
        self.room = board.add_library_item('location', 'Activation room', 'amber strips',
                                           [image(self.tmp / 'room.png', (90, 60, 20))])
        self.nobody = board.add_library_item('character', 'Guard', '', [image(self.tmp / 'guard.png', (20, 20, 20))])
        self.board = board

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def panel(self, title, duration, refs=(), transition='cut', images=()):
        panel = self.board.add_panel(title=title, duration=duration, references=list(refs),
                                     prompt={'action': f'{title} happens'},
                                     images=[{'file': str(f), 'role': r} for f, r in images])
        self.board.update_panel(panel['id'], transition={'type': transition, 'duration': 0.5})
        return panel

    def test_grid_overlaps_and_rules(self):
        h = self.h3film
        self.assertEqual([h.segment_length(x) for x in (1, 120, 144, 145)], [5, 124, 141, 141])
        self.assertEqual([h.valid_overlap(x) for x in (0, 3, 39, 40, 60)], [0, 1, 39, 39, 56])
        self.panel('Wake', 9.4, [self.robot['id']])
        self.panel('Look', 12.3, [self.robot['id'], self.room['id']])
        self.panel('Hands', 1.0, [self.robot['id']], transition='fade to black')
        self.panel('Door', 4.5, [self.robot['id']], transition='crossfade')
        self.panel('Hall', 7.0)
        film, _, warnings = h.build(self.board, PER_PANEL)
        timeline_director_rules(film['timeline'])
        segments = film['segments']
        self.assertEqual([s['overlap'] for s in segments], [0, 39, 39, 0, 39])
        # visible duration = requested, within half a 17-frame step
        for segment in segments:
            self.assertLessEqual(abs(segment['seconds'] - segment['requestedSeconds']), 8.5 / 24 + 1e-9)
        self.assertEqual(film['frames'], segments[-1]['endFrame'])
        self.assertEqual((film['width'], film['height']), (960, 544))
        self.assertFalse(warnings)
        no_cut = h.build(self.board, {'grouping': 'panel', 'overlapOnCuts': False, 'overlapOnFades': True})[0]['segments']
        # A panel's transition is the seam after it: Wake cut, Look cut, Hands fade, Door crossfade. Hands lasts
        # 1 s (56-frame segment with 39 carried, 17 new), so the next overlap is cut down to fit inside it.
        self.assertEqual([s['overlap'] for s in no_cut], [0, 0, 0, 5, 39])
        timeline_director_rules(h.build(self.board, {'grouping': 'panel', 'overlapOnCuts': False})[0]['timeline'])
        wide = h.build(self.board, dict(PER_PANEL, shortEdge=768))[0]
        self.assertEqual((wide['width'], wide['height']), (1344, 768))

    def test_pictures_numbering_and_prompts(self):
        sketch = image(self.tmp / 'sketch.png', (10, 120, 10))
        first = image(self.tmp / 'first.png', (10, 10, 120))
        self.panel('Wake', 5, [self.robot['id'], self.room['id']], images=[(sketch, 'sketch'), (first, 'first')])
        self.panel('Guard', 5, [self.nobody['id']])
        film, files, _ = self.h3film.build(self.board, PER_PANEL)
        one, two = film['segments']
        self.assertEqual(one['pictures'], ['<Picture 1> Unit 7', '<Picture 2> Activation room',
                                           '<Picture 3> first, shot 1'])
        prompt = one['prompt']
        self.assertIn('Ultra-realistic science fiction.', prompt)
        self.assertIn('<Picture 1> is Unit 7 (ivory armour, black joints).', prompt)
        self.assertIn('<Picture 2> is Activation room (amber strips).', prompt)
        self.assertIn('<Picture 3> is the first frame of shot 1.', prompt)
        self.assertNotIn('continues directly', prompt)
        self.assertNotIn('Shot 1', prompt, 'no shot header for a single shot')
        self.assertIn('It continues directly from the previous shot.', two['prompt'])
        self.assertEqual(two['pictures'], ['<Picture 1> Guard'], 'the identity scope is the panel by default')
        everyone = self.h3film.build(self.board, dict(PER_PANEL, identityScope='film', shotPictures='all'))[0]['segments']
        self.assertEqual(everyone[1]['pictures'], ['<Picture 1> Unit 7', '<Picture 2> Guard'])
        self.assertEqual(len(everyone[0]['pictures']), 5, 'Unit 7, Guard, room, first, sketch')
        timeline = film['timeline']
        self.assertEqual(len(timeline['images']), len(files), 'each picture file once')
        self.assertEqual(timeline['segmentConfig']['segments'][0]['images'][0],
                         timeline['segmentConfig']['segments'][0]['images'][0])
        custom = self.h3film.build(self.board, dict(PER_PANEL, identityText='Face of {name} = <Picture {n}>.',
                                                     continuityText=''))[0]['segments']
        self.assertIn('Face of Unit 7 = <Picture 1>.', custom[0]['prompt'])
        self.assertNotIn('continues directly', custom[1]['prompt'])

    def test_several_pictures_per_character(self):
        more = image(self.tmp / 'profile.png', (150, 150, 140))
        self.board.update_library_item(self.robot['id'], files=[self.board.folder / self.robot['files'][0], more])
        self.panel('Wake', 5, [self.robot['id'], self.room['id']])
        one = self.h3film.build(self.board)[0]['segments'][0]
        self.assertEqual(one['pictures'], ['<Picture 1> Unit 7', '<Picture 2> Activation room'])
        two = self.h3film.build(self.board, {'identityPictures': 2})[0]['segments'][0]
        self.assertEqual(two['pictures'], ['<Picture 1> Unit 7', '<Picture 2> Unit 7 (2)', '<Picture 3> Activation room'])
        self.assertIn('<Picture 2> is Unit 7 again, from another angle.', two['prompt'])
        with self.assertRaises(self.model.StoryboardError):
            self.h3film.build(self.board, {'identityPictures': 0})

    def test_nine_pictures_at_most_and_bad_options(self):
        refs = []
        for index in range(11):
            item = self.board.add_library_item('object', f'Prop {index}', '',
                                               [image(self.tmp / f'prop{index}.png', (index * 20, 0, 0))])
            refs.append(item['id'])
        self.panel('Clutter', 5, refs)
        film, _, warnings = self.h3film.build(self.board)
        self.assertEqual(len(film['segments'][0]['pictures']), 9)
        self.assertIn('2 picture(s) left out', warnings[0])
        for bad in ({'overlapFrames': 40}, {'identityScope': 'x'}, {'nope': 1}, {'objectText': '{unknown}'}):
            with self.assertRaises(self.model.StoryboardError):
                self.h3film.build(self.board, bad)

    def media(self, name, kind, frequency=200):
        import subprocess
        import imageio_ffmpeg
        path = self.tmp / name
        source = {'video': ['-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24', '-t', '20', '-pix_fmt', 'yuv420p'],
                  'silent': ['-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24', '-t', '2', '-pix_fmt', 'yuv420p', '-metadata', f'title={name}'],
                  'talking': ['-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=24', '-f', 'lavfi', '-i',
                              'sine=frequency=300', '-t', '3', '-pix_fmt', 'yuv420p', '-shortest'],
                  'audio': ['-f', 'lavfi', '-i', f'sine=frequency={frequency}', '-t', '4']}[kind]
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-v', 'error', *source, str(path)], check=True)
        return path

    def test_videos_and_sounds_per_segment(self):
        long_video = self.board.add_library_item('video', 'Walk', 'tired walk', [self.media('walk.mp4', 'video')])
        talking = self.board.add_library_item('video', 'Speech', '', [self.media('talk.mp4', 'talking')])
        rain = self.board.add_library_item('audio', 'Rain', 'on stone', [self.media('rain.wav', 'audio')])
        voice = self.media('voice.wav', 'audio', 330)
        self.board.update_library_item(self.robot['id'], files=[self.board.folder / self.robot['files'][0], voice])
        self.panel('Wake', 5, [self.robot['id']])
        self.panel('Walk', 6, [self.robot['id'], long_video['id'], talking['id'], rain['id']])
        film, files, warnings = self.h3film.build(self.board, dict(PER_PANEL, videoSound=True, maxReferenceSeconds=10))
        timeline_director_rules(film['timeline'])
        one, two = film['segments']
        self.assertEqual(one['videos'], [])
        self.assertEqual(one['audios'], ['<Audio 1> voice of Unit 7'], 'the voice follows the character')
        self.assertEqual(two['videos'], ['<Video 1> Walk', '<Video 2> Speech'])
        self.assertEqual(two['audios'], ['<Audio 1> voice of Unit 7', '<Audio 2> Rain', '<Audio 3> sound of Speech'],
                         'the silent-free video gives its sound; voices first')
        self.assertIn('<Video 1> is a motion reference for Walk', two['prompt'])
        self.assertIn('<Audio 1> is the voice of Unit 7.', two['prompt'])
        self.assertIn('<Audio 3> is the sound of <Video 2> (Speech).', two['prompt'])
        clips = film['timeline']['videoClips']
        self.assertEqual({c['cytoolsSegment'] for c in clips}, {2})
        window = film['timeline']['segmentConfig']['segments'][1]
        for clip in clips:
            self.assertFalse(clip['hasAudio'])
            self.assertEqual(clip['referenceMode'], 'edit')
            self.assertAlmostEqual(clip['start'] * 24, window['startFrame'] + two['overlap'], places=3,
                                   msg='after the carried frames')
            self.assertLessEqual((clip['start'] + clip['duration']) * 24, window['endFrame'] + 1e-6)
        self.assertLessEqual(clips[0]['duration'], 10, 'cut to the longest reference')
        sounds = {a['name']: a for a in film['timeline']['audios']}
        self.assertEqual(sounds['Rain']['audioMode'], 'reference')
        self.assertNotIn('duration', sounds['Rain'], '4 s: kept whole')
        self.assertTrue(all(name.startswith(('images/', 'media/')) for name in files))
        target = self.tmp / 'out' / 'media film'
        self.h3film.export_film(self.board, target, {'videoSound': True})
        written = json.loads((target / 'film.json').read_text(encoding='utf-8'))
        for key in ('audios', 'videoClips'):
            self.assertTrue(all((target / a['file']).is_file() for a in written['timeline'][key]))
        stock = json.loads((target / 'workflow_timeline_director.json').read_text(encoding='utf-8'))
        pasted = json.loads(next(n for n in stock['nodes'] if n['type'] == 'MiniMaxH3TimelinePlanner')['widgets_values'][3])
        self.assertEqual(pasted['videoClips'], [], 'global clips would leak into the other segments')
        self.assertTrue(all(a['file'].startswith('cytools_film/media film/') for a in pasted['audios']))
        self.assertIn('Vidéos de référence', (target / 'LISEZ-MOI.txt').read_text(encoding='utf-8'))
        off = self.h3film.build(self.board, {'includeVideos': False, 'includeVoices': False, 'includeAudio': False})[0]
        self.assertEqual((off['timeline']['videoClips'], off['timeline']['audios']), ([], []))

    def test_twelve_references_at_most(self):
        props = [self.board.add_library_item('object', f'Prop {i}', '', [image(self.tmp / f'p{i}.png', (i * 20, 9, 9))])['id']
                 for i in range(9)]
        videos = [self.board.add_library_item('video', f'V{i}', '', [self.media(f'v{i}.mp4', 'silent')])['id']
                  for i in range(3)]
        sounds = [self.board.add_library_item('audio', f'A{i}', '', [self.media(f'a{i}.wav', 'audio', 400 + 50 * i)])['id']
                  for i in range(4)]
        self.panel('Busy', 5, props + videos + sounds)
        film, _, warnings = self.h3film.build(self.board)
        segment = film['segments'][0]
        self.assertEqual((len(segment['pictures']), len(segment['videos']), len(segment['audios'])), (6, 3, 3))
        self.assertTrue(any('left out' in w for w in warnings))

    def test_panels_grouped_by_sequence(self):
        h = self.h3film
        first = self.board.doc['sequences'][0]
        self.panel('Dark', 3, [self.robot['id'], self.room['id']])
        self.panel('Eyes', 3, [self.robot['id']])
        lines = self.board.add_panel(first['id'], title='Voice', duration=5.5, references=[self.robot['id']],
                                     prompt={'action': 'the interface stabilizes', 'sound': 'soft tones',
                                             'dialogue': [{'speaker': self.nobody['id'], 'line': 'Hello...', 'offScreen': True},
                                                          {'speaker': self.nobody['id'], 'line': 'Stay calm.', 'offScreen': True}]})
        self.board.update_panel(lines['id'], transition={'type': 'crossfade', 'duration': 0.5})
        second = self.board.add_sequence('Hall')
        for title, seconds in (('Door', 4), ('Walk', 9), ('Glass', 6), ('Crowd', 5)):
            panel = self.board.add_panel(second['id'], title=title, duration=seconds, prompt={'action': title.lower()})
            self.board.update_panel(panel['id'], transition={'type': 'cut', 'duration': 0.5})
        film, _, warnings = h.build(self.board)
        timeline_director_rules(film['timeline'])
        segments = film['segments']
        # sequence 1 (11.5 s) in one window; sequence 2 (24 s) balanced into two windows, never 20 + 4
        self.assertEqual([[s['title'] for s in seg['shots']] for seg in segments],
                         [['Dark', 'Eyes', 'Voice'], ['Door', 'Walk'], ['Glass', 'Crowd']])
        self.assertEqual(segments[0]['title'], 'Sequence 1')
        self.assertEqual([s['overlap'] for s in segments], [0, 39, 0], 'continuity after the crossfade only')
        prompt = segments[0]['prompt']
        self.assertIn('Shot 1 (0.0-3.0 s):', prompt)
        self.assertIn('Cut. Shot 2 (3.0-6.0 s):', prompt)
        self.assertIn('Guard (off screen) says: "Hello... Stay calm."', prompt, 'one speech per speaker')
        self.assertIn('Sound: Soft tones.', prompt)
        for noise in ('frames', 'final edit', 'precedence', 'overlap'):
            self.assertNotIn(noise, prompt.lower())
        self.assertIn('It continues directly from the previous shot.', segments[1]['prompt'])
        self.assertIn('Dissolve.', h.build(self.board, {'grouping': 'film', 'maxSegmentSeconds': 40})[0]['segments'][0]['prompt'])
        self.assertAlmostEqual(sum(s['seconds'] for s in segments), film['frames'] / 24)
        capped = h.build(self.board, {'maxShotsPerSegment': 1})[0]['segments']
        self.assertEqual(len(capped), 7)
        short = h.build(self.board, {'maxSegmentSeconds': 10})[0]['segments']
        self.assertTrue(all(s['requestedSeconds'] <= 10 or len(s['shots']) == 1 for s in short))
        with self.assertRaises(self.model.StoryboardError):
            h.build(self.board, {'grouping': 'scene'})

    def test_long_panel_warns(self):
        self.panel('Long take', 20)
        _, _, warnings = self.h3film.build(self.board)
        self.assertIn('longer than the 15 s', warnings[0])

    def test_export_folder_and_workflows(self):
        self.panel('Wake', 5, [self.robot['id']])
        self.panel('Look', 5, [self.robot['id'], self.room['id']])
        target = self.tmp / 'out' / 'robot_film'
        result = self.h3film.export_film(self.board, target)
        film = json.loads((target / 'film.json').read_text(encoding='utf-8'))
        self.assertEqual(film['format'], 'cytools-h3-film')
        for asset in film['timeline']['images']:
            self.assertTrue((target / asset['file']).is_file())
            self.assertEqual((asset['width'], asset['height']), (64, 36))
        disk = json.loads((target / 'workflow_cytools_film.json').read_text(encoding='utf-8'))
        sampler = next(n for n in disk['nodes'] if n['type'] == 'CyH3FilmSampler')
        self.assertEqual(sampler['widgets_values'][:4], [42, 'fixed', True, 'match'],
                         "the editor adds 'control after generate' behind the seed")
        plan = next(n for n in disk['nodes'] if n['type'] == 'CyH3FilmPlan')
        self.assertEqual(plan['widgets_values'][0], 'cytools_film/robot_film/film.json')
        self.assertEqual(len(disk['links']), 8)
        stock = json.loads((target / 'workflow_timeline_director.json').read_text(encoding='utf-8'))
        planner = next(n for n in stock['nodes'] if n['type'] == 'MiniMaxH3TimelinePlanner')
        pasted = json.loads(planner['widgets_values'][3])
        self.assertTrue(all(a['file'].startswith('cytools_film/robot_film/images/') for a in pasted['images']))
        self.assertIn('input/cytools_film/robot_film/', (target / 'LISEZ-MOI.txt').read_text(encoding='utf-8'))
        self.assertEqual(result['frames'], film['frames'])

    def test_workflow_for_a_comfyui_input_folder(self):
        from storyboard import comfy_workflow
        self.panel('Wake', 5, [self.robot['id']])
        drive_input = self.tmp / 'Mon Drive' / 'ComfyUI' / 'input' / 'cytools_film'
        target = self.h3film.films_folder_target(self.board, drive_input)
        self.h3film.export_film(self.board, target)
        disk = json.loads((target / 'workflow_cytools_film.json').read_text(encoding='utf-8'))
        plan = next(n for n in disk['nodes'] if n['type'] == 'CyH3FilmPlan')
        self.assertEqual(plan['widgets_values'][0], f'cytools_film/{target.name}/film.json',
                         'the path the node reads, relative to ComfyUI/input')
        self.assertFalse(any(n['type'] == 'ModelPatchLoader' for n in disk['nodes']), 'no control: no ControlNet')
        self.assertEqual(self.h3film.comfy_input_folder(self.tmp / 'ComfyUI' / 'input' / 'films' / 'a'), 'films/a')
        self.assertEqual(self.h3film.comfy_input_folder(self.tmp / 'exports' / 'b'), 'cytools_film/b')
        # re-exporting replaces an earlier export; any other non-empty folder is refused, never emptied
        self.h3film.export_film(self.board, target)
        other = self.tmp / 'precious'
        other.mkdir()
        (other / 'keep.txt').write_text('mine', encoding='utf-8')
        with self.assertRaises(self.model.StoryboardError):
            self.h3film.export_film(self.board, other)
        self.assertTrue((other / 'keep.txt').is_file())
        # a film with control videos gets the Fun ControlNet loader wired to the sampler
        film = json.loads((target / 'film.json').read_text(encoding='utf-8'))
        film['timeline']['segmentConfig']['segments'][0]['cytoolsControl'] = {'file': 'media/d.mp4'}
        controlled = comfy_workflow.film_sampler_workflow(film, 'cytools_film/x/film.json', control_patch='cn.safetensors')
        loader = next(n for n in controlled['nodes'] if n['type'] == 'ModelPatchLoader')
        self.assertEqual(loader['widgets_values'], ['cn.safetensors'])
        sampler = next(n for n in controlled['nodes'] if n['type'] == 'CyH3FilmSampler')
        slot = next(i for i in sampler['inputs'] if i['name'] == 'control_patch')
        self.assertTrue(any(l[0] == slot['link'] and l[1] == loader['id'] for l in controlled['links']))


if __name__ == '__main__':
    unittest.main()

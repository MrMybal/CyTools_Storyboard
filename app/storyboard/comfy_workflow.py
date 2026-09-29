"""ComfyUI editor workflows (the format the ComfyUI page loads by drag and drop) for a film.

Two graphs, same loaders and sampling settings as the Timeline Director examples (turbo
8-step fused transformer, euler / simple, 8 steps, SelfLift 6 + 2):

- `film_sampler_workflow`: CyTools H3 Film Plan reads film.json, CyTools H3 Film Sampler
  renders segment by segment to disk (resume, reuse of unchanged segments);
- `timeline_director_workflow`: only Timeline Director nodes; the timeline is pasted in the
  Material Planner, its Finite Segment Sampler keeps the whole film in memory.

Widget values follow each node's input order (ComfyUI assigns them by position).
"""
import copy
import json

from .h3film import CONTROL_PATCH, TURBO_MODEL


class Workflow:
    def __init__(self):
        self.nodes, self.links = [], []
        self._link = 0

    def node(self, node_id, kind, pos, widgets, inputs=(), outputs=(), size=(320, 120), title=None):
        entry = {'id': node_id, 'type': kind, 'pos': list(pos), 'size': list(size), 'flags': {},
                 'order': len(self.nodes), 'mode': 0,
                 'inputs': [{'name': name, 'type': kind_, 'link': None} for name, kind_ in inputs],
                 'outputs': [{'name': name, 'type': kind_, 'links': [], 'slot_index': index}
                             for index, (name, kind_) in enumerate(outputs)],
                 'properties': {'Node name for S&R': kind}, 'widgets_values': list(widgets)}
        if title:
            entry['title'] = title
        self.nodes.append(entry)
        return entry

    def connect(self, source, slot, target, input_name):
        self._link += 1
        source_node = next(n for n in self.nodes if n['id'] == source)
        target_node = next(n for n in self.nodes if n['id'] == target)
        index = next(i for i, x in enumerate(target_node['inputs']) if x['name'] == input_name)
        kind = source_node['outputs'][slot]['type']
        source_node['outputs'][slot]['links'].append(self._link)
        target_node['inputs'][index]['link'] = self._link
        self.links.append([self._link, source, slot, target, index, kind])

    def document(self):
        return {'last_node_id': max(n['id'] for n in self.nodes), 'last_link_id': self._link, 'nodes': self.nodes,
                'links': self.links, 'groups': [], 'config': {}, 'extra': {'ds': {'scale': 0.6, 'offset': [0, 0]}},
                'version': 0.4}


def _loaders(w, steps=8):
    w.node(1, 'UNETLoader', (0, 0), [TURBO_MODEL, 'default'], outputs=[('MODEL', 'MODEL')], size=(420, 82))
    w.node(2, 'CLIPLoader', (0, 130), ['qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors', 'minimax', 'default'],
           outputs=[('CLIP', 'CLIP')], size=(420, 106))
    w.node(3, 'VAELoader', (0, 280), ['minimax_h3_video_vae_fp16.safetensors'], outputs=[('VAE', 'VAE')])
    w.node(4, 'VAELoader', (0, 380), ['minimax_h3_audio_vae_fp32.safetensors'], outputs=[('VAE', 'VAE')])
    w.node(5, 'KSamplerSelect', (0, 480), ['euler'], outputs=[('SAMPLER', 'SAMPLER')])
    w.node(6, 'BasicScheduler', (0, 580), ['simple', steps, 1.0], inputs=[('model', 'MODEL')],
           outputs=[('SIGMAS', 'SIGMAS')])
    w.connect(1, 0, 6, 'model')


SAMPLING_INPUTS = [('model', 'MODEL'), ('clip', 'CLIP'), ('vae', 'VAE'), ('audio_vae', 'VAE'),
                   ('finite_plan', 'MINIMAX_H3_FINITE_SEGMENT_PLAN'), ('sampler', 'SAMPLER'), ('sigmas', 'SIGMAS')]


def _wire_sampling(w, sampler_id, plan_id, plan_slot):
    for source, slot, name in ((1, 0, 'model'), (2, 0, 'clip'), (3, 0, 'vae'), (4, 0, 'audio_vae'),
                               (plan_id, plan_slot, 'finite_plan'), (5, 0, 'sampler'), (6, 0, 'sigmas')):
        w.connect(source, slot, sampler_id, name)


def film_sampler_workflow(film, film_file, seed=42, control_patch=None):
    """Plan + disk sampler; a film with control videos also gets the Fun ControlNet loader."""
    w = Workflow()
    _loaders(w)
    controlled = any(s.get('cytoolsControl') for s in film['timeline']['segmentConfig']['segments'])
    w.node(10, 'CyH3FilmPlan', (480, 0), [film_file, '', 0, 0, 'from film', '', 0],
           outputs=[('Material Plan', 'MINIMAX_H3_TIMELINE_PLAN'), ('Segment Plan', 'MINIMAX_H3_FINITE_SEGMENT_PLAN'),
                    ('Plan report', 'STRING')], size=(420, 260), title=f'{film["title"]} - film plan')
    # The editor adds a 'control after generate' widget behind every seed field.
    inputs = SAMPLING_INPUTS + ([('control_patch', 'MODEL_PATCH')] if controlled else [])
    w.node(11, 'CyH3FilmSampler', (960, 0), [seed, 'fixed', True, 'match', film['title'] or 'film', True, '', True],
           inputs=inputs, outputs=[('Film MP4', 'STRING'), ('Run folder', 'STRING'), ('Status', 'STRING')],
           size=(420, 300), title=f'{film["title"]} - disk render')
    _wire_sampling(w, 11, 10, 1)
    if controlled:
        w.node(7, 'ModelPatchLoader', (480, 300), [control_patch or CONTROL_PATCH],
               outputs=[('MODEL_PATCH', 'MODEL_PATCH')], size=(420, 60), title='Fun ControlNet Union (control videos)')
        w.connect(7, 0, 11, 'control_patch')
    return w.document()


def timeline_director_workflow(film, input_folder, seed=42):
    """Planner with the timeline pasted in; media paths relative to ComfyUI's input folder."""
    timeline = copy.deepcopy(film['timeline'])
    # Timeline Director treats video clips as global to the timeline (guides and gap frames in
    # the neighbouring segments); only CyTools H3 Film Plan keeps them in their own segment.
    timeline['videoClips'] = []
    for asset in timeline['images'] + timeline['audios']:
        asset['file'] = f'{input_folder}/{asset["file"]}'
    w = Workflow()
    _loaders(w)
    w.node(10, 'MiniMaxH3TimelinePlanner', (480, 0),
           [film['width'], film['height'], film['frames'] / 24, json.dumps(timeline, ensure_ascii=False), ''],
           inputs=[('import_preset', 'MINIMAX_H3_TIMELINE_PRESET'), ('prompt_index', 'INT')],
           outputs=[('Material Plan', 'MINIMAX_H3_TIMELINE_PLAN'), ('Omni Media Bundle', 'MINIMAX_H3_OMNI_MEDIA_BUNDLE'),
                    ('Segment Plan', 'MINIMAX_H3_FINITE_SEGMENT_PLAN')], size=(1400, 900),
           title=f'{film["title"]} - {len(film["segments"])} segments')
    w.node(11, 'MiniMaxH3FiniteSegmentSampler', (1920, 0), [seed, 'fixed', True, 'match'], inputs=SAMPLING_INPUTS,
           outputs=[('Last Sampled Latent', 'LATENT'), ('Merged Frames', 'IMAGE'), ('Merged Audio', 'AUDIO'),
                    ('Sampling Status', 'STRING')], size=(400, 260))
    _wire_sampling(w, 11, 10, 2)
    w.node(12, 'CreateVideo', (2360, 0), [24], inputs=[('images', 'IMAGE'), ('audio', 'AUDIO')],
           outputs=[('VIDEO', 'VIDEO')])
    w.connect(11, 1, 12, 'images')
    w.connect(11, 2, 12, 'audio')
    w.node(13, 'SaveVideo', (2360, 180), ['video/H3_film', 'mp4', 'h264'], inputs=[('video', 'VIDEO')], size=(320, 300))
    w.connect(12, 0, 13, 'video')
    return w.document()

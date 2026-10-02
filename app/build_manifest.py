"""Write CyTool.json for CyTools_Storyboard. Run after changing an operation:

    runtime/python/Scripts/python.exe app/build_manifest.py
"""
import json
import sys
from pathlib import Path

APP = Path(__file__).resolve().parent
sys.path.insert(0, str(APP))
from storyboard import h3film, h3workflow, imagegen, imagemodels, model  # noqa: E402
from storyboard.pose import NAMES as POSES  # noqa: E402

VERSION = '0.2.0'
PROJECT = {'type': 'string', 'x-cy-kind': 'Directory', 'maxLength': 4096,
           'description': 'Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.'}
FILE = {'type': 'string', 'x-cy-kind': 'File', 'maxLength': 4096,
        'description': 'Local file; copied into the project assets.'}
IMAGE = {'type': 'object', 'additionalProperties': False, 'required': ['file'], 'properties': {
    'file': FILE, 'role': {'type': 'string', 'enum': list(model.IMAGE_ROLES), 'default': 'sketch'},
    'time': {'type': 'number', 'minimum': 0, 'description': 'For keyframes: seconds from the start of the panel.'},
    'caption': {'type': 'string', 'maxLength': 500}}}
DIALOGUE = {'type': 'object', 'additionalProperties': False, 'properties': {
    'speaker': {'type': 'string', 'maxLength': 200, 'description': 'Library character id or a free name.'},
    'language': {'type': 'string', 'maxLength': 40, 'default': 'English'},
    'line': {'type': 'string', 'maxLength': 2000}, 'offScreen': {'type': 'boolean', 'default': False},
    'delivery': {'type': 'string', 'maxLength': 200}}}
PROMPT = {'type': 'object', 'additionalProperties': False, 'x-cy-kind': 'Object', 'properties': {
    'scene': {'type': 'string', 'maxLength': 4000, 'x-cy-kind': 'MultilineString'},
    'action': {'type': 'string', 'maxLength': 8000, 'x-cy-kind': 'MultilineString'},
    'shotSize': {'type': 'string', 'enum': list(model.SHOT_SIZES)},
    'angle': {'type': 'string', 'enum': list(model.ANGLES)},
    'cameraMove': {'type': 'string', 'enum': list(model.CAMERA_MOVES)},
    'cameraAmplitude': {'type': 'string', 'enum': list(model.AMPLITUDES)},
    'cameraSpeed': {'type': 'string', 'enum': list(model.SPEEDS)},
    'lens': {'type': 'string', 'maxLength': 100},
    'sound': {'type': 'string', 'maxLength': 2000}, 'music': {'type': 'string', 'maxLength': 2000},
    'dialogue': {'type': 'array', 'maxItems': 50, 'items': DIALOGUE},
    'freeText': {'type': 'string', 'maxLength': 60000, 'x-cy-kind': 'MultilineString',
                 'description': 'Anything else, written as you want it passed on.'}}}
TRANSITION = {'type': 'object', 'additionalProperties': False, 'properties': {
    'type': {'type': 'string', 'enum': list(model.TRANSITIONS)},
    'duration': {'type': 'number', 'minimum': 0, 'maximum': 10}}}
PANEL_FIELDS = {
    'title': {'type': 'string', 'maxLength': 200},
    'duration': {'type': 'number', 'minimum': 0.1, 'maximum': 600, 'description': 'Seconds on screen.'},
    'status': {'type': 'string', 'enum': list(model.STATUSES)},
    'color': {'type': 'string', 'maxLength': 20},
    'images': {'type': 'array', 'maxItems': 30, 'items': IMAGE},
    'prompt': PROMPT,
    'references': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Library item ids.'},
    'transition': TRANSITION,
    'notes': {'type': 'string', 'maxLength': 8000, 'x-cy-kind': 'MultilineString'},
}
DOCUMENT = {'type': 'object', 'properties': {'project': {'type': 'string'}, 'document': {'type': 'object'},
                                             'timeline': {'type': 'array'}, 'totalDuration': {'type': 'number'},
                                             'issues': {'type': 'array'}}, 'required': ['project']}
VEC3 = {'type': 'array', 'items': {'type': 'number'}, 'minItems': 3, 'maxItems': 4}
CAMERA = {'type': 'object', 'additionalProperties': False, 'required': ['position', 'target'], 'properties': {
    'position': {**VEC3, 'description': 'Metres; Y is up, the ground is Y = 0.'},
    'target': {**VEC3, 'description': 'The point the camera looks at.'},
    'fov': {'type': 'number', 'minimum': 5, 'maximum': 150, 'default': 40, 'description': 'Vertical field of view, degrees.'},
    'roll': {'type': 'number', 'minimum': -180, 'maximum': 180, 'default': 0}}}
DRAW_ITEM = {'type': 'object', 'additionalProperties': False, 'required': ['type', 'points'], 'properties': {
    'type': {'type': 'string', 'enum': ['rect', 'ellipse', 'line', 'arrow', 'stroke', 'text', 'figure']},
    'points': {'type': 'array', 'maxItems': 2000, 'items': {'type': 'array', 'items': {'type': 'number'},
                                                             'minItems': 2, 'maxItems': 2},
               'description': 'Coordinates from 0 to 1 of the frame (x right, y down). Two corners for rect/ellipse, '
                              'start and end for line/arrow, the path for stroke, one point for text and figure '
                              '(a figure stands on it).'},
    'color': {'type': 'string', 'maxLength': 20}, 'width': {'type': 'number', 'minimum': 0.5, 'maximum': 50},
    'fill': {'type': 'boolean'}, 'text': {'type': 'string', 'maxLength': 500},
    'size': {'type': 'number', 'minimum': 0.005, 'maximum': 1, 'description': 'Text height or figure scale (share of the frame).'}}}
DRAWING = {'type': 'object', 'additionalProperties': False, 'properties': {
    'background': {'type': 'string', 'maxLength': 20}, 'items': {'type': 'array', 'maxItems': 500, 'items': DRAW_ITEM}}}
OBJECT_FIELDS = {
    'name': {'type': 'string', 'maxLength': 200}, 'color': {'type': 'string', 'maxLength': 20},
    'position': VEC3, 'rotation': {**VEC3, 'description': 'Degrees around X, Y, Z.'},
    'scale': {**VEC3, 'description': 'Size in metres for box/sphere/cylinder/cone, a factor for the others.'},
    'role': {'type': 'string', 'enum': ['set', 'character', 'object', 'location']},
    'reference': {'type': 'string', 'description': 'Library item this shape stands for.'},
    'pose': {'type': 'string', 'description': 'Character pose on the stage: a preset or a project pose id.'}}
FILM_OPTIONS = {'type': 'object', 'additionalProperties': False, 'properties': {
    'shortEdge': {'type': 'integer', 'enum': list(h3film.SHORT_EDGES),
                  'description': 'Short edge of the canvas; the other side follows the storyboard aspect (multiples of 32).'},
    'width': {'type': 'integer', 'minimum': 0, 'maximum': 2560, 'description': 'Explicit width (with height); 0 = from shortEdge.'},
    'height': {'type': 'integer', 'minimum': 0, 'maximum': 2560},
    'grouping': {'type': 'string', 'enum': list(h3film.GROUPINGS),
                 'description': 'panel: one segment per panel; sequence (default): consecutive panels of a sequence '
                                'share segments of about maxSegmentSeconds, H3 cutting between their shots; film: '
                                'the same across sequences.'},
    'maxSegmentSeconds': {'type': 'number', 'minimum': 2, 'maximum': 149, 'description': 'Longest grouped segment.'},
    'maxShotsPerSegment': {'type': 'integer', 'minimum': 0, 'description': 'Most shots in a grouped segment; 0 = no limit.'},
    'shotText': {'type': 'string', 'maxLength': 2000, 'description': 'Shot header in a grouped segment; {shot}, {start}, {end}, {title}.'},
    'dialogueText': {'type': 'string', 'maxLength': 2000, 'description': 'A line; {name}, {how} (" (off screen)"), {line}.'},
    'soundText': {'type': 'string', 'maxLength': 2000, 'description': "A shot's sound; {text}. Empty leaves it out."},
    'musicText': {'type': 'string', 'maxLength': 2000, 'description': "A shot's music; {text}. Empty leaves it out."},
    'overlapFrames': {'type': 'integer', 'enum': list(h3film.OVERLAPS),
                      'description': 'Frames each segment re-generates from the previous one (continuity); removed at assembly.'},
    'overlapOnCuts': {'type': 'boolean', 'description': 'Also carry continuity across plain cuts (same scene).'},
    'overlapOnFades': {'type': 'boolean', 'description': 'Also carry continuity across fades to/from black.'},
    'globalPrompt': {'type': 'string', 'maxLength': 8000, 'description': 'Text added to every segment.'},
    'includeStyle': {'type': 'boolean'}, 'includeDescription': {'type': 'boolean'},
    'referenceNote': {'type': 'string', 'maxLength': 4000},
    'continuityText': {'type': 'string', 'maxLength': 4000, 'description': 'Sentence for carried frames; {frames}, {seconds}.'},
    'identityScope': {'type': 'string', 'enum': ['panel', 'film'],
                      'description': 'Identity pictures of the characters a panel uses, or of every character in every segment.'},
    'identityText': {'type': 'string', 'maxLength': 2000, 'description': '{n}, {name}, {description}'},
    'identityPictures': {'type': 'integer', 'minimum': 1, 'maximum': 6,
                         'description': 'Pictures of each character sent per segment (the first ones of the item).'},
    'identityMoreText': {'type': 'string', 'maxLength': 2000, 'description': 'Sentence of the 2nd, 3rd... picture of a character.'},
    'shotPictures': {'type': 'string', 'enum': ['main', 'all', 'none'],
                     'description': "The panel's own pictures: the main one (layout render first), all, or none."},
    'layoutText': {'type': 'string', 'maxLength': 2000}, 'sketchText': {'type': 'string', 'maxLength': 2000},
    'firstText': {'type': 'string', 'maxLength': 2000}, 'lastText': {'type': 'string', 'maxLength': 2000},
    'keyframeText': {'type': 'string', 'maxLength': 2000, 'description': '{n}, {time}'},
    'referenceText': {'type': 'string', 'maxLength': 2000},
    'includeLocations': {'type': 'boolean'}, 'locationText': {'type': 'string', 'maxLength': 2000},
    'includeObjects': {'type': 'boolean'}, 'objectText': {'type': 'string', 'maxLength': 2000},
    'includeStyles': {'type': 'boolean'}, 'styleText': {'type': 'string', 'maxLength': 2000},
    'includeSound': {'type': 'boolean'},
    'includeVideos': {'type': 'boolean', 'description': 'Library items of kind video used by the panel become <Video N> '
                                                        'references of its segment (3 at most).'},
    'videoText': {'type': 'string', 'maxLength': 2000, 'description': '{n}, {name}, {description}'},
    'includeVoices': {'type': 'boolean', 'description': "An audio file among a character's files becomes its voice "
                                                        '(<Audio N>) in the segments where it appears.'},
    'voiceText': {'type': 'string', 'maxLength': 2000},
    'includeAudio': {'type': 'boolean', 'description': 'Library items of kind audio used by the panel become <Audio N>.'},
    'audioText': {'type': 'string', 'maxLength': 2000},
    'videoSound': {'type': 'boolean', 'description': "Also give the reference videos' own sound as <Audio N>."},
    'videoSoundText': {'type': 'string', 'maxLength': 2000, 'description': '{n}, {video}, {name}'},
    'maxReferenceSeconds': {'type': 'number', 'minimum': 2, 'maximum': 15,
                            'description': 'Longer videos and sounds are cut to this length.'},
    'secondPass': {'type': 'boolean', 'description': 'SelfLift two-stage sampling (low-res steps, latent upscale, high-res steps).'},
    'secondPassModel': {'type': 'string', 'maxLength': 300, 'description': 'Latent upscaler file name.'},
    'secondPassHighSteps': {'type': 'integer', 'minimum': 1, 'maximum': 50},
    'controlPatchModel': {'type': 'string', 'maxLength': 300,
                          'description': 'Fun ControlNet file loaded by the ComfyUI workflow written next to film.json '
                                         '(films with control videos).'},
    'generatedAudio': {'type': 'boolean', 'description': 'Generate sound with the picture (off = silent film).'},
    'depthControl': {'type': 'string', 'enum': ['off', 'indicative', 'guided', 'strict', 'custom'],
                     'description': 'Depth video of the panels staged in 3D as Fun ControlNet control: indicative '
                                    '(0.35, first 35 % of the steps, strong blur), guided (0.6, medium blur), strict '
                                    '(1.0, sharp), custom.'},
    'controlStrength': {'type': 'number', 'minimum': 0.05, 'maximum': 2},
    'controlEnd': {'type': 'number', 'minimum': 0.05, 'maximum': 1, 'description': 'Share of the steps it applies to.'},
    'controlBlur': {'type': 'string', 'enum': ['none', 'medium', 'strong']},
    'controlSource': {'type': 'string', 'enum': ['auto', 'depth', 'pose', 'overlay'],
                      'description': 'Control video: depth of the set, OpenPose pose of the characters, auto (pose '
                                     'when a character is in frame), or the pose drawn over the depth (experimental).'},
    'poseFeet': {'type': 'boolean', 'description': 'Draw the feet (OpenPose BODY_25: heel, big toe, small toe) in '
                                                   'the pose control.'},
    'poseHands': {'type': 'boolean', 'description': 'Draw the hands (OpenPose hand model, 21 points) in the pose '
                                                    'control when they are large enough on screen.'},}}
TEXT = {'type': 'string', 'maxLength': 2000}
FOOT = {'type': 'array', 'items': {'type': 'number'}, 'minItems': 2, 'maxItems': 2}
HAND = {'type': 'array', 'items': {'type': 'number'}, 'minItems': 6, 'maxItems': 8}
LIMB = {'type': 'array', 'items': {'type': 'number'}, 'minItems': 3, 'maxItems': 4}
ANGLES = {'type': 'object', 'additionalProperties': False, 'description': 'Degrees; values not given are kept.',
          'properties': {
              'lean': {'type': 'number', 'minimum': -45, 'maximum': 90, 'description': 'Upper body forwards.'},
              'twist': {'type': 'number', 'minimum': -90, 'maximum': 90, 'description': 'Upper body to its left.'},
              'bend': {'type': 'number', 'minimum': -45, 'maximum': 45, 'description': 'Upper body tilted to its left side.'},
              'tilt': {'type': 'number', 'minimum': -25, 'maximum': 25,
                       'description': 'Pelvis tilted, left hip up; the legs hang from it, the upper body stays.'},
              'head': {'type': 'array', 'items': {'type': 'number'}, 'minItems': 2, 'maxItems': 2,
                       'description': '[turn to its left (-80..80), tilt up (-45..60)]'},
              'seat': {'type': ['number', 'null'], 'minimum': 0.2, 'maximum': 1.2,
                       'description': 'Pelvis height in metres when seated; null = on its feet.'},
              'r_arm': {**LIMB, 'description': '[raise forwards (-60..180), raise sideways (-20..180), elbow bend (0..150), turn of the arm about itself, forearm outwards (-90..90, optional)]'},
              'l_arm': LIMB,
              'r_leg': {**LIMB, 'description': '[raise forwards (-45..130), raise sideways (-30..60), knee bend (0..150), turn of the leg about itself, knee outwards (-45..45, optional)]'},
              'l_leg': LIMB,
              'r_hand': {**HAND, 'description': '[curl of the thumb, index, middle, ring, little finger (0..100 %), '
                                                'spread of the fingers (0..30 degrees), wrist bent towards the palm (-70..80), '
                                                'towards the thumb (-25..35), both optional]'},
              'l_hand': HAND,
              'r_foot': {**FOOT, 'description': '[foot pitched toes down: on tiptoe when positive (-30..60), '
                                                'toes bent up (-40..70)]; the foot is flat on the ground at 0.'},
              'l_foot': FOOT}}
WORKFLOW_OPTIONS = {'type': 'object', 'additionalProperties': False, 'properties': {
    'shortEdge': {'type': 'integer', 'enum': list(h3workflow.SHORT_EDGES)},
    'width': {'type': 'integer', 'minimum': 0, 'maximum': 2560}, 'height': {'type': 'integer', 'minimum': 0, 'maximum': 2560},
    'seed': {'type': 'integer', 'minimum': 0, 'maximum': 9007199254740991},
    'seedPolicy': {'type': 'string', 'enum': ['fixed', 'increment', 'random']},
    'steps': {'type': 'integer', 'minimum': 0, 'maximum': 100, 'description': '0 = the Tool default.'},
    'acceleration': {'type': 'string', 'enum': list(h3workflow.ACCELERATIONS),
                     'description': 'Turbo LoRA for shots without references.'},
    'referenceAcceleration': {'type': 'string', 'enum': list(h3workflow.REFERENCE_ACCELERATIONS),
                              'description': 'Turbo LoRA for shots with references (H3 has no 8-step one for them).'},
    'chain': {'type': 'string', 'enum': list(h3workflow.CHAIN),
              'description': 'Start a shot on the last frame of the previous one: after crossfades, always, never.'},
    'longPanels': {'type': 'string', 'enum': ['split', 'clamp'], 'description': 'Panels over 15 s: chained parts, or 15 s.'},
    'shortPanels': {'type': 'string', 'enum': ['trim', 'extend'], 'description': 'Panels under 4 s: generate 4 s and trim, or keep 4 s.'},
    'exactDurations': {'type': 'boolean', 'description': 'Trim each shot to its panel duration (H3 rounds up to 5 + 17n frames).'},
    'layoutUse': {'type': 'string', 'enum': ['reference', 'first_frame', 'none'],
                  'description': 'The 2D/3D layout render: a reference picture, the first frame, or unused.'},
    'identityScope': {'type': 'string', 'enum': ['panel', 'film']},
    'includeLocations': {'type': 'boolean'}, 'includeObjects': {'type': 'boolean'}, 'includeStyles': {'type': 'boolean'},
    'includeSketches': {'type': 'boolean'}, 'includeVideos': {'type': 'boolean'}, 'videoSound': {'type': 'boolean'},
    'includeVoices': {'type': 'boolean'}, 'includeAudio': {'type': 'boolean'},
    'maxReferenceSeconds': {'type': 'number', 'minimum': 2, 'maximum': 15},
    'includeStyle': {'type': 'boolean'}, 'globalPrompt': {'type': 'string', 'maxLength': 8000},
    'promptLayout': {'type': 'string', 'enum': ['auto', 'structured', 'integrated'],
                     'description': 'H3 prompt layout; auto = structured when characters are defined by pictures.'},
    'layoutText': TEXT, 'sketchText': TEXT, 'referenceText': TEXT, 'locationText': TEXT, 'objectText': TEXT,
    'styleText': TEXT, 'videoText': TEXT, 'audioText': TEXT, 'continuedText': TEXT,
    'depthControl': {'type': 'string', 'enum': ['off', 'indicative', 'guided', 'strict', 'custom'],
                     'description': 'Depth video of the panels staged in 3D as Fun ControlNet control: indicative '
                                    '(0.35, first 35 % of the steps, strong blur), guided (0.6, medium blur), strict '
                                    '(1.0, sharp), custom.'},
    'controlStrength': {'type': 'number', 'minimum': 0.05, 'maximum': 2},
    'controlEnd': {'type': 'number', 'minimum': 0.05, 'maximum': 1, 'description': 'Share of the steps it applies to.'},
    'controlBlur': {'type': 'string', 'enum': ['none', 'medium', 'strong']},
    'controlSource': {'type': 'string', 'enum': ['auto', 'depth', 'pose', 'overlay'],
                      'description': 'Control video: depth of the set, OpenPose pose of the characters, auto (pose '
                                     'when a character is in frame), or the pose drawn over the depth (experimental).'},
    'poseFeet': {'type': 'boolean', 'description': 'Draw the feet (OpenPose BODY_25: heel, big toe, small toe) in '
                                                   'the pose control.'},
    'poseHands': {'type': 'boolean', 'description': 'Draw the hands (OpenPose hand model, 21 points) in the pose '
                                                    'control when they are large enough on screen.'},
    'controlVersion': {'type': 'string', 'enum': ['2.0', '1.0'], 'description': 'Fun ControlNet Union version.'}}}
WORKFLOW_SUMMARY = {'type': 'object', 'properties': {
    'shots': {'type': 'array'}, 'width': {'type': 'integer'}, 'height': {'type': 'integer'},
    'seconds': {'type': 'number'}, 'generations': {'type': 'integer'}, 'steps': {'type': 'integer'},
    'warnings': {'type': 'array'}, 'folder': {'type': 'string', 'x-cy-kind': 'Directory'},
    'file': {'type': 'string', 'x-cy-kind': 'File'}, 'workflow': {'type': 'object'}}, 'required': ['shots']}
FILM_SUMMARY = {'type': 'object', 'properties': {
    'segments': {'type': 'array'}, 'frames': {'type': 'integer'}, 'seconds': {'type': 'number'},
    'width': {'type': 'integer'}, 'height': {'type': 'integer'}, 'warnings': {'type': 'array'},
    'folder': {'type': 'string', 'x-cy-kind': 'Directory'}, 'file': {'type': 'string'}, 'files': {'type': 'array'},
    'globalPrompt': {'type': 'string'}, 'options': {'type': 'object'}}, 'required': ['segments', 'frames']}
LIGHT = {'ramBytes': 256 * 1024 ** 2, 'diskBytes': 512 * 1024 ** 2}


VIEW = {'type': 'object', 'additionalProperties': False, 'required': ['key', 'text'], 'properties': {
    'key': {'type': 'string', 'minLength': 1, 'maxLength': 60}, 'text': {'type': 'string', 'maxLength': 2000},
    'on': {'type': 'boolean'}, 'format': {'type': 'string', 'enum': list(imagegen.FORMATS)}}}
IMAGE_OPTIONS = {'type': 'object', 'additionalProperties': False, 'properties': {
    'model': {'type': 'string', 'maxLength': 80, 'description': 'Image model for pictures from references ("" = the '
              'default installed one). See image_engine_status.'},
    'textModel': {'type': 'string', 'maxLength': 80, 'description': 'Image model for pictures from a text alone.'},
    'steps': {'type': 'integer', 'minimum': 0, 'maximum': 100, 'description': '0 = the model default.'},
    'guidance': {'type': 'number', 'minimum': 0, 'maximum': 20, 'description': '0 = the model default.'},
    'fast': {'type': 'boolean', 'description': 'Few-step LoRA when the model has one.'},
    'megapixels': {'type': 'number', 'minimum': 0.25, 'maximum': 4},
    'count': {'type': 'integer', 'minimum': 1, 'maximum': 16, 'description': 'Pictures per view.'},
    'seed': {'type': 'integer', 'minimum': 0, 'maximum': 2147483647},
    'randomSeed': {'type': 'boolean', 'description': 'false: `seed`, seed + 1... are used, for reproducible pictures.'},
    'negative': {'type': 'string', 'maxLength': 4000}, 'includeStyle': {'type': 'boolean'},
    'loras': {'type': 'array', 'maxItems': imagegen.MAX_LORAS, 'description': 'LoRA files applied to the model, in order; '
              'names inside data/models/comfyui/loras (see image_engine_status). A LoRA belongs to one model family.',
              'items': {'type': 'object', 'additionalProperties': False, 'required': ['file'], 'properties': {
                  'file': {'type': 'string', 'minLength': 1, 'maxLength': 255},
                  'strength': {'type': 'number', 'minimum': -4, 'maximum': 4, 'default': 1.0},
                  'on': {'type': 'boolean', 'default': True}}}},
    'keepLoadedMinutes': {'type': 'integer', 'minimum': 0, 'maximum': 1440,
                          'description': 'The model stays in memory this long after the last picture; 0 = until unloaded.'},
    'server': {'type': 'string', 'maxLength': 500, 'description': 'Address of another ComfyUI to render on (Colab tunnel); '
               '"" = the private engine of the application.'},
    'characterViews': {'type': 'array', 'maxItems': 40, 'items': VIEW},
    'locationViews': {'type': 'array', 'maxItems': 40, 'items': VIEW},
    **{key: {'type': 'string', 'maxLength': 4000} for key in imagegen.TEXTS},
    'panelFormat': {'type': 'string', 'enum': list(imagegen.FORMATS)},
    'panelGuide': {'type': 'string', 'enum': list(imagegen.GUIDES),
                   'description': 'How a 3D-staged shot gets its framing: control (depth or pose of the staging through '
                                  'the ControlNet of the model), layout (the staging render as a picture), both, none; '
                                  'auto = control when the ControlNet is installed, else layout.'},
    'panelControlSource': {'type': 'string', 'enum': list(imagegen.CONTROL_SOURCES)},
    'panelControlStrength': {'type': 'number', 'exclusiveMinimum': 0, 'maximum': 2},
    'panelControlEnd': {'type': 'number', 'exclusiveMinimum': 0, 'maximum': 1,
                        'description': 'Share of the steps during which the control applies.'},
    'panelControlBlur': {'type': 'string', 'enum': ['none', 'medium', 'strong']},
    'panelCharacterPictures': {'type': 'integer', 'minimum': 1, 'maximum': 6,
                               'description': 'Pictures of each character sent for a shot or a place: its first picture, '
                                              'then its generated views (full body first).'},
    'freeFormat': {'type': 'string', 'enum': list(imagegen.FORMATS)}}}
IMAGE_PLAN = {
    'project': dict(PROJECT, description='Project (needed by every recipe except free).'),
    'recipe': {'type': 'string', 'enum': list(imagegen.RECIPES), 'default': 'free',
               'description': 'character: views of a library character; location: views of a place, empty or with a '
                              'character; panel: the picture of a shot; free: any prompt.'},
    'item': {'type': 'string', 'maxLength': 80, 'description': 'Library item id (character or location recipe).'},
    'panel': {'type': 'string', 'maxLength': 80, 'description': 'Panel id (panel recipe).'},
    'views': {'type': 'array', 'maxItems': 40, 'items': {'type': 'string', 'maxLength': 60},
              'description': 'View keys to render; default: the views switched on in the options.'},
    'character': {'type': 'string', 'maxLength': 80, 'description': 'Character id placed in the location (location recipe).'},
    'prompt': {'type': 'string', 'maxLength': 8000, 'description': 'Text of the free recipe.'},
    'references': {'type': 'array', 'maxItems': 16, 'items': {'type': 'string', 'maxLength': 4096},
                   'description': 'Free recipe: picture files or library item ids used as references (none = from the text).'},
    'format': {'type': 'string', 'enum': list(imagegen.FORMATS)},
    'extra': {'type': 'string', 'maxLength': 2000, 'description': 'Added to every prompt of the recipe.'},
    'extras': {'type': 'string', 'maxLength': 80, 'description': 'Panel recipe: character id that every mannequin of the '
               'staging without a reference stands for (a crowd of the same character).'},
    'label': {'type': 'string', 'maxLength': 120}, 'options': IMAGE_OPTIONS}
ANY = {'type': 'object', 'additionalProperties': True}
IMAGE_MODEL = {'type': 'string', 'enum': sorted(imagemodels.catalog())}
# No VRAM reservation: the engine keeps its model loaded between jobs (a reservation would refuse the
# second job for lack of free VRAM), ComfyUI offloads what does not fit, and with the `server` option
# nothing runs on this machine. What each model needs is declared on the backend's models.
HEAVY = {'ramBytes': 8 * 1024 ** 3, 'cpuThreads': 2}
NETWORK = {'ramBytes': 1024 ** 3, 'cpuThreads': 2, 'diskBytes': 40 * 1024 ** 3}


# Operations that use or change the image engine and its model files: they never run at the same time
# (a model removed or re-downloaded while it renders, the engine reinstalled while it runs).
IMAGE_ENGINE_OPERATIONS = ('generate_images', 'unload_image_model', 'install_image_engine', 'install_image_model',
                           'verify_image_model', 'remove_image_model')


def image_operations():
    def op(op_id, name, description, inputs, required=(), resources=None, permissions=(), backends=(), progress=True):
        entry = operation(op_id, name, description, inputs, ANY, required=required, progress=progress)
        entry.update(resourceRequirements=resources or LIGHT, permissions=list(permissions), supportedBackends=list(backends))
        if op_id in IMAGE_ENGINE_OPERATIONS:
            entry['exclusiveGroups'] = ['image-engine']
        return entry
    return [
        op('plan_images', 'Plan pictures', 'The requests a recipe would send to the image model (prompts, reference '
           'pictures, sizes, seeds), without generating anything.', IMAGE_PLAN, progress=False),
        op('generate_images', 'Generate pictures', 'Generate reference pictures in the application: views of a character '
           'or a place from its reference pictures (or from its description), a character placed in a place, the picture '
           'of a shot from its staging render, or a free prompt. The model stays loaded between calls. Returns the '
           'pictures with their recipe; keep=true copies them into the project and attaches them (library item files, '
           'first image of the panel).',
           dict(IMAGE_PLAN, keep={'type': 'boolean', 'default': False, 'description': 'Copy every picture into the project.'},
                attach={'type': 'boolean', 'default': True, 'description': 'With keep: attach to the item or the panel.'},
                save_options={'type': 'boolean', 'default': False, 'description': 'Remember the options in the project.'}),
           resources=HEAVY, backends=['comfyui']),
        op('keep_generated_image', 'Keep a generated picture', 'Copy one picture returned by generate_images into the '
           'project with its recipe, and attach it to its target.',
           {'project': PROJECT, 'file': {'type': 'string', 'x-cy-kind': 'File', 'maxLength': 4096},
            'attach': {'type': 'boolean', 'default': True}}, required=['project', 'file'], progress=False),
        op('export_image_workflows', 'Export ComfyUI picture workflows', 'Write the ComfyUI workflow of a recipe (editor '
           'file to drop on the ComfyUI page, API prompt) and its reference pictures (folder cytools_images, to copy '
           'into ComfyUI/input): the same graph the application renders.',
           dict(IMAGE_PLAN, folder={'type': 'string', 'x-cy-kind': 'Directory', 'maxLength': 4096,
                                    'description': 'Target folder; default exports/comfyui_images in the project.'},
                name={'type': 'string', 'maxLength': 60}), progress=False),
        op('image_engine_status', 'Image engine status', 'Engine environment, models (installed, size, licence) and the '
           'model currently in memory.', {}, progress=False),
        op('unload_image_model', 'Unload the image model', 'Stop the image engine and give its memory back.', {},
           progress=False),
        op('install_image_engine', 'Install the image engine', 'Create or repair the private engine: a Python '
           'environment with PyTorch (CUDA 13) and a pinned ComfyUI checkout, checked by import.',
           {'cpu_only': {'type': 'boolean', 'default': False}}, resources=NETWORK, permissions=['network']),
        op('install_image_model', 'Install an image model', 'Download the files of a model (resumable, size and SHA-256 '
           'checked); files shared with another model are not downloaded twice.',
           {'model': IMAGE_MODEL, 'accept_license': {'type': 'boolean', 'default': True},
            'repair': {'type': 'boolean', 'default': False}}, required=['model'], resources=NETWORK, permissions=['network']),
        op('verify_image_model', 'Verify an image model', 'Check every file of a model against its declared SHA-256.',
           {'model': IMAGE_MODEL}, required=['model']),
        op('remove_image_model', 'Remove an image model', 'Delete the files of a model that no other installed model uses.',
           {'model': IMAGE_MODEL}, required=['model'], progress=False),
    ]


def image_backend():
    models = []
    for entry in imagemodels.catalog().values():
        models.append({'id': entry['id'], 'name': entry['name'], 'version': entry['source']['revision'][:12],
                       'source': entry['source']['url'], 'license': entry['license']['name'],
                       'licenseUrl': entry['license']['url'], 'location': 'Local', 'runsLocally': True,
                       'installed': False, 'downloadSize': entry['downloadBytes'], 'installedSize': entry['downloadBytes'],
                       'resourceRequirements': {'ramBytes': entry['resources']['ramBytes'],
                                                'vramBytes': {'auto': entry['resources']['vramBytes']}}})
    return {'id': 'comfyui', 'name': 'Private ComfyUI image engine (Qwen-Image)', 'version': '0.38.0',
            'license': 'GPL-3.0 (ComfyUI); each model has its own licence', 'licenseUrl': 'https://github.com/comfyanonymous/ComfyUI',
            'shareableModelInstance': False, 'threadSafe': False, 'concurrentInference': False, 'maxConcurrentInference': 1,
            'gpu': {'required': True}, 'cpu': {'supported': False}, 'models': models}


def operation(op_id, name, description, inputs, outputs=None, required=('project',), progress=False):
    return {'id': op_id, 'name': name, 'description': description,
            'inputSchema': {'type': 'object', 'properties': inputs, 'required': list(required),
                            'additionalProperties': False},
            'outputSchema': outputs or DOCUMENT, 'resourceRequirements': LIGHT, 'supportedBackends': [],
            'permissions': [], 'canRunAsync': True, 'canCancel': True, 'supportsProgress': progress}


def manifest():
    ops = [
        operation('create_storyboard', 'Create a storyboard', 'Create a project folder (.cystory) with one empty sequence.',
                  {'title': {'type': 'string', 'minLength': 1, 'maxLength': 120},
                   'folder': {'type': 'string', 'x-cy-kind': 'Directory', 'maxLength': 4096,
                              'description': 'Parent folder; default data/projects.'},
                   'aspect': {'type': 'string', 'enum': list(model.ASPECTS), 'default': '16:9'},
                   'fps': {'type': 'integer', 'minimum': 1, 'maximum': 120, 'default': 24},
                   'default_duration': {'type': 'number', 'minimum': 0.1, 'maximum': 600, 'default': 5}},
                  required=['title']),
        operation('duplicate_storyboard', 'Save a storyboard as a copy', 'Copy a project under another title (document '
                  'and assets, its own folder and id); the original is left as it is.',
                  {'project': PROJECT, 'title': {'type': 'string', 'minLength': 1, 'maxLength': 120},
                   'folder': {'type': 'string', 'x-cy-kind': 'Directory', 'maxLength': 4096,
                              'description': 'Parent folder of the copy; default: next to the original.'}},
                  required=['project', 'title']),
        operation('list_storyboards', 'List storyboards', 'Projects in data/projects (or in a given folder).',
                  {'folder': {'type': 'string', 'x-cy-kind': 'Directory', 'maxLength': 4096}},
                  {'type': 'object', 'properties': {'projects': {'type': 'array'}}, 'required': ['projects']}, required=[]),
        operation('describe_storyboard', 'Describe a storyboard',
                  'The whole document, the timeline (start/end of every panel), the total duration and the problems found.',
                  {'project': PROJECT}),
        operation('update_storyboard', 'Change storyboard settings', 'Title, description and settings.',
                  {'project': PROJECT, 'title': {'type': 'string', 'maxLength': 120},
                   'description': {'type': 'string', 'maxLength': 8000},
                   'settings': {'type': 'object', 'additionalProperties': False, 'properties': {
                       'aspect': {'type': 'string', 'enum': list(model.ASPECTS)},
                       'fps': {'type': 'integer', 'minimum': 1, 'maximum': 120},
                       'defaultDuration': {'type': 'number', 'minimum': 0.1, 'maximum': 600},
                       'minSegment': {'type': 'number', 'minimum': 0, 'maximum': 600},
                       'maxSegment': {'type': 'number', 'minimum': 0.1, 'maximum': 600},
                       'style': {'type': 'string', 'maxLength': 4000},
                       'language': {'type': 'string', 'maxLength': 40}}}}),
        operation('add_panel', 'Add a panel', 'Add a panel at the end of a sequence, or after a given panel.',
                  {'project': PROJECT, 'sequence': {'type': 'string'}, 'after': {'type': 'string'}, **PANEL_FIELDS}),
        operation('update_panel', 'Change a panel', 'Change any field of a panel; prompt fields are merged.',
                  {'project': PROJECT, 'panel': {'type': 'string'}, **PANEL_FIELDS}, required=['project', 'panel']),
        operation('duplicate_panel', 'Duplicate a panel', 'Copy a panel right after itself.',
                  {'project': PROJECT, 'panel': {'type': 'string'}}, required=['project', 'panel']),
        operation('move_panel', 'Move a panel', 'Move a panel to a position, in its sequence or another one.',
                  {'project': PROJECT, 'panel': {'type': 'string'}, 'sequence': {'type': 'string'},
                   'index': {'type': 'integer', 'minimum': 0}}, required=['project', 'panel']),
        operation('remove_panel', 'Remove a panel', 'Delete a panel (its assets stay in the project).',
                  {'project': PROJECT, 'panel': {'type': 'string'}}, required=['project', 'panel']),
        operation('add_sequence', 'Add a sequence', 'A new group of panels.',
                  {'project': PROJECT, 'title': {'type': 'string', 'maxLength': 200}, 'after': {'type': 'string'}}),
        operation('update_sequence', 'Change a sequence', 'Title, colour, notes.',
                  {'project': PROJECT, 'sequence': {'type': 'string'}, 'title': {'type': 'string', 'maxLength': 200},
                   'color': {'type': 'string', 'maxLength': 20}, 'notes': {'type': 'string', 'maxLength': 8000}},
                  required=['project', 'sequence']),
        operation('remove_sequence', 'Remove a sequence', 'Delete a sequence and its panels.',
                  {'project': PROJECT, 'sequence': {'type': 'string'}}, required=['project', 'sequence']),
        operation('add_library_item', 'Add a reference', 'A character, location, object, style, image, audio or video '
                  'reference usable by any panel.',
                  {'project': PROJECT, 'kind': {'type': 'string', 'enum': list(model.KINDS)},
                   'name': {'type': 'string', 'maxLength': 200}, 'description': {'type': 'string', 'maxLength': 8000},
                   'files': {'type': 'array', 'maxItems': 20, 'items': FILE},
                   'tags': {'type': 'array', 'items': {'type': 'string', 'maxLength': 60}}},
                  required=['project', 'kind', 'name']),
        operation('update_library_item', 'Change a reference', 'Name, description, kind, files, tags.',
                  {'project': PROJECT, 'item': {'type': 'string'}, 'kind': {'type': 'string', 'enum': list(model.KINDS)},
                   'name': {'type': 'string', 'maxLength': 200}, 'description': {'type': 'string', 'maxLength': 8000},
                   'files': {'type': 'array', 'maxItems': 20, 'items': FILE},
                   'tags': {'type': 'array', 'items': {'type': 'string', 'maxLength': 60}}},
                  required=['project', 'item']),
        operation('remove_library_item', 'Remove a reference', 'Also removed from the panels that used it.',
                  {'project': PROJECT, 'item': {'type': 'string'}}, required=['project', 'item']),
        operation('validate_storyboard', 'Check a storyboard', 'Missing images, empty panels, durations outside the '
                  'limits, unknown references.', {'project': PROJECT}),
        operation('export_contact_sheet', 'Export a contact sheet', 'All panels on one PNG with numbers, durations and text.',
                  {'project': PROJECT, 'columns': {'type': 'integer', 'minimum': 1, 'maximum': 10, 'default': 4},
                   'cell_width': {'type': 'integer', 'minimum': 160, 'maximum': 1200, 'default': 480}},
                  {'type': 'object', 'properties': {'file': {'type': 'string', 'x-cy-kind': 'Image'}}, 'required': ['file']}),
        operation('export_summary', 'Export a script', 'The storyboard as Markdown or as one self-contained HTML page.',
                  {'project': PROJECT, 'format': {'type': 'string', 'enum': ['md', 'html'], 'default': 'html'}},
                  {'type': 'object', 'properties': {'file': {'type': 'string'}}, 'required': ['file']}),
        operation('export_animatic', 'Export an animatic', 'Every panel for its duration with its transition, as an '
                  'MP4 (captions optional); a panel staged in 3D plays its camera, character and pose moves.',
                  {'project': PROJECT, 'captions': {'type': 'boolean', 'default': True},
                   'fps': {'type': 'integer', 'minimum': 1, 'maximum': 60, 'default': 24},
                   'motion': {'type': 'boolean', 'default': True,
                              'description': 'Render the moves of 3D panels (off: one picture per panel).'},
                   'motion_fps': {'type': 'integer', 'minimum': 4, 'maximum': 24, 'default': 12,
                                  'description': 'Rendered pictures per second for 3D moves.'}},
                  {'type': 'object', 'properties': {'file': {'type': 'string', 'x-cy-kind': 'Video'},
                                                    'duration': {'type': 'number'}}, 'required': ['file']},
                  progress=True),
        operation('add_stage', 'Add a 3D stage', 'A 3D set of simple shapes that panels can be framed in; several '
                  'panels sharing one stage keep the same places from one shot to the next.',
                  {'project': PROJECT, 'name': {'type': 'string', 'maxLength': 200}}),
        operation('update_stage', 'Change a 3D stage', 'Name, sky colour, ground on/off and colour.',
                  {'project': PROJECT, 'stage': {'type': 'string'}, 'name': {'type': 'string', 'maxLength': 200},
                   'sky': {'type': 'string', 'maxLength': 20}, 'ground': {'type': 'boolean'},
                   'groundColour': {'type': 'string', 'maxLength': 20}}, required=['project', 'stage']),
        operation('remove_stage', 'Remove a 3D stage', 'Panels framed in it go back to their images.',
                  {'project': PROJECT, 'stage': {'type': 'string'}}, required=['project', 'stage']),
        operation('add_object', 'Add a shape to a stage', 'Box, sphere, cylinder, cone, capsule, plane, mannequin, or an '
                  'imported mesh (.glb .gltf .obj .ply .stl .off). New shapes stand on the ground.',
                  {'project': PROJECT, 'stage': {'type': 'string'},
                   'shape': {'type': 'string', 'enum': ['box', 'sphere', 'cylinder', 'cone', 'capsule', 'plane',
                                                        'mannequin', 'mesh'], 'default': 'box'},
                   'mesh': {**FILE, 'description': 'Mesh file, for shape = mesh.'}, **OBJECT_FIELDS},
                  required=['project', 'stage']),
        operation('update_object', 'Change a shape', 'Change a shape on its stage (every panel using the stage sees it).',
                  {'project': PROJECT, 'object': {'type': 'string'}, **OBJECT_FIELDS}, required=['project', 'object']),
        operation('duplicate_object', 'Duplicate a shape', 'A copy one metre to the right.',
                  {'project': PROJECT, 'object': {'type': 'string'}}, required=['project', 'object']),
        operation('remove_object', 'Remove a shape', 'Also removes its per-panel placements.',
                  {'project': PROJECT, 'object': {'type': 'string'}}, required=['project', 'object']),
        operation('add_pose', 'Add a character pose', 'A project pose made joint by joint, starting from a '
                  'preset (standing, walking, running, sitting, crouching, arms raised, pointing) or another project '
                  'pose; usable as the pose or end pose of any character.',
                  {'project': PROJECT, 'name': {'type': 'string', 'maxLength': 120},
                   'base': {'type': 'string', 'default': 'standing'}, 'angles': ANGLES,
                   'walks': {'type': 'boolean', 'default': True,
                             'description': 'The legs walk when a character in this pose moves.'}}),
        operation('update_pose', 'Change a character pose', 'Rename a project pose or change some of its joints.',
                  {'project': PROJECT, 'pose': {'type': 'string'}, 'name': {'type': 'string', 'maxLength': 120},
                   'angles': ANGLES, 'walks': {'type': 'boolean'}}, required=['project', 'pose']),
        operation('remove_pose', 'Remove a character pose', 'The characters using it go back to standing.',
                  {'project': PROJECT, 'pose': {'type': 'string'}}, required=['project', 'pose']),
        operation('set_panel_layout', 'Stage a panel', 'Choose how a panel is laid out: its images (image), a 2D drawing, '
                  'or a shot on a 3D stage with a start camera and an optional end camera.',
                  {'project': PROJECT, 'panel': {'type': 'string'},
                   'mode': {'type': 'string', 'enum': ['image', '2d', '3d']}, 'stage': {'type': 'string'},
                   'camera': CAMERA, 'cameraEnd': {'anyOf': [CAMERA, {'type': 'null'}]}, 'drawing': DRAWING},
                  required=['project', 'panel']),
        operation('override_object', 'Place a shape in one panel', 'Move, turn, resize or hide a shape in this panel only '
                  '(a character walking between shots); clear = back to the stage placement.',
                  {'project': PROJECT, 'panel': {'type': 'string'}, 'object': {'type': 'string'},
                   'position': VEC3, 'rotation': VEC3, 'scale': VEC3, 'hidden': {'type': 'boolean'},
                   'positionEnd': {'anyOf': [VEC3, {'type': 'null'}], 'description': 'Where it is at the end of the '
                                                                                    'panel (it moves there); null = still.'},
                   'rotationEnd': {'anyOf': [VEC3, {'type': 'null'}]},
                   'pose': {'type': 'string', 'description': 'Character pose in this panel: ' + ', '.join(POSES) +
                                                            ' or a project pose id (add_pose).'},
                   'poseEnd': {'type': 'string', 'description': 'Pose at the end of the panel (same values).'},
                   'clear': {'type': 'boolean', 'default': False}}, required=['project', 'panel', 'object']),
        operation('render_panel_layout', 'Render a panel layout', 'Render the 2D drawing or the 3D shot (from the start '
                  'or end camera) into the project; it becomes the panel picture. 3D also writes a depth map.',
                  {'project': PROJECT, 'panel': {'type': 'string'},
                   'camera': {'type': 'string', 'enum': ['start', 'end'], 'default': 'start'}},
                  {'type': 'object', 'properties': {'render': {'type': 'string', 'x-cy-kind': 'Image'},
                                                    'depth': {'type': 'string'},
                                                    'project': {'type': 'string'}}, 'required': ['render']},
                  required=['project', 'panel']),
        operation('suggest_camera_move', 'Read the camera move', 'Compare the start and end cameras of a 3D panel and '
                  'name the move (push in, truck, pan, tilt, crane, zoom, arc...) with its amplitude and speed; '
                  'apply = write it into the panel prompt.',
                  {'project': PROJECT, 'panel': {'type': 'string'}, 'apply': {'type': 'boolean', 'default': False}},
                  {'type': 'object', 'properties': {'cameraMove': {'type': 'string'}, 'cameraAmplitude': {'type': 'string'},
                                                    'cameraSpeed': {'type': 'string'}}, 'required': ['cameraMove']},
                  required=['project', 'panel']),
        operation('export_h3_film', 'Export a MiniMax H3 film', 'Turn the storyboard into a multi-segment MiniMax H3 '
                  'film: film.json (a Timeline Director timeline: by default the panels of a sequence grouped into '
                  'windows of about 20 s whose prompt describes the shots in order, overlap frames where the picture '
                  'continues, identity/location/shot pictures per window), its pictures, and two '
                  'ComfyUI workflows (CyTools H3 Film disk sampler, Timeline Director). The same file runs in '
                  'CyTools_MiniMaxH3 on Colab.',
                  {'project': PROJECT, 'folder': {'type': 'string', 'x-cy-kind': 'Directory', 'maxLength': 4096,
                                                  'description': 'Target folder (replaced); default exports/h3_film/<title>.'},
                   'options': FILM_OPTIONS, 'workflows': {'type': 'boolean', 'default': True},
                   'save_options': {'type': 'boolean', 'default': True,
                                    'description': 'Remember these options in the project.'}},
                  FILM_SUMMARY, progress=True),
        operation('export_h3_workflow', 'Convert to a MiniMax H3 workflow',
                  'Convert the storyboard into a CyTools_MiniMaxH3 workflow (workflow.json + media/): one H3 '
                  'generation per panel with its first/last frame, keyframe guides and references (characters, '
                  'layout, locations, videos, voices, sounds), chaining, prompts in the H3 layout, durations '
                  'trimmed to the panels, and a final edit with the storyboard transitions. Run it with '
                  'run_workflow in CyTools_MiniMaxH3.',
                  {'project': PROJECT, 'folder': {'type': 'string', 'x-cy-kind': 'Directory', 'maxLength': 4096,
                                                  'description': 'Target folder (replaced); default exports/h3_workflow/<title>.'},
                   'options': WORKFLOW_OPTIONS, 'save_options': {'type': 'boolean', 'default': True}},
                  WORKFLOW_SUMMARY, progress=True),
        operation('preview_h3_workflow', 'Preview the MiniMax H3 workflow', 'The shots, generations, trims, '
                  'references and prompts the conversion would produce, and the workflow itself, without writing.',
                  {'project': PROJECT, 'options': WORKFLOW_OPTIONS}, WORKFLOW_SUMMARY),
        operation('preview_h3_film', 'Preview a MiniMax H3 film', 'Segments, frame windows, pictures and prompts the '
                  'export would produce, without writing anything.',
                  {'project': PROJECT, 'options': FILM_OPTIONS}, FILM_SUMMARY),
    ] + image_operations()
    return {
        'schemaVersion': 1, 'protocolVersion': '1.0', 'id': 'cy.tool.storyboard', 'name': 'CyTools_Storyboard',
        'version': VERSION,
        'description': 'Storyboards for generated films: timed panels with images, structured prompts, dialogue, '
                       'camera, sound and a reference library; panels staged on shared 3D sets of simple shapes or drawn in 2D; '
                       'contact sheet, script and animatic exports; MiniMax H3 film and workflow exports with '
                       'depth or pose control videos; reference pictures generated in the application (characters, '
                       'places, shots) with Qwen-Image on a private ComfyUI engine, or exported as ComfyUI workflows.',
        'vendor': 'Cyberalien', 'author': 'Cyberalien', 'executable': 'runtime/python/Scripts/python.exe app/tool.py',
        'license': 'GPL-3.0-only (Tool code, see LICENSE).',
        'categories': ['video', 'planning'], 'tags': ['storyboard', 'animatic', 'shot list', 'prompt', 'previs', 'layout'],
        'capabilities': ['jobs', 'cancellation', 'progress'], 'backends': [image_backend()],
        'platforms': [{'os': 'Windows', 'architecture': 'x64', 'status': 'Experimental', 'computeBackends': ['CPU']},
                      {'os': 'Linux', 'architecture': 'x64', 'status': 'Experimental', 'computeBackends': ['CPU'],
                       'notes': 'Launcher script provided, not executed on Linux.'}],
        'interfaces': ['Native', 'CLI', 'JSONL', 'HTTP', 'MCP', 'ImGui'], 'runtimeRequirements': [],
        'concurrency': {'policy': 'Sequential', 'maxWorkers': 1},
        'operations': ops, 'standaloneExecutable': 'CyTools_Storyboard.exe',
        'distributionStatus': 'Development build: see LISEZ-MOI.md',
    }


if __name__ == '__main__':
    target = APP / 'CyTool.json'
    target.write_text(json.dumps(manifest(), indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(target)

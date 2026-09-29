"""Build a small sample storyboard (drawn images, references, dialogue) for UI checks and demos.

    runtime\\python\\Scripts\\python.exe app\\tests\\make_sample.py <parent folder>
"""
import shutil
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from storyboard import model  # noqa: E402


def drawing(path, colour, caption, figure=True):
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (960, 540), colour)
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 360, 960, 540], fill=tuple(max(0, c - 40) for c in colour))
    draw.rectangle([620, 80, 900, 380], outline='white', width=4)
    if figure:
        draw.ellipse([300, 150, 360, 210], outline='white', width=4)
        draw.line([330, 210, 330, 330], fill='white', width=4)
        draw.line([330, 330, 290, 420], fill='white', width=4)
        draw.line([330, 330, 370, 420], fill='white', width=4)
        draw.line([290, 250, 370, 250], fill='white', width=4)
    draw.text((20, 20), caption, fill='white')
    image.save(path)
    return path


def build(parent):
    parent = Path(parent)
    target = parent / 'The courtyard.cystory'
    if target.exists():
        shutil.rmtree(target)
    board = model.Storyboard.create(parent, 'The courtyard')
    board.doc['description'] = 'Lea arrives late to a meeting in a quiet courtyard.'
    board.doc['settings']['style'] = 'Cinematic, live-action, dusk, soft rain'
    sketches = parent / '_sketches'
    sketches.mkdir(exist_ok=True)
    lea = board.add_library_item('character', 'Lea', 'a woman in her thirties, red wool coat',
                                 [drawing(sketches / 'lea.png', (120, 40, 40), 'Lea - red coat')])
    yard = board.add_library_item('location', 'The courtyard', 'a small paved courtyard closed by a stone wall',
                                  [drawing(sketches / 'yard.png', (60, 70, 90), 'courtyard', False)])
    # A voice for Lea, a sound and a motion reference video (generated test media).
    import imageio_ffmpeg
    import subprocess
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    voice, rain, walk = sketches / 'lea_voice.wav', sketches / 'rain.wav', sketches / 'walk.mp4'
    subprocess.run([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i', 'sine=frequency=220:sample_rate=24000',
                    '-t', '4', str(voice)], check=True)
    subprocess.run([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i', 'anoisesrc=color=pink:amplitude=0.2',
                    '-t', '6', str(rain)], check=True)
    subprocess.run([ffmpeg, '-y', '-v', 'error', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=24',
                    '-t', '3', '-pix_fmt', 'yuv420p', str(walk)], check=True)
    lea = board.update_library_item(lea['id'], files=[*[board.folder / f for f in lea['files']], voice])
    rain_item = board.add_library_item('audio', 'Rain ambience', 'light rain on stone', [rain])
    walk_item = board.add_library_item('video', 'Walk cycle', 'a slow, tired walk', [walk])
    board.add_panel(title='Establishing', duration=6,
                    images=[{'file': str(drawing(sketches / 's1.png', (50, 60, 80), 'wide - courtyard', False)), 'role': 'sketch'}],
                    prompt={'scene': 'the courtyard at dusk, wet stones', 'shotSize': 'wide shot',
                            'cameraMove': 'push in', 'cameraSpeed': 'slow', 'sound': 'light rain'},
                    references=[yard['id']], transition={'type': 'crossfade', 'duration': 0.5}, status='ready')
    board.add_panel(title='Lea enters', duration=5,
                    images=[{'file': str(drawing(sketches / 's2.png', (70, 60, 80), 'medium - Lea enters left')), 'role': 'sketch'}],
                    prompt={'action': 'Lea enters from the left and walks toward the camera.', 'shotSize': 'medium shot',
                            'cameraMove': 'tracking shot'},
                    references=[lea['id'], yard['id'], walk_item['id'], rain_item['id']], status='draft')
    board.add_panel(title='Close-up', duration=4,
                    images=[{'file': str(drawing(sketches / 's3.png', (90, 50, 50), 'close-up - Lea')), 'role': 'first'}],
                    prompt={'action': 'She looks up at the window.', 'shotSize': 'close-up',
                            'dialogue': [{'speaker': lea['id'], 'language': 'English', 'line': 'We are late.'}]},
                    references=[lea['id']])
    act2 = board.add_sequence('Inside')
    board.add_panel(sequence_id=act2['id'], title='The door', duration=12,
                    prompt={'action': 'The heavy door opens slowly onto a dark hall.', 'cameraMove': 'pull out'},
                    transition={'type': 'fade to black', 'duration': 1.0})
    # A 3D stage shared by the first two panels, and a drawn 2D panel.
    from storyboard import layout
    stage = layout.add_stage(board, 'Courtyard')
    layout.add_object(board, stage['id'], 'plane', 'Paving', color='#6d6a66', scale=[10, 1, 8], reference=yard['id'])
    layout.add_object(board, stage['id'], 'box', 'Back wall', color='#9b8f80', position=[0, 1.5, -4], scale=[10, 3, 0.4])
    layout.add_object(board, stage['id'], 'box', 'Door', color='#5a4232', position=[2.5, 1.1, -3.75], scale=[1.2, 2.2, 0.2])
    layout.add_object(board, stage['id'], 'cylinder', 'Lamp post', color='#303030', position=[-3, 1.5, -1], scale=[0.15, 3, 0.15])
    person = layout.add_object(board, stage['id'], 'mannequin', 'Lea', reference=lea['id'], position=[-3.5, 0, 1])
    panels = board.panels()
    layout.set_layout(board, panels[0]['id'], mode='3d', stage=stage['id'],
                      camera={'position': [0, 2.2, 9], 'target': [0, 1.2, -2], 'fov': 45},
                      cameraEnd={'position': [0, 1.9, 6], 'target': [0, 1.2, -3], 'fov': 45})
    layout.set_layout(board, panels[1]['id'], mode='3d', stage=stage['id'],
                      camera={'position': [1.5, 1.6, 5], 'target': [-1.5, 1.1, 0], 'fov': 35})
    # Lea walks in during "Lea enters" (a walking cycle), and points at the window at the end of the close-up.
    layout.override_object(board, panels[1]['id'], person['id'], position=[-3.0, 0, 0.5], rotation=[0, 70, 0],
                           positionEnd=[-0.8, 0, 1.2], rotationEnd=[0, 40, 0])
    waves = layout.add_pose(board, 'Lea waves', base='standing',
                            angles={'r_arm': [15, 140, 70], 'head': [25, 10], 'twist': 10})
    layout.override_object(board, panels[1]['id'], person['id'], poseEnd=waves['id'])
    layout.set_layout(board, panels[3]['id'], mode='2d', drawing={'background': '#2b2b30', 'items': [
        {'type': 'rect', 'points': [[0.3, 0.15], [0.7, 0.95]], 'color': '#6b4a35', 'fill': True},
        {'type': 'rect', 'points': [[0.35, 0.2], [0.65, 0.95]], 'color': '#0c0c10', 'fill': True},
        {'type': 'figure', 'points': [[0.5, 0.95]], 'color': '#d0c8b8', 'size': 0.1, 'width': 5},
        {'type': 'arrow', 'points': [[0.8, 0.5], [0.95, 0.5]], 'color': '#e0a030', 'width': 6},
        {'type': 'text', 'points': [[0.03, 0.03]], 'text': 'door opens', 'color': '#ffffff', 'size': 0.06}]})
    for panel in (panels[0], panels[1], panels[3]):
        layout.render_panel(board, panel['id'])
    board.save()
    shutil.rmtree(sketches)
    return board.folder


if __name__ == '__main__':
    print(build(sys.argv[1]))

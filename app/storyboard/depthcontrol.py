"""Control videos of 3D-staged panels for MiniMax H3's Fun ControlNet: depth and character pose.

Source (option controlSource): 'depth' (the set), 'pose' (the characters' OpenPose
skeletons, see pose.py), 'auto' (pose when the panel shows a character, else depth) or
'overlay' (the skeletons drawn over the depth; experimental: Fun ControlNet Union was not
trained on mixed pictures).

A panel staged on a 3D set has a start camera and, optionally, an end camera. Its depth
control is a real video: one depth frame per video frame along the camera move (position,
target, field of view and roll interpolated linearly), with the panel's own placements.
One depth range is used for the whole video (from its first and last frames), so the grey
levels do not flicker as the camera moves. Near is white, far is black.

A blocking is a sketch, not a set: the fidelity level decides how much H3 must follow it,
the same levels as the Unreal blocking of CyTools_MiniMaxH3:

    indicative  strength 0.35, first 35 % of the steps, strong blur   (placement and depth order)
    guided      strength 0.6,  first 60 % of the steps, medium blur
    strict      strength 1.0,  all the steps, no blur                 (shapes followed closely)
    custom      strength / end / blur of your choice

Blur = downscale, Gaussian blur, upscale and grey-level quantisation: the layout stays, the
exact shape of the boxes and capsules goes.
"""
import math
from pathlib import Path

import numpy as np

from . import layout as layouts
from .model import StoryboardError

FPS = 24
FIDELITY = {
    'indicative': {'strength': 0.35, 'start': 0.0, 'end': 0.35, 'blur': 'strong'},
    'guided': {'strength': 0.6, 'start': 0.0, 'end': 0.6, 'blur': 'medium'},
    'strict': {'strength': 1.0, 'start': 0.0, 'end': 1.0, 'blur': 'none'},
}
LEVELS = ('off', *FIDELITY, 'custom')
SOURCES = ('auto', 'depth', 'pose', 'overlay')
BLUR = {'none': None, 'medium': (6, 2, 16), 'strong': (12, 3, 32)}


def settings(options):
    """{'strength', 'start', 'end', 'blur'} for the chosen level, or None when depth control is off."""
    level = options.get('depthControl', 'off')
    if level not in LEVELS:
        raise StoryboardError(f'depthControl must be one of {", ".join(LEVELS)}.')
    if level == 'off':
        return None
    if level == 'custom':
        values = {'strength': float(options.get('controlStrength', 0.5)), 'start': 0.0,
                  'end': float(options.get('controlEnd', 0.5)), 'blur': options.get('controlBlur', 'medium')}
    else:
        values = dict(FIDELITY[level])
    if values['blur'] not in BLUR:
        raise StoryboardError('controlBlur must be none, medium or strong.')
    if not 0 < values['strength'] <= 2 or not 0 < values['end'] <= 1:
        raise StoryboardError('The control strength goes up to 2 and its end from 0 to 1 (share of the steps).')
    return values


def staged(board, panel):
    """The panel's 3D stage when it is staged in 3D, else None."""
    state = layouts.ensure(panel)
    if state['mode'] != '3d' or not state['stage']:
        return None
    try:
        return layouts.stage(board, state['stage'])
    except StoryboardError:
        return None


def camera_at(panel, t):
    """The camera of a 3D panel at t in [0, 1] of its move."""
    state = layouts.ensure(panel)
    start, end = state['camera'], state.get('cameraEnd') or state['camera']
    t = min(1.0, max(0.0, float(t)))

    def lerp(a, b):
        return [float(x) + (float(y) - float(x)) * t for x, y in zip(a, b)]
    return {'position': lerp(start['position'], end['position']), 'target': lerp(start['target'], end['target']),
            'fov': start.get('fov', 40.0) + (end.get('fov', 40.0) - start.get('fov', 40.0)) * t,
            'roll': start.get('roll', 0.0) + (end.get('roll', 0.0) - start.get('roll', 0.0)) * t}


def _depth(board, panel, t, size):
    from . import render3d
    state = layouts.ensure(panel)
    result = render3d.renderer().render(staged(board, panel), camera_at(panel, t), size, state['overrides'],
                                        folder=board.folder, grid=True, want_depth=True, t=t,
                                        poses=board.doc.get('poses'))
    return result['depth']


def characters_at(board, panel, t):
    from . import pose, render3d
    state = layouts.ensure(panel)
    return [(item, t) for item in render3d.resolved_objects(staged(board, panel), state['overrides'], t,
                                                            board.doc.get('poses'))
            if pose.is_character(item)]


def _pose(board, panel, t, size, hands=True, feet=True):
    from . import pose
    return pose.draw(characters_at(board, panel, t), camera_at(panel, t), size, hands=hands, feet=feet)


def shows_characters(board, panel):
    """Whether a character of the panel is in frame at its start, middle or end."""
    from . import pose
    from .render3d import camera_matrices
    if staged(board, panel) is None:
        return False
    for t in (0.0, 0.5, 1.0):
        camera = camera_at(panel, t)
        view, projection = camera_matrices(camera, 16 / 9)
        for item, _ in characters_at(board, panel, t):
            neck = pose.world_joints(item, t)[1]
            clip = projection @ view @ np.append(neck, 1.0)
            if clip[3] > 0 and abs(clip[0] / clip[3]) <= 1 and abs(clip[1] / clip[3]) <= 1:
                return True
    return False


def source_for(board, panel, options):
    """'depth' or 'pose' or 'overlay' for one panel (auto: pose when a character is in frame)."""
    source = options.get('controlSource', 'auto')
    if source not in SOURCES:
        raise StoryboardError(f'controlSource must be one of {", ".join(SOURCES)}.')
    if source == 'auto':
        return 'pose' if shows_characters(board, panel) else 'depth'
    return source


def _range(samples):
    finite = np.concatenate([d[np.isfinite(d)] for d in samples]) if samples else np.array([])
    if not finite.size:
        return 0.0, 1.0
    near = float(np.percentile(finite, 1))
    median = float(np.percentile(finite, 50))
    far = min(float(np.percentile(finite, 97)), near + 3.0 * max(median - near, 0.5))
    return near, max(far, near + 0.1)


def _grey(depth, near, far, blur):
    from PIL import Image, ImageFilter
    value = np.clip((far - np.nan_to_num(depth, posinf=far)) / (far - near), 0, 1)
    grey = (value * 255).astype(np.uint8)
    if BLUR.get(blur):
        factor, sigma, step = BLUR[blur]
        height, width = grey.shape
        image = Image.fromarray(grey).resize((max(2, width // factor), max(2, height // factor)), Image.BOX)
        image = image.filter(ImageFilter.GaussianBlur(sigma)).resize((width, height), Image.BICUBIC)
        grey = (np.asarray(image) // step * step).astype(np.uint8)
    return grey


def write_video(board, samples, path, size, blur='none', source='depth', hands=True, feet=True):
    """samples: [(panel, t)] one per video frame (24 fps). Writes an H.264 MP4 of control frames:
    depth (grey), pose (OpenPose skeletons on black, with the hands and feet when asked) or overlay
    (skeletons over the depth)."""
    import imageio_ffmpeg
    if not samples:
        raise StoryboardError('A control video needs at least one frame.')
    if source not in ('depth', 'pose', 'overlay'):
        raise StoryboardError(f'Unknown control source {source!r}.')
    for panel, _ in samples:
        if staged(board, panel) is None:
            raise StoryboardError(f'Panel "{panel["title"]}" is not staged in 3D: it has no depth or pose.')
    size = (int(size[0]) // 2 * 2, int(size[1]) // 2 * 2)
    if source != 'pose':
        near, far = _range([_depth(board, *samples[0], size), _depth(board, *samples[-1], size)])
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = imageio_ffmpeg.write_frames(str(path), size, fps=FPS, codec='libx264', pix_fmt_in='rgb24',
                                         pix_fmt_out='yuv420p', output_params=['-crf', '12'], macro_block_size=2)
    writer.send(None)
    try:
        cache = {}
        for panel, t in samples:
            key = (panel['id'], round(t, 6))
            if key not in cache:
                if source == 'pose':
                    frame = _pose(board, panel, t, size, hands, feet)
                else:
                    grey = _grey(_depth(board, panel, t, size), near, far, blur)
                    frame = np.repeat(grey[..., None], 3, axis=2)
                    if source == 'overlay':
                        skeleton = _pose(board, panel, t, size, hands, feet)
                        drawn = skeleton.any(axis=2)
                        frame[drawn] = skeleton[drawn]
                cache = {key: np.ascontiguousarray(frame)}
            writer.send(cache[key])
    finally:
        writer.close()
    return path


def write_picture(board, panel, path, size, source='depth', blur='none', t=0.0, hands=True, feet=True):
    """One control picture of a 3D panel at t of its move, as a PNG: depth (grey, near is white),
    pose (OpenPose skeletons on black) or overlay (skeletons over the depth)."""
    from PIL import Image
    if staged(board, panel) is None:
        raise StoryboardError(f'Panel "{panel["title"]}" is not staged in 3D: it has no depth or pose.')
    if source not in ('depth', 'pose', 'overlay'):
        raise StoryboardError(f'Unknown control source {source!r}.')
    size = (int(size[0]), int(size[1]))
    if source == 'pose':
        frame = _pose(board, panel, t, size, hands, feet)
    else:
        depth = _depth(board, panel, t, size)
        near, far = _range([depth])
        frame = np.repeat(_grey(depth, near, far, blur)[..., None], 3, axis=2)
        if source == 'overlay':
            skeleton = _pose(board, panel, t, size, hands, feet)
            drawn = skeleton.any(axis=2)
            frame[drawn] = skeleton[drawn]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(np.ascontiguousarray(frame)).save(path)
    return path


def panel_samples(panel, frames, start_seconds=0.0):
    """Frames of a panel's move: frame f is at (start + f / 24) seconds of the panel."""
    duration = max(float(panel['duration']), 1 / FPS)
    return [(panel, min(1.0, (start_seconds + f / FPS) / duration)) for f in range(int(frames))]


def frame_count(seconds):
    """H3's frame count for a duration (17k + 5, rounded up)."""
    frames = max(5, round(seconds * FPS))  # as CyTools_MiniMaxH3 (spec.frames_for_duration)
    while frames % 17 != 5:
        frames += 1
    return frames

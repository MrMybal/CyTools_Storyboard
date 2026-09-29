"""What a storyboard becomes outside the application: a contact sheet, a summary, an animatic.

Everything is rendered locally with Pillow and the ffmpeg shipped by imageio-ffmpeg; no
model, no network. Every function takes a `cancelled()` callable and runs ffmpeg as a child
process with an argument list, killed on cancellation.
"""
import html
import subprocess
import tempfile
import time
from pathlib import Path

from .model import describe_camera

CANVAS = {'16:9': (1280, 720), '21:9': (1680, 720), '2.39:1': (1720, 720), '4:3': (960, 720), '1:1': (720, 720),
          '3:4': (720, 960), '9:16': (720, 1280)}
PALETTE = ['#3b5b92', '#7a3b92', '#92653b', '#3b926b', '#923b4a', '#5f6b7a']


class ExportError(RuntimeError):
    pass


def _font(size):
    from PIL import ImageFont
    try:
        import imgui_bundle
        path = Path(imgui_bundle.__file__).parent / 'assets' / 'fonts' / 'DroidSans.ttf'
        return ImageFont.truetype(str(path), size)
    except Exception:  # fall back on Pillow's bitmap font rather than failing an export
        return ImageFont.load_default()


def _wrap(draw, text, font, width):
    words, lines, line = str(text).split(), [], ''
    for word in words:
        trial = (line + ' ' + word).strip()
        if draw.textlength(trial, font=font) <= width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def main_image(board, panel):
    """The picture that stands for a panel: its 2D/3D layout render when it uses one, else the
    sketch, then first frame, keyframe, reference."""
    layout = panel.get('layout') or {}
    if layout.get('mode') in ('2d', '3d') and layout.get('render') and (board.folder / layout['render']).is_file():
        return board.folder / layout['render']
    for role in ('sketch', 'first', 'keyframe', 'reference', 'last'):
        for image in panel['images']:
            if image['role'] == role and (board.folder / image['file']).is_file():
                return board.folder / image['file']
    return None


def sentence(text):
    """'wet stones' -> 'Wet stones.' so parts joined with spaces read as sentences."""
    text = (text or '').strip()
    if not text:
        return ''
    if text[-1] not in '.!?"\')…»':
        text += '.'
    return text[0].upper() + text[1:]


def panel_text(board, panel):
    prompt = panel['prompt']
    names = {item['id']: item['name'] for item in board.doc['library']}
    parts = []
    shot = ' '.join(x for x in (prompt.get('shotSize'), prompt.get('angle') and f'({prompt["angle"]})') if x)
    if shot:
        parts.append(shot[0].upper() + shot[1:] + '.')
    for key in ('scene', 'action'):
        if prompt.get(key):
            parts.append(sentence(prompt[key]))
    camera = describe_camera(prompt)
    if camera:
        parts.append(camera)
    for line in prompt.get('dialogue') or []:
        speaker = names.get(line.get('speaker'), line.get('speaker') or '')
        if line.get('line'):
            parts.append(f'{speaker}: "{line["line"]}"' if speaker else f'"{line["line"]}"')
    if prompt.get('freeText'):
        parts.append(sentence(prompt['freeText']))
    return ' '.join(parts)


def frame(board, panel, size, caption=True, number=None, picture=None):
    """A panel as one image of the canvas size: letterboxed picture (its main image, or `picture`,
    a PIL image such as one moment of a 3D move) or a title card, plus caption."""
    from PIL import Image, ImageDraw
    width, height = size
    canvas = Image.new('RGB', size, (18, 18, 20))
    source = main_image(board, panel) if picture is None else None
    draw = ImageDraw.Draw(canvas)
    if picture is not None:
        picture = picture.convert('RGB')
        picture.thumbnail(size)
        canvas.paste(picture, ((width - picture.width) // 2, (height - picture.height) // 2))
    elif source:
        with Image.open(source) as picture:
            picture = picture.convert('RGB')
            picture.thumbnail(size)
            canvas.paste(picture, ((width - picture.width) // 2, (height - picture.height) // 2))
    else:
        colour = panel.get('color') or PALETTE[hash(panel['id']) % len(PALETTE)]
        canvas.paste(colour, (0, 0, width, height))
        font = _font(max(18, height // 12))
        lines = _wrap(draw, panel['title'] or 'Untitled', font, width * 0.8)
        y = height // 2 - len(lines) * font.size // 2
        for line in lines:
            draw.text(((width - draw.textlength(line, font=font)) / 2, y), line, fill='white', font=font)
            y += int(font.size * 1.2)
    if caption:
        font = _font(max(14, height // 34))
        text = panel_text(board, panel)
        header = (f'{number}. ' if number else '') + f'{panel["title"]}  -  {panel["duration"]:.1f} s'
        lines = [header] + _wrap(draw, text, font, width - 40)[:3]
        band = int(len(lines) * font.size * 1.3 + 16)
        overlay = Image.new('RGBA', (width, band), (0, 0, 0, 170))
        canvas.paste(overlay, (0, height - band), overlay)
        y = height - band + 8
        for index, line in enumerate(lines):
            draw.text((20, y), line, fill='white' if index else (255, 214, 120), font=font)
            y += int(font.size * 1.3)
    return canvas


def contact_sheet(board, target, columns=4, cell_width=480):
    """All panels as a printable grid with numbers, durations and descriptions."""
    from PIL import Image, ImageDraw
    panels = board.panels()
    if not panels:
        raise ExportError('The storyboard has no panel yet.')
    aspect = CANVAS.get(board.doc['settings']['aspect'], (1280, 720))
    cell_height = int(cell_width * aspect[1] / aspect[0])
    text_height = 110
    rows = (len(panels) + columns - 1) // columns
    title_height = 70
    sheet = Image.new('RGB', (columns * (cell_width + 20) + 20, title_height + rows * (cell_height + text_height + 20)),
                      (245, 245, 242))
    draw = ImageDraw.Draw(sheet)
    title_font, text_font, bold = _font(34), _font(15), _font(18)
    total = board.total_duration()
    draw.text((20, 18), f'{board.doc["title"]}  -  {len(panels)} panels  -  {int(total // 60)}:{total % 60:04.1f}',
              fill=(20, 20, 20), font=title_font)
    timeline = {row['id']: row for row in board.timeline()}
    for index, panel in enumerate(panels):
        x = 20 + (index % columns) * (cell_width + 20)
        y = title_height + (index // columns) * (cell_height + text_height + 20)
        sheet.paste(frame(board, panel, (cell_width, cell_height), caption=False), (x, y))
        start = timeline[panel['id']]['start']
        draw.text((x, y + cell_height + 6), f'{index + 1}. {panel["title"]}   {panel["duration"]:.1f} s   @ {start:.1f} s',
                  fill=(20, 20, 20), font=bold)
        for line_index, line in enumerate(_wrap(draw, panel_text(board, panel), text_font, cell_width)[:4]):
            draw.text((x, y + cell_height + 32 + line_index * 18), line, fill=(60, 60, 60), font=text_font)
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target)
    return target


def summary(board, target, kind='md'):
    """A readable script of the storyboard (Markdown or a self-contained HTML page)."""
    panels = board.panels()
    timeline = {row['id']: row for row in board.timeline()}
    names = {item['id']: item['name'] for item in board.doc['library']}
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if kind == 'md':
        lines = [f'# {board.doc["title"]}', '', board.doc.get('description', ''), '',
                 f'Total: {board.total_duration():.1f} s, {len(panels)} panels, aspect {board.doc["settings"]["aspect"]}', '']
        if board.doc['library']:
            lines += ['## References', '']
            for item in board.doc['library']:
                lines.append(f'- **{item["name"]}** ({item["kind"]}): {item.get("description", "")}')
            lines.append('')
        number = 0
        for sequence in board.sequences():
            lines += [f'## {sequence["title"]}', '']
            for panel in sequence['panels']:
                number += 1
                row = timeline[panel['id']]
                lines.append(f'### {number}. {panel["title"]} - {panel["duration"]:.1f} s ({row["start"]:.1f}-{row["end"]:.1f} s)')
                image = main_image(board, panel)
                if image:
                    lines.append(f'![{panel["title"]}]({Path(image).relative_to(board.folder).as_posix()})')
                lines.append(panel_text(board, panel))
                refs = [names.get(r, r) for r in panel['references']]
                if refs:
                    lines.append('References: ' + ', '.join(refs))
                if panel['prompt'].get('sound'):
                    lines.append('Sound: ' + panel['prompt']['sound'])
                if panel['prompt'].get('music'):
                    lines.append('Music: ' + panel['prompt']['music'])
                if panel['notes']:
                    lines.append('Notes: ' + panel['notes'])
                lines.append(f'Transition: {panel["transition"]["type"]}')
                lines.append('')
        target.write_text('\n'.join(lines), encoding='utf-8')
        return target
    import base64
    parts = [f'<!doctype html><meta charset="utf-8"><title>{html.escape(board.doc["title"])}</title>',
             '<style>body{font-family:sans-serif;max-width:1100px;margin:auto;background:#f6f6f3}'
             '.p{display:flex;gap:16px;background:white;margin:10px 0;padding:10px;border-radius:6px}'
             '.p img{width:360px;border-radius:4px}.t{color:#666;font-size:13px}</style>',
             f'<h1>{html.escape(board.doc["title"])}</h1><p class="t">{board.total_duration():.1f} s - {len(panels)} panels</p>']
    number = 0
    for sequence in board.sequences():
        parts.append(f'<h2>{html.escape(sequence["title"])}</h2>')
        for panel in sequence['panels']:
            number += 1
            image = main_image(board, panel)
            tag = ''
            if image:
                data = base64.b64encode(Path(image).read_bytes()).decode()
                mime = 'png' if image.suffix.lower() == '.png' else 'jpeg'
                tag = f'<img src="data:image/{mime};base64,{data}">'
            parts.append(f'<div class="p">{tag}<div><b>{number}. {html.escape(panel["title"])}</b> '
                         f'<span class="t">{panel["duration"]:.1f} s</span><p>{html.escape(panel_text(board, panel))}</p>'
                         f'<p class="t">{html.escape(panel["notes"])}</p></div></div>')
    target.write_text(''.join(parts), encoding='utf-8')
    return target


def _ffmpeg(arguments, cancelled):
    import imageio_ffmpeg
    command = [imageio_ffmpeg.get_ffmpeg_exe(), '-hide_banner', '-nostdin', '-y', '-loglevel', 'error',
               *[str(a) for a in arguments]]
    with tempfile.TemporaryFile() as log:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=log,
                                   creationflags=0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        while process.poll() is None:
            if cancelled():
                process.kill()
                process.wait()
                raise ExportError('Cancelled.')
            time.sleep(0.05)
        log.seek(0)
        error = log.read().decode('utf-8', 'replace')
    if process.returncode:
        raise ExportError('ffmpeg failed: ' + ' | '.join(error.strip().splitlines()[-3:]))


def moves(board, panel):
    """Whether a panel is staged in 3D with something that changes during it (camera move, a
    character or object moving, turning or changing pose)."""
    from . import layout as layouts
    state = panel.get('layout') or {}
    if state.get('mode') != '3d' or not state.get('stage'):
        return False
    if state.get('cameraEnd'):
        return True
    return any(o.get('positionEnd') or o.get('rotationEnd') or o.get('poseEnd')
               for o in (layouts.ensure(panel).get('overrides') or {}).values())


def _moving_clip(board, panel, size, clip, captions, number, fps, motion_fps, fades, cancelled):
    """Render a 3D panel along its move (camera, characters, poses) into an MP4 clip."""
    import imageio_ffmpeg
    import numpy as np
    from PIL import Image
    from . import depthcontrol, layout as layouts, render3d
    state = layouts.ensure(panel)
    stage = layouts.stage(board, state['stage'])
    count = max(2, int(round(panel['duration'] * motion_fps)))
    writer = imageio_ffmpeg.write_frames(str(clip), size, fps=motion_fps, codec='libx264', pix_fmt_in='rgb24',
                                         pix_fmt_out='yuv420p', macro_block_size=2,
                                         output_params=['-vf', ','.join(fades + [f'fps={fps}']), '-preset', 'veryfast',
                                                        '-t', f'{panel["duration"]:.3f}'])
    writer.send(None)
    try:
        for index in range(count):
            if cancelled():
                raise ExportError('Cancelled.')
            t = index / (count - 1)
            result = render3d.renderer().render(stage, depthcontrol.camera_at(panel, t), size, state['overrides'],
                                                folder=board.folder, t=t, poses=board.doc.get('poses'))
            image = frame(board, panel, size, caption=captions, number=number, picture=Image.fromarray(result['color']))
            writer.send(np.ascontiguousarray(np.asarray(image)))
    finally:
        writer.close()


def animatic(board, target, captions=True, fps=24, cancelled=lambda: False, progress=lambda f, text: None,
             motion=True, motion_fps=12):
    """Each panel for its duration, with its transition, as an MP4 you can play and share. With
    `motion`, a panel staged in 3D plays its move (camera, characters, poses) at `motion_fps`
    rendered pictures per second instead of holding one picture."""
    panels = board.panels()
    if not panels:
        raise ExportError('The storyboard has no panel yet.')
    size = CANVAS.get(board.doc['settings']['aspect'], (1280, 720))
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='animatic-') as folder:
        folder = Path(folder)
        clips = []
        for index, panel in enumerate(panels):
            if cancelled():
                raise ExportError('Cancelled.')
            progress(index / len(panels) * 0.8, f'{index + 1}/{len(panels)} {panel["title"]}')
            clip = folder / f'{index:04d}.mp4'
            fades = []
            if panel['transition']['type'] == 'fade to black':
                start = max(0.0, panel['duration'] - panel['transition']['duration'])
                fades.append(f'fade=t=out:st={start:.3f}:d={panel["transition"]["duration"]:.3f}')
            if index and panels[index - 1]['transition']['type'] == 'fade from black':
                fades.append(f'fade=t=in:st=0:d={panels[index - 1]["transition"]["duration"]:.3f}')
            if motion and moves(board, panel):
                _moving_clip(board, panel, size, clip, captions, index + 1, fps, motion_fps, fades, cancelled)
                clips.append((clip, panel))
                continue
            still = folder / f'{index:04d}.png'
            frame(board, panel, size, caption=captions, number=index + 1).save(still)
            _ffmpeg(['-loop', 1, '-framerate', fps, '-i', still, '-t', f'{panel["duration"]:.3f}',
                     *(['-vf', ','.join(fades)] if fades else []), '-c:v', 'libx264', '-preset', 'veryfast',
                     '-pix_fmt', 'yuv420p', '-r', fps, clip], cancelled)
            clips.append((clip, panel))
        progress(0.85, 'Joining')
        arguments = []
        for clip, _ in clips:
            arguments += ['-i', clip]
        # Same frame rate, time base and pixel aspect for every clip (xfade refuses mixed ones:
        # a held picture and a rendered 3D move are encoded differently).
        chain = [f'[{index}:v]fps={fps},settb=AVTB,setsar=1,format=yuv420p[n{index}]' for index in range(len(clips))]
        label, clock = '[n0]', clips[0][1]['duration']
        for index in range(1, len(clips)):
            previous = clips[index - 1][1]
            if previous['transition']['type'] == 'crossfade':
                duration = min(previous['transition']['duration'], previous['duration'] / 2, clips[index][1]['duration'] / 2)
                offset = clock - duration
                chain.append(f'{label}[n{index}]xfade=transition=fade:duration={duration:.3f}:offset={offset:.3f}[v{index}]')
                clock = offset + clips[index][1]['duration']
            else:
                chain.append(f'{label}[n{index}]concat=n=2:v=1:a=0[v{index}]')
                clock += clips[index][1]['duration']
            label = f'[v{index}]'
        arguments += ['-filter_complex', ';'.join(chain), '-map', label]
        _ffmpeg([*arguments, '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', target],
                cancelled)
    progress(1.0, 'Done')
    return target

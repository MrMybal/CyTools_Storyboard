"""Small UI helpers: non-blocking file dialogs, thumbnails, opening files."""
import os
import subprocess
import sys
from pathlib import Path

from imgui_bundle import hello_imgui, imgui as native, portable_file_dialogs as pfd

from ui_common import tr
from cyui_modules.images import ImageData, ImageState, image_viewport

IMAGE_FILTER = ['Images', '*.png *.jpg *.jpeg *.webp *.bmp']
MEDIA_FILTER = ['Media', '*.png *.jpg *.jpeg *.webp *.bmp *.wav *.mp3 *.flac *.ogg *.m4a *.mp4 *.mov *.webm *.mkv']


def open_local(path):
    path = Path(path)
    if not path.exists():
        return
    if os.name == 'nt':
        os.startfile(path)
    else:
        subprocess.Popen(['open' if sys.platform == 'darwin' else 'xdg-open', str(path)])


class Dialogs:
    """Portable file dialogs are asynchronous: start one, poll it every frame."""

    def __init__(self):
        self._pending = {}

    def open(self, key, title, filters, folder='', multiple=False):
        if key not in self._pending:
            options = pfd.opt.multiselect if multiple else pfd.opt.none
            self._pending[key] = ('open', pfd.open_file(tr(title), str(folder or Path.home()), filters, options))

    def folder(self, key, title, folder=''):
        if key not in self._pending:
            self._pending[key] = ('folder', pfd.select_folder(tr(title), str(folder or Path.home())))

    def save(self, key, title, filters, default=''):
        if key not in self._pending:
            self._pending[key] = ('save', pfd.save_file(tr(title), str(default or Path.home()), filters))

    def result(self, key):
        entry = self._pending.get(key)
        if not entry or not entry[1].ready():
            return None
        kind, dialog = self._pending.pop(key)
        value = dialog.result()
        if kind == 'open':
            return list(value or [])
        return [value] if value else []


dialogs = Dialogs()


class Textures:
    """Images uploaded once per (path, mtime, size)."""

    def __init__(self, limit=256):
        self.cache, self.limit = {}, limit
        self.dimensions = {}

    def get(self, path, max_side=256):
        try:
            stat = Path(path).stat()
        except (OSError, TypeError):
            return None
        key = (str(path), stat.st_mtime_ns, max_side)
        if key in self.cache:
            return self.cache[key]
        try:
            import numpy as np
            from PIL import Image
            with Image.open(path) as image:
                self.dimensions[key]=image.size
                image.thumbnail((max_side, max_side))
                rgba = np.ascontiguousarray(np.asarray(image.convert('RGBA'), dtype=np.uint8))
            texture = hello_imgui.create_texture_gpu_from_rgba_data(rgba)
        except Exception:
            texture = None
        if len(self.cache) >= self.limit:
            oldest=next(iter(self.cache))
            self.cache.pop(oldest)
            self.dimensions.pop(oldest,None)
        self.cache[key] = texture
        return texture


textures = Textures()
_preview_states = {}


def image(path, width, height, max_side=512):
    """Draw a file fitted into width x height; return the size drawn (0, 0 if nothing)."""
    texture = textures.get(path, max_side) if path else None
    if texture is None:
        return 0, 0
    if max_side>=512:
        key=(str(path),native.get_id('##image-preview'))
        state=_preview_states.setdefault(key,ImageState())
        if len(_preview_states)>256:
            for previous in list(_preview_states)[:-128]:_preview_states.pop(previous,None)
        stat=Path(path).stat()
        source_width,source_height=textures.dimensions.get((str(path),stat.st_mtime_ns,max_side),(texture.width,texture.height))
        image_viewport('##image-preview',state,ImageData(texture.texture_id(),source_width,source_height),
                       (max(1,width),max(1,height)))
        return width,height
    scale = min(width / max(texture.width, 1), height / max(texture.height, 1))
    w, h = max(1, texture.width * scale), max(1, texture.height * scale)
    native.image(native.ImTextureRef(texture.texture_id()), native.ImVec2(w, h))
    return w, h


def colour(value, fallback=(0.23, 0.36, 0.57, 1.0)):
    """'#rrggbb' -> ImVec4."""
    try:
        value = value.lstrip('#')
        return native.ImVec4(int(value[0:2], 16) / 255, int(value[2:4], 16) / 255, int(value[4:6], 16) / 255, 1.0)
    except (AttributeError, ValueError, IndexError):
        return native.ImVec4(*fallback)


def hex_colour(vec):
    return '#%02x%02x%02x' % (int(vec[0] * 255), int(vec[1] * 255), int(vec[2] * 255))

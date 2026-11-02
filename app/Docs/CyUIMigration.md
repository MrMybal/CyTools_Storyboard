# Modular CyUI integration

The standalone application includes unmodified CyUI 1.2.0 Python sources, pinned to
revision 8367401fe45fc22bfed5e227cb3de343177f676b. The source hashes and selected modules
are recorded in app/cyui-source.json. The installed application does not need an upstream checkout or account.

## Modules and ownership

Core, Canvas, Timeline, Inspector, Images, Viewport and Diagnostics.

The custom timeline is replaced by the common timeline with pointer zoom/pan, selection,
ruler seeking and duration handles. Overlapping crossfades use separate visual lanes so
both edges remain reachable. A drag is a preview until commit, Escape cancels, and an
external document revision cancels stale gestures. One committed gesture produces one
existing host Undo transaction. Moving a clip reorders its panel inside its sequence:
this document format owns sequential timing, rather than free gaps or arbitrary tracks.

Panel title, duration and status use the typed common Inspector. Duration presets and
project-specific controls remain available. The 3D render is displayed through Viewport;
the existing camera, asynchronous renderer, object picking, pose handles and ImGuizmo
remain host-owned. The 2D drawing uses Canvas clipping and pointer-centred navigation;
existing drawing tools and the host history remain intact. Large image/animatic previews
use Images with original source dimensions; compact thumbnails retain their lightweight
host image call. Structured logs retain raw selection and whole-file copy.

The board cards and reference-library payloads remain application views: they carry
story ordering, panel prompts, reference roles and project-specific drag/drop actions.
Character posing, 3D rendering, film/workflow exports, project persistence, jobs, image
generation and models remain in the host. CyUI does not implement these engines.

## Build and maintenance

Keep the vendored files unchanged. Application adapters live under gui/ and in
gui_log_view.py. Refresh only from the pinned checkout using
python app/scripts/sync_cyui.py PATH_TO_CYUI. Existing source/release builders include
the selected package and notices. No CMake umbrella, demo, Gallery, browser/CEF or
second Dear ImGui instance is introduced. Existing imgui-bundle remains pinned.

Run the application suite and tests/test_modular_ui.py with runtime/python's Python.
Build the launcher using app/build_launcher.ps1 and validate the actual Windows package.
Tests cover source integrity, cached diagnostics, actual ImGui frames in five themes,
both densities, English/French and simulated DPI scales. This does not certify physical
multi-monitor behavior. Linux/macOS execution remains unverified for this migration.

English remains the default. French, themes, density and text size remain persistent.
Application catalogs are shared with the selected CyUI locale without translating user
messages, model IDs, project data or file paths.

## License

CyUI is MIT: the complete text is included in LICENCES/CyUI-MIT.txt at the product root
and in app/LICENCES. Upstream license: https://github.com/MrMybal/CyUI/blob/main/LICENSE.
The application's own license and all dependency/model licenses remain unchanged.

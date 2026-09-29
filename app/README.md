# CyTools_Storyboard — developer notes

Storyboard editor built on CyToolsCore 0.9.0 (scaffolded with `cytools new --desktop`).

| Path | Content |
|---|---|
| `storyboard/model.py` | Document (`cytools.storyboard/1`), project folder `.cystory`, content-addressed assets, sequences/panels/library, timeline (crossfades overlap), validation, migration, atomic save with 5 backups |
| `storyboard/export.py` | Contact sheet (Pillow), Markdown/HTML script, animatic MP4 (ffmpeg from imageio-ffmpeg; cut, crossfade, fades; 3D panels rendered along their camera, object and pose moves, clips normalised before xfade) |
| `storyboard/render3d.py` | Offscreen OpenGL renderer (moderngl): primitives, mannequin, meshes (trimesh), per-panel overrides, depth in metres, object-id picking, camera frustums; one GL context per thread |
| `storyboard/layout.py` | Stages, objects, per-panel overrides, panel layout (image/2d/3d), 2D drawing raster, render into `assets/renders/`, camera move read from start/end cameras |
| `storyboard/h3film.py`, `storyboard/comfy_workflow.py` | MiniMax H3 film: panels → Timeline Director windows (5 + 17n frames, overlaps), pictures, reference videos (clips placed after the carried frames, `hasAudio: false`, `referenceMode: edit`, `cytoolsSegment`), sounds (voices, audio items, video sound) and prompts per segment (every sentence an option), 12-reference cap, film.json + images/ + media/ + two ComfyUI editor workflows |
| `gui/film_export.py` | Export window with the live segment table |
| `storyboard/depthcontrol.py` | Control videos of 3D panels along their camera move for Fun ControlNet, used by both exports: depth (fixed range, fidelity blur), pose, auto, overlay |
| `storyboard/pose.py` | Character skeleton (OpenPose COCO-18) posed by angles (lean, twist, side bend, pelvis tilt, hands: five finger curls, a spread and the wrist bend (towards the palm, towards the thumb), feet: pitch and toes (flat on the ground at 0, heading from the shin; `skeleton(..., feet=True)` / `world_feet`: ankle, heel, ball, toe tips, big and small toe; drawn in the OpenPose control as BODY_25 feet, option `poseFeet`; the lowest sole point stands on the ground), with an OpenPose 21-point hand per side from `skeleton(..., hands=True)` / `world_hands`, head turn/tilt, 4 per limb: forwards, sideways, bend, turn about itself — 3-angle poses still load, seat), presets and project poses (`doc['poses']`, joint by joint, bounded), walking cycle from the distance covered, end pose, two-bone IK (`reach`: wrist/ankle to a world point, exact within the limits), `swivel` (elbow/knee turned about the root-end line, hand or foot kept), `look` (head towards a point), `lean_to` (shoulder: upper body lean/twist/side bend; neck: lean/side bend), `curl` (fingertip: that finger's curl), `bend_wrist` (palm handle at the knuckles), `bend_toes` (toe tips), `tilt_pelvis` (hip: pelvis tilted about the other hip, legs re-planted, upper body kept), `shift_pelvis` (pelvis handle between the hips, `handle_point`: pelvis moved over planted feet, returns the position shift); the layout editor exposes them all as handles in the 3D view, OpenPose drawing; the 3D mannequin is built on it (`render3d._posed_mannequin`) |
| `storyboard/h3workflow.py`, `gui/workflow_export.py` | Conversion into a CyTools_MiniMaxH3 workflow (`cytools.minimax_h3.workflow/1`): one generate step per panel (4-15 s, long panels split into chained parts, trims to the exact duration, frame extraction for chaining), first/last frames, keyframe guides, references, H3 structured prompts, final concat with per-seam transitions; window with the live shot table |
| `tool.py` | 37 operations (storyboard, panels, sequences, library, stages, objects, panel layouts, renders, camera move, exports) |
| `build_manifest.py` | Writes `CyTool.json` |
| `gui/main.py` | Dear ImGui editor: library, board with drag and drop, inspector, timeline with duration handles, animatic player, undo/redo, autosave, reload of external edits |
| `gui/layout_editor.py` | Layout tab: 3D viewport rendered on a worker thread (own GL context, latest request wins), ImGuizmo gizmo, picking, orbit/pan/zoom of the view or of a shot camera, 2D canvas; auto-render of panel pictures |
| `gui/updates.py`, `maintenance.py` | GitHub application updates (staged, verified, rollback) |
| `locales/add_storyboard_fr.py`, `locales/add_layout_fr.py`, `locales/add_film_fr.py`, `locales/add_workflow_fr.py` | French strings for `ui.json` |
| `tests/` | model, operations and exports, editor logic, updates; `make_sample.py` builds a demo project |

## Install

From the Tool folder, with Python 3.11 and `git` on the PATH:

```
py -3.11 -m venv runtime\python
runtime\python\Scripts\python.exe -m pip install "cytools-core[mcp] @ git+https://github.com/MrMybal/CyToolsCore.git@442f537"
runtime\python\Scripts\python.exe -m pip install -r app\requirements.txt
powershell -File app\build_launcher.ps1
```

## Tests and checks

```
cd app
..\runtime\python\Scripts\python.exe -m unittest discover -s tests         # 42 tests
..\runtime\python\Scripts\python.exe tests\mcp_check.py                    # real MCP session on a 3D stage
..\runtime\python\Scripts\python.exe tests\make_sample.py <folder>
..\runtime\python\Scripts\python.exe gui\main.py --smoke-test --ui-test-project=<project> [--ui-test-language=fr]
    [--ui-test-tab=Layout --ui-test-layout=panel:2,select:Lea,pilot:1]
..\runtime\python\Scripts\cytools.exe validate CyTool.json
```

Executed on 27/09/2026 (Windows 10): the 42 tests; the Layout tab (3D free view, object
selected with its gizmo, view through the shot camera, 2D canvas) in English and French;
`tests/mcp_check.py` (stage, shapes, per-panel placement, render, camera move, film export over MCP);
the film export of the sample project checked by Timeline Director's real planner and a real
ComfyUI v0.37.0 (both workflows loaded in the ComfyUI page and accepted); the window in English and French on the
sample project (`data/reports/ui-storyboard-*.png`); `CyTools_Storyboard.exe` from `C:\`;
a real MCP session (create, add panel, describe). Not executed: Linux, a real GitHub release,
the interactive gestures (drag and drop, duration handles, paste) by a person.

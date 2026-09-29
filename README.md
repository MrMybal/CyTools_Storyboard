# CyTools Storyboard

A standalone storyboard and previs application for generated films (Windows desktop application,
command line and MCP server on one runtime), built on the
[CyToolsCore](https://github.com/MrMybal/CyToolsCore) SDK. French user guide:
[LISEZ-MOI.md](LISEZ-MOI.md). Developer guide: [app/README.md](app/README.md).

It is where a film is edited before it is generated: shots, timing, references, staging and
camera, then exported for **MiniMax H3** — as a film read by the
[ComfyUI-CyTools-H3Film](https://github.com/MrMybal/ComfyUI-CyTools-H3Film) nodes, or as a
workflow for CyTools_MiniMaxH3.

## What it does

- **Board and timeline**: sequences of timed panels with drag and drop, duration handles,
  transitions (cut, crossfade, fades), undo / redo, autosave, status and colours.
- **Structured prompts per panel**: scene, action, shot size, angle, camera move with amplitude
  and speed, lens, dialogue lines per character (language, delivery, off-screen), sound, music.
- **Reference library**: characters, locations, objects, styles, pictures, sounds and videos,
  linked to the panels that use them; a character's audio file is its voice.
- **Staging**: panels framed on shared **3D sets** of simple shapes, meshes and posable
  mannequins (orbit / pan / zoom, gizmos, shot cameras with a start and an end), or drawn in
  **2D**. Characters walk along their moves, change pose during a shot and are posed joint by
  joint or directly in the view with handles on the hands, fingers, wrists, elbows, shoulders,
  head, neck, pelvis, hips, knees, feet and toes (inverse kinematics, joint limits).
- **Exports**: contact sheet (PNG), script (HTML or Markdown), animatic (MP4 with captions; 3D
  panels play their camera and character moves).
- **MiniMax H3 film**: one H3 segment per panel on the 5 + 17n frame grid, overlapping segments
  across cuts, pictures, reference videos and sounds per segment, editable prompt sentences,
  optional depth or OpenPose control videos (with hands and feet) rendered from the 3D staging,
  and a ComfyUI workflow written next to the film.
- **MiniMax H3 workflow**: the storyboard as a CyTools_MiniMaxH3 workflow (one generation per
  panel, trims and transitions, final edit).

## Requirements

- Windows 10/11 x64 (the Linux launcher is provided but has not been run on Linux).
- Python 3.11 and `git` on the PATH to build the private environment.
- An OpenGL 3.3 capable GPU or driver for the 3D view and renders (no AI model runs here).

## Installation

From the Tool folder:

```
py -3.11 -m venv runtime\python
runtime\python\Scripts\python.exe -m pip install "cytools-core[mcp] @ git+https://github.com/MrMybal/CyToolsCore.git@442f537"
runtime\python\Scripts\python.exe -m pip install -r app\requirements.txt
powershell -File app\build_launcher.ps1
```

Then double-click `CyTools_Storyboard.exe`.

## Command line and MCP

```
runtime\python\Scripts\python.exe app\tool.py describe
runtime\python\Scripts\python.exe app\tool.py invoke export_h3_film --params-file params.json
```

Every operation (storyboards, panels, library, stages and objects, poses, renders, exports) is
declared in `app/CyTool.json` and reachable through the CLI and MCP transports of CyToolsCore.

## Layout

| Path | Content |
| --- | --- |
| `CyTools_Storyboard.exe`, `CyTools_Storyboard.sh` | launchers (the exe is built by `app/build_launcher.ps1`) |
| `app/` | code, manifest, interface, locales, tests and scripts |
| `data/` | projects, settings, logs and reports — created locally, never committed |
| `runtime/` | the private Python environment — created locally, never committed |

## Tests

```
cd app
..\runtime\python\Scripts\python.exe -m unittest discover -s tests
..\runtime\python\Scripts\python.exe tests\mcp_check.py
```

## License

GPL-3.0-only — see [LICENSE](LICENSE). Generated media and the MiniMax H3 weights are not part of
this repository; the weights follow their own licence (MiniMax H3 Community License).

Maintained by Cyberalien.

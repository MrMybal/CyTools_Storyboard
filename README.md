<table width="100%">
  <tr>
    <td width="300" align="left" valign="top">
      <a href="https://mrmybal.github.io/CyTools_Storyboard/">Website</a><br>
      <a href="https://mrmybal.github.io/CyTools_Storyboard/Documentation.html#/en/overview">Documentation</a><br>
      <a href="https://github.com/MrMybal/CyTools_Storyboard">GitHub</a><br><br>
      <sub>README</sub><br>
      <a href="README.md">English</a> · <a href="README.fr.md">Français</a>
    </td>
    <td width="400" align="center" valign="middle">
      <a href="https://mrmybal.github.io/CyTools_Storyboard/"><img src="app/assets/branding/logo.png" alt="CyTools Storyboard logo" width="128"></a>
    </td>
    <td width="300" align="right" valign="top">
      <p><sub>Application license</sub><br><a href="LICENSE"><strong>GPL-3.0-only</strong></a></p>
      <p><sub>Application version</sub><br><a href="VERSION.md"><strong>0.2.3</strong></a><br><strong>EXPERIMENTAL</strong></p>
      <p><a href="https://github.com/MrMybal/CyTools_Storyboard/releases/download/v0.2.3/CyTools_Storyboard-0.2.3-windows-x64.zip"><strong>Download</strong></a><br><sub>Windows x64 · portable</sub></p>
    </td>
  </tr>
</table>

<h1 align="center">CyTools Storyboard</h1>


Arrange timed panels, develop the camera and stage a shot in 3D. Carry references and dialogue into images, animatics and compatible film workflows. For directors, storyboard artists and creators preparing a film or a generated sequence.

> **EXPERIMENTAL · 0.2.3**
>
> Published Windows build for evaluation; some engine paths remain unvalidated. Read the [version notes and known limitations](VERSION.md).

[![Storyboard workspace · reference library, timed panels, inspector and timeline.](website/assets/showcase/board.webp)](website/assets/showcase/board.webp)

*Storyboard workspace · reference library, timed panels, inspector and timeline.*


## The application

### Board & timing

Arrange panels into sequences, set their duration and transitions, and keep shot notes alongside the picture. Each panel can carry dialogue, action, camera and sound directions.

### 3D staging

Stage shots with shapes, meshes and posable mannequins. Work with shot cameras, start/end positions and character poses, then reuse the set across panels.

[![Layout workspace · mannequin, shared set and shot cameras.](website/assets/showcase/layout.webp)](website/assets/showcase/layout.webp)

*Layout workspace · mannequin, shared set and shot cameras.*


### Reference images

Import reference pictures or prepare images with a compatible Qwen-Image workflow. A private ComfyUI engine or a configured external ComfyUI performs the generation. Keep the recipe with each accepted image.

[![Images workspace · a shot picture and its generation settings.](website/assets/showcase/images.webp)](website/assets/showcase/images.webp)

*Images workspace · a shot picture and its generation settings.*


## Features

- **Board:** timed panels, sequences, transitions, inspector, undo/redo and autosave.
- **Shot direction:** action, framing, lenses, camera moves, dialogue, delivery, sound/music notes and linked references.
- **Staging:** shared 3D sets, meshes, posable mannequins, shot cameras, poses and movement; 2D drawing is also available.
- **Images:** imports or compatible Qwen-Image/ComfyUI generation, with recipes retained for accepted pictures.
- **Exports:** contact sheets, scripts, animatics, MiniMax H3 film handoffs and CyTools_MiniMaxH3 workflows. H3 inference belongs to the receiving application.

**Desktop and automation:** English is the default interface language; French is selectable in Options. Save/load generation configurations, follow copyable application logs and use the declared operations through the CLI or MCP. The [manual](https://mrmybal.github.io/CyTools_Storyboard/Documentation.html#/en/overview) describes the real parameters and output contracts.

---

## Installation

The published application build is **Windows x64**. The portable ZIP includes its private Python runtime and base UI/media dependencies. Models and optional heavy engines are separate downloads.

1. [Download CyTools Storyboard 0.2.3](https://github.com/MrMybal/CyTools_Storyboard/releases/download/v0.2.3/CyTools_Storyboard-0.2.3-windows-x64.zip).
2. Extract the complete ZIP into a writable folder. Keep `app/` and `runtime/` beside the launcher.
3. Open **CyTools_Storyboard.exe**. Use the installation/model workspace for the components you need; review each component licence and any provider access conditions before download.

No machine Python is needed just to open the portable application. Source setup and some optional engine installers require additional tools such as Git. Keep the full release folder; the standalone `.exe` or an `app` update ZIP alone is not a complete installation.

Experimental Windows x64 application; Linux is unvalidated. The 3D view requires OpenGL 3.3. Local image generation needs its separate compatible GPU engine and model weights. H3 export prepares a handoff; this application does not run MiniMax H3 inference itself. Qwen-Image licences differ, including non-commercial variants.

### Updates and data

For an existing compatible installation, use its Updates page and the matching application update package. Keep `data/`, installed engines and models. An update for another runtime ABI must not be forced. If the required runtime changes, use the complete portable release in a separate folder and follow the migration instructions.

## Source, build and required libraries

<details>
<summary>Windows source setup and optional build tools</summary>


Use Python **3.11** for the base source environment. Git is needed for cloning and pinned Git requirements. Building the launcher needs the MSVC x64 Build Tools; use a developer command prompt.

```powershell
git clone https://github.com/MrMybal/CyTools_Storyboard.git
cd CyTools_Storyboard
py -3.11 -m venv runtime\python
runtime\python\Scripts\python.exe -m pip install "cytools-core[mcp] @ git+https://github.com/MrMybal/CyToolsCore.git@a8d200f2d0baaade1633e0683663b4506c595f74"
runtime\python\Scripts\python.exe -m pip install -r app\requirements.txt
powershell -File app\build_launcher.ps1
.\CyTools_Storyboard.exe
```

The exact base requirements are in [app/requirements.txt](app/requirements.txt). Engines use their own environments and model catalogues; installing the base environment does not install them. Follow the [developer setup](app/README.md) for the detailed build and optional components.

</details>

---

## License

**CyTools Storyboard is licensed under [GPL-3.0-only](LICENSE).** CyToolsCore, CyUI and CyDoc remain MIT components; their licences do not change the application licence. Optional engines, plugins and model weights retain their own terms.

### Main components and third-party libraries

| Library · source | License · terms | Use / scope |
| --- | --- | --- |
| [CyToolsCore 0.10.1](https://github.com/MrMybal/CyToolsCore) | [MIT](LICENCES/CyToolsCore-MIT.txt) | SDK/runtime: jobs, sessions, resources, CLI and MCP. |
| [CyUI 1.2.0](https://github.com/MrMybal/CyUI) | [MIT](LICENCES/CyUI-MIT.txt) | Selected bundled Python UI modules. |
| [CyDoc 0.1.0](https://github.com/MrMybal/CyDoc) | [MIT](LICENCES/CyDoc-MIT.txt) | Bundled offline reader; Node/npm are authoring/build tools only. |
| [Dear ImGui / imgui-bundle](https://github.com/pthom/imgui_bundle) | [MIT + component notices](https://github.com/pthom/imgui_bundle/blob/main/LICENSE) | Desktop renderer and its bundled native components. |
| [CPython 3.11](https://www.python.org/) | [PSF + component notices](https://docs.python.org/3.11/license.html) | Private runtime included in the Windows portable archive. |
| [ModernGL / glcontext / trimesh](app/requirements.txt) | [MIT](LICENCES/SOURCES.txt) | 3D staging, viewport and mesh handling. |
| [NumPy / Pillow](app/requirements.txt) | [BSD-3-Clause / MIT-CMU](LICENCES/SOURCES.txt) | Arrays and image rendering. |
| [imageio / imageio-ffmpeg / FFmpeg](https://github.com/imageio/imageio-ffmpeg) | [BSD-2-Clause; bundled FFmpeg GPL-3.0](LICENCES/SOURCES.txt) | Animation/control video and animatic export; retain the actual FFmpeg build notices. |
| [ComfyUI / PyTorch](app/engines.json) | [GPL-3.0 / BSD-3-Clause](LICENCES/SOURCES.txt) | Optional downloaded image engine. Qwen-Image weights use research or Apache terms depending on the model. |

This table indexes the main components; it does not replace their complete transitive notices. Retain [LICENCES/](LICENCES/), [app/licenses.json](app/licenses.json), the licences beside installed packages and the notices in each optional engine/model. CUDA libraries, when installed, also retain NVIDIA’s terms.

## References and links

- [Documentation](https://mrmybal.github.io/CyTools_Storyboard/Documentation.html#/en/overview)
- [Website](https://mrmybal.github.io/CyTools_Storyboard/)
- [Source repository](https://github.com/MrMybal/CyTools_Storyboard) · [Releases and checksums](https://github.com/MrMybal/CyTools_Storyboard/releases)
- [Issue tracker](https://github.com/MrMybal/CyTools_Storyboard/issues) · [Version notes](VERSION.md)
- [Developer setup](app/README.md)

<details>
<summary><strong>AI Usage</strong></summary>

- [Start here: project agent guide](app/AGENTS.md) — product rules and important files.
- [Operations and AI integration](app/Documentation/DocAI.md) — actual tool contracts and task usage.
- [Build this application](app/README.md) — source setup and application-specific commands.

</details>

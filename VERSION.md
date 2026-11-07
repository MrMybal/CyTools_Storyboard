# CyTools Storyboard — version notes

[Français](VERSION.fr.md) · [README](README.md)

## Published application

**0.2.3 · EXPERIMENTAL · Windows x64**

This is the application version, not the version of its SDK or UI library. This experimental release is intended for evaluation.

- [Published release and checksums](https://github.com/MrMybal/CyTools_Storyboard/releases/tag/v0.2.3)
- [Portable Windows download](https://github.com/MrMybal/CyTools_Storyboard/releases/download/v0.2.3/CyTools_Storyboard-0.2.3-windows-x64.zip)

## Changes in this binary release

- Complete English/French CyDoc manual with navigation, search, contextual help and the relevant media.
- Offline reader and the existing native operation contracts retained.
- Python runtime ABI and model/engine requirements unchanged from the preceding application release.

The product showcase, README layout and repository navigation were added after this binary release. They do not announce a new executable or imply that later source changes shipped in the ZIP.

## Component versions

| Component | Version | Role |
| --- | --- | --- |
| CyTools Storyboard | 0.2.3 | Application |
| CyToolsCore | 0.10.1 | SDK / runtime |
| CyUI | 1.2.0 | Selected UI modules |
| CyDoc | 0.1.0 | Bundled reader |

## Documented limitations

Experimental Windows x64 application; Linux is unvalidated. The 3D view requires OpenGL 3.3. Local image generation needs its separate compatible GPU engine and model weights. H3 export prepares a handoff; this application does not run MiniMax H3 inference itself. Qwen-Image licences differ, including non-commercial variants.

Engines and weights are installed separately. A declared operation or a downloadable model is not evidence that every parameter combination, hardware configuration or model has been validated. Retain the licences delivered with your installed release.

## Bug reports and updates

The current release notes do not publish a bug-by-bug ticket list. Use the issue tracker for confirmed reports; the limitations above describe platform and optional-component availability.

- [Issue tracker](https://github.com/MrMybal/CyTools_Storyboard/issues)
- [All releases](https://github.com/MrMybal/CyTools_Storyboard/releases)

For a compatible existing installation, use its update stream and preserve data/models. A runtime ABI change requires its matching complete distribution; do not force an incompatible app-only update.

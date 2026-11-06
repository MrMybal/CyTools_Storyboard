---
id: operation-export-h3-film
title: export_h3_film
description: Turn the storyboard into a multi-segment MiniMax H3 film: film.json (a Timeline Director timeline: by default the panels of a sequence grouped into windows of about 20 s whose prompt describes the shots in order, overlap…
section: Reference
order: 200
parent: operations
revision: 095849b75a82c9f2
---

Turn the storyboard into a multi-segment MiniMax H3 film: film.json (a Timeline Director timeline: by default the panels of a sequence grouped into windows of about 20 s whose prompt describes the shots in order, overlap frames where the picture continues, identity/location/shot pictures per window), its pictures, and two ComfyUI workflows (CyTools H3 Film disk sampler, Timeline Director). The same file runs in CyTools_MiniMaxH3 on Colab.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `folder` | `string` | No | Target folder (replaced); default exports/h3_film/<title>.  |
| `options` | `object` | No | See the operation parameters.  |
| `workflows` | `boolean` | No | See the operation parameters. `default=true` |
| `save_options` | `boolean` | No | Remember these options in the project. `default=true` |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `segments` | `array` | Yes | See the operation parameters.  |
| `frames` | `integer` | Yes | See the operation parameters.  |
| `seconds` | `number` | No | See the operation parameters.  |
| `width` | `integer` | No | See the operation parameters.  |
| `height` | `integer` | No | See the operation parameters.  |
| `warnings` | `array` | No | See the operation parameters.  |
| `folder` | `string` | No | See the operation parameters.  |
| `file` | `string` | No | See the operation parameters.  |
| `files` | `array` | No | See the operation parameters.  |
| `globalPrompt` | `string` | No | See the operation parameters.  |
| `options` | `object` | No | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_h3_film
```

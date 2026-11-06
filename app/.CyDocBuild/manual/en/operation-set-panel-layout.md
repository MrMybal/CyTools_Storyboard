---
id: operation-set-panel-layout
title: set_panel_layout
description: Choose how a panel is laid out: its images (image), a 2D drawing, or a shot on a 3D stage with a start camera and an optional end camera.
section: Reference
order: 200
parent: operations
revision: 7ecf367104adf1cd
---

Choose how a panel is laid out: its images (image), a 2D drawing, or a shot on a 3D stage with a start camera and an optional end camera.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `panel` | `string` | Yes | See the operation parameters.  |
| `mode` | `string` | No | See the operation parameters. `enum=["image", "2d", "3d"]` |
| `stage` | `string` | No | See the operation parameters.  |
| `camera` | `object` | No | See the operation parameters.  |
| `cameraEnd` | `value` | No | See the operation parameters.  |
| `drawing` | `object` | No | See the operation parameters.  |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | See the operation parameters.  |
| `document` | `object` | No | See the operation parameters.  |
| `timeline` | `array` | No | See the operation parameters.  |
| `totalDuration` | `number` | No | See the operation parameters.  |
| `issues` | `array` | No | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation set_panel_layout
```

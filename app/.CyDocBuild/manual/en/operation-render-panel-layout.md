---
id: operation-render-panel-layout
title: render_panel_layout
description: Render the 2D drawing or the 3D shot (from the start or end camera) into the project; it becomes the panel picture. 3D also writes a depth map.
section: Reference
order: 200
parent: operations
revision: a47fd5b0988d709a
---

Render the 2D drawing or the 3D shot (from the start or end camera) into the project; it becomes the panel picture. 3D also writes a depth map.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `panel` | `string` | Yes | See the operation parameters.  |
| `camera` | `string` | No | See the operation parameters. `default="start"`, `enum=["start", "end"]` |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `render` | `string` | Yes | See the operation parameters.  |
| `depth` | `string` | No | See the operation parameters.  |
| `project` | `string` | No | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation render_panel_layout
```

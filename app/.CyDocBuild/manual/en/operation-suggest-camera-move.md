---
id: operation-suggest-camera-move
title: suggest_camera_move
description: Compare the start and end cameras of a 3D panel and name the move (push in, truck, pan, tilt, crane, zoom, arc...) with its amplitude and speed; apply = write it into the panel prompt.
section: Reference
order: 200
parent: operations
revision: 64198ee4e8e55c3b
---

Compare the start and end cameras of a 3D panel and name the move (push in, truck, pan, tilt, crane, zoom, arc...) with its amplitude and speed; apply = write it into the panel prompt.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `panel` | `string` | Yes | See the operation parameters.  |
| `apply` | `boolean` | No | See the operation parameters. `default=false` |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `cameraMove` | `string` | Yes | See the operation parameters.  |
| `cameraAmplitude` | `string` | No | See the operation parameters.  |
| `cameraSpeed` | `string` | No | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation suggest_camera_move
```

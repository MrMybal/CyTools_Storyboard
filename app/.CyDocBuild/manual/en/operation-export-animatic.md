---
id: operation-export-animatic
title: export_animatic
description: Every panel for its duration with its transition, as an MP4 (captions optional); a panel staged in 3D plays its camera, character and pose moves.
section: Reference
order: 200
parent: operations
revision: 3d59555a73909dd9
---

Every panel for its duration with its transition, as an MP4 (captions optional); a panel staged in 3D plays its camera, character and pose moves.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `captions` | `boolean` | No | See the operation parameters. `default=true` |
| `fps` | `integer` | No | See the operation parameters. `default=24`, `minimum=1`, `maximum=60` |
| `motion` | `boolean` | No | Render the moves of 3D panels (off: one picture per panel). `default=true` |
| `motion_fps` | `integer` | No | Rendered pictures per second for 3D moves. `default=12`, `minimum=4`, `maximum=24` |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `file` | `string` | Yes | See the operation parameters.  |
| `duration` | `number` | No | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_animatic
```

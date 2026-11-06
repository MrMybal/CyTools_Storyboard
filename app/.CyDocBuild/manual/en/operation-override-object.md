---
id: operation-override-object
title: override_object
description: Move, turn, resize or hide a shape in this panel only (a character walking between shots); clear = back to the stage placement.
section: Reference
order: 200
parent: operations
revision: b63de36c6fb7b14d
---

Move, turn, resize or hide a shape in this panel only (a character walking between shots); clear = back to the stage placement.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `panel` | `string` | Yes | See the operation parameters.  |
| `object` | `string` | Yes | See the operation parameters.  |
| `position` | `array` | No | See the operation parameters.  |
| `rotation` | `array` | No | See the operation parameters.  |
| `scale` | `array` | No | See the operation parameters.  |
| `hidden` | `boolean` | No | See the operation parameters.  |
| `positionEnd` | `value` | No | Where it is at the end of the panel (it moves there); null = still.  |
| `rotationEnd` | `value` | No | See the operation parameters.  |
| `pose` | `string` | No | Character pose in this panel: standing, walking, running, sitting, crouching, arms raised, pointing or a project pose id (add_pose).  |
| `poseEnd` | `string` | No | Pose at the end of the panel (same values).  |
| `clear` | `boolean` | No | See the operation parameters. `default=false` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation override_object
```

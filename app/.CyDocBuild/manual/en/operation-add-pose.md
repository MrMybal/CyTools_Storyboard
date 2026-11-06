---
id: operation-add-pose
title: add_pose
description: A project pose made joint by joint, starting from a preset (standing, walking, running, sitting, crouching, arms raised, pointing) or another project pose; usable as the pose or end pose of any character.
section: Reference
order: 200
parent: operations
revision: 66c045db17c1e6e6
---

A project pose made joint by joint, starting from a preset (standing, walking, running, sitting, crouching, arms raised, pointing) or another project pose; usable as the pose or end pose of any character.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `name` | `string` | No | See the operation parameters.  |
| `base` | `string` | No | See the operation parameters. `default="standing"` |
| `angles` | `object` | No | Degrees; values not given are kept.  |
| `walks` | `boolean` | No | The legs walk when a character in this pose moves. `default=true` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_pose
```

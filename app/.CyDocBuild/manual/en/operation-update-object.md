---
id: operation-update-object
title: update_object
description: Change a shape on its stage (every panel using the stage sees it).
section: Reference
order: 200
parent: operations
revision: e03c3849cf6fe09f
---

Change a shape on its stage (every panel using the stage sees it).

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `object` | `string` | Yes | See the operation parameters.  |
| `name` | `string` | No | See the operation parameters.  |
| `color` | `string` | No | See the operation parameters.  |
| `position` | `array` | No | See the operation parameters.  |
| `rotation` | `array` | No | Degrees around X, Y, Z.  |
| `scale` | `array` | No | Size in metres for box/sphere/cylinder/cone, a factor for the others.  |
| `role` | `string` | No | See the operation parameters. `enum=["set", "character", "object", "location"]` |
| `reference` | `string` | No | Library item this shape stands for.  |
| `pose` | `string` | No | Character pose on the stage: a preset or a project pose id.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_object
```

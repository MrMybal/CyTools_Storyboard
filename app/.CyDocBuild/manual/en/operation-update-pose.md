---
id: operation-update-pose
title: update_pose
description: Rename a project pose or change some of its joints.
section: Reference
order: 200
parent: operations
revision: eafb549755863930
---

Rename a project pose or change some of its joints.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `pose` | `string` | Yes | See the operation parameters.  |
| `name` | `string` | No | See the operation parameters.  |
| `angles` | `object` | No | Degrees; values not given are kept.  |
| `walks` | `boolean` | No | See the operation parameters.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_pose
```

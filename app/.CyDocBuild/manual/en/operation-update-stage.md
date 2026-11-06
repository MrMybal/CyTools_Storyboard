---
id: operation-update-stage
title: update_stage
description: Name, sky colour, ground on/off and colour.
section: Reference
order: 200
parent: operations
revision: bc5fef3f790c52d2
---

Name, sky colour, ground on/off and colour.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `stage` | `string` | Yes | See the operation parameters.  |
| `name` | `string` | No | See the operation parameters.  |
| `sky` | `string` | No | See the operation parameters.  |
| `ground` | `boolean` | No | See the operation parameters.  |
| `groundColour` | `string` | No | See the operation parameters.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_stage
```

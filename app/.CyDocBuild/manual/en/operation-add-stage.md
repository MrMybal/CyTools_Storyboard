---
id: operation-add-stage
title: add_stage
description: A 3D set of simple shapes that panels can be framed in; several panels sharing one stage keep the same places from one shot to the next.
section: Reference
order: 200
parent: operations
revision: b54008654c162c96
---

A 3D set of simple shapes that panels can be framed in; several panels sharing one stage keep the same places from one shot to the next.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `name` | `string` | No | See the operation parameters.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_stage
```

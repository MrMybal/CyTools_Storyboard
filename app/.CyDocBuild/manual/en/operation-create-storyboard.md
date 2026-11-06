---
id: operation-create-storyboard
title: create_storyboard
description: Create a project folder (.cystory) with one empty sequence.
section: Reference
order: 200
parent: operations
revision: 781946bfc9d75578
---

Create a project folder (.cystory) with one empty sequence.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `title` | `string` | Yes | See the operation parameters.  |
| `folder` | `string` | No | Parent folder; default data/projects.  |
| `aspect` | `string` | No | See the operation parameters. `default="16:9"`, `enum=["16:9", "21:9", "4:3", "1:1", "3:4", "9:16", "2.39:1"]` |
| `fps` | `integer` | No | See the operation parameters. `default=24`, `minimum=1`, `maximum=120` |
| `default_duration` | `number` | No | See the operation parameters. `default=5`, `minimum=0.1`, `maximum=600` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation create_storyboard
```

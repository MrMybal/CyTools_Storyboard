---
id: operation-move-panel
title: move_panel
description: Move a panel to a position, in its sequence or another one.
section: Reference
order: 200
parent: operations
revision: a6eca6835a9f0bd4
---

Move a panel to a position, in its sequence or another one.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `panel` | `string` | Yes | See the operation parameters.  |
| `sequence` | `string` | No | See the operation parameters.  |
| `index` | `integer` | No | See the operation parameters. `minimum=0` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation move_panel
```

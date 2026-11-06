---
id: operation-update-panel
title: update_panel
description: Change any field of a panel; prompt fields are merged.
section: Reference
order: 200
parent: operations
revision: b1c5253acf04c852
---

Change any field of a panel; prompt fields are merged.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `panel` | `string` | Yes | See the operation parameters.  |
| `title` | `string` | No | See the operation parameters.  |
| `duration` | `number` | No | Seconds on screen. `minimum=0.1`, `maximum=600` |
| `status` | `string` | No | See the operation parameters. `enum=["idea", "draft", "ready", "generated"]` |
| `color` | `string` | No | See the operation parameters.  |
| `images` | `array` | No | See the operation parameters.  |
| `prompt` | `object` | No | See the operation parameters.  |
| `references` | `array` | No | Library item ids.  |
| `transition` | `object` | No | See the operation parameters.  |
| `notes` | `string` | No | See the operation parameters.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_panel
```

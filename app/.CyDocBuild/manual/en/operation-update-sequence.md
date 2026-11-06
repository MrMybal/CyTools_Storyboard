---
id: operation-update-sequence
title: update_sequence
description: Title, colour, notes.
section: Reference
order: 200
parent: operations
revision: 38bbf7cca01e1d28
---

Title, colour, notes.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `sequence` | `string` | Yes | See the operation parameters.  |
| `title` | `string` | No | See the operation parameters.  |
| `color` | `string` | No | See the operation parameters.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_sequence
```

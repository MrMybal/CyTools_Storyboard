---
id: operation-preview-h3-film
title: preview_h3_film
description: Segments, frame windows, pictures and prompts the export would produce, without writing anything.
section: Reference
order: 200
parent: operations
revision: a1e0701f6934db9b
---

Segments, frame windows, pictures and prompts the export would produce, without writing anything.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `options` | `object` | No | See the operation parameters.  |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `segments` | `array` | Yes | See the operation parameters.  |
| `frames` | `integer` | Yes | See the operation parameters.  |
| `seconds` | `number` | No | See the operation parameters.  |
| `width` | `integer` | No | See the operation parameters.  |
| `height` | `integer` | No | See the operation parameters.  |
| `warnings` | `array` | No | See the operation parameters.  |
| `folder` | `string` | No | See the operation parameters.  |
| `file` | `string` | No | See the operation parameters.  |
| `files` | `array` | No | See the operation parameters.  |
| `globalPrompt` | `string` | No | See the operation parameters.  |
| `options` | `object` | No | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation preview_h3_film
```

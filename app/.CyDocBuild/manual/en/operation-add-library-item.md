---
id: operation-add-library-item
title: add_library_item
description: A character, location, object, style, image, audio or video reference usable by any panel.
section: Reference
order: 200
parent: operations
revision: 571df7b3158682a2
---

A character, location, object, style, image, audio or video reference usable by any panel.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `kind` | `string` | Yes | See the operation parameters. `enum=["character", "location", "object", "style", "image", "audio", "video"]` |
| `name` | `string` | Yes | See the operation parameters.  |
| `description` | `string` | No | See the operation parameters.  |
| `files` | `array` | No | See the operation parameters.  |
| `tags` | `array` | No | See the operation parameters.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_library_item
```

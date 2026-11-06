---
id: operation-generate-images
title: generate_images
description: Generate reference pictures in the application: views of a character or a place from its reference pictures (or from its description), a character placed in a place, the picture of a shot from its staging render, or a free…
section: Reference
order: 200
parent: operations
revision: 57d264877c36cba1
---

Generate reference pictures in the application: views of a character or a place from its reference pictures (or from its description), a character placed in a place, the picture of a shot from its staging render, or a free prompt. The model stays loaded between calls. Returns the pictures with their recipe; keep=true copies them into the project and attaches them (library item files, first image of the panel).

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | No | Project (needed by every recipe except free).  |
| `recipe` | `string` | No | character: views of a library character; location: views of a place, empty or with a character; panel: the picture of a shot; free: any prompt. `default="free"`, `enum=["character", "location", "panel", "free"]` |
| `item` | `string` | No | Library item id (character or location recipe).  |
| `panel` | `string` | No | Panel id (panel recipe).  |
| `views` | `array` | No | View keys to render; default: the views switched on in the options.  |
| `character` | `string` | No | Character id placed in the location (location recipe).  |
| `prompt` | `string` | No | Text of the free recipe.  |
| `references` | `array` | No | Free recipe: picture files or library item ids used as references (none = from the text).  |
| `format` | `string` | No | See the operation parameters. `enum=["project", "1:1", "3:4", "4:3", "2:3", "3:2", "9:16", "16:9", "21:9", "2.39:1"]` |
| `extra` | `string` | No | Added to every prompt of the recipe.  |
| `extras` | `string` | No | Panel recipe: character id that every mannequin of the staging without a reference stands for (a crowd of the same character).  |
| `label` | `string` | No | See the operation parameters.  |
| `options` | `object` | No | See the operation parameters.  |
| `keep` | `boolean` | No | Copy every picture into the project. `default=false` |
| `attach` | `boolean` | No | With keep: attach to the item or the panel. `default=true` |
| `save_options` | `boolean` | No | Remember the options in the project. `default=false` |
## Returns {#returns}

No named fields are declared at this level. Inspect the operation schema with `describe-operation` for its exact shape.

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: `comfyui`
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation generate_images
```

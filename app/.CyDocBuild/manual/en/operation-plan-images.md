---
id: operation-plan-images
title: plan_images
description: The requests a recipe would send to the image model (prompts, reference pictures, sizes, seeds), without generating anything.
section: Reference
order: 200
parent: operations
revision: 7352d4cdbf38556e
---

The requests a recipe would send to the image model (prompts, reference pictures, sizes, seeds), without generating anything.

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
## Returns {#returns}

No named fields are declared at this level. Inspect the operation schema with `describe-operation` for its exact shape.

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation plan_images
```

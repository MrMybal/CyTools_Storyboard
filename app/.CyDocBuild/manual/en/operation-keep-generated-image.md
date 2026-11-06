---
id: operation-keep-generated-image
title: keep_generated_image
description: Copy one picture returned by generateimages into the project with its recipe, and attach it to its target.
section: Reference
order: 200
parent: operations
revision: eda24e186425c4b0
---

Copy one picture returned by generate_images into the project with its recipe, and attach it to its target.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `file` | `string` | Yes | See the operation parameters.  |
| `attach` | `boolean` | No | See the operation parameters. `default=true` |
## Returns {#returns}

No named fields are declared at this level. Inspect the operation schema with `describe-operation` for its exact shape.

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation keep_generated_image
```

---
id: operation-remove-image-model
title: remove_image_model
description: Delete the files of a model that no other installed model uses.
section: Reference
order: 200
parent: operations
revision: 178c4dd92d51e712
---

Delete the files of a model that no other installed model uses.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `model` | `string` | Yes | See the operation parameters. `enum=["qwen-image-2.1-controlnet-int8", "qwen-image-2.1-int8", "qwen-image-2512-fp8", "qwen-image-edit-2511-int8"]` |
## Returns {#returns}

No named fields are declared at this level. Inspect the operation schema with `describe-operation` for its exact shape.

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation remove_image_model
```

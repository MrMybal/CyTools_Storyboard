---
id: operation-install-image-model
title: install_image_model
description: Download the files of a model (resumable, size and SHA-256 checked); files shared with another model are not downloaded twice.
section: Reference
order: 200
parent: operations
revision: cd385070de85a937
---

Download the files of a model (resumable, size and SHA-256 checked); files shared with another model are not downloaded twice.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `model` | `string` | Yes | See the operation parameters. `enum=["qwen-image-2.1-controlnet-int8", "qwen-image-2.1-int8", "qwen-image-2512-fp8", "qwen-image-edit-2511-int8"]` |
| `accept_license` | `boolean` | No | See the operation parameters. `default=true` |
| `repair` | `boolean` | No | See the operation parameters. `default=false` |
## Returns {#returns}

No named fields are declared at this level. Inspect the operation schema with `describe-operation` for its exact shape.

## Behaviour and access {#behaviour}

- Required permissions: `network`
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation install_image_model
```

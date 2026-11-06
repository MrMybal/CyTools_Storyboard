---
id: operation-install-image-engine
title: install_image_engine
description: Create or repair the private engine: a Python environment with PyTorch (CUDA 13) and a pinned ComfyUI checkout, checked by import.
section: Reference
order: 200
parent: operations
revision: 338a89f23d608bb4
---

Create or repair the private engine: a Python environment with PyTorch (CUDA 13) and a pinned ComfyUI checkout, checked by import.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `cpu_only` | `boolean` | No | See the operation parameters. `default=false` |
## Returns {#returns}

No named fields are declared at this level. Inspect the operation schema with `describe-operation` for its exact shape.

## Behaviour and access {#behaviour}

- Required permissions: `network`
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation install_image_engine
```

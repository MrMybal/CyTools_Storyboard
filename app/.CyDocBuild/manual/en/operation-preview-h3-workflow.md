---
id: operation-preview-h3-workflow
title: preview_h3_workflow
description: The shots, generations, trims, references and prompts the conversion would produce, and the workflow itself, without writing.
section: Reference
order: 200
parent: operations
revision: a8a8f1185d9ccf9f
---

The shots, generations, trims, references and prompts the conversion would produce, and the workflow itself, without writing.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `options` | `object` | No | See the operation parameters.  |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `shots` | `array` | Yes | See the operation parameters.  |
| `width` | `integer` | No | See the operation parameters.  |
| `height` | `integer` | No | See the operation parameters.  |
| `seconds` | `number` | No | See the operation parameters.  |
| `generations` | `integer` | No | See the operation parameters.  |
| `steps` | `integer` | No | See the operation parameters.  |
| `warnings` | `array` | No | See the operation parameters.  |
| `folder` | `string` | No | See the operation parameters.  |
| `file` | `string` | No | See the operation parameters.  |
| `workflow` | `object` | No | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation preview_h3_workflow
```

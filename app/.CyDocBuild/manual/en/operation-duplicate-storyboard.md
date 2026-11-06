---
id: operation-duplicate-storyboard
title: duplicate_storyboard
description: Copy a project under another title (document and assets, its own folder and id); the original is left as it is.
section: Reference
order: 200
parent: operations
revision: 2a0e4e1a68779126
---

Copy a project under another title (document and assets, its own folder and id); the original is left as it is.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `title` | `string` | Yes | See the operation parameters.  |
| `folder` | `string` | No | Parent folder of the copy; default: next to the original.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation duplicate_storyboard
```

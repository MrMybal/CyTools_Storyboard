---
id: operation-list-storyboards
title: list_storyboards
description: Projects in data/projects (or in a given folder).
section: Reference
order: 200
parent: operations
revision: 96f51148e752130b
---

Projects in data/projects (or in a given folder).

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `folder` | `string` | No | See the operation parameters.  |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `projects` | `array` | Yes | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation list_storyboards
```

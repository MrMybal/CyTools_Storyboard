---
id: operation-export-contact-sheet
title: export_contact_sheet
description: All panels on one PNG with numbers, durations and text.
section: Reference
order: 200
parent: operations
revision: 38fc2e0362851197
---

All panels on one PNG with numbers, durations and text.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `columns` | `integer` | No | See the operation parameters. `default=4`, `minimum=1`, `maximum=10` |
| `cell_width` | `integer` | No | See the operation parameters. `default=480`, `minimum=160`, `maximum=1200` |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `file` | `string` | Yes | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_contact_sheet
```

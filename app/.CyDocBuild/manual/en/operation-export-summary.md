---
id: operation-export-summary
title: export_summary
description: The storyboard as Markdown or as one self-contained HTML page.
section: Reference
order: 200
parent: operations
revision: 8676b18ea6b9b084
---

The storyboard as Markdown or as one self-contained HTML page.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `format` | `string` | No | See the operation parameters. `default="html"`, `enum=["md", "html"]` |
## Returns {#returns}

| Name | Type | Required | Description |
|---|---|---|---|
| `file` | `string` | Yes | See the operation parameters.  |

## Behaviour and access {#behaviour}

- Required permissions: none declared.
- Backends: none declared.
- Cancellation: supported.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_summary
```

---
id: operation-export-h3-workflow
title: export_h3_workflow
description: Convert the storyboard into a CyToolsMiniMaxH3 workflow (workflow.json + media/): one H3 generation per panel with its first/last frame, keyframe guides and references (characters, layout, locations, videos, voices, sounds),…
section: Reference
order: 200
parent: operations
revision: d6c1084dd5770295
---

Convert the storyboard into a CyTools_MiniMaxH3 workflow (workflow.json + media/): one H3 generation per panel with its first/last frame, keyframe guides and references (characters, layout, locations, videos, voices, sounds), chaining, prompts in the H3 layout, durations trimmed to the panels, and a final edit with the storyboard transitions. Run it with run_workflow in CyTools_MiniMaxH3.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `folder` | `string` | No | Target folder (replaced); default exports/h3_workflow/<title>.  |
| `options` | `object` | No | See the operation parameters.  |
| `save_options` | `boolean` | No | See the operation parameters. `default=true` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation export_h3_workflow
```

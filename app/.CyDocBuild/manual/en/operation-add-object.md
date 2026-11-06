---
id: operation-add-object
title: add_object
description: Box, sphere, cylinder, cone, capsule, plane, mannequin, or an imported mesh (.glb .gltf .obj .ply .stl .off). New shapes stand on the ground.
section: Reference
order: 200
parent: operations
revision: d66630c60c91fd16
---

Box, sphere, cylinder, cone, capsule, plane, mannequin, or an imported mesh (.glb .gltf .obj .ply .stl .off). New shapes stand on the ground.

## Parameters {#contract}

| Name | Type | Required | Description |
|---|---|---|---|
| `project` | `string` | Yes | Project folder (.cystory) or its storyboard.json; a bare name is looked up in data/projects.  |
| `stage` | `string` | Yes | See the operation parameters.  |
| `shape` | `string` | No | See the operation parameters. `default="box"`, `enum=["box", "sphere", "cylinder", "cone", "capsule", "plane", "mannequin", "mesh"]` |
| `mesh` | `string` | No | Mesh file, for shape = mesh.  |
| `name` | `string` | No | See the operation parameters.  |
| `color` | `string` | No | See the operation parameters.  |
| `position` | `array` | No | See the operation parameters.  |
| `rotation` | `array` | No | Degrees around X, Y, Z.  |
| `scale` | `array` | No | Size in metres for box/sphere/cylinder/cone, a factor for the others.  |
| `role` | `string` | No | See the operation parameters. `enum=["set", "character", "object", "location"]` |
| `reference` | `string` | No | Library item this shape stands for.  |
| `pose` | `string` | No | Character pose on the stage: a preset or a project pose id.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_object
```

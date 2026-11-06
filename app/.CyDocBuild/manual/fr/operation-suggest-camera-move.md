---
id: operation-suggest-camera-move
title: suggest_camera_move
description: Comparer les caméras de départ et de fin d'un panneau 3D et nommer le mouvement (approche, camion, pan, tilt, grue, zoom, arc...) avec son amplitude et sa vitesse ; appliquer = l'écrire dans le prompt du panneau.
section: Référence
order: 200
parent: operations
sourceRevision: 64198ee4e8e55c3b
---

Comparer les caméras de départ et de fin d'un panneau 3D et nommer le mouvement (approche, camion, pan, tilt, grue, zoom, arc...) avec son amplitude et sa vitesse ; appliquer = l'écrire dans le prompt du panneau.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `panel` | `string` | Oui | Voir les paramètres de l’opération.  |
| `apply` | `boolean` | Non | Voir les paramètres de l’opération. `default=false` |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `cameraMove` | `string` | Oui | Voir les paramètres de l’opération.  |
| `cameraAmplitude` | `string` | Non | Voir les paramètres de l’opération.  |
| `cameraSpeed` | `string` | Non | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation suggest_camera_move
```

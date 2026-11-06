---
id: operation-set-panel-layout
title: set_panel_layout
description: Choisissez comment un panneau est disposé : ses images (image), un dessin 2D, ou une prise sur une scène 3D avec une caméra de départ et une caméra optionnelle de fin.
section: Référence
order: 200
parent: operations
sourceRevision: 7ecf367104adf1cd
---

Choisissez comment un panneau est disposé : ses images (image), un dessin 2D, ou une prise sur une scène 3D avec une caméra de départ et une caméra optionnelle de fin.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `panel` | `string` | Oui | Voir les paramètres de l’opération.  |
| `mode` | `string` | Non | Voir les paramètres de l’opération. `enum=["image", "2d", "3d"]` |
| `stage` | `string` | Non | Voir les paramètres de l’opération.  |
| `camera` | `object` | Non | Voir les paramètres de l’opération.  |
| `cameraEnd` | `value` | Non | Voir les paramètres de l’opération.  |
| `drawing` | `object` | Non | Voir les paramètres de l’opération.  |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Voir les paramètres de l’opération.  |
| `document` | `object` | Non | Voir les paramètres de l’opération.  |
| `timeline` | `array` | Non | Voir les paramètres de l’opération.  |
| `totalDuration` | `number` | Non | Voir les paramètres de l’opération.  |
| `issues` | `array` | Non | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation set_panel_layout
```

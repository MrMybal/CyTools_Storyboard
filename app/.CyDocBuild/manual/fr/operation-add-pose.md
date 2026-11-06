---
id: operation-add-pose
title: add_pose
description: Une pose du projet joint par joint, en partant d'une prédéfinie (debout, marchant, courant, assis, genoux baissés, bras levés, pointant) ou d'une autre pose du projet ; utilisable comme pose ou pose finale de tout personnage.
section: Référence
order: 200
parent: operations
sourceRevision: 66c045db17c1e6e6
---

Une pose du projet joint par joint, en partant d'une prédéfinie (debout, marchant, courant, assis, genoux baissés, bras levés, pointant) ou d'une autre pose du projet ; utilisable comme pose ou pose finale de tout personnage.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `name` | `string` | Non | Voir les paramètres de l’opération.  |
| `base` | `string` | Non | Voir les paramètres de l’opération. `default="standing"` |
| `angles` | `object` | Non | Grades; des valeurs non fournies sont conservées.  |
| `walks` | `boolean` | Non | Les jambes marchent lorsque un personnage dans cette pose se déplace. `default=true` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_pose
```

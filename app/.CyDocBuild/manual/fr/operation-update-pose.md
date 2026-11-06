---
id: operation-update-pose
title: update_pose
description: Renommez une pose de projet ou modifiez certaines de ses articulations.
section: Référence
order: 200
parent: operations
sourceRevision: eafb549755863930
---

Renommez une pose de projet ou modifiez certaines de ses articulations.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `pose` | `string` | Oui | Voir les paramètres de l’opération.  |
| `name` | `string` | Non | Voir les paramètres de l’opération.  |
| `angles` | `object` | Non | Grades; des valeurs non fournies sont conservées.  |
| `walks` | `boolean` | Non | Voir les paramètres de l’opération.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_pose
```

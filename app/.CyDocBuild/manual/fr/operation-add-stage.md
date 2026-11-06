---
id: operation-add-stage
title: add_stage
description: Un ensemble 3D de formes simples dans lesquelles les panneaux peuvent être encadrés ; plusieurs panneaux partageant une même scène conservent les mêmes positions d'un cliché à l'autre.
section: Référence
order: 200
parent: operations
sourceRevision: b54008654c162c96
---

Un ensemble 3D de formes simples dans lesquelles les panneaux peuvent être encadrés ; plusieurs panneaux partageant une même scène conservent les mêmes positions d'un cliché à l'autre.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `name` | `string` | Non | Voir les paramètres de l’opération.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_stage
```

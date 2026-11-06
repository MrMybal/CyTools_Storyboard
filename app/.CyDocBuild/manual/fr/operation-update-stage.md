---
id: operation-update-stage
title: update_stage
description: Nom, couleur du ciel, sol activé/désactivé et couleur.
section: Référence
order: 200
parent: operations
sourceRevision: bc5fef3f790c52d2
---

Nom, couleur du ciel, sol activé/désactivé et couleur.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `stage` | `string` | Oui | Voir les paramètres de l’opération.  |
| `name` | `string` | Non | Voir les paramètres de l’opération.  |
| `sky` | `string` | Non | Voir les paramètres de l’opération.  |
| `ground` | `boolean` | Non | Voir les paramètres de l’opération.  |
| `groundColour` | `string` | Non | Voir les paramètres de l’opération.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_stage
```

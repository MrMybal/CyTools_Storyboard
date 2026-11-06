---
id: operation-update-sequence
title: update_sequence
description: Titre, couleur, notes.
section: Référence
order: 200
parent: operations
sourceRevision: 38bbf7cca01e1d28
---

Titre, couleur, notes.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `sequence` | `string` | Oui | Voir les paramètres de l’opération.  |
| `title` | `string` | Non | Voir les paramètres de l’opération.  |
| `color` | `string` | Non | Voir les paramètres de l’opération.  |
| `notes` | `string` | Non | Voir les paramètres de l’opération.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_sequence
```

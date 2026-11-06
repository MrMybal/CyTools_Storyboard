---
id: operation-duplicate-storyboard
title: duplicate_storyboard
description: Copiez un projet sous un autre titre (document et assets, son propre dossier et id) ; le projet original est laissé tel quel.
section: Référence
order: 200
parent: operations
sourceRevision: 2a0e4e1a68779126
---

Copiez un projet sous un autre titre (document et assets, son propre dossier et id) ; le projet original est laissé tel quel.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `title` | `string` | Oui | Voir les paramètres de l’opération.  |
| `folder` | `string` | Non | Dossier parent de la copie ; par défaut : à côté du original.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation duplicate_storyboard
```

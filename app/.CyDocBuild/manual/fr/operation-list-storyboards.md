---
id: operation-list-storyboards
title: list_storyboards
description: Projets dans data/projects (ou dans un dossier donné).
section: Référence
order: 200
parent: operations
sourceRevision: 96f51148e752130b
---

Projets dans data/projects (ou dans un dossier donné).

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `folder` | `string` | Non | Voir les paramètres de l’opération.  |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `projects` | `array` | Oui | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation list_storyboards
```

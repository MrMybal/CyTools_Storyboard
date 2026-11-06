---
id: operation-create-storyboard
title: create_storyboard
description: Créez un dossier de projet (.cystory) contenant une seule séquence vide.
section: Référence
order: 200
parent: operations
sourceRevision: 781946bfc9d75578
---

Créez un dossier de projet (.cystory) contenant une seule séquence vide.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `title` | `string` | Oui | Voir les paramètres de l’opération.  |
| `folder` | `string` | Non | Dossier parent ; par défaut : data/projects.  |
| `aspect` | `string` | Non | Voir les paramètres de l’opération. `default="16:9"`, `enum=["16:9", "21:9", "4:3", "1:1", "3:4", "9:16", "2.39:1"]` |
| `fps` | `integer` | Non | Voir les paramètres de l’opération. `default=24`, `minimum=1`, `maximum=120` |
| `default_duration` | `number` | Non | Voir les paramètres de l’opération. `default=5`, `minimum=0.1`, `maximum=600` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation create_storyboard
```

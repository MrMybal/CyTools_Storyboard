---
id: operation-preview-h3-workflow
title: preview_h3_workflow
description: Les prises de vue, générations, trims, références et prompts qui seraient produits par la conversion, ainsi que le flux de travail lui-même, sans écrire.
section: Référence
order: 200
parent: operations
sourceRevision: a8a8f1185d9ccf9f
---

Les prises de vue, générations, trims, références et prompts qui seraient produits par la conversion, ainsi que le flux de travail lui-même, sans écrire.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `options` | `object` | Non | Voir les paramètres de l’opération.  |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `shots` | `array` | Oui | Voir les paramètres de l’opération.  |
| `width` | `integer` | Non | Voir les paramètres de l’opération.  |
| `height` | `integer` | Non | Voir les paramètres de l’opération.  |
| `seconds` | `number` | Non | Voir les paramètres de l’opération.  |
| `generations` | `integer` | Non | Voir les paramètres de l’opération.  |
| `steps` | `integer` | Non | Voir les paramètres de l’opération.  |
| `warnings` | `array` | Non | Voir les paramètres de l’opération.  |
| `folder` | `string` | Non | Voir les paramètres de l’opération.  |
| `file` | `string` | Non | Voir les paramètres de l’opération.  |
| `workflow` | `object` | Non | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation preview_h3_workflow
```

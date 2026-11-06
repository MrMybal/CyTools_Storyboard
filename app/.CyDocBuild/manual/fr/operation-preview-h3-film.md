---
id: operation-preview-h3-film
title: preview_h3_film
description: Les segments, fenêtres d’images, images et prompts qui seraient produits par l’exportation, sans écrire quoi que ce soit.
section: Référence
order: 200
parent: operations
sourceRevision: a1e0701f6934db9b
---

Les segments, fenêtres d’images, images et prompts qui seraient produits par l’exportation, sans écrire quoi que ce soit.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `options` | `object` | Non | Voir les paramètres de l’opération.  |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `segments` | `array` | Oui | Voir les paramètres de l’opération.  |
| `frames` | `integer` | Oui | Voir les paramètres de l’opération.  |
| `seconds` | `number` | Non | Voir les paramètres de l’opération.  |
| `width` | `integer` | Non | Voir les paramètres de l’opération.  |
| `height` | `integer` | Non | Voir les paramètres de l’opération.  |
| `warnings` | `array` | Non | Voir les paramètres de l’opération.  |
| `folder` | `string` | Non | Voir les paramètres de l’opération.  |
| `file` | `string` | Non | Voir les paramètres de l’opération.  |
| `files` | `array` | Non | Voir les paramètres de l’opération.  |
| `globalPrompt` | `string` | Non | Voir les paramètres de l’opération.  |
| `options` | `object` | Non | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation preview_h3_film
```

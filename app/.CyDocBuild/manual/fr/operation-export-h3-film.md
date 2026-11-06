---
id: operation-export-h3-film
title: export_h3_film
description: Transformer le story-board en film multi-segment MiniMax H3 : film.json (une timeline du directeur : par défaut, les panneaux d'une séquence regroupés dans des fenêtres d'environ 20 s dont le prompt décrit les prises dans…
section: Référence
order: 200
parent: operations
sourceRevision: 095849b75a82c9f2
---

Transformer le story-board en film multi-segment MiniMax H3 : film.json (une timeline du directeur : par défaut, les panneaux d'une séquence regroupés dans des fenêtres d'environ 20 s dont le prompt décrit les prises dans l'ordre, superposition des images où la prise continue, images par fenêtre pour l'identité/la localisation/la prise). Ses images et deux workflows ComfyUI (CyTools H3 Film échantillon de disque, Timeline Director). Le même fichier s'exécute dans CyTools_MiniMaxH3 sur Colab.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `folder` | `string` | Non | Dossier cible (remplacé) ; par défaut, exports/h3_film/<title>.  |
| `options` | `object` | Non | Voir les paramètres de l’opération.  |
| `workflows` | `boolean` | Non | Voir les paramètres de l’opération. `default=true` |
| `save_options` | `boolean` | Non | Rester ces options dans le projet. `default=true` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation export_h3_film
```

---
id: operation-add-panel
title: add_panel
description: Ajoutez un panneau à la fin d'une séquence, ou après un panneau donné.
section: Référence
order: 200
parent: operations
sourceRevision: ddc8fa50d79ff588
---

Ajoutez un panneau à la fin d'une séquence, ou après un panneau donné.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `sequence` | `string` | Non | Voir les paramètres de l’opération.  |
| `after` | `string` | Non | Voir les paramètres de l’opération.  |
| `title` | `string` | Non | Voir les paramètres de l’opération.  |
| `duration` | `number` | Non | Secondes sur l'écran. `minimum=0.1`, `maximum=600` |
| `status` | `string` | Non | Voir les paramètres de l’opération. `enum=["idea", "draft", "ready", "generated"]` |
| `color` | `string` | Non | Voir les paramètres de l’opération.  |
| `images` | `array` | Non | Voir les paramètres de l’opération.  |
| `prompt` | `object` | Non | Voir les paramètres de l’opération.  |
| `references` | `array` | Non | Identifiants d'éléments de la bibliothèque.  |
| `transition` | `object` | Non | Voir les paramètres de l’opération.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_panel
```

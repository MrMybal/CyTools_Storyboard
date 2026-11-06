---
id: operation-move-panel
title: move_panel
description: Déplacez un panneau à une position, dans sa séquence ou une autre.
section: Référence
order: 200
parent: operations
sourceRevision: a6eca6835a9f0bd4
---

Déplacez un panneau à une position, dans sa séquence ou une autre.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `panel` | `string` | Oui | Voir les paramètres de l’opération.  |
| `sequence` | `string` | Non | Voir les paramètres de l’opération.  |
| `index` | `integer` | Non | Voir les paramètres de l’opération. `minimum=0` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation move_panel
```

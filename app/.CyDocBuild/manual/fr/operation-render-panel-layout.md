---
id: operation-render-panel-layout
title: render_panel_layout
description: Renderiser le dessin 2D ou la prise 3D (de la caméra de départ ou de fin) dans le projet ; il devient l'image du panneau. 3D écrit également une carte de profondeur.
section: Référence
order: 200
parent: operations
sourceRevision: a47fd5b0988d709a
---

Renderiser le dessin 2D ou la prise 3D (de la caméra de départ ou de fin) dans le projet ; il devient l'image du panneau. 3D écrit également une carte de profondeur.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `panel` | `string` | Oui | Voir les paramètres de l’opération.  |
| `camera` | `string` | Non | Voir les paramètres de l’opération. `default="start"`, `enum=["start", "end"]` |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `render` | `string` | Oui | Voir les paramètres de l’opération.  |
| `depth` | `string` | Non | Voir les paramètres de l’opération.  |
| `project` | `string` | Non | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation render_panel_layout
```

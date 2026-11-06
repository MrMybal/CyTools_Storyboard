---
id: operation-export-animatic
title: export_animatic
description: Chaque panneau pour sa durée avec son transition, comme un MP4 (les sous-titres optionnels) ; un panneau en 3D joue sa caméra, son personnage et ses mouvements de pose.
section: Référence
order: 200
parent: operations
sourceRevision: 3d59555a73909dd9
---

Chaque panneau pour sa durée avec son transition, comme un MP4 (les sous-titres optionnels) ; un panneau en 3D joue sa caméra, son personnage et ses mouvements de pose.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `captions` | `boolean` | Non | Voir les paramètres de l’opération. `default=true` |
| `fps` | `integer` | Non | Voir les paramètres de l’opération. `default=24`, `minimum=1`, `maximum=60` |
| `motion` | `boolean` | Non | Render les mouvements des panneaux 3D (off: une image par panneau). `default=true` |
| `motion_fps` | `integer` | Non | Images renderizées par seconde pour les mouvements 3D. `default=12`, `minimum=4`, `maximum=24` |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `file` | `string` | Oui | Voir les paramètres de l’opération.  |
| `duration` | `number` | Non | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_animatic
```

---
id: operation-update-object
title: update_object
description: Change une forme sur sa scène (chaque panneau utilisant la scène la voit).
section: Référence
order: 200
parent: operations
sourceRevision: e03c3849cf6fe09f
---

Change une forme sur sa scène (chaque panneau utilisant la scène la voit).

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `object` | `string` | Oui | Voir les paramètres de l’opération.  |
| `name` | `string` | Non | Voir les paramètres de l’opération.  |
| `color` | `string` | Non | Voir les paramètres de l’opération.  |
| `position` | `array` | Non | Voir les paramètres de l’opération.  |
| `rotation` | `array` | Non | Dégrés autour de X, Y, Z.  |
| `scale` | `array` | Non | Taille en mètres pour un cube/sphère/cylindre/cone, un facteur pour les autres.  |
| `role` | `string` | Non | Voir les paramètres de l’opération. `enum=["set", "character", "object", "location"]` |
| `reference` | `string` | Non | Élément de la bibliothèque que représente cette forme.  |
| `pose` | `string` | Non | Pose du personnage sur la scène : une prédéfinie ou un id de pose du projet.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation update_object
```

---
id: operation-add-object
title: add_object
description: Boîte, sphère, cylindre, cône, capsule, plan, mannequin, ou une maillage importé (.glb .gltf .obj .ply .stl .off). Les nouvelles formes se tiennent sur le sol.
section: Référence
order: 200
parent: operations
sourceRevision: d66630c60c91fd16
---

Boîte, sphère, cylindre, cône, capsule, plan, mannequin, ou une maillage importé (.glb .gltf .obj .ply .stl .off). Les nouvelles formes se tiennent sur le sol.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `stage` | `string` | Oui | Voir les paramètres de l’opération.  |
| `shape` | `string` | Non | Voir les paramètres de l’opération. `default="box"`, `enum=["box", "sphere", "cylinder", "cone", "capsule", "plane", "mannequin", "mesh"]` |
| `mesh` | `string` | Non | Fichier maillage, pour shape = maillage.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation add_object
```

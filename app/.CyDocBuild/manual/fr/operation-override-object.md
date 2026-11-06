---
id: operation-override-object
title: override_object
description: Déplacez, tournez, redimensionnez ou masquez une forme dans ce panneau uniquement (un personnage qui marche entre les prises) ; clear = retour à la position sur la scène.
section: Référence
order: 200
parent: operations
sourceRevision: b63de36c6fb7b14d
---

Déplacez, tournez, redimensionnez ou masquez une forme dans ce panneau uniquement (un personnage qui marche entre les prises) ; clear = retour à la position sur la scène.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `panel` | `string` | Oui | Voir les paramètres de l’opération.  |
| `object` | `string` | Oui | Voir les paramètres de l’opération.  |
| `position` | `array` | Non | Voir les paramètres de l’opération.  |
| `rotation` | `array` | Non | Voir les paramètres de l’opération.  |
| `scale` | `array` | Non | Voir les paramètres de l’opération.  |
| `hidden` | `boolean` | Non | Voir les paramètres de l’opération.  |
| `positionEnd` | `value` | Non | Où elle se trouve à la fin du panneau (elle y va) ; null = immobile.  |
| `rotationEnd` | `value` | Non | Voir les paramètres de l’opération.  |
| `pose` | `string` | Non | Pose du personnage dans ce panneau : debout, marchant, courant, assis, genoux baissés, bras levés, pointant ou une pose de projet id (add_pose).  |
| `poseEnd` | `string` | Non | Positionner à la fin du panneau (mêmes valeurs).  |
| `clear` | `boolean` | Non | Voir les paramètres de l’opération. `default=false` |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation override_object
```

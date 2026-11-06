---
id: operation-validate-storyboard
title: validate_storyboard
description: Images manquantes, cases vides, durées en dehors des limites, références inconnues.
section: Référence
order: 200
parent: operations
sourceRevision: b76b217f860aface
---

Images manquantes, cases vides, durées en dehors des limites, références inconnues.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
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
runtime\python\Scripts\python.exe app\tool.py describe-operation validate_storyboard
```

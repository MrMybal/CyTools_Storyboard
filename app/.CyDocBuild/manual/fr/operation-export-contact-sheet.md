---
id: operation-export-contact-sheet
title: export_contact_sheet
description: Toutes les cases sur un PNG avec des numéros, des durées et du texte.
section: Référence
order: 200
parent: operations
sourceRevision: 38fc2e0362851197
---

Toutes les cases sur un PNG avec des numéros, des durées et du texte.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `columns` | `integer` | Non | Voir les paramètres de l’opération. `default=4`, `minimum=1`, `maximum=10` |
| `cell_width` | `integer` | Non | Voir les paramètres de l’opération. `default=480`, `minimum=160`, `maximum=1200` |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `file` | `string` | Oui | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_contact_sheet
```

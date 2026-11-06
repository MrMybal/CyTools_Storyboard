---
id: operation-export-summary
title: export_summary
description: Le scénario comme Markdown ou comme une seule page HTML autonome.
section: Référence
order: 200
parent: operations
sourceRevision: 8676b18ea6b9b084
---

Le scénario comme Markdown ou comme une seule page HTML autonome.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `format` | `string` | Non | Voir les paramètres de l’opération. `default="html"`, `enum=["md", "html"]` |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `file` | `string` | Oui | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_summary
```

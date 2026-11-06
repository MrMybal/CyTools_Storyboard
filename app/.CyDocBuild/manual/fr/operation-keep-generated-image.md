---
id: operation-keep-generated-image
title: keep_generated_image
description: Copiez l'une des images retournées par generateimages dans le projet avec sa recette, et l'attachez à sa cible.
section: Référence
order: 200
parent: operations
sourceRevision: eda24e186425c4b0
---

Copiez l'une des images retournées par generate_images dans le projet avec sa recette, et l'attachez à sa cible.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `file` | `string` | Oui | Voir les paramètres de l’opération.  |
| `attach` | `boolean` | Non | Voir les paramètres de l’opération. `default=true` |
## Retours {#returns}

Aucun champ nommé n’est déclaré à ce niveau. Consultez le schéma avec `describe-operation` pour connaître sa forme exacte.

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation keep_generated_image
```

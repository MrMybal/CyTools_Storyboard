---
id: operation-remove-image-model
title: remove_image_model
description: Supprimez les fichiers d'un modèle qui ne sont utilisés par aucun autre modèle installé.
section: Référence
order: 200
parent: operations
sourceRevision: 178c4dd92d51e712
---

Supprimez les fichiers d'un modèle qui ne sont utilisés par aucun autre modèle installé.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `model` | `string` | Oui | Voir les paramètres de l’opération. `enum=["qwen-image-2.1-controlnet-int8", "qwen-image-2.1-int8", "qwen-image-2512-fp8", "qwen-image-edit-2511-int8"]` |
## Retours {#returns}

Aucun champ nommé n’est déclaré à ce niveau. Consultez le schéma avec `describe-operation` pour connaître sa forme exacte.

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation remove_image_model
```

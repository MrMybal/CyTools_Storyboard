---
id: operation-verify-image-model
title: verify_image_model
description: Vérifiez chaque fichier d'un modèle contre sa déclaration SHA-256.
section: Référence
order: 200
parent: operations
sourceRevision: 70f54666598c3a67
---

Vérifiez chaque fichier d'un modèle contre sa déclaration SHA-256.

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
runtime\python\Scripts\python.exe app\tool.py describe-operation verify_image_model
```

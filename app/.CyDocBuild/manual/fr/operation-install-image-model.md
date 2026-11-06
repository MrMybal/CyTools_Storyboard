---
id: operation-install-image-model
title: install_image_model
description: Téléchargez les fichiers d'un modèle (reprise possible, taille et SHA-256 vérifiés); les fichiers partagés avec un autre modèle ne sont pas téléchargés deux fois.
section: Référence
order: 200
parent: operations
sourceRevision: cd385070de85a937
---

Téléchargez les fichiers d'un modèle (reprise possible, taille et SHA-256 vérifiés); les fichiers partagés avec un autre modèle ne sont pas téléchargés deux fois.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `model` | `string` | Oui | Voir les paramètres de l’opération. `enum=["qwen-image-2.1-controlnet-int8", "qwen-image-2.1-int8", "qwen-image-2512-fp8", "qwen-image-edit-2511-int8"]` |
| `accept_license` | `boolean` | Non | Voir les paramètres de l’opération. `default=true` |
| `repair` | `boolean` | Non | Voir les paramètres de l’opération. `default=false` |
## Retours {#returns}

Aucun champ nommé n’est déclaré à ce niveau. Consultez le schéma avec `describe-operation` pour connaître sa forme exacte.

## Comportement et accès {#behaviour}

- Autorisations requises : `network`
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation install_image_model
```

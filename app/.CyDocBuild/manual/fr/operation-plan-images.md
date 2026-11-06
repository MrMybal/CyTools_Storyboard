---
id: operation-plan-images
title: plan_images
description: Les requêtes que la recette enverrait au modèle d’images (prompts, images de référence, tailles, graines), sans générer quoi que ce soit.
section: Référence
order: 200
parent: operations
sourceRevision: 7352d4cdbf38556e
---

Les requêtes que la recette enverrait au modèle d’images (prompts, images de référence, tailles, graines), sans générer quoi que ce soit.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Non | Projet (nécessaire pour toutes les recettes sauf la recette free).  |
| `recipe` | `string` | Non | character: vues d'un personnage de la bibliothèque; location: vues d'un lieu, vide ou avec un personnage; panel: l'image d'une prise de vue; free: tout prompt. `default="free"`, `enum=["character", "location", "panel", "free"]` |
| `item` | `string` | Non | Identifiant d'élément de la bibliothèque (recette de personnage ou de lieu).  |
| `panel` | `string` | Non | Identifiant de la vue (recette de panel).  |
| `views` | `array` | Non | Clés de vues à rendre; par défaut : les vues activées dans les options.  |
| `character` | `string` | Non | Identifiant du personnage placé dans la localisation (recette de localisation).  |
| `prompt` | `string` | Non | Texte de la recette libre.  |
| `references` | `array` | Non | Recette libre : fichiers d'images ou ids d'éléments de la bibliothèque utilisés comme références (aucun = de la texte).  |
| `format` | `string` | Non | Voir les paramètres de l’opération. `enum=["project", "1:1", "3:4", "4:3", "2:3", "3:2", "9:16", "16:9", "21:9", "2.39:1"]` |
| `extra` | `string` | Non | Ajouté à chaque prompt de la recette.  |
| `extras` | `string` | Non | Recette de panneau : identifiant du personnage que chaque mannequin du plateau sans référence représente (une foule du même personnage).  |
| `label` | `string` | Non | Voir les paramètres de l’opération.  |
| `options` | `object` | Non | Voir les paramètres de l’opération.  |
## Retours {#returns}

Aucun champ nommé n’est déclaré à ce niveau. Consultez le schéma avec `describe-operation` pour connaître sa forme exacte.

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation plan_images
```

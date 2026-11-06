---
id: operation-install-image-engine
title: install_image_engine
description: Créez ou réparez le moteur privé: un environnement Python avec PyTorch (CUDA 13) et une version bloquée de ComfyUI, vérifiée par import.
section: Référence
order: 200
parent: operations
sourceRevision: 338a89f23d608bb4
---

Créez ou réparez le moteur privé: un environnement Python avec PyTorch (CUDA 13) et une version bloquée de ComfyUI, vérifiée par import.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `cpu_only` | `boolean` | Non | Voir les paramètres de l’opération. `default=false` |
## Retours {#returns}

Aucun champ nommé n’est déclaré à ce niveau. Consultez le schéma avec `describe-operation` pour connaître sa forme exacte.

## Comportement et accès {#behaviour}

- Autorisations requises : `network`
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation install_image_engine
```

---
id: operation-export-h3-workflow
title: export_h3_workflow
description: Transformer le story-board en workflow CyToolsMiniMaxH3 (workflow.json + media/) : une génération H3 par panneau avec sa première/ultime image, guides et références clés (personnages, mise en page, lieux, vidéos, voix, sons),…
section: Référence
order: 200
parent: operations
sourceRevision: d6c1084dd5770295
---

Transformer le story-board en workflow CyTools_MiniMaxH3 (workflow.json + media/) : une génération H3 par panneau avec sa première/ultime image, guides et références clés (personnages, mise en page, lieux, vidéos, voix, sons), chaînage, prompts dans la mise en page H3, durées tronquées aux panneaux, et une édition finale avec les transitions du story-board. L'exécuter avec run_workflow dans CyTools_MiniMaxH3.

## Paramètres {#contract}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `project` | `string` | Oui | Dossier de projet (.cystory) ou son storyboard.json ; un nom pur est recherché dans data/projects.  |
| `folder` | `string` | Non | Dossier cible (remplacé) ; par défaut, exports/h3_workflow/<title>.  |
| `options` | `object` | Non | Voir les paramètres de l’opération.  |
| `save_options` | `boolean` | Non | Voir les paramètres de l’opération. `default=true` |
## Retours {#returns}

| Nom | Type | Obligatoire | Description |
|---|---|---|---|
| `shots` | `array` | Oui | Voir les paramètres de l’opération.  |
| `width` | `integer` | Non | Voir les paramètres de l’opération.  |
| `height` | `integer` | Non | Voir les paramètres de l’opération.  |
| `seconds` | `number` | Non | Voir les paramètres de l’opération.  |
| `generations` | `integer` | Non | Voir les paramètres de l’opération.  |
| `steps` | `integer` | Non | Voir les paramètres de l’opération.  |
| `warnings` | `array` | Non | Voir les paramètres de l’opération.  |
| `folder` | `string` | Non | Voir les paramètres de l’opération.  |
| `file` | `string` | Non | Voir les paramètres de l’opération.  |
| `workflow` | `object` | Non | Voir les paramètres de l’opération.  |

## Comportement et accès {#behaviour}

- Autorisations requises : aucune déclarée.
- Moteurs : aucun déclaré.
- Annulation : prise en charge.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe-operation export_h3_workflow
```

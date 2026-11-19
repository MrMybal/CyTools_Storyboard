---
id: operations
title: Automatisation et API
description: Connectez un client et consultez les opérations disponibles.
section: Référence
order: 80
parent: overview
sourceRevision: b261975572b1a892
---

## Ligne de commande {#cli}

Depuis la racine de l’application, utilisez son interpréteur Python privé. `describe` et `list-operations` examinent le contrat public.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe
runtime\python\Scripts\python.exe app\tool.py list-operations
runtime\python\Scripts\python.exe app\tool.py invoke list_storyboards --params "{}"
```

## MCP {#mcp}

Configurez votre client MCP pour lancer l’interpréteur privé avec `app/tool.py mcp`, en utilisant le dossier de l’application comme dossier de travail. Reconnectez-le lorsque le catalogue d’opérations exposées change.

## Fichiers des tâches {#task-files}

Les entrées locales acceptent des chemins absolus lisibles et sont importées automatiquement dans l’espace de la tâche. Exportez les résultats utiles avant de terminer la tâche. Ne réutilisez pas les chemins temporaires après nettoyage.

## Opérations {#operations}

- [`create_storyboard`](doc:operation-create-storyboard)
- [`duplicate_storyboard`](doc:operation-duplicate-storyboard)
- [`list_storyboards`](doc:operation-list-storyboards)
- [`describe_storyboard`](doc:operation-describe-storyboard)
- [`update_storyboard`](doc:operation-update-storyboard)
- [`add_panel`](doc:operation-add-panel)
- [`update_panel`](doc:operation-update-panel)
- [`duplicate_panel`](doc:operation-duplicate-panel)
- [`move_panel`](doc:operation-move-panel)
- [`remove_panel`](doc:operation-remove-panel)
- [`add_sequence`](doc:operation-add-sequence)
- [`update_sequence`](doc:operation-update-sequence)
- [`remove_sequence`](doc:operation-remove-sequence)
- [`add_library_item`](doc:operation-add-library-item)
- [`update_library_item`](doc:operation-update-library-item)
- [`remove_library_item`](doc:operation-remove-library-item)
- [`validate_storyboard`](doc:operation-validate-storyboard)
- [`export_contact_sheet`](doc:operation-export-contact-sheet)
- [`export_summary`](doc:operation-export-summary)
- [`export_animatic`](doc:operation-export-animatic)
- [`add_stage`](doc:operation-add-stage)
- [`update_stage`](doc:operation-update-stage)
- [`remove_stage`](doc:operation-remove-stage)
- [`add_object`](doc:operation-add-object)
- [`update_object`](doc:operation-update-object)
- [`duplicate_object`](doc:operation-duplicate-object)
- [`remove_object`](doc:operation-remove-object)
- [`add_pose`](doc:operation-add-pose)
- [`update_pose`](doc:operation-update-pose)
- [`remove_pose`](doc:operation-remove-pose)
- [`set_panel_layout`](doc:operation-set-panel-layout)
- [`override_object`](doc:operation-override-object)
- [`render_panel_layout`](doc:operation-render-panel-layout)
- [`suggest_camera_move`](doc:operation-suggest-camera-move)
- [`export_h3_film`](doc:operation-export-h3-film)
- [`export_h3_workflow`](doc:operation-export-h3-workflow)
- [`preview_h3_workflow`](doc:operation-preview-h3-workflow)
- [`preview_h3_film`](doc:operation-preview-h3-film)
- [`plan_images`](doc:operation-plan-images)
- [`generate_images`](doc:operation-generate-images)
- [`keep_generated_image`](doc:operation-keep-generated-image)
- [`export_image_workflows`](doc:operation-export-image-workflows)
- [`image_engine_status`](doc:operation-image-engine-status)
- [`unload_image_model`](doc:operation-unload-image-model)
- [`install_image_engine`](doc:operation-install-image-engine)
- [`install_image_model`](doc:operation-install-image-model)
- [`verify_image_model`](doc:operation-verify-image-model)
- [`remove_image_model`](doc:operation-remove-image-model)


## Communication native {#native-communication}

Le paquet Windows contient CyToolsCore 0.11.0 et la bibliothèque de communication
native CyMCPSDK 0.7.1. Les mêmes paramètres complets des opérations sont disponibles
pour les clients IA et l’application autonome. Lancez `ai_communication_status` avec
`includeOperations: true` pour consulter le catalogue effectif. Cette opération ne
contacte aucun fournisseur IA et ne génère pas de contenu.

Les fichiers générés par la CLI sont temporaires par défaut. Ajoutez `--export-dir`
suivi d’un dossier absolu hors du stockage des jobs pour les conserver. Par MCP,
exportez avec `cy_export_job` avant `cy_finish_task`. Le nettoyage des tâches ne
supprime pas les entrées originales, modèles installés, conversations et documents
de projet persistants.

Pour la première migration depuis Core 0.10.x, installez le paquet Windows complet.
Une mise à jour de l’application seule ne peut pas ajouter la bibliothèque native
au précédent runtime. Les intégrations de modèles et de fournisseurs conservent
leurs compatibilités et permissions : cette mise à jour ne rend pas compatible un
modèle ou une plateforme non pris en charge.

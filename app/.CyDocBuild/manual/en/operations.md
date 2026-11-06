---
id: operations
title: Automation and API
description: Connect a client and inspect the available operations.
section: Reference
order: 80
parent: overview
revision: eda11f1d29dd44b2
---

## Command line {#cli}

From the application root, use the private Python interpreter. `describe` and `list-operations` inspect the public contract.

```powershell
runtime\python\Scripts\python.exe app\tool.py describe
runtime\python\Scripts\python.exe app\tool.py list-operations
runtime\python\Scripts\python.exe app\tool.py invoke list_storyboards --params "{}"
```

## MCP {#mcp}

Configure your MCP client to start the private interpreter with `app/tool.py mcp`, using the application folder as its working directory. Restart the connection when its exposed operation catalogue changes.

## Task files {#task-files}

Local file inputs accept absolute readable paths and are imported into the task workspace automatically. Export wanted results before finishing the task. Do not rely on temporary paths after task cleanup.

## Operations {#operations}

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

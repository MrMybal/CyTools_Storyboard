---
id: installation
title: Installation and models
description: Prepare the runtime, engines and optional models.
section: Guide
order: 5
parent: overview
revision: e76de1a045623e61
---

## Start the application {#start}

Open `CyTools_Storyboard.exe` on Windows. If the private runtime is missing, follow the installation steps in [Features and installation](doc:guide-readme). Launchers and engine requirements differ by application; do not assume that a copied source folder is a portable installation.

## Engines and models {#models}

Editing boards and layouts does not require the image model. Image generation needs its separate ComfyUI environment, compatible Qwen-Image weights and an appropriate NVIDIA GPU. Exporting a MiniMax H3 film prepares a handoff; H3 inference is performed by the receiving tool.

Read the licence and source shown for each component before downloading. When access is restricted, open the official model page, obtain access with your account and authenticate locally. Do not paste credentials into generation settings.

## Storage {#storage}

Keep application data and model weights separate from the application files. Check the selected installation folder and available disk space before starting a large download. Changing a download-cache setting does not move existing models.

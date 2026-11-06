---
id: guide-lisez-moi
title: User guide
description: Use the application step by step.
section: Guide
order: 10
parent: overview
revision: 57e9dd30df547d36
---

## CyTools Storyboard {#cytools-storyboard}

Prepare a film frame by frame: images, durations, prompts, dialogues, camera, sound, and references, before transforming it into a workflow (the conversion will come in a later version; the format is independent of the generator).

## Start {#demarrer}

Double-click `CyTools_Storyboard.exe`, then New (or Open... / Recent). Projects are created in `data/projects/` as a folder `Titre.cystory`: `storyboard.json` + `assets/` (all imported images and sounds are copied there), so the folder can be moved or sent as is.

## The screen {#l-ecran}

- References (left column): characters, locations, objects, styles, images, sounds, videos, with description, tags, and files (add or paste from clipboard). Drag a reference onto a map to add it to the scene.
- Table (center) : sequences and their plans in cards (image, number, duration, status, references). Drag a card onto another to move it, or onto the title of a sequence; right-click to duplicate, insert or delete.
- Inspector (right): title, duration (with 4/5/8/10/15 s), status, color; images with their role (sketch, first/last image, key image at an instant, reference); structured prompt (scene, action, shot value, angle, camera movement, amplitude, speed, lens, dialogues by character and language, sound, music, free text); checked references; transition to the next shot; notes; check remarks.
- Timeline (bottom) : the plans at the time scale; pulling the right edge of a plan changes its duration; fades make the plans overlap as exported.
- Read the animatic : minute reading in a window, with pause and cursor.
- Exporter : contact sheet (PNG), script (HTML autonomous or Markdown), animatic (MP4 with captions). In the animatic MP4, a staged 3D shot plays its movement: camera from start to finish, characters moving, turning and changing poses (12 rendered images per second, adjustable by operation `export_animatic` : `motion`, `motion_fps`); other shots remain a fixed image. The integrated reader, on the other hand, shows one image per shot. The files go into `exports/` of the project.

## Staging: image, 2D drawing or 3D stage {#mise-en-scene-image-dessin-2d-ou-plateau-3d}

Each plan chooses how it is represented (inspector, scene layout section, or scene tab):

- Image : the images imported or pasted, as before.
- 2D Drawing: Quick sketches in the film format — rectangle, ellipse, line, arrow (movement), pencil, silhouette (stands on the clicked point), text; color, thickness, fill, background; selection for moving or deleting.
- 3D Stage: Simple shapes (cube, sphere, cylinder, cone, capsule, plane, mannequin) or imported meshes (.glb .gltf .obj .ply .stl .off), shared across multiple planes: the same location remains in the same place from one plane to another. Each shape has a name, a role (set decoration, character, object, location), a color, and can point to a library reference. Placement using gizmo (W to move, E to rotate, R to scale) or keyboard; the 'Move in this plane only' box moves a character for this plane without affecting the stage (marked `*`).
- Navigation: Right-click drag = orbit, middle-click = move, scroll wheel = zoom, left-click = select.
- View Through: Free view, camera of the current plane (start) or end camera; when viewing through a camera, the same gestures move it. 'Start = this view' / 'End = this view' set the cameras; focal length in mm (equivalent 24x36) and roll. Cameras of other planes on the same stage are drawn in gray.
- Propose Camera Movement compares the start and end cameras and fills the prompt (traveling forward, lateral, panoramic, zoom, arc...).

Rendered image (and, in 3D, a depth map) becomes the image of the plane one second after each change: used in cards, contact sheet, script, and animatic.

Undo / Redo (Ctrl+Z / Ctrl+Y). All changes are automatically saved one second after each modification, with 5 backup copies in `backups/` of the project. If the CLI or a AI (MCP) modifies the project while the window is open, the window reloads (without overwriting an unsaved modification).

## MiniMax H3 Film (Export > MiniMax H3 Film...) {#film-minimax-h3-exporter-film-minimax-h3}

Transform the storyboard into a multi-segment film for MiniMax H3: one segment per shot, which starts a few frames before the end of the previous one to keep the locations, characters, lighting, and sound from one shot to the next (these frames are removed during editing). Each segment receives its frames, numbered `<Picture 1>`...:

1. the characters' identity (those from the plan, or all in each segment) — first image from the library reference;
2. the image of the plan: the 2D/3D rendering of the staging, otherwise sketch, first/last image, key image;
3. the places, objects and styles referenced by the plan.

And, by segment (3 each, 12 references in total)

- reference videos `<Video N>`: the video library elements used by the plan (movement, action, camera). Each video belongs only to its segment;
- sounds `<Audio N>`: the voice of a character (an audio file among its files, used in every segment where it appears), the audio elements of the plan and, optionally, the reference video sounds. Long references are cut off (up to 15 seconds, adjustable).

The prompt of each segment = global text (style, note on images), sentence on images repeated, one sentence per image, then the text of the plan (value of plan, scene, action, camera, dialogues, sound). All these sentences are modifiable (section Phrases), as the overlap (0 to 73 images, on cuts and/or fades), resolution and sampling in two passes. The table shows live each segment: images, requested duration and real duration (H3 counts in 5 + 17n images), complete prompt.

Export written in `exports/h3_film/<titre>/`: `film.json` + `images/`, two workflows ComfyUI (`workflow_cytools_film.json` with our render nodes on disk, `workflow_timeline_director.json` with only the nodes Timeline Director) and a `LISEZ-MOI.txt`. The same `film.json` opens in CyTools_MiniMaxH3 (Film tab) to generate it on Colab.

Film files (section Destination of film) : by default each project exports into its own folder; one can choose a common folder, for example `Mon Drive/ComfyUI/input/cytools_film` with Google Drive for computer. Each film has its own folder, and the path read by the node CyTools H3 Film Plan (`cytools_film/<film>/film.json`, relative to the folder `input` of ComfyUI) is calculated and displayed. Reexport replaces the previous export of the same film; a folder that does not contain an export is never emptied (export is refused). When plans have a control (depth or pose), the workflow `workflow_cytools_film.json` adds the loader of ControlNet Fun Union (`ModelPatchLoader`); its file is set in File ControlNet (workflow ComfyUI).

For the ComfyUI H3 Colab kit (shared notebook, version 15 and later): the mounting is done here, the export goes to `input/cytools_film/`, then in ComfyUI we open the film workflow and start it; the unchanged segments from a previous render are reused after a retouch.

## Workflow MiniMax H3 (Export > Workflow MiniMax H3...) {#workflow-minimax-h3-exporter-workflow-minimax-h3}

Converts the storyboard into a CyTools_MiniMaxH3 workflow (`workflow.json` + `media/`), to be opened in its Workflows tab: one H3 generation per shot, followed by a final montage with the transitions from the storyboard (cut, chained fade, fade to black). This is another way to produce the film: each shot is an independent take that can be redone alone, while the 'Film' export generates a continuous film segment by segment.

- Durations: H3 generates between 4 to 15 seconds. A shorter shot is generated at 4 seconds and then cut; a longer shot is split into chained segments (each segment starts with the last image of the previous one); each shot is cut to its exact duration.
- Images: first / last image of the shot → first / last image of the generation; keyframes → guides at their instant; 2D/3D scene render → reference image (or first image, as chosen).
- References: character identity, sketches, locations, objects, styles, reference videos, character voices, sounds (9 images, 3 videos, 3 sounds, 12 in total).
- Chaining: a shot can start with the last image of the previous one (after a chained fade by default, always or never).
- Prompt in official format H3 : `subject_definitions` (`<Subject 1>` = the character of `<Picture 1>`, voice `<Audio N>`), `summary`, `retention_analysis`, `detailed_description`, dialogues `<d>[English] ...</d>` with (S1), (S2)..., `overall_soundscape`, `non_diegetic_music`.
- Seed, not, turbo (with or without references), format and all sentences are settings; the table shows for each shot the requested, generated and kept duration, and the exact prompt.

## Character poses and movements (Scenes tab) {#poses-et-deplacements-des-personnages-onglet-mise-en-scene}

A character on set (mannequin or capsule, role 'character') has a pose: standing, walking, running, sitting, crouching, arms raised, pointing. The 3D mannequin takes it. For a given shot, you can also choose a final pose (it transitions from one to another) and check 'Moves during the shot' with a start and end position and rotation (using the gizmo with 'Gizmo on the end position', or the values). A standing character who moves walks (the walking cycle is calculated based on the distance). The 'Moment in the shot' cursor shows the scene at any point in the shot.

Joints (section 'Joints' under the pose): torso (lean, pivot), head (turn, lift), for each arm lift forward/side and bend the elbow, for each leg lift forward/side and bend the knee, and the sitting position (hip height). You set the start or end pose; 'Symmetric' applies the same setting to both sides. Tapping a joint from a predefined pose creates a copy: a project pose, named, reusable by all characters and in all shots (listed after the predefined poses). A project pose can 'walk when the character moves' (then its legs follow the walking cycle, its arms stay as they are). The mannequin, renders, and OpenPose control skeleton follow these poses. In the 3D view, the selected character shows handles (box 'Pose handles in view'), moved in the shot facing the camera:

hands and feet: you grab a hand or foot and place it; the arm (shoulder, elbow) or leg (hip, knee) folds to reach it. Out of reach, the limb stretches towards the point;

- elbows and knees: the arm or leg turns around the shoulder-hand line (hip-foot) — the hand or foot does not move, the elbow or knee goes as close as possible to the point. This setting is also a slider ('Turn the forearm / knee outward'); an extended limb does not have an elbow to orient;
- In the 3D view, the selected character shows handles (box 'Pose handles in view'), moved in the shot facing the camera:
- head: a handle floats in front of the face, connected to the nose by a line; it can be moved and the head will look at that point (rotation and tilting).
- shoulders: the upper body tilts, turns, and leans to the side to bring the shoulder to the point; the arms and head follow, while the legs remain still. The shoulder stays at its distance from the pelvis: if pulled further, the torso will reach its limits. Leaning to the side is also a cursor ("Lean to the side").
- neck: the upper body tilts forward, backward, or to the side to bring the neck to the point without turning (the torso rotation is controlled by the shoulders). The neck stays at its distance from the pelvis: pulling it straight down doesn't change much; it's the front or side that you pull it to.
- pelvis: the handle, between the two hips, moves the pelvis and the feet stay on the ground. Down, the knees bend (squatting); to the side or forward, the weight shifts from one leg to the other and the character shifts in that plane to keep its feet from sliding. The pelvis never rises higher than the legs can extend. Sitting, the handle sets the height of the seat.
- hips: pulling one hip up or down makes the pelvis pivot around the other hip (swaying). The legs, attached to the pelvis, follow and stay on the ground; the upper body keeps its angles (it only rises or falls with the pelvis). Standing with legs straight, the hip cannot rise higher: the other one then lowers and its knee bends, like when swaying. Sitting, the seat height follows. The swaying is also a cursor ("Pelvis Swivel", ±25°). With the hip only 10 cm from the center of the pelvis, the gesture is multiplied: the "Hips Multiplication" setting next to the checkbox is set from 1:1 (direct) to 1:10, 1:4 by default (the handle moves four times less than the mouse). The setting is saved in preferences. fingers: each hand has five fingers with three phalanges. At the end of each finger, a small colored handle (thumb red, index yellow, middle green, ring blue, pinky purple) can bend or straighten that finger alone to bring its tip to the point. These handles only appear if the hand is large enough on the screen (zoom in on it); check "Fingers". From the front, a hanging hand is seen by its palm and its fingers overlap: turning the view separates them. In the joints, each hand has a cursor per finger (bent, in %) and the spread of the fingers; the predefined pose "pointing" extends the index and bends the others.
- fingers. The 3D model now has hands (palm and phalanges). fingers. The 3D model now has hands (palm and phalanges).
- wrist: a white handle on the palm (at the knuckles) bends the wrist so that the hand points toward the point — toward the palm or the back of the hand (-70 to 80°), toward the thumb or the little finger (-25 to 35°); the fingers keep their flexion. It appears when the hand is large enough on the screen (otherwise it would be confused with the wrist handle). Both angles are also cursors for the hand ("Wrist Bent", "Wrist Toward Thumb").
- toes: each foot now has a heel, sole, and toes. The foot remains flat on the ground regardless of what the leg does, and points where the leg points (a knee turned outward turns the foot). An orange handle at the end of the toes raises or bends them; it appears when the foot is large enough on the screen (otherwise it would be confused with the ankle handle), and remains available during walking. The toes do not sink into the ground: on a flat foot, pulling them down does not change anything. The foot cursors also set the foot's tilt ("Foot Tilted (Pointing Down)", -30 to 60°): this is now the lowest point of the soles that touch the ground, so on tiptoe (foot tilted, toes raised) the whole body rises by about 8 cm. The model, the depth map, and the OpenPose skeleton of the control show the feet.

The handle modifies the pose during adjustment (beginning or end): the view is placed at the beginning or end of the shot during the gesture. The angles remain within the limits of the body. A character's legs that are moving follow the walk: their feet, knees, hips, and pelvis do not have handles. Poses recorded before the addition of limb rotation (three angles), side tilt, or pelvis sway remain valid: these angles are then 0; without hand adjustment, the fingers are slightly bent (15%) and the wrist is straight; without foot adjustment, they are flat, toes straight.

## Depth or Pose Control (3D Staged Scenes) {#controle-par-la-profondeur-ou-la-pose-plans-mis-en-scene-en-3d}

In both exports (Film and Workflow), each 3D staged scene on the set receives a depth video that guides the generation by Fun ControlNet Union: a depth image per generated image, along the camera movement of the shot (camera start → camera end), with a fixed depth scale to avoid flickering. In the film, images from the previous segment hold the end of the previous shot.

As blocking is just an indication (a cube for a wall, a capsule for a character), the level is adjusted:

| Level | Strength | Applied on | Blurred |
|---|---|---|---|
| Indicative (default) | 0,35 | 35% of steps | Strong: disposition and depth order only |
| Guided | 0,6 | 60% of steps | medium |
| strict | 1,0 | all steps | none: forms followed closely |
| custom / disabled | optional | optional | optional |

2D image or drawing plans do not have depth.

Source of control (setting 'Control'):

- pose of characters: the OpenPose (18 points, standard colors) characters' skeletons, projected by the camera of the plan to each image, with their poses, their walk and their movements. Seen from behind, the nose and eyes are omitted, as in OpenPose. The hands (OpenPose hand model: 21 points, bones in rainbow colors) are added when they are large enough on screen; 'Hands in pose' box, checked by default (option `poseHands`). The feet follow the OpenPose BODY_25 convention: heel, big toe and little toe connected to the ankle, blue for the left foot, cyan for the right; 'Feet in pose' box checked by default (option `poseFeet`). The basic skeleton remains the one with 18 points;
- depth of the set: as above;
- auto (par défaut) : la pose quand un personnage est dans le cadre, sinon la profondeur de champ ;
- pose on depth: skeletons drawn on the blurred depth, in a single video (experimental: Fun ControlNet Union has not been trained on this mix).

The blur of fidelity levels applies only to depth; the strength and part of the steps apply to both.

## Images: generate the references in the application (Images tab) {#images-generer-les-references-dans-l-application-onglet-images}

H3 works even better with a character as it provides real images. The Images tab generates them within the application, starting from your initial images or from text:

- Character : choose a character from the library. Its images (the first, as many as the model accepts) serve as references and the application generates the checked views: face, three-quarters, profile, back, portraits... Without an image, the views start from its description.
- Location : same principle for a setting (wide shot, close-up, close shot, detail), empty or with a character inside ('Character in the location').
- Plan : the image of a plan. The 3D mise en scène gives the framing, the character and the location of the plan give the appearance, the text of the plan gives the action. 'Framing coming from the 3D mise en scène' chooses how: structure guide (the depth or stage pose passes through the ControlNet of the model; the model never sees a gray mannequin), scene image (the mannequin render is sent as an image, to replace), both, or none. In automatic, the structure guide is taken as soon as the ControlNet is installed. The character is sent with several images ('Images per character' : its first image, then its views generated, whole body first). When the stage contains models without reference (a crowd), the list "models without reference are" tells the model that they are other instances of a character.
- Free prompt: a text, with or without reference images.

Each view is a modifiable line (case, format, text) ; « Add a view » creates others. Sentences sent to the model are in « Phrases », and « What will be asked » shows the exact prompt of each image before launching.

Generate starts the calculation; images arrive on the right. Keep copy the image in the project with its recipe (prompt, references, seed, model): it adds to the images of the character or place, or becomes the first image of the plan — it is she that the export H3 sends instead of the render mannequins. Reproduce the seed reuses the seed of an image for the next ones. Images not kept remain in the work folder.

### LoRA {#lora}

In « Generation », the section LoRA lists the files `.safetensors` from the folder `data/models/comfyui/loras/` (« Add files LoRA... » copies them there, « Open the folder of LoRA » opens it). Check those to apply and set their strength (from -2 to 2); they are applied to the model in the order of the list, before the LoRA « few steps » of the model. A LoRA is done for a family of model (Qwen-Image 2.1, Qwen-Image-Edit 2511 or Qwen-Image 2512): a LoRA from another family has no useful effect. Its trigger words are put in the prompt or in « Added to each image ». The LoRA used are noted in the recipe of each kept image and in the workflows ComfyUI exported.

### Engine and Models (Installation, at the top right of the tab) {#moteur-et-modeles-installation-en-haut-a-droite-de-l-onglet}

At the beginning, nothing is installed:

1. Install or repair the engine: create `runtime/engines/image` (Python private, PyTorch CUDA 13) and download ComfyUI (fixed version) into `runtime/sources/ComfyUI`. Approximately 8 GB.
2. Download a model (resumable, size and SHA-256 verified):

| model | Usage | Size | License |
|---|---|---|---|
| Qwen-Image 2.1 (int8) — default | single text and up to 10 references | 17.3 GB | Qwen Research (non-commercial) |
| Qwen-Image 2.1 ControlNet (int8) | structure guide for plans (depth, pose) | 3.8 Go | Qwen Research (non-commercial) |
| Qwen-Image-Edit 2511 (int8) | 1 to 3 references, 4 steps without its LoRA | 31.0 Go | Apache-2.0 |
| Qwen-Image 2512 (fp8) | text only, 4 steps without its LoRA | 30.9 Go | Apache-2.0 |

Files go into `data/models/comfyui/`; the text encoder and the common VAE for 2511 and 2512 are downloaded only once.

The engine is a private ComfyUI that the application launches itself, in the background, on `127.0.0.1` only. The model remains in memory between two generations (setting 'Keep the model in memory', 30 minutes by default, 0 = until closure); Unloading frees it immediately. Canceling a generation stops the current image without unloading the model.

Another ComfyUI: by providing an address (the tunnel of your ComfyUI Colab, for example), the same images are calculated there instead of on this computer; the models must then be in its `models/` folders.

### The same images in ComfyUI {#les-memes-images-dans-comfyui}

Workflows ComfyUI... write, for what is chosen on screen, a folder `exports/comfyui_images/` with:

- `<nom>.json`: the workflow to drag onto the page ComfyUI (all plans/views, common loaders);
- `<nom>_api.json` : the same graph in format API;
- `cytools_images/` : reference images, to be copied into `ComfyUI/input/`.

It is exactly the graph that the application calculates; the workflow note lists the expected model files.

## Limitations (30/09/2026) {#limites-30-09-2026}

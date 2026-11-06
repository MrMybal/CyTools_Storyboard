# CyTools Storyboard

[Documentation](https://mrmybal.github.io/CyTools_Storyboard/#/fr/overview) · [English](https://mrmybal.github.io/CyTools_Storyboard/#/en/overview)

Préparer un film généré plan par plan : images, durées, prompts, dialogues, caméra, son et
références, avant de le transformer en workflow (la conversion viendra dans une version
suivante ; le format est indépendant du générateur).

## Démarrer

Double-cliquer **`CyTools_Storyboard.exe`**, puis **Nouveau** (ou **Ouvrir...** /
**Récents**). Les projets sont créés dans `data/projects/` sous la forme d'un dossier
`Titre.cystory` : `storyboard.json` + `assets/` (toutes les images et sons importés y sont
copiés), donc le dossier peut être déplacé ou envoyé tel quel.

## L'écran

- **Références** (colonne de gauche) : personnages, lieux, objets, styles, images, sons,
  vidéos, avec description, tags et fichiers (ajout ou collage depuis le presse-papiers).
  Glisser une référence sur une carte l'ajoute au plan.
- **Tableau** (centre) : les séquences et leurs plans en cartes (image, numéro, durée,
  statut, références). Glisser une carte sur une autre pour la déplacer, ou sur le titre
  d'une séquence ; clic droit pour dupliquer, insérer ou supprimer.
- **Inspecteur** (droite) : titre, durée (avec 4/5/8/10/15 s), statut, couleur ; images
  avec leur rôle (croquis, première / dernière image, image clé à un instant, référence) ;
  prompt structuré (scène, action, valeur de plan, angle, mouvement de caméra, amplitude,
  vitesse, objectif, dialogues par personnage et langue, son, musique, texte libre) ;
  références cochées ; transition vers le plan suivant ; notes ; remarques de vérification.
- **Frise** (bas) : les plans à l'échelle du temps ; tirer le bord droit d'un plan change sa
  durée ; les fondus font chevaucher les plans comme à l'export.
- **Lire l'animatic** : lecture minutée dans une fenêtre, avec pause et curseur.
- **Exporter** : planche contact (PNG), script (HTML autonome ou Markdown), animatic (MP4
  avec légendes). Dans l'animatic MP4, un plan mis en scène en 3D **joue son mouvement** :
  caméra de début à fin, personnages qui se déplacent, tournent et changent de pose (12 images
  rendues par seconde, réglable par l'opération `export_animatic` : `motion`, `motion_fps`) ; les
  autres plans restent une image fixe. Le lecteur intégré, lui, montre une image par plan. Les
  fichiers vont dans `exports/` du projet.

## Mise en scène : image, dessin 2D ou plateau 3D

Chaque plan choisit comment il est représenté (inspecteur, section **Mise en scène**, ou
onglet **Mise en scène**) :

- **Image** : les images importées ou collées, comme avant.
- **Dessin 2D** : un croquis rapide au format du film — rectangle, ellipse, ligne, flèche
  (mouvement), crayon, silhouette (se tient sur le point cliqué), texte ; couleur, épaisseur,
  remplissage, fond ; sélection pour déplacer ou supprimer.
- **Plateau 3D** : un décor de formes simples (cube, sphère, cylindre, cône, capsule, plan,
  mannequin) ou de maillages importés (.glb .gltf .obj .ply .stl .off), partagé par plusieurs
  plans : un même lieu reste au même endroit d'un plan à l'autre. Chaque forme a un nom, un
  rôle (décor, personnage, objet, lieu), une couleur et peut pointer vers une référence de la
  bibliothèque. Placement au gizmo (W déplacer, E tourner, R échelle) ou au clavier ; la case
  « Déplacer dans ce plan seulement » déplace un personnage pour ce plan sans toucher au
  plateau (marqué `*`).
  - Navigation : clic droit glissé = orbite, clic milieu = déplacement, molette = zoom,
    clic gauche = sélection.
  - **Regarder par** : vue libre, caméra du plan (début) ou caméra de fin ; en regardant par
    une caméra, les mêmes gestes la déplacent. « Début = cette vue » / « Fin = cette vue »
    posent les caméras ; focale en mm (équivalent 24x36) et roulis. Les caméras des autres
    plans du même plateau sont dessinées en gris.
  - **Proposer le mouvement de caméra** compare la caméra de début et celle de fin et remplit
    le prompt (travelling avant, latéral, panoramique, zoom, arc...).

L'image rendue (et, en 3D, une carte de profondeur) devient l'image du plan une seconde après
chaque changement : cartes, planche contact, script et animatic l'utilisent.

Annuler / Rétablir (Ctrl+Z / Ctrl+Y). Tout est enregistré automatiquement une seconde après
chaque modification, avec 5 copies de secours dans `backups/` du projet. Si la CLI ou une IA
(MCP) modifie le projet pendant que la fenêtre est ouverte, la fenêtre le recharge (sans
écraser une modification non encore enregistrée).

## Film MiniMax H3 (Exporter > Film MiniMax H3...)

Transforme le storyboard en film multi-segments pour MiniMax H3 : un segment par plan, qui
commence quelques images avant la fin du précédent pour garder les lieux, les personnages,
la lumière et le son d'un plan à l'autre (ces images sont retirées au montage). Chaque
segment reçoit ses images, numérotées `<Picture 1>`... :

1. l'identité des personnages (ceux du plan, ou tous dans chaque segment) — première image
   de la référence de la bibliothèque ;
2. l'image du plan : le rendu 2D/3D de la mise en scène, sinon croquis, première/dernière
   image, image clé ;
3. les lieux, objets et styles référencés par le plan.

Et, par segment (3 de chaque, 12 références en tout) :

- **vidéos de référence** `<Video N>` : les éléments de bibliothèque de type vidéo utilisés
  par le plan (mouvement, action, caméra). Chaque vidéo n'appartient qu'à son segment ;
- **sons** `<Audio N>` : la **voix** d'un personnage (un fichier audio parmi ses fichiers,
  utilisé dans chaque segment où il apparaît), les éléments de type audio du plan et, en
  option, le son des vidéos de référence. Les références trop longues sont coupées
  (15 s au plus, réglable).

Le prompt de chaque segment = texte global (style, note sur les images), phrase sur les
images reprises, une phrase par image, puis le texte du plan (valeur de plan, scène, action,
caméra, dialogues, son). **Toutes ces phrases sont modifiables** (section *Phrases*), comme
le chevauchement (0 à 73 images, sur les coupes et/ou les fondus), la résolution et
l'échantillonnage en deux passes. Le tableau montre en direct chaque segment : images, durée
demandée et durée réelle (H3 compte en 5 + 17n images), prompt complet.

L'export écrit dans `exports/h3_film/<titre>/` : `film.json` + `images/`, deux workflows
ComfyUI (`workflow_cytools_film.json` avec nos nœuds de rendu sur disque,
`workflow_timeline_director.json` avec les seuls nœuds Timeline Director) et un
`LISEZ-MOI.txt`. Le même `film.json` s'ouvre dans CyTools_MiniMaxH3 (onglet Film) pour le
générer sur Colab.

**Dossier des films** (section *Destination du film*) : par défaut chaque projet exporte dans
son propre dossier ; on peut choisir un dossier commun, par exemple
`Mon Drive/ComfyUI/input/cytools_film` avec Google Drive pour ordinateur. Chaque film y a son
dossier, et le chemin lu par le nœud **CyTools H3 Film Plan** (`cytools_film/<film>/film.json`,
relatif au dossier `input` de ComfyUI) est calculé et affiché. Réexporter remplace l'export
précédent du même film ; un dossier qui ne contient pas d'export n'est jamais vidé (l'export
est refusé). Quand des plans ont un contrôle (profondeur ou pose), le workflow
`workflow_cytools_film.json` ajoute le chargeur du ControlNet Fun Union (`ModelPatchLoader`) ;
son fichier se règle dans *Fichier ControlNet (workflow ComfyUI)*.

Pour le kit Colab ComfyUI H3 (notebook partagé, V15 et suivantes) : le montage se fait ici,
l'export va dans `input/cytools_film/`, puis dans ComfyUI on ouvre le workflow du film et on
lance ; les segments inchangés d'un rendu précédent sont réutilisés après une retouche.

## Workflow MiniMax H3 (Exporter > Workflow MiniMax H3...)

Convertit le storyboard en workflow de **CyTools_MiniMaxH3** (`workflow.json` + `media/`), à
ouvrir dans son onglet Workflows : **une génération H3 par plan**, puis un montage final avec
les transitions du storyboard (coupe, fondu enchaîné, fondu au noir). C'est l'autre façon de
produire le film : chaque plan est une prise indépendante que l'on peut refaire seule,
alors que l'export « Film » génère un film continu segment après segment.

- **Durées** : H3 génère de 4 à 15 s. Un plan plus court est généré sur 4 s puis recoupé ;
  un plan plus long est découpé en parties enchaînées (chaque partie démarre sur la
  dernière image de la précédente) ; chaque plan est recoupé à sa durée exacte.
- **Images** : première / dernière image du plan → première / dernière image de la
  génération ; images clés → guides à leur instant ; rendu de mise en scène 2D/3D →
  image de référence (ou première image, au choix).
- **Références** : identité des personnages, croquis, lieux, objets, styles, vidéos de
  référence, voix des personnages, sons (9 images, 3 vidéos, 3 sons, 12 en tout).
- **Enchaînement** : un plan peut démarrer sur la dernière image du précédent (après un
  fondu enchaîné par défaut, toujours ou jamais).
- **Prompt** au format officiel H3 : `subject_definitions` (`<Subject 1>` = le personnage
  de `<Picture 1>`, voix `<Audio N>`), `summary`, `retention_analysis`,
  `detailed_description`, dialogues `<d>[English] ...</d>` avec (S1), (S2)…,
  `overall_soundscape`, `non_diegetic_music`.
- Graine, pas, turbo (sans / avec références), format et toutes les phrases sont des
  réglages ; le tableau montre pour chaque plan la durée demandée, générée et gardée, et
  le prompt exact.

## Poses et déplacements des personnages (onglet Mise en scène)

Un personnage du plateau (mannequin ou capsule, rôle « personnage ») a une **pose** : debout,
marche, course, assis, accroupi, bras levés, pointe du doigt. Le mannequin 3D la prend.
Pour un plan donné, on peut aussi choisir une **pose de fin** (il passe de l'une à l'autre)
et cocher **« Se déplace pendant le plan »** avec une position et une rotation de fin (au
gizmo avec « Gizmo sur la position de fin », ou aux valeurs). Un personnage debout qui se
déplace **marche** (cycle de pas calculé d'après la distance). Le curseur **« Moment dans
le plan »** montre la scène à n'importe quel instant du plan.

**Articulations** (section « Articulations » sous la pose) : buste (pencher, pivoter), tête
(tourner, lever), pour chaque bras lever vers l'avant / sur le côté et plier le coude, pour
chaque jambe lever vers l'avant / sur le côté et plier le genou, et la position assise
(hauteur du bassin). On règle la pose de début ou la pose de fin ; « Symétrique » applique
le même réglage aux deux côtés. Toucher une articulation d'une pose prédéfinie en crée une
copie : une **pose du projet**, nommée, réutilisable par tous les personnages et dans tous
les plans (listée à la suite des poses prédéfinies). Une pose du projet peut « marcher quand
le personnage se déplace » (ses jambes suivent alors le cycle de marche, ses bras restent
tels quels). Le mannequin, les rendus et le squelette OpenPose du contrôle suivent ces poses.

**Dans la vue 3D**, le personnage sélectionné montre des poignées (case « Poignées de pose
dans la vue »), déplacées dans le plan face à la caméra :

- **mains et pieds** : on attrape une main ou un pied et on le place ; le bras (épaule, coude)
  ou la jambe (hanche, genou) se replie pour l'atteindre. Hors de portée, le membre se tend
  vers le point ;
- **coudes et genoux** : le bras ou la jambe tourne autour de la ligne épaule-main
  (hanche-pied) — la main ou le pied ne bouge pas, le coude ou le genou va au plus près du
  point. Ce réglage est aussi un curseur (« Tourner l'avant-bras / le genou vers
  l'extérieur ») ; un membre tendu n'a pas de coude à orienter ;
- **tête** : une poignée flotte devant le visage, reliée au nez par un trait ; on la déplace
  et la tête regarde ce point (rotation et inclinaison).
- **épaules** : le haut du corps se penche, tourne et s'incline sur le côté pour amener
  l'épaule au point ; les bras et la tête suivent, les jambes ne bougent pas. L'épaule reste à
  sa distance du bassin : tirée plus loin, le buste va jusqu'à ses limites. L'inclinaison sur
  le côté est aussi un curseur (« Pencher sur le côté ») ;
- **cou** : le haut du corps se penche en avant, en arrière ou sur le côté pour amener le cou
  au point, sans tourner (la rotation du buste se règle par les épaules). Le cou reste à sa
  distance du bassin : le tirer tout droit vers le bas change peu de chose, c'est vers l'avant
  ou sur le côté qu'on le tire ;
- **bassin** : la poignée, entre les deux hanches, déplace le bassin et les pieds restent au
  sol. Vers le bas, les genoux se plient (accroupi) ; de côté ou vers l'avant, le poids passe
  d'une jambe à l'autre et le personnage se décale dans ce plan pour que ses pieds ne glissent
  pas. Le bassin ne monte jamais plus haut que les jambes tendues ne le permettent. Assis, la
  poignée règle la hauteur du siège ;
- **hanches** : une hanche tirée vers le haut ou vers le bas fait **basculer le bassin**
  autour de l'autre hanche (déhanché). Les jambes, attachées au bassin, suivent et les pieds
  restent au sol ; le haut du corps garde ses angles (il monte ou descend seulement avec le
  bassin). Debout jambes tendues, la hanche ne peut pas monter plus haut : c'est alors l'autre
  qui descend et son genou se plie, comme quand on se déhanche. Assis, la hauteur du siège
  suit. La bascule est aussi un curseur (« Bascule du bassin », ±25°). Une hanche n'étant qu'à
  10 cm du centre du bassin, le geste est **démultiplié** : réglage « Démultiplication des
  hanches » à côté de la case des poignées, de 1:1 (direct) à 1:10, 1:4 par défaut (la poignée
  bouge quatre fois moins que la souris). Le réglage est conservé dans les préférences.
- **doigts** : chaque main a cinq doigts de trois phalanges. Au bout de chaque doigt, une petite
  poignée de couleur (pouce rouge, index jaune, majeur vert, annulaire bleu, auriculaire violet)
  plie ou déplie ce doigt seul pour amener son bout au plus près du point. Ces poignées
  n'apparaissent que si la main est assez grande à l'écran (zoomer dessus) ; case « Doigts ».
  Vue de face, une main qui pend se présente par la tranche et ses doigts se superposent :
  tourner la vue les sépare. Dans les articulations, chaque main a un curseur par doigt (plié,
  en %) et l'écartement des doigts ; la pose prédéfinie « pointing » tend l'index et plie les
  autres doigts. Le mannequin 3D a maintenant des mains (paume et phalanges).
- **poignet** : une poignée blanche sur la paume (aux jointures) plie le poignet pour que la
  main pointe vers le point — vers la paume ou le dos de la main (-70 à 80°), vers le pouce ou
  l'auriculaire (-25 à 35°) ; les doigts gardent leur flexion. Elle apparaît quand la main est
  assez grande à l'écran (sinon elle se confondrait avec celle du poignet). Les deux angles
  sont aussi des curseurs de la main (« Poignet plié », « Poignet vers le pouce »).
- **orteils** : chaque pied a maintenant un talon, une plante et des orteils. Le pied reste à
  plat sur le sol quoi que fasse la jambe, et pointe là où la jambe pointe (un genou tourné vers
  l'extérieur tourne le pied). Une poignée orange au bout des orteils les relève ou les plie ;
  elle apparaît quand le pied est assez grand à l'écran (sinon elle se confondrait avec celle
  de la cheville), et reste disponible pendant la marche. Les orteils ne s'enfoncent pas dans
  le sol : sur un pied à plat, les tirer vers le bas ne change rien. Les curseurs du pied
  règlent aussi l'inclinaison du pied (« Pied incliné (pointe vers le bas) », de -30 à 60°) :
  c'est désormais le point le plus bas des semelles qui touche le sol, donc sur la pointe des
  pieds (pied incliné, orteils relevés) tout le corps monte d'environ 8 cm. Le mannequin, la
  carte de profondeur et le squelette OpenPose du contrôle montrent les pieds.

La poignée modifie la pose en cours de réglage (début ou fin) : la vue se place au début ou à
la fin du plan pendant le geste. Les angles restent dans les limites du corps. Les jambes d'un
personnage qui se déplace suivent la marche : ses pieds, ses genoux, ses hanches et son
bassin n'ont pas de poignée.
Les poses enregistrées avant l'ajout de la rotation des membres (trois angles), de l'inclinaison
sur le côté ou de la bascule du bassin restent valables : ces angles valent alors 0 ; sans
réglage des mains, les doigts sont légèrement pliés (15 %) et le poignet est droit ; sans
réglage des pieds, ils sont à plat, orteils droits.

## Contrôle par la profondeur ou la pose (plans mis en scène en 3D)

Dans les deux exports (Film et Workflow), chaque plan mis en scène sur un plateau 3D reçoit
une **vidéo de profondeur** qui guide la génération par Fun ControlNet Union : une image de
profondeur par image générée, le long du mouvement de caméra du plan (caméra de début →
caméra de fin), avec une échelle de profondeur fixe pour éviter le scintillement. Dans le
film, les images reprises du segment précédent tiennent la fin du plan précédent.

Comme le blocage n'est qu'une indication (un cube pour un mur, une capsule pour un
personnage), le niveau se règle :

| Niveau | Force | Appliqué sur | Flou |
|---|---|---|---|
| indicatif (défaut) | 0,35 | 35 % des pas | fort : disposition et ordre de profondeur seulement |
| guidé | 0,6 | 60 % des pas | moyen |
| strict | 1,0 | tous les pas | aucun : formes suivies de près |
| personnalisé / désactivé | au choix | au choix | au choix |

Les plans en image ou en dessin 2D n'ont pas de profondeur.

**Source du contrôle** (réglage « Contrôle ») :

- **pose des personnages** : les squelettes OpenPose (18 points, couleurs standard) des
  personnages, projetés par la caméra du plan à chaque image, avec leurs poses, leur marche
  et leurs déplacements. Vus de dos, le nez et les yeux sont omis, comme dans OpenPose. Les
  **mains** (modèle de main OpenPose : 21 points, os aux couleurs de l'arc-en-ciel) sont
  ajoutées quand elles sont assez grandes à l'écran ; case « Mains dans la pose », cochée par
  défaut (option `poseHands`). Les **pieds** suivent la convention OpenPose BODY_25 : talon,
  gros orteil et petit orteil reliés à la cheville, bleu pour le pied gauche, cyan pour le
  droit ; case « Pieds dans la pose », cochée par défaut (option `poseFeet`). Le squelette de
  base reste celui à 18 points ;
- **profondeur du décor** : comme ci-dessus ;
- **auto** (par défaut) : la pose quand un personnage est dans le cadre, sinon la profondeur ;
- **pose sur la profondeur** : les squelettes dessinés sur la profondeur floutée, en une
  seule vidéo (expérimental : Fun ControlNet Union n'a pas été entraîné sur ce mélange).

Le flou des niveaux de fidélité ne s'applique qu'à la profondeur ; la force et la part des
pas s'appliquent aux deux.

## Images : générer les références dans l'application (onglet Images)

H3 suit d'autant mieux un personnage qu'il en reçoit de vraies images. L'onglet **Images**
les fabrique dans l'application, à partir de tes images de départ ou d'un texte :

- **Personnage** : choisis un personnage de la bibliothèque. Ses images (les premières, autant
  que le modèle en accepte) servent de références et l'application génère les vues cochées :
  face, trois-quarts, profil, dos, portraits... Sans image, les vues partent de sa description.
- **Lieu** : même principe pour un décor (vue large, contre-champ, plongée, détail), vide ou
  avec un personnage dedans (« Personnage dans le lieu »).
- **Plan** : l'image d'un plan. La mise en scène 3D donne le cadrage, le personnage et le lieu
  du plan donnent l'apparence, le texte du plan donne l'action. « Cadrage venant de la mise en
  scène 3D » choisit comment : **guide de structure** (la profondeur ou la pose du plateau passe
  par le ControlNet du modèle ; le modèle ne voit jamais de mannequin gris), **image de mise en
  scène** (le rendu en mannequins est envoyé comme image, à remplacer), les deux, ou aucun.
  En automatique, le guide de structure est pris dès que le ControlNet est installé. Le
  personnage est envoyé avec plusieurs images (« Images par personnage » : sa première image,
  puis ses vues générées, corps entier d'abord). Quand le plateau contient des mannequins sans
  référence (une foule), la liste « mannequins sans référence sont » dit au modèle que ce sont
  d'autres exemplaires d'un personnage.
- **Prompt libre** : un texte, avec ou sans images de référence.

Chaque vue est une ligne modifiable (case, format, texte) ; « Ajouter une vue » en crée
d'autres. Les phrases envoyées au modèle sont dans « Phrases », et « Ce qui sera demandé »
montre le prompt exact de chaque image avant de lancer.

**Générer** lance le calcul ; les images arrivent à droite. **Garder** copie l'image dans le
projet avec sa recette (prompt, références, graine, modèle) : elle s'ajoute aux images du
personnage ou du lieu, ou devient la première image du plan — c'est elle que l'export H3
envoie alors à la place du rendu en mannequins. **Reprendre la graine** réutilise la graine
d'une image pour les suivantes. Les images non gardées restent dans le dossier du travail.

### LoRA

Dans « Génération », la section **LoRA** liste les fichiers `.safetensors` du dossier
`data/models/comfyui/loras/` (« Ajouter des fichiers LoRA... » les y copie, « Ouvrir le dossier
des LoRA » l'ouvre). Coche ceux à appliquer et règle leur force (de -2 à 2) ; ils sont appliqués
au modèle dans l'ordre de la liste, avant le LoRA « peu de pas » du modèle. Un LoRA est fait pour
une famille de modèle (Qwen-Image 2.1, Qwen-Image-Edit 2511 ou Qwen-Image 2512) : un LoRA d'une
autre famille n'a pas d'effet utile. Ses mots déclencheurs se mettent dans le prompt ou dans
« Ajouté à chaque image ». Les LoRA utilisés sont notés dans la recette de chaque image gardée
et dans les workflows ComfyUI exportés.

### Moteur et modèles (Installation, en haut à droite de l'onglet)

Rien n'est installé au départ :

1. **Installer ou réparer le moteur** : crée `runtime/engines/image` (Python privé, PyTorch
   CUDA 13) et télécharge ComfyUI (version fixée) dans `runtime/sources/ComfyUI`. Environ 8 Go.
2. **Télécharger** un modèle (reprise possible, taille et SHA-256 vérifiés) :

| Modèle | Usage | Taille | Licence |
|---|---|---|---|
| Qwen-Image 2.1 (int8) — par défaut | texte seul et jusqu'à 10 références | 17,3 Go | Qwen Research (non commerciale) |
| Qwen-Image 2.1 ControlNet (int8) | guide de structure des plans (profondeur, pose) | 3,8 Go | Qwen Research (non commerciale) |
| Qwen-Image-Edit 2511 (int8) | 1 à 3 références, 4 pas avec son LoRA | 31,0 Go | Apache-2.0 |
| Qwen-Image 2512 (fp8) | texte seul, 4 pas avec son LoRA | 30,9 Go | Apache-2.0 |

   Les fichiers vont dans `data/models/comfyui/` ; l'encodeur de texte et le VAE communs à 2511
   et 2512 ne sont téléchargés qu'une fois.

Le moteur est un ComfyUI privé que l'application lance elle-même, en arrière-plan, sur
`127.0.0.1` seulement. Le modèle **reste en mémoire** entre deux générations (réglage « Garder
le modèle en mémoire », 30 minutes par défaut, 0 = jusqu'à la fermeture) ; **Décharger** le
libère tout de suite. Annuler une génération arrête l'image en cours sans décharger le modèle.

**Autre ComfyUI** : en donnant une adresse (le tunnel de ton ComfyUI Colab par exemple), les
mêmes images sont calculées là-bas au lieu de cet ordinateur ; les modèles doivent alors être
dans ses dossiers `models/`.

### Les mêmes images dans ComfyUI

**Workflows ComfyUI...** écrit, pour ce qui est choisi à l'écran, un dossier
`exports/comfyui_images/` avec :

- `<nom>.json` : le workflow à glisser sur la page ComfyUI (tous les plans/vues, chargeurs communs) ;
- `<nom>_api.json` : le même graphe au format API ;
- `cytools_images/` : les images de référence, à copier dans `ComfyUI/input/`.

C'est exactement le graphe que l'application calcule ; la note du workflow liste les fichiers
de modèle attendus.

## CLI et IA (MCP)

```
runtime\python\Scripts\python.exe app\tool.py list-operations
runtime\python\Scripts\python.exe app\tool.py invoke create_storyboard --params "{\"title\":\"Mon film\"}"
runtime\python\Scripts\python.exe app\tool.py mcp
```

## Licences

Le dossier `LICENCES` (textes en anglais) accompagne chaque copie de l'application :
`CyToolsCore-MIT.txt` (le SDK CyToolsCore 0.10.1, sous licence MIT) et `SOURCES.txt` (licence et
source de chaque composant inclus ou téléchargé : Python et ses paquets, FFmpeg, moteur d'images,
modèles). Le code propre de l'application reste sous GPL-3.0 (`LICENSE`).

## Limites (30/09/2026)

- Images (onglet Images) : le moteur réel a été installé et démarré sur cette machine (ComfyUI
  0.37.0, PyTorch 2.14.0+cu130, RTX 3090, noyaux int8 trouvés), les graphes des trois familles
  de modèles sont acceptés par le vrai ComfyUI et identiques à ce que sa page produit en
  chargeant les workflows exportés, le téléchargement avec reprise a été exécuté. Première
  génération réelle le 30/09/2026 avec Qwen-Image 2.1 : six vues d'un personnage à partir de
  trois références, 42,6 s par image (25 pas, 1 MP, RTX 3090 déjà occupée par autre chose) ;
  la vue de dos est sortie de face (texte de la vue renforcé depuis, pas encore revérifié).
  Plans générés avec le rendu de mise en scène envoyé comme image : résultat inégal (mannequins
  et blocs gris parfois conservés, proportions fausses avec une seule image du personnage).
  D'où le guide de structure par ControlNet (ComfyUI 0.38.0) : graphes acceptés par un vrai
  ComfyUI 0.38.0 et identiques à ceux de sa page, images de profondeur et de pose rendues,
  ControlNet téléchargé — **aucune image réelle n'a encore été générée avec ce guide**. Qwen-Image-Edit 2511 et Qwen-Image 2512
  n'ont pas été téléchargés. Le calcul sur un autre ComfyUI n'a été essayé que sur un ComfyUI
  local sans modèle.

- Film MiniMax H3 : vérifié par le vrai planificateur de Timeline Director et le vrai ComfyUI
  (graphes acceptés, vidéos et sons décodés segment par segment), mais aucun film réel n'a
  encore été généré (pas de GPU H3 ici).
- Les vidéos de référence ne passent que par le nœud CyTools H3 Film Plan : le workflow
  Timeline Director seul est exporté sans elles (il les appliquerait à tous les segments).
- Maillages .fbx et .dae non lus (trimesh ne les ouvre pas sans modules en plus) : les
  convertir en .glb. Un maillage illisible s'affiche comme un cube.
- Contrôle de profondeur : les vidéos sont vérifiées (longueur, taille, décodage par Timeline
  Director, graphes acceptés par le vrai ComfyUI), mais aucune génération réelle ne l'a encore
  utilisé ; son effet réel sur H3 (et avec le transformer turbo fusionné) reste à voir.
- Les gestes à la souris (orbite, gizmo, dessin) ont été vérifiés par captures et par les
  calculs sous-jacents, pas encore par une personne à la souris.
- Glisser des fichiers depuis l'Explorateur vers la fenêtre n'est pas géré (boutons et collage).
- Le Python privé dépend du Python 3.11 installé sur cette machine ; lanceur Linux non exécuté.
- Mises à jour GitHub testées avec des fixtures seulement (aucun dépôt de release n'existe).


## Documentation locale

Dans l’application, ouvrir **Options → Ouvrir le manuel local (F1)** ou appuyer sur **F1**. Le lecteur hors ligne complet est livré dans `app/Documentation/Documentation.html`. [Régénérer le manuel](app/.CyDocBuild/README.md).

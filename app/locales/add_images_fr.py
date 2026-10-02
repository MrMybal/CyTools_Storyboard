"""Add the French translations of the Images tab (picture generation) to ui.json.

    runtime/python/Scripts/python.exe app/locales/add_images_fr.py
"""
import json
from pathlib import Path

FR = {
    'Images': 'Images', 'Character': 'Personnage', 'Place': 'Lieu', 'Shot': 'Plan', 'Free prompt': 'Prompt libre',
    'Generate the pictures MiniMax H3 needs, from your reference pictures or from a text. The pictures you keep go into '
    'the project: a character or a place gets new reference pictures, a shot gets its first image.':
        "Génère les images dont MiniMax H3 a besoin, à partir de tes images de référence ou d'un texte. Les images que "
        "tu gardes entrent dans le projet : un personnage ou un lieu reçoit de nouvelles images de référence, un plan "
        "reçoit sa première image.",
    'These pictures are the references: the first ones of the item, as many as the model takes.':
        "Ces images servent de références : les premières de l'élément, autant que le modèle en accepte.",
    'No picture yet: the views are generated from the description alone.':
        "Pas encore d'image : les vues sont générées à partir de la description seule.",
    'Description': 'Description', 'Add reference pictures...': 'Ajouter des images de référence...',
    'Reference pictures': 'Images de référence', 'nobody (empty place)': 'personne (lieu vide)',
    'Character in the place': 'Personnage dans le lieu',
    'The staging render gives the framing, the characters and the place of the shot give the look. The kept picture '
    'becomes the first image of the shot.':
        "Le rendu de mise en scène donne le cadrage, les personnages et le lieu du plan donnent l'apparence. L'image "
        "gardée devient la première image du plan.",
    'Prompt': 'Prompt', 'Reference pictures (none: from the text alone)': 'Images de référence (aucune : à partir du texte seul)',
    'Add pictures...': 'Ajouter des images...', 'Added to every picture': 'Ajouté à chaque image',
    'Generation': 'Génération', 'Pictures per view': 'Images par vue', 'Size': 'Taille', 'Random seed': 'Graine aléatoire',
    'Seed': 'Graine', 'Fast mode (few steps)': 'Mode rapide (peu de pas)', 'Steps (0 = auto)': 'Pas (0 = auto)',
    'Guidance (0 = auto)': 'Guidage (0 = auto)', 'Project style in the prompt': 'Style du projet dans le prompt',
    'Negative prompt': 'Prompt négatif',
    'Keep the model loaded (minutes, 0 = until closed)': 'Garder le modèle en mémoire (minutes, 0 = jusqu\'à la fermeture)',
    'Sentences': 'Phrases', 'Default sentences##img': 'Phrases par défaut##img',
    'Choose what to generate.': 'Choisis ce qu\'il faut générer.', 'Generate': 'Générer',
    'ComfyUI workflows...': 'Workflows ComfyUI...', 'ComfyUI workflows': 'Workflows ComfyUI', 'picture(s)': 'image(s)',
    'Cancel##gen': 'Annuler##gen', 'What will be asked': 'Ce qui sera demandé', 'reference(s)': 'référence(s)',
    'The library has none yet: add one in the Storyboard tab (References), with a description.':
        "La bibliothèque n'en contient pas encore : ajoutes-en un dans l'onglet Storyboard (Références), avec une description.",
    'Views': 'Vues', 'Add a view': 'Ajouter une vue', 'Default views': 'Vues par défaut', 'Format': 'Format',
    'project': 'projet', 'Model for pictures from references': 'Modèle pour les images à partir de références',
    'Model for pictures from a text': "Modèle pour les images à partir d'un texte",
    'automatic (installed default)': 'automatique (modèle installé par défaut)', 'not installed': 'non installé',
    'Model in memory': 'Modèle en mémoire', 'Unload': 'Décharger',
    'No model in memory (loaded at the first picture).': 'Aucun modèle en mémoire (chargé à la première image).',
    'picture': 'image', 'steps': 'pas',
    'The engine did not find its CUDA kernels for int8 models: pictures are slower. Repair the engine (Installation).':
        "Le moteur n'a pas trouvé ses noyaux CUDA pour les modèles int8 : les images sont plus lentes. Répare le moteur (Installation).",
    'Installation (engine and models)': 'Installation (moteur et modèles)', 'Image engine': "Moteur d'images",
    'Image engine (private ComfyUI, PyTorch CUDA 13)': "Moteur d'images (ComfyUI privé, PyTorch CUDA 13)",
    'A private Python environment with PyTorch under runtime/engines/image, created at its final path and checked by '
    'import before use.':
        "Un environnement Python privé avec PyTorch sous runtime/engines/image, créé à son emplacement définitif et "
        "vérifié par import avant usage.",
    'Install or repair the engine (GPU)': 'Installer ou réparer le moteur (GPU)', 'Cancel##eng': 'Annuler##eng',
    'Where the pictures are rendered': 'Où les images sont calculées',
    'Other ComfyUI (address, empty = this computer)': 'Autre ComfyUI (adresse, vide = cet ordinateur)',
    'Empty: the engine of this application, on this computer. An address (for example the tunnel of a Colab ComfyUI): '
    'the same pictures are rendered there; its models must be in its own folders.':
        "Vide : le moteur de cette application, sur cet ordinateur. Une adresse (par exemple le tunnel d'un ComfyUI "
        "Colab) : les mêmes images y sont calculées ; ses modèles doivent être dans ses propres dossiers.",
    'Models': 'Modèles', 'present': 'présent', 'Licence': 'Licence', 'Repair': 'Réparer', 'Resume': 'Reprendre',
    'Download': 'Télécharger', 'Verify files': 'Vérifier les fichiers', 'Remove': 'Retirer', 'Official page': 'Page officielle',
    'NotInstalled': 'Non installé', 'Installed': 'Installé', 'Partial': 'Partiel', 'Downloading': 'Téléchargement',
    'Verifying': 'Vérification', 'Interrupted': 'Interrompu', 'Failed': 'Échec', 'Cancelled': 'Annulé',
    'One model for pictures from a text and from up to 10 reference pictures.':
        "Un seul modèle pour les images à partir d'un texte et à partir de 10 images de référence au plus.",
    'Pictures from 1 to 3 reference pictures; 4 steps with its Lightning LoRA.':
        'Images à partir de 1 à 3 images de référence ; 4 pas avec son LoRA Lightning.',
    'Pictures from a text only; 4 steps with its Lightning LoRA.':
        "Images à partir d'un texte seulement ; 4 pas avec son LoRA Lightning.",
    'The generated pictures appear here. Keep the ones you like: they are copied into the project with their recipe '
    '(prompt, references, seed), the others stay in the job folder.':
        "Les images générées apparaissent ici. Garde celles qui te plaisent : elles sont copiées dans le projet avec "
        "leur recette (prompt, références, graine), les autres restent dans le dossier du travail.",
    'Keep all': 'Tout garder', 'Clear the list': 'Vider la liste', 'Thumbnails': 'Vignettes',
    'Kept in the project': 'Gardée dans le projet', 'Keep': 'Garder', 'Discard': 'Écarter', 'Open': 'Ouvrir',
    'Again': 'Reprendre la graine', 'Use this seed for the next pictures': 'Utiliser cette graine pour les prochaines images',
    'Pictures': 'Images',
    'Character from its pictures ({pictures}, {description}, {view}, {name})': 'Personnage à partir de ses images ({pictures}, {description}, {view}, {name})',
    'Character from its description ({name}, {description}, {view})': 'Personnage à partir de sa description ({name}, {description}, {view})',
    'Place from its pictures ({pictures}, {description}, {view}, {name})': 'Lieu à partir de ses images ({pictures}, {description}, {view}, {name})',
    'Place from its description ({name}, {description}, {view})': 'Lieu à partir de sa description ({name}, {description}, {view})',
    'Character in a place ({character}, {place}, {description}, {view})': 'Personnage dans un lieu ({character}, {place}, {description}, {view})',
    'Shot ({framing}, {people}, {place}, {text})': 'Plan ({framing}, {people}, {place}, {text})',
    'Shot: layout picture ({picture})': 'Plan : image de mise en scène ({picture})',
    'Shot: character picture ({picture}, {name}, {description})': 'Plan : image du personnage ({picture}, {name}, {description})',
    'Shot: place picture ({picture}, {name}, {description})': 'Plan : image du lieu ({picture}, {name}, {description})',
    'main (first image, else layout render)': 'principale (première image, sinon rendu de mise en scène)',
    'Pictures per character': 'Images par personnage',
    'picture(s). The first ones are the references sent to the model': 'image(s). Les premières sont les références envoyées au modèle',
    '"First" puts a picture at the head of the list; kept pictures are added at the end.':
        '« En premier » met une image en tête de liste ; les images gardées sont ajoutées à la fin.',
    'reference': 'référence', 'First': 'En premier',
    'Take this picture out of the item (the file stays in the project)': "Retirer cette image de l'élément (le fichier reste dans le projet)",
    'Added to the pictures of': 'Ajoutée aux images de', 'Set as the first image of the shot': 'Définie comme première image du plan',
    'file not found': 'fichier introuvable', 'Forget': 'Oublier', 'Add LoRA files...': 'Ajouter des fichiers LoRA...',
    'LoRA files': 'Fichiers LoRA', 'Open the LoRA folder': 'Ouvrir le dossier des LoRA',
    'No LoRA yet. A LoRA is made for one model (Qwen-Image 2.1, Qwen-Image-Edit 2511 or Qwen-Image 2512); its trigger '
    'words go in the prompt or in "Added to every picture".':
        "Pas encore de LoRA. Un LoRA est fait pour un modèle (Qwen-Image 2.1, Qwen-Image-Edit 2511 ou Qwen-Image 2512) ; "
        "ses mots déclencheurs vont dans le prompt ou dans « Ajouté à chaque image ».",
    'Save as...': 'Enregistrer sous...', 'Title of the copy': 'Titre de la copie', 'Save the copy': 'Enregistrer la copie',
    'The project is saved by itself after every change. This makes a copy under another title and opens it.':
        "Le projet s'enregistre tout seul après chaque modification. Ceci en fait une copie sous un autre titre et l'ouvre.",
    'saving...': 'enregistrement...', 'saved': 'enregistré',
    'Shot: the other figures are a character, structure guide ({name}, {picture}, {count})':
        'Plan : les autres silhouettes sont un personnage, guide de structure ({name}, {picture}, {count})',
    'Framing from the 3D staging': 'Cadrage venant de la mise en scène 3D',
    'automatic (structure guide when its model is installed)': 'automatique (guide de structure si son modèle est installé)',
    'structure guide (depth or pose, ControlNet)': 'guide de structure (profondeur ou pose, ControlNet)',
    'staging picture': 'image de mise en scène', 'both': 'les deux', 'none (text and references only)': 'aucun (texte et références seulement)',
    'The ControlNet of the model is not installed (Installation): the staging picture is used instead.':
        "Le ControlNet du modèle n'est pas installé (Installation) : l'image de mise en scène est utilisée à la place.",
    'The ControlNet of the model is not installed (Installation).': "Le ControlNet du modèle n'est pas installé (Installation).",
    'Guide': 'Guide', 'Strength##imgctl': 'Force##imgctl', 'Until (share of the steps)##imgctl': "Jusqu'à (part des pas)##imgctl",
    'Structure guide for Qwen-Image 2.1: a shot follows the depth or the pose of its 3D staging.':
        'Guide de structure pour Qwen-Image 2.1 : un plan suit la profondeur ou la pose de sa mise en scène 3D.',
    'what the text describes': 'ce que décrit le texte',
    'mannequin(s) without a reference are': 'mannequin(s) sans référence sont',
    'Shot: the other mannequins are a character ({name}, {picture}, {count})': 'Plan : les autres mannequins sont un personnage ({name}, {picture}, {count})',
    'Shot: the other mannequins have no reference ({count})': 'Plan : les autres mannequins sont sans référence ({count})',
    'Shot: character picture ({picture}, {name}, {description})': 'Plan : images du personnage ({picture}, {name}, {description})',
    'Being downloaded by another client': 'Téléchargement en cours par un autre client',
    'Character, other pictures ({n}, {name}, {description})': 'Personnage, autres images ({n}, {name}, {description})',
}


def main():
    path = Path(__file__).with_name('ui.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    added = 0
    for english, french in FR.items():
        if english not in data:      # words other screens already translate keep their translation
            data[english] = {'en': english, 'fr': french}
            added += 1
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{added} entries added, {len(FR) - added} already there')


if __name__ == '__main__':
    main()

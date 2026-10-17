"""Add the French translations of the CyUI interface (toolbar, library, inspector, Images tab) to ui.json.

    runtime/python/Scripts/python.exe app/locales/add_cyui_fr.py
"""
import json
from pathlib import Path

FR = {
    'New storyboard': 'Nouveau storyboard', 'Storyboard created': 'Storyboard créé',
    'Copy saved and opened': 'Copie enregistrée et ouverte', 'Undo (Ctrl+Z)': 'Annuler (Ctrl+Z)',
    'Redo (Ctrl+Y)': 'Rétablir (Ctrl+Y)', 'Add a panel after the selected one': 'Ajouter un plan après celui sélectionné',
    'Sequence': 'Séquence', 'Add a sequence at the end': 'Ajouter une séquence à la fin',
    'Play the animatic': "Lire l'animatic",
    'Contact sheet, script, animatic, MiniMax H3 film and workflow': 'Planche contact, script, animatic, film et workflow MiniMax H3',
    'DOCUMENTS': 'DOCUMENTS', 'Open the project folder': 'Ouvrir le dossier du projet', 'cards': 'cartes',
    'Open the export': "Ouvrir l'export", 'REFERENCES': 'RÉFÉRENCES', 'New reference': 'Nouvelle référence',
    'Add this reference to the library': 'Ajouter cette référence à la bibliothèque',
    'No reference yet': 'Pas encore de référence', 'Add characters, places, objects...': 'Ajoute des personnages, des lieux, des objets...',
    'Drag it onto a card to use it in that panel': "Glisse-la sur une carte pour l'utiliser dans ce plan",
    'file(s)': 'fichier(s)', 'Nothing matches the search.': 'Rien ne correspond à la recherche.',
    'Name': 'Nom', 'Kind': 'Type', 'comma separated': 'séparés par des virgules', 'Files': 'Fichiers',
    'Take this file out of the reference': 'Retirer ce fichier de la référence',
    'Click to edit, drag to move, right click for more. Drop a reference on it to use it.':
        "Clic pour modifier, glisser pour déplacer, clic droit pour plus. Dépose une référence dessus pour l'utiliser.",
    'Add a panel to this sequence': 'Ajouter un plan à cette séquence', 'Delete this sequence': 'Supprimer cette séquence',
    'Delete this sequence?': 'Supprimer cette séquence ?', 'TIMELINE': 'FRISE',
    'Seconds on screen; the presets set it at once.': "Secondes à l'écran ; les préréglages la fixent d'un clic.",
    'Length': 'Durée', 'Notes': 'Notes',
    'No image yet: add a sketch, a first frame, a keyframe or a reference.':
        "Pas encore d'image : ajoute un croquis, une première image, une image clé ou une référence.",
    'Caption': 'Légende', 'Move up': 'Monter', 'Open the file': 'Ouvrir le fichier', 'Remove from this panel': 'Retirer de ce plan',
    'what we hear': "ce qu'on entend", 'off screen': 'hors champ', 'Remove this line': 'Retirer cette réplique',
    'What is said': 'Ce qui est dit',
    'Added to the prompts of the exports and of the generated pictures.':
        'Ajouté aux prompts des exports et des images générées.',
    'No problem found.': 'Aucun problème trouvé.', 'Pause': 'Pause', 'No storyboard open': 'Aucun storyboard ouvert',
    'Create one (+) or open one from the toolbar.': "Crée-en un (+) ou ouvre-en un depuis la barre d'outils.",
    'Generate the pictures MiniMax H3 needs, from your reference pictures or from a text. The pictures you keep go into the project.':
        "Génère les images dont MiniMax H3 a besoin, à partir de tes images de référence ou d'un texte. "
        'Les images que tu gardes entrent dans le projet.',
    'e.g. wet armour, night': 'ex. armure mouillée, nuit',
    'The kept picture becomes the first image of the shot.': "L'image gardée devient la première image du plan.",
    'Structure guide: the depth or the pose of the staging guides the picture, the model never sees a mannequin. '
    'Staging picture: the mannequin render is sent as a picture.':
        "Guide de structure : la profondeur ou la pose de la mise en scène guide l'image, le modèle ne voit jamais de "
        'mannequin. Image de mise en scène : le rendu en mannequins est envoyé comme image.',
    'Uses the few-step LoRA of the model when it has one.': 'Utilise le LoRA « peu de pas » du modèle quand il en a un.',
    'The same graph as a ComfyUI workflow, with its reference pictures':
        'Le même graphe en workflow ComfyUI, avec ses images de référence',
    'the model stays loaded': 'le modèle reste chargé', 'make it a reference': 'en faire une référence',
    'Give the memory of the model back now': 'Libérer tout de suite la mémoire du modèle',
    'Install the engine and a model below before generating.': 'Installe le moteur et un modèle ci-dessous avant de générer.',
    'No picture yet': "Pas encore d'image", 'Choose what to generate on the left, then Generate.':
        "Choisis à gauche ce qu'il faut générer, puis Générer.",
    'RESULTS': 'RÉSULTATS', 'Segments of the film': 'Segments du film', 'Shots of the workflow': 'Plans du workflow',
    'No panel selected': 'Aucun plan sélectionné', 'Previous panel': 'Plan précédent', 'Next panel': 'Plan suivant',
    'New stage': 'Nouveau plateau', 'Compact': 'Compacte', 'Comfortable': 'Confortable', 'Density': 'Densité',
}


def main():
    path = Path(__file__).with_name('ui.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    added = 0
    for english, french in FR.items():
        if english not in data:
            data[english] = {'en': english, 'fr': french}
            added += 1
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{added} entries added, {len(FR) - added} already there')


if __name__ == '__main__':
    main()

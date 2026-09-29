"""Add the French translations of CyTools_Storyboard's interface strings to ui.json.

    runtime/python/Scripts/python.exe app/locales/add_storyboard_fr.py
"""
import json
from pathlib import Path

FR = {
    '(free name)': '(nom libre)', 'A verified release is activated at the next start; data/ is never replaced.':
    "Une release vérifiée est activée au prochain démarrage ; data/ n'est jamais remplacé.",
    'Action': 'Action', 'Add': 'Ajouter', 'Add a line': 'Ajouter une réplique', 'Add a panel after': 'Ajouter un plan après',
    'Add characters, locations or images in the left column, then tick them here (or drag them onto a card).':
    'Ajoutez des personnages, lieux ou images dans la colonne de gauche, puis cochez-les ici (ou glissez-les sur une carte).',
    'Add files...': 'Ajouter des fichiers...', 'Add images...': 'Ajouter des images...', 'Add panel': 'Ajouter un plan',
    'Add panel here': 'Ajouter un plan ici', 'Add sequence': 'Ajouter une séquence', 'Animatic': 'Animatic',
    'Animatic (MP4)': 'Animatic (MP4)', 'Aspect': 'Format', 'Audio': 'Audio', 'Card size': 'Taille des cartes',
    'Characters': 'Personnages', 'Contact sheet (PNG)': 'Planche contact (PNG)', 'Create': 'Créer',
    'Create a storyboard (New) or open one to start.': 'Créez un storyboard (Nouveau) ou ouvrez-en un pour commencer.',
    'Default duration': 'Durée par défaut', 'Delete': 'Supprimer', 'Delete reference': 'Supprimer la référence',
    'Delete sequence': 'Supprimer la séquence', 'Delete this sequence and its panels?': 'Supprimer cette séquence et ses plans ?',
    'Dialogue': 'Dialogue', 'Dialogue language': 'Langue des dialogues', 'Dismiss': 'Fermer',
    'Download and verify': 'Télécharger et vérifier',
    'Drag the right edge of a panel to change its duration.': "Tirez le bord droit d'un plan pour changer sa durée.",
    'Duplicate': 'Dupliquer', 'Duration (s)': 'Durée (s)', 'Empty: add a panel or drop one on the title.':
    'Vide : ajoutez un plan ou déposez-en un sur le titre.', 'Export': 'Exporter', 'Exported: ': 'Exporté : ',
    'Free text': 'Texte libre', 'GitHub repository (owner/name)': 'Dépôt GitHub (propriétaire/nom)', 'Images': 'Images',
    'Images for this panel': 'Images de ce plan', 'Installed version': 'Version installée', 'Keep': 'Garder',
    'Latest release': 'Dernière release', 'Lens': 'Objectif', 'Locations': 'Lieux', 'Longest generation': 'Génération la plus longue',
    'Music': 'Musique', 'New': 'Nouveau', 'No colour': 'Sans couleur',
    'No repository is configured for this Tool yet: enter the one where its releases are published (see app/UPDATES.md).':
    'Aucun dépôt configuré pour ce Tool : saisissez celui où ses releases sont publiées (voir app/UPDATES.md).',
    'Nothing yet.': 'Rien pour le moment.', 'Objects': 'Objets', 'Open': 'Ouvrir', 'Open a storyboard': 'Ouvrir un storyboard',
    'Open...': 'Ouvrir...', 'Panel': 'Plan', 'Paste image': "Coller l'image", 'Play animatic': "Lire l'animatic",
    'Project folder': 'Dossier du projet', 'Prompt': 'Prompt', 'Recent': 'Récents', 'Redo': 'Rétablir',
    'Reference files': 'Fichiers de référence', 'References': 'Références', 'Restore the previous version': 'Restaurer la version précédente',
    'Roles: sketch (what the shot looks like), first / last frame, keyframe at a time, reference.':
    "Rôles : croquis (à quoi ressemble le plan), première / dernière image, image clé à un instant, référence.",
    'Script (HTML)': 'Script (HTML)', 'Script (Markdown)': 'Script (Markdown)', 'Select a panel to edit it.':
    'Sélectionnez un plan pour le modifier.', 'Sound': 'Son', 'Storyboard': 'Storyboard',
    'Storyboard settings': 'Réglages du storyboard', 'Style': 'Style', 'Styles': 'Styles', 'Tags': 'Tags',
    'The clipboard holds no image.': "Le presse-papiers ne contient pas d'image.",
    'The project was changed outside the window and has been reloaded.': 'Le projet a été modifié hors de la fenêtre et a été rechargé.',
    'Timeline zoom': 'Zoom de la frise', 'Title': 'Titre', 'Transition and notes': 'Transition et notes',
    'Transition to next': 'Transition vers le suivant', 'Undo': 'Annuler', 'Up': 'Monter', 'Video': 'Vidéo',
    'Working...': 'En cours...', 'errors': 'erreurs', 'no image': "pas d'image", 'off': 'hors champ', 'panels': 'plans',
    'remarks': 'remarques', 'dialogue': 'dialogue', 'up to date': 'à jour', 'update available': 'mise à jour disponible',
    'Scene': 'Scène', 'Status': 'Statut', 'Shot size': 'Valeur de plan', 'Angle': 'Angle', 'Camera': 'Caméra',
    'Amplitude': 'Amplitude', 'Speed': 'Vitesse', 'Remove': 'Retirer', 'Updates': 'Mises à jour', 'All': 'Tout',
    # model values
    'character': 'personnage', 'location': 'lieu', 'object': 'objet', 'style': 'style', 'image': 'image', 'audio': 'audio',
    'video': 'vidéo', 'sketch': 'croquis', 'first': 'première image', 'last': 'dernière image', 'keyframe': 'image clé',
    'reference': 'référence', 'idea': 'idée', 'draft': 'brouillon', 'ready': 'prêt', 'generated': 'généré',
    'extreme wide shot': 'très grand plan d\'ensemble', 'wide shot': 'plan large', 'full shot': 'plan en pied',
    'medium wide shot': 'plan américain', 'medium shot': 'plan moyen', 'medium close-up': 'plan rapproché',
    'close-up': 'gros plan', 'extreme close-up': 'très gros plan', 'insert shot': 'insert',
    'over-the-shoulder shot': 'plan par-dessus l\'épaule', 'eye level': 'hauteur des yeux', 'high angle': 'plongée',
    'low angle': 'contre-plongée', "bird's-eye view": 'vue plongeante zénithale', "worm's-eye view": 'contre-plongée extrême',
    'dutch angle': 'plan débullé', 'POV': 'vue subjective', 'static shot': 'plan fixe', 'push in': 'travelling avant',
    'pull out': 'travelling arrière', 'zoom in': 'zoom avant', 'zoom out': 'zoom arrière', 'pan left': 'panoramique gauche',
    'pan right': 'panoramique droite', 'truck left': 'travelling latéral gauche', 'truck right': 'travelling latéral droit',
    'tilt up': 'panoramique vertical haut', 'tilt down': 'panoramique vertical bas', 'pedestal up': 'élévation',
    'pedestal down': 'descente', 'arc shot': 'travelling circulaire', 'tracking shot': 'plan de suivi', 'handheld': 'caméra à l\'épaule',
    'shake slightly': 'léger tremblement', 'shake strongly': 'fort tremblement', 'roll clockwise': 'roulis horaire',
    'roll counterclockwise': 'roulis antihoraire', 'small': 'petite', 'large': 'grande', 'slow': 'lente', 'fast': 'rapide',
    'cut': 'coupe', 'crossfade': 'fondu enchaîné', 'fade to black': 'fondu au noir', 'fade from black': 'ouverture au noir',
}


def main():
    path = Path(__file__).with_name('ui.json')
    data = json.loads(path.read_text(encoding='utf-8'))
    for english, french in FR.items():
        data[english] = {'en': english, 'fr': french}
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'{len(FR)} entries written')


if __name__ == '__main__':
    main()

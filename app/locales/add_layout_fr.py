"""Add the French translations of the Layout tab (2D drawing, 3D stage) to ui.json.

    runtime/python/Scripts/python.exe app/locales/add_layout_fr.py
"""
import json
from pathlib import Path

FR = {
    'Layout': 'Mise en scène', 'Image': 'Image', '2D drawing': 'Dessin 2D', '3D stage': 'Plateau 3D',
    'Edit the layout': 'Modifier la mise en scène',
    'The layout picture is the panel image; it updates a second after a change.':
    "L'image de la mise en scène devient l'image du plan ; elle se met à jour une seconde après chaque changement.",
    'Select a panel in the Storyboard tab first.': "Sélectionnez d'abord un plan dans l'onglet Storyboard.",
    'This panel uses its imported images. Choose 2D drawing or 3D stage above to stage it.':
    'Ce plan utilise ses images importées. Choisissez Dessin 2D ou Plateau 3D ci-dessus pour le mettre en scène.',
    'Stage': 'Plateau', 'Used by': 'Utilisé par', 'panels': 'plans', 'Ground': 'Sol', 'Sky': 'Ciel',
    'Create a stage (New) to place shapes and cameras.': 'Créez un plateau (Nouveau) pour placer des formes et des caméras.',
    'Box': 'Cube', 'Sphere': 'Sphère', 'Cylinder': 'Cylindre', 'Cone': 'Cône', 'Capsule': 'Capsule', 'Plane': 'Plan',
    'Mannequin': 'Mannequin', 'Import a mesh...': 'Importer un maillage...', 'Meshes': 'Maillages',
    'box': 'cube', 'sphere': 'sphère', 'cylinder': 'cylindre', 'cone': 'cône', 'capsule': 'capsule', 'plane': 'plan',
    'mannequin': 'mannequin', 'mesh': 'maillage', 'set': 'décor',
    'Objects': 'Objets', '* moved in this panel only': '* déplacé dans ce plan seulement',
    'Selected object': 'Objet sélectionné', 'Role': 'Rôle',
    'Reference: what this shape stands for.': 'Référence : ce que cette forme représente.',
    'Move in this panel only': 'Déplacer dans ce plan seulement', 'Position': 'Position', 'Rotation': 'Rotation',
    'Scale': 'Échelle', 'Hidden in this panel': 'Masqué dans ce plan',
    'Back to the stage placement': 'Revenir au placement du plateau',
    'Look through': 'Regarder par', 'Free view': 'Vue libre', 'Shot camera (start)': 'Caméra du plan (début)',
    'Shot camera (end)': 'Caméra du plan (fin)', 'Start = this view': 'Début = cette vue', 'End = this view': 'Fin = cette vue',
    'No end camera': 'Pas de caméra de fin', 'Move (W)': 'Déplacer (W)', 'Rotate (E)': 'Tourner (E)',
    'Scale (R)': 'Échelle (R)', 'Focal (mm, 24x36)': 'Focale (mm, 24x36)', 'Roll': 'Roulis',
    'Suggest the camera move': 'Proposer le mouvement de caméra',
    'Prompt camera set to: ': 'Caméra du prompt réglée sur : ',
    'Right drag: orbit - middle drag: pan - wheel: zoom - click: select - W/E/R: move/rotate/scale. With a shot camera '
    'selected, the gestures move that camera.':
    'Clic droit glissé : orbite - clic milieu glissé : déplacement - molette : zoom - clic : sélection - W/E/R : '
    'déplacer/tourner/échelle. En regardant par une caméra du plan, les gestes déplacent cette caméra.',
    'Select': 'Sélection', 'Rectangle': 'Rectangle', 'Ellipse': 'Ellipse', 'Line': 'Ligne', 'Arrow': 'Flèche',
    'Pen': 'Crayon', 'Figure': 'Silhouette', 'Text': 'Texte', 'Colour': 'Couleur', 'Width': 'Épaisseur',
    'Filled': 'Rempli', 'Background': 'Fond', 'Selected element': 'Élément sélectionné', 'Size': 'Taille',
    'Clear the drawing': 'Effacer le dessin',
    'Figures stand on the point you click; arrows show movement.':
    'Les silhouettes se tiennent sur le point cliqué ; les flèches indiquent un mouvement.',
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

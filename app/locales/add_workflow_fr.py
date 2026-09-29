"""Add the French translations of the MiniMax H3 workflow conversion window to ui.json.

    runtime/python/Scripts/python.exe app/locales/add_workflow_fr.py
"""
import json
from pathlib import Path

FR = {
    'MiniMax H3 workflow': 'Workflow MiniMax H3',
    'MiniMax H3 workflow (one generation per panel)...': 'Workflow MiniMax H3 (une génération par plan)...',
    'One MiniMax H3 generation per panel, with its own frames and references, then one edit with the storyboard '
    'transitions. Open workflow.json in CyTools_MiniMaxH3 (Workflows tab) to run it on the Colab GPU.':
    'Une génération MiniMax H3 par plan, avec ses propres images et références, puis un montage avec les '
    'transitions du storyboard. Ouvrez workflow.json dans CyTools_MiniMaxH3 (onglet Workflows) pour le lancer '
    'sur le GPU Colab.',
    'Picture and sampling': 'Image et échantillonnage', 'Seed': 'Graine', 'Seeds': 'Graines',
    'same for every shot': 'la même pour chaque plan', '+1 per shot': '+1 par plan', 'random': 'aléatoire',
    'Steps (0 = default)': 'Pas (0 = défaut)',
    'Turbo (shots without references)': 'Turbo (plans sans références)',
    'Turbo (shots with references)': 'Turbo (plans avec références)',
    '4 steps': '4 pas', '8 steps': '8 pas', 'Shots': 'Plans',
    "Start on the previous shot's last frame": 'Commencer sur la dernière image du plan précédent',
    'after crossfades': 'après les fondus enchaînés', 'always': 'toujours', 'never': 'jamais',
    'Layout render': 'Rendu de mise en scène', 'a reference picture': 'une image de référence',
    'the first frame': 'la première image', 'unused': 'non utilisé',
    'Panels over 15 s': 'Plans de plus de 15 s', 'chained parts': 'parties enchaînées', '15 s': '15 s',
    'Panels under 4 s': 'Plans de moins de 4 s', '4 s trimmed': '4 s recoupées', 'keep 4 s': 'garder 4 s',
    'Trim to the panel durations': 'Recouper à la durée des plans',
    'References per shot': 'Références par plan', 'Sketches': 'Croquis',
    'Prompt layout': 'Forme du prompt', 'auto (structured when characters have pictures)':
    'auto (structurée quand les personnages ont des images)', 'structured (subjects)': 'structurée (sujets)',
    'integrated': 'intégrée', 'Added to every shot': 'Ajouté à chaque plan',
    'Next part of a long panel': "Partie suivante d'un plan long",
    'Convert to a workflow': 'Convertir en workflow',
    'shots': 'plans', 'H3 generations': 'générations H3', 'workflow steps': 'étapes de workflow',
    'Generated': 'Généré', 'Kept': 'Gardé', 'Generations': 'Générations', 'First frame': 'Première image',
    'Guides': 'Guides', 'Pictures / videos / sounds': 'Images / vidéos / sons', 'Turbo': 'Turbo',
    'previous shot': 'plan précédent', 'image': 'image',
    'Click a row to read its prompt. H3 generates 4 to 15 s on a 5 + 17n frame grid; each shot is trimmed back to '
    'its panel duration.':
    'Cliquez sur une ligne pour lire son prompt. H3 génère de 4 à 15 s sur une grille de 5 + 17n images ; chaque '
    'plan est recoupé à la durée de son plan dans le storyboard.',
    'Depth control of 3D panels': 'Contrôle de profondeur des plans en 3D',
    'off': 'désactivé',
    'indicative (0.35, blurred)': 'indicatif (0,35, flou)',
    'guided (0.6)': 'guidé (0,6)',
    'strict (1.0, sharp)': 'strict (1,0, net)',
    'custom': 'personnalisé',
    'Strength': 'Force',
    'Until (share of the steps)': "Jusqu'à (part des pas)",
    'Blur': 'Flou',
    'none': 'aucun',
    'medium': 'moyen',
    'strong': 'fort',
    'Depth': 'Profondeur',
    'yes': 'oui',
    'A depth video along the camera move of each panel staged in 3D guides the generation (Fun ControlNet Union). The blur keeps the layout and drops the exact shapes of the blocking.': 'Une vidéo de profondeur, le long du mouvement de caméra de chaque plan mis en scène en 3D, guide la génération (Fun ControlNet Union). Le flou garde la disposition et efface les formes exactes du blocage.',
    'Pose': 'Pose',
    'At the end': 'À la fin',
    'same pose': 'même pose',
    'Moves during the panel': 'Se déplace pendant le plan',
    'Gizmo on the end placement': 'Gizmo sur la position de fin',
    'End position': 'Position de fin',
    'End rotation': 'Rotation de fin',
    'A standing character that moves walks; use the Moment slider to watch it.': 'Un personnage debout qui se déplace marche ; le curseur Moment permet de le voir.',
    'Moment in the panel': 'Moment dans le plan',
    'standing': 'debout',
    'walking': 'marche',
    'running': 'course',
    'sitting': 'assis',
    'crouching': 'accroupi',
    'arms raised': 'bras levés',
    'pointing': 'pointe du doigt',
    'Control': 'Contrôle',
    'auto (pose when a character is in frame)': 'auto (pose quand un personnage est dans le cadre)',
    'depth of the set': 'profondeur du décor',
    'pose of the characters': 'pose des personnages',
    'pose over depth (experimental)': 'pose sur la profondeur (expérimental)',
    'depth': 'profondeur',
    'pose': 'pose',
    'overlay': 'superposé',
    'A control video along the camera move of each panel staged in 3D guides the generation (Fun ControlNet Union): the depth of the set, or the pose of the characters (OpenPose skeletons, with their poses and moves). The blur applies to the depth only.': "Une vidéo de contrôle le long du mouvement de caméra de chaque plan mis en scène en 3D guide la génération (Fun ControlNet Union) : la profondeur du décor, ou la pose des personnages (squelettes OpenPose, avec leurs poses et déplacements). Le flou ne s'applique qu'à la profondeur.",
    'Joints': 'Articulations',
    'Start pose': 'Pose de début',
    'End pose': 'Pose de fin',
    'Symmetric (right = left)': 'Symétrique (droite = gauche)',
    'Lean forwards': 'Pencher en avant',
    'Twist (to its left)': 'Pivoter le buste (vers sa gauche)',
    'Head turn (to its left)': 'Tourner la tête (vers sa gauche)',
    'Head tilt (up)': 'Lever la tête',
    'Seated (pelvis at a height)': 'Assis (bassin à une hauteur)',
    'Seat height (m)': "Hauteur d'assise (m)",
    'Right arm': 'Bras droit',
    'Left arm': 'Bras gauche',
    'Right leg': 'Jambe droite',
    'Left leg': 'Jambe gauche',
    'Both arms': 'Les deux bras',
    'Both legs': 'Les deux jambes',
    'Raise forwards': "Lever vers l'avant",
    'Raise sideways': 'Lever sur le côté',
    'Elbow bend': 'Plier le coude',
    'Knee bend': 'Plier le genou',
    'Pose name': 'Nom de la pose',
    'Walks when the character moves': 'Marche quand le personnage se déplace',
    'Delete this project pose': 'Supprimer cette pose du projet',
    'A preset: moving a joint makes an editable copy of it for this project.': 'Une pose prédéfinie : bouger une articulation en crée une copie modifiable pour ce projet.',
    'Hand and foot handles': 'Poignées des mains et des pieds',
    'Pose handles in the view': 'Poignées de pose dans la vue',
    'Turn the forearm outwards': "Tourner l'avant-bras vers l'extérieur",
    'Turn the knee outwards': "Tourner le genou vers l'extérieur",
    'Bend sideways (to its left)': 'Pencher sur le côté (vers sa gauche)',
    'Pelvis tilt (left hip up)': 'Bascule du bassin (hanche gauche en haut)',
    'Hip gearing': 'Démultiplication des hanches',
    'Fingers': 'Doigts',
    'Fingertip handles, shown when a hand is large enough on screen: zoom in on it.': "Poignées au bout des doigts, affichées quand la main est assez grande à l'écran : zoomer dessus.",
    'Right hand': 'Main droite',
    'Left hand': 'Main gauche',
    'Both hands': 'Les deux mains',
    'Thumb curl (%)': 'Pouce plié (%)',
    'Index curl (%)': 'Index plié (%)',
    'Middle finger curl (%)': 'Majeur plié (%)',
    'Ring finger curl (%)': 'Annulaire plié (%)',
    'Little finger curl (%)': 'Auriculaire plié (%)',
    'Finger spread': 'Écartement des doigts',
    'Hands in the pose': 'Mains dans la pose',
    'Feet in the pose': 'Pieds dans la pose',
    'Wrist bend (towards the palm)': 'Poignet plié (vers la paume)',
    'Wrist towards the thumb': 'Poignet vers le pouce',
    'Right foot': 'Pied droit',
    'Left foot': 'Pied gauche',
    'Both feet': 'Les deux pieds',
    'Foot pitch (toes down)': 'Pied incliné (pointe vers le bas)',
    'Toes bent up': 'Orteils relevés',
    'A hip handle moves this many times less than the mouse (1:1 = direct).': 'Une poignée de hanche bouge ce nombre de fois moins que la souris (1:1 = direct).',
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

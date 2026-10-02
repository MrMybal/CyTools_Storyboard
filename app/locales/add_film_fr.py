"""Add the French translations of the MiniMax H3 film export window to ui.json.

    runtime/python/Scripts/python.exe app/locales/add_film_fr.py
"""
import json
from pathlib import Path

FR = {
    'MiniMax H3 film': 'Film MiniMax H3', 'MiniMax H3 film (ComfyUI / Colab)...': 'Film MiniMax H3 (ComfyUI / Colab)...',
    'One H3 segment per panel. Each segment starts a few frames before the previous one ends: those frames carry '
    'places, characters, light and sound across the cut, then are removed. The same film runs in CyTools_MiniMaxH3 '
    '(Colab) or in ComfyUI.':
    'Un segment H3 par plan. Chaque segment commence quelques images avant la fin du précédent : ces images '
    'transportent les lieux, les personnages, la lumière et le son à travers la coupe, puis sont retirées. Le même '
    'film tourne dans CyTools_MiniMaxH3 (Colab) ou dans ComfyUI.',
    'Picture': 'Image', 'Short edge': 'Petit côté', 'Width (0 = auto)': 'Largeur (0 = auto)',
    'Continuity between segments': 'Continuité entre les segments', 'Overlap': 'Chevauchement',
    '0 - independent segments': '0 - segments indépendants', '1 frame': '1 image', '5 frames (0.2 s)': '5 images (0,2 s)',
    '22 frames (0.9 s)': '22 images (0,9 s)', '39 frames (1.6 s)': '39 images (1,6 s)',
    '56 frames (2.3 s)': '56 images (2,3 s)', '73 frames (3.0 s)': '73 images (3,0 s)',
    'Across cuts': 'Aussi sur les coupes franches', 'Across fades to black': 'Aussi sur les fondus au noir',
    'Crossfades always carry continuity. Without overlap, segments are generated independently.':
    'Les fondus enchaînés gardent toujours la continuité. Sans chevauchement, les segments sont générés '
    'indépendamment.',
    'Pictures per segment (9 at most)': 'Images par segment (9 au maximum)',
    'Character identity': 'Identité des personnages', 'characters the panel uses': 'personnages utilisés par le plan',
    'every character, in every segment': 'tous les personnages, dans chaque segment',
    'Shot pictures': 'Images du plan', 'main (layout render first)': 'principale (rendu de mise en scène d\'abord)',
    'all the panel images': 'toutes les images du plan', 'none': 'aucune',
    'Project style': 'Style du projet', 'Project description': 'Description du projet',
    'Sound and music lines': 'Lignes son et musique', 'Added to every segment': 'Ajouté à chaque segment',
    'Note about the pictures': 'Note sur les images', 'Sentences': 'Phrases', 'Default sentences': 'Phrases par défaut',
    'Carried opening frames ({frames}, {seconds})': 'Images d\'ouverture reprises ({frames}, {seconds})',
    'Character identity ({n}, {name}, {description})': 'Identité d\'un personnage ({n}, {name}, {description})',
    'Layout render ({n})': 'Rendu de mise en scène ({n})', 'Sketch ({n})': 'Croquis ({n})',
    'First frame ({n})': 'Première image ({n})', 'Last frame ({n})': 'Dernière image ({n})',
    'Keyframe ({n}, {time})': 'Image clé ({n}, {time})', 'Shot reference ({n})': 'Référence du plan ({n})',
    'Location ({n}, {name}, {description})': 'Lieu ({n}, {name}, {description})',
    'Object ({n}, {name}, {description})': 'Objet ({n}, {name}, {description})',
    'Style ({n}, {name}, {description})': 'Style ({n}, {name}, {description})',
    'Sampling': 'Échantillonnage', 'Two-stage sampling (latent upscaler)': 'Échantillonnage en deux passes '
                                                                           '(agrandissement latent)',
    'High-resolution steps': 'Pas en haute résolution', 'Generate sound': 'Générer le son',
    'Export the film': 'Exporter le film', 'Open the export folder': 'Ouvrir le dossier d\'export',
    'Default options': 'Options par défaut', 'segments': 'segments', 'frames': 'images', 'no picture': 'aucune image',
    'Asked': 'Demandé', 'Real': 'Réel', 'Frames': "Plage d'images", 'Pictures': 'Images',
    'Click a row to read its prompt. Real durations follow the 5 + 17n frame grid of H3.':
    'Cliquez sur une ligne pour lire son prompt. Les durées réelles suivent la grille de 5 + 17n images de H3.',
    'Reference video ({n}, {name}, {description})': 'Vidéo de référence ({n}, {name}, {description})',
    'Character voice ({n}, {name}, {description})': "Voix d'un personnage ({n}, {name}, {description})",
    'Reference sound ({n}, {name}, {description})': 'Son de référence ({n}, {name}, {description})',
    'Sound of a reference video ({n}, {video}, {name})': "Son d'une vidéo de référence ({n}, {video}, {name})",
    'Reference videos': 'Vidéos de référence',
    'Character voices': 'Voix des personnages',
    'Reference sounds': 'Sons de référence',
    'Sound of the reference videos': 'Son des vidéos de référence',
    'Longest reference (s)': 'Référence la plus longue (s)',
    'Videos and sounds per segment (3 of each, 12 references in all)': 'Vidéos et sons par segment (3 de chaque, 12 références en tout)',
    "Videos: library items of kind video used by the panel. Voices: an audio file in a character's files. Sounds: library items of kind audio used by the panel.": "Vidéos : éléments de bibliothèque de type vidéo utilisés par le plan. Voix : un fichier audio parmi les fichiers d'un personnage. Sons : éléments de type audio utilisés par le plan.",
    'Videos': 'Vidéos',
    'Sounds': 'Sons',
    'Videos / sounds': 'Vidéos / sons',
    'ControlNet file (ComfyUI workflow)': 'Fichier ControlNet (workflow ComfyUI)',
    'Where the film goes': 'Destination du film',
    'Films folder': 'Dossier des films',
    'the project (exports/h3_film)': 'le projet (exports/h3_film)',
    'Choose...': 'Choisir...',
    'Films folder (for example ComfyUI/input/cytools_film on your Drive)': 'Dossier des films (par exemple ComfyUI/input/cytools_film sur ton Drive)',
    'Back to the project folder': 'Revenir au dossier du projet',
    'This film': 'Ce film',
    'in the ComfyUI workflow': 'dans le workflow ComfyUI',
    'The panels of a sequence are grouped into H3 segments of about 20 s: H3 cuts between the shots of a segment '
    'itself, so characters, places and sound stay continuous. A segment may start a few frames before the previous '
    'one ends (crossfades by default). The same film runs in CyTools_MiniMaxH3 (Colab) or in ComfyUI.':
        "Les cases d'une séquence sont regroupées en segments H3 d'environ 20 s : H3 coupe lui-même entre les plans "
        "d'un segment, si bien que personnages, lieux et son restent continus. Un segment peut commencer quelques "
        "images avant la fin du précédent (fondus enchaînés par défaut). Le même film tourne dans CyTools_MiniMaxH3 "
        "(Colab) ou dans ComfyUI.",
    'Segments': 'Segments', 'Grouping': 'Regroupement',
    'one segment per panel': 'un segment par case', 'panels of a sequence together': "les cases d'une séquence ensemble",
    'panels of the whole film together': 'les cases de tout le film ensemble',
    'Longest segment (s)': 'Segment le plus long (s)', 'Shots per segment (0 = any)': 'Plans par segment (0 = libre)',
    'H3 was trained on segments of up to 15 s; longer ones work but motion and faces may drift. Fewer shots per '
    'segment follow the prompt more closely.':
        "H3 a été entraîné sur des segments de 15 s au plus ; plus longs, ils marchent mais le mouvement et les visages "
        "peuvent dériver. Moins de plans par segment suivent le prompt de plus près.",
    'Shot header in a grouped segment ({shot}, {start}, {end}, {title})':
        "En-tête d'un plan dans un segment regroupé ({shot}, {start}, {end}, {title})",
    'Line of dialogue ({name}, {how}, {line})': 'Réplique ({name}, {how}, {line})',
    'Sound of a shot ({text})': "Son d'un plan ({text})", 'Music of a shot ({text})': "Musique d'un plan ({text})",
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

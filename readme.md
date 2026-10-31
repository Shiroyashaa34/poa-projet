# Robot Projet POA BENENES Nassim & KABOURI OUZENNOU Jaouad

Projet de semestre HAI716 en IASD. Un robot consulte un dictionnaire, 
fouille une armoire et rapporte un objet à un résident. 
Il ne connaît pas les murs au départ: il les découvre en avançant
et recalcule son chemin quand il en croise un.

Langage : Python - Version: 3.9 ou plus récente

## Lancer

```
python agent.py <carte.json> <scenario.json> <dossier_donnees> <trace_sortie.json>
```

Exemple (depuis la racine du dépôt):

```
python agent.py base_fournie/cartes/appartement_01.json base_fournie/cartes/scenario_01.json base_fournie/donnees sortie.json
```

Dépendances: aucune (bibliothèque standard de Python uniquement).

Le programme n'affiche rien, il écrit la trace dans le fichier de sortie. Si un
fichier d'entrée est invalide, il affiche l'erreur et s'arrête avec le code 1.

Pour voir le robot se déplacer, on a fait un petit script qui rejoue la trace
dans le terminal (c'est celui de la vidéo) :

```
python affichage.py base_fournie/cartes/appartement_01.json sortie.json 1
```

Le `1` est le numéro de la demande à rejouer. On peut ajouter un 4e argument
pour la vitesse des pas.

## Tester

```
python -m unittest discover -s tests -v
```

Les tests couvrent les 7 points de la section 8 : planification, replanification,
dictionnaire, sélecteur de l'armoire, règle de repli, validation des fichiers et
résident inaccessible. On teste aussi les 5 cartes fournies et une carte qu'on a
faite nous-mêmes (`tests/cartes/`).

## Organisation du code

| Fichier | Rôle |
|---|---|
| `agent.py` | point d'entrée, boucle de décision (perception, mémoire, décision, action) |
| `monde.py` | simulateur: le seul à lire la grille et le contenu des casiers |
| `memoire.py` | carte mentale du robot et parcours en largeur (BFS) |
| `decision.py` | lecture de l'émotion, ordre des casiers candidats, déplacement du sélecteur |
| `reconfort_io.py` | fourni: lecture des fichiers et écriture de la trace, on y a ajouté la validation |
| `affichage.py` | affiche une trace dans le terminal |
| `tests/` | tests automatisés |

## État

**Ce qui marche.** Les 5 cartes fournies : toutes les demandes sont livrées et
les traces sont valides. Les échecs (`emotion indeterminee`, `armoire vide`,
`resident inaccessible`) sont gérés sans arrêter le scénario. Les fichiers invalides de la section 5.6 sont refusés, sauf quelques cas listés plus bas.

**Ce qui ne marche pas.**
- Si un résident est inaccessible, le robot garde l'objet en main, et les
  demandes suivantes échouent (`robot deja charge`, motif qui n'est pas dans
  l'énoncé!).
- Le robot recalcule son chemin à chaque pas, ça devient lent sur de très
  grandes cartes.
- Il n'est pas optimal: il peut aller dans des culs-de-sac et repasser par des
  casiers déjà vus..
- La validation reste incomplète: un résident sans nom, un casier sans objet ou une version de mauvais type comme true sont encore acceptés.

## Vidéo

Dans le zip, nommée `demo.mp4`, également déclarée dans `rendu.json`. 


# Robot de réconfort — BENENES Nassim & KABOURI OUZENNOU Jaouad

Projet de semestre, master informatique. Un robot à perception locale
consulte un dictionnaire, fouille une armoire et rapporte un objet à un
résident.

Langage : Python — Version : 3.9 ou plus récente

## Lancer

```
python agent.py <carte.json> <scenario.json> <dossier_donnees> <trace_sortie.json>
```

Exemple :

```
python agent.py cartes/appartement_01.json cartes/scenario_01.json donnees sortie.json
```

Dépendances : aucune (bibliothèque standard de Python uniquement).

## Tester

```
<à compléter quand les tests existent>
```

*À compléter : une phrase sur ce que couvrent les tests.*

## Organisation du code

| Fichier | Rôle |
|---|---|
| `agent.py` | point d'entrée, boucle de décision |
| `reconfort_io.py` | fourni : lecture des fichiers d'entrée, écriture de la trace |
| `…` | *à compléter au fur et à mesure* |

## État

**Ce qui marche.** *À compléter en fin de projet.*

**Ce qui ne marche pas.** *À compléter en fin de projet.*

## Vidéo

`demo.mp4`, également déclarée dans `rendu.json`.
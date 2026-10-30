import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

DONNEES = RACINE / "base_fournie" / "donnees"
CARTES = RACINE / "base_fournie" / "cartes"

EMOTIONS = ["joie", "confiance", "peur", "surprise", "tristesse", "degout", "colere", "anticipation"]
INTENSITES = ["faible", "moyenne", "forte"]

def carte_depuis_grille(grille, nom="mini"):
    """Construit un dict carte a partir d'une grille dans test."""
    carte = {
        "format": "robot-reconfort/carte", "version": 1, "nom": nom,
        "dimensions": {"hauteur": len(grille), "largeur": len(grille[0])},
        "legende": {}, "grille": list(grille), "residents": [],
    }
    for l, ligne in enumerate(grille):
        for c, symbole in enumerate(ligne):
            if symbole == "R":
                carte["depart_robot"] = [l, c]
            elif symbole == "A":
                carte["armoire"] = {"position": [l, c]}
            elif symbole == "D":
                carte["dictionnaire"] = {"position": [l, c]}
            elif symbole == "P":
                n = len(carte["residents"]) + 1
                carte["residents"].append({"id": f"R{n}", "nom": f"res{n}", "position": [l, c]})
    return carte

def armoire_test(vides=(), casier_depart=(1, 0)):
    """Armoire complete: chaque casier contient 'objet_l_c', sauf vides"""
    #vides = ensemble de tuples (ligne, colonne) des casiers qu'on veut laisser vides
    casiers = []
    for l in range(3):
        for c in range(8):
            casiers.append({
                "ligne": l, "colonne": c,
                "emotion": EMOTIONS[c], "intensite": INTENSITES[l],
                "objet": None if (l, c) in vides else f"objet_{l}_{c}",
            })
    return {
        "format": "robot-reconfort/armoire", "version": 1, "nom": "armoire_test",
        "emotions": EMOTIONS, "intensites": INTENSITES,
        "casier_depart": list(casier_depart), "casiers": casiers,
    }
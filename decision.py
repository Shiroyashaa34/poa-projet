from __future__ import annotations
import reconfort_io as rio

def construire_lexique(dictionnaire: dict) -> dict[str, tuple[str, str]]:
    return {
        forme: (entree["emotion"], entree["intensite"])
        for entree in dictionnaire.get("entrees", [])
        for forme in entree["formes"]
    }

def analyser_message(message: str, lexique: dict[str, tuple[str, str]]) -> tuple[str, str] | None:
    for mot in rio.normaliser(message):
        if mot in lexique:
            return lexique[mot]
    return None

def coordonnees_casier(emotion: str, intensite: str, armoire: dict) -> tuple[int, int]:
    col = armoire["emotions"].index(emotion)
    row = armoire["intensites"].index(intensite)
    return row, col

def generer_replis(ligne: int, col: int) -> list[tuple[tuple[int, int], str]]:
    candidats = []
    for d in range(3):                                    
        colonnes = [col] if d == 0 else [(col + d) % 8, (col - d) % 8]  
        for i in sorted(range(3), key=lambda i: (abs(i - ligne), i)):  
            for c in colonnes:
                if d == 0:
                    repli = "aucun" if i == ligne else "intensite"
                else:
                    repli = f"voisine_{d}"
                candidats.append(((i, c), repli))
    return candidats

# plus court chemin entre deux casiers 
def trajet_casier(depart: tuple[int, int], arrivee: tuple[int, int]) -> list[str]:
    l1, c1 = depart
    l2, c2 = arrivee
    mouvements = []
    #vertical
    if l2 > l1:
        mouvements.extend(["S"] * (l2 - l1))
    elif l2 < l1:
        mouvements.extend(["N"] * (l1 - l2))

    #horizontal
    a = (c2 - c1) % 8
    if a <= 8 - a:
        mouvements.extend(["E"] * a)
    else:
        mouvements.extend(["O"] * (8 - a))

    return mouvements

# premier candidat non vide
def prochain_candidat(candidats, casiers_vus):
    for casier, repli in candidats:
        if casier in casiers_vus and casiers_vus[casier] is None:
            continue    
        return casier, repli
    return None        
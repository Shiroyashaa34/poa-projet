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
    candidats.append(((ligne, col), "aucun"))
    for l in range(3):
        if l != ligne:
            candidats.append(((l, col), "intensite"))
    candidats.append(((ligne, (col - 1) % 8), "voisine_1"))
    candidats.append(((ligne, (col + 1) % 8), "voisine_1"))
    candidats.append(((ligne, (col - 2) % 8), "voisine_2"))
    candidats.append(((ligne, (col + 2) % 8), "voisine_2"))
    return candidats
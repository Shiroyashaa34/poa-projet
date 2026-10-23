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
    for d in range(3):                                    # 1. distance sur la roue
        colonnes = [col] if d == 0 else [(col + d) % 8, (col - d) % 8]  # 4. horaire puis antihoraire
        for i in sorted(range(3), key=lambda i: (abs(i - ligne), i)):  # 2. écart, 3. plus faible
            for c in colonnes:
                if d == 0:
                    repli = "aucun" if i == ligne else "intensite"
                else:
                    repli = f"voisine_{d}"
                candidats.append(((i, c), repli))
    return candidats
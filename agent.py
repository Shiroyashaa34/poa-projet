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
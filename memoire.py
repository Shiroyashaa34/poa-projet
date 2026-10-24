from collections import deque
from monde import DIRECTIONS, voisin

#remonte les parents pour reconstruire le chemin
def reconstruire(predecesseur, case):
    chemin = [case]
    while predecesseur[chemin[-1]] is not None:
        chemin.append(predecesseur[chemin[-1]])
    chemin.reverse()
    return chemin

#parcours en largeur
def plus_court_chemin(depart, arrivees, est_traversable):
    depart = tuple(depart)
    arrivees = set(map(tuple, arrivees))
    if depart in arrivees:
        return [depart]

    predecesseur = {depart: None}
    file = deque([depart])

    while file:
        courant = file.popleft()
        for d in DIRECTIONS:
            v = voisin(courant, d)
            if v in predecesseur or not est_traversable(v):
                continue
            predecesseur[v] = courant
            if v in arrivees:
                return reconstruire(predecesseur, v)
            file.append(v)

    return None

#donne la lettre direction
def direction_entre(depart, arrivee):
    for d in DIRECTIONS:
        if voisin(depart, d) == tuple(arrivee):
            return d
    raise ValueError(f"Les cases {depart} et {arrivee} ne sont pas adjacentes")

#carte mentale (stock tout ce que le robot a découvert)
class Memoire:
    def __init__(self, carte):
        self.hauteur = carte["dimensions"]["hauteur"]
        self.largeur = carte["dimensions"]["largeur"]
        self.grille = [["?"] * self.largeur for _ in range(self.hauteur)]

        l, c = carte["depart_robot"]
        self.grille[l][c] = "libre"

        l, c = carte["armoire"]["position"]
        self.grille[l][c] = "armoire"

        l, c = carte["dictionnaire"]["position"]
        self.grille[l][c] = "dictionnaire"

        for r in carte["residents"]:
            l, c = r["position"]
            self.grille[l][c] = "resident"

        self.casiers = {}

    #maj des 4 voisins
    def memoriser_perception(self, position, perception):
        for d, type_case in perception.items():
            l, c = voisin(position, d)
            if 0 <= l < self.hauteur and 0 <= c < self.largeur:
                self.grille[l][c] = type_case

    #test case traversable ou pas
    def est_traversable(self, case):
        l, c = case
        if not (0 <= l < self.hauteur and 0 <= c < self.largeur):
            return False
        return self.grille[l][c] in ("libre", "?")

    #test si la case adjacente est traversable ou pas
    def cases_adjacentes(self, cible):
        return [
            voisin(cible, d)
            for d in DIRECTIONS
            if self.est_traversable(voisin(cible, d))
        ]

    #calcul itirenaire jusqua la cible
    def chemin_vers(self, depart, cible):
        arrivees = self.cases_adjacentes(cible)
        if not arrivees:
            return None
        return plus_court_chemin(depart, arrivees, self.est_traversable)

    #save casier
    def memoriser_casier(self, casier, contenu):
        self.casiers[tuple(casier)] = contenu

    #test casier deja vu
    def casier_deja_vu(self, casier):
        return tuple(casier) in self.casiers
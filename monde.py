
DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}

SYMBOLES = {
    "#": "mur",
    ".": "libre",
    "R": "libre",           # case de depart= case libre
    "A": "armoire",
    "D": "dictionnaire",
    "P": "resident",
}

LIGNES_ARMOIRE = 3
COLONNES_ARMOIRE = 8


class ActionIllegale(Exception):
    """L'agent a tente une action interdite : c'est un bug de l'agent."""


def voisin(case, direction):
    """Case atteinte en faisant un pas dans `direction`."""
    dl, dc = DIRECTIONS[direction]
    return (case[0] + dl, case[1] + dc)


class Monde:

    def __init__(self, carte, armoire):
        self._grille = carte["grille"]
        self._objets = {(c["ligne"], c["colonne"]): c["objet"]
                        for c in armoire["casiers"]}

        self.position = tuple(carte["depart_robot"])
        self.casier = tuple(armoire["casier_depart"])
        self.transporte = None

        self.pos_armoire = tuple(carte["armoire"]["position"])
        self.pos_dictionnaire = tuple(carte["dictionnaire"]["position"])
        self.residents = {r["id"]: tuple(r["position"])
                          for r in carte["residents"]}

    # --robot--
    def _type_case(self, case):
        l, c = case
        if not (0 <= l < len(self._grille) and 0 <= c < len(self._grille[l])):
            return "mur"    # hors grille : on le traite comme un mur
        return SYMBOLES[self._grille[l][c]]

    def adjacent(self, cible):
        """Le robot est-il orthogonalement colle a `cible` ?"""
        return any(voisin(self.position, d) == cible for d in DIRECTIONS)

    def percevoir(self):
        """Les quatre cases autour du robot, et rien d'autre (3.2)."""
        return {d: self._type_case(voisin(self.position, d))
                for d in DIRECTIONS}

    def contenu_casier(self):
        """Objet du casier courant si le robot est devant l'armoire, sinon None."""
        if not self.adjacent(self.pos_armoire):
            return None
        return self._objets.get(self.casier)

    # -actions-
    def avancer(self, direction):
        cible = voisin(self.position, direction)
        if self._type_case(cible) != "libre":
            raise ActionIllegale(f"AVANCER {direction} : {cible} n'est pas libre")
        self.position = cible

    def consulter(self):
        if not self.adjacent(self.pos_dictionnaire):
            raise ActionIllegale("CONSULTER : pas adjacent au dictionnaire")

    def chercher(self, direction):
        if not self.adjacent(self.pos_armoire):
            raise ActionIllegale("CHERCHER : pas adjacent a l'armoire")
        l, c = self.casier
        dl, dc = DIRECTIONS[direction]
        l += dl
        if not 0 <= l < LIGNES_ARMOIRE:
            raise ActionIllegale(f"CHERCHER {direction} : les lignes ne bouclent pas")
        c = (c + dc) % COLONNES_ARMOIRE      # les colonnes bouclent
        self.casier = (l, c)

    def prendre(self, objet):
        if not self.adjacent(self.pos_armoire):
            raise ActionIllegale("PRENDRE : pas adjacent a l'armoire")
        if self.transporte is not None:
            raise ActionIllegale("PRENDRE : le robot transporte deja un objet")
        if self._objets.get(self.casier) != objet:
            raise ActionIllegale(f"PRENDRE {objet} : pas dans le casier {self.casier}")
        self.transporte = objet

    def donner(self, objet, resident):
        if not self.adjacent(self.residents[resident]):
            raise ActionIllegale(f"DONNER : pas adjacent au resident {resident}")
        if self.transporte != objet:
            raise ActionIllegale(f"DONNER {objet} : le robot ne le transporte pas")
        self.transporte = None
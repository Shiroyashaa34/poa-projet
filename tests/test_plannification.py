import unittest
 
import outils
from monde import voisin, DIRECTIONS
from memoire import Memoire, plus_court_chemin, direction_entre
from decision import trajet_casier
 
# deux pieces separees par un mur, une seule ouverture en (3, 4)
PIECES = [
    "#########",
    "#R..#...#",
    "#...#.A.#",
    "#.D...P.#",
    "#########",
]
# meme plan, mais sans ouverture
FERME = [ligne if i != 3 else "#.D.#.P.#" for i, ligne in enumerate(PIECES)]
 
 
def memoire_connue(grille):
    """Memoire dont les murs du dessin sont deja decouverts."""
    m = Memoire(outils.carte_depuis_grille(grille))
    for l, ligne in enumerate(grille):
        for c, symbole in enumerate(ligne):
            if symbole == "#":
                m.grille[l][c] = "mur"
    return m
 
 
class TestPlanification(unittest.TestCase):
    def setUp(self):
        self.m = memoire_connue(PIECES)
 
    def test_ligne_droite(self):
        ch = plus_court_chemin((1, 1), [(1, 3)], self.m.est_traversable)
        self.assertEqual(ch, [(1, 1), (1, 2), (1, 3)])
 
    def test_depart_egal_arrivee(self):
        ch = plus_court_chemin((1, 1), [(1, 1)], self.m.est_traversable)
        self.assertEqual(ch, [(1, 1)])
 
    def test_contourne_le_mur_par_l_ouverture(self):
        ch = plus_court_chemin((1, 3), [(1, 5)], self.m.est_traversable)
        self.assertEqual(len(ch) - 1, 6)
        self.assertIn((3, 4), ch)
 
    def test_inaccessible(self):
        m = memoire_connue(FERME)
        self.assertIsNone(plus_court_chemin((1, 1), [(1, 5)], m.est_traversable))
 
    def test_direction_entre(self):
        cas = {(1, 2): "N", (3, 2): "S", (2, 3): "E", (2, 1): "O"}
        for arrivee, attendu in cas.items():
            with self.subTest(arrivee=arrivee):
                self.assertEqual(direction_entre((2, 2), arrivee), attendu)
 
    def test_chemin_vers_armoire_finit_a_cote(self):
        ch = self.m.chemin_vers((1, 1), (2, 6))
        self.assertTrue(any(voisin(ch[-1], d) == (2, 6) for d in DIRECTIONS))
        self.assertIn((3, 4), ch)
 
    def test_replanifie_quand_un_mur_est_decouvert(self):
        m = Memoire(outils.carte_depuis_grille(PIECES))   # aucun mur connu
        avant = plus_court_chemin((1, 3), [(1, 5)], m.est_traversable)
        self.assertEqual(avant, [(1, 3), (1, 4), (1, 5)])  # il croit pouvoir passer tout droit
 
        # arrive en (1, 3), le robot percoit un mur a l'est
        m.memoriser_perception((1, 3), {"N": "libre", "S": "libre", "E": "mur", "O": "libre"})
 
        apres = plus_court_chemin((1, 3), [(1, 5)], m.est_traversable)
        self.assertNotIn((1, 4), apres)
        self.assertEqual(len(apres) - 1, 4)               # detour : 2 pas de plus
 
    def test_trajet_casier(self):
        cas = {
            ((0, 2), (2, 2)): ["S", "S"],
            ((1, 1), (1, 3)): ["E", "E"],
            ((1, 7), (1, 0)): ["E"],        # les colonnes bouclent
            ((1, 0), (1, 7)): ["O"],
            ((1, 3), (1, 3)): [],
        }
        for (depart, arrivee), attendu in cas.items():
            with self.subTest(depart=depart, arrivee=arrivee):
                self.assertEqual(trajet_casier(depart, arrivee), attendu)
 
 
if __name__ == "__main__":
    unittest.main()
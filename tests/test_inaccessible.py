import unittest

import outils
import reconfort_io as rio
from monde import Monde
from agent import Agent


DICO = rio.charger_dictionnaire(outils.DONNEES / "dictionnaire.json")
MESSAGE = "Je suis triste"


def lancer(grille, residents=("R1",)):
    carte = outils.carte_depuis_grille(grille)
    armoire = outils.armoire_test()
    monde = Monde(carte, armoire)
    trace = rio.Trace(carte["nom"], "test", ["Test"])
    agent = Agent(carte, DICO, monde, trace)
    for num, res in enumerate(residents, 1):
        agent.traiter_demande({"numero": num, "resident": res, "message": MESSAGE})
    return trace.livraisons, trace.pas


class TestInaccessible(unittest.TestCase):
    def test_dictionnaire_inaccessible(self):
        grille = [
            "#######",
            "#R.A#D#",
            "#..P###",
            "#######",
        ]
        livraisons, _ = lancer(grille)
        self.assertFalse(livraisons[0]["succes"])
        self.assertEqual(livraisons[0]["motif_echec"], "dictionnaire inaccessible")

    def test_armoire_inaccessible(self):
        grille = [
            "#######",
            "#R.D#A#",
            "#..P###",
            "#######",
        ]
        livraisons, _ = lancer(grille)
        self.assertFalse(livraisons[0]["succes"])
        self.assertEqual(livraisons[0]["emotion"], "tristesse")
        self.assertEqual(livraisons[0]["motif_echec"], "armoire inaccessible")

    def test_resident_inaccessible(self):
        # Le dictionnaire et l'armoire sont accessibles, mais le resident est isole.
        grille = [
            "#########",
            "#R..D.A.#",
            "#.....#P#",
            "#########",
        ]
        livraisons, _ = lancer(grille)
        self.assertFalse(livraisons[0]["succes"])
        self.assertEqual(livraisons[0]["motif_echec"], "resident inaccessible")

    def test_robot_enferme_au_depart(self):
        grille = [
            "#######",
            "#R#.DA#",
            "###..P#",
            "#######",
        ]
        livraisons, pas = lancer(grille)
        self.assertFalse(livraisons[0]["succes"])
        self.assertEqual(len(pas), 0)

    def test_robot_deja_charge_apres_resident_inaccessible(self):
        # R1 est isole. Le robot, le dictionnaire et l'armoire sont dans la
        # meme zone accessible. R2 est le resident situe dans la zone accessible.
        grille = [
            "#########",
            "#P#D.A.R#",
            "###.....#",
            "#......P#",
            "#########",
        ]
        livraisons, _ = lancer(grille, residents=("R1", "R2"))
        self.assertEqual(livraisons[0]["motif_echec"], "resident inaccessible")
        self.assertEqual(livraisons[1]["motif_echec"], "robot deja charge")


if __name__ == "__main__":
    unittest.main()

import unittest

import outils
import reconfort_io as rio
from monde import Monde, ActionIllegale
from agent import Agent

GRILLE = [
    "#########",
    "#R.A.D.P#",
    "#.......#",
    "#########",
]


class TestSelecteur(unittest.TestCase):

    def monde_devant_armoire(self, casier_depart):
        carte = outils.carte_depuis_grille(GRILLE)
        monde = Monde(carte, outils.armoire_test(casier_depart=casier_depart))
        monde.avancer("E")                      
        return monde

    def test_les_colonnes_bouclent(self):
        monde = self.monde_devant_armoire((1, 0))
        monde.chercher("O")
        self.assertEqual(monde.casier, (1, 7)) 
        monde.chercher("E")
        self.assertEqual(monde.casier, (1, 0))  

    def test_les_lignes_ne_bouclent_pas(self):
        with self.assertRaises(ActionIllegale):
            self.monde_devant_armoire((0, 3)).chercher("N")
        with self.assertRaises(ActionIllegale):
            self.monde_devant_armoire((2, 3)).chercher("S")

class TestRepli(unittest.TestCase):
    """'Je suis triste' -> tristesse / moyenne -> casier exact [1, 4]."""

    def livrer(self, vides):
        carte = outils.carte_depuis_grille(GRILLE)
        dico = rio.charger_dictionnaire(outils.DONNEES / "dictionnaire.json")
        trace = rio.Trace("mini", "test")
        agent = Agent(carte, dico, Monde(carte, outils.armoire_test(vides)), trace)
        agent.traiter_demande({"numero": 1, "resident": "R1", "message": "Je suis triste"})
        return trace.livraisons[0], trace.pas

    def test_casier_exact_garni(self):
        liv, _ = self.livrer(vides=())
        self.assertEqual((liv["casier_choisi"], liv["repli"]), ([1, 4], "aucun"))

    def test_casier_vide_repli_en_intensite(self):
        liv, _ = self.livrer(vides={(1, 4)})
        self.assertEqual((liv["casier_choisi"], liv["repli"]), ([0, 4], "intensite"))

    def test_colonne_vide_repli_sur_voisine(self):
        liv, pas = self.livrer(vides={(0, 4), (1, 4), (2, 4)})
        self.assertEqual((liv["casier_choisi"], liv["repli"]), ([1, 5], "voisine_1"))
        vus = {tuple(p["casier"]) for p in pas if p["action"] in ("CHERCHER", "PRENDRE")}
        self.assertTrue({(0, 4), (1, 4), (2, 4)} <= vus)

    def test_aucun_casier_garni_a_distance_2(self):
        vides = {(l, c) for l in range(3) for c in (2, 3, 4, 5, 6)}
        liv, _ = self.livrer(vides)
        self.assertFalse(liv["succes"])
        self.assertEqual(liv["motif_echec"], "armoire vide")

if __name__ == "__main__":
    unittest.main()
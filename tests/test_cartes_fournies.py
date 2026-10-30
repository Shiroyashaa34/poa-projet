import unittest

import outils
import reconfort_io as rio
from monde import Monde
from agent import Agent


class TestCartesFournies(unittest.TestCase):
    def test_les_5_cartes(self):
        dico = rio.charger_dictionnaire(outils.DONNEES / "dictionnaire.json")
        for n in range(1, 6):
            with self.subTest(carte=n):
                carte = rio.charger_carte(outils.CARTES / f"appartement_0{n}.json")
                scenario = rio.charger_scenario(outils.CARTES / f"scenario_0{n}.json", carte)
                armoire = rio.charger_armoire(outils.DONNEES / f"{scenario['armoire']}.json")
                trace = rio.Trace(carte["nom"], scenario["nom"])

                #on retire la grille, si l'agent s'en sort, c'est qu'il passe bien par Monde et pas par carte["grille"]
                sans_grille = {k: v for k, v in carte.items() if k != "grille"}
                agent = Agent(sans_grille, dico, Monde(carte, armoire), trace)
                for demande in scenario["demandes"]:
                    agent.traiter_demande(demande)
                self.assertTrue(all(l["succes"] for l in trace.livraisons))

                #perceptions et contenus_casier doivent correspondre a la trace           
                monde = Monde(carte, armoire)
                for pas in trace.pas:
                    self.assertEqual(monde.percevoir(), pas["perception"])
                    self.assertEqual(monde.contenu_casier(), pas["contenu_casier"])
                    if pas["action"] == "AVANCER":
                        monde.avancer(pas["argument"])
                    elif pas["action"] == "CHERCHER":
                        monde.chercher(pas["argument"])

if __name__ == "__main__":
    unittest.main()
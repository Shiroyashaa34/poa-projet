import unittest

import outils
import reconfort_io as rio
from monde import Monde
from agent import Agent

DOSSIER = outils.RACINE / "tests" / "cartes"


class TestCartePiege(unittest.TestCase):

    def test_les_5_demandes(self):
        carte = rio.charger_carte(DOSSIER / "appartement_piege.json")
        scenario = rio.charger_scenario(DOSSIER / "scenario_piege.json", carte)
        dico = rio.charger_dictionnaire(outils.DONNEES / "dictionnaire.json")
        armoire = rio.charger_armoire(outils.DONNEES / f"{scenario['armoire']}.json")
        trace = rio.Trace(carte["nom"], scenario["nom"])
        agent = Agent(carte, dico, Monde(carte, armoire), trace)
        for demande in scenario["demandes"]:
            agent.traiter_demande(demande)

        obtenu = [(l["casier_choisi"], l["repli"], l["motif_echec"]) for l in trace.livraisons]
        self.assertEqual(obtenu, [
            ([2, 4], "voisine_1", None),        # "sidere" avant "seul" + colonne surprise vide
            ([1, 4], "aucun", None),          
            (None, "aucun", "emotion indeterminee"),
            ([1, 7], "intensite", None),        
            (None, "aucun", "resident inaccessible"),  # R3 entoure de murs et de residents
        ])


if __name__ == "__main__":
    unittest.main()
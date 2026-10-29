import json
import tempfile
import unittest
from pathlib import Path

import outils
import reconfort_io as rio

GRILLE = ["#######", "#R.A.D#", "#..P..#", "#######"]


class TestValidation(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.chemin = Path(tmp.name) / "test.json"

    def ecrire(self, donnees):
        self.chemin.write_text(json.dumps(donnees), encoding="utf-8")
        return self.chemin

    def test_fichier_absent_ou_corrompu(self):
        with self.assertRaises(rio.ErreurFichier):
            rio.charger_carte(self.chemin)
        self.chemin.write_text("{pas du json", encoding="utf-8")
        with self.assertRaises(rio.ErreurFichier):
            rio.charger_carte(self.chemin)

    def test_carte_invalide(self):
        base = outils.carte_depuis_grille(GRILLE)
        for err in [
            {**base, "grille": ["###", "##"]},          # non rectangulaire
            {**base, "depart_robot": [9, 9]},           # hors bornes
            {**base, "depart_robot": [0, 0]},           # sur un mur
        ]:
            with self.assertRaises(rio.ErreurFichier):
                rio.charger_carte(self.ecrire(err))

    def test_armoire_invalide(self):
        base = outils.armoire_test()
        for err in [
            {**base, "casiers": base["casiers"][:20]},  # pas 24 casiers
            {**base, "casier_depart": [5, 0]},          # hors de l'armoire
        ]:
            with self.assertRaises(rio.ErreurFichier):
                rio.charger_armoire(self.ecrire(err))

    def test_dictionnaire_invalide(self):
        dico = json.loads((outils.DONNEES / "dictionnaire.json").read_text(encoding="utf-8"))
        dico["entrees"][0]["emotion"] = "inconnue"
        with self.assertRaises(rio.ErreurFichier):
            rio.charger_dictionnaire(self.ecrire(dico))

    def test_scenario_invalide(self):
        carte = outils.carte_depuis_grille(GRILLE)
        scenario = {
            "format": "robot-reconfort/scenario", "version": 1, "nom": "s",
            "carte": "mini", "armoire": "armoire_standard",
            "demandes": [{"numero": 1, "resident": "R99", "message": "aide"}],
        }
        with self.assertRaises(rio.ErreurFichier):
            rio.charger_scenario(self.ecrire(scenario), carte)


if __name__ == "__main__":
    unittest.main()
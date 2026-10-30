import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import outils
import reconfort_io as rio
import agent

GRILLE = ["#######", "#R.A.D#", "#..P..#", "#######"]
CARTE = outils.carte_depuis_grille(GRILLE, "mini")
ARMOIRE = outils.armoire_test()
SCENARIO = {
    "format": "robot-reconfort/scenario", "version": 1, "nom": "s",
    "carte": "mini", "armoire": "armoire_standard",
    "demandes": [{"numero": 1, "resident": "R1", "message": "Bonjour"}],
}


def demande(**champs):
    """Scenario valide dont la premiere demande est modifiee."""
    return {**SCENARIO, "demandes": [{**SCENARIO["demandes"][0], **champs}]}


def sans(donnees, champ):
    return {k: v for k, v in donnees.items() if k != champ}


def casier0(**champs):
    """Armoire valide dont le casier [0, 0] est modifie."""
    return {**ARMOIRE, "casiers": [{**ARMOIRE["casiers"][0], **champs}] + ARMOIRE["casiers"][1:]}


class TestValidation(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dossier = Path(tmp.name)

    def ecrire(self, donnees, nom="test.json"):
        chemin = self.dossier / nom
        chemin.write_text(donnees if isinstance(donnees, str) else json.dumps(donnees), encoding="utf-8")
        return chemin

    def verifier_rejet(self, fonction, cas_invalides, *args):
        for nom, donnees in cas_invalides.items():
            with self.subTest(nom):
                with self.assertRaises(rio.ErreurFichier):
                    fonction(self.ecrire(donnees), *args)

    def test_fichier_illisible_ou_non_json(self):
        with self.assertRaises(rio.ErreurFichier):
            rio.charger_carte(self.dossier / "absent.json")
        chemin = self.dossier / "corrompu.json"
        for contenu in (b"{pas du json", b"[1, 2]", b"\xff\xfe\x00"):
            chemin.write_bytes(contenu)
            with self.assertRaises(rio.ErreurFichier):
                rio.charger_carte(chemin)

    def test_entete_et_champs_carte(self):
        self.assertEqual(rio.charger_carte(self.ecrire(CARTE))["nom"], "mini")
        self.verifier_rejet(rio.charger_carte, {
            "mauvaise version": {**CARTE, "version": 2},
            "mauvais format": {**CARTE, "format": "autre"},
            "champ obligatoire absent": sans(CARTE, "residents"),
            "mauvais type de champ": {**CARTE, "dimensions": "4x7"},
        })

    def test_grille_carte_invalide(self):
        self.verifier_rejet(rio.charger_carte, {
            "dimensions incoherentes": {**CARTE, "dimensions": {"hauteur": 9, "largeur": 7}},
            "grille non rectangulaire": {**CARTE, "grille": ["#######", "#R.A.D", "#..P..#", "#######"]},
            "caractere inconnu": {**CARTE, "grille": ["#######", "#R.A.D#", "#X.P..#", "#######"]},
        })

    def test_positions_carte_invalides(self):
        res = CARTE["residents"][0]
        self.verifier_rejet(rio.charger_carte, {
            "depart hors bornes": {**CARTE, "depart_robot": [9, 9]},
            "depart pas sur R": {**CARTE, "depart_robot": [1, 2]},
            "armoire pas sur A": {**CARTE, "armoire": {"position": [1, 2]}},
            "dictionnaire pas sur D": {**CARTE, "dictionnaire": {"position": [1, 4]}},
            "resident sur un mur": {**CARTE, "residents": [{**res, "position": [0, 0]}]},
            "deux residents meme id": {**CARTE, "residents": [res, res]},
        })

    def test_armoire_structure_invalide(self):
        self.assertEqual(len(rio.charger_armoire(self.ecrire(ARMOIRE))["casiers"]), 24)
        casiers = ARMOIRE["casiers"]
        self.verifier_rejet(rio.charger_armoire, {
            "23 casiers": {**ARMOIRE, "casiers": casiers[:23]},
            "casier en double": {**ARMOIRE, "casiers": [dict(casiers[0])] + casiers[:23]},
            "casier hors bornes": casier0(ligne=5),
            "casier_depart hors bornes": {**ARMOIRE, "casier_depart": [3, 0]},
        })

    def test_armoire_contenu_invalide(self):
        self.verifier_rejet(rio.charger_armoire, {
            "etiquette mal indexee": casier0(emotion="peur"),
            "emotion inconnue": casier0(emotion="nostalgie"),
            "objet chaine vide": casier0(objet=""),
        })

    def test_dictionnaire_invalide(self):
        dico = json.loads((outils.DONNEES / "dictionnaire.json").read_text(encoding="utf-8"))
        self.assertTrue(rio.charger_dictionnaire(self.ecrire(dico))["entrees"])
        e0, e1 = dico["entrees"][:2]
        self.verifier_rejet(rio.charger_dictionnaire, {
            "emotions dans le desordre": {**dico, "emotions": list(reversed(outils.EMOTIONS))},
            "mot dans deux entrees": {**dico, "entrees": [e0, {**e1, "formes": [e0["formes"][0]]}]},
            "emotion inconnue": {**dico, "entrees": [{**e0, "emotion": "nostalgie"}]},
            "intensite inconnue": {**dico, "entrees": [{**e0, "intensite": "enorme"}]},
            "formes vide": {**dico, "entrees": [{**e0, "formes": []}]},
        })

    def test_scenario_invalide(self):
        self.assertEqual(len(rio.charger_scenario(self.ecrire(SCENARIO), CARTE)["demandes"]), 1)
        self.verifier_rejet(rio.charger_scenario, {
            "champ demandes absent": sans(SCENARIO, "demandes"),
            "numero non entier": demande(numero="1"),
            "message non chaine": demande(message=42),
            "scenario pour une autre carte": {**SCENARIO, "carte": "autre"},
            "resident absent de la carte": demande(resident="R99"),
        }, CARTE)

    def test_programme_complet(self):
        sortie = self.dossier / "trace.json"

        def lancer(carte=CARTE, scenario=SCENARIO):
            args = [self.ecrire(carte, "carte.json"), self.ecrire(scenario, "scenario.json"),
                    outils.DONNEES, sortie]
            sortie.unlink(missing_ok=True)
            with contextlib.redirect_stderr(io.StringIO()) as err:
                return agent.main(["agent.py", *map(str, args)]), err.getvalue()

        code, _ = lancer()
        self.assertEqual(code, 0)
        self.assertTrue(sortie.exists())

        for nom, fichiers in {
            "carte de mauvaise version": {"carte": {**CARTE, "version": 2}},
            "scenario pour une autre carte": {"scenario": {**SCENARIO, "carte": "autre"}},
            "armoire du scenario introuvable": {"scenario": {**SCENARIO, "armoire": "inexistante"}},
        }.items():
            with self.subTest(nom):
                code, erreur = lancer(**fichiers)
                self.assertNotEqual(code, 0)
                self.assertTrue(erreur.strip())
                self.assertFalse(sortie.exists())


if __name__ == "__main__":
    unittest.main()
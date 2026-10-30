import unittest

import tests.outils as outils
import reconfort_io as rio
from decision import construire_lexique, analyser_message


class TestDictionnaire(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dico = rio.charger_dictionnaire(outils.DONNEES / "dictionnaire.json")
        cls.lexique = construire_lexique(dico)

    def lire(self, message):
        return analyser_message(message, self.lexique)

    def test_un_message_par_emotion(self):
        cas = {
            "Je suis heureux de te revoir": ("joie", "moyenne"),
            "Je te fais confiance pour ça": ("confiance", "moyenne"),
            "Il y a une tempête dehors, je suis terrifié.": ("peur", "forte"),
            "Le facteur est passé un dimanche, c'est bizarre.": ("surprise", "faible"),
            "Je me sens triste depuis ce matin": ("tristesse", "moyenne"),
            "Cette odeur me dégoûte": ("degout", "moyenne"),
            "Je suis en colère contre mon voisin": ("colere", "moyenne"),
            "Je suis impatient de te revoir": ("anticipation", "moyenne"),
        }
        for message, attendu in cas.items():
            with self.subTest(message=message):
                self.assertEqual(self.lire(message), attendu)

    def test_le_premier_mot_reconnu_gagne(self):
        message = "Je suis sidéré, la téle s'est allumée toute seule."
        self.assertEqual(self.lire(message), ("surprise", "forte"))

    def test_ordre_inverse_donne_l_autre_emotion(self):
        self.assertEqual(self.lire("Je me sens seule, et ce bruit m'a sidérée."), ("tristesse", "moyenne"))

    def test_accents_et_majuscules(self):
        self.assertEqual(self.lire("Je suis TRISTE, vraiment TRISTE !!!"), ("tristesse", "moyenne"))

    def test_aucun_mot_reconnu(self):
        self.assertIsNone(self.lire("Bonjour, pouvez-vous ouvrir la fenêtre ?"))

    def test_message_vide(self):
        self.assertIsNone(self.lire(""))


if __name__ == "__main__":
    unittest.main()
import sys
from pathlib import Path

import reconfort_io as rio
from monde import Monde, DIRECTIONS, voisin
from memoire import Memoire, direction_entre
from decision import (construire_lexique, analyser_message, coordonnees_casier,
                      generer_replis, trajet_casier, prochain_candidat)

EQUIPE = ["BENENES Nassim", "KABOURI OUZENNOU Jaouad"]


class Agent:

    def __init__(self, carte, dictionnaire, monde, trace):
        self.monde = monde         
        self.trace = trace
        self.memoire = Memoire(carte)
        self.lexique = construire_lexique(dictionnaire)
        self.dictionnaire = dictionnaire

        self.position = tuple(carte["depart_robot"])
        self.casier = tuple(monde.casier)
        self.pos_armoire = tuple(carte["armoire"]["position"])
        self.pos_dictionnaire = tuple(carte["dictionnaire"]["position"])
        self.residents = {r["id"]: tuple(r["position"]) for r in carte["residents"]}

        self.objet_porte = None
        self.demande = None

    # 1 PERCEPTION 
    def percevoir(self):
        return self.monde.percevoir(), self.monde.contenu_casier()

    # 2 MEMOIRE 
    def memoriser(self, perception, contenu):
        self.memoire.memoriser_perception(self.position, perception)
        if self.adjacent(self.pos_armoire):
            self.memoire.memoriser_casier(self.casier, contenu)

    def adjacent(self, cible):
        return any(voisin(self.position, d) == cible for d in DIRECTIONS)

    # 3 DECISION 
    def pas_vers(self, cible):
        chemin = self.memoire.chemin_vers(self.position, cible)
        if chemin is None:
            return None
        if len(chemin) == 1:
            return "ARRIVE"
        return direction_entre(chemin[0], chemin[1])

    # 4 ACTION 
    def agir(self, action, argument, perception, contenu):
        # la trace note la position et le casier AVANT l'action (enonce 5.5)
        self.trace.ajouter_pas(demande=self.demande, position=self.position,
                               casier=self.casier, action=action, argument=argument,
                               perception=perception, contenu_casier=contenu)
        if action == "AVANCER":
            self.monde.avancer(argument)
            self.position = voisin(self.position, argument)
        elif action == "CHERCHER":
            self.monde.chercher(argument)
            dl, dc = DIRECTIONS[argument]
            self.casier = (self.casier[0] + dl, (self.casier[1] + dc) % 8)
        elif action == "CONSULTER":
            self.monde.consulter()
        elif action == "PRENDRE":
            self.monde.prendre(argument)
            self.objet_porte = argument
        elif action == "DONNER":
            self.monde.donner(argument, self.resident_courant)
            self.objet_porte = None

    # etapes d'une demande
    def rejoindre(self, cible):
        while True:
            perception, contenu = self.percevoir()
            self.memoriser(perception, contenu)
            d = self.pas_vers(cible)        # replanifie a chaque pas
            if d is None:
                return False
            if d == "ARRIVE":
                return True
            self.agir("AVANCER", d, perception, contenu)

    def faire_sur_place(self, action, argument=None):
        perception, contenu = self.percevoir()
        self.memoriser(perception, contenu)
        self.agir(action, argument, perception, contenu)

    def fouiller(self, candidats):
        while True:
            perception, contenu = self.percevoir()
            self.memoriser(perception, contenu)
            cible = prochain_candidat(candidats, self.memoire.casiers)
            if cible is None:
                return None
            casier, repli = cible
            if casier == self.casier:       # deja vu et garni : on le prend
                self.agir("PRENDRE", contenu, perception, contenu)
                return casier, repli, contenu
            d = trajet_casier(self.casier, casier)[0]
            self.agir("CHERCHER", d, perception, contenu)

    def traiter_demande(self, demande):
        self.demande = demande["numero"]
        self.resident_courant = demande["resident"]
        echec = lambda motif, emo=None, inten=None: self.trace.ajouter_livraison(
            demande=self.demande, resident=self.resident_courant, emotion=emo,
            intensite=inten, casier_choisi=None, repli="aucun", objet=None,
            succes=False, motif_echec=motif)

        # dictionnaire
        if not self.rejoindre(self.pos_dictionnaire):
            return echec("dictionnaire inaccessible")
        self.faire_sur_place("CONSULTER")
        lu = analyser_message(demande["message"], self.lexique)
        if lu is None:
            return echec("emotion indeterminee")
        emotion, intensite = lu

        # armoire
        if self.objet_porte is not None:
            # objet d'une livraison ratee encore en main : PRENDRE serait illegal
            return echec("robot deja charge", emotion, intensite)
        if not self.rejoindre(self.pos_armoire):
            return echec("armoire inaccessible", emotion, intensite)
        ligne, col = coordonnees_casier(emotion, intensite, self.dictionnaire)
        trouve = self.fouiller(generer_replis(ligne, col))
        if trouve is None:
            return echec("armoire vide", emotion, intensite)
        casier, repli, objet = trouve

        # resident
        if not self.rejoindre(self.residents[self.resident_courant]):
            return echec("resident inaccessible", emotion, intensite)
        self.faire_sur_place("DONNER", objet)
        self.trace.ajouter_livraison(
            demande=self.demande, resident=self.resident_courant, emotion=emotion,
            intensite=intensite, casier_choisi=casier, repli=repli, objet=objet,
            succes=True)


def main(argv):
    if len(argv) != 5:
        print("usage : python agent.py <carte> <scenario> <dossier_donnees> <trace_sortie>",
              file=sys.stderr)
        return 2
    chemin_carte, chemin_scenario = Path(argv[1]), Path(argv[2])
    dossier, sortie = Path(argv[3]), Path(argv[4])

    try:
        carte = rio.charger_carte(chemin_carte)
        scenario = rio.charger_scenario(chemin_scenario, carte)
        dictionnaire = rio.charger_dictionnaire(dossier / "dictionnaire.json")
        armoire = rio.charger_armoire(dossier / f"{scenario['armoire']}.json")
    except rio.ErreurFichier as err:
        print(f"erreur : {err}", file=sys.stderr)
        return 1

    monde = Monde(carte, armoire)
    trace = rio.Trace(carte["nom"], scenario["nom"], EQUIPE)
    agent = Agent(carte, dictionnaire, monde, trace)
    for demande in scenario["demandes"]:
        agent.traiter_demande(demande)
    trace.ecrire(sortie)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
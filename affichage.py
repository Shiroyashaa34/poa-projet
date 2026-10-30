"""
lancer: python affichage.py <carte.json> <trace.json> [demande] [secondes_par_pas]

A gauche la vraie carte, a droite la carte mentale du robot.
Ce script n'est pas l'agent : il a le droit de lire la grille.
"""

import json
import os
import sys
import time

DIRECTIONS = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "O": (0, -1)}
SYMBOLE = {"mur": "#", "libre": ".", "armoire": "A", "dictionnaire": "D", "resident": "P"}

PAUSE_MUR = 1.8
PAUSE_FIN = 3.0

def effacer_ecran():
    os.system("cls" if os.name == "nt" else "clear")

def carte_mentale_initiale(carte):
    """Ce que le robot sait au depart : les positions connues, rien d'autre."""
    #design: le robot connait les cibles (A, D, P) mais pas les murs.
    #c'est ce desequilibre qui rend la decouverte de mur impactante.
    h, w = carte["dimensions"]["hauteur"], carte["dimensions"]["largeur"]
    mentale = [["?"] * w for _ in range(h)]
    l, c = carte["depart_robot"]
    mentale[l][c] = "."
    for objet, symbole in (("armoire", "A"), ("dictionnaire", "D")):
        l, c = carte[objet]["position"]
        mentale[l][c] = symbole
    for r in carte["residents"]:
        l, c = r["position"]
        mentale[l][c] = "P"
    return mentale

def ajouter_perception(mentale, position, perception):
    """Met a jour la carte mentale, et renvoie les cases qui ont change."""
    changees = []
    for d, type_case in perception.items():
        l, c = position[0] + DIRECTIONS[d][0], position[1] + DIRECTIONS[d][1]
        if 0 <= l < len(mentale) and 0 <= c < len(mentale[0]):
            nouveau = SYMBOLE[type_case]
            if mentale[l][c] != nouveau:
                changees.append((l, c, nouveau))
            mentale[l][c] = nouveau
    return changees

def dessiner(carte, trace, mentale, pas, livraisons_faites, changees):
    l_robot, c_robot = pas["position"]
    print(f" {carte['nom']} — {trace['scenario']}")
    print(f" Demande {pas['demande']}    t = {pas['t']}\n")
    print(f" {'REALITE':<{len(carte['grille'][0]) + 6}}CARTE MENTALE DU ROBOT")
    for l, ligne in enumerate(carte["grille"]):
        reel = list(ligne.replace("R", "."))
        ment = list(mentale[l])
        if l == l_robot:
            reel[c_robot] = "█"
            ment[c_robot] = "█"
        print(" " + "".join(reel) + "      " + "".join(ment))

    action = pas["action"] + (f" {pas['argument']}" if pas["argument"] else "")
    print(f"\n Action  : {action}")
    print(f" Casier  : {pas['casier']}   contenu : {pas['contenu_casier'] or '-'}")
    print(" Vu      : " + "  ".join(f"{d} {v}" for d, v in pas["perception"].items()))

    if any(sym == "#" for _, _, sym in changees):
        print("\n  >>> Mur decouvert <<<")

    if livraisons_faites:
        print("\n Livraisons :")
        for liv in livraisons_faites:
            etat = liv["objet"] if liv["succes"] else "ECHEC (" + liv["motif_echec"] + ")"
            print(f"   {liv['demande']}. {liv['resident']} : {etat}")

def main(argv):
    if len(argv) not in (3, 4, 5):
        print(__doc__.strip())
        return 2
    with open(argv[1], encoding="utf-8") as f:
        carte = json.load(f)
    with open(argv[2], encoding="utf-8") as f:
        trace = json.load(f)
    demande = int(argv[3]) if len(argv) >= 4 else 1
    pause = float(argv[4]) if len(argv) == 5 else 1.0

    pas_demande = [p for p in trace["pas"] if p["demande"] == demande]
    if not pas_demande:
        print(f"aucun pas pour la demande {demande}")
        return 1

    mentale = carte_mentale_initiale(carte)
    nb_murs = 0
    for pas in trace["pas"]:
        changees = ajouter_perception(mentale, pas["position"], pas["perception"])
        if pas["demande"] != demande:
            continue    #demandes d'avant: le robot apprend, mais pas affiché
        nb_murs += sum(1 for _, _, sym in changees if sym == "#")

        effacer_ecran()
        dessiner(carte, trace, mentale, pas, [], changees)

        if any(sym == "#" for _, _, sym in changees):
            time.sleep(PAUSE_MUR)
        else:
            time.sleep(pause)

    #derniere image: livraison de cette demande
    livraison = [liv for liv in trace["livraisons"] if liv["demande"] == demande]
    effacer_ecran()
    dessiner(carte, trace, mentale, pas_demande[-1], livraison, [])
    if nb_murs == 0:
        print("\n (aucun mur decouvert pendant le trajet)")
    else:
        pluriel = "s" if nb_murs > 1 else ""
        print(f"\n ({nb_murs} mur{pluriel} decouvert{pluriel} pendant le trajet)")
    time.sleep(PAUSE_FIN)
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
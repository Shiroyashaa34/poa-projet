"""
Base de code fournie -- projet "Robot de reconfort".

Ce module fait DEUX choses, et rien d'autre :

  1. lire les quatre fichiers d'entree (carte, dictionnaire, armoire,
     scenario) ;
  2. construire et exporter le fichier de trace attendu a la sortie.

Tout le reste du projet -- perception, carte mentale, planification de
chemin, consultation du dictionnaire, fouille de l'armoire, boucle de
decision -- est a votre charge. Ne cherchez pas ces fonctions ici : elles
n'y sont pas, et c'est volontaire.

Vous avez le droit de modifier ce fichier. Vous avez surtout le devoir de
le comprendre : les verifications faites ici sont minimales (voir la
section "Ce qui n'est PAS verifie" plus bas), et les validations
manquantes font partie du travail demande.

Python 3.9+. Aucune dependance externe.
"""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

__all__ = [
    "ErreurFichier",
    "charger_carte",
    "charger_dictionnaire",
    "charger_armoire",
    "charger_scenario",
    "normaliser",
    "Trace",
]

VERSION_ATTENDUE = 1

EMOTIONS = (
    "joie",
    "confiance",
    "peur",
    "surprise",
    "tristesse",
    "degout",
    "colere",
    "anticipation",
)
INTENSITES = ("faible", "moyenne", "forte")
CASES_GRILLE = ("#", ".", "R", "A", "D", "P")

_derniere_carte: Optional[Dict[str, Any]] = None


class ErreurFichier(Exception):
    """Fichier d'entree absent, illisible, ou d'un type inattendu."""


# ---------------------------------------------------------------------------
# Lecture
# ---------------------------------------------------------------------------

def _lire_json(chemin: str | Path, format_attendu: str) -> Dict[str, Any]:
    """Lit un fichier JSON UTF-8 et verifie son en-tete.

    Ce qui EST verifie ici :
      - le fichier existe et se lit en UTF-8 ;
      - son contenu est du JSON valide ;
      - la racine est un objet ;
      - les champs "format" et "version" sont presents et corrects.

    Ce qui n'est PAS verifie (a vous de le faire, enonce section 5.6) :
      - la presence et le type de chacun des autres champs ;
      - la coherence des donnees (grille rectangulaire, positions dans les
        bornes, resident pose sur un mur, casier hors de l'armoire,
        emotion inconnue, resident cite par un scenario mais absent de la
        carte...).
    """
    chemin = Path(chemin)
    try:
        texte = chemin.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise ErreurFichier(f"fichier introuvable : {chemin}") from None
    except UnicodeDecodeError as err:
        raise ErreurFichier(
            f"{chemin} n'est pas encode en UTF-8 (octet {err.start})"
        ) from None
    except OSError as err:
        raise ErreurFichier(f"{chemin} illisible : {err}") from None

    try:
        donnees = json.loads(texte)
    except json.JSONDecodeError as err:
        raise ErreurFichier(
            f"{chemin} n'est pas un JSON valide : {err.msg} "
            f"(ligne {err.lineno}, colonne {err.colno})"
        ) from None

    if not isinstance(donnees, dict):
        raise ErreurFichier(
            f"{chemin} : la racine doit etre un objet JSON, "
            f"pas {type(donnees).__name__}"
        )

    format_trouve = donnees.get("format")
    if format_trouve != format_attendu:
        raise ErreurFichier(
            f"{chemin} : format attendu '{format_attendu}', "
            f"trouve {format_trouve!r}"
        )

    version = donnees.get("version")
    if version != VERSION_ATTENDUE:
        raise ErreurFichier(
            f"{chemin} : version {VERSION_ATTENDUE} attendue, trouve {version!r}"
        )

    return donnees


def _est_entier(valeur: Any) -> bool:
    return isinstance(valeur, int) and not isinstance(valeur, bool)


def _verifier_position(
    chemin: Path, pos: Any, hauteur: int, largeur: int, nom: str
) -> tuple[int, int]:
    if (
        not isinstance(pos, list)
        or len(pos) != 2
        or not _est_entier(pos[0])
        or not _est_entier(pos[1])
    ):
        raise ErreurFichier(f"{chemin} : position invalide pour {nom}")
    l, c = pos
    if not (0 <= l < hauteur and 0 <= c < largeur):
        raise ErreurFichier(f"{chemin} : {nom} hors des bornes ({l}, {c})")
    return l, c


def charger_carte(chemin: str | Path) -> Dict[str, Any]:
    """Charge un fichier carte. Voir l'enonce, section 5.1."""
    global _derniere_carte
    chemin = Path(chemin)
    donnees = _lire_json(chemin, "robot-reconfort/carte")

    if not isinstance(donnees.get("nom"), str) or not donnees["nom"]:
        raise ErreurFichier(f"{chemin} : champ 'nom' manquant ou invalide")

    dimensions = donnees.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ErreurFichier(f"{chemin} : champ 'dimensions' manquant ou invalide")
    hauteur = dimensions.get("hauteur")
    largeur = dimensions.get("largeur")
    if not (_est_entier(hauteur) and _est_entier(largeur) and hauteur > 0 and largeur > 0):
        raise ErreurFichier(f"{chemin} : dimensions invalides")

    grille = donnees.get("grille")
    if not isinstance(grille, list) or len(grille) != hauteur:
        raise ErreurFichier(f"{chemin} : la grille doit compter {hauteur} lignes")
    for ligne in grille:
        if not isinstance(ligne, str) or len(ligne) != largeur:
            raise ErreurFichier(f"{chemin} : la grille n'est pas rectangulaire")
        for car in ligne:
            if car not in CASES_GRILLE:
                raise ErreurFichier(f"{chemin} : caractere {car!r} inconnu dans la grille")

    rl, rc = _verifier_position(
        chemin, donnees.get("depart_robot"), hauteur, largeur, "depart_robot"
    )
    if grille[rl][rc] == "#":
        raise ErreurFichier(f"{chemin} : depart_robot pose sur un mur")

    for meuble in ("armoire", "dictionnaire"):
        bloc = donnees.get(meuble)
        if not isinstance(bloc, dict):
            raise ErreurFichier(f"{chemin} : champ {meuble!r} manquant ou invalide")
        ml, mc = _verifier_position(
            chemin, bloc.get("position"), hauteur, largeur, meuble
        )
        if grille[ml][mc] == "#":
            raise ErreurFichier(f"{chemin} : {meuble} pose sur un mur")

    residents = donnees.get("residents")
    if not isinstance(residents, list) or not residents:
        raise ErreurFichier(f"{chemin} : champ 'residents' manquant ou vide")
    ids_vus = set()
    for res in residents:
        if not isinstance(res, dict):
            raise ErreurFichier(f"{chemin} : resident invalide")
        res_id = res.get("id")
        if not isinstance(res_id, str) or not res_id:
            raise ErreurFichier(f"{chemin} : identifiant de resident invalide")
        if res_id in ids_vus:
            raise ErreurFichier(f"{chemin} : resident {res_id!r} en double")
        ids_vus.add(res_id)
        pl, pc = _verifier_position(
            chemin, res.get("position"), hauteur, largeur, f"resident {res_id}"
        )
        if grille[pl][pc] == "#":
            raise ErreurFichier(f"{chemin} : resident {res_id} pose sur un mur")

    _derniere_carte = donnees
    return donnees


def charger_dictionnaire(chemin: str | Path) -> Dict[str, Any]:
    """Charge un fichier dictionnaire. Voir l'enonce, section 5.2."""
    chemin = Path(chemin)
    donnees = _lire_json(chemin, "robot-reconfort/dictionnaire")

    if not isinstance(donnees.get("nom"), str) or not donnees["nom"]:
        raise ErreurFichier(f"{chemin} : champ 'nom' manquant ou invalide")
    if donnees.get("emotions") != list(EMOTIONS):
        raise ErreurFichier(f"{chemin} : liste 'emotions' invalide")
    if donnees.get("intensites") != list(INTENSITES):
        raise ErreurFichier(f"{chemin} : liste 'intensites' invalide")

    entrees = donnees.get("entrees")
    if not isinstance(entrees, list):
        raise ErreurFichier(f"{chemin} : champ 'entrees' manquant ou invalide")
    for entree in entrees:
        if not isinstance(entree, dict):
            raise ErreurFichier(f"{chemin} : entree invalide")
        formes = entree.get("formes")
        if (
            not isinstance(formes, list)
            or not formes
            or not all(isinstance(f, str) and f for f in formes)
        ):
            raise ErreurFichier(f"{chemin} : champ 'formes' invalide")
        if entree.get("emotion") not in EMOTIONS:
            raise ErreurFichier(f"{chemin} : emotion inconnue {entree.get('emotion')!r}")
        if entree.get("intensite") not in INTENSITES:
            raise ErreurFichier(f"{chemin} : intensite inconnue {entree.get('intensite')!r}")

    return donnees


def charger_armoire(chemin: str | Path) -> Dict[str, Any]:
    """Charge un fichier armoire. Voir l'enonce, section 5.3."""
    chemin = Path(chemin)
    donnees = _lire_json(chemin, "robot-reconfort/armoire")

    if not isinstance(donnees.get("nom"), str) or not donnees["nom"]:
        raise ErreurFichier(f"{chemin} : champ 'nom' manquant ou invalide")
    if donnees.get("emotions") != list(EMOTIONS):
        raise ErreurFichier(f"{chemin} : liste 'emotions' invalide")
    if donnees.get("intensites") != list(INTENSITES):
        raise ErreurFichier(f"{chemin} : liste 'intensites' invalide")

    _verifier_position(chemin, donnees.get("casier_depart"), 3, 8, "casier_depart")

    casiers = donnees.get("casiers")
    if not isinstance(casiers, list) or len(casiers) != 24:
        raise ErreurFichier(f"{chemin} : l'armoire doit contenir 24 casiers")

    casiers_vus = set()
    for casier in casiers:
        if not isinstance(casier, dict):
            raise ErreurFichier(f"{chemin} : casier invalide")
        l, c = casier.get("ligne"), casier.get("colonne")
        if not (_est_entier(l) and _est_entier(c) and 0 <= l < 3 and 0 <= c < 8):
            raise ErreurFichier(f"{chemin} : casier hors de l'armoire ({l}, {c})")
        if (l, c) in casiers_vus:
            raise ErreurFichier(f"{chemin} : casier ({l}, {c}) en double")
        casiers_vus.add((l, c))
        if casier.get("emotion") not in EMOTIONS:
            raise ErreurFichier(f"{chemin} : emotion inconnue {casier.get('emotion')!r}")
        if casier.get("intensite") not in INTENSITES:
            raise ErreurFichier(f"{chemin} : intensite inconnue {casier.get('intensite')!r}")
        if casier["emotion"] != EMOTIONS[c] or casier["intensite"] != INTENSITES[l]:
            raise ErreurFichier(f"{chemin} : casier ({l}, {c}) mal indexe")
        objet = casier.get("objet")
        if objet is not None and (not isinstance(objet, str) or not objet):
            raise ErreurFichier(f"{chemin} : objet invalide dans le casier ({l}, {c})")

    return donnees


def charger_scenario(
    chemin: str | Path, carte: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Charge un fichier scenario. Voir l'enonce, section 5.4."""
    chemin = Path(chemin)
    donnees = _lire_json(chemin, "robot-reconfort/scenario")

    for champ in ("nom", "carte", "armoire"):
        if not isinstance(donnees.get(champ), str) or not donnees[champ]:
            raise ErreurFichier(f"{chemin} : champ {champ!r} manquant ou invalide")

    demandes = donnees.get("demandes")
    if not isinstance(demandes, list):
        raise ErreurFichier(f"{chemin} : champ 'demandes' manquant ou invalide")

    cible_carte = carte if carte is not None else _derniere_carte
    residents_connus = (
        {r["id"] for r in cible_carte["residents"]}
        if cible_carte is not None
        else None
    )

    for dem in demandes:
        if not isinstance(dem, dict):
            raise ErreurFichier(f"{chemin} : demande invalide")
        if not _est_entier(dem.get("numero")):
            raise ErreurFichier(f"{chemin} : numero de demande invalide")
        res = dem.get("resident")
        if not isinstance(res, str) or not res:
            raise ErreurFichier(f"{chemin} : resident invalide dans une demande")
        if residents_connus is not None and res not in residents_connus:
            raise ErreurFichier(
                f"{chemin} : resident {res!r} absent de la carte"
            )
        if not isinstance(dem.get("message"), str):
            raise ErreurFichier(f"{chemin} : message invalide dans une demande")

    return donnees


# ---------------------------------------------------------------------------
# Normalisation des messages
# ---------------------------------------------------------------------------

def normaliser(texte: str) -> List[str]:
    """Decoupe un message en mots comparables au dictionnaire.

    Minuscules, accents retires, decoupage sur tout ce qui n'est pas une
    lettre. C'est exactement la regle de l'enonce, section 6.1 ;
    reimplementez-la vous-meme si vous travaillez dans un autre langage.

        >>> normaliser("Je suis TERRIFIEE, vraiment !")
        ['je', 'suis', 'terrifiee', 'vraiment']
    """
    decompose = unicodedata.normalize("NFD", texte.lower())
    sans_accents = "".join(
        c for c in decompose if unicodedata.category(c) != "Mn"
    )
    mots: List[str] = []
    courant: List[str] = []
    for caractere in sans_accents:
        if caractere.isalpha():
            courant.append(caractere)
        elif courant:
            mots.append("".join(courant))
            courant = []
    if courant:
        mots.append("".join(courant))
    return mots


# ---------------------------------------------------------------------------
# Ecriture de la trace
# ---------------------------------------------------------------------------

ACTIONS = ("AVANCER", "CONSULTER", "CHERCHER", "PRENDRE", "DONNER", "ATTENDRE")
DIRECTIONS = ("N", "S", "E", "O")
REPLIS = ("aucun", "intensite", "voisine_1", "voisine_2")


class Trace:
    """Accumule les pas et les livraisons, puis ecrit le fichier de sortie.

    Utilisation typique :

        trace = Trace(nom_carte="appartement_01",
                      nom_scenario="scenario_01",
                      equipe=["Dupont", "Martin"])
        ...
        trace.ajouter_pas(demande=1, position=(6, 1), casier=(1, 0),
                          action="AVANCER", argument="E",
                          perception={"N": "libre", "S": "mur",
                                      "E": "libre", "O": "mur"})
        ...
        trace.ajouter_livraison(demande=1, resident="R1",
                                emotion="tristesse", intensite="moyenne",
                                casier_choisi=(1, 4), repli="aucun",
                                objet="couverture", succes=True)
        trace.ecrire("sorties/trace_01.json")
    """

    def __init__(
        self,
        nom_carte: str,
        nom_scenario: str,
        equipe: Optional[Sequence[str]] = None,
    ) -> None:
        self.nom_carte = nom_carte
        self.nom_scenario = nom_scenario
        self.equipe: List[str] = list(equipe or [])
        self.pas: List[Dict[str, Any]] = []
        self.livraisons: List[Dict[str, Any]] = []

    # -- pas ---------------------------------------------------------------

    def ajouter_pas(
        self,
        demande: Optional[int],
        position: Sequence[int],
        casier: Sequence[int],
        action: str,
        argument: Optional[str] = None,
        perception: Optional[Dict[str, str]] = None,
        contenu_casier: Optional[str] = None,
        commentaire: Optional[str] = None,
    ) -> None:
        """Enregistre un pas de simulation.

        `position`  : couple (ligne, colonne) du robot AVANT l'action.
        `casier`    : couple (ligne, colonne) du selecteur dans l'armoire,
                      AVANT l'action.
        `perception`: ce que le robot voit depuis sa position, sous la forme
                      d'un dictionnaire des quatre directions vers "mur",
                      "libre", "armoire", "dictionnaire" ou "resident".
        `contenu_casier` : l'objet du casier courant, quand le robot est
                      devant l'armoire et peut donc le voir ; None sinon.
        """
        if action not in ACTIONS:
            raise ValueError(
                f"action inconnue {action!r} (attendu : {', '.join(ACTIONS)})"
            )
        if action in ("AVANCER", "CHERCHER") and argument not in DIRECTIONS:
            raise ValueError(
                f"{action} attend une direction parmi {DIRECTIONS}, "
                f"pas {argument!r}"
            )
        self.pas.append({
            "t": len(self.pas),
            "demande": demande,
            "position": [int(position[0]), int(position[1])],
            "casier": [int(casier[0]), int(casier[1])],
            "action": action,
            "argument": argument,
            "perception": dict(perception) if perception else None,
            "contenu_casier": contenu_casier,
            "commentaire": commentaire,
        })

    # -- livraisons --------------------------------------------------------

    def ajouter_livraison(
        self,
        demande: int,
        resident: str,
        emotion: Optional[str],
        intensite: Optional[str],
        casier_choisi: Optional[Sequence[int]],
        repli: str,
        objet: Optional[str],
        succes: bool,
        motif_echec: Optional[str] = None,
    ) -> None:
        """Enregistre l'issue d'une demande, reussie ou non.

        En cas d'echec, `succes` vaut False et `motif_echec` explique
        pourquoi en une chaine courte (par exemple "resident inaccessible",
        "armoire vide", "emotion indeterminee").
        """
        if repli not in REPLIS:
            raise ValueError(
                f"repli inconnu {repli!r} (attendu : {', '.join(REPLIS)})"
            )
        if not succes and not motif_echec:
            raise ValueError("un echec doit etre accompagne d'un motif_echec")
        self.livraisons.append({
            "demande": int(demande),
            "resident": resident,
            "emotion": emotion,
            "intensite": intensite,
            "casier_choisi": ([int(casier_choisi[0]), int(casier_choisi[1])]
                              if casier_choisi is not None else None),
            "repli": repli,
            "objet": objet,
            "pas_utilises": sum(1 for p in self.pas if p["demande"] == demande),
            "succes": bool(succes),
            "motif_echec": motif_echec,
        })

    # -- export ------------------------------------------------------------

    def en_dictionnaire(self) -> Dict[str, Any]:
        reussies = sum(1 for l in self.livraisons if l["succes"])
        return {
            "format": "robot-reconfort/trace",
            "version": VERSION_ATTENDUE,
            "carte": self.nom_carte,
            "scenario": self.nom_scenario,
            "equipe": self.equipe,
            "pas": self.pas,
            "livraisons": self.livraisons,
            "resume": {
                "demandes": len(self.livraisons),
                "reussies": reussies,
                "echecs": len(self.livraisons) - reussies,
                "pas_total": len(self.pas),
            },
        }

    def ecrire(self, chemin: str | Path) -> Path:
        """Ecrit la trace en JSON UTF-8 indente. Cree le dossier au besoin."""
        chemin = Path(chemin)
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(
            json.dumps(self.en_dictionnaire(), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        return chemin
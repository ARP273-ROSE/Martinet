"""Garde d'observatoire : un PC qui pilote un télescope ne se met pas à jour n'importe quand.

Sur un poste d'astrophotographie (N.I.N.A., PHD2, SharpCap, APT ou la plateforme
ASCOM installés), trois précautions :

* le passage automatique ne démarre pas pendant une acquisition (logiciel
  d'acquisition ou de guidage ouvert) ;
* ni pendant la plage de nuit (17:00-09:00 par défaut) : une tâche planifiée
  ratée (PC éteint) se rattrape au démarrage suivant, souvent en pleine nuit ;
* les pilotes proposés par Windows Update (USB-série de la monture, chipset…)
  ne partent jamais seuls : ils restent visibles et s'installent à la main,
  de jour, quand on peut vérifier que la monture et la caméra répondent encore.
"""
from __future__ import annotations

import datetime as dt
import re
from functools import lru_cache

from . import demo, systeme

# noms installés (registre) qui font d'un PC un poste d'observatoire
MOTIF_POSTE = re.compile(r"^(N\.I\.N\.A|Nighttime Imaging|PHD2|SharpCap|APT - Astro Photography|"
                         r"ASCOM Platform|Sequence Generator Pro|Voyager)", re.I)
# processus d'acquisition, de guidage ou de pilotage (noms d'exécutables, sans .exe)
PROCESSUS_ACQUISITION = frozenset({
    "nina", "phd2", "sharpcap", "apt", "sequencegenerator", "voyager2", "ascom.remoteserver",
})


def _heure(texte: str) -> dt.time:
    h, m = texte.strip().split(":")
    return dt.time(int(h), int(m))


def plage_valide(plage: str) -> bool:
    try:
        debut, fin = plage.split("-")
        _heure(debut), _heure(fin)
        return True
    except ValueError:
        return False


def dans_plage(maintenant: dt.time, plage: str) -> bool:
    """« 17:00-09:00 » : vrai de 17 h à 9 h (la plage peut passer minuit). Plage vide : jamais."""
    if not plage or not plage_valide(plage):
        return False
    debut, fin = (_heure(x) for x in plage.split("-"))
    if debut <= fin:
        return debut <= maintenant < fin
    return maintenant >= debut or maintenant < fin


@lru_cache(maxsize=1)
def poste_astro() -> bool:
    if demo.actif() or systeme.linux():
        return False
    from . import materiel
    try:
        return any(MOTIF_POSTE.search(nom) for nom, _v, _e in materiel.logiciels_du_registre())
    except OSError:
        return False


def active(reglages) -> bool:
    if reglages.garde_observatoire == "oui":
        return True
    if reglages.garde_observatoire == "non":
        return False
    return poste_astro()


def processus_en_cours() -> set[str]:
    """Noms (minuscules, sans .exe) des processus ouverts ; vide si on ne peut pas savoir."""
    if demo.actif() or systeme.linux():
        return set()
    code, sortie = systeme.executer(["tasklist", "/FO", "CSV", "/NH"], timeout=30)
    if code != 0:
        return set()
    noms = set()
    for ligne in sortie.splitlines():
        m = re.match(r'\s*"([^"]+)"', ligne)
        if m:
            noms.add(re.sub(r"\.exe$", "", m.group(1), flags=re.I).lower())
    return noms


def acquisition_en_cours(processus: set[str] | None = None) -> list[str]:
    processus = processus_en_cours() if processus is None else processus
    return sorted(processus & PROCESSUS_ACQUISITION)


def raison_de_reporter(reglages, maintenant: dt.datetime | None = None,
                       processus: set[str] | None = None) -> str | None:
    """Pourquoi le passage automatique attend (texte court), ou None s'il peut partir."""
    if not active(reglages):
        return None
    ouverts = acquisition_en_cours(processus)
    if ouverts:
        return "acquisition:" + ", ".join(ouverts)
    maintenant = maintenant or dt.datetime.now()
    if dans_plage(maintenant.time(), reglages.plage_nuit):
        return "nuit:" + reglages.plage_nuit
    return None


def windows_voulues(liste, reglages) -> list:
    """Mises à jour Windows qui partent d'elles-mêmes (passage auto et « tout mettre à jour »)."""
    garde = active(reglages)
    return [m for m in liste
            if (reglages.facultatives or not m.facultatif) and not (garde and m.pilote)]


def pilotes_retenus(liste, reglages) -> list:
    if not active(reglages):
        return []
    return [m for m in liste if m.pilote and (reglages.facultatives or not m.facultatif)]

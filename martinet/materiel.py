"""Ce que dit le registre : logiciels installés et cartes graphiques.

Lecture seule, par winreg (aucune commande lancée). Sert de repli quand
winget est absent, et à connaître la carte graphique et son pilote.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import demo
from .versions import nvidia_lisible

CLASSE_AFFICHAGE = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
DESINSTALLATION = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
FABRICANTS = {"10de": "nvidia", "1002": "amd", "8086": "intel"}


@dataclass
class Carte:
    nom: str
    fabricant: str           # nvidia, amd, intel, autre
    id_peripherique: str     # « 2786 »
    version_windows: str     # « 32.0.15.7680 »
    date: str = ""
    version_logiciel: str = ""   # AMD : version d'Adrenalin (« 26.10.1 »)
    processeur: str = ""         # nom du processeur (graphismes intégrés)

    @property
    def version(self) -> str:
        if self.fabricant == "nvidia":
            return nvidia_lisible(self.version_windows) or self.version_windows
        return self.version_logiciel or self.version_windows


def _valeur(cle, nom, defaut=""):
    import winreg
    try:
        return winreg.QueryValueEx(cle, nom)[0]
    except OSError:
        return defaut


def cartes_graphiques() -> list[Carte]:
    if demo.actif():
        return [Carte(**c) for c in demo.CARTES]
    import re
    import winreg
    cartes = []
    try:
        racine = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, CLASSE_AFFICHAGE)
    except OSError:
        return cartes
    i = 0
    while True:
        try:
            nom_cle = winreg.EnumKey(racine, i)
        except OSError:
            break
        i += 1
        if not nom_cle.isdigit():
            continue
        try:
            cle = winreg.OpenKey(racine, nom_cle)
        except OSError:
            continue
        ident = str(_valeur(cle, "MatchingDeviceId")).lower()
        m = re.search(r"ven_([0-9a-f]{4}).*?dev_([0-9a-f]{4})", ident)
        if not m:
            continue
        cartes.append(Carte(nom=str(_valeur(cle, "DriverDesc")),
                            fabricant=FABRICANTS.get(m.group(1), "autre"),
                            id_peripherique=m.group(2).upper(),
                            version_windows=str(_valeur(cle, "DriverVersion")),
                            date=str(_valeur(cle, "DriverDate")),
                            version_logiciel=str(_valeur(cle, "RadeonSoftwareVersion")),
                            processeur=processeur()))
    # une même carte peut apparaître plusieurs fois (anciennes entrées)
    vues, uniques = set(), []
    for c in cartes:
        if (c.id_peripherique, c.version_windows) not in vues:
            vues.add((c.id_peripherique, c.version_windows))
            uniques.append(c)
    return uniques


def processeur() -> str:
    """« AMD Ryzen 7 5700G with Radeon Graphics » : sert aux graphismes intégrés."""
    if demo.actif():
        return demo.PROCESSEUR
    import winreg
    try:
        cle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
    except OSError:
        return ""
    return " ".join(str(_valeur(cle, "ProcessorNameString")).split())


def logiciels_du_registre() -> list[tuple[str, str, str]]:
    """(nom, version, éditeur) des programmes de « Ajouter ou supprimer »."""
    if demo.actif():
        return [(n, v, "") for _, n, v, _, _ in demo.PAQUETS]
    import winreg
    vus: dict[str, tuple[str, str, str]] = {}
    emplacements = [(winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_64KEY),
                    (winreg.HKEY_LOCAL_MACHINE, winreg.KEY_WOW64_32KEY),
                    (winreg.HKEY_CURRENT_USER, 0)]
    for ruche, vue in emplacements:
        try:
            racine = winreg.OpenKey(ruche, DESINSTALLATION, 0, winreg.KEY_READ | vue)
        except OSError:
            continue
        i = 0
        while True:
            try:
                sous = winreg.EnumKey(racine, i)
            except OSError:
                break
            i += 1
            try:
                cle = winreg.OpenKey(racine, sous)
            except OSError:
                continue
            nom = str(_valeur(cle, "DisplayName")).strip()
            if (not nom or _valeur(cle, "SystemComponent", 0) == 1
                    or _valeur(cle, "ParentKeyName") or _valeur(cle, "ReleaseType")):
                continue
            vus.setdefault(nom.lower(), (nom, str(_valeur(cle, "DisplayVersion")),
                                         str(_valeur(cle, "Publisher"))))
    return sorted(vus.values(), key=lambda t: t[0].lower())

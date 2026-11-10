"""Ménage sûr : ce que Windows sait recréer, rien d'autre.

Pas de « nettoyage du registre » (aucun gain mesurable, risque réel), pas
de cache de navigateur (il se reremplit aussitôt, et l'on perd du temps de
chargement). Chaque élément se mesure avant d'être nettoyé ; un fichier en
cours d'utilisation est simplement laissé en place.
"""
from __future__ import annotations

import ctypes
import os

import time
from dataclasses import dataclass
from pathlib import Path

from . import demo, systeme

AGE_MINI_JOURS = 7


@dataclass
class Element:
    cle: str
    coche: bool             # coché d'office
    admin: bool             # demande les droits administrateur
    taille: int | None = None
    nombre: int | None = None


ELEMENTS = [
    Element("temp_utilisateur", True, False),
    Element("temp_windows", True, True),
    Element("rapports_erreurs", True, False),
    Element("optimisation_distribution", True, True),
    Element("telechargements_martinet", True, False),
    Element("composants", False, True),
    Element("corbeille", False, False),
]


def _env(nom: str, defaut: str) -> Path:
    return Path(os.environ.get(nom, defaut))


def dossiers(cle: str) -> list[Path]:
    racine = _env("SystemRoot", r"C:\Windows")
    if cle == "temp_utilisateur":
        return [_env("TEMP", str(Path.home() / "AppData" / "Local" / "Temp"))]
    if cle == "temp_windows":
        return [racine / "Temp"]
    if cle == "rapports_erreurs":
        pd = _env("ProgramData", r"C:\ProgramData") / "Microsoft" / "Windows" / "WER"
        local = _env("LOCALAPPDATA", "") / "Microsoft" / "Windows" / "WER"
        return [pd / "ReportArchive", pd / "ReportQueue", local / "ReportArchive", local / "ReportQueue"]
    if cle == "optimisation_distribution":
        return [racine / "ServiceProfiles" / "NetworkService" / "AppData" / "Local" / "Microsoft"
                / "Windows" / "DeliveryOptimization" / "Cache"]
    if cle == "telechargements_martinet":
        return [systeme.dossier_donnees() / "telechargements"]
    return []


def _fichiers(cle: str):
    limite = time.time() - AGE_MINI_JOURS * 86400 if cle.startswith("temp_") else None
    for d in dossiers(cle):
        try:
            if not d.is_dir():
                continue
        except OSError:                      # dossier d'un compte système, sans droit de lecture
            continue
        for racine, _sous, noms in os.walk(d, onerror=lambda e: None):
            for n in noms:
                f = Path(racine) / n
                try:
                    st = f.stat()
                except OSError:
                    continue
                if limite is not None and st.st_mtime > limite:
                    continue
                yield f, st.st_size


# ------------------------------------------------------------ corbeille
class _InfoCorbeille(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_ulong), ("i64Size", ctypes.c_longlong),
                ("i64NumItems", ctypes.c_longlong)]


def _corbeille() -> tuple[int, int]:
    info = _InfoCorbeille()
    info.cbSize = ctypes.sizeof(info)
    if ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info)) != 0:
        return 0, 0
    return int(info.i64Size), int(info.i64NumItems)


# ------------------------------------------------------------ mesurer / nettoyer
def mesurer(cle: str) -> tuple[int | None, int | None]:
    if demo.actif():
        demo.pause(0.1)
        return demo.MENAGE[cle]
    if cle == "composants":
        return None, None                    # inconnu avant nettoyage (DISM)
    if cle == "corbeille":
        return _corbeille()
    taille = nombre = 0
    for _f, t in _fichiers(cle):
        taille += t
        nombre += 1
    return taille, nombre


def nettoyer(cle: str, journal=None) -> int:
    """Nettoie un élément ; renvoie les octets libérés (estimation)."""
    if demo.actif():
        demo.pause(0.3)
        t = demo.MENAGE[cle][0]
        return t or 0
    if cle == "composants":
        avant = systeme.espace_libre()
        code, sortie = systeme.executer_flux(
            ["Dism.exe", "/Online", "/Cleanup-Image", "/StartComponentCleanup"], journal, timeout=7200)
        return max(0, systeme.espace_libre() - avant)
    if cle == "corbeille":
        taille, _ = _corbeille()
        # SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x7)
        return taille
    if cle == "optimisation_distribution":
        avant = mesurer(cle)[0] or 0
        systeme.powershell("Delete-DeliveryOptimizationCache -Force", timeout=600)
        return max(0, avant - (mesurer(cle)[0] or 0))
    libere = 0
    for f, t in list(_fichiers(cle)):
        try:
            f.unlink()
            libere += t
        except OSError:
            continue                          # en cours d'utilisation
    # dossiers vidés (jamais la racine)
    for d in dossiers(cle):
        if d.is_dir():
            for racine, sous, _ in os.walk(d, topdown=False):
                for s in sous:
                    try:
                        (Path(racine) / s).rmdir()
                    except OSError:
                        pass
    return libere


def taille_lisible(octets: int | None, unites=("o", "Ko", "Mo", "Go", "To")) -> str:
    if octets is None:
        return "?"
    v = float(octets)
    for u in unites:
        if v < 1024 or u == unites[-1]:
            return f"{v:.0f} {u}" if u in unites[:2] else f"{v:.1f} {u}".replace(".", ",")
        v /= 1024
    return ""




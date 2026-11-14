"""Ménage sûr : ce que Windows sait recréer, rien d'autre.

Pas de « nettoyage du registre » (aucun gain mesurable, risque réel). Les
caches de navigateur et de shaders sont proposés mais jamais cochés d'office :
ils se reremplissent aussitôt (pages plus lentes, saccades en jeu le temps de
recompiler). Chaque élément se mesure avant d'être nettoyé ; un fichier en
cours d'utilisation est simplement laissé en place.
"""
from __future__ import annotations

import ctypes
import fnmatch
import glob
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


ELEMENTS_WINDOWS = [
    Element("temp_utilisateur", True, False),
    Element("temp_windows", True, True),
    Element("rapports_erreurs", True, False),
    Element("optimisation_distribution", True, True),
    Element("telechargements_martinet", True, False),
    Element("vidages_memoire", True, True),
    Element("journaux_windows", True, True),
    Element("restes_nvidia", True, True),
    Element("miniatures", False, False),
    Element("caches_navigateurs", False, False),
    Element("caches_shaders", False, False),
    Element("composants", False, True),
    Element("corbeille", False, False),
]


ELEMENTS = ELEMENTS_WINDOWS          # compatibilité : utiliser elements()

ELEMENTS_LINUX = [
    Element("cache_paquets", True, True),
    Element("cache_desinstalles", True, True),
    Element("fichiers_construction", True, False),
    Element("flatpak_inutilises", True, False),
    Element("miniatures", False, False),
    Element("journaux_systeme", False, True),
    Element("vidages_systeme", False, True),
    Element("corbeille", False, False),
]


def elements() -> list[Element]:
    """Les éléments du système en cours (Windows ou Linux)."""
    return ELEMENTS_LINUX if systeme.linux() else ELEMENTS_WINDOWS


def nettoyer_tout(cles: list[str], journal=None) -> int:
    """Plusieurs éléments d'un coup : sous Linux, une seule demande de mot de passe."""
    if systeme.linux():
        from . import menage_linux
        return menage_linux.nettoyer_tout(cles, journal)
    total = 0
    for c in cles:
        try:
            total += nettoyer(c, journal)
        except OSError as exc:
            if journal:
                journal(f"{c} : {exc}")
    return total


#: éléments où seuls les fichiers de plus de AGE_MINI_JOURS sont pris
AVEC_AGE = {"temp_utilisateur", "temp_windows", "journaux_windows"}
#: éléments limités à certains noms de fichiers (le dossier contient autre chose)
FILTRES = {"miniatures": ("thumbcache_*.db",)}
#: navigateurs dont on ne touche pas le cache tant qu'ils sont ouverts
PROCESSUS_NAVIGATEURS = ("chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "vivaldi.exe")


def _env(nom: str, defaut: str) -> Path:
    return Path(os.environ.get(nom, defaut))


def _globs(*motifs: Path) -> list[Path]:
    return [Path(p) for m in motifs for p in sorted(glob.glob(str(m)))]


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
    local = _env("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))
    if cle == "vidages_memoire":
        return [racine / "MEMORY.DMP", racine / "Minidump", racine / "LiveKernelReports", local / "CrashDumps"]
    if cle == "journaux_windows":
        return [racine / "Logs" / "CBS", racine / "Logs" / "DISM", racine / "Logs" / "WindowsUpdate",
                racine / "Panther"]
    if cle == "restes_nvidia":
        pd = _env("ProgramData", r"C:\ProgramData")
        lecteur = Path(os.environ.get("SystemDrive", "C:") + "\\")
        return [lecteur / "NVIDIA", lecteur / "AMD", pd / "NVIDIA Corporation" / "Downloader"]
    if cle == "miniatures":
        return [local / "Microsoft" / "Windows" / "Explorer"]
    if cle == "caches_navigateurs":
        chromium = [local / "Google" / "Chrome" / "User Data", local / "Microsoft" / "Edge" / "User Data",
                    local / "BraveSoftware" / "Brave-Browser" / "User Data"]
        caches = []
        for ud in chromium:
            for sous in ("Cache", "Code Cache", "GPUCache"):
                caches += _globs(ud / "*" / sous)
        return caches + _globs(local / "Mozilla" / "Firefox" / "Profiles" / "*" / "cache2")
    if cle == "caches_shaders":
        return [local / "D3DSCache", local / "NVIDIA" / "DXCache", local / "NVIDIA" / "GLCache",
                local / "AMD" / "DxCache", local / "AMD" / "DxcCache"]
    return []


def _fichiers(cle: str):
    limite = time.time() - AGE_MINI_JOURS * 86400 if cle in AVEC_AGE else None
    filtres = FILTRES.get(cle)
    for d in dossiers(cle):
        try:
            if d.is_file():                  # fichier isolé (MEMORY.DMP)
                st = d.stat()
                if limite is None or st.st_mtime <= limite:
                    yield d, st.st_size
                continue
            if not d.is_dir():
                continue
        except OSError:                      # dossier d'un compte système, sans droit de lecture
            continue
        for racine, sous, noms in os.walk(d, onerror=lambda e: None):
            if filtres:
                sous[:] = []                 # pas de descente : seuls les fichiers visés
            for n in noms:
                if filtres and not any(fnmatch.fnmatch(n.lower(), m) for m in filtres):
                    continue
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
    if systeme.linux():
        from . import menage_linux
        return menage_linux.mesurer(cle)
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
    if cle == "caches_navigateurs" and (ouverts := navigateurs_ouverts()):
        if journal:
            journal(f"{', '.join(ouverts)} : ouvert(s), cache laissé en place")
        return 0
    libere = 0
    for f, t in list(_fichiers(cle)):
        try:
            f.unlink()
            libere += t
        except OSError:
            continue                          # en cours d'utilisation
    # dossiers vidés (jamais la racine)
    if cle in FILTRES:
        return libere
    for d in dossiers(cle):
        if d.is_dir():
            for racine, sous, _ in os.walk(d, topdown=False):
                for s in sous:
                    try:
                        (Path(racine) / s).rmdir()
                    except OSError:
                        pass
    return libere


def navigateurs_ouverts() -> list[str]:
    code, sortie = systeme.executer(["tasklist", "/fo", "csv", "/nh"], timeout=30)
    if code != 0:
        return list(PROCESSUS_NAVIGATEURS)          # dans le doute, on ne touche à rien
    vus = {l.split(",")[0].strip('"').lower() for l in sortie.splitlines() if l.strip()}
    return [p for p in PROCESSUS_NAVIGATEURS if p in vus]


def taille_lisible(octets: int | None, unites=None) -> str:
    """« 1,5 Go » en français, « 1.5 GB » en anglais."""
    from .i18n import langue
    if octets is None:
        return "?"
    francais = langue() == "fr"
    unites = unites or (("o", "Ko", "Mo", "Go", "To") if francais else ("B", "KB", "MB", "GB", "TB"))
    v = float(octets)
    for u in unites:
        if v < 1024 or u == unites[-1]:
            if u in unites[:2]:
                return f"{v:.0f} {u}"
            texte = f"{v:.1f} {u}"
            return texte.replace(".", ",") if francais else texte
        v /= 1024
    return ""




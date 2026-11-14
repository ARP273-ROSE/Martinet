"""Accès au système : commandes, PowerShell, droits, réseau, dossiers.

Tout ce qui touche Windows passe par ici, pour que le reste du programme
reste testable ailleurs (mode démonstration, voir demo.py).
"""
from __future__ import annotations

import base64
import html
import json
import os
import re
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

NOM = "Martinet"
WINDOWS = sys.platform == "win32"


def cible() -> str:
    """« windows », « linux » ou « autre » ; MARTINET_SYSTEME l'impose (essais, captures)."""
    force = os.environ.get("MARTINET_SYSTEME", "")
    if force in ("windows", "linux"):
        return force
    if WINDOWS:
        return "windows"
    return "linux" if sys.platform.startswith("linux") else "autre"


def linux() -> bool:
    return cible() == "linux"


def windows10() -> bool:
    """Windows 10 (numéro de build inférieur à 22000) ; MARTINET_WINDOWS10=1 l'imite pour les essais."""
    if os.environ.get("MARTINET_WINDOWS10") == "1":
        return True
    if not WINDOWS:
        return False
    try:
        return sys.getwindowsversion().build < 22000
    except AttributeError:
        return False


#: fin de l'extension ESU grand public de Windows 10 (prolongée d'un an par Microsoft en juin 2026)
FIN_ESU_WINDOWS10 = "2027-10-12"


def windows10_esu(aujourd_hui=None) -> bool:
    """Windows 10 reçoit-il encore des correctifs (PC inscrit à l'ESU) ?"""
    import datetime
    jour = aujourd_hui or datetime.date.today()
    return jour <= datetime.date.fromisoformat(FIN_ESU_WINDOWS10)


def outil(nom: str) -> str | None:
    """Chemin d'une commande, ou None si elle n'est pas installée."""
    import shutil
    return shutil.which(nom)


#: sorties de pacman, paccache, journalctl… lisibles quelle que soit la langue du système
ENV_C = {"LC_ALL": "C", "LANG": "C"}
SANS_FENETRE = 0x08000000 if WINDOWS else 0          # CREATE_NO_WINDOW
AGENT = "Martinet (logiciel libre de mise a jour)"


class Annule(Exception):
    """L'utilisateur a interrompu l'opération."""


# ---------------------------------------------------------------- dossiers
def dossier_donnees() -> Path:
    """Données hors du dossier d'installation : elles survivent aux mises à jour."""
    ici = Path(__file__).resolve().parent.parent
    python = ici.parent / "python"
    installe = (python / "python.exe").exists() or (python / "bin" / "python3").exists()
    if os.environ.get("MARTINET_DONNEES"):
        base = Path(os.environ["MARTINET_DONNEES"])
    elif not installe:
        base = ici / "_donnees"
    elif WINDOWS:
        base = Path(os.environ.get("LOCALAPPDATA", Path.home())) / NOM
    else:
        base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / NOM
    try:
        base.mkdir(parents=True, exist_ok=True)
    except OSError:
        base = Path.home()
    return base


def sous_dossier(nom: str) -> Path:
    d = dossier_donnees() / nom
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- droits
def est_admin() -> bool:
    if not WINDOWS:
        return os.environ.get("MARTINET_DEMO_ADMIN", "1") == "1"
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relancer_en_admin(arguments: list[str]) -> bool:
    """Relance le programme avec élévation (fenêtre UAC). True si accepté."""
    if not WINDOWS:
        return False
    import ctypes
    exe = executable_fenetre()
    script = str(Path(__file__).resolve().parent.parent / "run.py")
    params = subprocess.list2cmdline([script, *arguments])
    r = ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, None, 1)
    return r > 32


def executable_fenetre() -> str:
    """pythonw.exe à côté de python.exe : aucune console qui s'ouvre."""
    exe = Path(sys.executable)
    if WINDOWS:
        w = exe.with_name("pythonw.exe")
        if w.exists():
            return str(w)
    return str(exe)


# ---------------------------------------------------------------- commandes
def _decoder(octets: bytes) -> str:
    for codec in ("utf-8", "cp850", "cp1252"):
        try:
            return octets.decode(codec)
        except UnicodeDecodeError:
            continue
    return octets.decode("utf-8", errors="replace")


_CLIXML_S = re.compile(r'<S S="(?:Error|Warning)">(.*?)</S>', re.S)


def _dechiffrer_xml(t: str) -> str:
    t = re.sub(r"_x([0-9A-Fa-f]{4})_", lambda m: chr(int(m.group(1), 16)), t)
    return html.unescape(t)


def clixml_lisible(texte: str) -> str:
    """Remplace les erreurs PowerShell sérialisées (« #< CLIXML ») par leur texte."""
    if "CLIXML" not in texte and "<Objs" not in texte:
        return texte

    def bloc(m: re.Match) -> str:
        morceaux = [_dechiffrer_xml(x) for x in _CLIXML_S.findall(m.group(0))]
        return " ".join(" ".join(morceaux).split())

    texte = re.sub(r"<Objs\b.*?(?:</Objs>|$)", bloc, texte, flags=re.S)
    return "\n".join(l for l in texte.splitlines() if l.strip() != "#< CLIXML")


def executer(cmd: list[str], timeout: float | None = 600, env: dict | None = None) -> tuple[int, str]:
    """Lance une commande sans fenêtre et renvoie (code, sortie + erreurs)."""
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=timeout,
                           creationflags=SANS_FENETRE, stdin=subprocess.DEVNULL,
                           env={**os.environ, **env} if env else None)
    except FileNotFoundError:
        return 127, f"introuvable : {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "délai dépassé"
    return r.returncode, _decoder(r.stdout) + clixml_lisible(_decoder(r.stderr))


def nettoyer_ligne(ligne: str) -> str:
    """Retire les animations de progression (winget redessine sa ligne avec \\r).

    Le \\r final d'une fin de ligne CRLF (PowerShell) n'est pas une animation :
    il est retiré avant de garder le dernier morceau redessiné."""
    morceau = ligne.rstrip("\r").split("\r")[-1].rstrip()
    if morceau.strip() in {"-", "\\", "|", "/"}:
        return ""
    # barres de progression faites de blocs
    if morceau and set(morceau.strip()) <= set("█▒░▓ ") :
        return ""
    return morceau


def executer_flux(cmd: list[str], ligne_cb=None, annulation: threading.Event | None = None,
                  timeout: float | None = 7200, env: dict | None = None) -> tuple[int, str]:
    """Comme executer(), en transmettant chaque ligne au fil de l'eau."""
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                stdin=subprocess.DEVNULL, creationflags=SANS_FENETRE,
                                env={**os.environ, **env} if env else None)
    except FileNotFoundError:
        return 127, f"introuvable : {cmd[0]}"
    lignes: list[str] = []
    tampon = b""
    assert proc.stdout is not None
    while True:
        if annulation is not None and annulation.is_set():
            proc.kill()
            raise Annule()
        bloc = proc.stdout.read1(4096) if hasattr(proc.stdout, "read1") else proc.stdout.read(4096)
        if not bloc:
            break
        tampon += bloc
        while b"\n" in tampon:
            brut, tampon = tampon.split(b"\n", 1)
            ligne = clixml_lisible(nettoyer_ligne(_decoder(brut)))
            if ligne:
                lignes.append(ligne)
                if ligne_cb:
                    ligne_cb(ligne)
    if tampon:
        ligne = clixml_lisible(nettoyer_ligne(_decoder(tampon)))
        if ligne:
            lignes.append(ligne)
            if ligne_cb:
                ligne_cb(ligne)
    try:
        code = proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        code = 124
    return code, "\n".join(lignes)


PROLOGUE_PS = ("$ProgressPreference='SilentlyContinue';"
               "[Console]::OutputEncoding=[Text.Encoding]::UTF8;"
               "$OutputEncoding=[Text.Encoding]::UTF8;")


def commande_powershell(script: str) -> list[str]:
    code = base64.b64encode((PROLOGUE_PS + script).encode("utf-16-le")).decode("ascii")
    return ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-EncodedCommand", code]


def powershell(script: str, timeout: float | None = 600) -> tuple[int, str]:
    return executer(commande_powershell(script), timeout=timeout)


def powershell_flux(script: str, ligne_cb=None, annulation=None, timeout=7200) -> tuple[int, str]:
    return executer_flux(commande_powershell(script), ligne_cb, annulation, timeout)


def json_de_sortie(texte: str):
    """Dernier document JSON d'une sortie PowerShell (marqué par ###JSON###)."""
    if "###JSON###" in texte:
        texte = texte.rsplit("###JSON###", 1)[1]
    texte = texte.strip()
    if not texte:
        return None
    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        return None


def en_liste(valeur) -> list:
    """ConvertTo-Json rend un objet seul au lieu d'une liste d'un élément."""
    if valeur is None:
        return []
    return valeur if isinstance(valeur, list) else [valeur]


# ---------------------------------------------------------------- réseau
def telecharger_texte(url: str, timeout: float = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": AGENT,
                                               "Accept": "application/json, text/html;q=0.9, */*;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return _decoder(r.read())


def telecharger_json(url: str, timeout: float = 20):
    return json.loads(telecharger_texte(url, timeout))


def telecharger_fichier(url: str, destination: Path, progression=None,
                        annulation: threading.Event | None = None) -> Path:
    """Téléchargement en HTTPS seulement, écrit d'abord dans un .part."""
    if not url.lower().startswith("https://"):
        raise ValueError("adresse non sécurisée refusée")
    destination.parent.mkdir(parents=True, exist_ok=True)
    partiel = destination.with_suffix(destination.suffix + ".part")
    entetes = {"User-Agent": AGENT}
    if "drivers.amd.com" in url.lower():
        # sans page d'origine, AMD renvoie vers une page « téléchargement incomplet »
        entetes["Referer"] = "https://www.amd.com/"
    req = urllib.request.Request(url, headers=entetes)
    with urllib.request.urlopen(req, timeout=60) as r, open(partiel, "wb") as f:
        if "text/html" in (r.headers.get("Content-Type") or "").lower():
            raise ValueError(f"page web reçue au lieu de l'installeur : {r.geturl()[:120]}")
        total = int(r.headers.get("Content-Length") or 0)
        lu = 0
        while True:
            if annulation is not None and annulation.is_set():
                f.close()
                partiel.unlink(missing_ok=True)
                raise Annule()
            bloc = r.read(1 << 16)
            if not bloc:
                break
            f.write(bloc)
            lu += len(bloc)
            if progression:
                progression(lu, total)
    os.replace(partiel, destination)
    return destination


# ---------------------------------------------------------------- ouvrir
def ouvrir(cible: str) -> None:
    """Ouvre une adresse ou un dossier avec le programme par défaut."""
    from PyQt6.QtCore import QUrl
    from PyQt6.QtGui import QDesktopServices
    url = QUrl(cible) if "://" in cible else QUrl.fromLocalFile(cible)
    QDesktopServices.openUrl(url)


def lancer_installeur(chemin: Path, arguments: list[str] | None = None) -> int | None:
    """Lance un installeur téléchargé et attend sa fin quand c'est possible.

    Si Martinet a déjà les droits administrateur, l'installeur en hérite et
    on attend son code de sortie ; sinon Windows demande l'élévation à
    l'installeur lui-même (ShellExecute) et on ne peut pas attendre.
    """
    arguments = arguments or []
    if not WINDOWS:
        return None
    if est_admin():
        r = subprocess.run([str(chemin), *arguments], creationflags=0)
        return r.returncode
    os.startfile(str(chemin), "open", subprocess.list2cmdline(arguments))  # type: ignore[attr-defined]
    return None


def redemarrage_en_attente() -> bool:
    if linux():
        from . import demo
        if demo.actif():
            return False
        # le noyau en marche a été remplacé : ses modules ont disparu du disque
        return not Path("/usr/lib/modules", os.uname().release).is_dir()
    if not WINDOWS:
        return False
    import winreg
    cles = [r"SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending",
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired"]
    for c in cles:
        try:
            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, c))
            return True
        except OSError:
            continue
    return False


def espace_libre(lecteur: str | None = None) -> int:
    import shutil
    lecteur = lecteur or (os.environ.get("SystemDrive", "C:") + "\\" if WINDOWS else "/")
    try:
        return shutil.disk_usage(lecteur).free
    except OSError:
        return 0

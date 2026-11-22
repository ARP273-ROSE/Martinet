"""Linux : vos applications publiées sur GitHub (paquets du kit, installés par installer.sh).

Chacune vit dans ~/.local/share/<nom>/ et y garde sa fiche app/kit.json
(dépôt GitHub, nom des fichiers) et sa version (app/VERSION). Martinet les
retrouve seul, compare à la dernière Release, et met à jour par le chemin
officiel : l'archive Linux publiée, vérifiée par SHA256SUMS, puis son
installer.sh — le même geste qu'une installation à la main, sans sudo. Les
réglages de chaque application vivent ailleurs et ne sont jamais touchés.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import demo, systeme
from .i18n import tr
from .versions import plus_recente

API = "https://api.github.com/repos/{depot}/releases/latest"


@dataclass
class Appli:
    nom: str                  # nom affiché
    tech: str                 # nom technique (dossier ~/.local/share/<tech>)
    fichier: str              # nom des fichiers publiés (« Coupole »)
    depot: str                # « proprietaire/depot »
    dossier: str
    installee: str
    derniere: str = ""
    archive: str = ""         # lien de l'archive Linux de la dernière version
    sommes: str = ""          # lien de SHA256SUMS
    etat: str = "inconnu"     # a_jour, maj, erreur, inconnu
    erreur: str = ""
    genre: str = "kit"        # kit (installer.sh) ou appimage (un seul fichier remplacé)


#: AppImages connues : début du nom de fichier → dépôt GitHub qui les publie.
APPIMAGES = {"PerceNeigeSimulator": "ARP273-ROSE/perce-neige-sim"}


def _dossiers_appimages() -> list[Path]:
    maison = Path.home()
    return [maison / "Applications", maison / ".local" / "bin", maison / "AppImages"]


def _versions_appimages() -> Path:
    return systeme.dossier_donnees() / "appimages.json"


def _lire_versions() -> dict:
    try:
        return json.loads(_versions_appimages().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _noter_version(chemin: str, version: str) -> None:
    v = _lire_versions()
    v[chemin] = version
    try:
        f = _versions_appimages()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(v, indent=1, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def trouver_appimages() -> list[Appli]:
    """AppImages connues posées à la main. Leur version n'est pas lisible dans le fichier :
    Martinet retient celle qu'il a installée ; inconnue la première fois, donc remplacée
    une fois par la dernière Release, puis suivie."""
    connues = _lire_versions()
    presentes = {k: v for k, v in connues.items() if Path(k).is_file()}
    if presentes != connues:                  # AppImage supprimée : on l'oublie
        try:
            _versions_appimages().write_text(json.dumps(presentes, indent=1, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass
    applis, vus = [], set()
    for d in _dossiers_appimages():
        try:
            fichiers = sorted(d.glob("*.AppImage"))
        except OSError:
            continue
        for f in fichiers:
            for prefixe, depot in APPIMAGES.items():
                if f.name.startswith(prefixe) and str(f) not in vus and f.is_file() and not f.is_symlink():
                    vus.add(str(f))
                    applis.append(Appli(prefixe, prefixe.lower(), prefixe, depot, str(f),
                                        connues.get(str(f), ""), genre="appimage"))
    return applis


def lire_release_appimage(donnees: dict, prefixe: str, arch: str) -> tuple[str, str, str]:
    """(version, lien de l'AppImage, lien de SHA256SUMS) ; l'AppImage sans architecture est x86_64."""
    version = str(donnees.get("tag_name") or "").lstrip("vV")
    liens = {a.get("name") or "": a.get("browser_download_url") for a in donnees.get("assets") or []}
    autre = "x86_64" if arch == "arm64" else "arm64"
    candidats = [n for n in liens if n.startswith(prefixe) and n.endswith(".AppImage")
                 and autre not in n and "aarch64" not in n]
    if arch == "arm64":
        candidats = [n for n in candidats if "arm64" in n or "aarch64" in n]
    candidats.sort(key=lambda n: (version not in n, n))
    return version, (liens[candidats[0]] if candidats else ""), liens.get("SHA256SUMS") or ""


def _racine() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def architecture() -> str:
    m = platform.machine().lower()
    return "arm64" if m in ("aarch64", "arm64") else "x86_64"


def trouver() -> list[Appli]:
    """Les applications du kit installées dans le profil (Martinet excepté : il se met à jour seul)."""
    if demo.actif():
        return [Appli(*a) for a in demo.APPLIS_LINUX]
    applis = []
    racine = _racine()
    try:
        dossiers = sorted(racine.iterdir())
    except OSError:
        return []
    for d in dossiers:
        fiche = d / "app" / "kit.json"
        try:
            kit = json.loads(fiche.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        depot, tech = kit.get("depot_distribution") or "", kit.get("nom_technique") or d.name
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", depot) or tech == "martinet":
            continue
        try:
            version = (d / "app" / (kit.get("fichier_version") or "VERSION")).read_text(encoding="utf-8").strip()
        except OSError:
            version = ""
        applis.append(Appli(kit.get("nom_affiche") or kit.get("nom_fichier") or d.name, tech,
                            kit.get("nom_fichier") or d.name, depot, str(d), version))
    depots_kit = {a.depot for a in applis}
    images = trouver_appimages()
    for a in images:
        if a.depot in depots_kit:
            # même application installée deux fois (kit + AppImage) : on ne met à jour que le kit
            a.etat, a.erreur = "doublon", tr("lx.applis.doublon", chemin=a.dossier)
    return applis + images


def lire_release(donnees: dict, fichier: str, arch: str) -> tuple[str, str, str]:
    """(version, lien de l'archive Linux, lien de SHA256SUMS) d'une Release GitHub."""
    version = str(donnees.get("tag_name") or "").lstrip("vV")
    liens = {a.get("name"): a.get("browser_download_url") for a in donnees.get("assets") or []}
    archive = liens.get(f"{fichier}-{version}-linux-{arch}.tar.gz") or liens.get(f"{fichier}-linux-{arch}.tar.gz") or ""
    return version, archive, liens.get("SHA256SUMS") or ""


def verifier(applis: list[Appli] | None = None, journal=None) -> list[Appli]:
    applis = trouver() if applis is None else applis
    if demo.actif():
        demo.pause(0.3)
        for a in applis:
            a.etat = "maj" if a.derniere and plus_recente(a.derniere, a.installee) else "a_jour"
        return applis
    for a in applis:
        if a.etat == "doublon":
            if journal:
                journal(a.erreur)
            continue
        if journal:
            journal(tr("journal.source", nom=a.nom))
        try:
            donnees = systeme.telecharger_json(API.format(depot=a.depot), timeout=20)
            lire = lire_release_appimage if a.genre == "appimage" else lire_release
            a.derniere, a.archive, a.sommes = lire(donnees, a.fichier, architecture())
            if not a.archive:
                a.etat, a.erreur = "erreur", tr("lx.applis.pas_archive")
            elif a.genre == "appimage" and not a.installee:
                a.etat = "maj"                # version inconnue : on pose la dernière une fois
            else:
                a.etat = "maj" if plus_recente(a.derniere, a.installee) else "a_jour"
        except Exception as exc:              # noqa: BLE001 — une appli en échec n'arrête pas les autres
            a.etat, a.erreur = "erreur", str(exc)[:200]
    return applis


def en_marche(dossier: str) -> bool:
    """Un processus tourne-t-il depuis ce dossier, ou cette AppImage ? (la remplacer sous ses pieds
    la ferait planter)"""
    if Path(dossier).is_file():
        cible = dossier.encode()
        for p in Path("/proc").glob("[0-9]*"):
            try:
                arguments = (p / "cmdline").read_bytes().split(b"\0")
                environ = (p / "environ").read_bytes().split(b"\0")
            except OSError:
                continue
            if cible in arguments[:2] or b"APPIMAGE=" + cible in environ:
                return True
        return False
    prefixe = dossier.rstrip("/").encode() + b"/"
    moi = str(os.getpid())
    for p in Path("/proc").glob("[0-9]*"):
        if p.name == moi:
            continue
        try:
            arguments = (p / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        # le programme lancé depuis le dossier (python/bin/python3, Coupole.sh…), pas une simple mention
        if any(a.startswith(prefixe) for a in arguments[:2]):
            return True
    return False


def _empreinte_attendue(sommes: str, nom: str) -> str:
    for ligne in sommes.splitlines():
        morceaux = ligne.split()
        if len(morceaux) == 2 and morceaux[1].lstrip("*") == nom:
            return morceaux[0].lower()
    return ""


def _extraire(archive: Path, dest: Path) -> None:
    """Extraction sûre : rien hors du dossier, pas de lien qui en sorte."""
    with tarfile.open(archive) as t:
        try:
            t.extractall(dest, filter="data")
            return
        except TypeError:                     # Python antérieur à 3.12 : le filtre à la main
            pass
        racine = dest.resolve()
        for m in t.getmembers():
            cible = (dest / m.name).resolve()
            if racine not in cible.parents and cible != racine:
                raise ValueError(tr("lx.archive.refusee", nom=m.name))
            if (m.issym() or m.islnk()) and (os.path.isabs(m.linkname) or ".." in Path(m.linkname).parts):
                raise ValueError(tr("lx.archive.refusee", nom=m.name))
            if m.isdev():
                raise ValueError(tr("lx.archive.refusee", nom=m.name))
        t.extractall(dest)


def mettre_a_jour(a: Appli, journal=None, annulation=None) -> tuple[bool, str]:
    """Archive officielle → empreinte vérifiée → installer.sh."""
    if demo.actif():
        demo.pause(0.3)
        if journal:
            journal(f"{a.nom} {a.installee} -> {a.derniere}")
        return True, ""
    if en_marche(a.dossier):
        return False, tr("lx.applis.ouverte", nom=a.nom)
    if not a.archive or not a.sommes:
        return False, tr("lx.applis.pas_archive")
    if a.genre == "appimage":
        return _remplacer_appimage(a, journal, annulation)
    with tempfile.TemporaryDirectory(prefix="martinet-") as tmp:
        tmp = Path(tmp)
        nom = a.archive.rsplit("/", 1)[-1]
        archive = tmp / nom
        if journal:
            journal(tr("journal.telechargement", nom=nom))
        systeme.telecharger_fichier(a.archive, archive, None, annulation)
        attendue = _empreinte_attendue(systeme.telecharger_texte(a.sommes, timeout=30), nom)
        reelle = hashlib.sha256(archive.read_bytes()).hexdigest()
        if not attendue or attendue != reelle:
            return False, tr("lx.applis.empreinte")
        dest = tmp / "x"
        _extraire(archive, dest)
        installeurs = sorted(dest.glob("*/installer.sh")) or sorted(dest.glob("installer.sh"))
        if not installeurs:
            return False, tr("lx.applis.pas_installeur")
        code, sortie = systeme.executer_flux(["sh", str(installeurs[0])], journal, annulation, timeout=1800)
        shutil.rmtree(dest, ignore_errors=True)
    return code == 0, ("" if code == 0 else (sortie.strip().splitlines() or [f"code {code}"])[-1][:200])


def _remplacer_appimage(a: Appli, journal=None, annulation=None) -> tuple[bool, str]:
    """Nouvelle AppImage téléchargée à côté de l'ancienne, empreinte vérifiée, puis échange
    atomique : jamais de fichier à moitié écrit à la place du programme."""
    cible = Path(a.dossier)
    nom = a.archive.rsplit("/", 1)[-1]
    neuve = cible.with_name(f".{cible.name}.martinet")
    try:
        if journal:
            journal(tr("journal.telechargement", nom=nom))
        systeme.telecharger_fichier(a.archive, neuve, None, annulation)
        attendue = _empreinte_attendue(systeme.telecharger_texte(a.sommes, timeout=30), nom)
        h = hashlib.sha256()
        with open(neuve, "rb") as f:
            for bloc in iter(lambda: f.read(1 << 20), b""):
                h.update(bloc)
        if not attendue or attendue != h.hexdigest():
            return False, tr("lx.applis.empreinte")
        neuve.chmod(cible.stat().st_mode | 0o111)
        os.replace(neuve, cible)
    except Exception as exc:                  # noqa: BLE001
        return False, str(exc)[:200]
    finally:
        neuve.unlink(missing_ok=True)
    _noter_version(str(cible), a.derniere)
    return True, ""

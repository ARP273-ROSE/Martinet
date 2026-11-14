"""Ménage sous Manjaro / Arch : ce que le système sait recréer.

* Le cache de pacman n'est jamais vidé en entier : on garde les deux
  dernières versions de chaque paquet, de quoi revenir en arrière si une
  mise à jour casse quelque chose (paccache -rk2, la règle de l'Arch Wiki).
* Les paquets orphelins ne sont pas du « ménage » : ils se retirent un par
  un, cochés, depuis la page Système.
* Ce qui demande les droits d'administrateur passe en une seule demande de
  mot de passe (pamac via polkit, sinon pkexec).
"""
from __future__ import annotations

import getpass
import os
import re
from pathlib import Path

from . import demo, systeme

AGE_MINI_JOURS = 7


def _maison() -> Path:
    return Path.home()


def _cache() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or _maison() / ".cache")


def _donnees_xdg() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or _maison() / ".local" / "share")


def dossiers(cle: str) -> list[Path]:
    if cle == "fichiers_construction":
        return [_cache() / "yay", _cache() / "paru" / "clone",
                Path("/var/tmp") / f"pamac-build-{getpass.getuser()}"]
    if cle == "miniatures":
        return [_cache() / "thumbnails"]
    if cle == "corbeille":
        return [_donnees_xdg() / "Trash" / "files", _donnees_xdg() / "Trash" / "info"]
    if cle == "vidages_systeme":
        return [Path("/var/lib/systemd/coredump")]
    if cle == "telechargements_martinet":
        return [systeme.dossier_donnees() / "telechargements"]
    return []


def _taille_dossiers(cle: str) -> tuple[int, int]:
    taille = nombre = 0
    for d in dossiers(cle):
        try:
            if not d.is_dir():
                continue
        except OSError:
            continue
        for racine, _sous, noms in os.walk(d, onerror=lambda e: None):
            for n in noms:
                try:
                    st = os.lstat(os.path.join(racine, n))
                except OSError:
                    continue
                taille += st.st_size
                nombre += 1
    return taille, nombre


def lire_paccache(texte: str) -> tuple[int, int]:
    """« ==> finished dry run: 63 candidates (disk space saved: 1.20 GiB) »."""
    from .linux_paquets import lire_taille
    m = re.search(r"(\d+)\s+candidates?\s*\(disk space saved:\s*([^)]+)\)", texte)
    if not m:
        return 0, 0
    return lire_taille(m.group(2)), int(m.group(1))


def lire_journal(texte: str) -> int:
    """« Archived and active journals take up 1.2G in the file system. »"""
    m = re.search(r"take up\s+([\d.,]+)\s*([KMGT]?)", texte)
    if not m:
        return 0
    return int(float(m.group(1).replace(",", ".")) * 1024 ** " KMGT".index(m.group(2) or " "))


def mesurer(cle: str) -> tuple[int | None, int | None]:
    if demo.actif():
        demo.pause(0.1)
        return demo.MENAGE_LINUX[cle]
    if cle in ("cache_paquets", "cache_desinstalles"):
        if not systeme.outil("paccache"):
            return None, None
        args = ["-dk2"] if cle == "cache_paquets" else ["-duk0"]
        _c, sortie = systeme.executer(["paccache", *args], timeout=120, env=systeme.ENV_C)
        return lire_paccache(sortie)
    if cle == "flatpak_inutilises":
        return None, None                    # flatpak ne sait pas le dire sans le faire
    if cle == "journaux_systeme":
        _c, sortie = systeme.executer(["journalctl", "--disk-usage"], timeout=60, env=systeme.ENV_C)
        return lire_journal(sortie), None
    return _taille_dossiers(cle)


# ------------------------------------------------------------ nettoyage
def _vider(cle: str) -> int:
    """Fichiers de l'utilisateur : effacés un à un, ceux qui résistent restent."""
    libere = 0
    for d in dossiers(cle):
        if not d.is_dir():
            continue
        for racine, sous, noms in os.walk(d, topdown=False, onerror=lambda e: None):
            for n in noms:
                f = os.path.join(racine, n)
                try:
                    t = os.lstat(f).st_size
                    os.unlink(f)
                    libere += t
                except OSError:
                    continue
            for s in sous:
                try:
                    os.rmdir(os.path.join(racine, s))
                except OSError:
                    pass
    return libere


def commandes_root(cles: list[str]) -> list[str]:
    """Commandes à lancer en administrateur, regroupées dans UNE demande (pkexec)."""
    lignes = []
    pamac = bool(systeme.outil("pamac"))
    if "cache_paquets" in cles and not pamac:
        lignes.append("paccache -rk2")
    if "cache_desinstalles" in cles and not pamac:
        lignes.append("paccache -ruk0")
    if "journaux_systeme" in cles:
        lignes.append("journalctl --vacuum-time=4weeks")
    if "vidages_systeme" in cles:
        lignes.append("find /var/lib/systemd/coredump -type f -delete")
    return lignes


def nettoyer_tout(cles: list[str], journal=None) -> int:
    """Nettoie les éléments choisis ; renvoie les octets libérés (estimation)."""
    if demo.actif():
        demo.pause(0.3)
        return sum(demo.MENAGE_LINUX[c][0] or 0 for c in cles)
    avant = {c: (mesurer(c)[0] or 0) for c in cles if c in ("cache_paquets", "cache_desinstalles",
                                                              "journaux_systeme", "vidages_systeme")}
    libere = 0
    if systeme.outil("pamac"):
        # le cache passe par pamac : la règle polkit de Martinet, si elle est posée, évite le mot de passe
        if "cache_paquets" in cles:
            systeme.executer_flux(["pamac", "clean", "--keep", "2", "--no-confirm"], journal, timeout=1800)
        if "cache_desinstalles" in cles:
            systeme.executer_flux(["pamac", "clean", "--uninstalled", "--keep", "0", "--no-confirm"], journal,
                                  timeout=1800)
    lignes = commandes_root(cles)
    if lignes:
        script = "\n".join(lignes)
        if journal:
            journal("pkexec : " + " ; ".join(lignes))
        code, sortie = systeme.executer_flux(["pkexec", "sh", "-c", script], journal, timeout=1800)
        if code in (126, 127) and journal:
            from .i18n import tr
            journal(tr("lx.refuse"))
    if "flatpak_inutilises" in cles and systeme.outil("flatpak"):
        systeme.executer_flux(["flatpak", "uninstall", "--unused", "-y", "--noninteractive"], journal,
                              timeout=1800)
    for c in cles:
        if c in ("fichiers_construction", "miniatures", "corbeille", "telechargements_martinet"):
            libere += _vider(c)
    for c, t in avant.items():
        libere += max(0, t - (mesurer(c)[0] or 0))
    return libere

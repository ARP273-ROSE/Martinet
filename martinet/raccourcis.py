"""Raccourcis morts : ceux dont le programme ou le fichier a disparu.

Les fichiers .lnk sont lus directement (format MS-SHLLINK, documenté par
Microsoft), sans lancer de commande. Prudence avant tout :

* un raccourci « spécial » (Panneau de configuration, application du Store,
  raccourci d'installation Windows Installer) n'a pas de chemin : ignoré ;
* une cible sur un lecteur absent (clé USB, disque débranché) ou sur le
  réseau n'est pas vérifiée — interroger un NAS en veille le réveillerait,
  et un partage injoignable n'est pas une preuve de disparition ;
* rien n'est effacé : les raccourcis sont MIS DE CÔTÉ dans les données de
  Martinet, avec leur emplacement d'origine, et se restaurent d'un clic.
"""
from __future__ import annotations

import datetime
import json
import os
import shutil
import struct
from dataclasses import dataclass
from pathlib import Path

from . import demo, systeme

# LinkFlags
A_IDLIST, A_LINKINFO, A_NOM, A_RELATIF, A_DOSSIER, A_ARGS, A_ICONE, UNICODE = (
    0x1, 0x2, 0x4, 0x8, 0x10, 0x20, 0x40, 0x80)
A_DARWIN, A_EXPSTRING = 0x1000, 0x200
SIG_ENVIRONNEMENT = 0xA0000001


@dataclass
class Cible:
    chemin: str = ""
    special: bool = False      # pas de chemin de fichier (shell, Store, MSI)


def _chaine_c(donnees: bytes, debut: int, large: bool) -> str:
    if large:
        fin = debut
        while fin + 1 < len(donnees) and donnees[fin:fin + 2] != b"\0\0":
            fin += 2
        return donnees[debut:fin].decode("utf-16-le", errors="replace")
    fin = donnees.find(b"\0", debut)
    fin = len(donnees) if fin < 0 else fin
    codec = "mbcs" if systeme.WINDOWS else "cp1252"
    return donnees[debut:fin].decode(codec, errors="replace")


def lire_lnk(donnees: bytes) -> Cible:
    """Chemin visé par un raccourci Windows (.lnk)."""
    if len(donnees) < 0x4C or struct.unpack_from("<I", donnees, 0)[0] != 0x4C:
        raise ValueError("pas un raccourci Windows")
    drapeaux = struct.unpack_from("<I", donnees, 0x14)[0]
    if drapeaux & A_DARWIN:
        return Cible(special=True)
    pos = 0x4C
    if drapeaux & A_IDLIST:
        pos += 2 + struct.unpack_from("<H", donnees, pos)[0]
    chemin_info = ""
    if drapeaux & A_LINKINFO:
        debut = pos
        taille, entete, li_flags, _vol, base, reseau, suffixe = struct.unpack_from("<7I", donnees, pos)
        base_u = suffixe_u = 0
        if entete >= 0x24:
            base_u, suffixe_u = struct.unpack_from("<2I", donnees, pos + 28)
        suffixe_txt = (_chaine_c(donnees, debut + suffixe_u, True) if suffixe_u
                       else _chaine_c(donnees, debut + suffixe, False))
        if li_flags & 0x1:
            racine = (_chaine_c(donnees, debut + base_u, True) if base_u
                      else _chaine_c(donnees, debut + base, False))
            chemin_info = racine + suffixe_txt
        elif li_flags & 0x2:
            r = debut + reseau
            _t, _f, nom_off = struct.unpack_from("<3I", donnees, r)
            nom_u = struct.unpack_from("<I", donnees, r + 20)[0] if nom_off > 0x14 else 0
            partage = _chaine_c(donnees, r + nom_u, True) if nom_u else _chaine_c(donnees, r + nom_off, False)
            chemin_info = partage + ("\\" + suffixe_txt if suffixe_txt else "")
        pos = debut + taille
    chaines = {}
    large = bool(drapeaux & UNICODE)
    for drapeau in (A_NOM, A_RELATIF, A_DOSSIER, A_ARGS, A_ICONE):
        if drapeaux & drapeau:
            n = struct.unpack_from("<H", donnees, pos)[0]
            pos += 2
            octets = n * (2 if large else 1)
            brut = donnees[pos:pos + octets]
            chaines[drapeau] = brut.decode("utf-16-le" if large else "cp1252", errors="replace")
            pos += octets
    chemin_env = ""
    while pos + 8 <= len(donnees):
        taille_bloc = struct.unpack_from("<I", donnees, pos)[0]
        if taille_bloc < 8:
            break
        signature = struct.unpack_from("<I", donnees, pos + 4)[0]
        if signature == SIG_ENVIRONNEMENT and taille_bloc >= 0x314:
            chemin_env = (_chaine_c(donnees, pos + 268, True) or _chaine_c(donnees, pos + 8, False))
        pos += taille_bloc
    if chemin_env:
        return Cible(os.path.expandvars(chemin_env))
    if chemin_info:
        return Cible(chemin_info)
    if A_RELATIF in chaines:
        return Cible(chaines[A_RELATIF], special=False)
    return Cible(special=True)


@dataclass
class Raccourci:
    fichier: str               # chemin du .lnk
    lieu: str                  # « bureau », « demarrer », « barre »
    cible: str


def lieux() -> list[tuple[str, Path]]:
    if not systeme.WINDOWS:
        return []
    env = os.environ
    profil = Path(env.get("USERPROFILE", Path.home()))
    appdata = Path(env.get("APPDATA", profil / "AppData" / "Roaming"))
    programdata = Path(env.get("ProgramData", r"C:\ProgramData"))
    public = Path(env.get("PUBLIC", r"C:\Users\Public"))
    bureau = _dossier_connu("Desktop") or profil / "Desktop"
    return [("bureau", bureau), ("bureau", public / "Desktop"),
            ("demarrer", appdata / "Microsoft" / "Windows" / "Start Menu"),
            ("demarrer", programdata / "Microsoft" / "Windows" / "Start Menu"),
            ("barre", appdata / "Microsoft" / "Internet Explorer" / "Quick Launch" / "User Pinned" / "TaskBar")]


def _dossier_connu(nom: str) -> Path | None:
    """Bureau redirigé (OneDrive…) : le chemin réel est dans le registre."""
    try:
        import winreg
        cle = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
        return Path(os.path.expandvars(winreg.QueryValueEx(cle, nom)[0]))
    except Exception:
        return None


def verdict(cible: str) -> str:
    """« ok », « mort », ou « non_verifie » (réseau, lecteur absent)."""
    if not cible:
        return "non_verifie"
    if cible.startswith("\\\\") or "://" in cible:
        return "non_verifie"
    racine = os.path.splitdrive(cible)[0]
    if racine and not os.path.exists(racine + "\\"):
        return "non_verifie"
    return "ok" if os.path.exists(cible) else "mort"


def chercher_morts(journal=None) -> list[Raccourci]:
    if demo.actif():
        demo.pause(0.5)
        return [Raccourci(f"C:\\Exemple\\{l}\\{n}", "bureau" if l == "Bureau" else "demarrer", c)
                for l, n, c in demo.RACCOURCIS_MORTS]
    morts, vus = [], set()
    for lieu, dossier in lieux():
        if not dossier.is_dir():
            continue
        for f in dossier.rglob("*.lnk"):
            if f in vus:
                continue
            vus.add(f)
            try:
                cible = lire_lnk(f.read_bytes())
            except (OSError, ValueError, struct.error):
                continue
            if cible.special:
                continue
            chemin = cible.chemin
            if not os.path.isabs(chemin) and not chemin.startswith("\\\\"):
                chemin = str((f.parent / chemin).resolve())
            if verdict(chemin) == "mort":
                morts.append(Raccourci(str(f), lieu, chemin))
    if journal:
        journal(f"{len(vus)} raccourcis lus, {len(morts)} morts")
    return morts


# ------------------------------------------------------------ mise de côté
def _quarantaine() -> Path:
    return systeme.sous_dossier("raccourcis_mis_de_cote")


def mettre_de_cote(liste: list[Raccourci]) -> tuple[int, list[str]]:
    """Déplace les raccourcis ; renvoie (nombre déplacé, erreurs)."""
    if demo.actif():
        return len(liste), []
    lot = _quarantaine() / datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    lot.mkdir(parents=True, exist_ok=True)
    index, erreurs = [], []
    for r in liste:
        source = Path(r.fichier)
        dest = lot / source.name
        n = 1
        while dest.exists():
            dest = lot / f"{source.stem}_{n}{source.suffix}"
            n += 1
        try:
            shutil.move(str(source), str(dest))
            index.append({"fichier": dest.name, "origine": str(source), "cible": r.cible})
        except OSError as exc:
            erreurs.append(f"{source.name} : {exc.strerror or exc}")
    (lot / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return len(index), erreurs


@dataclass
class MisDeCote:
    lot: str
    fichier: str
    origine: str
    cible: str


def mis_de_cote() -> list[MisDeCote]:
    if demo.actif():
        return []
    elements = []
    for lot in sorted(_quarantaine().iterdir(), reverse=True):
        try:
            index = json.loads((lot / "index.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for e in index:
            if (lot / e["fichier"]).exists():
                elements.append(MisDeCote(lot.name, e["fichier"], e["origine"], e.get("cible", "")))
    return elements


def restaurer(elements: list[MisDeCote]) -> tuple[int, list[str]]:
    n, erreurs = 0, []
    for e in elements:
        source = _quarantaine() / e.lot / e.fichier
        dest = Path(e.origine)
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                raise FileExistsError(f"{dest.name} existe déjà")
            shutil.move(str(source), str(dest))
            n += 1
        except OSError as exc:
            erreurs.append(f"{dest.name} : {exc}")
    return n, erreurs

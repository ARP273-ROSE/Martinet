"""Manjaro / Arch : paquets, Flatpak, micrologiciels et entretien du système.

Martinet ne remplace pas le gestionnaire de paquets, il le pilote :

* **pamac** (Manjaro) d'abord : dépôts ET AUR en une transaction, et la
  demande de mot de passe passe par polkit — une vraie fenêtre, sans
  terminal. À défaut, **yay** (avec pkexec pour les droits), puis pacman.
* jamais de mise à jour partielle (interdite sous Arch) : on met à jour
  tout le système ou rien ;
* rien n'est retiré sans qu'on l'ait coché (paquets orphelins) ;
* les fichiers .pacnew sont signalés, pas fusionnés : c'est à vous de voir.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import demo, systeme
from .i18n import tr

LIGNE_MAJ = re.compile(r"^(\S+)\s+(\S+)\s+->\s+(\S+)(?:\s+(\S+))?\s*$")


@dataclass
class Paquet:
    nom: str
    installee: str
    disponible: str
    origine: str          # depots, aur, flatpak
    ident: str = ""       # identifiant Flatpak


@dataclass
class Micrologiciel:
    appareil: str
    installee: str
    disponible: str
    resume: str = ""


@dataclass
class Systeme:
    """Ce qui demande votre attention, hors mises à jour."""
    noyau: str = ""
    redemarrer: bool = False
    noyaux_fin_de_vie: list = field(default_factory=list)
    hors_depots: list = field(default_factory=list)     # paquets installés absents des dépôts (AUR compris)
    pacnew: list = field(default_factory=list)          # chemins
    orphelins: list = field(default_factory=list)       # (nom, taille en octets)
    micrologiciels: list = field(default_factory=list)  # Micrologiciel
    outils: dict = field(default_factory=dict)          # nom -> présent


# ------------------------------------------------------------ outils présents
def outils() -> dict:
    if demo.actif():
        return {"pamac": True, "yay": True, "paccache": True, "flatpak": True, "fwupdmgr": True,
                "checkupdates": True, "pacman": True}
    return {n: bool(systeme.outil(n))
            for n in ("pamac", "yay", "paccache", "flatpak", "fwupdmgr", "checkupdates", "pacman")}


# ------------------------------------------------------------ lecture des sorties
def lire_mises_a_jour(texte: str, origine_par_defaut: str = "depots") -> list[Paquet]:
    """« nom  ancienne -> nouvelle  dépôt » (pamac, checkupdates, yay -Qua)."""
    paquets = []
    for ligne in texte.splitlines():
        m = LIGNE_MAJ.match(ligne.strip())
        if not m:
            continue
        depot = (m.group(4) or "").lower()
        origine = "aur" if depot == "aur" else origine_par_defaut
        paquets.append(Paquet(m.group(1), m.group(2), m.group(3), origine))
    return paquets


def lire_flatpak(maj: str, installes: str) -> list[Paquet]:
    """flatpak remote-ls --updates et flatpak list, colonnes séparées par des tabulations."""
    versions = {}
    for ligne in installes.splitlines():
        champs = ligne.split("\t")
        if len(champs) >= 2:
            versions[champs[0].strip()] = champs[-1].strip()
    paquets = []
    for ligne in maj.splitlines():
        champs = [c.strip() for c in ligne.split("\t")]
        if len(champs) < 2 or not champs[0] or "." not in champs[0]:
            continue
        ident, nom = champs[0], champs[1] or champs[0]
        dispo = champs[2] if len(champs) > 2 else ""
        paquets.append(Paquet(nom, versions.get(ident, ""), dispo, "flatpak", ident))
    return paquets


def lire_taille(texte: str) -> int:
    """« 1.5 GiB », « 230.4 MiB », « 12 KiB » → octets."""
    m = re.search(r"([\d.,]+)\s*([KMGT]?)i?B\b", texte)
    if not m:
        return 0
    valeur = float(m.group(1).replace(",", "."))
    return int(valeur * 1024 ** " KMGT".index(m.group(2) or " "))


def lire_orphelins(qi: str) -> list[tuple[str, int]]:
    """pacman -Qi (en anglais) → [(nom, taille installée)]."""
    resultat, nom = [], None
    for ligne in qi.splitlines():
        if ligne.startswith("Name "):
            nom = ligne.split(":", 1)[1].strip()
        elif ligne.startswith("Installed Size") and nom:
            resultat.append((nom, lire_taille(ligne.split(":", 1)[1])))
            nom = None
    return resultat


def noyaux_fin_de_vie(hors_depots: list[str]) -> list[str]:
    """Manjaro retire des dépôts le noyau qui n'est plus suivi : il reste installé, sans correctif."""
    return [n for n in hors_depots if re.fullmatch(r"linux\d{2,3}(-rt)?", n)]


def lire_fwupd(donnees) -> list[Micrologiciel]:
    resultat = []
    for appareil in (donnees or {}).get("Devices", []):
        versions = appareil.get("Releases") or []
        if not versions:
            continue
        r = versions[0]
        resultat.append(Micrologiciel(appareil.get("Name", "?"), appareil.get("Version", ""),
                                      r.get("Version", ""), (r.get("Summary") or "")[:120]))
    return resultat


# ------------------------------------------------------------ recherche
def rechercher(journal=None) -> list[Paquet]:
    """Mises à jour des dépôts, de l'AUR et de Flatpak, sans rien modifier."""
    if demo.actif():
        demo.pause(0.6)
        return [Paquet(*p) for p in demo.PAQUETS_LINUX]
    o = outils()
    paquets: list[Paquet] = []
    if o["pamac"]:
        if journal:
            journal("pamac checkupdates -a")
        _code, sortie = systeme.executer(["pamac", "checkupdates", "-a"], timeout=300, env=systeme.ENV_C)
        paquets += lire_mises_a_jour(sortie)
    else:
        if o["checkupdates"]:
            if journal:
                journal("checkupdates")
            _code, sortie = systeme.executer(["checkupdates"], timeout=300, env=systeme.ENV_C)
            paquets += lire_mises_a_jour(sortie)
        if o["yay"]:
            if journal:
                journal("yay -Qua")
            _code, sortie = systeme.executer(["yay", "-Qua"], timeout=300, env=systeme.ENV_C)
            paquets += lire_mises_a_jour(sortie, "aur")
    if o["flatpak"]:
        if journal:
            journal("flatpak remote-ls --updates")
        _c, maj = systeme.executer(["flatpak", "remote-ls", "--updates",
                                    "--columns=application,name,version"], timeout=300, env=systeme.ENV_C)
        _c, inst = systeme.executer(["flatpak", "list", "--columns=application,version"],
                                    timeout=120, env=systeme.ENV_C)
        paquets += lire_flatpak(maj, inst)
    return paquets


def etat_systeme(journal=None) -> Systeme:
    if demo.actif():
        demo.pause(0.3)
        import copy
        s = Systeme(**copy.deepcopy(demo.SYSTEME_LINUX))
        s.micrologiciels = [Micrologiciel("System Firmware", "1.2.0", "1.4.1")]
        return s
    s = Systeme(outils=outils())
    s.noyau = os.uname().release
    # le noyau en marche a été remplacé : ses modules ont disparu du disque
    s.redemarrer = bool(s.noyau) and not Path("/usr/lib/modules", s.noyau).is_dir()
    if s.outils["pacman"]:
        _c, sortie = systeme.executer(["pacman", "-Qmq"], timeout=60, env=systeme.ENV_C)
        s.hors_depots = [l.strip() for l in sortie.splitlines() if l.strip()]
        s.noyaux_fin_de_vie = noyaux_fin_de_vie(s.hors_depots)
        _c, sortie = systeme.executer(["pacman", "-Qdtq"], timeout=60, env=systeme.ENV_C)
        noms = [l.strip() for l in sortie.splitlines() if l.strip() and " " not in l.strip()]
        if noms:
            _c, qi = systeme.executer(["pacman", "-Qi", *noms], timeout=60, env=systeme.ENV_C)
            s.orphelins = lire_orphelins(qi)
    s.pacnew = chercher_pacnew()
    if s.outils["fwupdmgr"]:
        if journal:
            journal("fwupdmgr get-updates")
        _c, sortie = systeme.executer(["fwupdmgr", "get-updates", "--json", "--no-unreported-check"],
                                      timeout=120, env=systeme.ENV_C)
        try:
            import json
            s.micrologiciels = lire_fwupd(json.loads(sortie[sortie.find("{"):]))
        except ValueError:
            s.micrologiciels = []
    return s


def chercher_pacnew(racine: str = "/etc") -> list[str]:
    trouves = []
    for dossier, _sous, noms in os.walk(racine, onerror=lambda e: None):
        for n in noms:
            if n.endswith((".pacnew", ".pacsave")):
                trouves.append(os.path.join(dossier, n))
    return sorted(trouves)


# ------------------------------------------------------------ actions
def mettre_a_jour(journal=None, annulation=None, aur: bool = True, flatpak: bool = True) -> tuple[bool, str]:
    """Tout le système (jamais de mise à jour partielle), puis Flatpak."""
    if demo.actif():
        for p in demo.PAQUETS_LINUX:
            demo.pause(0.2)
            if journal:
                journal(f"{p[0]} {p[1]} -> {p[2]}")
        return True, ""
    o = outils()
    if o["pamac"]:
        cmd = ["pamac", "upgrade", "--aur" if aur else "--no-aur", "--no-confirm"]
    elif o["yay"]:
        cmd = ["yay", "-Syu", "--noconfirm", "--sudo", "pkexec"] + ([] if aur else ["--repo"])
    elif o["pacman"]:
        cmd = ["pkexec", "pacman", "-Syu", "--noconfirm"]
    else:
        return False, tr("lx.pas_de_pacman")
    code, sortie = systeme.executer_flux(cmd, journal, annulation, timeout=14400)
    ok, detail = code == 0, ("" if code == 0 else _motif(code, sortie))
    if flatpak and o["flatpak"]:
        c2, s2 = systeme.executer_flux(["flatpak", "update", "-y", "--noninteractive"], journal, annulation,
                                       timeout=7200)
        if c2 != 0:
            ok, detail = False, (detail + " ; " if detail else "") + "flatpak : " + _motif(c2, s2)
    return ok, detail


def _motif(code: int, sortie: str) -> str:
    if code in (126, 127) and not sortie.startswith("introuvable"):
        return tr("lx.refuse")                 # pkexec / polkit : demande refusée ou fermée
    derniere = [l for l in sortie.splitlines() if l.strip()][-1:] or [f"code {code}"]
    return derniere[0][:200]


def retirer_orphelins(noms: list[str], journal=None, annulation=None) -> tuple[bool, str]:
    if demo.actif():
        return True, ""
    noms = [n for n in noms if re.fullmatch(r"[A-Za-z0-9@._+-]+", n)]
    if not noms:
        return True, ""
    if outils()["pamac"]:
        cmd = ["pamac", "remove", "--no-confirm", *noms]
    else:
        cmd = ["pkexec", "pacman", "-Rns", "--noconfirm", *noms]
    code, sortie = systeme.executer_flux(cmd, journal, annulation, timeout=3600)
    return code == 0, ("" if code == 0 else _motif(code, sortie))


def mettre_a_jour_micrologiciels(journal=None, annulation=None) -> tuple[bool, str]:
    """Jamais en automatique : une mise à jour de micrologiciel se surveille."""
    if demo.actif():
        return True, ""
    code, sortie = systeme.executer_flux(["fwupdmgr", "update", "-y", "--no-reboot-check"], journal,
                                         annulation, timeout=3600)
    return code == 0, ("" if code == 0 else _motif(code, sortie))


# ------------------------------------------------------------ mises à jour sans mot de passe
REGLE_POLKIT = Path("/etc/polkit-1/rules.d/49-martinet-pamac.rules")


def texte_regle(utilisateur: str) -> str:
    return ("// Martinet : mises à jour de " + utilisateur + " sans mot de passe (pamac seulement).\n"
            "polkit.addRule(function(action, subject) {\n"
            "    if (action.id == \"org.manjaro.pamac.commit\" && subject.user == \""
            + utilisateur + "\") {\n"
            "        return polkit.Result.YES;\n"
            "    }\n"
            "});\n")


def regle_active() -> bool:
    if demo.actif():
        return False
    return REGLE_POLKIT.exists()


def poser_regle(active: bool) -> tuple[bool, str]:
    """Une règle polkit limitée à pamac et à vous : le passage planifié n'a plus besoin de vous."""
    if demo.actif():
        return True, ""
    import getpass
    utilisateur = getpass.getuser()
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*\$?", utilisateur):
        return False, tr("lx.utilisateur_inattendu")
    if active:
        script = (f"install -m 0644 /dev/stdin {REGLE_POLKIT} <<'FIN'\n{texte_regle(utilisateur)}FIN\n")
    else:
        script = f"rm -f {REGLE_POLKIT}\n"
    code, sortie = systeme.executer(["pkexec", "sh", "-c", script], timeout=300)
    return code == 0, ("" if code == 0 else _motif(code, sortie))

"""winget, le gestionnaire de paquets de Windows (l'équivalent de « yay »).

Lecture : par le module PowerShell officiel Microsoft.WinGet.Client, qui
rend de vrais objets (identifiant complet, versions, source). À défaut, on
lit le tableau texte de `winget upgrade` / `winget list`, dont les colonnes
se repèrent par la position des titres — quelle que soit la langue.

Écriture : toujours la commande `winget`, paquet par paquet, pour que
l'échec d'un logiciel n'empêche pas les autres et que chaque résultat soit
connu.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import demo, systeme
from .versions import plus_recente

SOURCES_SUIVIES = {"winget", "msstore"}
ACCORDS = ["--accept-source-agreements", "--disable-interactivity"]


@dataclass
class Paquet:
    id: str
    nom: str
    installee: str
    disponible: str = ""
    source: str = ""

    @property
    def suivi(self) -> bool:
        """winget sait-il mettre à jour ce logiciel ?"""
        return self.source.lower() in SOURCES_SUIVIES and bool(self.id)

    @property
    def a_mettre_a_jour(self) -> bool:
        if not (self.suivi and self.disponible):
            return False
        if self.installee.lower() in ("", "unknown", "inconnu"):
            return True
        return self.disponible != self.installee and not plus_recente(self.installee, self.disponible)


@dataclass
class Inventaire:
    paquets: list[Paquet] = field(default_factory=list)
    methode: str = ""            # « module » ou « texte »
    erreur: str = ""

    @property
    def a_jour(self) -> list[Paquet]:
        return [p for p in self.paquets if p.a_mettre_a_jour]

    @property
    def non_suivis(self) -> list[Paquet]:
        return [p for p in self.paquets if not p.suivi]


def disponible() -> bool:
    if demo.actif():
        return True
    code, _ = systeme.executer(["winget", "--version"], timeout=30)
    return code == 0


# ------------------------------------------------------------ module PowerShell
SCRIPT_MODULE = r"""
$ErrorActionPreference = 'Stop'
if (-not (Get-Module -ListAvailable -Name Microsoft.WinGet.Client)) {
    if (-not (Get-PackageProvider -ListAvailable -Name NuGet -ErrorAction SilentlyContinue)) {
        Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -Scope CurrentUser | Out-Null
    }
    Install-Module -Name Microsoft.WinGet.Client -Scope CurrentUser -Force -AllowClobber | Out-Null
}
Import-Module Microsoft.WinGet.Client
$liste = Get-WinGetPackage | ForEach-Object {
    [pscustomobject]@{
        id = [string]$_.Id; nom = [string]$_.Name; installee = [string]$_.InstalledVersion
        disponible = [string]($_.AvailableVersions | Select-Object -First 1)
        maj = [bool]$_.IsUpdateAvailable; source = [string]$_.Source
    }
}
'###JSON###'
ConvertTo-Json -InputObject @($liste) -Depth 3 -Compress
"""


def _par_module() -> Inventaire:
    code, sortie = systeme.powershell(SCRIPT_MODULE, timeout=600)
    donnees = systeme.json_de_sortie(sortie)
    if code != 0 or donnees is None:
        raise RuntimeError(sortie.strip()[-400:] or f"code {code}")
    paquets = []
    for d in systeme.en_liste(donnees):
        dispo = d.get("disponible") or "" if d.get("maj") else ""
        paquets.append(Paquet(d.get("id") or "", d.get("nom") or "", d.get("installee") or "",
                              dispo, d.get("source") or ""))
    return Inventaire(paquets, "module")


# ------------------------------------------------------------ tableau texte
_TIRETS = re.compile(r"^-{10,}\s*$")


def lire_tableau(texte: str) -> list[list[str]]:
    """Lignes d'un tableau winget, découpées aux positions des titres.

    Renvoie une liste de cellules par ligne ; le premier tableau seulement
    (le second, « nécessite un ciblage explicite », est lu à part).
    """
    lignes = [systeme.nettoyer_ligne(l) for l in texte.replace("\r\n", "\n").split("\n")]
    for i in range(1, len(lignes)):
        if _TIRETS.match(lignes[i]):
            entete = lignes[i - 1]
            debuts = [m.start() for m in re.finditer(r"\S+", entete)]
            if len(debuts) < 3:
                continue
            resultat = []
            for ligne in lignes[i + 1:]:
                if not ligne.strip() or len(ligne) <= debuts[2]:
                    break
                bornes = debuts + [None]
                cellules = [ligne[bornes[k]:bornes[k + 1]].strip() for k in range(len(debuts))]
                ident = cellules[1]
                if not ident or " " in ident:
                    break
                resultat.append(cellules)
            return resultat
    return []


def _texte_vers_paquets(texte: str, avec_dispo: bool) -> list[Paquet]:
    paquets = []
    for c in lire_tableau(texte):
        colonnes = len(c)
        c = c + [""] * (5 - colonnes)
        if avec_dispo or colonnes >= 5:     # Nom Id Version Disponible Source
            paquets.append(Paquet(c[1], c[0], c[2], c[3], c[4]))
        else:                               # Nom Id Version Source
            paquets.append(Paquet(c[1], c[0], c[2], "", c[3]))
    return paquets


def _par_texte() -> Inventaire:
    code, liste = systeme.executer(["winget", "list", *ACCORDS], timeout=300)
    if code == 127:
        return Inventaire([], "texte", "winget")
    tous = _texte_vers_paquets(liste, avec_dispo=False)
    _, maj = systeme.executer(["winget", "upgrade", "--include-unknown", *ACCORDS], timeout=300)
    dispo = {p.id: p.disponible for p in _texte_vers_paquets(maj, avec_dispo=True)}
    for p in tous:
        if p.id in dispo:
            p.disponible = dispo[p.id]
            if not p.source:
                p.source = "winget"
        elif p.disponible and not p.source:
            # `winget list` a une colonne « Disponible » : la source est en 5e
            p.source, p.disponible = p.disponible, ""
    return Inventaire(tous, "texte")


def inventaire(journal=None) -> Inventaire:
    if demo.actif():
        demo.pause(0.6)
        return Inventaire([Paquet(i, n, v, d if d != v else "", s) for i, n, v, d, s in demo.PAQUETS],
                          "demo")
    if journal:
        journal("winget : lecture des logiciels installés…")
    try:
        return _par_module()
    except Exception as exc:                     # module absent, PowerShell bridé…
        if journal:
            journal(f"module WinGet indisponible ({str(exc)[:120]}), lecture du tableau texte")
        return _par_texte()


# ------------------------------------------------------------ actions
def mettre_a_jour(paquet_id: str, journal=None, annulation=None) -> tuple[bool, str]:
    if demo.actif():
        for etape in ("Téléchargement", "Vérification du hachage", "Installation"):
            demo.pause(0.3)
            if journal:
                journal(f"{paquet_id} : {etape}")
        return True, ""
    cmd = ["winget", "upgrade", "--id", paquet_id, "--exact", "--silent", "--include-unknown",
           "--accept-package-agreements", *ACCORDS]
    code, sortie = systeme.executer_flux(cmd, journal, annulation)
    return code == 0, (f"0x{code & 0xFFFFFFFF:08X}" if code else "")


def installer(paquet_id: str, journal=None, annulation=None) -> tuple[bool, str]:
    """Installe par winget un logiciel déjà présent : il devient suivi."""
    if demo.actif():
        demo.pause(0.5)
        return True, ""
    cmd = ["winget", "install", "--id", paquet_id, "--exact", "--silent",
           "--accept-package-agreements", *ACCORDS]
    code, _ = systeme.executer_flux(cmd, journal, annulation)
    return code == 0, (f"0x{code & 0xFFFFFFFF:08X}" if code else "")


SCRIPT_RECHERCHE = r"""
$ErrorActionPreference = 'Stop'
Import-Module Microsoft.WinGet.Client
$r = Find-WinGetPackage -Query $env:MARTINET_REQUETE | Select-Object -First 8 | ForEach-Object {
    [pscustomobject]@{ id = [string]$_.Id; nom = [string]$_.Name; version = [string]$_.Version; source = [string]$_.Source } }
'###JSON###'
ConvertTo-Json -InputObject @($r) -Compress
"""


def rechercher(requete: str) -> list[Paquet]:
    """Candidats winget pour un logiciel non suivi (par son nom)."""
    if demo.actif():
        demo.pause(0.4)
        if "nina" in requete.lower().replace(".", ""):
            return [Paquet("NINA.NINA", "N.I.N.A. - Nighttime Imaging 'N' Astronomy", "3.2.0.9001",
                           source="winget")]
        return []
    import os
    requete = re.sub(r"\(.*?\)|\d[\d.]*|x64|x86|64-bit|32-bit", " ", requete)
    requete = " ".join(requete.split()[:3])
    os.environ["MARTINET_REQUETE"] = requete
    code, sortie = systeme.powershell(SCRIPT_RECHERCHE, timeout=120)
    donnees = systeme.json_de_sortie(sortie)
    if code == 0 and donnees is not None:
        return [Paquet(d["id"], d["nom"], d.get("version", ""), source=d.get("source", ""))
                for d in systeme.en_liste(donnees)]
    code, texte = systeme.executer(["winget", "search", requete, *ACCORDS], timeout=120)
    return [Paquet(c[1], c[0], c[2] if len(c) > 2 else "", source=c[-1])
            for c in lire_tableau(texte)][:8]

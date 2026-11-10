"""Logiciels que winget ne suit pas : où trouver leur dernière version.

Trois façons de connaître la dernière version publiée :

* **nvidia** — le service de NVIDIA interrogé avec l'identifiant de la carte
  graphique (celui qu'utilise l'application NVIDIA) : version, date, lien
  direct de l'installeur officiel ;
* **github** — les Releases d'un dépôt (étiquettes de préversion écartées) ;
* **page** — la page de téléchargement de l'éditeur, lue avec un motif.

Le catalogue fourni (sources_defaut.json) se complète par les sources que
l'utilisateur ajoute ; elles sont rangées dans ses données (sources.json).
"""
from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from . import demo, systeme
from .materiel import Carte
from .versions import la_plus_haute, plus_recente

DEFAUT = Path(__file__).resolve().parent / "sources_defaut.json"
API_NVIDIA = ("https://gfwsl.geforce.com/nvidia_web_services/controller.gfeclientcontent.NG.php/"
              "com.nvidia.services.GFEClientContent_NG.getDispDrvrByDevid/")
TYPES = ("github", "page")


@dataclass
class Source:
    id: str
    nom: str
    motif: str                    # expression régulière sur le nom installé
    type: str                     # github, page
    depot: str = ""
    url: str = ""
    regex: str = ""
    exclure_tag: str = ""
    exclure_apres: str = ""
    fichier: str = ""             # motif du fichier à télécharger (github)
    page: str = ""                # page de téléchargement à ouvrir
    perso: bool = False

    def correspond(self, nom_installe: str) -> bool:
        try:
            return re.search(self.motif, nom_installe, re.I) is not None
        except re.error:
            return False

    def vers_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if v and k != "perso"}
        return d


@dataclass
class Resultat:
    nom: str                      # nom affiché du logiciel
    installee: str
    derniere: str = ""
    etat: str = "inconnu"         # a_jour, maj, erreur, inconnu
    page: str = ""
    fichier: str = ""             # lien direct de l'installeur, s'il est connu
    erreur: str = ""
    source: str = ""              # id de la source, « nvidia » pour la carte
    details: dict = field(default_factory=dict)


# ------------------------------------------------------------ catalogue
def _fichier_perso() -> Path:
    return systeme.dossier_donnees() / "sources.json"


def charger() -> list[Source]:
    sources = [Source(**d) for d in json.loads(DEFAUT.read_text(encoding="utf-8"))]
    try:
        perso = json.loads(_fichier_perso().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        perso = []
    ids = {s.id for s in sources}
    for d in perso:
        d = {k: v for k, v in d.items() if k in Source.__dataclass_fields__}
        d["perso"] = True
        s = Source(**d)
        if s.id in ids:                    # une source perso remplace celle du catalogue
            sources = [x for x in sources if x.id != s.id]
        sources.append(s)
    return sources


def enregistrer_perso(sources: list[Source]) -> None:
    donnees = [s.vers_dict() for s in sources if s.perso]
    _fichier_perso().write_text(json.dumps(donnees, ensure_ascii=False, indent=2), encoding="utf-8")


def nouvel_id(nom: str, existants: set[str]) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", nom.lower()).strip("-") or "source"
    ident, n = base, 2
    while ident in existants:
        ident, n = f"{base}-{n}", n + 1
    return ident


# ------------------------------------------------------------ dernière version
def texte_de_page(contenu: str) -> str:
    contenu = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", contenu)
    contenu = html.unescape(re.sub(r"<[^>]+>", " ", contenu))
    return re.sub(r"\s+", " ", contenu)


def version_dans_page(texte: str, regex: str, exclure_apres: str = "") -> str | None:
    trouvees = []
    for m in re.finditer(regex, texte):
        if exclure_apres and re.search(exclure_apres, texte[m.end():m.end() + 30], re.I):
            continue
        trouvees.append(m.group(1) if m.groups() else m.group(0))
    return la_plus_haute(trouvees)


def derniere_github(depot: str, exclure_tag: str = "", fichier: str = "") -> tuple[str, str, str]:
    """(version, page de la Release, lien de l'installeur ou « »)."""
    rels = systeme.telecharger_json(f"https://api.github.com/repos/{depot}/releases?per_page=30")
    for r in rels:
        tag = r.get("tag_name") or ""
        if r.get("draft") or r.get("prerelease"):
            continue
        if exclure_tag and re.search(exclure_tag, tag, re.I):
            continue
        lien = ""
        if fichier:
            for a in r.get("assets") or []:
                if re.search(fichier, a.get("name", ""), re.I):
                    lien = a.get("browser_download_url", "")
                    break
        return tag.lstrip("vV"), r.get("html_url", ""), lien
    raise LookupError("aucune version publiée")


def derniere(source: Source) -> tuple[str, str, str]:
    if source.type == "github":
        version, page, lien = derniere_github(source.depot, source.exclure_tag, source.fichier)
        return version, source.page or page, lien
    if source.type == "page":
        texte = texte_de_page(systeme.telecharger_texte(source.url))
        v = version_dans_page(texte, source.regex, source.exclure_apres)
        if not v:
            raise LookupError("version introuvable sur la page")
        return v, source.page or source.url, ""
    raise ValueError(f"type de source inconnu : {source.type}")


def verifier(source: Source, nom_installe: str, installee: str) -> Resultat:
    res = Resultat(nom_installe, installee, source=source.id, page=source.page or source.url)
    if demo.actif():
        demo.pause(0.2)
        fausses = {"phd2": "2.6.14", "ascom": "7.1.3", "nina": "3.2", "astap": "2026.07.16"}
        res.derniere = fausses.get(source.id, installee)
    else:
        try:
            res.derniere, res.page, res.fichier = derniere(source)
        except Exception as exc:
            res.etat, res.erreur = "erreur", str(exc)[:200]
            return res
    res.etat = "maj" if plus_recente(res.derniere, installee) else "a_jour"
    return res


# ------------------------------------------------------------ NVIDIA
def url_nvidia(id_peripherique: str) -> str:
    requete = {"dIDa": [f"{id_peripherique.upper()}_10DE"], "osC": "10.0", "osB": "19041",
               "is6": "1", "lg": "1033", "iLp": "1", "prvMd": "0", "gcV": "3.25.1.27",
               "gIsB": "0", "dch": "1", "upCRD": "0", "isCRD": "0"}
    return API_NVIDIA + json.dumps(requete, separators=(",", ":"))


def lire_reponse_nvidia(donnees: dict) -> dict:
    attr = donnees.get("DriverAttributes") or {}
    if not attr.get("Version"):
        raise LookupError("carte inconnue du service NVIDIA")
    return {"version": attr["Version"], "date": (attr.get("ReleaseDateTime") or "")[:10],
            "nom": attr.get("Name") or "", "fichier": attr.get("DownloadURLAdmin") or attr.get("DownloadURL") or "",
            "page": attr.get("DetailsURL") or "https://www.nvidia.com/drivers/"}


def verifier_carte(carte: Carte) -> Resultat:
    res = Resultat(carte.nom, carte.version, source=carte.fabricant)
    if carte.fabricant != "nvidia":
        res.page = {"amd": "https://www.amd.com/support/download/drivers.html",
                    "intel": "https://www.intel.com/content/www/us/en/support/detect.html"
                    }.get(carte.fabricant, "")
        res.etat = "inconnu"
        return res
    if demo.actif():
        demo.pause(0.2)
        infos = {"version": "621.14", "date": "2026-11-04", "nom": "GeForce Game Ready Driver",
                 "fichier": "https://us.download.nvidia.com/Windows/621.14/exemple.exe",
                 "page": "https://www.nvidia.com/drivers/"}
    else:
        try:
            infos = lire_reponse_nvidia(systeme.telecharger_json(url_nvidia(carte.id_peripherique)))
        except Exception as exc:
            res.etat, res.erreur = "erreur", str(exc)[:200]
            res.page = "https://www.nvidia.com/drivers/"
            return res
    res.derniere, res.page, res.fichier = infos["version"], infos["page"], infos["fichier"]
    res.details = {"date": infos["date"], "nom": infos["nom"]}
    res.etat = "maj" if plus_recente(res.derniere, carte.version) else "a_jour"
    return res

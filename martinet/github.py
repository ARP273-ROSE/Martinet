"""Dernière Release d'un dépôt GitHub, même quand l'API refuse.

L'API de GitHub n'accepte que 60 demandes par heure et par adresse IP sans
compte. Derrière un VPN, l'adresse est partagée avec d'autres : la limite est
vite atteinte (« HTTP Error 403: rate limit exceeded »). Dans ce cas, on lit les
pages publiques de github.com, qui ne sont pas comptées :

* ``/releases/latest`` redirige vers l'étiquette de la dernière version stable ;
* ``/releases.atom`` liste les étiquettes récentes (pour écarter certaines) ;
* ``/releases/expanded_assets/<étiquette>`` liste les fichiers joints.

Le résultat a la forme d'une réponse de l'API (tag_name, html_url, assets).
Une variable d'environnement GITHUB_TOKEN, si elle existe, est utilisée.
"""
from __future__ import annotations

import html
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from . import systeme

API = "https://api.github.com/repos/{depot}/releases"
SITE = "https://github.com/{depot}/releases"
PREVERSION = re.compile(r"(alpha|beta|\brc|-rc|pre|preview|nightly|dev|test)", re.I)
DUREE_CACHE = 600                     # s : « Vérifier » deux fois de suite ne recompte pas
_cache: dict[tuple, tuple[float, dict]] = {}
_api_limitee_jusqu_a = 0.0            # après un refus, on ne réessaie pas l'API tout de suite


def _ouvrir(url: str, timeout: float, api: bool = False):
    entetes = {"User-Agent": systeme.AGENT}
    if api:
        entetes["Accept"] = "application/vnd.github+json"
        jeton = os.environ.get("GITHUB_TOKEN", "").strip()
        if jeton:
            entetes["Authorization"] = f"Bearer {jeton}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=entetes), timeout=timeout)


def _texte(url: str, timeout: float) -> tuple[str, str]:
    """(contenu, adresse finale après redirections)."""
    with _ouvrir(url, timeout) as r:
        return r.read().decode("utf-8", "replace"), r.geturl()


def _limite(exc: Exception) -> bool:
    return isinstance(exc, urllib.error.HTTPError) and exc.code in (403, 429)


# ------------------------------------------------------------ par l'API
def _par_api(depot: str, exclure_tag: str, timeout: float) -> dict | None:
    import json
    if not exclure_tag:
        with _ouvrir(API.format(depot=depot) + "/latest", timeout, api=True) as r:
            return json.loads(r.read().decode("utf-8"))
    with _ouvrir(API.format(depot=depot) + "?per_page=30", timeout, api=True) as r:
        rels = json.loads(r.read().decode("utf-8"))
    for rel in rels:
        tag = rel.get("tag_name") or ""
        if rel.get("draft") or rel.get("prerelease") or re.search(exclure_tag, tag, re.I):
            continue
        return rel
    return None


# ------------------------------------------------------------ par le site
def etiquettes_atom(contenu: str) -> list[str]:
    """Étiquettes du flux releases.atom, de la plus récente à la plus ancienne."""
    return [urllib.parse.unquote(html.unescape(t))
            for t in re.findall(r'href="[^"]*/releases/tag/([^"]+)"', contenu)]


def fichiers_joints(contenu: str, depot: str, tag: str) -> list[dict]:
    vus, assets = set(), []
    prefixe = f"/{depot}/releases/download/"
    for lien in re.findall(r'href="([^"]*/releases/download/[^"]+)"', contenu):
        lien = html.unescape(lien)
        if not lien.lower().startswith(prefixe.lower()) or lien in vus:
            continue
        vus.add(lien)
        nom = urllib.parse.unquote(lien.rsplit("/", 1)[-1])
        assets.append({"name": nom, "browser_download_url": "https://github.com" + lien})
    return assets


def _par_site(depot: str, exclure_tag: str, timeout: float) -> dict | None:
    site = SITE.format(depot=depot)
    tag = ""
    try:
        _, finale = _texte(site + "/latest", timeout)
        m = re.search(r"/releases/tag/([^/?#]+)$", finale)
        if m:
            tag = urllib.parse.unquote(m.group(1))
    except urllib.error.HTTPError as exc:
        if exc.code != 404:                   # 404 : aucune version stable marquée « latest »
            raise
    if not tag or (exclure_tag and re.search(exclure_tag, tag, re.I)):
        tag = ""
        contenu, _ = _texte(site + ".atom", timeout)
        for t in etiquettes_atom(contenu):
            if PREVERSION.search(t) or (exclure_tag and re.search(exclure_tag, t, re.I)):
                continue
            tag = t
            break
    if not tag:
        return None
    contenu, _ = _texte(f"{site}/expanded_assets/{urllib.parse.quote(tag)}", timeout)
    return {"tag_name": tag, "html_url": f"{site}/tag/{urllib.parse.quote(tag)}",
            "assets": fichiers_joints(contenu, depot, tag)}


# ------------------------------------------------------------ entrée
def derniere_release(depot: str, exclure_tag: str = "", timeout: float = 20) -> dict | None:
    """Dernière Release stable (brouillons, préversions et étiquettes exclues écartés),
    sous la forme d'une réponse de l'API ; None si le dépôt n'en a aucune."""
    global _api_limitee_jusqu_a
    cle = (depot.lower(), exclure_tag)
    deja = _cache.get(cle)
    if deja and time.monotonic() - deja[0] < DUREE_CACHE:
        return deja[1]
    rel = None
    if time.monotonic() >= _api_limitee_jusqu_a:
        try:
            rel = _par_api(depot, exclure_tag, timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 404 and not exclure_tag:
                rel = None                    # aucune Release stable
            elif _limite(exc):
                _api_limitee_jusqu_a = time.monotonic() + DUREE_CACHE
                rel = _par_site(depot, exclure_tag, timeout)
            else:
                raise
    else:
        rel = _par_site(depot, exclure_tag, timeout)
    _cache[cle] = (time.monotonic(), rel)
    return rel


def vider_cache() -> None:
    global _api_limitee_jusqu_a
    _cache.clear()
    _api_limitee_jusqu_a = 0.0

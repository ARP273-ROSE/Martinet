"""Garde-fous de traduction."""
import re
import string
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
from martinet import i18n, menage  # noqa: E402


def champs(modele: str) -> set:
    return {nom for _, nom, _, _ in string.Formatter().parse(modele) if nom}


def test_toutes_les_cles_dans_les_deux_langues():
    for cle, textes in i18n.TEXTES.items():
        for lg in i18n.LANGUES:
            assert textes.get(lg, "").strip(), f"{cle} : texte {lg} vide ou absent"


def test_memes_champs_de_format():
    for cle, textes in i18n.TEXTES.items():
        assert champs(textes["fr"]) == champs(textes["en"]), cle


def test_chaque_cle_utilisee_existe():
    """Une clé appelée par tr("…") sans texte afficherait la clé elle-même."""
    manquantes = []
    for f in [RACINE / "run.py", *sorted((RACINE / "martinet").glob("*.py"))]:
        for cle in re.findall(r'tr\("([a-z_.0-9]+)"[,)]', f.read_text(encoding="utf-8")):
            if cle not in i18n.TEXTES:
                manquantes.append(f"{f.name}: {cle}")
    assert not manquantes, manquantes


def test_cles_construites_existent():
    from martinet.pages import PAGES
    from martinet import windows_update
    attendues = [f"page.{p.cle}" for p in PAGES] + [f"page.{p.cle}.aide" for p in PAGES]
    attendues += [f"menage.{e.cle}" for e in menage.ELEMENTS] + [f"menage.{e.cle}.aide" for e in menage.ELEMENTS]
    attendues += [f"jour.{i}" for i in range(7)] + ["lieu.bureau", "lieu.demarrer", "lieu.barre"]
    attendues += [f"wu.code.{c}" for c in windows_update.CODES.values()]
    attendues += [f"etape.{e}" for e in ("programmes", "cartes", "windows", "raccourcis", "menage")]
    attendues += ["mode.manuel", "mode.auto", "src.type_github", "src.type_page"]
    assert [c for c in attendues if c not in i18n.TEXTES] == []


def test_cle_inconnue_ne_casse_rien():
    assert i18n.tr("cle.qui.n.existe.pas") == "cle.qui.n.existe.pas"


def test_detection_par_environnement(monkeypatch):
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("LANG", "fr_FR.UTF-8")
    assert i18n.detecter() == "fr"
    monkeypatch.setenv("LANG", "de_DE.UTF-8")
    assert i18n.detecter() == "en"


def test_option_version():
    sortie = subprocess.run([sys.executable, str(RACINE / "run.py"), "--version"],
                            capture_output=True, text=True, timeout=60)
    assert sortie.returncode == 0 and sortie.stdout.startswith("Martinet ")

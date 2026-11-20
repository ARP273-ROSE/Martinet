# -*- coding: utf-8 -*-
"""Common kit consistency (installer, updates, packages).

These mismatches only show at the user's: a named mutex the installer does
not know, a version written twice, a kit.json key forgotten, user data
travelling in the update archive, a second publishing workflow.
"""
import json
import re
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
KIT = json.loads((RACINE / 'kit.json').read_text(encoding='utf-8'))
sys.path.insert(0, str(RACINE))


def test_verrou_nomme_identique_a_l_installeur():
    iss = (RACINE / 'installer.iss').read_text(encoding='utf-8')
    assert 'AppMutex={#AppName}EnCours' in iss
    entree = (RACINE / KIT['point_entree']).read_text(encoding='utf-8')
    assert 'f"{NOM}EnCours"' in entree and f'NOM = "{KIT["nom_fichier"]}"' in entree


def test_version_unique():
    version = (RACINE / KIT['fichier_version']).read_text(encoding='utf-8').strip()
    assert re.fullmatch(r'\d+\.\d+\.\d+', version)
    journal = (RACINE / 'CHANGELOG.md').read_text(encoding='utf-8')
    assert re.search(rf'^### {re.escape(version)}$', journal, re.M), "CHANGELOG sans la version"
    import martinet
    assert martinet.__version__ == version


def test_kit_json_complet():
    for cle in ('nom_technique', 'nom_fichier', 'nom_affiche', 'depot_distribution',
                'point_entree', 'icone', 'appid', 'icone_png',
                'description_fr', 'description_en', 'categories_linux'):
        assert KIT.get(cle), cle
    for chemin in [KIT['point_entree'], KIT['icone_png'],
                   *KIT['modules'], *KIT['paquets'], *KIT['assets']]:
        assert (RACINE / chemin).exists(), chemin


def test_donnees_de_l_utilisateur_hors_de_l_archive():
    for nom in ('_rapports', 'reglages_rapports.json'):
        assert nom in KIT['fichiers_proteges'], nom


def test_un_seul_workflow_de_publication():
    wf = RACINE / '.github' / 'workflows'
    publient = [p.name for p in wf.glob('*.yml')
                if 'action-gh-release' in p.read_text(encoding='utf-8')
                or 'gh release create' in p.read_text(encoding='utf-8')]
    assert publient == ['release.yml'], publient


def test_une_seule_source_pour_le_logo():
    svg = (RACINE / 'logo.svg').read_text(encoding='utf-8')
    assert svg.lstrip().startswith('<?xml') and '<svg' in svg
    for taille in (16, 32, 64, 128, 256, 512):
        assert (RACINE / f'logo_{taille}.png').exists(), taille


def test_ecarter_retente_si_fichier_verrouille(tmp_path, monkeypatch):
    """Un antivirus qui tient le fichier quelques secondes ne fait pas échouer la mise à jour."""
    import shutil
    import updater
    src = tmp_path / "run.py"
    src.write_text("x")
    vrai_move = shutil.move
    refus = {"n": 2}

    def move(a, b):
        if refus["n"]:
            refus["n"] -= 1
            raise PermissionError(5, "Accès refusé", a)
        return vrai_move(a, b)

    monkeypatch.setattr(updater.shutil, "move", move)
    updater._ecarter(src, tmp_path / "ailleurs.py", pause=0)
    assert (tmp_path / "ailleurs.py").read_text() == "x"


def test_ecarter_abandonne_apres_les_essais(tmp_path, monkeypatch):
    import pytest
    import updater
    src = tmp_path / "run.py"
    src.write_text("x")

    def move(a, b):
        raise PermissionError(5, "Accès refusé", a)

    monkeypatch.setattr(updater.shutil, "move", move)
    with pytest.raises(PermissionError):
        updater._ecarter(src, tmp_path / "b", essais=3, pause=0)

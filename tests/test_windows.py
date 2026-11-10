"""Essais sur un VRAI Windows (CI windows-latest) : registre, PowerShell,
raccourcis créés par Windows lui-même, Windows Update, winget.

Ignorés ailleurs. MARTINET_DEMO est forcé à 0 : on veut le vrai système.
"""
import os
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows seulement")


@pytest.fixture(autouse=True)
def vrai_systeme(monkeypatch):
    monkeypatch.setenv("MARTINET_DEMO", "0")
    from martinet import demo
    monkeypatch.setattr(demo, "actif", lambda: False)


def creer_raccourci(lnk: Path, cible: str):
    from martinet import systeme
    script = (f"$s = (New-Object -ComObject WScript.Shell).CreateShortcut('{lnk}');"
              f"$s.TargetPath = '{cible}'; $s.Save()")
    code, sortie = systeme.powershell(script, timeout=60)
    assert code == 0 and lnk.exists(), sortie


def test_powershell_json():
    from martinet import systeme
    code, sortie = systeme.powershell("'###JSON###'; ConvertTo-Json @{a = 'é'; n = 3} -Compress")
    assert code == 0 and systeme.json_de_sortie(sortie) == {"a": "é", "n": 3}


def test_lecture_de_vrais_raccourcis(tmp_path):
    from martinet import raccourcis
    vivant = tmp_path / "vivant.lnk"
    creer_raccourci(vivant, os.path.join(os.environ["SystemRoot"], "notepad.exe"))
    c = raccourcis.lire_lnk(vivant.read_bytes())
    assert c.chemin.lower().endswith("notepad.exe") and raccourcis.verdict(c.chemin) == "ok"
    cible_morte = tmp_path / "parti" / "outil.exe"
    cible_morte.parent.mkdir()
    cible_morte.write_text("")
    mort = tmp_path / "mort.lnk"
    creer_raccourci(mort, str(cible_morte))
    cible_morte.unlink()
    c = raccourcis.lire_lnk(mort.read_bytes())
    assert Path(c.chemin) == cible_morte and raccourcis.verdict(c.chemin) == "mort"


def test_raccourci_mort_sur_le_bureau_mis_de_cote_puis_restaure(tmp_path):
    from martinet import raccourcis
    bureau = Path(os.environ["USERPROFILE"]) / "Desktop"
    bureau.mkdir(exist_ok=True)
    cible = tmp_path / "disparu.exe"
    cible.write_text("")
    lnk = bureau / "Essai Martinet.lnk"
    creer_raccourci(lnk, str(cible))
    cible.unlink()
    try:
        morts = [r for r in raccourcis.chercher_morts() if Path(r.fichier).name == lnk.name]
        assert len(morts) == 1
        n, erreurs = raccourcis.mettre_de_cote(morts)
        assert n == 1 and not erreurs and not lnk.exists()
        elements = [e for e in raccourcis.mis_de_cote() if e.fichier == lnk.name]
        assert raccourcis.restaurer(elements)[0] == 1 and lnk.exists()
    finally:
        lnk.unlink(missing_ok=True)


def test_registre_et_carte_graphique():
    from martinet import materiel
    logiciels = materiel.logiciels_du_registre()
    assert len(logiciels) > 5 and all(n for n, _v, _e in logiciels)
    for c in materiel.cartes_graphiques():          # le runner n'a pas de NVIDIA : pas de plantage
        assert c.id_peripherique and c.fabricant


def test_mesures_du_menage():
    from martinet import menage
    for e in menage.ELEMENTS:
        if e.cle != "composants":
            taille, nombre = menage.mesurer(e.cle)
            assert taille is not None and taille >= 0


def test_windows_update_recherche():
    from martinet import windows_update
    liste = windows_update.rechercher()
    assert isinstance(liste, list)
    for m in liste:
        assert m.id and m.titre


def test_winget_inventaire():
    from martinet import systeme, winget
    if systeme.executer(["winget", "--version"], timeout=60)[0] != 0:
        pytest.skip("winget absent de ce Windows")
    inv = winget.inventaire(print)
    assert inv.paquets, inv.erreur
    assert any(p.suivi for p in inv.paquets)


def test_planification_aller_retour():
    from martinet import planif, systeme
    if not systeme.est_admin():
        pytest.skip("droits administrateur nécessaires")
    ok, detail = planif.creer("hebdo", 6, "12:00")
    try:
        assert ok, detail
        etat = planif.etat()
        assert etat and etat["prochaine"]
    finally:
        assert planif.supprimer()[0]
    assert planif.etat() is None

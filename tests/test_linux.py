"""Mode Linux (Manjaro / Arch) : lecture des sorties, lanceurs, ménage, interface."""
import os

import pytest

from martinet import linux_paquets as lp


@pytest.fixture
def linux(monkeypatch):
    monkeypatch.setenv("MARTINET_SYSTEME", "linux")


def test_lire_mises_a_jour_pamac():
    texte = ("2 available updates:\nwhich  0.1-1 -> 2.25-1  core\n"
             "visual-studio-code-bin  1.105.1-1 -> 1.106.0-1  AUR\n")
    p = lp.lire_mises_a_jour(texte)
    assert [(x.nom, x.installee, x.disponible, x.origine) for x in p] == [
        ("which", "0.1-1", "2.25-1", "depots"), ("visual-studio-code-bin", "1.105.1-1", "1.106.0-1", "aur")]


def test_lire_checkupdates_et_yay():
    assert lp.lire_mises_a_jour("mesa 1:25.2.6-1 -> 1:25.2.7-1\n")[0].disponible == "1:25.2.7-1"
    assert lp.lire_mises_a_jour("yay 13.0.0-1 -> 13.0.1-1\n", "aur")[0].origine == "aur"
    assert lp.lire_mises_a_jour("Synchronizing package databases...\n") == []


def test_lire_flatpak():
    maj = "org.stellarium.Stellarium\tStellarium\t25.4\norg.gnome.Platform\tGNOME\t48\n"
    inst = "org.stellarium.Stellarium\t25.3\n"
    p = lp.lire_flatpak(maj, inst)
    assert (p[0].nom, p[0].installee, p[0].disponible, p[0].ident) == ("Stellarium", "25.3", "25.4",
                                                                      "org.stellarium.Stellarium")


def test_orphelins_et_tailles():
    qi = ("Name            : python-sphinx\nVersion : 8.2\nInstalled Size  : 14.60 MiB\n\n"
          "Name            : qt5-tools\nInstalled Size  : 9.8 MiB\n")
    assert lp.lire_orphelins(qi) == [("python-sphinx", int(14.6 * 1024 ** 2)), ("qt5-tools", int(9.8 * 1024 ** 2))]
    assert lp.lire_taille("1.5 GiB") == int(1.5 * 1024 ** 3)


def test_noyaux_fin_de_vie():
    assert lp.noyaux_fin_de_vie(["linux66", "yay", "linux61-rt", "linux-firmware"]) == ["linux66", "linux61-rt"]


def test_fwupd():
    d = {"Devices": [{"Name": "UEFI", "Version": "1.0", "Releases": [{"Version": "1.2", "Summary": "x"}]},
                     {"Name": "Souris", "Version": "2", "Releases": []}]}
    m = lp.lire_fwupd(d)
    assert len(m) == 1 and (m[0].appareil, m[0].installee, m[0].disponible) == ("UEFI", "1.0", "1.2")


def test_pacnew(tmp_path):
    (tmp_path / "pacman.conf.pacnew").write_text("x")
    (tmp_path / "sous").mkdir()
    (tmp_path / "sous" / "a.pacsave").write_text("x")
    (tmp_path / "b.conf").write_text("x")
    assert [os.path.basename(p) for p in lp.chercher_pacnew(str(tmp_path))] == ["pacman.conf.pacnew", "a.pacsave"]


def test_regle_polkit_limitee_a_pamac():
    t = lp.texte_regle("utilisateur")
    assert 'action.id == "org.manjaro.pamac.commit"' in t and 'subject.user == "utilisateur"' in t


def test_paccache_et_journal():
    from martinet import menage_linux as ml
    assert ml.lire_paccache("==> finished dry run: 63 candidates (disk space saved: 1.20 GiB)") == (
        int(1.2 * 1024 ** 3), 63)
    assert ml.lire_journal("Archived and active journals take up 1.2G in the file system.") == int(1.2 * 1024 ** 3)


def test_lanceurs_morts(tmp_path, monkeypatch, linux):
    from martinet import raccourcis
    monkeypatch.setenv("MARTINET_DEMO", "0")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    apps = tmp_path / "data" / "applications"
    apps.mkdir(parents=True)
    (apps / "mort.desktop").write_text("[Desktop Entry]\nType=Application\nName=X\nExec=/opt/disparu/x %U\n")
    (apps / "vivant.desktop").write_text("[Desktop Entry]\nType=Application\nName=Y\nExec=env A=1 sh -c true\n")
    (apps / "lien.desktop").write_text("[Desktop Entry]\nType=Link\nURL=https://exemple.org\n")
    (apps / "amovible.desktop").write_text("[Desktop Entry]\nType=Application\nExec=/media/absent/prog\n")
    morts = raccourcis.chercher_morts()
    assert [os.path.basename(m.fichier) for m in morts] == ["mort.desktop"]
    assert morts[0].cible == "/opt/disparu/x" and morts[0].lieu == "menu"
    n, err = raccourcis.mettre_de_cote(morts)
    assert n == 1 and not err and not (apps / "mort.desktop").exists()
    assert raccourcis.restaurer(raccourcis.mis_de_cote())[0] == 1 and (apps / "mort.desktop").exists()


def test_bureau_xdg(tmp_path, monkeypatch):
    from martinet import raccourcis
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "c"))
    (tmp_path / "c").mkdir()
    (tmp_path / "c" / "user-dirs.dirs").write_text('XDG_DESKTOP_DIR="$HOME/Bureau"\n')
    assert raccourcis.dossier_bureau_linux() == tmp_path / "Bureau"


def test_minuteur_systemd(monkeypatch):
    from martinet import planif
    service, timer = planif.unites_systemd("hebdo", 6, "12:00")
    assert "OnCalendar=Sun *-*-* 12:00:00" in timer and "Persistent=true" in timer
    assert "--auto" in service and "Type=oneshot" in service
    assert "OnCalendar=*-*-* 07:30:00" in planif.unites_systemd("quotidien", 0, "07:30")[1]


def test_menage_linux_demo(linux):
    from martinet import menage
    cles = [e.cle for e in menage.elements()]
    assert "cache_paquets" in cles and "temp_windows" not in cles
    assert menage.mesurer("cache_paquets")[0] > 0
    assert menage.nettoyer_tout(["cache_paquets", "miniatures"]) > 0


def test_orchestre_linux_demo(linux):
    from martinet import orchestre
    from martinet.reglages import Reglages
    b = orchestre.verifier_tout(Reglages())
    assert b.paquets and b.lx is not None and b.morts and b.menage and b.inventaire is None
    resume = orchestre.tout_mettre_a_jour(Reglages(), bilan=b)
    texte = "\n".join(resume)
    assert "Paquets" in texte or "Packages" in texte
    assert "linux66" in texte


def test_textes_linux_existent(linux):
    from martinet import i18n, menage
    from martinet.pages import pages_du_systeme
    attendues = [f"page.{p.cle}" for p in pages_du_systeme()] + [f"page.{p.cle}.aide" for p in pages_du_systeme()]
    attendues += [f"menage.{e.cle}" for e in menage.elements()] + [f"menage.{e.cle}.aide" for e in menage.elements()]
    attendues += ["lieu.menu", "lieu.autostart", "lieu.bureau"] + [f"lx.origine.{o}" for o in ("depots", "aur", "flatpak")]
    attendues += [f"lx.etape.{e}" for e in ("programmes", "windows", "raccourcis", "menage")]
    assert [c for c in attendues if c not in i18n.TEXTES] == []
    assert i18n.tr("page.raccourcis") in ("Lanceurs morts", "Dead launchers")


@pytest.fixture
def boites(monkeypatch):
    from PyQt6 import QtWidgets
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    B = QtWidgets.QMessageBox
    monkeypatch.setattr(B, "information", lambda *a, **k: None)
    monkeypatch.setattr(B, "warning", lambda *a, **k: None)
    monkeypatch.setattr(B, "question", lambda *a, **k: B.StandardButton.Yes)
    return app


def _fermer(w):
    w.file.annuler()
    w.file.attendre(10000)
    w.close()


def test_fenetre_linux(boites, linux):
    from martinet.fenetre import FenetrePrincipale
    w = FenetrePrincipale()
    assert [c.cle for c in w._classes] == ["accueil", "paquets", "systeme", "raccourcis", "menage", "planif",
                                          "historique"]
    w.file.attendre(10000)
    w.verifier_tout()
    assert w.file.attendre(30000)
    assert "Flatpak" in w.plan_tout(w.bilan, True)
    w.tout_mettre_a_jour()
    assert w.file.attendre(30000)
    _fermer(w)


def test_windows10(boites, monkeypatch):
    from PyQt6 import QtWidgets
    from martinet import systeme
    from martinet.fenetre import FenetrePrincipale
    monkeypatch.setenv("MARTINET_WINDOWS10", "1")
    assert systeme.windows10()
    w = FenetrePrincipale()
    assert any(l.objectName() == "avertissement" for l in w.pages["windows"].findChildren(QtWidgets.QLabel))
    _fermer(w)


def test_tailles_dans_la_langue():
    from martinet import menage
    from martinet.i18n import definir_langue, langue
    avant = langue()
    try:
        definir_langue("en")
        assert menage.taille_lisible(3 * 1024 ** 3) == "3.0 GB"
        definir_langue("fr")
        assert menage.taille_lisible(3 * 1024 ** 3) == "3,0 Go"
    finally:
        definir_langue(avant)

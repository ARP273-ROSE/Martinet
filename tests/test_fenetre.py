"""La fenêtre sans écran (QT_QPA_PLATFORM=offscreen), en mode démonstration.

Parcourt le chemin d'un utilisateur : tout vérifier, regarder chaque page,
mettre à jour une sélection, tout mettre à jour, changer de langue — et
vérifie que le fil graphique n'est jamais bloqué pendant le travail.
"""
import time

import pytest
from PyQt6 import QtCore, QtWidgets

from martinet import style
from martinet.i18n import definir_langue

definir_langue("fr")


@pytest.fixture(scope="module")
def app():
    a = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    style.appliquer(a)
    return a


@pytest.fixture
def fen(app, monkeypatch):
    from martinet.fenetre import FenetrePrincipale
    messages = []
    monkeypatch.setattr(QtWidgets.QMessageBox, "information", lambda *a, **k: messages.append(a[2]))
    monkeypatch.setattr(QtWidgets.QMessageBox, "warning", lambda *a, **k: messages.append(a[2]))
    monkeypatch.setattr(QtWidgets.QMessageBox, "question",
                        lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes)
    w = FenetrePrincipale()
    w.messages = messages
    w.show()
    w.file.attendre(10000)
    yield w
    w.file.annuler()
    w.file.attendre(10000)
    w.close()


def test_verifier_tout_sans_bloquer(app, fen, monkeypatch):
    monkeypatch.delenv("MARTINET_DEMO_RAPIDE")          # pauses réelles : le travail dure
    battements = []
    minuteur = QtCore.QTimer()
    minuteur.timeout.connect(lambda: battements.append(time.time()))
    minuteur.start(20)
    fen.verifier_tout()
    assert fen.file.attendre(30000)
    minuteur.stop()
    assert len(battements) > 3, "la boucle d'événements a été bloquée"
    b = fen.bilan
    assert b.inventaire and b.windows and b.morts and b.menage and b.cartes and not b.erreurs
    assert fen.pages["programmes"].table.rowCount() == 6
    assert fen.pages["hors"].t_sources.rowCount() == 4
    assert fen.pages["windows"].table.rowCount() == 4
    assert fen.pages["raccourcis"].table.rowCount() == 3
    assert "6 mise(s) à jour" in fen.pages["accueil"].cartes["programmes"].text()
    # facultatives incluses par défaut ; décochées si le réglage est retiré
    assert len(fen.pages["windows"].table.donnees()) == 4
    fen.pages["windows"].c_facultatives.setChecked(False)
    assert len(fen.pages["windows"].table.donnees()) == 3 and not fen.reglages.facultatives
    fen.pages["windows"].c_facultatives.setChecked(True)


def test_mettre_a_jour_une_selection_et_ignorer(app, fen):
    fen.verifier_tout({"programmes"})
    fen.file.attendre(30000)
    page = fen.pages["programmes"]
    page.table.tout_cocher(False)
    page.table.item(0, 0).setCheckState(QtCore.Qt.CheckState.Checked)
    page.mettre_a_jour()
    assert fen.file.attendre(30000)
    assert fen.messages and fen.messages[-1].startswith("Programmes : 1 sur 1")
    assert page.table.rowCount() == 5
    page.table.selectRow(0)
    page.ignorer()
    assert len(fen.reglages.ignores_winget) == 1 and page.table.rowCount() == 4
    assert fen.pages["historique"].table.rowCount() >= 1


def test_tout_mettre_a_jour(app, fen):
    fen.verifier_tout()
    fen.file.attendre(30000)
    fen.tout_mettre_a_jour()
    assert fen.file.attendre(60000)
    texte = "\n".join(fen.messages)
    assert "Programmes : 6 sur 6 mis à jour." in texte and "Ménage" in texte
    assert "À faire à la main : PHD2" in texte


def test_raccourcis_et_menage(app, fen):
    fen.verifier_tout({"raccourcis", "menage"})
    fen.file.attendre(30000)
    fen.pages["raccourcis"].mettre_de_cote()
    assert fen.pages["raccourcis"].table.rowCount() == 0
    fen.pages["menage"].nettoyer()
    assert fen.file.attendre(30000)
    assert any("libérés" in m for m in fen.messages)


def test_changer_de_langue(app, fen):
    fen.verifier_tout({"programmes"})
    fen.file.attendre(30000)
    fen._changer_langue("en")
    try:
        assert fen.nav.item(0).text() == "Dashboard"
        assert fen.pages["programmes"].table.rowCount() == 6            # le bilan survit
        assert fen.pages["programmes"].table.horizontalHeaderItem(0).text() == "Program"
    finally:
        fen._changer_langue("fr")


def test_dialogue_source(app):
    from martinet.dialogues import DialogueSource, _nom_court
    assert _nom_court("ASCOM Platform 7 (x64) 7.0.2") == "ASCOM Platform"
    d = DialogueSource(None, nom_installe="Mon Outil 2.1 (x64)")
    assert d.nom.text() == "Mon Outil" and d.motif.text() == "^Mon Outil"
    d.depot.setText("https://github.com/moi/outil/")
    assert d._erreurs() == ""
    s = d.source({"mon-outil"})
    assert s.depot == "moi/outil" and s.id == "mon-outil-2" and s.perso
    d.type.setCurrentIndex(1)
    d.url.setText("http://non-securise")
    assert d._erreurs()


def test_plan_tout_liste_ce_qui_sera_fait(app, fen):
    fen.verifier_tout()
    fen.file.attendre(30000)
    texte = fen.plan_tout(fen.bilan, True)
    assert "winget" in texte and "Defender" in texte and "NVIDIA" in texte
    assert "raccourci" in texte.lower() or "shortcut" in texte.lower()


def test_fin_de_session_refusee_pendant_un_passage(app, fen):
    import threading
    win = fen
    win.file.attendre(20000)
    libre = threading.Event()
    win.file.ajouter("essai", lambda j, a: libre.wait(10))

    class Gestionnaire:
        annule = False

        def cancel(self):
            self.annule = True

    g = Gestionnaire()
    win.fin_de_session(g)
    assert g.annule
    libre.set()
    assert win.file.arreter(5000)
    g2 = Gestionnaire()
    win.file.attendre(5000)
    win.fin_de_session(g2)
    assert not g2.annule

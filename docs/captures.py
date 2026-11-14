"""Fabrique les captures du manuel, sans écran :

    QT_QPA_PLATFORM=offscreen python docs/captures.py

Mode démonstration : logiciels, mises à jour et raccourcis fictifs, aucun
nom ni chemin réel. Les données vont dans un dossier temporaire.
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["MARTINET_DEMO"] = "1"
os.environ["MARTINET_DEMO_RAPIDE"] = "1"
os.environ["MARTINET_SYSTEME"] = "windows"
os.environ["MARTINET_DONNEES"] = tempfile.mkdtemp(prefix="martinet-captures-")
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))

from PyQt6 import QtWidgets  # noqa: E402

from martinet import style  # noqa: E402
from martinet.i18n import definir_langue  # noqa: E402

PAGES = ["accueil", "programmes", "hors", "windows", "raccourcis", "menage", "planif", "historique"]


def main():
    app = QtWidgets.QApplication([])
    style.appliquer(app)
    QtWidgets.QMessageBox.information = staticmethod(lambda *a, **k: None)
    QtWidgets.QMessageBox.question = staticmethod(lambda *a, **k: QtWidgets.QMessageBox.StandardButton.Yes)
    from martinet.fenetre import FenetrePrincipale
    for lg in ("fr", "en"):
        definir_langue(lg)
        w = FenetrePrincipale()
        w.resize(1180, 760)
        w.show()
        w.file.attendre(10000)
        w.aller("accueil")
        app.processEvents()
        w.grab().save(str(ICI / f"capture_vide-{lg}.png"))
        w.verifier_tout()
        w.file.attendre(30000)
        w.pages["windows"].table.selectRow(0)
        for cle in PAGES:
            if cle == "historique":
                w.pages["menage"].nettoyer()
                w.file.attendre(30000)
                w.pages["historique"].table.selectRow(0)
            w.aller(cle)
            app.processEvents()
            w.grab().save(str(ICI / f"capture_{cle}-{lg}.png"))
        from martinet.dialogues import DialogueSource
        d = DialogueSource(w, nom_installe="Outil maison de traitement 1.0" if lg == "fr"
                           else "Home-made processing tool 1.0")
        d.depot.setText("editeur/outil")
        d.resultat.setText(("Dernière version trouvée : 1.4.2" if lg == "fr" else "Latest version found: 1.4.2"))
        d.show()
        app.processEvents()
        d.grab().save(str(ICI / f"capture_source-{lg}.png"))
        d.close()
        w.close()
    # Linux (Manjaro) : les pages propres à Linux, dans les deux langues
    os.environ["MARTINET_SYSTEME"] = "linux"
    for lg in ("fr", "en"):
        definir_langue(lg)
        w = FenetrePrincipale()
        w.resize(1180, 760)
        w.show()
        w.file.attendre(10000)
        w.verifier_tout()
        w.file.attendre(30000)
        for cle in ("accueil", "paquets", "systeme", "menage", "planif"):
            w.aller(cle)
            app.processEvents()
            w.grab().save(str(ICI / f"capture_lx_{cle}-{lg}.png"))
        w.close()
    os.environ["MARTINET_SYSTEME"] = "windows"
    print("captures écrites dans", ICI)


if __name__ == "__main__":
    main()

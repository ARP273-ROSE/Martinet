"""Passage automatique (tâche planifiée) : aucune fenêtre, une notification.

Applique ce que les réglages autorisent, consigne tout dans l'historique,
puis affiche une notification Windows qui résume le passage ; un clic
dessus ouvre Martinet quand il reste quelque chose à faire à la main.
"""
from __future__ import annotations

import sys
import threading

from . import historique, orchestre, reglages as mod_reglages, systeme
from .i18n import tr


def executer(notifier: bool = True) -> int:
    r = mod_reglages.charger()
    journal: list[str] = []
    try:
        resume = orchestre.tout_mettre_a_jour(r, journal.append, threading.Event(),
                                              r.auto_programmes, r.auto_windows, r.auto_menage,
                                              pilote=r.auto_pilote, ranger_raccourcis=r.auto_raccourcis)
        code = 0
    except Exception as exc:                          # noqa: BLE001 — consigné
        resume = [tr("msg.erreur", detail=f"{type(exc).__name__}: {exc}")]
        code = 1
    historique.ajouter("auto", journal + [""] + resume, " · ".join(resume)[:300])
    if notifier:
        _notifier(resume)
    return code


def _notifier(resume: list[str]) -> None:
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1])
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            return
        from pathlib import Path
        icone = Path(__file__).resolve().parent.parent / "logo_64.png"
        tray = QtWidgets.QSystemTrayIcon(QtGui.QIcon(str(icone)))
        tray.show()

        def ouvrir():
            import subprocess
            script = str(Path(__file__).resolve().parent.parent / "run.py")
            subprocess.Popen([systeme.executable_fenetre(), script], creationflags=systeme.SANS_FENETRE)
            app.quit()

        tray.messageClicked.connect(ouvrir)
        tray.showMessage(tr("auto.titre"), "\n".join(resume[:6]),
                         QtWidgets.QSystemTrayIcon.MessageIcon.Information, 15000)
        QtCore.QTimer.singleShot(30000, app.quit)
        app.exec()
    except Exception:
        pass

"""File de travaux : une seule opération à la fois, hors du fil graphique.

Deux installeurs lancés en même temps se gênent (Windows Installer n'en
accepte qu'un : erreur 1618) ; on enchaîne donc tout, vérifications
comprises, et la fenêtre reste réactive pendant ce temps.
"""
from __future__ import annotations

import threading
from collections import deque

from PyQt6 import QtCore

from . import systeme


class Ouvrier(QtCore.QThread):
    ligne = QtCore.pyqtSignal(str)
    termine = QtCore.pyqtSignal(object, object)      # résultat, erreur (str) ou None

    def __init__(self, fonction, parent=None):
        super().__init__(parent)
        self.fonction = fonction
        self.annulation = threading.Event()

    def run(self):
        try:
            resultat = self.fonction(self.ligne.emit, self.annulation)
            self.termine.emit(resultat, None)
        except systeme.Annule:
            self.termine.emit(None, "annule")
        except Exception as exc:                       # noqa: BLE001 — renvoyé à la fenêtre
            import traceback
            self.ligne.emit(traceback.format_exc(limit=3))
            self.termine.emit(None, f"{type(exc).__name__}: {exc}")


class FileTaches(QtCore.QObject):
    debut = QtCore.pyqtSignal(str)                    # titre
    fin = QtCore.pyqtSignal()                         # file vide
    ligne = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._attente: deque = deque()
        self._courant: Ouvrier | None = None
        self.titre_courant = ""

    @property
    def occupee(self) -> bool:
        return self._courant is not None

    def __len__(self):
        return len(self._attente) + (1 if self._courant else 0)

    def ajouter(self, titre: str, fonction, rappel=None) -> None:
        """fonction(journal, annulation) -> résultat ; rappel(résultat, erreur)."""
        self._attente.append((titre, fonction, rappel))
        if self._courant is None:
            self._suivante()

    def annuler(self) -> None:
        self._attente.clear()
        if self._courant is not None:
            self._courant.annulation.set()

    def _suivante(self):
        if not self._attente:
            self._courant = None
            self.titre_courant = ""
            self.fin.emit()
            return
        titre, fonction, rappel = self._attente.popleft()
        self.titre_courant = titre
        ouvrier = Ouvrier(fonction, self)
        ouvrier.ligne.connect(self.ligne)
        ouvrier.termine.connect(lambda r, e, rp=rappel, o=ouvrier: self._fini(o, rp, r, e))
        self._courant = ouvrier
        self.debut.emit(titre)
        ouvrier.start()

    def _fini(self, ouvrier, rappel, resultat, erreur):
        ouvrier.wait()
        ouvrier.deleteLater()
        if rappel is not None:
            try:
                rappel(resultat, erreur)
            except Exception as exc:                   # noqa: BLE001
                self.ligne.emit(f"{type(exc).__name__}: {exc}")
        self._suivante()

    def attendre(self, delai_ms: int = 600000) -> bool:
        """Pour les essais : boucle d'événements jusqu'à file vide."""
        boucle = QtCore.QEventLoop()
        self.fin.connect(boucle.quit)
        QtCore.QTimer.singleShot(delai_ms, boucle.quit)
        if self.occupee:
            boucle.exec()
        return not self.occupee

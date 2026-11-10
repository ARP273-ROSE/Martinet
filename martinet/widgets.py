"""Petits éléments d'interface communs aux pages."""
from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets

from . import style

ROLE_DONNEE = QtCore.Qt.ItemDataRole.UserRole


class Tableau(QtWidgets.QTableWidget):
    """Tableau en lecture seule ; première colonne cochable si demandé."""

    def __init__(self, titres: list[str], cochable: bool = True, parent=None):
        super().__init__(0, len(titres), parent)
        self.cochable = cochable
        self.setHorizontalHeaderLabels(titres)
        self.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setWordWrap(False)
        en_tete = self.horizontalHeader()
        en_tete.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        en_tete.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        en_tete.setStretchLastSection(False)
        # aucun tri tant que l'utilisateur n'a pas cliqué un titre : l'ordre
        # de remplissage (le plus utile d'abord) est conservé
        en_tete.setSortIndicator(-1, QtCore.Qt.SortOrder.AscendingOrder)

    def remplir(self, lignes) -> None:
        """lignes : itérable de (cellules, donnée, cochée, couleur ou None)."""
        self.setSortingEnabled(False)
        self.setRowCount(0)
        for cellules, donnee, cochee, couleur in lignes:
            r = self.rowCount()
            self.insertRow(r)
            for c, texte in enumerate(cellules):
                item = QtWidgets.QTableWidgetItem(str(texte))
                if c == 0:
                    item.setData(ROLE_DONNEE, donnee)
                    if self.cochable:
                        item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(QtCore.Qt.CheckState.Checked if cochee
                                           else QtCore.Qt.CheckState.Unchecked)
                if couleur and c == len(cellules) - 1:
                    item.setForeground(QtGui.QColor(couleur))
                self.setItem(r, c, item)
        self.setSortingEnabled(True)

    def donnees(self, seulement_cochees: bool = True) -> list:
        res = []
        for r in range(self.rowCount()):
            item = self.item(r, 0)
            if item is None:
                continue
            if not seulement_cochees or not self.cochable or item.checkState() == QtCore.Qt.CheckState.Checked:
                res.append(item.data(ROLE_DONNEE))
        return res

    def selection(self) -> list:
        lignes = sorted({i.row() for i in self.selectedIndexes()})
        return [self.item(r, 0).data(ROLE_DONNEE) for r in lignes if self.item(r, 0)]

    def tout_cocher(self, oui: bool) -> None:
        etat = QtCore.Qt.CheckState.Checked if oui else QtCore.Qt.CheckState.Unchecked
        for r in range(self.rowCount()):
            if self.item(r, 0):
                self.item(r, 0).setCheckState(etat)


def bouton(texte: str, rappel=None, principal: bool = False, infobulle: str = "") -> QtWidgets.QPushButton:
    b = QtWidgets.QPushButton(texte)
    if principal:
        b.setProperty("role", "principal")
    if infobulle:
        b.setToolTip(infobulle)
    if rappel:
        b.clicked.connect(rappel)
    return b


def rangee(*elements, etirer: bool = True) -> QtWidgets.QHBoxLayout:
    h = QtWidgets.QHBoxLayout()
    for e in elements:
        if isinstance(e, QtWidgets.QLayout):
            h.addLayout(e)
        else:
            h.addWidget(e)
    if etirer:
        h.addStretch(1)
    return h


def titre(texte: str, sous_titre: str = "") -> QtWidgets.QWidget:
    w = QtWidgets.QWidget()
    v = QtWidgets.QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 6)
    t = QtWidgets.QLabel(texte)
    t.setProperty("role", "titre")
    v.addWidget(t)
    if sous_titre:
        s = QtWidgets.QLabel(sous_titre)
        s.setProperty("role", "sous-titre")
        s.setWordWrap(True)
        v.addWidget(s)
    return w


def etiquette(texte: str = "", couleur: str | None = None, gras: bool = False) -> QtWidgets.QLabel:
    lbl = QtWidgets.QLabel(texte)
    lbl.setWordWrap(True)
    lbl.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
    css = []
    if couleur:
        css.append(f"color: {couleur};")
    if gras:
        css.append("font-weight: 600;")
    if css:
        lbl.setStyleSheet(" ".join(css))
    return lbl


COULEUR_ETAT = {"maj": style.ORANGE, "a_jour": style.VERT, "seul": style.VERT, "erreur": style.ALERTE,
                "inconnu": style.GRIS}

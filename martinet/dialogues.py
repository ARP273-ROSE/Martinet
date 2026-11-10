"""Boîtes de dialogue : sources de versions, choix d'un paquet winget."""
from __future__ import annotations

import re

from PyQt6 import QtWidgets

from . import sources, style
from .i18n import tr
from .widgets import Tableau, bouton, etiquette, rangee


class DialogueSource(QtWidgets.QDialog):
    """Ajouter ou modifier une source de version pour un logiciel."""

    def __init__(self, parent, nom_installe: str = "", source: sources.Source | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("src.titre"))
        self.setMinimumWidth(560)
        self._origine = source
        f = QtWidgets.QFormLayout(self)
        f.addRow(etiquette(tr("src.aide"), style.GRIS))
        self.nom = QtWidgets.QLineEdit(source.nom if source else _nom_court(nom_installe))
        self.motif = QtWidgets.QLineEdit(source.motif if source else
                                         ("^" + re.escape(_nom_court(nom_installe)).replace("\\ ", " ") if nom_installe else ""))
        self.motif.setToolTip(tr("src.motif.aide"))
        self.type = QtWidgets.QComboBox()
        self.type.addItem(tr("src.type_github"), "github")
        self.type.addItem(tr("src.type_page"), "page")
        self.depot = QtWidgets.QLineEdit(source.depot if source else "")
        self.depot.setPlaceholderText(tr("src.depot.exemple"))
        self.url = QtWidgets.QLineEdit(source.url if source else "")
        self.url.setPlaceholderText("https://")
        self.regex = QtWidgets.QLineEdit(source.regex if source else r"[Vv]ersion (\d+(?:\.\d+)+)")
        self.regex.setToolTip(tr("src.regex.aide"))
        self.page = QtWidgets.QLineEdit(source.page if source else "")
        self.page.setPlaceholderText("https://")
        f.addRow(tr("src.nom"), self.nom)
        f.addRow(tr("src.motif"), self.motif)
        f.addRow(tr("src.type"), self.type)
        f.addRow(tr("src.depot"), self.depot)
        f.addRow(tr("src.url"), self.url)
        f.addRow(tr("src.regex"), self.regex)
        f.addRow(tr("src.page"), self.page)
        self.resultat = etiquette("")
        f.addRow(rangee(bouton(tr("src.tester"), self.tester)))
        f.addRow(self.resultat)
        boutons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                             | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        boutons.accepted.connect(self._valider)
        boutons.rejected.connect(self.reject)
        f.addRow(boutons)
        if source:
            self.type.setCurrentIndex(0 if source.type == "github" else 1)
        self.type.currentIndexChanged.connect(self._type)
        self._type()

    def _type(self):
        github = self.type.currentData() == "github"
        self.depot.setEnabled(github)
        self.url.setEnabled(not github)
        self.regex.setEnabled(not github)

    def source(self, existants: set[str] | None = None) -> sources.Source:
        o = self._origine
        ident = o.id if o else sources.nouvel_id(self.nom.text(), existants or set())
        depot = self.depot.text().strip()
        depot = re.sub(r"^https?://github\.com/", "", depot).strip("/")
        return sources.Source(id=ident, nom=self.nom.text().strip(), motif=self.motif.text().strip(),
                              type=self.type.currentData(), depot=depot, url=self.url.text().strip(),
                              regex=self.regex.text().strip(), page=self.page.text().strip(),
                              exclure_tag=(o.exclure_tag if o else "dev|rc|beta|alpha|preview"),
                              exclure_apres=(o.exclure_apres if o else ""),
                              fichier=(o.fichier if o else ""), perso=True)

    def _erreurs(self) -> str:
        s = self.source()
        if not s.nom or not s.motif:
            return tr("src.err_nom")
        try:
            re.compile(s.motif)
            if s.type == "page":
                re.compile(s.regex)
        except re.error as exc:
            return tr("src.err_regex", detail=str(exc))
        if s.type == "github" and not re.fullmatch(r"[\w.-]+/[\w.-]+", s.depot):
            return tr("src.err_depot")
        if s.type == "page" and not s.url.startswith("https://"):
            return tr("src.err_url")
        return ""

    def tester(self):
        err = self._erreurs()
        if err:
            self.resultat.setText(err)
            return
        self.resultat.setText(tr("src.test_en_cours"))
        QtWidgets.QApplication.processEvents()
        try:
            version, page, lien = sources.derniere(self.source())
            texte = tr("src.test_ok", version=version)
            if lien:
                texte += "\n" + tr("src.test_lien", lien=lien)
            self.resultat.setText(texte)
        except Exception as exc:                       # noqa: BLE001 — affiché tel quel
            self.resultat.setText(tr("src.test_ko", detail=str(exc)[:200]))

    def _valider(self):
        err = self._erreurs()
        if err:
            self.resultat.setText(err)
            return
        self.accept()


def _nom_court(nom: str) -> str:
    """« ASCOM Platform 7 (x64) 7.0.2 » → « ASCOM Platform »."""
    nom = re.sub(r"\(.*?\)", " ", nom)
    nom = re.sub(r"\bv?\d[\d.]*\b|x64|x86|64-bit|32-bit", " ", nom, flags=re.I)
    return " ".join(nom.split())


class GestionSources(QtWidgets.QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(tr("src.gestion"))
        self.resize(760, 420)
        v = QtWidgets.QVBoxLayout(self)
        v.addWidget(etiquette(tr("src.gestion.aide"), style.GRIS))
        self.table = Tableau([tr("src.nom"), tr("src.type"), tr("src.adresse"), tr("src.origine")],
                             cochable=False)
        v.addWidget(self.table, 1)
        v.addLayout(rangee(bouton(tr("src.ajouter"), self.ajouter), bouton(tr("src.modifier"), self.modifier),
                           bouton(tr("src.supprimer"), self.supprimer)))
        fermer = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Close)
        fermer.rejected.connect(self.reject)
        v.addWidget(fermer)
        self._charger()

    def _charger(self):
        self.liste = sources.charger()
        self.table.remplir(([s.nom, tr("src.type_" + s.type), s.depot or s.url,
                             tr("src.perso") if s.perso else tr("src.catalogue")], s, False, None)
                           for s in self.liste)

    def ajouter(self):
        d = DialogueSource(self)
        if d.exec():
            self.liste.append(d.source({s.id for s in self.liste}))
            sources.enregistrer_perso(self.liste)
            self._charger()

    def modifier(self):
        choix = self.table.selection()
        if not choix:
            return
        d = DialogueSource(self, source=choix[0])
        if d.exec():
            neuve = d.source()
            self.liste = [neuve if s.id == neuve.id else s for s in self.liste]
            sources.enregistrer_perso(self.liste)
            self._charger()

    def supprimer(self):
        choix = [s for s in self.table.selection() if s.perso]
        if not choix:
            QtWidgets.QMessageBox.information(self, tr("src.gestion"), tr("src.catalogue_fixe"))
            return
        ids = {s.id for s in choix}
        self.liste = [s for s in self.liste if s.id not in ids]
        sources.enregistrer_perso(self.liste)
        self._charger()


def choisir_paquet(parent, nom: str, candidats) -> object | None:
    d = QtWidgets.QDialog(parent)
    d.setWindowTitle(tr("hors.chercher_winget"))
    d.resize(640, 320)
    v = QtWidgets.QVBoxLayout(d)
    v.addWidget(etiquette(tr("hors.winget_choix", nom=nom)))
    t = Tableau([tr("col.logiciel"), tr("col.id"), tr("col.version"), tr("col.source")], cochable=False)
    t.remplir(([p.nom, p.id, p.installee, p.source], p, False, None) for p in candidats)
    if t.rowCount():
        t.selectRow(0)
    v.addWidget(t, 1)
    v.addWidget(etiquette(tr("hors.winget_avertissement"), style.GRIS))
    b = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                   | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
    b.accepted.connect(d.accept)
    b.rejected.connect(d.reject)
    v.addWidget(b)
    if d.exec() and t.selection():
        return t.selection()[0]
    return None

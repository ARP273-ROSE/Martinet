"""Les pages de la fenêtre : une par famille de mises à jour."""
from __future__ import annotations

import datetime
import os
from pathlib import Path

from PyQt6 import QtCore, QtWidgets

from . import (historique, menage, orchestre, planif, raccourcis, reglages as mod_reglages,
               sources, style, systeme, windows_update, winget)
from .i18n import tr
from .widgets import COULEUR_ETAT, Tableau, bouton, etiquette, rangee, titre


class Page(QtWidgets.QWidget):
    cle = ""

    def __init__(self, fen):
        super().__init__()
        self.fen = fen
        self.v = QtWidgets.QVBoxLayout(self)
        self.v.setContentsMargins(18, 14, 18, 10)
        self.v.addWidget(titre(tr(f"page.{self.cle}"), tr(f"page.{self.cle}.aide")))

    @property
    def bilan(self) -> orchestre.Bilan:
        return self.fen.bilan

    @property
    def reglages(self):
        return self.fen.reglages

    def rafraichir(self) -> None:
        """Remplit la page à partir du bilan courant."""


# ====================================================================== accueil
class PageAccueil(Page):
    cle = "accueil"

    def __init__(self, fen):
        super().__init__(fen)
        self.b_verifier = bouton(tr("accueil.verifier"), fen.verifier_tout, principal=True)
        self.b_tout = bouton(tr("accueil.tout"), fen.tout_mettre_a_jour, principal=True)
        self.b_tout.setToolTip(tr("accueil.tout.bulle"))
        self.b_verifier.setMinimumHeight(40)
        self.b_tout.setMinimumHeight(40)
        self.v.addLayout(rangee(self.b_verifier, self.b_tout))
        grille = QtWidgets.QGridLayout()
        grille.setSpacing(12)
        self.cartes: dict[str, QtWidgets.QPushButton] = {}
        cles = (("paquets", "systeme", "raccourcis", "menage", "planif") if systeme.linux()
                else ("programmes", "hors", "windows", "raccourcis", "menage", "planif"))
        for i, cle in enumerate(cles):
            c = QtWidgets.QPushButton()
            c.setProperty("role", "carte")
            c.setMinimumHeight(92)
            c.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred)
            c.clicked.connect(lambda _=False, k=cle: fen.aller(k))
            self.cartes[cle] = c
            grille.addWidget(c, i // 2, i % 2)
        self.v.addLayout(grille)
        self.derniere = etiquette("", style.GRIS)
        self.v.addWidget(self.derniere)
        self.v.addStretch(1)
        self.rafraichir()

    def _carte(self, cle, etat):
        self.cartes[cle].setText(f"{tr('page.' + cle)}\n{etat}")

    def rafraichir(self):
        b = self.bilan
        jamais = tr("accueil.pas_verifie")
        if systeme.linux():
            self._rafraichir_linux(b, jamais)
        else:
            self._rafraichir_windows(b, jamais)
        self._carte("raccourcis", jamais if b.morts is None else
                    (tr("accueil.n_morts", n=len(b.morts)) if b.morts else tr("accueil.aucun_mort")))
        if not b.menage:
            self._carte("menage", jamais)
        else:
            total = sum((t or 0) for k, (t, _n) in b.menage.items()
                        if any(e.cle == k and e.coche for e in menage.elements()))
            self._carte("menage", tr("accueil.recuperable", taille=menage.taille_lisible(total)))
        etat = self.fen.etat_planif
        if etat is None:
            self._carte("planif", tr("accueil.planif_aucune"))
        else:
            self._carte("planif", tr("accueil.planif_prochaine", date=_date(etat.get("prochaine"))))

    def _rafraichir_linux(self, b, jamais):
        if b.paquets is None:
            self._carte("paquets", jamais)
        else:
            n = len(b.paquets) + len([a for a in (b.applis or []) if a.etat == "maj"])
            self._carte("paquets", tr("accueil.n_maj", n=n) if n else tr("accueil.a_jour"))
        s = b.lx
        if s is None:
            self._carte("systeme", jamais)
            return
        points = []
        if s.redemarrer:
            points.append(tr("lx.accueil.redemarrer"))
        if s.noyaux_fin_de_vie:
            points.append(tr("lx.accueil.noyau_fin"))
        if s.micrologiciels:
            points.append(tr("lx.accueil.micrologiciels", n=len(s.micrologiciels)))
        if s.pacnew:
            points.append(tr("lx.accueil.pacnew", n=len(s.pacnew)))
        if s.orphelins:
            points.append(tr("lx.accueil.orphelins", n=len(s.orphelins)))
        self._carte("systeme", "  ·  ".join(points) if points else tr("lx.accueil.rien"))

    def _rafraichir_windows(self, b, jamais):
        if b.inventaire is None:
            self._carte("programmes", jamais)
            self._carte("hors", jamais)
        else:
            n = len(orchestre.a_mettre_a_jour(b, self.reglages))
            self._carte("programmes", tr("accueil.n_maj", n=n) if n else tr("accueil.a_jour"))
            n = len([r for r in b.hors if r.etat == "maj"])
            self._carte("hors", (tr("accueil.n_maj", n=n) if n else tr("accueil.a_jour"))
                        + "  ·  " + tr("accueil.sans_source", n=len(b.sans_source)))
        if b.windows is None:
            self._carte("windows", jamais)
        else:
            n = len([m for m in b.windows if not m.facultatif])
            pilote = [c for c in b.cartes if c.etat == "maj"]
            txt = tr("accueil.n_maj", n=n) if n else tr("accueil.a_jour")
            if pilote:
                txt += "  ·  " + tr("accueil.pilote_gpu", version=pilote[0].derniere)
            if systeme.windows10():
                txt += "  ·  " + tr("accueil.w10")
            self._carte("windows", txt)


def _jour(iso: str | None) -> str:
    try:
        return datetime.date.fromisoformat(iso or "").strftime(tr("format.date"))
    except ValueError:
        return iso or "—"


def _date(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        d = datetime.datetime.fromisoformat(iso)
    except ValueError:
        return iso
    return d.strftime(tr("format.date_heure"))


# ====================================================================== programmes
class PageProgrammes(Page):
    cle = "programmes"

    def __init__(self, fen):
        super().__init__(fen)
        self.table = Tableau([tr("col.logiciel"), tr("col.id"), tr("col.installee"),
                              tr("col.disponible"), tr("col.source")])
        self.voir_ignores = QtWidgets.QCheckBox(tr("prog.voir_ignores"))
        self.voir_ignores.toggled.connect(self.rafraichir)
        self.v.addLayout(rangee(
            bouton(tr("action.verifier"), lambda: fen.verifier_tout({"programmes"})),
            bouton(tr("prog.maj_selection"), self.mettre_a_jour, principal=True),
            bouton(tr("action.tout_cocher"), lambda: self.table.tout_cocher(True)),
            bouton(tr("action.tout_decocher"), lambda: self.table.tout_cocher(False)),
            bouton(tr("prog.ignorer"), self.ignorer, infobulle=tr("prog.ignorer.aide")),
            self.voir_ignores))
        self.info = etiquette("", style.GRIS)
        self.v.addWidget(self.info)
        # winget absent (Windows 10 pas à jour) : le Store installe « Programme d'installation d'application »
        self.b_store = bouton(tr("prog.ouvrir_store"),
                              lambda: systeme.ouvrir("ms-windows-store://pdp/?ProductId=9NBLGGH4NNS1"))
        self.b_store.setVisible(False)
        self.v.addLayout(rangee(self.b_store))
        self.v.addWidget(self.table, 1)
        self.rafraichir()

    def rafraichir(self):
        inv = self.bilan.inventaire
        if inv is None:
            self.table.remplir([])
            self.info.setText(tr("accueil.pas_verifie"))
            return
        ignores = set(self.reglages.ignores_winget)
        lignes = []
        for p in inv.a_jour:
            ignore = p.id in ignores
            if ignore and not self.voir_ignores.isChecked():
                continue
            src = p.source + (f"  ({tr('prog.ignore')})" if ignore else "")
            lignes.append(([p.nom, p.id, p.installee or "?", p.disponible, src], p, not ignore,
                           style.GRIS if ignore else None))
        self.table.remplir(lignes)
        suivis = len([p for p in inv.paquets if p.suivi])
        texte = tr("prog.resume", n=len(lignes), suivis=suivis)
        if inv.erreur == "winget":
            texte = tr("prog.sans_winget")
        self.b_store.setVisible(inv.erreur == "winget")
        self.info.setText(texte)

    def mettre_a_jour(self):
        paquets = self.table.donnees()
        if not paquets:
            self.fen.message(tr("msg.rien_coche"))
            return

        def travail(journal, annulation):
            resultats = []
            for p in paquets:
                journal(tr("journal.maj_paquet", nom=p.nom, avant=p.installee, apres=p.disponible))
                resultats.append((p, *winget.mettre_a_jour(p.id, journal, annulation)))
            return resultats

        def fini(resultats, erreur):
            if erreur:
                return self.fen.erreur_tache(erreur)
            ok = [p for p, r, _ in resultats if r]
            ko = [f"{p.nom} ({c})" for p, r, c in resultats if not r]
            lignes = [tr("resume.programmes", ok=len(ok), n=len(resultats))]
            if ko:
                lignes.append(tr("resume.echecs", liste=", ".join(ko)))
            if self.bilan.inventaire:
                for p in ok:
                    p.installee, p.disponible = p.disponible, ""
            self.fen.consigner(lignes)
            self.fen.rafraichir_tout()
            self.fen.message("\n".join(lignes))

        self.fen.lancer(tr("tache.maj_programmes", n=len(paquets)), travail, fini)

    def ignorer(self):
        choisis = self.table.selection()
        if not choisis:
            self.fen.message(tr("msg.rien_selectionne"))
            return
        ign = set(self.reglages.ignores_winget)
        for p in choisis:
            ign.symmetric_difference_update({p.id})
        self.reglages.ignores_winget = sorted(ign)
        mod_reglages.enregistrer(self.reglages)
        self.fen.rafraichir_tout()


# ====================================================================== hors winget
class PageHors(Page):
    cle = "hors"

    def __init__(self, fen):
        super().__init__(fen)
        g1 = QtWidgets.QGroupBox(tr("hors.avec_source"))
        v1 = QtWidgets.QVBoxLayout(g1)
        self.t_sources = Tableau([tr("col.logiciel"), tr("col.installee"), tr("col.derniere"),
                                  tr("col.etat")], cochable=False)
        v1.addLayout(rangee(
            bouton(tr("action.verifier"), lambda: fen.verifier_tout({"programmes"})),
            bouton(tr("hors.installer"), self.installer, principal=True, infobulle=tr("hors.installer.aide")),
            bouton(tr("action.ouvrir_page"), self.ouvrir_page),
            bouton(tr("hors.sources"), self.gerer_sources)))
        v1.addWidget(self.t_sources)
        g2 = QtWidgets.QGroupBox(tr("hors.sans_source"))
        v2 = QtWidgets.QVBoxLayout(g2)
        v2.addWidget(etiquette(tr("hors.sans_source.aide"), style.GRIS))
        self.t_sans = Tableau([tr("col.logiciel"), tr("col.installee")], cochable=False)
        v2.addLayout(rangee(
            bouton(tr("hors.chercher_winget"), self.chercher_winget, infobulle=tr("hors.chercher_winget.aide")),
            bouton(tr("hors.ajouter_source"), self.ajouter_source),
            bouton(tr("hors.web"), self.chercher_web),
            bouton(tr("hors.ignorer"), self.ignorer)))
        v2.addWidget(self.t_sans)
        sep = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        sep.addWidget(g1)
        sep.addWidget(g2)
        self.v.addWidget(sep, 1)
        self.rafraichir()

    def rafraichir(self):
        lignes = []
        for r in self.bilan.hors:
            etat = {"maj": tr("etat.maj"), "a_jour": tr("etat.a_jour"), "seul": tr("etat.seul"),
                    "erreur": tr("etat.erreur", detail=r.erreur)}.get(r.etat, tr("etat.inconnu"))
            lignes.append(([r.nom, r.installee, r.derniere or "—", etat], r, False, COULEUR_ETAT.get(r.etat)))
        self.t_sources.remplir(lignes)
        self.t_sans.remplir(([p.nom, p.installee], p, False, None) for p in self.bilan.sans_source)

    def _choix(self):
        choix = self.t_sources.selection()
        if not choix:
            self.fen.message(tr("msg.rien_selectionne"))
        return choix

    def ouvrir_page(self):
        for r in self._choix():
            if r.page:
                systeme.ouvrir(r.page)

    def installer(self):
        for r in self._choix():
            if r.fichier:
                self.fen.telecharger_et_installer(r)
            elif r.page:
                self.fen.message(tr("hors.pas_de_lien", nom=r.nom))
                systeme.ouvrir(r.page)

    def gerer_sources(self):
        from .dialogues import GestionSources
        GestionSources(self).exec()

    def ajouter_source(self):
        from .dialogues import DialogueSource
        choix = self.t_sans.selection()
        nom = choix[0].nom if choix else ""
        d = DialogueSource(self, nom_installe=nom)
        if d.exec():
            tout = sources.charger()
            s = d.source(existants={x.id for x in tout})
            tout.append(s)
            sources.enregistrer_perso(tout)
            self.fen.verifier_tout({"programmes"})

    def chercher_web(self):
        from urllib.parse import quote_plus
        for p in self.t_sans.selection():
            systeme.ouvrir("https://duckduckgo.com/?q=" + quote_plus(f"{p.nom} download"))

    def ignorer(self):
        choix = self.t_sans.selection()
        if not choix:
            self.fen.message(tr("msg.rien_selectionne"))
            return
        noms = set(self.reglages.ignores_hors_winget) | {p.nom for p in choix}
        self.reglages.ignores_hors_winget = sorted(noms)
        mod_reglages.enregistrer(self.reglages)
        self.bilan.sans_source = [p for p in self.bilan.sans_source if p.nom not in noms]
        self.fen.rafraichir_tout()

    def chercher_winget(self):
        choix = self.t_sans.selection()
        if not choix:
            self.fen.message(tr("msg.rien_selectionne"))
            return
        p = choix[0]

        def fini(candidats, erreur):
            if erreur:
                return self.fen.erreur_tache(erreur)
            if not candidats:
                self.fen.message(tr("hors.winget_rien", nom=p.nom))
                return
            from .dialogues import choisir_paquet
            paquet = choisir_paquet(self, p.nom, candidats)
            if paquet is None:
                return
            self.fen.lancer(tr("tache.installer", nom=paquet.nom),
                            lambda j, a: winget.installer(paquet.id, j, a),
                            lambda r, e: (self.fen.erreur_tache(e) if e else
                                          (self.fen.message(tr("hors.confie_ok", nom=paquet.nom)
                                                            if r[0] else tr("hors.confie_ko", code=r[1])),
                                           self.fen.verifier_tout({"programmes"}))))

        self.fen.lancer(tr("tache.chercher", nom=p.nom), lambda j, a: winget.rechercher(p.nom), fini)


# ====================================================================== windows
class PageWindows(Page):
    cle = "windows"

    def __init__(self, fen):
        super().__init__(fen)
        if systeme.windows10():
            bandeau = etiquette(tr("win.w10"))
            bandeau.setObjectName("avertissement")
            self.v.addWidget(bandeau)
        g = QtWidgets.QGroupBox(tr("win.carte"))
        vg = QtWidgets.QVBoxLayout(g)
        self.l_carte = etiquette(tr("accueil.pas_verifie"))
        self.b_pilote = bouton(tr("win.pilote_installer"), self.installer_pilote, principal=True)
        self.b_page = bouton(tr("action.ouvrir_page"), self.ouvrir_page_pilote)
        vg.addWidget(self.l_carte)
        vg.addLayout(rangee(self.b_pilote, self.b_page))
        self.v.addWidget(g)
        g2 = QtWidgets.QGroupBox(tr("win.mises_a_jour"))
        v2 = QtWidgets.QVBoxLayout(g2)
        self.table = Tableau([tr("col.titre"), tr("col.type"), tr("col.taille")])
        v2.addLayout(rangee(
            bouton(tr("win.rechercher"), lambda: fen.verifier_tout({"windows"})),
            bouton(tr("win.installer"), self.installer, principal=True),
            bouton(tr("win.defender"), self.defender)))
        self.c_facultatives = QtWidgets.QCheckBox(tr("win.inclure_facultatives"))
        self.c_facultatives.setToolTip(tr("win.inclure_facultatives.aide"))
        self.c_facultatives.toggled.connect(self._facultatives)
        v2.addWidget(self.c_facultatives)
        self.info = etiquette("", style.GRIS)
        v2.addWidget(self.info)
        v2.addWidget(self.table)
        self.v.addWidget(g2, 1)
        self.rafraichir()

    def rafraichir(self):
        cartes = self.bilan.cartes
        if cartes:
            textes = []
            for r in cartes:
                if r.etat == "maj" and r.source == "amd":
                    etat = tr("win.pilote_maj_amd", version=r.derniere, nom=r.details.get("nom") or "")
                elif r.etat == "maj":
                    etat = tr("win.pilote_maj", version=r.derniere, date=_jour(r.details.get("date")),
                              nom=r.details.get("nom") or "")
                elif r.etat == "a_jour":
                    etat = tr("win.pilote_a_jour")
                elif r.etat == "erreur":
                    etat = tr("etat.erreur", detail=r.erreur)
                elif r.derniere:
                    etat = tr("win.pilote_amd_inconnu", version=r.derniere)
                else:
                    etat = tr("win.pilote_inconnu")
                if r.details.get("historique"):
                    etat += "<br>" + tr("win.pilote_historique")
                textes.append(f"<b>{r.nom}</b> — {tr('win.pilote_installe', version=r.installee)}<br>{etat}")
            self.l_carte.setText("<br><br>".join(textes))
        elif self.bilan.windows is not None:
            self.l_carte.setText(tr("win.pas_de_carte"))
        maj = [r for r in cartes if r.etat in ("maj", "inconnu") and r.fichier]
        self.b_pilote.setEnabled(bool(maj))
        self.b_page.setEnabled(any(r.page for r in cartes))
        if self.bilan.windows is None:
            self.table.remplir([])
            self.info.setText(tr("accueil.pas_verifie"))
            return
        lignes = []
        for m in self.bilan.windows:
            genre = tr("win.type_pilote") if m.pilote else tr("win.type_windows")
            if m.facultatif:
                genre += " · " + tr("win.facultatif")
            lignes.append(([m.titre, genre, menage.taille_lisible(m.taille)], m,
                           self.reglages.facultatives or not m.facultatif, None))
        self.table.remplir(lignes)
        self.info.setText(tr("win.resume", n=len(lignes)) if lignes else tr("win.rien"))
        self.c_facultatives.blockSignals(True)
        self.c_facultatives.setChecked(self.reglages.facultatives)
        self.c_facultatives.blockSignals(False)

    def _facultatives(self, oui: bool):
        self.reglages.facultatives = oui
        mod_reglages.enregistrer(self.reglages)
        self.fen.rafraichir_tout()

    def installer(self):
        choix = self.table.donnees()
        if not choix:
            self.fen.message(tr("msg.rien_coche"))
            return
        if not self.fen.exiger_admin():
            return

        def fini(r, erreur):
            if erreur:
                return self.fen.erreur_tache(erreur)
            lignes = [tr("resume.windows", n=r.get("n", 0), etat=tr("wu.code." + windows_update.decrire(r)))]
            if r.get("redemarrer"):
                lignes.append(tr("resume.redemarrer"))
            self.fen.consigner(lignes)
            self.fen.message("\n".join(lignes))
            self.fen.verifier_tout({"windows"})
            if r.get("redemarrer"):
                self.fen.proposer_redemarrage()

        self.fen.lancer(tr("tache.windows", n=len(choix)),
                        lambda j, a: windows_update.installer([m.id for m in choix], j, a), fini)

    def defender(self):
        self.fen.lancer(tr("win.defender"), lambda j, a: windows_update.mettre_a_jour_defender(j),
                        lambda r, e: self.fen.message(tr("win.defender_ok") if r else tr("win.defender_ko")))

    def installer_pilote(self):
        for r in self.bilan.cartes:
            if r.etat in ("maj", "inconnu") and r.fichier:
                self.fen.telecharger_et_installer(r)

    def ouvrir_page_pilote(self):
        for r in self.bilan.cartes:
            if r.page:
                systeme.ouvrir(r.page)


# ====================================================================== raccourcis
class PageRaccourcis(Page):
    cle = "raccourcis"

    def __init__(self, fen):
        super().__init__(fen)
        g = QtWidgets.QGroupBox(tr("racc.morts"))
        v = QtWidgets.QVBoxLayout(g)
        self.table = Tableau([tr("col.raccourci"), tr("col.lieu"), tr("col.cible")])
        v.addLayout(rangee(
            bouton(tr("racc.analyser"), lambda: fen.verifier_tout({"raccourcis"})),
            bouton(tr("racc.mettre_de_cote"), self.mettre_de_cote, principal=True),
            bouton(tr("racc.ouvrir_dossier"), self.ouvrir_dossier)))
        self.info = etiquette("", style.GRIS)
        v.addWidget(self.info)
        v.addWidget(self.table)
        g2 = QtWidgets.QGroupBox(tr("racc.de_cote"))
        v2 = QtWidgets.QVBoxLayout(g2)
        self.t_cote = Tableau([tr("col.raccourci"), tr("col.origine"), tr("col.date")])
        v2.addLayout(rangee(bouton(tr("racc.restaurer"), self.restaurer)))
        v2.addWidget(self.t_cote)
        sep = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        sep.addWidget(g)
        sep.addWidget(g2)
        self.v.addWidget(sep, 1)
        self.rafraichir()

    def rafraichir(self):
        morts = self.bilan.morts
        if morts is None:
            self.table.remplir([])
            self.info.setText(tr("accueil.pas_verifie"))
        else:
            self.table.remplir(([Path(r.fichier.replace("\\", "/")).name, tr("lieu." + r.lieu), r.cible],
                                r, True, None) for r in morts)
            self.info.setText(tr("racc.resume", n=len(morts)) if morts else tr("accueil.aucun_mort"))
        self.t_cote.remplir(([e.fichier, e.origine, e.lot.replace("_", " ")], e, False, None)
                            for e in raccourcis.mis_de_cote())

    def mettre_de_cote(self):
        choix = self.table.donnees()
        if not choix:
            self.fen.message(tr("msg.rien_coche"))
            return
        n, erreurs = raccourcis.mettre_de_cote(choix)
        lignes = [tr("racc.deplaces", n=n)]
        if erreurs:
            lignes.append(tr("racc.erreurs", liste="; ".join(erreurs)))
            if not systeme.est_admin():
                lignes.append(tr("racc.admin"))
        self.fen.consigner(lignes)
        self.bilan.morts = [r for r in (self.bilan.morts or [])
                            if r not in choix or os.path.exists(r.fichier)]
        if not systeme.WINDOWS:
            self.bilan.morts = [r for r in self.bilan.morts if r not in choix]
        self.fen.rafraichir_tout()
        self.fen.message("\n".join(lignes))

    def restaurer(self):
        choix = self.t_cote.donnees()
        if not choix:
            self.fen.message(tr("msg.rien_coche"))
            return
        n, erreurs = raccourcis.restaurer(choix)
        lignes = [tr("racc.restaures", n=n)] + ([tr("racc.erreurs", liste="; ".join(erreurs))] if erreurs else [])
        self.fen.consigner(lignes)
        self.rafraichir()
        self.fen.message("\n".join(lignes))

    def ouvrir_dossier(self):
        for r in self.table.selection():
            systeme.ouvrir(str(Path(r.fichier).parent))


# ====================================================================== ménage
class PageMenage(Page):
    cle = "menage"

    def __init__(self, fen):
        super().__init__(fen)
        self.table = Tableau([tr("col.element"), tr("col.description"), tr("col.taille")])
        self.table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.v.addLayout(rangee(
            bouton(tr("menage.mesurer"), lambda: fen.verifier_tout({"menage"})),
            bouton(tr("menage.nettoyer"), self.nettoyer, principal=True)))
        self.info = etiquette("", style.GRIS)
        self.v.addWidget(self.info)
        self.v.addWidget(self.table, 1)
        self.v.addWidget(etiquette(tr("menage.pas_de_registre"), style.GRIS))
        self.rafraichir()

    def rafraichir(self):
        mesures = self.bilan.menage
        lignes = []
        for e in menage.elements():
            t, n = mesures.get(e.cle, (None, None))
            if not mesures:
                taille = "—"
            elif e.cle == "composants":
                taille = tr("menage.variable")
            else:
                taille = menage.taille_lisible(t) + (f"  ({n})" if n else "")
            desc = tr(f"menage.{e.cle}.aide") + (f"  [{tr('menage.admin')}]" if e.admin else "")
            lignes.append(([tr(f"menage.{e.cle}"), desc, taille], e, e.coche, None))
        self.table.remplir(lignes)
        self.info.setText("" if mesures else tr("accueil.pas_verifie"))

    def nettoyer(self):
        choix = self.table.donnees()
        if not choix:
            self.fen.message(tr("msg.rien_coche"))
            return
        if not systeme.linux() and any(e.admin for e in choix) and not systeme.est_admin():
            # sous Linux, pas d'élévation de la fenêtre : polkit demande le mot de passe le moment venu
            if not self.fen.exiger_admin():
                choix = [e for e in choix if not e.admin]
        if any(e.cle == "corbeille" for e in choix):
            if not self.fen.confirmer(tr("menage.confirmer_corbeille")):
                choix = [e for e in choix if e.cle != "corbeille"]

        def travail(journal, annulation):
            for e in choix:
                journal(tr("journal.menage", element=tr(f"menage.{e.cle}")))
            if annulation.is_set():
                raise systeme.Annule()
            return menage.nettoyer_tout([e.cle for e in choix], journal)

        def fini(total, erreur):
            if erreur:
                return self.fen.erreur_tache(erreur)
            ligne = tr("resume.menage", taille=menage.taille_lisible(total))
            self.fen.consigner([ligne])
            self.fen.message(ligne)
            self.fen.verifier_tout({"menage"})

        self.fen.lancer(tr("tache.menage"), travail, fini)


# ====================================================================== planification
class PagePlanif(Page):
    cle = "planif"

    def __init__(self, fen):
        super().__init__(fen)
        r = self.reglages
        g = QtWidgets.QGroupBox(tr("planif.quand"))
        f = QtWidgets.QFormLayout(g)
        self.actif = QtWidgets.QCheckBox(tr("planif.actif"))
        self.frequence = QtWidgets.QComboBox()
        self.frequence.addItem(tr("planif.hebdo"), "hebdo")
        self.frequence.addItem(tr("planif.quotidien"), "quotidien")
        self.frequence.setCurrentIndex(0 if r.auto_frequence == "hebdo" else 1)
        self.jour = QtWidgets.QComboBox()
        for i in range(7):
            self.jour.addItem(tr(f"jour.{i}"), i)
        self.jour.setCurrentIndex(r.auto_jour % 7)
        self.heure = QtWidgets.QTimeEdit(QtCore.QTime.fromString(r.auto_heure, "HH:mm"))
        self.heure.setDisplayFormat("HH:mm")
        self.frequence.currentIndexChanged.connect(
            lambda: self.jour.setEnabled(self.frequence.currentData() == "hebdo"))
        self.jour.setEnabled(r.auto_frequence == "hebdo")
        f.addRow(self.actif)
        f.addRow(tr("planif.frequence"), self.frequence)
        f.addRow(tr("planif.jour"), self.jour)
        f.addRow(tr("planif.heure"), self.heure)
        self.v.addWidget(g)
        g2 = QtWidgets.QGroupBox(tr("planif.quoi"))
        v2 = QtWidgets.QVBoxLayout(g2)
        self.c_prog = QtWidgets.QCheckBox(tr("planif.programmes"))
        self.c_win = QtWidgets.QCheckBox(tr("planif.windows"))
        self.c_menage = QtWidgets.QCheckBox(tr("planif.menage"))
        self.c_pilote = QtWidgets.QCheckBox(tr("planif.pilote"))
        self.c_racc = QtWidgets.QCheckBox(tr("planif.raccourcis"))
        self.c_prog.setChecked(r.auto_programmes)
        self.c_win.setChecked(r.auto_windows)
        self.c_menage.setChecked(r.auto_menage)
        self.c_pilote.setChecked(r.auto_pilote)
        self.c_racc.setChecked(r.auto_raccourcis)
        for c in (self.c_prog, self.c_win, self.c_pilote, self.c_racc, self.c_menage):
            v2.addWidget(c)
        self.c_polkit = None
        if systeme.linux():
            # Linux : pas de Windows Update ni de pilote à part (ils viennent avec les paquets)
            self.c_win.setVisible(False)
            self.c_pilote.setVisible(False)
            from .pages_linux import regle_polkit_case
            self.c_polkit = regle_polkit_case(self)
            if self.c_polkit is not None:
                v2.addWidget(self.c_polkit)
        v2.addWidget(etiquette(tr("planif.signale"), style.GRIS))
        self.v.addWidget(g2)
        self.etat = etiquette("")
        self.v.addWidget(self.etat)
        self.v.addLayout(rangee(bouton(tr("planif.enregistrer"), self.enregistrer, principal=True),
                                bouton(tr("planif.maintenant"), self.maintenant)))
        self.v.addStretch(1)
        self.rafraichir()

    def rafraichir(self):
        e = self.fen.etat_planif
        self.actif.setChecked(e is not None)
        if e is None:
            self.etat.setText(tr("planif.etat_aucune"))
        else:
            res = e.get("resultat")
            res_txt = "—" if not e.get("derniere") else (tr("planif.res_ok") if res == 0
                                                          else tr("planif.res_code", code=f"0x{int(res) & 0xFFFFFFFF:X}"))
            self.etat.setText(tr("planif.etat", prochaine=_date(e.get("prochaine")),
                                 derniere=_date(e.get("derniere")), resultat=res_txt))

    def enregistrer(self):
        r = self.reglages
        r.auto_frequence = self.frequence.currentData()
        r.auto_jour = int(self.jour.currentData())
        r.auto_heure = self.heure.time().toString("HH:mm")
        r.auto_programmes = self.c_prog.isChecked()
        r.auto_windows = self.c_win.isChecked()
        r.auto_menage = self.c_menage.isChecked()
        r.auto_pilote = self.c_pilote.isChecked()
        r.auto_raccourcis = self.c_racc.isChecked()
        mod_reglages.enregistrer(r)
        if self.c_polkit is not None:
            from . import linux_paquets
            if self.c_polkit.isChecked() != linux_paquets.regle_active():
                ok_regle, detail = linux_paquets.poser_regle(self.c_polkit.isChecked())
                if not ok_regle:
                    self.c_polkit.setChecked(linux_paquets.regle_active())
                    self.fen.message(tr("lx.regle_echec", detail=detail), alerte=True)
        if self.actif.isChecked():
            if not self.fen.exiger_admin():
                return
            ok, detail = planif.creer(r.auto_frequence, r.auto_jour, r.auto_heure)
        else:
            ok, detail = (planif.supprimer() if self.fen.etat_planif else (True, ""))
        if not ok:
            self.fen.message(tr("planif.echec", detail=detail), alerte=True)
        self.fen.etat_planif = planif.etat()
        self.fen.rafraichir_tout()
        if ok:
            self.fen.message(tr("planif.ok"))

    def maintenant(self):
        r = self.reglages
        self.fen.lancer(tr("tache.auto"),
                        lambda j, a: orchestre.tout_mettre_a_jour(r, j, a, r.auto_programmes,
                                                                  r.auto_windows, r.auto_menage,
                                                                  pilote=r.auto_pilote,
                                                                  ranger_raccourcis=r.auto_raccourcis),
                        self.fen.fin_tout_mettre_a_jour)


# ====================================================================== historique
class PageHistorique(Page):
    cle = "historique"

    def __init__(self, fen):
        super().__init__(fen)
        sep = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        self.table = Tableau([tr("col.date"), tr("col.mode"), tr("col.resume")], cochable=False)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.detail = QtWidgets.QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.table.itemSelectionChanged.connect(self._detail)
        sep.addWidget(self.table)
        sep.addWidget(self.detail)
        self.v.addLayout(rangee(bouton(tr("histo.dossier"),
                                       lambda: systeme.ouvrir(str(systeme.dossier_donnees())))))
        self.v.addWidget(sep, 1)
        self.rafraichir()

    def rafraichir(self):
        self.table.remplir(([_date(e.get("date")), tr("mode." + e.get("mode", "manuel")),
                             e.get("resume", "")], e, False, None) for e in historique.lire())

    def _detail(self):
        choix = self.table.selection()
        self.detail.setPlainText("\n".join(choix[0].get("lignes", [])) if choix else "")


PAGES = [PageAccueil, PageProgrammes, PageHors, PageWindows, PageRaccourcis, PageMenage,
         PagePlanif, PageHistorique]


def pages_du_systeme() -> list:
    """Les pages du système en cours : Windows, ou Linux (paquets et état du système)."""
    if systeme.linux():
        from .pages_linux import PagePaquets, PageSysteme
        return [PageAccueil, PagePaquets, PageSysteme, PageRaccourcis, PageMenage, PagePlanif, PageHistorique]
    return PAGES


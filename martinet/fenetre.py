"""Fenêtre principale de Martinet."""
from __future__ import annotations

import threading
from pathlib import Path

from PyQt6 import QtCore, QtGui, QtWidgets

from . import __version__, historique, orchestre, planif, reglages as mod_reglages, sources, style, systeme
from .i18n import langue, tr
from .pages import PAGES
from .widgets import bouton, etiquette

RACINE = Path(__file__).resolve().parent.parent


def _minuscule(t: str) -> str:
    """Première lettre en minuscule, sauf sigle ou nom propre (« Windows » reste tel quel)."""
    return t[:1].lower() + t[1:] if t[1:2].islower() else t


class FenetrePrincipale(QtWidgets.QMainWindow):
    _maj_signal = QtCore.pyqtSignal(object, bool)

    def __init__(self):
        super().__init__()
        from .taches import FileTaches
        self.reglages = mod_reglages.charger()
        self.bilan = orchestre.Bilan()
        self.etat_planif: dict | None = None
        self.file = FileTaches(self)
        self.file.debut.connect(self._debut_tache)
        self.file.fin.connect(self._fin_file)
        self.file.ligne.connect(self._ligne)
        self.qsettings = QtCore.QSettings("ARP273-ROSE", "Martinet")
        self._journal_courant: list[str] = []
        self.setWindowTitle(f"Martinet {__version__}")
        self.resize(1180, 780)
        self._construire()
        self._menus()
        # état de la tâche planifiée, lu en arrière-plan (PowerShell : une seconde)
        self.lancer(tr("tache.planif"), lambda j, a: planif.etat(), self._etat_planif_lu, silencieux=True)

    # ------------------------------------------------------------ construction
    def _construire(self):
        centre = QtWidgets.QWidget()
        h = QtWidgets.QHBoxLayout(centre)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        self.nav = QtWidgets.QListWidget()
        self.nav.setObjectName("navigation")
        self.nav.setFixedWidth(230)
        self.pile = QtWidgets.QStackedWidget()
        self.pages = {}
        for classe in PAGES:
            page = classe(self)
            self.pages[classe.cle] = page
            self.pile.addWidget(page)
            self.nav.addItem(tr(f"page.{classe.cle}"))
        self.nav.currentRowChanged.connect(self.pile.setCurrentIndex)
        self.nav.setCurrentRow(0)
        h.addWidget(self.nav)

        droite = QtWidgets.QVBoxLayout()
        droite.setContentsMargins(0, 0, 0, 0)
        self.bandeau = QtWidgets.QFrame()
        self.bandeau.setObjectName("bandeau")
        hb = QtWidgets.QHBoxLayout(self.bandeau)
        hb.addWidget(etiquette(tr("admin.bandeau")), 1)
        hb.addWidget(bouton(tr("admin.relancer"), self.relancer_admin))
        self.bandeau.setVisible(not systeme.est_admin())
        marge = QtWidgets.QVBoxLayout()
        marge.setContentsMargins(12, 8, 12, 0)
        marge.addWidget(self.bandeau)
        droite.addLayout(marge)
        droite.addWidget(self.pile, 1)

        bas = QtWidgets.QWidget()
        vb = QtWidgets.QVBoxLayout(bas)
        vb.setContentsMargins(12, 4, 12, 8)
        ligne = QtWidgets.QHBoxLayout()
        self.etat = QtWidgets.QLabel(tr("etat.pret"))
        self.etat.setObjectName("etat")
        self.etape = QtWidgets.QLabel("")              # étape et dernière ligne, console cachée ou non
        self.etape.setObjectName("etape")
        self.etape.setMinimumWidth(50)
        self.etape.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
        self.b_annuler = bouton(tr("action.annuler"), self.file.annuler)
        self.b_annuler.setVisible(False)
        self.b_console = QtWidgets.QToolButton()
        self.b_console.setText(tr("console.afficher"))
        self.b_console.setCheckable(True)
        self.b_console.toggled.connect(self._basculer_console)
        ligne.addWidget(self.etat)
        ligne.addWidget(self.etape, 1)
        ligne.addWidget(self.b_annuler)
        ligne.addWidget(self.b_console)
        vb.addLayout(ligne)
        self.progres = QtWidgets.QProgressBar()
        self.progres.setObjectName("progres")
        self.progres.setRange(0, 0)
        self.progres.setTextVisible(True)
        self.progres.setFormat("%p %")
        self.progres.setVisible(False)
        vb.addWidget(self.progres)
        self.file.avance.connect(self._avance)
        self.console = QtWidgets.QPlainTextEdit()
        self.console.setObjectName("console")
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(5000)
        self.console.setMinimumHeight(150)
        self.console.setVisible(False)
        vb.addWidget(self.console)
        droite.addWidget(bas)
        h.addLayout(droite, 1)
        self.setCentralWidget(centre)
        if self.qsettings.value("console", False, type=bool):
            self.b_console.setChecked(True)

    def _menus(self):
        self.menuBar().clear()
        fichier = self.menuBar().addMenu(tr("menu.fichier"))
        fichier.addAction(tr("menu.donnees"), lambda: systeme.ouvrir(str(systeme.dossier_donnees())))
        fichier.addSeparator()
        fichier.addAction(tr("menu.quitter"), self.close).setShortcut("Ctrl+Q")
        lang = self.menuBar().addMenu(tr("menu.langue"))
        groupe = QtGui.QActionGroup(self)
        choisie = self.qsettings.value("langue", "auto", type=str)
        for code, cle in (("auto", "menu.langue.auto"), ("fr", "menu.langue.fr"), ("en", "menu.langue.en")):
            act = lang.addAction(tr(cle))
            act.setCheckable(True)
            act.setChecked(code == choisie)
            act.triggered.connect(lambda _=False, c=code: self._changer_langue(c))
            groupe.addAction(act)
        aide = self.menuBar().addMenu(tr("menu.aide"))
        aide.addAction(tr("menu.manuel"), self._ouvrir_manuel).setShortcut("F1")
        aide.addSeparator()
        aide.addAction(tr("menu.maj"), lambda: self._check_update(manual=True))
        aide.addAction(tr("menu.signaler"), self._signaler_probleme)
        self.act_autoreport = aide.addAction(tr("menu.rapports_auto"))
        self.act_autoreport.setCheckable(True)
        try:
            import reporting
            self.act_autoreport.setChecked(reporting.consentement() is True)
        except Exception:
            self.act_autoreport.setEnabled(False)
        self.act_autoreport.toggled.connect(self._basculer_rapports)
        aide.addSeparator()
        aide.addAction(tr("menu.a_propos"), self._a_propos)

    def _changer_langue(self, code: str):
        from .i18n import definir_langue
        self.qsettings.setValue("langue", code)
        definir_langue(code if code in ("fr", "en") else None)
        page = self.nav.currentRow()
        self._construire()
        self._menus()
        self.nav.setCurrentRow(page)
        self.rafraichir_tout()

    # ------------------------------------------------------------ navigation
    def aller(self, cle: str):
        for i, classe in enumerate(PAGES):
            if classe.cle == cle:
                self.nav.setCurrentRow(i)

    def rafraichir_tout(self):
        for page in self.pages.values():
            page.rafraichir()

    # ------------------------------------------------------------ travaux
    def lancer(self, titre: str, fonction, rappel=None, silencieux: bool = False):
        if not silencieux:
            self._ligne(f"— {titre}")
        self.file.ajouter(titre, fonction, rappel)

    def _debut_tache(self, titre):
        attente = len(self.file) - 1
        self.etat.setText(titre + (f"  (+{attente})" if attente > 0 else ""))
        self._libelle_etape = ""
        self._afficher_etape("")
        self.progres.setRange(0, 0)               # « occupé » tant que le travail n'a rien dit
        self.progres.setVisible(True)
        self.b_annuler.setVisible(True)

    def _fin_file(self):
        self.etat.setText(tr("etat.pret"))
        self.etape.setText("")
        self.progres.setVisible(False)
        self.b_annuler.setVisible(False)

    def _avance(self, milliemes: int, libelle: str):
        if self.progres.maximum() != 1000:
            self.progres.setRange(0, 1000)
        self.progres.setValue(milliemes)
        if libelle:
            self._libelle_etape = libelle
            self._afficher_etape("")

    def _afficher_etape(self, derniere: str):
        """« Étape — dernière ligne du journal », coupée à la largeur disponible."""
        morceaux = [m for m in (getattr(self, "_libelle_etape", ""), derniere.strip()) if m]
        texte = "  ·  ".join(dict.fromkeys(morceaux))
        if texte:
            texte = "— " + texte
        largeur = max(50, self.etape.width())
        self.etape.setText(self.etape.fontMetrics().elidedText(texte, QtCore.Qt.TextElideMode.ElideRight, largeur))
        self.etape.setToolTip(texte)

    def _ligne(self, texte: str):
        barre = self.console.verticalScrollBar()
        self.console.appendPlainText(texte)
        self._journal_courant.append(texte)
        # la console suit toujours la dernière ligne (même après une sélection)
        self.console.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        barre.setValue(barre.maximum())
        if self.file.occupee and not texte.startswith("— "):
            self._afficher_etape(texte.splitlines()[-1] if texte.strip() else "")

    def _basculer_console(self, oui: bool):
        self.console.setVisible(oui)
        self.b_console.setText(tr("console.masquer") if oui else tr("console.afficher"))
        self.qsettings.setValue("console", oui)

    def _etat_planif_lu(self, etat, erreur):
        self.etat_planif = etat if not erreur else None
        self.rafraichir_tout()

    def proposer_mode_auto(self):
        """Premier lancement : proposer le passage automatique, une seule fois."""
        if self.reglages.planif_proposee or self.etat_planif is not None:
            return
        self.reglages.planif_proposee = True
        mod_reglages.enregistrer(self.reglages)
        if not self.confirmer(tr("msg.proposer_auto")):
            return
        if not systeme.est_admin():
            self.message(tr("msg.auto_admin"))
            self.aller("planif")
            return
        r = self.reglages
        ok, detail = planif.creer(r.auto_frequence, r.auto_jour, r.auto_heure)
        self.etat_planif = planif.etat()
        self.rafraichir_tout()
        self.message(tr("planif.ok") if ok else tr("planif.echec", detail=detail), alerte=not ok)

    def verifier_tout(self, etapes: set | None = None):
        faites = etapes or {"programmes", "windows", "raccourcis", "menage"}

        def fini(b, erreur):
            if erreur:
                return self.erreur_tache(erreur)
            for etape, attributs in ETAPES.items():
                if etape in faites:
                    for nom in attributs:
                        setattr(self.bilan, nom, getattr(b, nom))
            self.bilan.erreurs.update(b.erreurs)
            self.rafraichir_tout()
            if b.erreurs:
                self.message(tr("msg.erreurs_etapes", liste="\n".join(
                    f"• {tr('etape.' + k)} : {v}" for k, v in b.erreurs.items())), alerte=True)

        self.lancer(tr("tache.verifier"),
                    lambda j, a: orchestre.verifier_tout(self.reglages, j, a, etapes), fini)

    def tout_mettre_a_jour(self):
        b = self.bilan
        if b.inventaire is None and b.windows is None:
            self.message(tr("msg.verifier_dabord"))
            return
        n_win = len([m for m in (b.windows or []) if self.reglages.facultatives or not m.facultatif])
        if not self.confirmer(tr("msg.confirmer_tout", liste=self.plan_tout(b, systeme.est_admin() or n_win > 0))):
            return
        if n_win and not systeme.est_admin() and not self.exiger_admin():
            return
        self._journal_courant = []
        self.lancer(tr("tache.tout"),
                    lambda j, a: orchestre.tout_mettre_a_jour(self.reglages, j, a, bilan=b),
                    self.fin_tout_mettre_a_jour)

    def plan_tout(self, b, admin: bool) -> str:
        """Ce que « Mettre à jour et nettoyer » va faire, ligne par ligne, avec les vrais nombres."""
        from . import menage
        r = self.reglages
        lignes, pas_fait = [], []
        n_prog = len(orchestre.a_mettre_a_jour(b, r))
        if n_prog:
            lignes.append(tr("tout.programmes", n=n_prog))
        if b.windows is not None:
            voulues = [m for m in b.windows if r.facultatives or not m.facultatif]
            fac = sum(1 for m in voulues if m.facultatif)
            if voulues:
                lignes.append(tr("tout.windows_fac", n=len(voulues), f=fac) if fac
                              else tr("tout.windows", n=len(voulues)))
            lignes.append(tr("tout.defender"))
        elements = [e for e in menage.ELEMENTS if e.coche and (admin or not e.admin)]
        if elements:
            taille = sum((b.menage.get(e.cle) or (0, 0))[0] or 0 for e in elements)
            lignes.append(tr("tout.menage", taille=menage.taille_lisible(taille),
                             liste=", ".join(_minuscule(tr("menage." + e.cle)) for e in elements)))
        pilotes = [c for c in b.cartes if c.etat == "maj" and c.source == "nvidia" and c.fichier]
        if pilotes and r.auto_pilote:
            lignes += [tr("tout.pilote", version=c.derniere) for c in pilotes]
        elif pilotes:
            pas_fait.append(tr("tout.pas_pilote"))
        if b.morts and r.auto_raccourcis:
            lignes.append(tr("tout.raccourcis", n=len(b.morts)))
        elif b.morts:
            pas_fait.append(tr("tout.pas_raccourcis"))
        for c in b.cartes:
            if c.etat == "maj" and c.source == "amd":
                pas_fait.append(tr("tout.pas_amd", version=c.derniere))
        hors = [x for x in b.hors if x.etat == "maj"]
        if hors:
            pas_fait.insert(0, tr("tout.pas_hors", n=len(hors)))
        texte = "\n".join(lignes)
        if pas_fait:
            texte += "\n\n" + tr("tout.pas_fait", liste=" ; ".join(pas_fait))
        return texte

    def fin_tout_mettre_a_jour(self, resume, erreur):
        if erreur:
            return self.erreur_tache(erreur)
        self.consigner(resume)
        self.message("\n".join(resume))
        self.bilan = orchestre.Bilan()
        self.rafraichir_tout()
        self.verifier_tout()
        if systeme.redemarrage_en_attente():
            self.proposer_redemarrage()

    def consigner(self, lignes: list[str], mode: str = "manuel"):
        try:
            historique.ajouter(mode, list(self._journal_courant) + [""] + lignes, " · ".join(lignes)[:300])
        except OSError:
            pass
        self._journal_courant = []
        if "historique" in self.pages:
            self.pages["historique"].rafraichir()

    def telecharger_et_installer(self, r: sources.Resultat):
        nom_fichier = r.fichier.rsplit("/", 1)[-1].split("?")[0] or "installeur.exe"
        dest = systeme.sous_dossier("telechargements") / nom_fichier
        if not self.confirmer(tr("msg.confirmer_installeur", nom=r.nom, version=r.derniere,
                                 adresse=r.fichier)):
            return

        def travail(journal, annulation):
            dernier = [0]

            def prog(lu, total):
                if total:
                    orchestre.avancer(journal, lu / total, nom_fichier)
                if total and lu * 10 // total != dernier[0]:
                    dernier[0] = lu * 10 // total
                    journal(f"{nom_fichier} : {lu * 100 // total} %")

            systeme.telecharger_fichier(r.fichier, dest, prog, annulation)
            journal(tr("journal.lancement", nom=nom_fichier))
            return systeme.lancer_installeur(dest)

        def fini(code, erreur):
            if erreur:
                return self.erreur_tache(erreur)
            ligne = (tr("msg.installeur_fini", nom=r.nom, code=code) if code is not None
                     else tr("msg.installeur_lance", nom=r.nom))
            self.consigner([ligne])
            self.message(ligne)

        self.lancer(tr("tache.telecharger", nom=r.nom), travail, fini)

    # ------------------------------------------------------------ dialogues
    def message(self, texte: str, alerte: bool = False):
        if alerte:
            QtWidgets.QMessageBox.warning(self, "Martinet", texte)
        else:
            QtWidgets.QMessageBox.information(self, "Martinet", texte)

    def confirmer(self, texte: str) -> bool:
        r = QtWidgets.QMessageBox.question(self, "Martinet", texte)
        return r == QtWidgets.QMessageBox.StandardButton.Yes

    def erreur_tache(self, erreur: str):
        if erreur == "annule":
            self.etat.setText(tr("etat.annule"))
            return
        self.message(tr("msg.erreur", detail=erreur), alerte=True)

    def exiger_admin(self) -> bool:
        if systeme.est_admin():
            return True
        if self.confirmer(tr("admin.demander")):
            self.relancer_admin()
        return False

    def relancer_admin(self):
        if systeme.relancer_en_admin(["--sans-elevation"]):
            QtWidgets.QApplication.quit()
        else:
            self.message(tr("admin.refuse"), alerte=True)

    def proposer_redemarrage(self):
        if self.confirmer(tr("msg.redemarrer")):
            systeme.executer(["shutdown.exe", "/r", "/t", "60", "/c", "Martinet"], timeout=30)

    def closeEvent(self, ev):
        if self.file.occupee and not self.confirmer(tr("msg.quitter_en_cours")):
            ev.ignore()
            return
        self.file.annuler()
        super().closeEvent(ev)

    # ------------------------------------------------------------ aide, kit
    def _ouvrir_manuel(self):
        try:
            import interface_kit
            if interface_kit.ouvrir_manuel([RACINE / "docs"], langue()):
                return
        except Exception:
            pass
        self.message(tr("msg.manuel_absent"))

    def _a_propos(self):
        boite = QtWidgets.QMessageBox(self)
        boite.setWindowTitle(tr("menu.a_propos"))
        logo = RACINE / "logo_128.png"
        if logo.exists():
            boite.setIconPixmap(QtGui.QPixmap(str(logo)))
        boite.setText(tr("a_propos.texte", version=__version__))
        boite.exec()

    def _basculer_rapports(self, coche: bool):
        try:
            import reporting
            reporting.definir_consentement(bool(coche))
        except Exception:
            pass

    def _check_update(self, manual: bool = False):
        if not hasattr(self, "_maj_branche"):
            self._maj_signal.connect(self._update_result)
            self._maj_branche = True
        if manual:
            self.statusBar().showMessage(tr("maj.recherche"))

        def worker():
            try:
                import updater
                info = updater.check(__version__)
            except Exception:
                info = None
            self._maj_signal.emit(info, manual)

        threading.Thread(target=worker, daemon=True, name="martinet-maj").start()

    def _update_result(self, info, manual: bool):
        self.statusBar().clearMessage()
        if not info:
            if manual:
                QtWidgets.QMessageBox.information(self, tr("maj.titre"), tr("maj.a_jour", version=__version__))
            return
        try:
            import updater
            installe = bool(updater.is_packaged())
            page = f"https://github.com/{updater.REPO}/releases/latest"
        except Exception:
            installe, page = False, ""
        box = QtWidgets.QMessageBox(self)
        box.setWindowTitle(tr("maj.titre"))
        box.setText(tr("maj.dispo", nouvelle=info["version"], version=__version__))
        notes = (info.get("notes") or "").strip()
        try:
            import updater
            notes = updater.notes_dans_la_langue(notes, langue())
        except Exception:
            pass
        if notes:
            box.setDetailedText(notes[:4000])
        oui = box.addButton(tr("maj.installer") if installe else tr("maj.page"),
                            QtWidgets.QMessageBox.ButtonRole.AcceptRole)
        box.addButton(tr("maj.plus_tard"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
        box.exec()
        if box.clickedButton() is not oui:
            return
        if not installe:
            if page:
                QtGui.QDesktopServices.openUrl(QtCore.QUrl(page))
            return
        self._telecharger_maj(info)

    def _telecharger_maj(self, info: dict):
        import updater
        dlg = QtWidgets.QProgressDialog(tr("maj.telechargement"), None, 0, 100, self)
        dlg.setWindowTitle(tr("maj.titre"))
        dlg.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dlg.setCancelButton(None)
        dlg.setMinimumDuration(0)
        etat = {"fait": 0, "total": 0, "fini": False, "erreur": None, "pose": False}

        def _prog(done, total):
            etat["fait"], etat["total"] = done, total

        def worker():
            try:
                etat["pose"] = bool(updater.download_and_apply(info, progress=_prog))
            except Exception as exc:
                etat["erreur"] = exc
            finally:
                etat["fini"] = True

        threading.Thread(target=worker, daemon=True, name="martinet-maj-pose").start()
        poll = QtCore.QTimer(self)
        poll.setInterval(100)

        def tick():
            if not etat["fini"]:
                if etat["total"] > 0:
                    dlg.setValue(min(99, etat["fait"] * 100 // etat["total"]))
                return
            poll.stop()
            dlg.close()
            if etat["erreur"] is not None or not etat["pose"]:
                texte = str(etat["erreur"] or "archive invalide")
                verrou = ("WinError 32" in texte or "used by another process" in texte
                          or isinstance(etat["erreur"], PermissionError))
                QtWidgets.QMessageBox.warning(self, tr("maj.titre"),
                                              tr("maj.verrou") if verrou else tr("maj.echec", erreur=texte))
                return
            QtWidgets.QMessageBox.information(self, tr("maj.titre"), tr("maj.redemarre"))
            try:
                updater.restart()
            finally:
                QtWidgets.QApplication.quit()

        poll.timeout.connect(tick)
        poll.start()
        self._maj_poll = poll

    def _signaler_probleme(self):
        try:
            import reporting
        except Exception:
            return
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(tr("signal.titre"))
        dlg.resize(560, 360)
        lo = QtWidgets.QVBoxLayout(dlg)
        lo.addWidget(QtWidgets.QLabel(tr("signal.invite")))
        texte = QtWidgets.QPlainTextEdit()
        texte.setPlaceholderText(tr("signal.exemple"))
        lo.addWidget(texte)
        note = etiquette(tr("signal.note"), style.GRIS)
        lo.addWidget(note)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.StandardButton.Ok
                                          | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        btns.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setText(tr("signal.envoyer"))
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lo.addWidget(btns)
        if dlg.exec() != QtWidgets.QDialog.DialogCode.Accepted:
            return
        description = texte.toPlainText().strip()
        if not description:
            return
        accord = reporting.consentement()
        if accord is not True:
            reporting.definir_consentement(True)
        rapport = reporting.envoyer("manuel", description=description, version=__version__)
        if accord is not True:
            reporting.definir_consentement(bool(accord))
        chemin = None
        try:
            chemin = reporting.paquet_local(rapport, None)
        except Exception:
            pass
        msg = (tr("signal.parti") if rapport.get("transmis", True) and not chemin
               else tr("signal.local", chemin=chemin))
        QtWidgets.QMessageBox.information(self, tr("signal.merci"), msg)


ETAPES = {"programmes": ("inventaire", "hors", "sans_source"), "windows": ("cartes", "windows"),
          "raccourcis": ("morts",), "menage": ("menage",)}

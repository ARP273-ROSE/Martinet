"""Pages propres à Linux (Manjaro / Arch) : paquets et état du système."""
from __future__ import annotations

import os

from PyQt6 import QtWidgets

from . import linux_paquets, menage, style, systeme
from .i18n import tr
from .pages import Page
from .widgets import Tableau, bouton, etiquette, rangee


# ====================================================================== paquets
class PagePaquets(Page):
    cle = "paquets"

    def __init__(self, fen):
        super().__init__(fen)
        self.b_maj = bouton(tr("lx.tout_maj"), self.mettre_a_jour, principal=True)
        self.v.addLayout(rangee(bouton(tr("action.rechercher"), lambda: fen.verifier_tout({"programmes"})),
                                self.b_maj))
        self.info = etiquette("", style.GRIS)
        self.outil = etiquette("", style.GRIS)
        self.v.addWidget(self.info)
        self.table = Tableau([tr("col.paquet"), tr("col.installee"), tr("col.disponible"), tr("col.provenance")],
                             cochable=False)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Stretch)
        self.v.addWidget(self.table, 1)
        self.v.addWidget(self.outil)
        self.rafraichir()

    def rafraichir(self):
        paquets = self.bilan.paquets
        o = linux_paquets.outils()
        gestionnaire = "pamac" if o["pamac"] else "yay" if o["yay"] else "pacman"
        self.outil.setText(tr("lx.gestionnaire", outil=gestionnaire))
        if paquets is None:
            self.table.remplir([])
            self.info.setText(tr("accueil.pas_verifie"))
            self.b_maj.setEnabled(False)
            return
        self.table.remplir(([p.nom, p.installee, p.disponible, tr("lx.origine." + p.origine)], p, False, None)
                           for p in paquets)
        n = {o: sum(1 for p in paquets if p.origine == o) for o in ("depots", "aur", "flatpak")}
        self.info.setText(tr("lx.resume_paquets", n=len(paquets), depots=n["depots"], aur=n["aur"],
                             flatpak=n["flatpak"]) if paquets else tr("accueil.a_jour"))
        self.b_maj.setEnabled(bool(paquets))

    def mettre_a_jour(self):
        if not self.fen.confirmer(tr("lx.confirmer_maj", n=len(self.bilan.paquets or []))):
            return

        def fini(r, erreur):
            if erreur:
                return self.fen.erreur_tache(erreur)
            ok, detail = r
            ligne = (tr("lx.resume.paquets", n=len(self.bilan.paquets or [])) if ok
                     else tr("lx.resume.paquets_ko", detail=detail))
            self.fen.consigner([ligne])
            self.fen.message(ligne, alerte=not ok)
            self.fen.verifier_tout({"programmes", "windows"})
            if systeme.redemarrage_en_attente():
                self.fen.proposer_redemarrage()

        self.fen.lancer(tr("lx.tache_maj"), lambda j, a: linux_paquets.mettre_a_jour(j, a), fini)


# ====================================================================== système
class PageSysteme(Page):
    cle = "systeme"

    def __init__(self, fen):
        super().__init__(fen)
        zone = QtWidgets.QScrollArea()
        zone.setWidgetResizable(True)
        zone.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        dedans = QtWidgets.QWidget()
        v = QtWidgets.QVBoxLayout(dedans)
        v.setContentsMargins(0, 0, 6, 0)
        self.v.addLayout(rangee(bouton(tr("action.rechercher"), lambda: fen.verifier_tout({"windows"}))))

        g = QtWidgets.QGroupBox(tr("lx.noyau"))
        vg = QtWidgets.QVBoxLayout(g)
        self.l_noyau = etiquette("")
        self.b_redemarrer = bouton(tr("lx.redemarrer"), fen.proposer_redemarrage)
        vg.addWidget(self.l_noyau)
        vg.addLayout(rangee(self.b_redemarrer))
        v.addWidget(g)

        g = QtWidgets.QGroupBox(tr("lx.micrologiciels"))
        vg = QtWidgets.QVBoxLayout(g)
        self.l_fw = etiquette("", style.GRIS)
        self.t_fw = Tableau([tr("col.appareil"), tr("col.installee"), tr("col.disponible")], cochable=False)
        self.t_fw.setMaximumHeight(140)
        self.b_fw = bouton(tr("lx.fw_installer"), self.micrologiciels)
        vg.addWidget(self.l_fw)
        vg.addWidget(self.t_fw)
        vg.addLayout(rangee(self.b_fw))
        v.addWidget(g)

        g = QtWidgets.QGroupBox(tr("lx.pacnew"))
        vg = QtWidgets.QVBoxLayout(g)
        self.l_pacnew = etiquette(tr("lx.pacnew.aide"), style.GRIS)
        self.t_pacnew = Tableau([tr("col.fichier")], cochable=False)
        self.t_pacnew.setMaximumHeight(140)
        vg.addWidget(self.l_pacnew)
        vg.addWidget(self.t_pacnew)
        vg.addLayout(rangee(bouton(tr("racc.ouvrir_dossier"), self.ouvrir_pacnew)))
        v.addWidget(g)

        g = QtWidgets.QGroupBox(tr("lx.orphelins"))
        vg = QtWidgets.QVBoxLayout(g)
        self.l_orph = etiquette("", style.GRIS)
        self.t_orph = Tableau([tr("col.paquet"), tr("col.taille")])
        self.t_orph.setMaximumHeight(180)
        self.b_orph = bouton(tr("lx.orphelins_retirer"), self.retirer_orphelins)
        vg.addWidget(self.l_orph)
        vg.addWidget(self.t_orph)
        vg.addLayout(rangee(self.b_orph))
        v.addWidget(g)

        g = QtWidgets.QGroupBox(tr("lx.hors_depots"))
        vg = QtWidgets.QVBoxLayout(g)
        self.l_hors = etiquette("", style.GRIS)
        vg.addWidget(self.l_hors)
        v.addWidget(g)
        v.addStretch(1)
        zone.setWidget(dedans)
        self.v.addWidget(zone, 1)
        self.rafraichir()

    def rafraichir(self):
        s = self.bilan.lx
        if s is None:
            self.l_noyau.setText(tr("accueil.pas_verifie"))
            for t in (self.t_fw, self.t_pacnew, self.t_orph):
                t.remplir([])
            for l in (self.l_fw, self.l_orph, self.l_hors):
                l.setText("")
            self.b_redemarrer.setEnabled(False)
            self.b_fw.setEnabled(False)
            self.b_orph.setEnabled(False)
            return
        lignes = [tr("lx.noyau_en_marche", noyau=s.noyau or "?")]
        lignes.append(tr("lx.redemarrer_oui") if s.redemarrer else tr("lx.redemarrer_non"))
        for k in s.noyaux_fin_de_vie:
            lignes.append(tr("lx.noyau_fin", noyau=k))
        self.l_noyau.setText("<br>".join(lignes))
        self.b_redemarrer.setEnabled(s.redemarrer)
        self.t_fw.remplir(([m.appareil, m.installee, m.disponible], m, False, None) for m in s.micrologiciels)
        if not s.outils.get("fwupdmgr", True):
            self.l_fw.setText(tr("lx.fw_absent"))
        else:
            self.l_fw.setText(tr("lx.fw_n", n=len(s.micrologiciels)) if s.micrologiciels else tr("lx.fw_rien"))
        self.b_fw.setEnabled(bool(s.micrologiciels))
        self.t_pacnew.remplir(([p], p, False, None) for p in s.pacnew)
        self.t_orph.remplir(([n, menage.taille_lisible(t)], n, False, None) for n, t in s.orphelins)
        self.l_orph.setText(tr("lx.orphelins_n", n=len(s.orphelins)) if s.orphelins else tr("lx.orphelins_rien"))
        self.b_orph.setEnabled(bool(s.orphelins))
        aur = [n for n in s.hors_depots if n not in s.noyaux_fin_de_vie]
        self.l_hors.setText(tr("lx.hors_depots_n", n=len(aur), liste=", ".join(aur[:40]))
                            if aur else tr("lx.hors_depots_rien"))

    def ouvrir_pacnew(self):
        for p in self.t_pacnew.selection()[:1]:
            systeme.ouvrir(os.path.dirname(p))

    def micrologiciels(self):
        if not self.fen.confirmer(tr("lx.fw_confirmer")):
            return

        def fini(r, erreur):
            if erreur:
                return self.fen.erreur_tache(erreur)
            ok, detail = r
            ligne = tr("lx.fw_ok") if ok else tr("lx.fw_ko", detail=detail)
            self.fen.consigner([ligne])
            self.fen.message(ligne, alerte=not ok)
            self.fen.verifier_tout({"windows"})

        self.fen.lancer(tr("lx.micrologiciels"), lambda j, a: linux_paquets.mettre_a_jour_micrologiciels(j, a),
                        fini)

    def retirer_orphelins(self):
        choix = self.t_orph.donnees()
        if not choix:
            self.fen.message(tr("msg.rien_coche"))
            return
        if not self.fen.confirmer(tr("lx.orphelins_confirmer", liste=", ".join(choix))):
            return

        def fini(r, erreur):
            if erreur:
                return self.fen.erreur_tache(erreur)
            ok, detail = r
            ligne = tr("lx.orphelins_ok", n=len(choix)) if ok else tr("lx.orphelins_ko", detail=detail)
            self.fen.consigner([ligne])
            self.fen.message(ligne, alerte=not ok)
            self.fen.verifier_tout({"windows"})

        self.fen.lancer(tr("lx.orphelins_retirer"), lambda j, a: linux_paquets.retirer_orphelins(choix, j, a), fini)


def regle_polkit_case(page) -> QtWidgets.QCheckBox | None:
    """Case « sans mot de passe » de la page Planification (pamac seulement)."""
    if not linux_paquets.outils()["pamac"]:
        return None
    c = QtWidgets.QCheckBox(tr("lx.sans_mot_de_passe"))
    c.setToolTip(tr("lx.sans_mot_de_passe.bulle"))
    c.setChecked(linux_paquets.regle_active())
    return c



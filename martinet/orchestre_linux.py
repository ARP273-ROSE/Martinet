"""Linux (Manjaro / Arch) : vérifier tout, puis tout faire, comme sous Windows.

Les étapes gardent les noms de la version Windows (« programmes » = paquets
des dépôts, de l'AUR et Flatpak ; « windows » = état du système) : la
fenêtre et la planification n'ont pas à savoir sur quel système elles sont.
"""
from __future__ import annotations

from . import linux_paquets, menage, raccourcis, systeme
from .i18n import tr
from .orchestre import Bilan, avancer
from .reglages import Reglages


def verifier_tout(reglages: Reglages, journal=None, annulation=None, etapes=None) -> Bilan:
    etapes = etapes or {"programmes", "windows", "raccourcis", "menage"}
    b = Bilan()
    parts = [(n, w) for n, w in (("programmes", 2), ("windows", 1), ("raccourcis", 0.3), ("menage", 0.7))
             if n in etapes]
    total = sum(w for _, w in parts) or 1
    debuts, cumul = {}, 0.0
    for n, w in parts:
        debuts[n] = (cumul / total, w / total)
        cumul += w

    def part(nom, dedans=0.0, detail=""):
        debut, poids = debuts[nom]
        avancer(journal, debut + poids * dedans, tr("lx.etape." + nom) + (f" — {detail}" if detail else ""))

    def etape(nom, fn):
        if annulation is not None and annulation.is_set():
            raise systeme.Annule()
        part(nom)
        try:
            fn()
        except systeme.Annule:
            raise
        except Exception as exc:              # une étape en échec n'arrête pas les autres
            b.erreurs[nom] = str(exc)[:300]
            if journal:
                journal(tr("journal.echec_etape", etape=nom, detail=str(exc)[:200]))

    if "programmes" in etapes:
        etape("programmes", lambda: setattr(b, "paquets", linux_paquets.rechercher(journal)))
    if "windows" in etapes:
        etape("windows", lambda: setattr(b, "lx", linux_paquets.etat_systeme(journal)))
    if "raccourcis" in etapes:
        etape("raccourcis", lambda: setattr(b, "morts", raccourcis.chercher_morts(journal)))
    if "menage" in etapes:
        def _menage():
            el = menage.elements()
            for i, e in enumerate(el):
                part("menage", i / len(el), tr("menage." + e.cle))
                b.menage[e.cle] = menage.mesurer(e.cle)
        etape("menage", _menage)
    avancer(journal, 1.0)
    return b


def a_nettoyer(reglages: Reglages) -> list:
    return [e for e in menage.elements() if e.coche]


def tout_mettre_a_jour(reglages: Reglages, journal=None, annulation=None, programmes=True, nettoyer=True,
                       bilan: Bilan | None = None, ranger_raccourcis: bool | None = None) -> list[str]:
    ranger_raccourcis = reglages.auto_raccourcis if ranger_raccourcis is None else ranger_raccourcis
    b = bilan or verifier_tout(reglages, journal, annulation,
                               {x for x, oui in (("programmes", programmes), ("menage", nettoyer)) if oui}
                               | {"raccourcis", "windows"})
    resume: list[str] = []

    def stop():
        if annulation is not None and annulation.is_set():
            raise systeme.Annule()

    unites = 3                       # paquets, ménage, lanceurs
    if programmes and b.paquets:
        stop()
        avancer(journal, 0.0, tr("lx.etape.programmes"))
        ok, detail = linux_paquets.mettre_a_jour(journal, annulation)
        resume.append(tr("lx.resume.paquets", n=len(b.paquets)) if ok
                      else tr("lx.resume.paquets_ko", detail=detail))
    elif programmes and b.paquets is not None:
        resume.append(tr("lx.resume.rien"))
    if nettoyer:
        stop()
        avancer(journal, 1 / unites, tr("etape.menage"))
        cles = [e.cle for e in a_nettoyer(reglages)]
        libere = menage.nettoyer_tout(cles, journal)
        resume.append(tr("resume.menage", taille=menage.taille_lisible(libere)))
    avancer(journal, 2 / unites, tr("etape.raccourcis"))
    if b.morts and ranger_raccourcis:
        try:
            n, _erreurs = raccourcis.mettre_de_cote(b.morts)
            resume.append(tr("racc.deplaces", n=n))
        except OSError as exc:
            resume.append(tr("resume.etape_ko", etape=tr("etape.raccourcis"), detail=str(exc)[:200]))
    elif b.morts:
        resume.append(tr("resume.raccourcis", n=len(b.morts)))
    # ce qui reste à faire à la main : signalé seulement
    lx = b.lx
    if lx is not None:
        if lx.micrologiciels:
            resume.append(tr("lx.resume.micrologiciels", n=len(lx.micrologiciels)))
        if lx.pacnew:
            resume.append(tr("lx.resume.pacnew", n=len(lx.pacnew)))
        if lx.orphelins:
            resume.append(tr("lx.resume.orphelins", n=len(lx.orphelins)))
        for k in lx.noyaux_fin_de_vie:
            resume.append(tr("lx.resume.noyau_fin", noyau=k))
    avancer(journal, 1.0)
    if systeme.redemarrage_en_attente():
        resume.append(tr("resume.redemarrer"))
    return resume

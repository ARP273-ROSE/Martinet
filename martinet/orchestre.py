"""Enchaînements communs à la fenêtre et à la tâche planifiée.

« Tout vérifier » ne modifie rien ; « tout mettre à jour » applique ce qui
peut l'être sans intervention (winget, Windows Update, ménage coché) et se
contente de SIGNALER le reste : un logiciel hors winget ou un pilote NVIDIA
s'installent avec l'utilisateur devant l'écran.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import materiel, menage, raccourcis, sources, systeme, windows_update, winget
from .i18n import tr
from .reglages import Reglages


@dataclass
class Bilan:
    inventaire: winget.Inventaire | None = None
    hors: list = field(default_factory=list)          # sources.Resultat
    sans_source: list = field(default_factory=list)   # winget.Paquet
    cartes: list = field(default_factory=list)        # sources.Resultat
    windows: list | None = None                       # windows_update.MiseAJour
    morts: list | None = None                         # raccourcis.Raccourci
    menage: dict = field(default_factory=dict)        # clé -> (taille, nombre)
    erreurs: dict = field(default_factory=dict)       # étape -> message


def _est_bruit(p: winget.Paquet) -> bool:
    """Entrées de « winget list » qui ne sont pas des logiciels à suivre."""
    ident = p.id.upper()
    if ident.startswith("MSIX\\"):          # applis du Store / de Windows, suivies par le Store
        return True
    if "STEAM APP " in ident:                # jeux : Steam les met à jour
        return True
    nom = p.nom.lower()
    return (nom.startswith(BRUIT) or "(kb" in nom)


#: composants de Windows et pilotes déjà livrés par Windows Update
BRUIT = ("security update", "update for", "mise à jour", "package de pilotes windows", "windows driver package",
         "microsoft visual c++", "microsoft windows desktop runtime", "microsoft .net", "microsoft update health",
         "microsoft windows application compatibility", "windows sdk", "vs_", "microsoft visual studio installer")


def hors_winget(inv: winget.Inventaire, reglages: Reglages, journal=None):
    """(résultats des logiciels qui ont une source, logiciels sans source)."""
    catalogue = sources.charger()
    candidats = [p for p in inv.non_suivis if not _est_bruit(p)]
    if not inv.paquets:                      # winget absent : on lit le registre
        candidats = [winget.Paquet("", n, v) for n, v, _ in materiel.logiciels_du_registre()]
    suivis = [p.nom for p in inv.paquets if p.suivi]
    ignores = {n.lower() for n in reglages.ignores_hors_winget}
    resultats, sans_source = [], []
    for p in sorted(candidats, key=lambda x: x.nom.lower()):
        if p.nom.lower() in ignores:
            continue
        source = next((s for s in catalogue if s.correspond(p.nom)), None)
        if source is None:
            sans_source.append(p)
            continue
        if any(source.correspond(n) for n in suivis):
            continue                          # une autre entrée du même logiciel est suivie
        if journal:
            journal(tr("journal.source", nom=p.nom))
        resultats.append(sources.verifier(source, p.nom, p.installee))
    return resultats, sans_source


def verifier_tout(reglages: Reglages, journal=None, annulation=None, etapes=None) -> Bilan:
    etapes = etapes or {"programmes", "windows", "raccourcis", "menage"}
    b = Bilan()

    def etape(nom, fn):
        if annulation is not None and annulation.is_set():
            raise systeme.Annule()
        try:
            fn()
        except systeme.Annule:
            raise
        except Exception as exc:              # une étape en échec n'arrête pas les autres
            b.erreurs[nom] = str(exc)[:300]
            if journal:
                journal(tr("journal.echec_etape", etape=nom, detail=str(exc)[:200]))

    if "programmes" in etapes:
        def _prog():
            b.inventaire = winget.inventaire(journal)
            b.hors, b.sans_source = hors_winget(b.inventaire, reglages, journal)
        etape("programmes", _prog)
    if "windows" in etapes:
        etape("cartes", lambda: setattr(b, "cartes", [sources.verifier_carte(c)
                                                      for c in materiel.cartes_graphiques()]))
        etape("windows", lambda: setattr(b, "windows", windows_update.rechercher(journal)))
    if "raccourcis" in etapes:
        etape("raccourcis", lambda: setattr(b, "morts", raccourcis.chercher_morts(journal)))
    if "menage" in etapes:
        etape("menage", lambda: b.menage.update({e.cle: menage.mesurer(e.cle) for e in menage.ELEMENTS}))
    return b


def a_mettre_a_jour(b: Bilan, reglages: Reglages) -> list[winget.Paquet]:
    if not b.inventaire:
        return []
    return [p for p in b.inventaire.a_jour if p.id not in reglages.ignores_winget]


def tout_mettre_a_jour(reglages: Reglages, journal=None, annulation=None,
                       programmes=True, windows=True, nettoyer=True, bilan: Bilan | None = None,
                       admin: bool | None = None, pilote: bool | None = None,
                       ranger_raccourcis: bool | None = None) -> list[str]:
    """Applique les mises à jour sans intervention ; renvoie le résumé."""
    admin = systeme.est_admin() if admin is None else admin
    pilote = reglages.auto_pilote if pilote is None else pilote
    ranger_raccourcis = reglages.auto_raccourcis if ranger_raccourcis is None else ranger_raccourcis
    resume: list[str] = []
    b = bilan or verifier_tout(reglages, journal, annulation,
                               {x for x, oui in (("programmes", programmes), ("windows", windows),
                                                 ("menage", nettoyer)) if oui} | {"raccourcis"})

    def stop():
        if annulation is not None and annulation.is_set():
            raise systeme.Annule()

    if programmes and b.inventaire is not None:
        liste = a_mettre_a_jour(b, reglages)
        ok = 0
        echecs = []
        for p in liste:
            stop()
            if journal:
                journal(tr("journal.maj_paquet", nom=p.nom, avant=p.installee, apres=p.disponible))
            reussi, code = winget.mettre_a_jour(p.id, journal, annulation)
            if reussi:
                ok += 1
            else:
                echecs.append(f"{p.nom} ({code})")
        resume.append(tr("resume.programmes", ok=ok, n=len(liste)))
        if echecs:
            resume.append(tr("resume.echecs", liste=", ".join(echecs)))
    if windows and b.windows is not None:
        voulues = [m for m in b.windows if reglages.facultatives or not m.facultatif]
        if voulues and admin:
            stop()
            r = windows_update.installer([m.id for m in voulues], journal, annulation)
            resume.append(tr("resume.windows", n=len(voulues),
                             etat=tr("wu.code." + windows_update.decrire(r))))
        elif voulues:
            resume.append(tr("resume.windows_admin", n=len(voulues)))
        else:
            resume.append(tr("resume.windows_rien"))
        windows_update.mettre_a_jour_defender(journal)
    if nettoyer:
        libere = 0
        for e in menage.ELEMENTS:
            stop()
            if e.coche and (admin or not e.admin):
                libere += menage.nettoyer(e.cle, journal)
        resume.append(tr("resume.menage", taille=menage.taille_lisible(libere)))
    poses = set()
    if pilote and admin:
        for r in b.cartes:
            if r.etat == "maj" and r.source == "nvidia" and r.fichier:
                stop()
                ok, detail = installer_pilote_silencieux(r, journal, annulation)
                resume.append(tr("resume.pilote_ok", version=r.derniere) if ok
                              else tr("resume.pilote_ko", detail=detail))
                if ok:
                    poses.add(id(r))
    # ce qui demande l'utilisateur : signalé seulement
    a_faire = [r for r in b.hors + b.cartes if r.etat == "maj" and id(r) not in poses]
    for r in a_faire:
        resume.append(tr("resume.a_faire", nom=r.nom, avant=r.installee, apres=r.derniere))
    if b.morts and ranger_raccourcis:
        n, _erreurs = raccourcis.mettre_de_cote(b.morts)
        resume.append(tr("racc.deplaces", n=n))
    elif b.morts:
        resume.append(tr("resume.raccourcis", n=len(b.morts)))
    if systeme.redemarrage_en_attente():
        resume.append(tr("resume.redemarrer"))
    return resume


#: options de l'installeur NVIDIA : installation EXPRESS (réglages par défaut,
#: composants par défaut, réglages existants conservés — pas de « -clean »),
#: sans fenêtre et sans redémarrage forcé
NVIDIA_SILENCIEUX = ["-s", "-noreboot"]


def installer_pilote_silencieux(r, journal=None, annulation=None) -> tuple[bool, str]:
    """Télécharge l'installeur officiel NVIDIA et le lance sans fenêtre."""
    if systeme_demo():
        return True, ""
    nom = r.fichier.rsplit("/", 1)[-1] or "nvidia.exe"
    dest = systeme.sous_dossier("telechargements") / nom
    if journal:
        journal(tr("journal.lancement", nom=nom))
    try:
        systeme.telecharger_fichier(r.fichier, dest, None, annulation)
        code, _ = systeme.executer_flux([str(dest), *NVIDIA_SILENCIEUX], journal, annulation, timeout=3600)
    except systeme.Annule:
        raise
    except Exception as exc:                          # noqa: BLE001 — rapporté dans le résumé
        return False, str(exc)[:200]
    return code == 0, ("" if code == 0 else f"code {code}")


def systeme_demo() -> bool:
    from . import demo
    return demo.actif()

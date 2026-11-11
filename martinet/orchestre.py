"""Enchaînements communs à la fenêtre et à la tâche planifiée.

« Tout vérifier » ne modifie rien ; « mettre à jour et nettoyer » applique ce qui
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


def avancer(journal, fraction: float, libelle: str = "") -> None:
    """Fait avancer la barre de la fenêtre (sans effet en ligne de commande)."""
    f = getattr(journal, "progres", None)
    if f is not None:
        f(max(0.0, min(1.0, fraction)), libelle)


def hors_winget(inv: winget.Inventaire, reglages: Reglages, journal=None, sur_avance=None):
    """(résultats des logiciels qui ont une source, logiciels sans source)."""
    catalogue = sources.charger()
    candidats = [p for p in inv.non_suivis if not _est_bruit(p)]
    if not inv.paquets:                      # winget absent : on lit le registre
        candidats = [winget.Paquet("", n, v) for n, v, _ in materiel.logiciels_du_registre()]
    suivis = [p.nom for p in inv.paquets if p.suivi]
    ignores = {n.lower() for n in reglages.ignores_hors_winget}
    resultats, sans_source = [], []
    tries = sorted(candidats, key=lambda x: x.nom.lower())
    for i, p in enumerate(tries):
        if sur_avance is not None:
            sur_avance(i / max(1, len(tries)), p.nom)
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
    # parts de la barre : (étape, poids) dans l'ordre où elles s'enchaînent
    parts = [(n, w) for n, w in (("programmes", 1), ("hors", 2), ("cartes", 0.3), ("windows", 2),
                                  ("raccourcis", 0.3), ("menage", 0.5))
             if n in etapes or (n == "hors" and "programmes" in etapes)
             or (n == "cartes" and "windows" in etapes)]
    total = sum(w for _, w in parts) or 1
    debuts, cumul = {}, 0.0
    for n, w in parts:
        debuts[n] = (cumul / total, w / total)
        cumul += w

    def part(nom, dedans=0.0, detail=""):
        debut, poids = debuts[nom]
        avancer(journal, debut + poids * dedans,
                tr("etape." + nom) + (f" — {detail}" if detail else ""))

    def etape(nom, fn):
        if annulation is not None and annulation.is_set():
            raise systeme.Annule()
        if nom in debuts:
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
        def _prog():
            b.inventaire = winget.inventaire(journal)
            part("hors")
            b.hors, b.sans_source = hors_winget(b.inventaire, reglages, journal,
                                                lambda f, nom: part("hors", f, nom))
        etape("programmes", _prog)
    if "windows" in etapes:
        etape("cartes", lambda: setattr(b, "cartes", [sources.verifier_carte(c)
                                                      for c in materiel.cartes_graphiques()]))
        etape("windows", lambda: setattr(b, "windows", windows_update.rechercher(journal)))
    if "raccourcis" in etapes:
        etape("raccourcis", lambda: setattr(b, "morts", raccourcis.chercher_morts(journal)))
    if "menage" in etapes:
        def _menage():
            for i, e in enumerate(menage.ELEMENTS):
                part("menage", i / len(menage.ELEMENTS), tr("menage." + e.cle))
                b.menage[e.cle] = menage.mesurer(e.cle)
        etape("menage", _menage)
    avancer(journal, 1.0)
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

    liste = a_mettre_a_jour(b, reglages) if programmes and b.inventaire is not None else []
    a_nettoyer = [e for e in menage.ELEMENTS if e.coche and (admin or not e.admin)] if nettoyer else []
    pilotes = [r for r in b.cartes if r.etat == "maj" and r.source == "nvidia" and r.fichier] \
        if pilote and admin else []
    unites = (len(liste) + (2 if windows and b.windows is not None else 0) + len(a_nettoyer)
              + len(pilotes) + 1) or 1
    fait = [0]

    def pas(libelle: str):
        avancer(journal, fait[0] / unites, libelle)
        fait[0] += 1

    if programmes and b.inventaire is not None:
        ok = 0
        echecs = []
        for p in liste:
            stop()
            pas(f"{p.nom} {p.installee} → {p.disponible}")
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
        pas("Windows Update")
        if voulues and admin:
            stop()
            try:
                r = windows_update.installer([m.id for m in voulues], journal, annulation)
                resume.append(tr("resume.windows", n=len(voulues),
                                 etat=tr("wu.code." + windows_update.decrire(r))))
            except systeme.Annule:
                raise
            except Exception as exc:          # noqa: BLE001 — la suite (pilote, ménage…) continue
                resume.append(tr("resume.etape_ko", etape="Windows Update", detail=str(exc)[:200]))
        elif voulues:
            resume.append(tr("resume.windows_admin", n=len(voulues)))
        else:
            resume.append(tr("resume.windows_rien"))
        pas("Microsoft Defender")
        try:
            windows_update.mettre_a_jour_defender(journal)
        except Exception as exc:              # noqa: BLE001
            if journal:
                journal(str(exc)[:200])
    if nettoyer:
        libere = 0
        for e in a_nettoyer:
            stop()
            pas(tr("menage." + e.cle))
            try:
                libere += menage.nettoyer(e.cle, journal)
            except OSError as exc:
                if journal:
                    journal(f"{e.cle} : {exc}")
        resume.append(tr("resume.menage", taille=menage.taille_lisible(libere)))
    poses = set()
    for r in pilotes:
        stop()
        pas(f"{r.nom} {r.derniere}")
        ok, detail = installer_pilote_silencieux(r, journal, annulation)
        resume.append(tr("resume.pilote_ok", version=r.derniere) if ok
                      else tr("resume.pilote_ko", detail=detail))
        if ok:
            poses.add(id(r))
    # ce qui demande l'utilisateur : signalé seulement
    a_faire = [r for r in b.hors + b.cartes if r.etat == "maj" and id(r) not in poses]
    for r in a_faire:
        resume.append(tr("resume.a_faire", nom=r.nom, avant=r.installee, apres=r.derniere))
    pas(tr("etape.raccourcis"))
    if b.morts and ranger_raccourcis:
        try:
            n, _erreurs = raccourcis.mettre_de_cote(b.morts)
            resume.append(tr("racc.deplaces", n=n))
        except OSError as exc:
            resume.append(tr("resume.etape_ko", etape="raccourcis", detail=str(exc)[:200]))
    elif b.morts:
        resume.append(tr("resume.raccourcis", n=len(b.morts)))
    avancer(journal, 1.0)
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

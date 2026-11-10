#!/usr/bin/env python3
"""Lanceur de Martinet — tenir Windows à jour d'un seul geste.

    python run.py                 ouvre la fenêtre
    python run.py --auto          passage automatique (tâche planifiée)
    python run.py --verifier      liste ce qui est à mettre à jour, sans rien changer

Branchement du kit commun : rapports d'incident (plantage Python, crash
natif, gel), accord au premier lancement, verrou nommé lu par l'installeur,
vérification silencieuse des mises à jour de Martinet lui-même.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or ".")

NOM = "Martinet"
_fichier_faulthandler = None


def _dossier_donnees() -> Path:
    from martinet import systeme
    return systeme.dossier_donnees()


def _demarrer_rapports() -> None:
    dossier = _dossier_donnees()
    trace_native = dossier / "_crash_natif.log"
    try:
        import reporting
        from martinet import __version__
        reporting.init(dossier, application="martinet", version=__version__)
        reporting.relever_crash_natif(trace_native)
        reporting.reprendre_file_en_fond()
    except Exception:
        pass
    try:
        import faulthandler
        global _fichier_faulthandler
        _fichier_faulthandler = open(trace_native, "w", encoding="utf-8")
        faulthandler.enable(file=_fichier_faulthandler, all_threads=True)
    except Exception:
        pass


def _demander_accord(win) -> None:
    try:
        import reporting
        from PyQt6 import QtWidgets
        premier = reporting.consentement() is None
        if premier:
            from martinet.i18n import tr
            boite = QtWidgets.QMessageBox(win)
            boite.setWindowTitle(NOM)
            boite.setIcon(QtWidgets.QMessageBox.Icon.Question)
            boite.setText(tr("accord.titre"))
            boite.setInformativeText(tr("accord.texte"))
            oui = boite.addButton(tr("dlg.oui"), QtWidgets.QMessageBox.ButtonRole.AcceptRole)
            boite.addButton(tr("dlg.non"), QtWidgets.QMessageBox.ButtonRole.RejectRole)
            boite.exec()
            reporting.definir_consentement(boite.clickedButton() is oui)
            win.act_autoreport.setChecked(reporting.consentement() is True)
        reporting.signaler_demarrage(premier=premier)
    except Exception:
        pass


def _rapport_crash(exc: BaseException) -> None:
    """Une application fenêtrée n'a pas de console : sans ce filet, une erreur
    au démarrage fermerait le programme sans rien montrer."""
    import datetime
    import traceback
    texte = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    entete = f"{NOM} — erreur au démarrage — {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
    chemin = _dossier_donnees() / "martinet-erreur.log"
    try:
        with open(chemin, "a", encoding="utf-8") as fh:
            fh.write(entete + texte + "\n")
    except OSError:
        chemin = "(journal impossible à écrire)"
    sys.stderr.write(entete + texte) if sys.stderr else None
    try:
        import reporting
        reporting.signaler_plantage(texte)
    except Exception:
        pass
    try:
        from PyQt6 import QtWidgets
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])  # noqa: F841
        from martinet.i18n import tr
        QtWidgets.QMessageBox.critical(
            None, NOM, tr("demarrage.echec", erreur=f"{type(exc).__name__}: {exc}", chemin=chemin))
    except Exception:
        pass


def _verifier() -> int:
    """--check : l'application et ses dépendances se chargent (lancé par la
    construction des paquets avec l'interpréteur embarqué ; aucune fenêtre)."""
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    try:
        from PyQt6 import QtWidgets
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv[:1])
        import interface_kit  # noqa: F401
        import reporting  # noqa: F401
        import updater  # noqa: F401
        from martinet import fenetre, orchestre, style  # noqa: F401
        style.appliquer(app)
        del app
    except Exception as exc:
        print(f"Martinet : ECHEC / FAILED -- {type(exc).__name__}: {exc}")
        return 1
    print("Martinet : OK")
    return 0


def _liste_console() -> int:
    """--verifier : bilan texte, sans rien modifier."""
    for flux in (sys.stdout, sys.stderr):        # console Windows : pas de caractère illisible
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    from martinet import orchestre, reglages
    from martinet.i18n import tr
    r = reglages.charger()
    b = orchestre.verifier_tout(r, print)
    print()
    for p in orchestre.a_mettre_a_jour(b, r):
        print(f"[winget]  {p.nom} : {p.installee} -> {p.disponible}")
    for x in b.hors + b.cartes:
        if x.etat == "maj":
            print(f"[{x.source}]  {x.nom} : {x.installee} -> {x.derniere}")
    for m in b.windows or []:
        print(f"[Windows] {m.titre}")
    for k, v in b.erreurs.items():
        print(tr("journal.echec_etape", etape=k, detail=v))
    return 0


def main() -> int:
    if "--check" in sys.argv[1:]:
        return _verifier()
    from martinet.i18n import definir_langue, tr
    ap = argparse.ArgumentParser(description=tr("cli.description"))
    ap.add_argument("--auto", action="store_true", help="scheduled run / passage planifié")
    ap.add_argument("--verifier", "--list", action="store_true", help="list updates / lister")
    ap.add_argument("--sans-elevation", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--lang", choices=["fr", "en"], help="interface language / langue")
    from martinet import __version__
    ap.add_argument("--version", action="version", version=f"Martinet {__version__}")
    args = ap.parse_args()

    from PyQt6 import QtCore
    choix = args.lang or QtCore.QSettings("ARP273-ROSE", NOM).value("langue", "auto", type=str)
    definir_langue(choix if choix in ("fr", "en") else None)

    if args.verifier:
        return _liste_console()
    _demarrer_rapports()
    if args.auto:
        from martinet import auto
        return auto.executer()

    from martinet import reglages, systeme
    if (systeme.WINDOWS and not args.sans_elevation and not systeme.est_admin()
            and reglages.charger().elever_au_demarrage):
        # une seule fenêtre UAC au lancement plutôt qu'une par installeur ;
        # en cas de refus, on continue sans les droits (bandeau dans la fenêtre)
        if systeme.relancer_en_admin(["--sans-elevation"] + (["--lang", args.lang] if args.lang else [])):
            return 0

    from PyQt6 import QtGui, QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName(NOM)
    from martinet import style
    style.appliquer(app)
    try:
        import interface_kit
        interface_kit.installer_dialogues_fichiers()
    except Exception:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            app._mutex_installeur = ctypes.windll.kernel32.CreateMutexW(None, False, f"{NOM}EnCours")
        except Exception:
            pass
    icone = Path(__file__).resolve().parent / "logo.png"
    if icone.exists():
        app.setWindowIcon(QtGui.QIcon(str(icone)))

    from martinet.fenetre import FenetrePrincipale
    win = FenetrePrincipale()
    win.show()
    QtCore.QTimer.singleShot(1200, lambda: (_demander_accord(win), win.proposer_mode_auto()))
    try:
        import updater
        if updater.is_packaged():
            QtCore.QTimer.singleShot(3000, lambda: win._check_update(manual=False))
    except Exception:
        pass
    try:
        import reporting
        vigie = reporting.Vigie(seuil=10.0, periode=2.0)
        vigie.demarrer()
        minuteur = QtCore.QTimer(win)
        minuteur.timeout.connect(vigie.battre)
        minuteur.start(2000)
        win._vigie, win._vigie_timer = vigie, minuteur
    except Exception:
        pass
    return app.exec()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as _exc:          # noqa: BLE001 — filet volontaire
        _rapport_crash(_exc)
        sys.exit(1)

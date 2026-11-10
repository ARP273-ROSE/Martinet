"""Textes de Martinet en français et en anglais, langue détectée automatiquement.

Règles (les mêmes que MountMonitor) :
* chaque clé existe dans les deux langues — un test l'exige ;
* les champs de format ({n}, {nom}…) sont les mêmes d'une langue à l'autre,
  sinon le texte lèverait une erreur à l'exécution, chez l'utilisateur ;
* une clé manquante retombe sur l'anglais, puis sur la clé elle-même :
  un texte non traduit est un défaut cosmétique, un bouton vide est une panne.

Ce module ne dépend pas de Qt : la tâche planifiée l'utilise aussi.
"""
from __future__ import annotations

import os
import sys

LANGUES = ("fr", "en")
_langue = None


def detecter() -> str:
    """Langue d'AFFICHAGE du système (pas celle des formats de date).

    Windows : GetUserDefaultUILanguage (la locale de format peut être
    britannique chez un francophone, et inversement). macOS : la liste
    AppleLanguages des préférences globales, lue sans lancer de commande.
    Linux : variables d'environnement.
    """
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        val = os.environ.get(var, "")
        if val and val not in ("C", "POSIX") and not val.startswith("C."):
            return "fr" if val.lower().startswith("fr") else "en"
    if sys.platform == "win32":
        try:
            import ctypes
            langid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            return "fr" if (langid & 0x3FF) == 0x0C else "en"
        except Exception:
            pass
    if sys.platform == "darwin":
        try:
            import plistlib
            from pathlib import Path
            chemin = Path.home() / "Library" / "Preferences" / ".GlobalPreferences.plist"
            with open(chemin, "rb") as f:
                langues = plistlib.load(f).get("AppleLanguages") or []
            if langues:
                return "fr" if str(langues[0]).lower().startswith("fr") else "en"
        except Exception:
            pass
    return "en"


def definir_langue(code: str | None) -> str:
    """Fixe la langue ('fr', 'en', ou None/'auto' pour la détection)."""
    global _langue
    _langue = code if code in LANGUES else detecter()
    return _langue


def langue() -> str:
    return _langue or definir_langue(None)


def tr(cle: str, **champs) -> str:
    textes = TEXTES.get(cle)
    if not textes:
        return cle
    modele = textes.get(langue()) or textes.get("en") or cle
    try:
        return modele.format(**champs) if champs else modele
    except (KeyError, IndexError, ValueError):
        return modele


def pluriel(n: int, cle_un: str, cle_plusieurs: str, **champs) -> str:
    return tr(cle_un if n == 1 else cle_plusieurs, n=n, **champs)


TEXTES: dict[str, dict[str, str]] = {
    # ---- général
    "cli.description": {"fr": "Tenir Windows à jour : programmes, Windows, pilotes, raccourcis, ménage.",
                        "en": "Keep Windows up to date: programs, Windows, drivers, shortcuts, clean-up."},
    "demarrage.echec": {"fr": "Martinet n'a pas pu démarrer :\n{erreur}\n\nDétails enregistrés dans :\n{chemin}",
                        "en": "Martinet could not start:\n{erreur}\n\nDetails saved in:\n{chemin}"},
    "dlg.oui": {"fr": "Oui", "en": "Yes"},
    "dlg.non": {"fr": "Non", "en": "No"},
    "accord.titre": {"fr": "Envoyer automatiquement les rapports d'incident ?",
                     "en": "Send incident reports automatically?"},
    "accord.texte": {"fr": "Si Martinet plante ou se fige, un rapport technique (version, système, trace de "
                           "l'erreur) peut partir tout seul pour aider à corriger le défaut. Il ne contient ni la "
                           "liste de vos logiciels ni vos fichiers. Modifiable à tout moment dans le menu Aide.",
                     "en": "If Martinet crashes or freezes, a technical report (version, system, error trace) "
                           "can be sent automatically to help fix the defect. It contains neither your list of "
                           "programs nor your files. You can change this at any time in the Help menu."},
    "a_propos.texte": {"fr": "<b>Martinet {version}</b><br>Tenir Windows à jour d'un seul geste : programmes "
                             "(winget), logiciels hors winget, Windows Update et pilotes, raccourcis morts, "
                             "ménage.<br><br>Logiciel libre — ARP273-ROSE",
                       "en": "<b>Martinet {version}</b><br>Keep Windows up to date in one go: programs "
                             "(winget), programs outside winget, Windows Update and drivers, dead shortcuts, "
                             "clean-up.<br><br>Free software — ARP273-ROSE"},
    "format.date": {"fr": "%d/%m/%Y", "en": "%Y-%m-%d"},
    "format.date_heure": {"fr": "%d/%m/%Y %H:%M", "en": "%Y-%m-%d %H:%M"},
    "auto.titre": {"fr": "Martinet — passage automatique", "en": "Martinet — scheduled run"},
    # ---- menus
    "menu.fichier": {"fr": "&Fichier", "en": "&File"},
    "menu.donnees": {"fr": "Ouvrir le dossier des données", "en": "Open the data folder"},
    "menu.quitter": {"fr": "Quitter", "en": "Quit"},
    "menu.langue": {"fr": "&Langue", "en": "&Language"},
    "menu.langue.auto": {"fr": "Automatique (langue du système)", "en": "Automatic (system language)"},
    "menu.langue.fr": {"fr": "Français", "en": "Français"},
    "menu.langue.en": {"fr": "English", "en": "English"},
    "menu.aide": {"fr": "&Aide", "en": "&Help"},
    "menu.manuel": {"fr": "Manuel (PDF)", "en": "User guide (PDF)"},
    "menu.maj": {"fr": "Rechercher une mise à jour de Martinet", "en": "Check for Martinet updates"},
    "menu.signaler": {"fr": "Signaler un problème…", "en": "Report a problem…"},
    "menu.rapports_auto": {"fr": "Envoi automatique des rapports d'incident",
                           "en": "Send incident reports automatically"},
    "menu.a_propos": {"fr": "À propos", "en": "About"},
    # ---- pages
    "page.accueil": {"fr": "Tableau de bord", "en": "Dashboard"},
    "page.accueil.aide": {"fr": "Tout vérifier en un clic, puis tout mettre à jour. Rien n'est modifié "
                                "pendant la vérification.",
                          "en": "Check everything in one click, then update everything. Nothing is changed "
                                "while checking."},
    "page.programmes": {"fr": "Programmes (winget)", "en": "Programs (winget)"},
    "page.programmes.aide": {"fr": "Les logiciels et applis du Store que winget, le gestionnaire de paquets "
                                   "de Windows, sait mettre à jour sans fenêtre.",
                             "en": "Programs and Store apps that winget, the Windows package manager, can "
                                   "update silently."},
    "page.hors": {"fr": "Hors winget", "en": "Outside winget"},
    "page.hors.aide": {"fr": "Les logiciels que winget ne suit pas. Ceux qui ont une source connue sont "
                             "comparés à la dernière version publiée par leur éditeur.",
                       "en": "Programs that winget does not track. Those with a known source are compared "
                             "with the latest version published by their vendor."},
    "page.windows": {"fr": "Windows et pilotes", "en": "Windows and drivers"},
    "page.windows.aide": {"fr": "Windows Update (système et pilotes des fabricants), antivirus Defender et "
                                "pilote de la carte graphique.",
                          "en": "Windows Update (system and vendor drivers), Defender antivirus and graphics "
                                "card driver."},
    "page.raccourcis": {"fr": "Raccourcis morts", "en": "Dead shortcuts"},
    "page.raccourcis.aide": {"fr": "Raccourcis du Bureau, du menu Démarrer et de la barre des tâches dont la "
                                   "cible a disparu. Ils sont mis de côté, jamais effacés.",
                             "en": "Desktop, Start menu and taskbar shortcuts whose target has disappeared. "
                                   "They are set aside, never deleted."},
    "page.menage": {"fr": "Ménage", "en": "Clean-up"},
    "page.menage.aide": {"fr": "Seulement ce que Windows sait recréer. Les fichiers en cours d'utilisation "
                               "sont laissés en place.",
                         "en": "Only what Windows can recreate. Files in use are left in place."},
    "page.planif": {"fr": "Planification", "en": "Schedule"},
    "page.planif.aide": {"fr": "Martinet peut passer tout seul, chaque semaine ou chaque jour, et vous "
                               "prévenir par une notification.",
                         "en": "Martinet can run on its own, weekly or daily, and let you know with a "
                               "notification."},
    "page.historique": {"fr": "Historique", "en": "History"},
    "page.historique.aide": {"fr": "Chaque passage, manuel ou automatique, avec le détail de ce qui a été fait.",
                             "en": "Every run, manual or scheduled, with the details of what was done."},
    # ---- état, actions communes
    "etat.pret": {"fr": "Prêt.", "en": "Ready."},
    "etat.annule": {"fr": "Opération annulée.", "en": "Operation cancelled."},
    "etat.maj": {"fr": "Mise à jour disponible", "en": "Update available"},
    "etat.a_jour": {"fr": "À jour", "en": "Up to date"},
    "etat.erreur": {"fr": "Vérification impossible : {detail}", "en": "Cannot check: {detail}"},
    "etat.inconnu": {"fr": "Version installée inconnue", "en": "Installed version unknown"},
    "etat.seul": {"fr": "Se met à jour tout seul", "en": "Updates itself"},
    "action.verifier": {"fr": "Vérifier", "en": "Check"},
    "action.annuler": {"fr": "Annuler", "en": "Cancel"},
    "action.ouvrir_page": {"fr": "Ouvrir la page", "en": "Open the page"},
    "action.tout_cocher": {"fr": "Tout cocher", "en": "Check all"},
    "action.tout_decocher": {"fr": "Tout décocher", "en": "Uncheck all"},
    "console.afficher": {"fr": "Afficher le détail", "en": "Show details"},
    "console.masquer": {"fr": "Masquer le détail", "en": "Hide details"},
    "admin.bandeau": {"fr": "Martinet tourne sans les droits administrateur : Windows Update, une partie du "
                            "ménage et la planification ne sont pas disponibles.",
                      "en": "Martinet is running without administrator rights: Windows Update, part of the "
                            "clean-up and scheduling are not available."},
    "admin.relancer": {"fr": "Relancer en administrateur", "en": "Restart as administrator"},
    "admin.demander": {"fr": "Cette action demande les droits administrateur. Relancer Martinet en "
                             "administrateur ?",
                       "en": "This action requires administrator rights. Restart Martinet as administrator?"},
    "admin.refuse": {"fr": "Les droits administrateur ont été refusés.", "en": "Administrator rights were denied."},
    # ---- colonnes
    "col.logiciel": {"fr": "Logiciel", "en": "Program"},
    "col.id": {"fr": "Identifiant", "en": "Id"},
    "col.installee": {"fr": "Installée", "en": "Installed"},
    "col.disponible": {"fr": "Disponible", "en": "Available"},
    "col.derniere": {"fr": "Dernière", "en": "Latest"},
    "col.source": {"fr": "Source", "en": "Source"},
    "col.etat": {"fr": "État", "en": "Status"},
    "col.version": {"fr": "Version", "en": "Version"},
    "col.titre": {"fr": "Mise à jour", "en": "Update"},
    "col.type": {"fr": "Type", "en": "Type"},
    "col.taille": {"fr": "Taille", "en": "Size"},
    "col.raccourci": {"fr": "Raccourci", "en": "Shortcut"},
    "col.lieu": {"fr": "Où", "en": "Where"},
    "col.cible": {"fr": "Cible introuvable", "en": "Missing target"},
    "col.origine": {"fr": "Emplacement d'origine", "en": "Original location"},
    "col.date": {"fr": "Date", "en": "Date"},
    "col.element": {"fr": "Élément", "en": "Item"},
    "col.description": {"fr": "Description", "en": "Description"},
    "col.mode": {"fr": "Mode", "en": "Mode"},
    "col.resume": {"fr": "Résumé", "en": "Summary"},
    # ---- tableau de bord
    "accueil.verifier": {"fr": "Tout vérifier", "en": "Check everything"},
    "accueil.tout": {"fr": "Tout mettre à jour", "en": "Update everything"},
    "accueil.pas_verifie": {"fr": "Pas encore vérifié", "en": "Not checked yet"},
    "accueil.a_jour": {"fr": "Tout est à jour", "en": "Everything is up to date"},
    "accueil.n_maj": {"fr": "{n} mise(s) à jour disponible(s)", "en": "{n} update(s) available"},
    "accueil.sans_source": {"fr": "{n} sans source connue", "en": "{n} without a known source"},
    "accueil.pilote_gpu": {"fr": "pilote graphique {version} disponible", "en": "graphics driver {version} available"},
    "accueil.n_morts": {"fr": "{n} raccourci(s) mort(s)", "en": "{n} dead shortcut(s)"},
    "accueil.aucun_mort": {"fr": "Aucun raccourci mort", "en": "No dead shortcuts"},
    "accueil.recuperable": {"fr": "{taille} récupérables", "en": "{taille} can be freed"},
    "accueil.planif_aucune": {"fr": "Aucun passage automatique", "en": "No scheduled run"},
    "accueil.planif_prochaine": {"fr": "Prochain passage : {date}", "en": "Next run: {date}"},
    # ---- programmes
    "prog.maj_selection": {"fr": "Mettre à jour la sélection", "en": "Update selected"},
    "prog.ignorer": {"fr": "Ignorer / ne plus ignorer", "en": "Ignore / stop ignoring"},
    "prog.ignorer.aide": {"fr": "Un logiciel ignoré n'est plus jamais mis à jour par Martinet, ni à la main "
                                "ni par la tâche planifiée.",
                          "en": "An ignored program is never updated by Martinet again, neither manually nor "
                                "by the scheduled run."},
    "prog.voir_ignores": {"fr": "Afficher les ignorés", "en": "Show ignored"},
    "prog.ignore": {"fr": "ignoré", "en": "ignored"},
    "prog.resume": {"fr": "{n} mise(s) à jour — {suivis} logiciels suivis par winget.",
                    "en": "{n} update(s) — {suivis} programs tracked by winget."},
    "prog.sans_winget": {"fr": "winget est absent : installez « Programme d'installation d'application » depuis "
                               "le Microsoft Store.",
                         "en": "winget is missing: install “App Installer” from the Microsoft Store."},
    # ---- hors winget
    "hors.avec_source": {"fr": "Logiciels avec une source connue", "en": "Programs with a known source"},
    "hors.installer": {"fr": "Télécharger et installer", "en": "Download and install"},
    "hors.installer.aide": {"fr": "Télécharge l'installeur officiel de l'éditeur et le lance : vous suivez "
                                  "l'installation à l'écran.",
                            "en": "Downloads the vendor's official installer and runs it: you follow the "
                                  "installation on screen."},
    "hors.sources": {"fr": "Sources…", "en": "Sources…"},
    "hors.sans_source": {"fr": "Logiciels sans source connue", "en": "Programs without a known source"},
    "hors.sans_source.aide": {"fr": "Pour chacun : le confier à winget s'il le connaît, lui ajouter une source "
                                    "(dépôt GitHub ou page de l'éditeur), ou l'ignorer.",
                              "en": "For each one: hand it over to winget if winget knows it, add a source "
                                    "(GitHub repository or vendor page), or ignore it."},
    "hors.chercher_winget": {"fr": "Confier à winget…", "en": "Hand over to winget…"},
    "hors.chercher_winget.aide": {"fr": "Cherche ce logiciel dans le catalogue winget ; s'il y est, winget le "
                                        "réinstalle par-dessus et le suit ensuite.",
                                  "en": "Looks for this program in the winget catalogue; if found, winget "
                                        "reinstalls it over the existing one and tracks it from then on."},
    "hors.ajouter_source": {"fr": "Ajouter une source…", "en": "Add a source…"},
    "hors.web": {"fr": "Chercher sur le web", "en": "Search the web"},
    "hors.ignorer": {"fr": "Ignorer", "en": "Ignore"},
    "hors.pas_de_lien": {"fr": "Pas de lien direct pour {nom} : la page de téléchargement va s'ouvrir.",
                         "en": "No direct link for {nom}: the download page will open."},
    "hors.winget_rien": {"fr": "winget ne connaît pas « {nom} ».", "en": "winget does not know “{nom}”."},
    "hors.winget_choix": {"fr": "Paquets winget qui pourraient correspondre à « {nom} » :",
                          "en": "winget packages that may match “{nom}”:"},
    "hors.winget_avertissement": {"fr": "winget installera sa version par-dessus celle qui est présente. Les "
                                        "réglages du logiciel sont en général conservés.",
                                  "en": "winget will install its version over the existing one. The program's "
                                        "settings are usually kept."},
    "hors.confie_ok": {"fr": "{nom} est maintenant suivi par winget.", "en": "{nom} is now tracked by winget."},
    "hors.confie_ko": {"fr": "winget n'a pas pu l'installer (code {code}).",
                       "en": "winget could not install it (code {code})."},
    # ---- sources
    "src.titre": {"fr": "Source de version", "en": "Version source"},
    "src.aide": {"fr": "Indiquez où Martinet trouve la dernière version de ce logiciel.",
                 "en": "Tell Martinet where to find the latest version of this program."},
    "src.nom": {"fr": "Nom", "en": "Name"},
    "src.motif": {"fr": "Nom installé (motif)", "en": "Installed name (pattern)"},
    "src.motif.aide": {"fr": "Expression régulière comparée au nom affiché dans « Ajouter ou supprimer des "
                             "programmes ».",
                       "en": "Regular expression matched against the name shown in “Add or remove programs”."},
    "src.type": {"fr": "Type", "en": "Type"},
    "src.type_": {"fr": "?", "en": "?"},
    "src.type_github": {"fr": "Releases GitHub", "en": "GitHub releases"},
    "src.type_page": {"fr": "Page web de l'éditeur", "en": "Vendor web page"},
    "src.type_seul": {"fr": "Se met à jour tout seul", "en": "Updates itself"},
    "src.depot": {"fr": "Dépôt GitHub", "en": "GitHub repository"},
    "src.depot.exemple": {"fr": "propriétaire/dépôt", "en": "owner/repository"},
    "src.url": {"fr": "Page à lire", "en": "Page to read"},
    "src.regex": {"fr": "Motif de version", "en": "Version pattern"},
    "src.regex.aide": {"fr": "Expression régulière ; le premier groupe entre parenthèses est la version. La "
                             "plus haute trouvée sur la page est retenue.",
                       "en": "Regular expression; the first group in brackets is the version. The highest "
                             "one found on the page is kept."},
    "src.page": {"fr": "Page de téléchargement", "en": "Download page"},
    "src.tester": {"fr": "Tester", "en": "Test"},
    "src.test_en_cours": {"fr": "Interrogation…", "en": "Querying…"},
    "src.test_ok": {"fr": "Dernière version trouvée : {version}", "en": "Latest version found: {version}"},
    "src.test_lien": {"fr": "Installeur : {lien}", "en": "Installer: {lien}"},
    "src.test_ko": {"fr": "Échec : {detail}", "en": "Failed: {detail}"},
    "src.err_nom": {"fr": "Le nom et le motif sont obligatoires.", "en": "Name and pattern are required."},
    "src.err_regex": {"fr": "Motif invalide : {detail}", "en": "Invalid pattern: {detail}"},
    "src.err_depot": {"fr": "Le dépôt s'écrit propriétaire/dépôt.", "en": "The repository is written owner/repository."},
    "src.err_url": {"fr": "La page doit commencer par https://", "en": "The page must start with https://"},
    "src.gestion": {"fr": "Sources de versions", "en": "Version sources"},
    "src.gestion.aide": {"fr": "Le catalogue fourni avec Martinet et vos propres sources. Modifier une source "
                               "du catalogue crée votre version, qui la remplace.",
                         "en": "The catalogue shipped with Martinet and your own sources. Editing a catalogue "
                               "source creates your own version, which replaces it."},
    "src.adresse": {"fr": "Adresse", "en": "Address"},
    "src.origine": {"fr": "Origine", "en": "Origin"},
    "src.perso": {"fr": "Personnelle", "en": "Custom"},
    "src.catalogue": {"fr": "Catalogue", "en": "Catalogue"},
    "src.catalogue_fixe": {"fr": "Seules vos sources personnelles peuvent être supprimées.",
                           "en": "Only your custom sources can be deleted."},
    "src.ajouter": {"fr": "Ajouter…", "en": "Add…"},
    "src.modifier": {"fr": "Modifier…", "en": "Edit…"},
    "src.supprimer": {"fr": "Supprimer", "en": "Delete"},
    "src.importer": {"fr": "Importer…", "en": "Import…"},
    "src.import_ok": {"fr": "{n} source(s) importée(s).", "en": "{n} source(s) imported."},
    "src.import_ko": {"fr": "Fichier refusé : {detail}", "en": "File rejected: {detail}"},
    # ---- windows
    "win.carte": {"fr": "Carte graphique", "en": "Graphics card"},
    "win.pilote_installer": {"fr": "Télécharger et installer le pilote", "en": "Download and install the driver"},
    "win.pilote_installe": {"fr": "pilote installé : {version}", "en": "installed driver: {version}"},
    "win.pilote_maj": {"fr": "Nouveau pilote : {nom} {version} du {date}", "en": "New driver: {nom} {version} from {date}"},
    "win.pilote_a_jour": {"fr": "Pilote à jour", "en": "Driver up to date"},
    "win.pilote_inconnu": {"fr": "Vérification automatique impossible pour ce fabricant : voir sa page.",
                           "en": "Automatic check not possible for this vendor: see its page."},
    "win.pas_de_carte": {"fr": "Aucune carte graphique reconnue.", "en": "No graphics card recognised."},
    "win.mises_a_jour": {"fr": "Windows Update", "en": "Windows Update"},
    "win.rechercher": {"fr": "Rechercher", "en": "Search"},
    "win.installer": {"fr": "Installer la sélection", "en": "Install selected"},
    "win.defender": {"fr": "Mettre à jour Defender", "en": "Update Defender"},
    "win.defender_ok": {"fr": "Signatures de Defender à jour.", "en": "Defender signatures up to date."},
    "win.defender_ko": {"fr": "Defender n'a pas été mis à jour (autre antivirus ?).",
                        "en": "Defender was not updated (another antivirus?)."},
    "win.type_pilote": {"fr": "Pilote", "en": "Driver"},
    "win.type_windows": {"fr": "Windows", "en": "Windows"},
    "win.facultatif": {"fr": "facultative", "en": "optional"},
    "win.resume": {"fr": "{n} mise(s) à jour en attente.", "en": "{n} pending update(s)."},
    "win.inclure_facultatives": {"fr": "Inclure les mises à jour facultatives (ici, avec « Tout mettre à jour » "
                                       "et en automatique)",
                                 "en": "Include optional updates (here, with “Update everything” and in "
                                       "scheduled runs)"},
    "win.inclure_facultatives.aide": {"fr": "Pilotes facultatifs et mises à jour en avant-première de Windows.",
                                      "en": "Optional drivers and Windows preview updates."},
    "win.rien": {"fr": "Windows est à jour.", "en": "Windows is up to date."},
    "wu.code.non_commence": {"fr": "non commencée", "en": "not started"},
    "wu.code.en_cours": {"fr": "en cours", "en": "in progress"},
    "wu.code.reussi": {"fr": "réussie", "en": "succeeded"},
    "wu.code.reussi_erreurs": {"fr": "réussie avec des erreurs", "en": "succeeded with errors"},
    "wu.code.echec": {"fr": "échec", "en": "failed"},
    "wu.code.annule": {"fr": "annulée", "en": "cancelled"},
    # ---- raccourcis
    "racc.morts": {"fr": "Raccourcis morts", "en": "Dead shortcuts"},
    "racc.analyser": {"fr": "Analyser", "en": "Scan"},
    "racc.mettre_de_cote": {"fr": "Mettre de côté la sélection", "en": "Set selected aside"},
    "racc.ouvrir_dossier": {"fr": "Ouvrir l'emplacement", "en": "Open location"},
    "racc.de_cote": {"fr": "Raccourcis mis de côté", "en": "Shortcuts set aside"},
    "racc.restaurer": {"fr": "Restaurer la sélection", "en": "Restore selected"},
    "racc.resume": {"fr": "{n} raccourci(s) dont la cible a disparu. Les cibles sur le réseau ou sur un "
                          "lecteur absent ne sont pas comptées.",
                    "en": "{n} shortcut(s) whose target has disappeared. Targets on the network or on a "
                          "missing drive are not counted."},
    "racc.deplaces": {"fr": "{n} raccourci(s) mis de côté.", "en": "{n} shortcut(s) set aside."},
    "racc.restaures": {"fr": "{n} raccourci(s) restauré(s).", "en": "{n} shortcut(s) restored."},
    "racc.erreurs": {"fr": "Non déplacés : {liste}", "en": "Not moved: {liste}"},
    "racc.admin": {"fr": "Les raccourcis communs à tous les utilisateurs demandent les droits administrateur.",
                   "en": "Shortcuts shared by all users require administrator rights."},
    "lieu.bureau": {"fr": "Bureau", "en": "Desktop"},
    "lieu.demarrer": {"fr": "Menu Démarrer", "en": "Start menu"},
    "lieu.barre": {"fr": "Barre des tâches", "en": "Taskbar"},
    # ---- ménage
    "menage.mesurer": {"fr": "Mesurer", "en": "Measure"},
    "menage.nettoyer": {"fr": "Nettoyer la sélection", "en": "Clean selected"},
    "menage.variable": {"fr": "variable", "en": "varies"},
    "menage.admin": {"fr": "administrateur", "en": "administrator"},
    "menage.pas_de_registre": {"fr": "Martinet ne « nettoie » pas le registre : aucun gain mesurable, et un "
                                     "vrai risque de casser un logiciel.",
                               "en": "Martinet does not “clean” the registry: no measurable gain, and a real "
                                     "risk of breaking a program."},
    "menage.confirmer_corbeille": {"fr": "Vider définitivement la corbeille ?",
                                   "en": "Empty the recycle bin for good?"},
    "menage.temp_utilisateur": {"fr": "Fichiers temporaires", "en": "Temporary files"},
    "menage.temp_utilisateur.aide": {"fr": "Votre dossier temporaire, fichiers de plus de 7 jours.",
                                     "en": "Your temporary folder, files older than 7 days."},
    "menage.temp_windows": {"fr": "Fichiers temporaires de Windows", "en": "Windows temporary files"},
    "menage.temp_windows.aide": {"fr": "Le dossier temporaire du système, fichiers de plus de 7 jours.",
                                 "en": "The system temporary folder, files older than 7 days."},
    "menage.rapports_erreurs": {"fr": "Rapports d'erreurs Windows", "en": "Windows error reports"},
    "menage.rapports_erreurs.aide": {"fr": "Rapports de plantage déjà archivés ou en attente d'envoi.",
                                     "en": "Crash reports already archived or waiting to be sent."},
    "menage.optimisation_distribution": {"fr": "Cache de téléchargement de Windows Update",
                                         "en": "Windows Update download cache"},
    "menage.optimisation_distribution.aide": {"fr": "Fichiers de mises à jour déjà installées (Optimisation de "
                                                    "distribution).",
                                              "en": "Files of updates already installed (Delivery "
                                                    "Optimization)."},
    "menage.telechargements_martinet": {"fr": "Installeurs téléchargés par Martinet",
                                        "en": "Installers downloaded by Martinet"},
    "menage.telechargements_martinet.aide": {"fr": "Les installeurs des logiciels hors winget, une fois "
                                                   "utilisés.",
                                             "en": "Installers of programs outside winget, once used."},
    "menage.composants": {"fr": "Anciens composants de Windows", "en": "Old Windows components"},
    "menage.composants.aide": {"fr": "Versions remplacées par les mises à jour (DISM). Plusieurs minutes.",
                               "en": "Versions replaced by updates (DISM). Several minutes."},
    "menage.corbeille": {"fr": "Corbeille", "en": "Recycle bin"},
    "menage.corbeille.aide": {"fr": "Jamais cochée d'office.", "en": "Never checked by default."},
    # ---- planification
    "planif.quand": {"fr": "Quand", "en": "When"},
    "planif.actif": {"fr": "Passage automatique", "en": "Scheduled run"},
    "planif.frequence": {"fr": "Fréquence", "en": "Frequency"},
    "planif.hebdo": {"fr": "Chaque semaine", "en": "Every week"},
    "planif.quotidien": {"fr": "Chaque jour", "en": "Every day"},
    "planif.jour": {"fr": "Jour", "en": "Day"},
    "planif.heure": {"fr": "Heure", "en": "Time"},
    "planif.quoi": {"fr": "Ce qui est fait sans vous", "en": "What is done without you"},
    "planif.programmes": {"fr": "Mettre à jour les programmes (winget)", "en": "Update programs (winget)"},
    "planif.windows": {"fr": "Installer les mises à jour Windows et les pilotes (facultatives : voir la page "
                             "Windows et pilotes)",
                       "en": "Install Windows updates and drivers (optional ones: see the Windows and drivers "
                             "page)"},
    "planif.menage": {"fr": "Faire le ménage coché d'office", "en": "Run the default clean-up"},
    "planif.pilote": {"fr": "Installer le nouveau pilote NVIDIA (installeur officiel, sans fenêtre)",
                      "en": "Install the new NVIDIA driver (official installer, no window)"},
    "planif.raccourcis": {"fr": "Mettre de côté les raccourcis morts (récupérables dans Raccourcis morts)",
                          "en": "Set dead shortcuts aside (recoverable from Dead shortcuts)"},
    "planif.signale": {"fr": "Les logiciels hors winget sont seulement signalés par la notification : leurs "
                             "installeurs ne savent pas tous s'installer sans vous.",
                       "en": "Programs outside winget are only reported in the notification: not all of their "
                             "installers can run without you."},
    "planif.enregistrer": {"fr": "Enregistrer", "en": "Save"},
    "planif.maintenant": {"fr": "Lancer ce passage maintenant", "en": "Run it now"},
    "planif.etat_aucune": {"fr": "Aucune tâche planifiée.", "en": "No scheduled task."},
    "planif.etat": {"fr": "Prochain passage : {prochaine} — dernier : {derniere} ({resultat})",
                    "en": "Next run: {prochaine} — last: {derniere} ({resultat})"},
    "planif.res_ok": {"fr": "réussi", "en": "succeeded"},
    "planif.res_code": {"fr": "code {code}", "en": "code {code}"},
    "planif.ok": {"fr": "Planification enregistrée.", "en": "Schedule saved."},
    "planif.echec": {"fr": "La tâche planifiée n'a pas pu être enregistrée :\n{detail}",
                     "en": "The scheduled task could not be saved:\n{detail}"},
    "jour.0": {"fr": "lundi", "en": "Monday"},
    "jour.1": {"fr": "mardi", "en": "Tuesday"},
    "jour.2": {"fr": "mercredi", "en": "Wednesday"},
    "jour.3": {"fr": "jeudi", "en": "Thursday"},
    "jour.4": {"fr": "vendredi", "en": "Friday"},
    "jour.5": {"fr": "samedi", "en": "Saturday"},
    "jour.6": {"fr": "dimanche", "en": "Sunday"},
    # ---- historique
    "histo.dossier": {"fr": "Ouvrir le dossier des données", "en": "Open the data folder"},
    "mode.manuel": {"fr": "à la main", "en": "manual"},
    "mode.auto": {"fr": "automatique", "en": "scheduled"},
    # ---- travaux
    "tache.verifier": {"fr": "Vérification…", "en": "Checking…"},
    "tache.tout": {"fr": "Mise à jour de tout…", "en": "Updating everything…"},
    "tache.auto": {"fr": "Passage automatique…", "en": "Scheduled run…"},
    "tache.planif": {"fr": "Lecture de la planification…", "en": "Reading the schedule…"},
    "tache.maj_programmes": {"fr": "Mise à jour de {n} programme(s)…", "en": "Updating {n} program(s)…"},
    "tache.windows": {"fr": "Installation de {n} mise(s) à jour Windows…", "en": "Installing {n} Windows update(s)…"},
    "tache.menage": {"fr": "Ménage…", "en": "Cleaning up…"},
    "tache.telecharger": {"fr": "Téléchargement de {nom}…", "en": "Downloading {nom}…"},
    "tache.chercher": {"fr": "Recherche de {nom} dans winget…", "en": "Looking for {nom} in winget…"},
    "tache.installer": {"fr": "Installation de {nom} par winget…", "en": "Installing {nom} with winget…"},
    "etape.programmes": {"fr": "Programmes", "en": "Programs"},
    "etape.cartes": {"fr": "Carte graphique", "en": "Graphics card"},
    "etape.windows": {"fr": "Windows Update", "en": "Windows Update"},
    "etape.raccourcis": {"fr": "Raccourcis", "en": "Shortcuts"},
    "etape.menage": {"fr": "Ménage", "en": "Clean-up"},
    "journal.source": {"fr": "Dernière version de {nom}…", "en": "Latest version of {nom}…"},
    "journal.echec_etape": {"fr": "Échec de l'étape « {etape} » : {detail}", "en": "Step “{etape}” failed: {detail}"},
    "journal.maj_paquet": {"fr": "{nom} : {avant} → {apres}", "en": "{nom}: {avant} → {apres}"},
    "journal.menage": {"fr": "Ménage : {element}", "en": "Clean-up: {element}"},
    "journal.lancement": {"fr": "Lancement de {nom}", "en": "Starting {nom}"},
    # ---- résumés
    "resume.programmes": {"fr": "Programmes : {ok} sur {n} mis à jour.", "en": "Programs: {ok} of {n} updated."},
    "resume.echecs": {"fr": "Échecs : {liste}", "en": "Failures: {liste}"},
    "resume.windows": {"fr": "Windows Update : {n} mise(s) à jour, {etat}.", "en": "Windows Update: {n} update(s), {etat}."},
    "resume.windows_admin": {"fr": "Windows Update : {n} en attente (droits administrateur nécessaires).",
                             "en": "Windows Update: {n} pending (administrator rights needed)."},
    "resume.windows_rien": {"fr": "Windows Update : rien à installer.", "en": "Windows Update: nothing to install."},
    "resume.menage": {"fr": "Ménage : {taille} libérés.", "en": "Clean-up: {taille} freed."},
    "resume.pilote_ok": {"fr": "Pilote graphique {version} installé.", "en": "Graphics driver {version} installed."},
    "resume.pilote_ko": {"fr": "Pilote graphique non installé : {detail}", "en": "Graphics driver not installed: {detail}"},
    "resume.a_faire": {"fr": "À faire à la main : {nom} {avant} → {apres}", "en": "To do by hand: {nom} {avant} → {apres}"},
    "resume.raccourcis": {"fr": "{n} raccourci(s) mort(s) à examiner.", "en": "{n} dead shortcut(s) to review."},
    "resume.redemarrer": {"fr": "Un redémarrage est nécessaire pour terminer.", "en": "A restart is needed to finish."},
    # ---- messages
    "msg.proposer_auto": {"fr": "Activer le passage automatique ?\n\nChaque dimanche à 12 h, Martinet met à "
                                "jour les programmes, Windows, les pilotes et le pilote NVIDIA, range les "
                                "raccourcis morts et fait le ménage, puis vous prévient par une notification. "
                                "Tout se règle ensuite dans Planification.",
                          "en": "Turn on the scheduled run?\n\nEvery Sunday at 12:00, Martinet updates programs, "
                                "Windows, drivers and the NVIDIA driver, sets dead shortcuts aside and cleans up, "
                                "then lets you know with a notification. Everything can be changed later in "
                                "Schedule."},
    "msg.auto_admin": {"fr": "Il faut les droits administrateur pour créer la tâche : relancez Martinet en "
                             "administrateur, puis enregistrez la page Planification.",
                       "en": "Administrator rights are needed to create the task: restart Martinet as "
                             "administrator, then save the Schedule page."},
    "msg.rien_coche": {"fr": "Rien n'est coché.", "en": "Nothing is checked."},
    "msg.rien_selectionne": {"fr": "Sélectionnez d'abord une ligne.", "en": "Select a row first."},
    "msg.verifier_dabord": {"fr": "Lancez d'abord « Tout vérifier ».", "en": "Run “Check everything” first."},
    "msg.confirmer_tout": {"fr": "Mettre à jour {prog} programme(s) et installer {win} mise(s) à jour Windows, "
                                 "puis faire le ménage coché d'office ?\n\nLe pilote NVIDIA et les raccourcis morts "
                                 "suivent les choix de la page Planification ; les logiciels hors winget "
                                 "s'installent depuis leur page.",
                           "en": "Update {prog} program(s) and install {win} Windows update(s), then run the "
                                 "default clean-up?\n\nThe NVIDIA driver and dead shortcuts follow the choices of "
                                 "the Schedule page; programs outside winget are installed from their own page."},
    "msg.confirmer_installeur": {"fr": "Télécharger et lancer l'installeur officiel de {nom} {version} ?\n\n{adresse}",
                                 "en": "Download and run the official installer of {nom} {version}?\n\n{adresse}"},
    "msg.installeur_fini": {"fr": "Installeur de {nom} terminé (code {code}).",
                            "en": "{nom} installer finished (code {code})."},
    "msg.installeur_lance": {"fr": "L'installeur de {nom} est lancé : suivez-le à l'écran.",
                             "en": "The {nom} installer has started: follow it on screen."},
    "msg.erreur": {"fr": "Erreur : {detail}", "en": "Error: {detail}"},
    "msg.erreurs_etapes": {"fr": "Certaines vérifications ont échoué :\n{liste}",
                           "en": "Some checks failed:\n{liste}"},
    "msg.redemarrer": {"fr": "Redémarrer l'ordinateur dans une minute pour terminer les mises à jour ?",
                       "en": "Restart the computer in one minute to finish the updates?"},
    "msg.quitter_en_cours": {"fr": "Une opération est en cours. Quitter quand même ?",
                             "en": "An operation is in progress. Quit anyway?"},
    "msg.manuel_absent": {"fr": "Le manuel est introuvable.", "en": "The user guide cannot be found."},
    # ---- mise à jour de Martinet (kit)
    "maj.titre": {"fr": "Mise à jour de Martinet", "en": "Martinet update"},
    "maj.recherche": {"fr": "Recherche d'une mise à jour…", "en": "Checking for updates…"},
    "maj.a_jour": {"fr": "Martinet {version} est à jour.", "en": "Martinet {version} is up to date."},
    "maj.dispo": {"fr": "La version {nouvelle} est disponible (vous avez la {version}).",
                  "en": "Version {nouvelle} is available (you have {version})."},
    "maj.installer": {"fr": "Installer maintenant", "en": "Install now"},
    "maj.page": {"fr": "Ouvrir la page", "en": "Open the page"},
    "maj.plus_tard": {"fr": "Plus tard", "en": "Later"},
    "maj.telechargement": {"fr": "Téléchargement de la mise à jour…", "en": "Downloading the update…"},
    "maj.verrou": {"fr": "Un fichier de Martinet est en cours d'utilisation : fermez les autres fenêtres de "
                         "Martinet et recommencez.",
                   "en": "A Martinet file is in use: close the other Martinet windows and try again."},
    "maj.echec": {"fr": "La mise à jour a échoué : {erreur}", "en": "The update failed: {erreur}"},
    "maj.redemarre": {"fr": "Mise à jour installée : Martinet va redémarrer.",
                      "en": "Update installed: Martinet will restart."},
    "signal.titre": {"fr": "Signaler un problème", "en": "Report a problem"},
    "signal.invite": {"fr": "Décrivez ce qui s'est passé :", "en": "Describe what happened:"},
    "signal.exemple": {"fr": "Par exemple : j'ai cliqué sur « Tout mettre à jour » et Firefox est resté à "
                             "l'ancienne version.",
                       "en": "For example: I clicked “Update everything” and Firefox stayed on the old version."},
    "signal.note": {"fr": "Le message part avec la version de Martinet et du système, rien d'autre.",
                    "en": "The message is sent with the Martinet and system versions, nothing else."},
    "signal.envoyer": {"fr": "Envoyer", "en": "Send"},
    "signal.merci": {"fr": "Merci", "en": "Thank you"},
    "signal.parti": {"fr": "Merci, le signalement est parti.", "en": "Thank you, the report was sent."},
    "signal.local": {"fr": "Pas de réseau : le signalement a été enregistré ici :\n{chemin}",
                     "en": "No network: the report was saved here:\n{chemin}"},
}

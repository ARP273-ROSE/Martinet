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


def _linux() -> bool:
    force = os.environ.get("MARTINET_SYSTEME", "")
    if force in ("windows", "linux"):
        return force == "linux"
    return sys.platform.startswith("linux")


def tr(cle: str, **champs) -> str:
    """Texte dans la langue choisie ; sous Linux, la variante « clé.lx » quand elle existe."""
    textes = (_linux() and TEXTES.get(cle + ".lx")) or TEXTES.get(cle)
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
    "page.accueil.aide": {"fr": "« Tout vérifier » ne modifie rien. « Mettre à jour et nettoyer » fait tout ce "
                                "qui se fait sans vous ; la liste exacte est montrée avant de commencer.",
                          "en": "“Check everything” changes nothing. “Update and clean up” does everything that "
                                "can be done without you; the exact list is shown before starting."},
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
    "accueil.tout": {"fr": "Mettre à jour et nettoyer", "en": "Update and clean up"},
    "accueil.tout.bulle": {"fr": "Programmes winget, Windows Update, Defender, pilote NVIDIA, ménage coché et "
                                 "raccourcis morts mis de côté. La liste exacte est montrée avant de commencer.",
                           "en": "winget programs, Windows Update, Defender, NVIDIA driver, checked clean-up and "
                                 "dead shortcuts set aside. The exact list is shown before starting."},
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
    "win.pilote_maj_amd": {"fr": "Nouveau pilote recommandé (WHQL) : {nom} {version}. L'installeur d'AMD s'ouvrira, "
                                 "il faut le suivre.",
                           "en": "New recommended (WHQL) driver: {nom} {version}. AMD's installer will open, "
                                 "follow it."},
    "win.pilote_amd_inconnu": {"fr": "Dernier pilote recommandé (WHQL) : {version}. Version installée illisible "
                                     "(pilote livré par Windows Update, sans AMD Software ?).",
                               "en": "Latest recommended (WHQL) driver: {version}. Installed version unreadable "
                                     "(driver from Windows Update, without AMD Software?)."},
    "win.pilote_historique": {"fr": "Puce sur la branche de maintenance d'AMD (Vega, Polaris) : nouveaux pilotes "
                                    "rares, Windows Update suffit le plus souvent.",
                              "en": "Chip on AMD's maintenance branch (Vega, Polaris): new drivers are rare, "
                                    "Windows Update is usually enough."},
    "tout.pas_amd": {"fr": "le pilote AMD {version} (son installeur se lance depuis « Windows et pilotes »)",
                     "en": "the AMD driver {version} (its installer runs from “Windows and drivers”)"},
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
    "win.inclure_facultatives": {"fr": "Inclure les mises à jour facultatives (ici, avec « Mettre à jour et nettoyer » "
                                       "et en automatique)",
                                 "en": "Include optional updates (here, with “Update and clean up” and in "
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
    "menage.vidages_memoire": {"fr": "Vidages mémoire après plantage", "en": "Crash memory dumps"},
    "menage.vidages_memoire.aide": {"fr": "MEMORY.DMP, minidumps et vidages des programmes plantés.",
                                    "en": "MEMORY.DMP, minidumps and dumps of crashed programs."},
    "menage.journaux_windows": {"fr": "Journaux de Windows", "en": "Windows logs"},
    "menage.journaux_windows.aide": {"fr": "Journaux d'installation et de mise à jour de plus de 7 jours.",
                                     "en": "Setup and update logs older than 7 days."},
    "menage.restes_nvidia": {"fr": "Restes d'installation des pilotes", "en": "Driver setup leftovers"},
    "menage.restes_nvidia.aide": {"fr": "Installeurs décompressés dans C:\\NVIDIA et C:\\AMD, et téléchargements "
                                        "de l'application NVIDIA.",
                                  "en": "Installers unpacked in C:\\NVIDIA and C:\\AMD, and NVIDIA app downloads."},
    "menage.miniatures": {"fr": "Cache des miniatures", "en": "Thumbnail cache"},
    "menage.miniatures.aide": {"fr": "Recréé à l'ouverture des dossiers d'images (plus lents la première fois).",
                               "en": "Rebuilt when picture folders are opened (slower the first time)."},
    "menage.caches_navigateurs": {"fr": "Caches des navigateurs", "en": "Browser caches"},
    "menage.caches_navigateurs.aide": {"fr": "Chrome, Edge, Brave, Firefox ; ni historique, ni cookies, ni mots de "
                                             "passe. Navigateurs fermés seulement.",
                                       "en": "Chrome, Edge, Brave, Firefox; no history, cookies or passwords. "
                                             "Only when the browsers are closed."},
    "menage.caches_shaders": {"fr": "Caches de shaders (DirectX, NVIDIA)", "en": "Shader caches (DirectX, NVIDIA)"},
    "menage.caches_shaders.aide": {"fr": "Recompilés au lancement des jeux : saccades le temps qu'ils se refassent.",
                                   "en": "Recompiled when games start: stutter while they rebuild."},
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
    "etape.hors": {"fr": "Hors winget", "en": "Outside winget"},
    "journal.source": {"fr": "Dernière version de {nom}…", "en": "Latest version of {nom}…"},
    "journal.echec_etape": {"fr": "Échec de l'étape « {etape} » : {detail}", "en": "Step “{etape}” failed: {detail}"},
    "journal.maj_paquet": {"fr": "{nom} : {avant} → {apres}", "en": "{nom}: {avant} → {apres}"},
    "journal.menage": {"fr": "Ménage : {element}", "en": "Clean-up: {element}"},
    "journal.lancement": {"fr": "Lancement de {nom}", "en": "Starting {nom}"},
    # ---- résumés
    "resume.programmes": {"fr": "Programmes : {ok} sur {n} mis à jour.", "en": "Programs: {ok} of {n} updated."},
    "resume.echecs": {"fr": "Échecs : {liste}", "en": "Failures: {liste}"},
    "resume.etape_ko": {"fr": "{etape} : échec ({detail}), la suite a continué.", "en": "{etape}: failed ({detail}), the rest went on."},
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
    "msg.confirmer_tout": {"fr": "Martinet va faire, dans l'ordre :\n\n{liste}\n\nOn y va ?",
                           "en": "Martinet will do, in this order:\n\n{liste}\n\nGo ahead?"},
    "tout.programmes": {"fr": "• mettre à jour {n} programme(s) winget", "en": "• update {n} winget program(s)"},
    "tout.windows": {"fr": "• installer {n} mise(s) à jour Windows", "en": "• install {n} Windows update(s)"},
    "tout.windows_fac": {"fr": "• installer {n} mise(s) à jour Windows, dont {f} facultative(s)",
                         "en": "• install {n} Windows update(s), {f} of them optional"},
    "tout.defender": {"fr": "• mettre à jour les signatures de Microsoft Defender",
                      "en": "• update the Microsoft Defender signatures"},
    "tout.menage": {"fr": "• ménage ({taille}) : {liste}", "en": "• clean-up ({taille}): {liste}"},
    "tout.pilote": {"fr": "• installer le pilote NVIDIA {version} (écran qui clignote)",
                    "en": "• install the NVIDIA driver {version} (screen flickers)"},
    "tout.raccourcis": {"fr": "• mettre de côté {n} raccourci(s) mort(s) (restaurables)",
                        "en": "• set aside {n} dead shortcut(s) (can be restored)"},
    "tout.pas_fait": {"fr": "Pas fait ici : {liste}.", "en": "Not done here: {liste}."},
    "tout.pas_hors": {"fr": "{n} logiciel(s) hors winget (depuis leur page)",
                      "en": "{n} program(s) outside winget (from their page)"},
    "tout.pas_pilote": {"fr": "le pilote NVIDIA (désactivé dans Planification)",
                        "en": "the NVIDIA driver (turned off in Schedule)"},
    "tout.pas_raccourcis": {"fr": "les raccourcis morts (désactivé dans Planification)",
                            "en": "dead shortcuts (turned off in Schedule)"},
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
    "signal.exemple": {"fr": "Par exemple : j'ai cliqué sur « Mettre à jour et nettoyer » et Firefox est resté à "
                             "l'ancienne version.",
                       "en": "For example: I clicked “Update and clean up” and Firefox stayed on the old version."},
    "signal.note": {"fr": "Le message part avec la version de Martinet et du système, rien d'autre.",
                    "en": "The message is sent with the Martinet and system versions, nothing else."},
    "signal.envoyer": {"fr": "Envoyer", "en": "Send"},
    "signal.merci": {"fr": "Merci", "en": "Thank you"},
    "signal.parti": {"fr": "Merci, le signalement est parti.", "en": "Thank you, the report was sent."},
    "signal.local": {"fr": "Pas de réseau : le signalement a été enregistré ici :\n{chemin}",
                     "en": "No network: the report was saved here:\n{chemin}"},
    # ---- Linux (Manjaro / Arch) ; « clé.lx » remplace « clé » sous Linux
    "cli.description.lx": {"fr": "Tenir Manjaro à jour : paquets, AUR, Flatpak, micrologiciels, lanceurs, ménage.",
                          "en": "Keep Manjaro up to date: packages, AUR, Flatpak, firmware, launchers, clean-up."},
    "action.rechercher": {"fr": "Rechercher",
                         "en": "Search"},
    "col.appareil": {"fr": "Appareil",
                    "en": "Device"},
    "col.fichier": {"fr": "Fichier",
                   "en": "File"},
    "col.paquet": {"fr": "Paquet",
                  "en": "Package"},
    "col.provenance": {"fr": "Provenance",
                      "en": "Source"},
    "page.paquets": {"fr": "Paquets",
                    "en": "Packages"},
    "page.paquets.aide": {"fr": "Dépôts Manjaro, AUR et Flatpak. Tout le système se met à jour d'un coup : sous Manjaro, une mise à jour partielle peut casser le système.",
                         "en": "Manjaro repositories, AUR and Flatpak. The whole system is updated at once: on Manjaro, a partial upgrade can break the system."},
    "page.systeme": {"fr": "Système",
                    "en": "System"},
    "page.systeme.aide": {"fr": "Ce qui demande votre décision : redémarrage, noyau, micrologiciels, fichiers .pacnew, paquets orphelins.",
                         "en": "What needs your decision: restart, kernel, firmware, .pacnew files, orphan packages."},
    "page.raccourcis.aide.lx": {"fr": "Lanceurs de votre menu, de votre Bureau et du démarrage automatique dont le programme a disparu. Ils sont mis de côté, jamais effacés.",
                               "en": "Launchers in your menu, on your Desktop and in autostart whose program has disappeared. They are set aside, never deleted."},
    "page.menage.aide.lx": {"fr": "Seulement ce que le système sait recréer. Le cache des paquets garde toujours les deux dernières versions, de quoi revenir en arrière.",
                           "en": "Only what the system can recreate. The package cache always keeps the last two versions, so you can roll back."},
    "page.planif.aide.lx": {"fr": "Martinet peut passer tout seul, chaque semaine ou chaque jour (minuteur systemd), et vous prévenir par une notification.",
                           "en": "Martinet can run on its own, weekly or daily (systemd timer), and let you know with a notification."},
    "accueil.tout.bulle.lx": {"fr": "Paquets (dépôts, AUR, Flatpak), ménage coché et lanceurs morts mis de côté. La liste exacte est montrée avant de commencer.",
                             "en": "Packages (repositories, AUR, Flatpak), checked clean-up and dead launchers set aside. The exact list is shown before starting."},
    "lieu.menu": {"fr": "Menu des applications",
                 "en": "Application menu"},
    "lieu.autostart": {"fr": "Démarrage automatique",
                      "en": "Autostart"},
    "col.raccourci.lx": {"fr": "Lanceur",
                        "en": "Launcher"},
    "col.cible.lx": {"fr": "Programme",
                    "en": "Program"},
    "racc.morts.lx": {"fr": "Lanceurs morts",
                     "en": "Dead launchers"},
    "page.raccourcis.lx": {"fr": "Lanceurs morts",
                          "en": "Dead launchers"},
    "planif.programmes.lx": {"fr": "Mettre à jour les paquets (dépôts, AUR, Flatpak)",
                            "en": "Update packages (repositories, AUR, Flatpak)"},
    "planif.raccourcis.lx": {"fr": "Mettre de côté les lanceurs morts (récupérables dans Lanceurs morts)",
                            "en": "Set dead launchers aside (recoverable from Dead launchers)"},
    "planif.signale.lx": {"fr": "Micrologiciels, fichiers .pacnew et paquets orphelins sont seulement signalés : ils demandent votre décision. Sans la case ci-dessous, le passage demande le mot de passe s'il vous trouve devant l'écran ; sinon il saute les paquets et le signale.",
                         "en": "Firmware, .pacnew files and orphan packages are only reported: they need your decision. Without the box below, the run asks for the password if you are at the screen; otherwise it skips packages and reports it."},
    "lx.sans_mot_de_passe": {"fr": "Mettre à jour sans demander le mot de passe (règle polkit limitée à pamac, à pacman lancé par yay, et à votre compte)",
                            "en": "Update without asking for the password (polkit rule limited to pamac, pacman run by yay, and your account)"},
    "lx.sans_mot_de_passe.bulle": {"fr": "Pose /etc/polkit-1/rules.d/49-martinet-pamac.rules : seuls pamac et pacman (celui que yay lance par pkexec), lancés par vous, peuvent installer ou retirer des paquets sans mot de passe. Décocher retire la règle.",
                                  "en": "Installs /etc/polkit-1/rules.d/49-martinet-pamac.rules: only pamac and pacman (the one yay runs through pkexec), run by you, may install or remove packages without a password. Unchecking removes the rule."},
    "lx.regle_echec": {"fr": "La règle polkit n'a pas pu être modifiée : {detail}",
                      "en": "The polkit rule could not be changed: {detail}"},
    "lx.gestionnaire": {"fr": "Gestionnaire utilisé : {outil}.",
                       "en": "Package manager used: {outil}."},
    "lx.tout_maj": {"fr": "Mettre à jour tout le système",
                   "en": "Update the whole system"},
    "lx.tache_maj": {"fr": "Mise à jour du système",
                    "en": "System update"},
    "lx.confirmer_maj": {"fr": "Mettre à jour les {n} paquet(s) ? Le mot de passe vous sera demandé (polkit).",
                        "en": "Update the {n} package(s)? You will be asked for your password (polkit)."},
    "lx.resume_paquets": {"fr": "{n} mise(s) à jour : {depots} des dépôts, {aur} de l'AUR, {flatpak} Flatpak.",
                         "en": "{n} update(s): {depots} from the repositories, {aur} from AUR, {flatpak} Flatpak."},
    "lx.origine.depots": {"fr": "dépôts",
                         "en": "repositories"},
    "lx.origine.aur": {"fr": "AUR",
                      "en": "AUR"},
    "lx.origine.flatpak": {"fr": "Flatpak",
                          "en": "Flatpak"},
    "lx.etape.programmes": {"fr": "Paquets",
                           "en": "Packages"},
    "lx.etape.windows": {"fr": "Système",
                        "en": "System"},
    "lx.etape.raccourcis": {"fr": "Lanceurs",
                           "en": "Launchers"},
    "lx.etape.menage": {"fr": "Ménage",
                       "en": "Clean-up"},
    "etape.paquets": {"fr": "Paquets",
                     "en": "Packages"},
    "etape.programmes.lx": {"fr": "Paquets",
                           "en": "Packages"},
    "etape.windows.lx": {"fr": "Système",
                        "en": "System"},
    "etape.raccourcis.lx": {"fr": "Lanceurs",
                           "en": "Launchers"},
    "lx.pas_de_pacman": {"fr": "pacman introuvable : ce n'est pas un système Arch ou Manjaro.",
                        "en": "pacman not found: this is not an Arch or Manjaro system."},
    "lx.refuse": {"fr": "mot de passe refusé ou demande fermée",
                 "en": "password refused or request closed"},
    "lx.utilisateur_inattendu": {"fr": "nom d'utilisateur inattendu",
                                "en": "unexpected user name"},
    "lx.resume.paquets": {"fr": "Paquets : {n} mise(s) à jour installée(s).",
                         "en": "Packages: {n} update(s) installed."},
    "lx.resume.paquets_ko": {"fr": "Paquets : échec ({detail}).",
                            "en": "Packages: failed ({detail})."},
    "lx.resume.rien": {"fr": "Paquets : rien à mettre à jour.",
                      "en": "Packages: nothing to update."},
    "lx.resume.micrologiciels": {"fr": "{n} micrologiciel(s) à mettre à jour (page Système).",
                                "en": "{n} firmware update(s) waiting (System page)."},
    "lx.resume.pacnew": {"fr": "{n} fichier(s) .pacnew à examiner (page Système).",
                        "en": "{n} .pacnew file(s) to review (System page)."},
    "lx.resume.orphelins": {"fr": "{n} paquet(s) orphelin(s) (page Système).",
                           "en": "{n} orphan package(s) (System page)."},
    "lx.resume.noyau_fin": {"fr": "Le noyau {noyau} n'est plus suivi : installez-en un plus récent.",
                           "en": "Kernel {noyau} is no longer maintained: install a newer one."},
    "lx.tout.paquets": {"fr": "• mettre à jour {n} paquet(s) : {depots} des dépôts, {aur} de l'AUR, {flatpak} Flatpak",
                       "en": "• update {n} package(s): {depots} from the repositories, {aur} from AUR, {flatpak} Flatpak"},
    "lx.tout.rien": {"fr": "• rien à mettre à jour",
                    "en": "• nothing to update"},
    "lx.tout.mot_de_passe": {"fr": "Le mot de passe sera demandé une ou deux fois (polkit), sauf si la règle « sans mot de passe » est posée.",
                            "en": "The password will be asked once or twice (polkit), unless the “no password” rule is installed."},
    "lx.pas.micrologiciels": {"fr": "{n} micrologiciel(s) (page Système)",
                             "en": "{n} firmware update(s) (System page)"},
    "lx.pas.orphelins": {"fr": "{n} paquet(s) orphelin(s) (page Système)",
                        "en": "{n} orphan package(s) (System page)"},
    "lx.pas.pacnew": {"fr": "{n} fichier(s) .pacnew (page Système)",
                     "en": "{n} .pacnew file(s) (System page)"},
    "lx.accueil.redemarrer": {"fr": "redémarrage nécessaire",
                             "en": "restart needed"},
    "lx.accueil.noyau_fin": {"fr": "noyau plus suivi",
                            "en": "kernel no longer maintained"},
    "lx.accueil.micrologiciels": {"fr": "{n} micrologiciel(s)",
                                 "en": "{n} firmware"},
    "lx.accueil.pacnew": {"fr": "{n} .pacnew",
                         "en": "{n} .pacnew"},
    "lx.accueil.orphelins": {"fr": "{n} orphelin(s)",
                            "en": "{n} orphan(s)"},
    "lx.accueil.rien": {"fr": "Rien à signaler",
                       "en": "Nothing to report"},
    "lx.noyau": {"fr": "Noyau et redémarrage",
                "en": "Kernel and restart"},
    "lx.noyau_en_marche": {"fr": "Noyau en marche : {noyau}",
                          "en": "Running kernel: {noyau}"},
    "lx.redemarrer_oui": {"fr": "<b>Redémarrage nécessaire</b> : le noyau en marche a été remplacé par une mise à jour.",
                         "en": "<b>Restart needed</b>: the running kernel was replaced by an update."},
    "lx.redemarrer_non": {"fr": "Pas de redémarrage nécessaire.",
                         "en": "No restart needed."},
    "lx.noyau_fin": {"fr": "<b>{noyau}</b> n'est plus dans les dépôts : il ne reçoit plus de correctifs. Installez un noyau suivi (Paramètres Manjaro › Noyau), puis retirez celui-ci.",
                    "en": "<b>{noyau}</b> is no longer in the repositories: it gets no more fixes. Install a maintained kernel (Manjaro Settings › Kernel), then remove this one."},
    "lx.redemarrer": {"fr": "Redémarrer",
                     "en": "Restart"},
    "lx.micrologiciels": {"fr": "Micrologiciels (fwupd)",
                         "en": "Firmware (fwupd)"},
    "lx.fw_installer": {"fr": "Mettre à jour les micrologiciels",
                       "en": "Update firmware"},
    "lx.fw_absent": {"fr": "fwupd n'est pas installé : sudo pacman -S fwupd.",
                    "en": "fwupd is not installed: sudo pacman -S fwupd."},
    "lx.fw_n": {"fr": "{n} mise(s) à jour de micrologiciel (carte mère, disque, souris…).",
               "en": "{n} firmware update(s) (motherboard, drive, mouse…)."},
    "lx.fw_rien": {"fr": "Micrologiciels à jour.",
                  "en": "Firmware up to date."},
    "lx.fw_confirmer": {"fr": "Mettre à jour les micrologiciels ? Ne coupez pas le courant pendant l'opération ; un redémarrage peut être demandé.",
                       "en": "Update the firmware? Do not cut the power during the operation; a restart may be requested."},
    "lx.fw_ok": {"fr": "Micrologiciels mis à jour.",
                "en": "Firmware updated."},
    "lx.fw_ko": {"fr": "Micrologiciels : échec ({detail}).",
                "en": "Firmware: failed ({detail})."},
    "lx.pacnew": {"fr": "Fichiers .pacnew et .pacsave",
                 "en": ".pacnew and .pacsave files"},
    "lx.pacnew.aide": {"fr": "Une nouvelle configuration fournie par un paquet attend votre décision. Comparez-la avec « sudo pacdiff » (ou meld), puis supprimez le .pacnew.",
                      "en": "A new configuration shipped by a package awaits your decision. Compare it with “sudo pacdiff” (or meld), then delete the .pacnew."},
    "lx.orphelins": {"fr": "Paquets orphelins",
                    "en": "Orphan packages"},
    "lx.orphelins_n": {"fr": "{n} paquet(s) installé(s) comme dépendance et dont plus rien n'a besoin. Vérifiez avant de retirer : un outil installé à la main peut s'y trouver.",
                      "en": "{n} package(s) installed as a dependency that nothing needs any more. Check before removing: a tool you installed yourself may be among them."},
    "lx.orphelins_rien": {"fr": "Aucun paquet orphelin.",
                         "en": "No orphan packages."},
    "lx.orphelins_retirer": {"fr": "Retirer la sélection",
                            "en": "Remove selected"},
    "lx.orphelins_confirmer": {"fr": "Retirer ces paquets ?\n\n{liste}",
                              "en": "Remove these packages?\n\n{liste}"},
    "lx.orphelins_ok": {"fr": "{n} paquet(s) orphelin(s) retiré(s).",
                       "en": "{n} orphan package(s) removed."},
    "lx.orphelins_ko": {"fr": "Orphelins : échec ({detail}).",
                       "en": "Orphans: failed ({detail})."},
    "lx.hors_depots": {"fr": "Paquets hors dépôts",
                      "en": "Packages outside the repositories"},
    "lx.hors_depots_n": {"fr": "{n} paquet(s) de l'AUR ou retiré(s) des dépôts : {liste}",
                        "en": "{n} package(s) from AUR or dropped from the repositories: {liste}"},
    "lx.hors_depots_rien": {"fr": "Tous les paquets viennent des dépôts.",
                           "en": "All packages come from the repositories."},
    "menage.cache_paquets": {"fr": "Anciennes versions des paquets",
                            "en": "Old package versions"},
    "menage.cache_paquets.aide": {"fr": "Cache de pacman : les deux dernières versions de chaque paquet sont gardées.",
                                 "en": "pacman cache: the last two versions of each package are kept."},
    "menage.cache_desinstalles": {"fr": "Paquets désinstallés en cache",
                                 "en": "Cached uninstalled packages"},
    "menage.cache_desinstalles.aide": {"fr": "Paquets du cache qui ne sont plus installés.",
                                      "en": "Cached packages that are no longer installed."},
    "menage.fichiers_construction": {"fr": "Fichiers de construction de l'AUR",
                                    "en": "AUR build files"},
    "menage.fichiers_construction.aide": {"fr": "Sources téléchargées par yay ou pamac pour construire les paquets AUR.",
                                         "en": "Sources downloaded by yay or pamac to build AUR packages."},
    "menage.flatpak_inutilises": {"fr": "Runtimes Flatpak inutilisés",
                                 "en": "Unused Flatpak runtimes"},
    "menage.flatpak_inutilises.aide": {"fr": "Bibliothèques Flatpak dont plus aucune application ne se sert.",
                                      "en": "Flatpak libraries no application uses any more."},
    "menage.journaux_systeme": {"fr": "Journaux du système (plus de 4 semaines)",
                               "en": "System logs (older than 4 weeks)"},
    "menage.journaux_systeme.aide": {"fr": "journald limite déjà leur taille ; utile seulement s'ils ont beaucoup grossi.",
                                    "en": "journald already caps their size; useful only if they grew a lot."},
    "menage.vidages_systeme": {"fr": "Vidages mémoire après plantage",
                              "en": "Crash memory dumps"},
    "menage.vidages_systeme.aide": {"fr": "Fichiers de systemd-coredump (effacés d'office après quelques jours).",
                                   "en": "systemd-coredump files (deleted automatically after a few days)."},
    "menage.miniatures.aide.lx": {"fr": "~/.cache/thumbnails : recréé à l'ouverture des dossiers d'images.",
                                 "en": "~/.cache/thumbnails: rebuilt when picture folders are opened."},
    "menage.corbeille.aide.lx": {"fr": "Jamais cochée d'office.",
                                "en": "Never checked by default."},
    "accueil.n_morts.lx": {"fr": "{n} lanceur(s) mort(s)",
                          "en": "{n} dead launcher(s)"},
    "accueil.aucun_mort.lx": {"fr": "Aucun lanceur mort",
                             "en": "No dead launchers"},
    "racc.de_cote.lx": {"fr": "Lanceurs mis de côté",
                       "en": "Launchers set aside"},
    "racc.resume.lx": {"fr": "{n} lanceur(s) dont le programme a disparu. Les programmes sur un disque amovible absent ne sont pas vérifiés.",
                      "en": "{n} launcher(s) whose program has disappeared. Programs on a missing removable drive are not checked."},
    "racc.deplaces.lx": {"fr": "{n} lanceur(s) mis de côté.",
                        "en": "{n} launcher(s) set aside."},
    "racc.restaures.lx": {"fr": "{n} lanceur(s) restauré(s).",
                         "en": "{n} launcher(s) restored."},
    "resume.raccourcis.lx": {"fr": "{n} lanceur(s) mort(s) à examiner.",
                            "en": "{n} dead launcher(s) to review."},
    "tout.raccourcis.lx": {"fr": "• mettre de côté {n} lanceur(s) mort(s) (restaurables)",
                          "en": "• set aside {n} dead launcher(s) (can be restored)"},
    "tout.pas_raccourcis.lx": {"fr": "les lanceurs morts (désactivé dans Planification)",
                              "en": "dead launchers (turned off in Schedule)"},
    # ---- Windows 10
    "accueil.w10": {"fr": "Windows 10 : plus de correctifs de sécurité",
                   "en": "Windows 10: no more security fixes"},
    "win.w10": {"fr": "<b>Windows 10</b> : Microsoft n'en publie plus les correctifs de sécurité (fin du support le 14 octobre 2025, de l'extension gratuite ESU le 13 octobre 2026). Martinet continue de mettre à jour ce qui l'est encore : programmes, pilotes, pilote graphique et signatures de Microsoft Defender.",
               "en": "<b>Windows 10</b>: Microsoft no longer publishes its security fixes (end of support on 14 October 2025, end of the free ESU extension on 13 October 2026). Martinet keeps updating what still is: programs, drivers, graphics driver and Microsoft Defender signatures."},
    "prog.ouvrir_store": {"fr": "Ouvrir le Microsoft Store (installer winget)",
                         "en": "Open the Microsoft Store (install winget)"},
    # ---- Linux : applications GitHub, gestionnaire
    "col.application": {"fr": "Application",
                       "en": "Application"},
    "col.depot": {"fr": "Dépôt GitHub",
                 "en": "GitHub repository"},
    "journal.telechargement": {"fr": "Téléchargement de {nom}…",
                              "en": "Downloading {nom}…"},
    "lx.applis": {"fr": "Vos applications (GitHub)",
                 "en": "Your applications (GitHub)"},
    "lx.applis_aucune": {"fr": "Aucune application installée par son installer.sh dans ~/.local/share.",
                        "en": "No application installed with its installer.sh in ~/.local/share."},
    "lx.applis_n": {"fr": "{n} mise(s) à jour sur {total} application(s) suivie(s). Une application ouverte est laissée pour plus tard.",
                   "en": "{n} update(s) among {total} tracked application(s). An open application is left for later."},
    "lx.applis_a_jour": {"fr": "{total} application(s) suivie(s), toutes à jour.",
                        "en": "{total} tracked application(s), all up to date."},
    "lx.applis.pas_archive": {"fr": "pas d'archive Linux dans la dernière version",
                             "en": "no Linux archive in the latest release"},
    "lx.applis.ouverte": {"fr": "{nom} est ouvert : fermez-le, ce sera fait au prochain passage",
                         "en": "{nom} is open: close it, it will be done on the next run"},
    "lx.applis.empreinte": {"fr": "empreinte SHA-256 différente de celle publiée : rien n'a été installé",
                           "en": "SHA-256 checksum differs from the published one: nothing was installed"},
    "lx.applis.pas_installeur": {"fr": "installer.sh absent de l'archive",
                                "en": "installer.sh missing from the archive"},
    "lx.resume.applis": {"fr": "Applications GitHub : {ok} sur {n} mise(s) à jour.",
                        "en": "GitHub applications: {ok} of {n} updated."},
    "lx.tout.applis": {"fr": "• mettre à jour {n} application(s) GitHub : {liste}",
                      "en": "• update {n} GitHub application(s): {liste}"},
    "lx.gestionnaire_choix": {"fr": "Gestionnaire :",
                             "en": "Package manager:"},
    "lx.gestionnaire.auto": {"fr": "automatique (yay s'il est installé, sinon pamac)",
                            "en": "automatic (yay if installed, else pamac)"},
    "lx.gestionnaire.yay": {"fr": "yay",
                           "en": "yay"},
    "lx.gestionnaire.pamac": {"fr": "pamac",
                             "en": "pamac"},
}

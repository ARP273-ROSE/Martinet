# Journal des versions / Changelog

### 0.5.2

- Un installeur qui demande à Windows de fermer Martinet en plein passage (Restart Manager d'un MSI) n'arrête
  plus tout : Martinet refuse poliment et le passage continue ; l'installeur remet au prochain redémarrage
  ce qui était vraiment utilisé. Fermeture propre même si une tâche tourne encore (plus de plantage de Qt).
  Le journal du passage est écrit au fil de l'eau : un passage coupé net apparaît dans l'historique au
  lancement suivant, avec sa dernière ligne.
- An installer asking Windows to close Martinet mid-run (an MSI's Restart Manager) no longer stops
  everything: Martinet declines and the run goes on. Clean exit even with a task still running (no more Qt
  crash). The run log is written as it goes: a run cut short shows up in the history at the next start.

### 0.5.1

- Windows 10 : le bandeau tient compte de la prolongation de l'ESU grand public jusqu'au 12 octobre 2027
  (gratuite en Europe) ; il ne parle de fin des correctifs qu'après cette date.
- Windows 10: the banner accounts for the consumer ESU extension until 12 October 2027 (free in Europe);
  it only mentions the end of fixes after that date.

### 0.5.0

- **Manjaro / Arch** : mode Linux complet. Paquets des dépôts, de l'AUR et Flatpak (yay s'il est installé,
  sinon pamac, au choix ; yay sans terminal, mot de passe par pkexec ; tout le système d'un coup, jamais de
  mise à jour partielle) ; vos applications publiées sur GitHub (installées par leur installer.sh)
  retrouvées seules et mises à jour par leur archive officielle, empreinte SHA-256 vérifiée ; page Système : redémarrage
  nécessaire, noyau plus suivi, micrologiciels (fwupd), fichiers .pacnew, paquets orphelins retirés un par
  un ; lanceurs .desktop morts mis de côté ; ménage (cache des paquets en gardant 2 versions, fichiers de
  construction AUR, runtimes Flatpak inutilisés, miniatures, journaux, vidages, corbeille) en une seule
  demande de mot de passe ; passage automatique par minuteur systemd ; règle polkit facultative, limitée
  à pamac, à pacman (yay) et au compte, pour mettre à jour sans mot de passe. Paquet Linux x86_64 (`installer.sh`, sans sudo).
- **Windows 10** : bandeau de fin de support, bouton vers le Microsoft Store si winget manque, PowerShell
  5.1 forcé en TLS 1.2 pour installer le module WinGet.
- **Manjaro / Arch**: full Linux mode. Repository, AUR and Flatpak packages (yay when installed, else pamac,
  your choice; yay without a terminal, password through pkexec; whole system at once, never a partial
  upgrade); your applications published on GitHub (installed with their installer.sh) found on their own
  and updated from their official archive, SHA-256 checked; System page: restart needed, unmaintained kernel,
  firmware (fwupd), .pacnew files, orphan packages removed one by one; dead .desktop launchers set aside;
  clean-up (package cache keeping 2 versions, AUR build files, unused Flatpak runtimes, thumbnails, logs,
  dumps, trash) with a single password request; scheduled run through a systemd timer; optional polkit
  rule, limited to pamac, pacman (yay) and the account, for password-less updates. Linux x86_64 package (`installer.sh`,
  no sudo).
- **Windows 10**: end-of-support banner, button to the Microsoft Store when winget is missing, PowerShell
  5.1 forced to TLS 1.2 to install the WinGet module.

### 0.4.0

- Pilotes AMD : cartes Radeon et graphismes intégrés des Ryzen. Martinet lit la page AMD de la carte (ou du
  processeur), retient le pilote recommandé (WHQL, jamais l'optionnel), le compare à la version d'AMD
  Software installée et lance l'installeur officiel. Puces Vega et Polaris signalées comme branche de
  maintenance. Le passage automatique signale le pilote AMD sans l'installer.
- Téléchargements depuis drivers.amd.com acceptés (page d'origine fournie) ; une page web reçue à la place
  d'un installeur est refusée.
- AMD drivers: Radeon cards and Ryzen integrated graphics. Martinet reads the card's (or processor's) AMD
  page, keeps the recommended driver (WHQL, never the optional one), compares it with the installed AMD
  Software version and runs the official installer. Vega and Polaris chips flagged as the maintenance
  branch. The automatic run reports the AMD driver without installing it.
- Downloads from drivers.amd.com accepted (referrer sent); a web page received instead of an installer is
  refused.

### 0.3.1

- « Tout mettre à jour » devient « Mettre à jour et nettoyer » : le bouton fait aussi le ménage, le pilote
  et les raccourcis. Avant de commencer, Martinet montre la liste exacte (avec les nombres) et ce qu'il
  ne fera pas.
- “Update everything” becomes “Update and clean up”: the button also cleans up, installs the driver and
  sets shortcuts aside. Before starting, Martinet shows the exact list (with the numbers) and what it
  will not do.

### 0.3.0

- Vraie barre de progression, sur toute la largeur, avec le pourcentage ; l'étape en cours et la dernière
  ligne du journal s'affichent à côté de la tâche, console cachée ou non.
- La console suit toujours la dernière ligne.
- Ménage : vidages mémoire après plantage, journaux de Windows, restes d'installation des pilotes
  (C:\NVIDIA, C:\AMD) ; proposés sans être cochés : cache des miniatures, caches des navigateurs
  (navigateurs fermés seulement), caches de shaders.
- Real progress bar, full width, with the percentage; the current step and the last log line are shown
  next to the task, console hidden or not.
- The console always follows the last line.
- Clean-up: crash memory dumps, Windows logs, driver setup leftovers (C:\NVIDIA, C:\AMD); offered but
  unchecked: thumbnail cache, browser caches (browsers closed only), shader caches.

### 0.2.2

- Windows Update : l'installation réussie était lue comme un échec (« code 0 ») à cause des fins de ligne
  CRLF de PowerShell ; corrigé.
- Une étape en échec (Windows Update, Defender, ménage, raccourcis) n'arrête plus les suivantes (pilote…).
- Vérification sans droits administrateur : un dossier système illisible n'est plus une erreur.
- Erreurs PowerShell affichées en texte clair au lieu du format CLIXML.
- Windows Update: a successful install was read as a failure ("code 0") because of PowerShell CRLF line
  endings; fixed.
- A failed step (Windows Update, Defender, clean-up, shortcuts) no longer stops the next ones (driver…).
- Check without administrator rights: an unreadable system folder is no longer an error.
- PowerShell errors shown as plain text instead of CLIXML.

### 0.2.1

- Pilote NVIDIA : seulement le pilote Game Ready (jamais Studio ni bêta), nom du pilote affiché ;
  installation express avec les réglages par défaut.
- NVIDIA driver: Game Ready only (never Studio or beta), driver name shown; express install with default
  settings.

### 0.2.0

- Lecture du tableau winget corrigée : un identifiant peut contenir des espaces (jeux Steam), un fichier
  peut commencer par une marque d'ordre des octets. Relevé sur un vrai poste : 374 logiciels lus.
- Plus de faux rapprochements (« PHD2 Log Viewer », bases d'étoiles d'ASTAP) ; une version installée
  inconnue est lue dans le nom du logiciel, sinon affichée « inconnue » au lieu de « à jour ».
- Logiciels qui se mettent à jour tout seuls (navigateurs, Microsoft 365, Adobe, NVIDIA App…) reconnus ;
  jeux Steam, pilotes déjà livrés par Windows et bibliothèques d'exécution écartés de la liste.
- GraXpert ajouté au catalogue ; bouton « Importer… » pour charger un fichier de sources.
- winget table reading fixed (identifiers with spaces, byte order mark); no more false matches; unknown
  installed versions read from the program name; self-updating programs recognised; Steam games, Windows
  drivers and runtimes left out; GraXpert added; “Import…” button for source files.

### 0.1.0

- Première version : programmes (winget), logiciels hors winget avec catalogue de sources, Windows Update
  et pilotes, pilote NVIDIA, raccourcis morts, ménage, passage automatique planifié, historique.
- First release: programs (winget), programs outside winget with a source catalogue, Windows Update and
  drivers, NVIDIA driver, dead shortcuts, clean-up, scheduled unattended run, history.

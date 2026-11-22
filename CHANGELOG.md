# Journal des versions / Changelog

### 0.6.10

- Pilote AMD : la carte graphique est trouvée même sans droits administrateur (le registre des pilotes
  est alors illisible ; Martinet passe par WMI), et la version d'Adrenalin est lue dans « AMD Software »
  de la liste des programmes quand la clé du pilote ne la donne pas. Vérifié sur une Radeon 780M
  (Ryzen 9 7940HS) : 26.11.2 installé, 26.11.2 recommandé.
- AMD driver: the graphics card is found even without administrator rights (the driver registry is
  then unreadable; Martinet uses WMI), and the Adrenalin version is read from “AMD Software” in the
  programs list when the driver key does not give it. Checked on a Radeon 780M (Ryzen 9 7940HS).

### 0.6.9

- Boutons des boîtes de dialogue dans la langue de Martinet (« Oui / Non » au lieu de « Yes / No ») :
  la traduction de Qt est chargée au démarrage et suit le changement de langue.
- Textes restés en français dans l'interface anglaise : messages de la console (recherche Windows Update,
  lecture winget, lanceurs et raccourcis lus, cache laissé en place), erreurs des sources (NVIDIA, AMD,
  pages des éditeurs), « programme introuvable », « délai dépassé », archive invalide.
- Dialog buttons in Martinet's language (“Oui / Non” instead of “Yes / No” in French): Qt's translation is
  loaded at start-up and follows the language switch.
- Texts left in French in the English interface: console messages (Windows Update search, winget reading,
  launchers and shortcuts read, cache left in place), source errors (NVIDIA, AMD, vendor pages), “program
  not found”, “timed out”, invalid archive.

### 0.6.8

- Linux : une application installée deux fois (paquet du kit et AppImage) n'est plus mise à jour en double.
  Seul le paquet est suivi, et Martinet signale que l'AppImage peut être supprimée.
- Linux : une AppImage supprimée est oubliée ; un paquet AUR mis à l'écart puis installé autrement (à la
  main, ou corrigé) sort de la liste des écartés.
- Linux: an application installed twice (kit package and AppImage) is no longer updated twice. Only the
  package is followed, and Martinet says the AppImage can be deleted.
- Linux: a deleted AppImage is forgotten; a skipped AUR package that gets installed another way (by hand,
  or fixed) leaves the skipped list.

### 0.6.7

- Linux : l'état de la règle « mises à jour sans mot de passe » est lu dans un témoin public
  (/etc/martinet/), déposé et retiré avec elle. polkit refuse en effet de répondre à un utilisateur
  ordinaire, si bien que la case de la page Planification restait décochée en 0.6.6. Une règle posée par une
  version antérieure se reprend en recochant la case.
- Linux: the state of the “updates without password” rule is read from a public marker (/etc/martinet/),
  placed and removed along with it. polkit refuses to answer an ordinary user, so the Schedule page box
  stayed unticked in 0.6.6. A rule set by an earlier version is picked up by ticking the box again.

### 0.6.6

- Linux : la fenêtre ne démarrait pas sur Manjaro (« Permission non accordée » sur
  /etc/polkit-1/rules.d, dossier réservé à root et polkitd). Martinet demande désormais à polkit lui-même
  si les mises à jour passent sans mot de passe, et la case de la page Planification reflète l'état réel.
- Linux: the window did not start on Manjaro (“Permission denied” on /etc/polkit-1/rules.d, a folder
  reserved for root and polkitd). Martinet now asks polkit itself whether updates run without a password,
  and the Schedule page box shows the real state.

### 0.6.5

- Linux, AUR : un paquet dont la construction a échoué (source à la somme de contrôle fausse, par exemple)
  est écarté aux passages suivants tant que l'AUR n'en publie pas une nouvelle version. Fini les centaines
  de Mo de dépendances retéléchargées et les mots de passe redemandés pour rien ; le résumé le signale.
- Journal Linux lisible : couleurs de yay et pacman retirées, message sans objet de pkexec masqué.
- Linux, AUR: a package whose build failed (wrong source checksum, for instance) is skipped on later runs
  until the AUR publishes a new version. No more hundreds of MB of dependencies downloaded again and
  passwords asked for nothing; the summary says so.
- Readable Linux log: yay and pacman colours removed, pointless pkexec message hidden.

### 0.6.4

- Linux, AppImage : une AppImage connue posée à la main (~/Applications, ~/.local/bin, ~/AppImages) est
  suivie comme les applications du kit : dernière Release, empreinte vérifiée par SHA256SUMS, échange
  atomique du fichier, jamais pendant qu'elle tourne. Sa version n'étant pas lisible dans le fichier,
  Martinet pose la dernière une première fois puis retient celle qu'il a installée. Premier cas :
  Perce-Neige Simulator.
- Linux, AppImage: a known AppImage placed by hand (~/Applications, ~/.local/bin, ~/AppImages) is followed
  like the kit apps: latest Release, checksum checked against SHA256SUMS, atomic file swap, never while it
  runs. As its version cannot be read from the file, Martinet installs the latest once, then remembers the
  version it installed. First case: Perce-Neige Simulator.

### 0.6.3

- Linux, pilote NVIDIA : après un changement de pilote et le redémarrage, Martinet repère qu'il manque
  aux applications Flatpak l'extension graphique de la nouvelle version et la fait installer. Sans elle,
  elles perdent l'accélération graphique.
- Linux, NVIDIA driver: after a driver change and the reboot, Martinet notices that Flatpak apps lack the
  graphics extension for the new version and has it installed. Without it they lose hardware acceleration.

### 0.6.2

- Linux, Flatpak : les runtimes qui n'annoncent pas de version (pilote graphique, codecs, plateformes)
  affichent « nouvelle révision » au lieu d'une colonne vide. Les runtimes installés en deux branches ne
  sont plus confondus : chaque branche a sa ligne et sa version installée.
- Linux, Flatpak: runtimes that announce no version (graphics driver, codecs, platforms) show “new
  revision” instead of an empty column. Runtimes installed in two branches are no longer mixed up: each
  branch has its own row and installed version.

### 0.6.1

- ASIStudio se met à jour tout seul : Martinet télécharge l'installeur officiel de ZWO, vérifie sa signature
  (SUZHOU ZWO CO., LTD.) et l'installe sans fenêtre ; il attend si ASICap, ASIImg ou un autre logiciel
  ASI est ouvert. Les pilotes ZWO (caméra, ASCOM) restent à installer à la main, mais le bouton
  « Installer » télécharge maintenant directement l'installeur officiel. Deux paquets du même nom (les deux
  « Microsoft Teams ») sont distingués par leur identifiant dans le résumé des échecs.
- ASIStudio updates on its own: Martinet downloads the official ZWO installer, checks its signature
  (SUZHOU ZWO CO., LTD.) and installs it without a window; it waits while ASICap, ASIImg or another ASI
  program is open. ZWO drivers (camera, ASCOM) are still installed by hand, but the "Install" button now
  downloads the official installer directly. Two packages with the same name (both "Microsoft Teams") are
  told apart by their identifier in the failure summary.

### 0.6.0

- Poste d'observatoire (N.I.N.A., PHD2, SharpCap, APT ou ASCOM installés) : le passage automatique attend
  qu'aucune acquisition ne soit en cours et ne démarre pas la nuit (17:00-09:00) ; les pilotes de Windows
  Update ne partent plus seuls (monture, caméra). Nouvelles sources : pilotes ZWO (caméra, ASCOM),
  ASIStudio, Cartes du Ciel ; 10Micron, PixInsight et Pegasus reconnus comme se mettant à jour seuls.
  Adobe Acrobat Pro ajouté aux logiciels payants.
- Observatory computer (N.I.N.A., PHD2, SharpCap, APT or ASCOM installed): the scheduled run waits until no
  imaging session is running and does not start at night (17:00-09:00); Windows Update drivers are no
  longer installed on their own (mount, camera). New sources: ZWO drivers (camera, ASCOM), ASIStudio,
  Cartes du Ciel; 10Micron, PixInsight and Pegasus recognised as self-updating. Adobe Acrobat Pro added to
  paid programs.

### 0.5.9

- Mise à jour de Martinet : les fichiers qui n'ont pas changé ne sont plus réécrits. Un antivirus qui garde
  la main sur l'un d'eux (souvent le lanceur, après une fausse alerte puis une restauration) ne bloque plus
  toute la mise à jour.
- Martinet update: files that have not changed are no longer rewritten. An antivirus holding on to one of
  them (often the launcher, after a false alarm and a restore) no longer blocks the whole update.

### 0.5.8

- Mise à jour de Martinet : si un fichier est momentanément bloqué (antivirus qui l'analyse, fichier restauré
  de quarantaine en lecture seule), Martinet patiente et réessaie au lieu d'échouer aussitôt. Si le blocage
  dure, le message conseille d'ajouter le dossier de Martinet aux exceptions de l'antivirus.
- Martinet update: if a file is briefly locked (antivirus scanning it, file restored from quarantine as
  read-only), Martinet waits and retries instead of failing at once. If the lock persists, the message
  suggests adding the Martinet folder to the antivirus exceptions.

### 0.5.7

- Logiciels payants : Martinet ne les fait plus jamais passer tout seul à une nouvelle version principale
  (6.x → 7.x), qui se rachète souvent, ni quand la version installée est inconnue. Les petites mises à jour
  restent automatiques. La ligne est en orange et décochée ; pour installer quand même, il suffit de la cocher.
  Liste de départ (USB Safely Remove, TreeSize, 4K Video Downloader+, RescuePRO, MakeMKV, Beyond Compare,
  Sublime Text/Merge, Directory Opus), à compléter avec le bouton « Payant oui / non ». Le résumé du passage
  automatique cite les logiciels laissés de côté.
- Paid programs: Martinet never moves them on its own to a new major version (6.x → 7.x), which often has to
  be bought again, nor when the installed version is unknown. Small updates stay automatic. The row shows in
  orange, unticked; tick it to install anyway. Starting list (USB Safely Remove, TreeSize, 4K Video
  Downloader+, RescuePRO, MakeMKV, Beyond Compare, Sublime Text/Merge, Directory Opus), extended with the
  “Paid: yes / no” button. The scheduled run's summary names the programs held back.

### 0.5.6

- Windows : la version de vos applications du kit est lue dans leur dossier (app\VERSION), plus dans le
  registre : leur mise à jour intégrée ne réécrit pas le registre, qui affichait encore l'ancienne version
  (une application à jour était annoncée « à faire à la main »). Console : plus de marqueurs techniques
  (Windows Update, mise à jour des applications).
- Windows: your kit apps' version is read from their folder (app\VERSION), not from the registry, which
  their built-in update does not rewrite (an up-to-date app was listed as “to do by hand”). Console: no more
  technical markers (Windows Update, app updates).

### 0.5.5

- Windows : vos applications du kit installées dans le profil (celles qui ont une source GitHub) sont
  mises à jour par « Mettre à jour et nettoyer » au lieu d'être laissées « à faire à la main ». Martinet
  lance, avec le Python de chaque application, sa propre mise à jour (hôtes GitHub, empreinte,
  signature quand l'application en a une) ; seul son code est remplacé, ses réglages ne bougent pas. Une
  application ouverte est laissée de côté.
- Windows: your kit apps installed in the user profile (those with a GitHub source) are now updated by
  “Update and clean up” instead of being left “to do by hand”. Martinet runs each app's own updater with
  that app's Python (GitHub hosts, checksum, signature when the app has one); only its code is replaced,
  its settings stay. An open app is skipped.

### 0.5.4

- Mises à jour signées : Martinet n'installe plus une mise à jour que si son archive figure dans un
  manifeste signé par la clé de l'éditeur (Ed25519, hors de GitHub) ; un accès GitHub volé ne peut plus
  pousser de code sur les postes. L'adresse atteinte après les redirections est vérifiée elle aussi.
- Signed updates: Martinet installs an update only if its archive is listed in a manifest signed by the
  publisher's key (Ed25519, kept off GitHub); a stolen GitHub access can no longer push code to installed
  copies. The address reached after redirects is checked as well.

### 0.5.3

- Coupure réseau pendant un passage : Martinet attend le retour du réseau (3 min au plus) puis refait une
  fois les mises à jour tombées sur une erreur de réseau ; le pilote graphique attend aussi le réseau
  avant son téléchargement. Le bilan sépare les échecs de réseau, les vrais échecs et les mises à jour que
  winget annonce sans savoir les appliquer (0x8A15002B). Defender arrêté (autre antivirus) : une ligne
  claire au lieu d'une erreur PowerShell.
- Network drop during a run: Martinet waits for the network (up to 3 min) and retries once the updates
  that failed on a network error; the graphics driver also waits before downloading. The summary separates
  network failures, real failures and updates winget lists but cannot apply (0x8A15002B). Defender not
  running (another antivirus): a clear line instead of a PowerShell error.

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

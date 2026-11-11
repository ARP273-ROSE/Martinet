# Journal des versions / Changelog

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

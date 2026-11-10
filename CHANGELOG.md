# Journal des versions / Changelog

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

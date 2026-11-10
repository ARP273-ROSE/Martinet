# Journal des versions / Changelog

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

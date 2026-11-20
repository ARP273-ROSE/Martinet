# Progression

## 0.1.0 — première version

Fait :
- moteur : winget (module PowerShell officiel, repli sur le tableau texte), registre, cartes graphiques,
  sources hors winget (GitHub, page d'éditeur, service NVIDIA), Windows Update (API COM), raccourcis
  (.lnk lus directement), ménage, tâche planifiée, historique ;
- fenêtre PyQt6 (8 pages), file de travaux unique, mode démonstration hors Windows ;
- passage automatique : programmes, Windows Update (facultatives au choix), pilote NVIDIA silencieux,
  raccourcis mis de côté, ménage, notification ;
- essais : Linux (mode démonstration) et Windows réel (workflow `essais.yml`) ; manuel FR/EN.

À vérifier sur un vrai poste :
- élévation au démarrage et bandeau sans droits ;
- installation silencieuse du pilote NVIDIA (`-s -noreboot`) ;
- notification de fin du passage automatique.

## 0.6.0 — poste d'observatoire (20/11/2026)

Constat sur un vrai PC d'observatoire : `facultatives=True` aurait laissé partir les pilotes facultatifs
(adaptateur USB-série de la monture…), et la tâche planifiée StartWhenAvailable pouvait se rattraper en
pleine nuit d'acquisition.
- `martinet/observatoire.py` : poste astro détecté par le registre (N.I.N.A., PHD2, SharpCap, APT, ASCOM
  Platform, SGP, Voyager) ou forcé (`garde_observatoire` = auto/oui/non). Passage auto reporté si un processus
  d'acquisition tourne ou pendant `plage_nuit` (17:00-09:00) ; pilotes Windows Update jamais automatiques.
- Sources : ZWO ASCOM / Camera Driver / ASIStudio, Cartes du Ciel ; 10Micron, PixInsight, Pegasus = « seul ».
  Adobe.Acrobat.Pro ajouté aux payants.
- Pas encore de réglage dans la fenêtre pour la garde (reglages.json seulement).

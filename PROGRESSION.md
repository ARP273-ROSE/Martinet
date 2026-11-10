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

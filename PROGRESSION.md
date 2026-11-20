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

## 0.6.1 — ASIStudio installé seul (20/11/2026)

Demande après un passage réel : les trois « à faire à la main » (ASIStudio, pilote ASCOM ZWO, pilote caméra
ZWO) sont-ils automatisables ? Décision : ASIStudio oui (simple application), les pilotes non (un pilote
caméra changé seul peut casser la connexion de l'acquisition le soir même).
- Champs de source `installeur` (lien direct stable, ici `dl.zwoastro.com/software?app=…`, redirection vers
  l'exe signé), `silencieux` (« /S », installeur NSIS), `signataire` (motif du sujet Authenticode exigé,
  `SUZHOU ZWO CO., LTD.`, certificat EV GlobalSign), `bloquants` (processus ASI* ouverts → report).
- `orchestre.installables_seuls` / `installer_seul` : téléchargement, `Get-AuthenticodeSignature` (Valid +
  sujet), lancement sans fenêtre ; admin requis, sinon simplement signalé. Les pilotes ZWO ont seulement le
  lien direct (bouton « Installer », avec confirmation).
- Nom de fichier pour un lien sans extension : `source-version.exe` (`sources.nom_installeur`).
- Résumé des échecs : identifiant winget ajouté quand deux paquets portent le même nom (Microsoft Teams).
- Constaté au même passage, pas dans Martinet : HWiNFO 8.54 (lien du manifeste winget en 404) ; échec de
  Microsoft.Teams.Free = winget terminé sans ligne de résultat (Martinet ne tue winget qu'à l'annulation,
  délai 2 h), cause non établie.
- Pas encore vu sur une vraie installation : le premier passage avec ASIStudio 1.23 le dira.

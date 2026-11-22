# Progression

## ▶ NOTE DE REPRISE (22/11/2026)

**Où on en est** : 0.6.9 publiée (branche main, étiquette v0.6.9, CI « essais » et « Publier une version »
vertes). Windows et Linux utilisés en vrai ; la mise à jour intégrée fonctionne sur les deux.

**Vérifié en vrai**
- Windows : passage complet avec les applications du kit (0.5.5/0.5.6), garde de fin de session (0.5.2),
  reprise réseau (0.5.3). Un antivirus qui verrouille le lanceur ne bloque plus la mise à jour (0.5.9 :
  fichiers inchangés laissés en place).
- Linux (Manjaro, carte NVIDIA) : installation par installer.sh, --verifier, --auto, pacman, yay et AUR,
  Flatpak, applications du kit, AppImage, mise à jour par le bouton (0.6.4 → 0.6.8), extension GL.nvidia
  après un changement de pilote, mise à l'écart d'un AUR en échec, purge des fichiers d'état (0.6.8),
  règle polkit posée avec son témoin /etc/martinet/regle-polkit-active.

**PAS encore vérifié**
- Linux : un passage AVEC des paquets à installer une fois la règle polkit posée (attendu : au plus une
  demande de mot de passe, celle du ménage).
- 0.6.9 : les boutons Oui / Non à l'écran (test unitaire seulement) ; Windows non revu après ce changement.
- Linux : le message « doublon » kit + AppImage, en vrai (test unitaire seulement).
- AMD : lecture de RadeonSoftwareVersion sur un vrai PC AMD ; Windows 10 réel ; garde d'observatoire
  (0.6.0) en conditions réelles.

**Choix arrêtés**
- Les applications lancées directement depuis des dépôts git de travail ne sont PAS mises à jour par
  Martinet (pas de git pull) : elles tournent déjà sur le code courant, et un pull à travers un partage
  réseau abîmerait les dépôts.
- Les messages d'erreur d'updater.py restent tels quels : fichier commun à toutes les applications du kit.

**Pièges rencontrés**
- /etc/polkit-1/rules.d est en 750 root:polkitd sur Manjaro : Path.exists() y lève PermissionError ;
  pkcheck --detail est refusé aux non-root. D'où le témoin public.
- yay est lancé avec --sudo pkexec : la règle « pkexec /usr/bin/pacman » couvre donc tous ses appels.
- Un antivirus comportemental peut mettre run.py en quarantaine (chaîne pythonw relancée) puis le garder
  verrouillé en silence après restauration.
- Qt ne traduit ses boutons standard qu'avec qtbase_<langue>.qm chargé (i18n.traduire_qt).

**Prochaines étapes**
1. Au prochain passage Linux avec des paquets à installer : compter les demandes de mot de passe.
2. Vérifier à l'écran Oui / Non (FR) et Yes / No (EN), sous Windows et sous Linux.
3. Reporter dans updater.py des autres applications du kit `_identique` + `_ecarter` (0.5.8/0.5.9) si un
   antivirus les bloque aussi.
4. Essais : `timeout 200 <venv>/bin/python -m pytest -q tests` (120 réussis, 13 sautés au 22/11).
   Publication : VERSION, CHANGELOG (FR + EN), commit, `git tag vX`, `git push origin main vX`.

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

## 21/11/2026 — Linux en vrai (Manjaro, carte NVIDIA) : 0.6.2 → 0.6.7

- Premier test sur une vraie machine Manjaro : installation par installer.sh, puis --verifier et --auto.
  Résultats : pacman OK (environ 590 paquets, nouveau noyau, pilote NVIDIA) ; AUR 4 sur 5 (astap : somme de
  contrôle amont fausse) ; applications du kit OK ; mise à jour par le bouton intégré OK (0.6.4 → 0.6.5 →
  0.6.6).
- 0.6.2 : Flatpak, runtimes sans version (« nouvelle révision ») et branches distinguées.
- 0.6.3 : extension GL.nvidia-<version chargée> installée après un changement de pilote. Vérifié : 615 posée,
  610 retirée.
- 0.6.4 : AppImages connues (table APPIMAGES ; version retenue dans appimages.json). Vérifié : Perce-Neige
  1.76.4 posé.
- 0.6.5 : AUR en échec écarté jusqu'à la version suivante (aur_echecs.json, vérifié écrit) ; journal sans
  ANSI ni message d'agent textuel polkit.
- 0.6.6 : la fenêtre plantait au démarrage (rules.d en 750 root:polkitd → PermissionError dans
  regle_active). 0.6.7 : pkcheck --detail est refusé aux non-root, donc l'état de la règle se lit dans un
  témoin public /etc/martinet/regle-polkit-active, posé et retiré avec la règle.
- Applications lancées depuis les dépôts git du NAS : volontairement pas de git pull, elles sont toujours sur
  le code courant.
- RESTE à constater : un passage en 0.6.7 avec la règle cochée (attendu : 1 seul mot de passe, pour le
  ménage ; astap affiché « écarté ») ; « 223,2 Mo » libérés deux fois de suite = probablement les dépendances
  de compilation d'astap remises en cache à chaque échec, ce qui devrait cesser ; kde.pacsave est compté
  avec les .pacnew (à revoir).
- 22/11 : 0.6.8 = doublon kit + AppImage d'un même dépôt signalé et non mis à jour ; appimages.json et
  aur_echecs.json purgés. Sur la machine : règle polkit posée (témoin présent), plus de .pacnew ni d'orphelin.
  Reste à éprouver la règle sur un passage avec de vrais paquets.

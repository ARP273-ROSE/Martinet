# Martinet

**FR** — Tenir Windows à jour d'un seul geste, comme `yay` ou `apt` sous Linux.
**EN** — Keep Windows up to date in one go, like `yay` or `apt` on Linux. *(English below.)*

![Martinet](logo_128.png)

## Ce que fait Martinet

| Page | Contenu |
|---|---|
| Tableau de bord | « Tout vérifier » (ne modifie rien), puis « Tout mettre à jour » |
| Programmes (winget) | logiciels et applis du Store mis à jour sans fenêtre par winget, le gestionnaire de paquets de Windows ; liste d'exclusions |
| Hors winget | logiciels que winget ne suit pas : dernière version lue chez l'éditeur (Releases GitHub ou page de téléchargement), installeur officiel en un clic ; « confier à winget » quand il connaît le logiciel ; vos propres sources |
| Windows et pilotes | Windows Update (système, pilotes des fabricants et mises à jour facultatives au choix), Defender, pilote NVIDIA comparé au service officiel de NVIDIA |
| Raccourcis morts | Bureau, menu Démarrer, barre des tâches ; mis de côté et restaurables, jamais effacés ; cibles réseau ou sur lecteur absent jamais comptées |
| Ménage | temporaires de plus de 7 jours, rapports d'erreurs, cache de Windows Update, vidages mémoire, journaux, restes d'installation des pilotes ; sur demande : miniatures, caches des navigateurs et des shaders, anciens composants (DISM), corbeille. Pas de « nettoyage du registre » |
| Planification | passage automatique quotidien ou hebdomadaire, notification à la fin |
| Historique | chaque passage et son détail |

En ligne de commande : `run.py --verifier` (liste sans rien changer), `run.py --auto` (passage complet).

Catalogue de sources fourni : PHD2, ASCOM Platform, N.I.N.A., ASTAP, GraXpert, SharpCap, et les logiciels qui se mettent à jour seuls ; le reste s'ajoute ou s'importe depuis l'interface.

Installation : télécharger `Martinet-Setup.exe` depuis les [Releases](https://github.com/ARP273-ROSE/Martinet/releases/latest). Martinet se met lui-même à jour.

---

## What Martinet does

- **Programs (winget)**: silent updates of programs and Store apps through winget, with an ignore list.
- **Outside winget**: programs winget does not track, checked against the vendor (GitHub releases or download page); official installer in one click; hand a program over to winget when it knows it; add your own sources.
- **Windows and drivers**: Windows Update (system, vendor drivers and optional updates if you wish), Defender, NVIDIA driver checked against NVIDIA's own service.
- **Dead shortcuts**: set aside and restorable, never deleted; network targets and missing drives are never counted.
- **Clean-up**: temporary files older than 7 days, error reports, Windows Update cache, crash dumps, logs, driver setup leftovers; on request: thumbnails, browser and shader caches, superseded components (DISM), recycle bin. No “registry cleaning”.
- **Schedule**: daily or weekly unattended run with a notification; **History** of every run.

Command line: `run.py --verifier` (list only), `run.py --auto` (full run).

Licence: MIT.

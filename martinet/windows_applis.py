"""Windows : vos applications du kit (installées dans %LOCALAPPDATA%\\Programs\\<Nom>).

Chacune embarque son Python (python\\) et son code (app\\, avec kit.json et
updater.py). Martinet ne réinvente pas leur mise à jour : il lance, avec le
Python de l'application, SON propre updater — celui qu'elle utilise d'elle-même
au démarrage, avec ses contrôles (hôtes GitHub, SHA256SUMS, signature Ed25519
quand l'application en a une). Seul app\\ est remplacé ; les réglages, qui
vivent ailleurs, ne sont jamais touchés. Une application ouverte est laissée
de côté : on ne remplace pas son code sous ses pieds.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from . import demo, systeme
from .linux_applis import Appli

# lancé par le Python de l'application, depuis son dossier app\
SCRIPT_MAJ = r"""
import sys, pathlib
app = pathlib.Path.cwd()
sys.path.insert(0, str(app))
import updater
version = (app / sys.argv[1]).read_text(encoding="utf-8").strip()
info = updater.check(version)
if not info:
    print("MARTINET:RIEN")
    sys.exit(3)
updater.download_and_apply(info)
print("MARTINET:OK " + str(info.get("version")))
"""


def _racine() -> Path:
    return Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local") / "Programs"


def trouver() -> list[Appli]:
    """Les applications du kit installées pour l'utilisateur (Martinet excepté)."""
    if demo.actif():
        return []
    applis = []
    try:
        dossiers = sorted(_racine().iterdir())
    except OSError:
        return []
    for d in dossiers:
        try:
            kit = json.loads((d / "app" / "kit.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        depot, tech = kit.get("depot_distribution") or "", kit.get("nom_technique") or d.name
        if (not re.fullmatch(r"[\w.-]+/[\w.-]+", depot) or tech == "martinet"
                or not (d / "python" / "python.exe").exists() or not (d / "app" / "updater.py").exists()):
            continue
        fichier_version = kit.get("fichier_version") or "VERSION"
        try:
            version = (d / "app" / fichier_version).read_text(encoding="utf-8").strip()
        except OSError:
            version = ""
        a = Appli(kit.get("nom_affiche") or kit.get("nom_fichier") or d.name, tech,
                  kit.get("nom_fichier") or d.name, depot, str(d), version)
        a.archive = fichier_version            # Windows : sert à retrouver la version
        applis.append(a)
    return applis


def en_marche(dossier: str) -> bool:
    """Un processus tourne-t-il depuis ce dossier (son Python embarqué) ?"""
    chemin = dossier.rstrip("\\/").replace("'", "''") + "\\"
    script = (f"$d = '{chemin}'; "
              "@(Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -and "
              "$_.ExecutablePath.StartsWith($d, [StringComparison]::OrdinalIgnoreCase) }).Count")
    code, sortie = systeme.powershell(script, timeout=60)
    if code != 0:
        return True                            # dans le doute, on ne touche pas
    try:
        return int(sortie.strip().splitlines()[-1]) > 0
    except (ValueError, IndexError):
        return False


def mettre_a_jour(a: Appli, journal=None, annulation=None) -> tuple[bool, str]:
    """Lance l'updater de l'application avec son propre Python."""
    from .i18n import tr
    if demo.actif():
        demo.pause(0.3)
        return True, ""
    if en_marche(a.dossier):
        return False, tr("lx.applis.ouverte", nom=a.nom)
    python = Path(a.dossier) / "python" / "python.exe"
    code, sortie = systeme.executer_flux([str(python), "-I", "-c", SCRIPT_MAJ, a.archive or "VERSION"],
                                         journal, annulation, timeout=1800,
                                         cwd=str(Path(a.dossier) / "app"))
    if code == 0 and "MARTINET:OK" in sortie:
        return True, ""
    if code == 3:
        return False, tr("win.applis.rien")
    lignes = [l for l in sortie.strip().splitlines() if l.strip()]
    return False, (lignes[-1][:200] if lignes else f"code {code}")

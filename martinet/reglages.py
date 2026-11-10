"""Réglages de Martinet, partagés entre la fenêtre et la tâche planifiée."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from . import systeme


@dataclass
class Reglages:
    ignores_winget: list[str] = field(default_factory=list)       # identifiants winget
    ignores_hors_winget: list[str] = field(default_factory=list)  # noms de logiciels
    elever_au_demarrage: bool = True
    # tâche planifiée
    auto_programmes: bool = True
    auto_windows: bool = True
    auto_menage: bool = True
    facultatives: bool = True      # mises à jour Windows facultatives incluses
    auto_pilote: bool = True       # pilote NVIDIA installé en silencieux
    auto_raccourcis: bool = True   # raccourcis morts mis de côté (récupérables)
    planif_proposee: bool = False  # question posée au premier lancement
    auto_jour: int = 6            # 0 = lundi … 6 = dimanche
    auto_heure: str = "12:00"
    auto_frequence: str = "hebdo"  # quotidien, hebdo


def _fichier():
    return systeme.dossier_donnees() / "reglages.json"


def charger() -> Reglages:
    try:
        donnees = json.loads(_fichier().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Reglages()
    connus = {k: v for k, v in donnees.items() if k in Reglages.__dataclass_fields__}
    return Reglages(**connus)


def enregistrer(r: Reglages) -> None:
    f = _fichier()
    tmp = f.with_suffix(".tmp")
    tmp.write_text(json.dumps(asdict(r), ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(f)

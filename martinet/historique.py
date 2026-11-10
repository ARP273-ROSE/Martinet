"""Historique des passages (fenêtre ou tâche planifiée), une ligne JSON chacun."""
from __future__ import annotations

import datetime
import json

from . import systeme

MAX = 500


def _fichier():
    return systeme.dossier_donnees() / "historique.jsonl"


def ajouter(mode: str, lignes: list[str], resume: str) -> None:
    entree = {"date": datetime.datetime.now().isoformat(timespec="seconds"),
              "mode": mode, "resume": resume, "lignes": lignes[-400:]}
    f = _fichier()
    anciennes = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
    anciennes = anciennes[-(MAX - 1):]
    anciennes.append(json.dumps(entree, ensure_ascii=False))
    f.write_text("\n".join(anciennes) + "\n", encoding="utf-8")


def lire() -> list[dict]:
    f = _fichier()
    if not f.exists():
        return []
    entrees = []
    for ligne in f.read_text(encoding="utf-8").splitlines():
        try:
            entrees.append(json.loads(ligne))
        except ValueError:
            continue
    return list(reversed(entrees))

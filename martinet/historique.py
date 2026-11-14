"""Historique des passages (fenêtre ou tâche planifiée), une ligne JSON chacun."""
from __future__ import annotations

import datetime
import json

from . import systeme

MAX = 500


def _fichier():
    return systeme.dossier_donnees() / "historique.jsonl"


def ajouter(mode: str, lignes: list[str], resume: str, date: str = "") -> None:
    entree = {"date": date or datetime.datetime.now().isoformat(timespec="seconds"),
              "mode": mode, "resume": resume, "lignes": lignes[-400:]}
    f = _fichier()
    anciennes = f.read_text(encoding="utf-8").splitlines() if f.exists() else []
    anciennes = anciennes[-(MAX - 1):]
    anciennes.append(json.dumps(entree, ensure_ascii=False))
    f.write_text("\n".join(anciennes) + "\n", encoding="utf-8")


# --- passage en cours : écrit ligne à ligne, pour qu'un passage coupé net
# (installeur qui ferme Martinet, coupure de courant…) laisse une trace.
def _fichier_passe():
    return systeme.dossier_donnees() / "passage_en_cours.log"


def demarrer_passe(mode: str) -> None:
    try:
        _fichier_passe().write_text(f"{mode}\n", encoding="utf-8")
    except OSError:
        pass


def ecrire_passe(texte: str) -> None:
    f = _fichier_passe()
    try:
        if f.exists():
            with open(f, "a", encoding="utf-8") as fh:
                fh.write(texte.rstrip("\n") + "\n")
    except OSError:
        pass


def finir_passe() -> None:
    try:
        _fichier_passe().unlink(missing_ok=True)
    except OSError:
        pass


def recuperer_passe_interrompue(resume: str) -> bool:
    """Au démarrage : un passage resté ouvert a été coupé ; il entre dans l'historique."""
    f = _fichier_passe()
    try:
        if not f.exists():
            return False
        lignes = f.read_text(encoding="utf-8", errors="replace").splitlines()
        date = datetime.datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return False
    finir_passe()
    if len(lignes) < 2:
        return False
    mode = lignes[0].strip() or "manuel"
    dernier = next((l for l in reversed(lignes[1:]) if l.strip()), "")
    ajouter(mode, lignes[1:] + ["", resume, dernier], f"{resume} · {dernier}"[:300], date=date)
    return True


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

"""Comparer deux numéros de version écrits n'importe comment.

« 7.1.3.4851 », « v7.1.3 », « 2026.07.16 », « 576.80 », « 3.2 HF1 » : on garde
la suite des nombres et on compare position par position, la plus courte
étant complétée par des zéros. Une version installée plus détaillée que la
version publiée (numéro de compilation en plus) n'est donc jamais vue comme
périmée : on préfère rater une mise à jour que d'en annoncer une fausse.
"""
from __future__ import annotations

import re

_NOMBRES = re.compile(r"\d+")


def nombres(version: str | None) -> tuple[int, ...]:
    if not version:
        return ()
    texte = str(version).strip()
    texte = re.sub(r"^[^\d]*", "", texte)          # « v », « Version », …
    return tuple(int(n) for n in _NOMBRES.findall(texte))


def comparer(a: str | None, b: str | None) -> int:
    """-1 si a < b, 0 si égales (ou incomparables), 1 si a > b."""
    na, nb = nombres(a), nombres(b)
    if not na or not nb:
        return 0
    n = max(len(na), len(nb))
    na += (0,) * (n - len(na))
    nb += (0,) * (n - len(nb))
    return (na > nb) - (na < nb)


def plus_recente(disponible: str | None, installee: str | None) -> bool:
    """La version disponible est-elle strictement plus récente ?"""
    return comparer(disponible, installee) > 0


def la_plus_haute(versions) -> str | None:
    meilleure = None
    for v in versions:
        if nombres(v) and (meilleure is None or comparer(v, meilleure) > 0):
            meilleure = v
    return meilleure


def nvidia_lisible(version_pilote: str | None) -> str | None:
    """Version Windows d'un pilote NVIDIA → numéro commercial.

    32.0.15.7680 → 576.80 : les cinq derniers chiffres des deux dernières
    parties. Renvoie None si le format ne s'y prête pas.
    """
    if not version_pilote:
        return None
    parties = str(version_pilote).split(".")
    if len(parties) != 4 or not all(p.isdigit() for p in parties):
        return None
    chiffres = (parties[2] + parties[3].zfill(4))[-5:]
    return f"{int(chiffres[:3])}.{chiffres[3:]}"

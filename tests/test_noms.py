"""Aucun nom indéfini dans le code (une étape Windows Update a cassé en 0.6.10 faute d'un import)."""
from pathlib import Path

import pytest


def test_aucun_nom_indefini():
    api = pytest.importorskip("pyflakes.api")
    from pyflakes import reporter as rep
    import io
    racine = Path(__file__).resolve().parent.parent
    sortie = io.StringIO()
    r = rep.Reporter(sortie, sortie)
    for f in sorted(racine.glob("martinet/*.py")) + [racine / n for n in
                                                    ("run.py", "updater.py", "interface_kit.py", "reporting.py")]:
        api.checkPath(str(f), r)
    indefinis = [l for l in sortie.getvalue().splitlines() if "undefined name" in l]
    assert not indefinis, "\n".join(indefinis)

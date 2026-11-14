"""Réglages communs : mode démonstration rapide, données dans un dossier jetable."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["MARTINET_DEMO_RAPIDE"] = "1"
os.environ.setdefault("MARTINET_DEMO", "1")          # tests/test_windows.py le remet à 0
# système imité par défaut : Windows (les essais Linux le changent eux-mêmes)
if os.environ.get("MARTINET_DEMO") == "1":
    os.environ.setdefault("MARTINET_SYSTEME", "windows")

import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def donnees(tmp_path, monkeypatch):
    monkeypatch.setenv("MARTINET_DONNEES", str(tmp_path / "donnees"))
    return tmp_path / "donnees"

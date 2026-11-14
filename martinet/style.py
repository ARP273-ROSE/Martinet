"""Apparence figée de Martinet (standard du kit : rien ne dépend du thème
de Windows). Bleu ciel et blanc, rouge brique pour les alertes."""
from __future__ import annotations

from pathlib import Path

POLICES = Path(__file__).resolve().parent / "polices"

CIEL = "#1C6DB4"
CIEL_FONCE = "#14548C"
ALERTE = "#B5382B"
VERT = "#2E7D32"
ORANGE = "#B26A00"
GRIS = "#6B7785"

COULEURS = {
    "fenetre": "#F4F6F9", "texte": "#1F2933", "base": "#FFFFFF", "base_alt": "#F1F5FA",
    "bouton": "#E9EEF4", "texte_bouton": "#1F2933", "selection": "#CFE3F7",
    "texte_selection": "#10263D", "lien": CIEL, "infobulle": "#FFFFFF",
    "texte_infobulle": "#1F2933", "desactive": "#98A2AE", "clair": "#FFFFFF",
    "moyen": "#C9D2DC", "sombre": "#9AA6B2",
}

FEUILLE = f"""
QListWidget#navigation {{ background: #E6ECF3; border: none; padding: 6px; font-size: 11pt; }}
QListWidget#navigation::item {{ padding: 9px 10px; border-radius: 6px; margin: 1px 0; }}
QListWidget#navigation::item:selected {{ background: {CIEL}; color: white; }}
QPushButton {{ padding: 6px 14px; border: 1px solid #C2CCD7; border-radius: 5px; background: #FFFFFF; }}
QPushButton:hover {{ border-color: {CIEL}; }}
QPushButton:disabled {{ color: #98A2AE; background: #EEF1F5; }}
QPushButton[role="principal"] {{ background: {CIEL}; color: white; border-color: {CIEL_FONCE}; font-weight: 600; }}
QPushButton[role="principal"]:hover {{ background: {CIEL_FONCE}; }}
QPushButton[role="principal"]:disabled {{ background: #9DBAD6; color: #EEF4FA; }}
QPushButton[role="carte"] {{ text-align: left; padding: 14px; background: white; border: 1px solid #D5DDE6; border-radius: 10px; }}
QPushButton[role="carte"]:hover {{ border: 1px solid {CIEL}; background: #F7FBFF; }}
QLabel[role="titre"] {{ font-size: 17pt; font-weight: 700; color: {CIEL_FONCE}; }}
QLabel[role="sous-titre"] {{ color: {GRIS}; font-size: 10.5pt; }}
QLabel#avertissement {{ background: #FFF4D6; border: 1px solid #E8C770; border-radius: 6px; padding: 8px 10px; }}
QFrame#bandeau {{ background: #FFF4D6; border: 1px solid #E8C770; border-radius: 6px; }}
QGroupBox {{ font-weight: 600; border: 1px solid #D5DDE6; border-radius: 8px; margin-top: 12px; padding-top: 10px; background: white; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 4px; color: {CIEL_FONCE}; }}
QTableWidget {{ gridline-color: #E3E8EE; border: 1px solid #D5DDE6; }}
QHeaderView::section {{ background: #EEF2F7; padding: 5px; border: none; border-bottom: 1px solid #D5DDE6; font-weight: 600; }}
QProgressBar#progres {{ min-height: 20px; max-height: 20px; border-radius: 6px; text-align: center; font-weight: 600; }}
QLabel#etat {{ font-weight: 600; }}
QLabel#etape {{ color: #4A5D72; }}
QPlainTextEdit#console {{ background: #10263D; color: #DDE7F2; font-family: Consolas, "DejaVu Sans Mono", monospace; font-size: 9pt; border-radius: 6px; }}
QProgressBar {{ border: 1px solid #C2CCD7; border-radius: 4px; text-align: center; height: 14px; background: white; }}
QProgressBar::chunk {{ background: {CIEL}; }}
"""


def appliquer(app) -> None:
    import interface_kit
    interface_kit.appliquer_style(app, COULEURS, polices=POLICES, famille="Source Sans 3",
                                  taille=10.0, feuille=FEUILLE, sombre=False)

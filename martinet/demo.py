"""Mode démonstration : données fictives quand on n'est pas sous Windows.

Sert aux essais automatiques, aux captures du manuel et au développement
sous Linux. Activé d'office hors Windows, ou par MARTINET_DEMO=1.
"""
from __future__ import annotations

import os
import sys
import time


def actif() -> bool:
    return os.environ.get("MARTINET_DEMO") == "1" or sys.platform != "win32"


def pause(s: float = 0.15) -> None:
    if os.environ.get("MARTINET_DEMO_RAPIDE") != "1":
        time.sleep(s)


PAQUETS = [
    # id, nom, installée, disponible, source
    ("Mozilla.Firefox", "Mozilla Firefox (x64 fr)", "144.0.1", "145.0", "winget"),
    ("VideoLAN.VLC", "VLC media player", "3.0.20", "3.0.21", "winget"),
    ("7zip.7zip", "7-Zip 24.08 (x64)", "24.08", "25.01", "winget"),
    ("Git.Git", "Git", "2.51.0", "2.52.0", "winget"),
    ("Stellarium.Stellarium", "Stellarium", "25.2", "25.3", "winget"),
    ("9NKSQGP7F2NH", "WhatsApp", "2.2540.3.0", "2.2545.1.0", "msstore"),
    ("Microsoft.PowerToys", "PowerToys (Preview)", "0.94.1", "0.94.1", "winget"),
    ("Notepad++.Notepad++", "Notepad++ (64-bit x64)", "8.8.6", "8.8.6", "winget"),
    ("", "N.I.N.A. - Nighttime Imaging 'N' Astronomy", "3.1.2.9001", "", ""),
    ("", "PHD2", "2.6.13", "", ""),
    ("", "ASCOM Platform 7", "7.0.2.4721", "", ""),
    ("", "ASTAP, Astrometric STAcking Program", "2025.10.18", "", ""),
    ("", "Outil maison de traitement", "1.0", "", ""),
    ("", "Pilote de caméra du fabricant", "3.29", "", ""),
]

MISES_A_JOUR_WINDOWS = [
    {"id": "d-1", "titre": "2026-11 Mise à jour cumulative pour Windows 11 Version 25H2 (KB5072001)",
     "pilote": False, "facultatif": False, "taille": 812_000_000, "kb": "5072001"},
    {"id": "d-2", "titre": "Mise à jour de la plateforme antimalware Microsoft Defender (KB4052623)",
     "pilote": False, "facultatif": False, "taille": 14_000_000, "kb": "4052623"},
    {"id": "d-3", "titre": "Realtek Semiconductor Corp. - Extension - 6.0.9800.1",
     "pilote": True, "facultatif": False, "taille": 1_200_000, "kb": ""},
    {"id": "d-4", "titre": "Advanced Micro Devices, Inc. - System - 6.0.0.8",
     "pilote": True, "facultatif": True, "taille": 300_000, "kb": ""},
]

CARTES = [{"nom": "NVIDIA GeForce RTX 4070", "fabricant": "nvidia", "id_peripherique": "2786",
           "version_windows": "32.0.15.8120", "date": "2026-09-02"}]

RACCOURCIS_MORTS = [
    ("Bureau", "Ancien jeu.lnk", r"D:\Jeux\AncienJeu\jeu.exe"),
    ("Menu Démarrer", "Logiciel désinstallé.lnk", r"C:\Program Files\Logiciel\logiciel.exe"),
    ("Menu Démarrer", "Aide en ligne.lnk", r"C:\Program Files (x86)\Outil\aide.chm"),
]

MENAGE = {
    "temp_utilisateur": (1_850_000_000, 4210),
    "temp_windows": (420_000_000, 610),
    "rapports_erreurs": (95_000_000, 37),
    "optimisation_distribution": (2_300_000_000, 88),
    "telechargements_martinet": (0, 0),
    "composants": (None, None),
    "corbeille": (3_100_000_000, 152),
}

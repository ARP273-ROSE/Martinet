"""Logiciels payants : jamais de passage automatique à une nouvelle version principale.

Beaucoup de licences valent pour une version principale (6.x) : la 7 se rachète.
winget, lui, ne connaît que « la plus récente » et l'installe sans prévenir ; la
licence ne marche plus et le logiciel redemande une clé. Martinet retient donc ces
mises à jour : elles restent affichées, décochées, et ne partent qu'à la main.
Les mises à jour mineures (6.4 → 6.5) continuent de se faire toutes seules.
"""
from __future__ import annotations

from .versions import saut_majeur

# identifiants winget de logiciels vendus par version principale (liste de départ,
# complétée ou corrigée par l'utilisateur dans la page Programmes)
PAYANTS_DEFAUT = frozenset({
    "CrystalRich.USBSafelyRemove",
    "JAMSoftware.TreeSize",              # l'édition payante ; la gratuite est JAMSoftware.TreeSize.Free
    "OpenMedia.4KVideoDownloaderPlus",
    "LCTechnology.RescuePRO",
    "GuinpinSoft.MakeMKV",
    "ScooterSoftware.BeyondCompare4",
    "SublimeHQ.SublimeText.4",
    "SublimeHQ.SublimeMerge",
    "GPSoftware.DirectoryOpus",
})


def est_payant(id_winget: str, reglages) -> bool:
    if id_winget in reglages.payants_retires:
        return False
    return id_winget in PAYANTS_DEFAUT or id_winget in reglages.payants_ajoutes


def retenu(p, reglages) -> bool:
    """Mise à jour retenue : logiciel payant + nouvelle version principale, pas encore acceptée."""
    return (est_payant(p.id, reglages) and saut_majeur(p.installee, p.disponible)
            and f"{p.id}@{p.disponible}" not in reglages.majeures_acceptees)


def basculer(id_winget: str, reglages) -> bool:
    """Marque payant / pas payant ; renvoie le nouvel état."""
    if est_payant(id_winget, reglages):
        reglages.payants_ajoutes = [i for i in reglages.payants_ajoutes if i != id_winget]
        if id_winget in PAYANTS_DEFAUT and id_winget not in reglages.payants_retires:
            reglages.payants_retires = sorted({*reglages.payants_retires, id_winget})
        return False
    reglages.payants_retires = [i for i in reglages.payants_retires if i != id_winget]
    if id_winget not in PAYANTS_DEFAUT:
        reglages.payants_ajoutes = sorted({*reglages.payants_ajoutes, id_winget})
    return True

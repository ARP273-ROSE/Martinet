"""Windows Update par son interface officielle (Microsoft.Update.Session).

C'est celle qu'utilise Paramètres > Windows Update : mises à jour du système
ET pilotes publiés par les fabricants (chipset, Wi-Fi, audio…). Les mises à
jour « facultatives » (BrowseOnly) sont listées mais jamais cochées d'office.
L'installation demande les droits administrateur.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from . import demo, systeme


@dataclass
class MiseAJour:
    id: str
    titre: str
    pilote: bool
    facultatif: bool
    taille: int
    kb: str = ""


SCRIPT_RECHERCHE = r"""
$ErrorActionPreference = 'Stop'
$session = New-Object -ComObject Microsoft.Update.Session
$session.ClientApplicationID = 'Martinet'
$res = $session.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0")
$liste = foreach ($u in $res.Updates) {
    [pscustomobject]@{ id = [string]$u.Identity.UpdateID; titre = [string]$u.Title
        pilote = ($u.Type -eq 2); facultatif = [bool]$u.BrowseOnly
        taille = [int64]$u.MaxDownloadSize; kb = (@($u.KBArticleIDs) -join ',') }
}
'###JSON###'
ConvertTo-Json -InputObject @($liste) -Compress
"""

SCRIPT_INSTALLATION = r"""
$ErrorActionPreference = 'Stop'
$voulus = $env:MARTINET_MAJ -split ','
$session = New-Object -ComObject Microsoft.Update.Session
$session.ClientApplicationID = 'Martinet'
$res = $session.CreateUpdateSearcher().Search("IsInstalled=0 and IsHidden=0")
$lot = New-Object -ComObject Microsoft.Update.UpdateColl
foreach ($u in $res.Updates) {
    if ($voulus -contains [string]$u.Identity.UpdateID) {
        if (-not $u.EulaAccepted) { $u.AcceptEula() }
        [void]$lot.Add($u)
        Write-Output ("+ " + $u.Title)
    }
}
if ($lot.Count -eq 0) { '###JSON###'; '{"code":2,"redemarrer":false,"n":0}'; exit }
Write-Output 'TELECHARGEMENT'
$tele = $session.CreateUpdateDownloader(); $tele.Updates = $lot; [void]$tele.Download()
Write-Output 'INSTALLATION'
$inst = $session.CreateUpdateInstaller(); $inst.Updates = $lot
$r = $inst.Install()
$details = for ($i = 0; $i -lt $lot.Count; $i++) {
    [pscustomobject]@{ titre = [string]$lot.Item($i).Title; code = [int]$r.GetUpdateResult($i).ResultCode }
}
'###JSON###'
ConvertTo-Json -Compress -Depth 3 -InputObject ([pscustomobject]@{
    code = [int]$r.ResultCode; redemarrer = [bool]$r.RebootRequired; n = $lot.Count; details = @($details) })
"""

#: OperationResultCode de l'API Windows Update
CODES = {0: "non_commence", 1: "en_cours", 2: "reussi", 3: "reussi_erreurs", 4: "echec", 5: "annule"}


def rechercher(journal=None) -> list[MiseAJour]:
    if demo.actif():
        demo.pause(0.8)
        return [MiseAJour(**d) for d in demo.MISES_A_JOUR_WINDOWS]
    if journal:
        journal("Windows Update : recherche (une à deux minutes)…")
    code, sortie = systeme.powershell(SCRIPT_RECHERCHE, timeout=1800)
    donnees = systeme.json_de_sortie(sortie)
    if code != 0 or donnees is None:
        raise RuntimeError(sortie.strip()[-300:] or f"code {code}")
    return [MiseAJour(d["id"], d["titre"], bool(d["pilote"]), bool(d["facultatif"]),
                      int(d.get("taille") or 0), d.get("kb") or "") for d in systeme.en_liste(donnees)]


def installer(ids: list[str], journal=None, annulation=None) -> dict:
    """Installe les mises à jour choisies ; renvoie {code, redemarrer, n, details}."""
    if demo.actif():
        for i in ids:
            demo.pause(0.4)
            if journal:
                journal(f"+ {i}")
        return {"code": 2, "redemarrer": True, "n": len(ids), "details": []}
    import os
    os.environ["MARTINET_MAJ"] = ",".join(ids)
    code, sortie = systeme.powershell_flux(SCRIPT_INSTALLATION, journal, annulation, timeout=14400)
    donnees = systeme.json_de_sortie(sortie)
    if donnees is None:
        raise RuntimeError(sortie.strip()[-300:] or f"code {code}")
    return donnees


def mettre_a_jour_defender(journal=None) -> bool:
    if demo.actif():
        demo.pause(0.3)
        return True
    code, sortie = systeme.powershell("Update-MpSignature -ErrorAction Stop", timeout=600)
    if code != 0 and "0x800106ba" in sortie.lower():
        # service Defender arrêté : un autre antivirus est actif, ou Defender est désactivé
        if journal:
            from .i18n import tr
            journal(tr("journal.defender_inactif"))
        return True
    if journal and code != 0:
        journal(sortie.strip()[-200:])
    return code == 0


def decrire(resultat: dict) -> str:
    return CODES.get(int(resultat.get("code", 4)), "echec")


def vers_json(liste: list[MiseAJour]) -> str:
    return json.dumps([m.__dict__ for m in liste], ensure_ascii=False)

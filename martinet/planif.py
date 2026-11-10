"""Tâche planifiée Windows : Martinet passe tout seul (mode --auto).

Elle tourne sous le compte de l'utilisateur, avec les droits les plus
élevés (Windows Update et le ménage en ont besoin), seulement quand il est
connecté, et rattrape un passage manqué au démarrage suivant.
"""
from __future__ import annotations

from pathlib import Path

from . import demo, systeme

NOM_TACHE = "Martinet"
JOURS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def commande() -> tuple[str, str]:
    script = Path(__file__).resolve().parent.parent / "run.py"
    return systeme.executable_fenetre(), f'"{script}" --auto'


def _ps_texte(s: str) -> str:
    return "'" + s.replace("'", "''") + "'"


def creer(frequence: str, jour: int, heure: str) -> tuple[bool, str]:
    if demo.actif():
        return True, ""
    exe, args = commande()
    if frequence == "quotidien":
        declencheur = f"New-ScheduledTaskTrigger -Daily -At {_ps_texte(heure)}"
    else:
        declencheur = f"New-ScheduledTaskTrigger -Weekly -DaysOfWeek {JOURS[jour % 7]} -At {_ps_texte(heure)}"
    script = f"""
$ErrorActionPreference = 'Stop'
$a = New-ScheduledTaskAction -Execute {_ps_texte(exe)} -Argument {_ps_texte(args)}
$t = {declencheur}
$p = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Highest
$s = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 4)
Register-ScheduledTask -TaskName {_ps_texte(NOM_TACHE)} -Action $a -Trigger $t -Principal $p -Settings $s -Force | Out-Null
"""
    code, sortie = systeme.powershell(script, timeout=60)
    return code == 0, sortie.strip()[-300:]


def supprimer() -> tuple[bool, str]:
    if demo.actif():
        return True, ""
    code, sortie = systeme.powershell(
        f"Unregister-ScheduledTask -TaskName {_ps_texte(NOM_TACHE)} -Confirm:$false -ErrorAction Stop",
        timeout=60)
    return code == 0, sortie.strip()[-300:]


def etat() -> dict | None:
    """{active, prochaine, derniere, resultat} ou None si la tâche n'existe pas."""
    if demo.actif():
        return {"active": True, "prochaine": "2026-11-15T12:00:00", "derniere": "2026-11-08T12:00:41",
                "resultat": 0}
    script = f"""
$t = Get-ScheduledTask -TaskName {_ps_texte(NOM_TACHE)} -ErrorAction SilentlyContinue
if (-not $t) {{ '###JSON###'; 'null'; exit }}
$i = $t | Get-ScheduledTaskInfo
'###JSON###'
ConvertTo-Json -Compress -InputObject ([pscustomobject]@{{
  active = ($t.State -ne 'Disabled')
  prochaine = if ($i.NextRunTime) {{ $i.NextRunTime.ToString('s') }} else {{ '' }}
  derniere = if ($i.LastRunTime -and $i.LastRunTime.Year -gt 2000) {{ $i.LastRunTime.ToString('s') }} else {{ '' }}
  resultat = [int64]$i.LastTaskResult }})
"""
    code, sortie = systeme.powershell(script, timeout=60)
    donnees = systeme.json_de_sortie(sortie)
    return donnees if isinstance(donnees, dict) else None


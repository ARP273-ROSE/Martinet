"""Passage automatique de Martinet (mode --auto).

Windows : tâche planifiée sous le compte de l'utilisateur, avec les droits
les plus élevés (Windows Update et le ménage en ont besoin), seulement quand
il est connecté, et qui rattrape un passage manqué au démarrage suivant.

Linux : minuteur systemd de l'utilisateur (~/.config/systemd/user), sans
droit particulier ; « Persistent=true » rattrape un passage manqué.
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


# ------------------------------------------------------------ Linux : minuteur systemd
JOURS_SYSTEMD = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _dossier_systemd() -> Path:
    import os
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "systemd" / "user"


def unites_systemd(frequence: str, jour: int, heure: str) -> tuple[str, str]:
    """(martinet.service, martinet.timer)."""
    import re
    import shlex
    if not re.fullmatch(r"\d{1,2}:\d{2}", heure):
        heure = "12:00"
    exe, args = commande()
    script = args.strip().rsplit(" ", 1)[0].strip('"')
    service = ("[Unit]\nDescription=Martinet : passage automatique\n\n"
               "[Service]\nType=oneshot\n"
               f"ExecStart={shlex.quote(exe)} {shlex.quote(script)} --auto\n"
               "TimeoutStartSec=4h\nNice=10\n")
    quand = f"*-*-* {heure}:00" if frequence == "quotidien" else f"{JOURS_SYSTEMD[jour % 7]} *-*-* {heure}:00"
    timer = ("[Unit]\nDescription=Martinet : passage automatique\n\n"
             f"[Timer]\nOnCalendar={quand}\nPersistent=true\nRandomizedDelaySec=5min\n\n"
             "[Install]\nWantedBy=timers.target\n")
    return service, timer


def _systemctl(*args) -> tuple[int, str]:
    return systeme.executer(["systemctl", "--user", *args], timeout=60, env=systeme.ENV_C)


def _creer_linux(frequence: str, jour: int, heure: str) -> tuple[bool, str]:
    d = _dossier_systemd()
    d.mkdir(parents=True, exist_ok=True)
    service, timer = unites_systemd(frequence, jour, heure)
    (d / "martinet.service").write_text(service, encoding="utf-8")
    (d / "martinet.timer").write_text(timer, encoding="utf-8")
    _systemctl("daemon-reload")
    code, sortie = _systemctl("enable", "--now", "martinet.timer")
    return code == 0, sortie.strip()[-300:]


def _supprimer_linux() -> tuple[bool, str]:
    _systemctl("disable", "--now", "martinet.timer")
    for nom in ("martinet.timer", "martinet.service"):
        (_dossier_systemd() / nom).unlink(missing_ok=True)
    code, sortie = _systemctl("daemon-reload")
    return code == 0, sortie.strip()[-300:]


def _date_systemd(texte: str) -> str:
    """« Sun 2026-11-15 12:03:10 CET » → « 2026-11-15T12:03:10 »."""
    import re
    m = re.search(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})", texte or "")
    return f"{m.group(1)}T{m.group(2)}" if m else ""


def _etat_linux() -> dict | None:
    if not (_dossier_systemd() / "martinet.timer").exists():
        return None
    _c, t = _systemctl("show", "martinet.timer", "-p", "ActiveState", "-p", "NextElapseUSecRealtime",
                       "-p", "LastTriggerUSec")
    _c, s = _systemctl("show", "martinet.service", "-p", "Result")
    v = dict(l.split("=", 1) for l in (t + "\n" + s).splitlines() if "=" in l)
    return {"active": v.get("ActiveState") == "active",
            "prochaine": _date_systemd(v.get("NextElapseUSecRealtime", "")),
            "derniere": _date_systemd(v.get("LastTriggerUSec", "")),
            "resultat": 0 if v.get("Result", "success") == "success" else 1}


# ------------------------------------------------------------ Windows : tâche planifiée
def creer(frequence: str, jour: int, heure: str) -> tuple[bool, str]:
    if demo.actif():
        return True, ""
    if systeme.linux():
        return _creer_linux(frequence, jour, heure)
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
    if systeme.linux():
        return _supprimer_linux()
    code, sortie = systeme.powershell(
        f"Unregister-ScheduledTask -TaskName {_ps_texte(NOM_TACHE)} -Confirm:$false -ErrorAction Stop",
        timeout=60)
    return code == 0, sortie.strip()[-300:]


def etat() -> dict | None:
    """{active, prochaine, derniere, resultat} ou None si la tâche n'existe pas."""
    if demo.actif():
        return {"active": True, "prochaine": "2026-11-15T12:00:00", "derniere": "2026-11-08T12:00:41",
                "resultat": 0}
    if systeme.linux():
        return _etat_linux()
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


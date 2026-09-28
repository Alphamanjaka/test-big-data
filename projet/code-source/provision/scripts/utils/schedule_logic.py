#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Logique pure de planification du pipeline ELT (stdlib uniquement).

Ce module ne touche ni au disque ni au process : il calcule les échéances
(daily / weekly / monthly), les drapeaux de lancement et vérifie si une
échéance doit être déclenchée, à partir d'une config de planification.
Il est partagé entre :
  - provision/scripts/scheduler/scheduler.py (le planificateur du cron VM) ;
  - engine/governance/pipeline.py (API de la page /pipeline) ;
  - les tests (fraction pure).

Convention horaire : les heures sont exprimées dans le fuseau de la VM
(Indian/Antananarivo, UTC+3) et comparées à l'heure locale Python.
"""

from __future__ import annotations

import calendar
import datetime
from typing import Any, Dict, Optional, Tuple

# ---------------------------------------------------------------------------
# Validation de la configuration
# ---------------------------------------------------------------------------

FREQUENCIES = ("daily", "weekly", "monthly")
RESUME_MODES = ("auto", "since", "full")

DEFAULT_SCHEDULE: Dict[str, Any] = {
    "enabled": False,
    "frequency": "daily",
    "time": "03:00",
    "day_of_week": 0,     # lundi = 0 ... dimanche = 6 (ISO)
    "day_of_month": 1,    # 1..31 (borné au dernier jour du mois)
    "resume": {
        "mode": "auto",   # auto | since | full
        "since": None,    # date ISO "YYYY-MM-DD" si mode 'since'
    },
}


def validate_schedule(cfg: Any) -> Dict[str, Any]:
    """Valide et normalise une config de planification.

    Lève ValueError avec un message lisible si un champ est invalide ; sinon
    renvoie un dictionnaire normalisé (jamais partiellement accepté).
    """
    if not isinstance(cfg, dict):
        raise ValueError("La planification doit être un objet (clé/valeur).")

    enabled = bool(cfg.get("enabled", False))

    freq = cfg.get("frequency", "daily")
    if freq not in FREQUENCIES:
        raise ValueError(
            "frequency invalide (%s) — attendu : %s" % (freq, ", ".join(FREQUENCIES))
        )

    raw_time = str(cfg.get("time", "03:00"))
    parts = raw_time.strip().split(":")
    if len(parts) != 2:
        raise ValueError("time invalide (%s) — format attendu HH:MM" % raw_time)
    try:
        hour, minute = int(parts[0]), int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        raise ValueError("time invalide (%s) — Format attendu HH:MM" % raw_time)

    try:
        day_of_week = int(cfg.get("day_of_week", 0))
    except (TypeError, ValueError):
        raise ValueError("day_of_week doit être un entier (0=lundi..6=dimanche)")
    if not (0 <= day_of_week <= 6):
        raise ValueError("day_of_week hors bornes (0=lundi..6=dimanche)")

    try:
        day_of_month = int(cfg.get("day_of_month", 1))
    except (TypeError, ValueError):
        raise ValueError("day_of_month doit être un entier (1..31)")
    if not (1 <= day_of_month <= 31):
        raise ValueError("day_of_month hors bornes (1..31)")

    resume = cfg.get("resume") or {}
    mode = resume.get("mode", "auto")
    if mode not in RESUME_MODES:
        raise ValueError(
            "resume.mode invalide (%s) — attendu : %s" % (mode, ", ".join(RESUME_MODES))
        )
    since = resume.get("since")
    if mode == "since":
        try:
            since_dt = datetime.datetime.strptime(str(since or ""), "%Y-%m-%d")
        except (ValueError, TypeError):
            raise ValueError(
                "resume.since requis et au format YYYY-MM-DD si resume.mode = since"
            )
        since = since_dt.date().isoformat()
    else:
        since = since if since else None

    return {
        "enabled": enabled,
        "frequency": freq,
        "time": "%02d:%02d" % (hour, minute),
        "day_of_week": day_of_week,
        "day_of_month": day_of_month,
        "resume": {"mode": mode, "since": since},
    }


# ---------------------------------------------------------------------------
# Calcul d'occurrences (temps local, fuseau de la VM)
# ---------------------------------------------------------------------------


def _split_time(time: str) -> Tuple[int, int]:
    hh, mm = time.split(":")
    return int(hh), int(mm)


def _occurrence(day: datetime.date, time: str) -> datetime.datetime:
    hh, mm = _split_time(time)
    return datetime.datetime(day.year, day.month, day.day, hh, mm)


def _last_day(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _candidate(now: datetime.datetime, cfg: Dict[str, Any]) -> datetime.datetime:
    """Occurrence 'candidate' de la période en cours pour current/next slot."""
    freq = cfg["frequency"]
    time = cfg["time"]
    if freq == "daily":
        return _occurrence(now.date(), time)
    if freq == "weekly":
        days_ahead = (int(cfg["day_of_week"]) - now.weekday()) % 7
        return _occurrence(now.date() + datetime.timedelta(days=days_ahead), time)
    # monthly
    day = min(int(cfg["day_of_month"]), _last_day(now.year, now.month))
    return _occurrence(now.date().replace(day=day), time)


def current_slot(now: datetime.datetime, cfg: Dict[str, Any]) -> Optional[datetime.datetime]:
    """Dernière échéance passée ≤ now (None si aucune encore dans la période)."""
    candidate = _candidate(now, cfg)
    if candidate <= now:
        return candidate
    if cfg["frequency"] == "daily":
        return None
    if cfg["frequency"] == "weekly":
        return candidate - datetime.timedelta(days=7)
    prev_month = now.month - 1 or 12
    prev_year = now.year if now.month > 1 else now.year - 1
    day = min(int(cfg["day_of_month"]), _last_day(prev_year, prev_month))
    return _occurrence(datetime.date(prev_year, prev_month, day), cfg["time"])


def next_slot(now: datetime.datetime, cfg: Dict[str, Any]) -> datetime.datetime:
    """Prochaine échéance à venir (> now), pour affichage."""
    candidate = _candidate(now, cfg)
    if candidate > now:
        return candidate
    if cfg["frequency"] == "daily":
        return candidate + datetime.timedelta(days=1)
    if cfg["frequency"] == "weekly":
        return candidate + datetime.timedelta(days=7)
    # monthly : mois suivant
    next_month = now.month % 12 + 1
    next_year = now.year + (1 if now.month == 12 else 0)
    day = min(int(cfg["day_of_month"]), _last_day(next_year, next_month))
    return _occurrence(datetime.date(next_year, next_month, day), cfg["time"])


# ---------------------------------------------------------------------------
# Décision de lancement et drapeaux
# ---------------------------------------------------------------------------


def should_launch(
    scheduler_state: Dict[str, Any], now: datetime.datetime, cfg: Dict[str, Any]
) -> Tuple[bool, str, Optional[datetime.datetime]]:
    """Décide si le pipeline doit être déclenché maintenant.

    Renvoie (lance, raison, slot) : le lancement n'a lieu que si la planification
    est active, si l'échéance courante est atteinte et si cette échéance exacte
    n'a pas déjà été déclenchée (`last_launched_slot`).
    """
    if not cfg.get("enabled", False):
        return False, "planification désactivée", None
    slot = current_slot(now, cfg)
    if slot is None:
        return False, "échéance non encore atteinte", None
    last = scheduler_state.get("last_launched_slot")
    if last:
        try:
            last_dt = datetime.datetime.fromisoformat(str(last))
        except ValueError:
            last_dt = None
        if last_dt is not None and last_dt >= slot:
            return False, "échéance déjà déclenchée (%s)" % slot.isoformat(), slot
    return True, "échéance atteinte", slot


def build_run_flags(cfg: Dict[str, Any]) -> list:
    """Drapeaux passés à run_pipeline.sh selon resume.mode."""
    mode = (cfg.get("resume") or {}).get("mode", "auto")
    if mode == "full":
        return ["--full"]
    if mode == "since":
        since = (cfg.get("resume") or {}).get("since")
        if since:
            return ["--since", str(since)]
    return ["--resume"]
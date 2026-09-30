#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Planificateur du pipeline ELT — déclenche run_pipeline.sh selon schedule.yaml.

Le cron VM exécute une vérification chaque minute :
    python -m provision.scripts.scheduler.scheduler --check

Le pipeline n'est lancé que si :
  1. la planification est active (enabled: true dans schedule.yaml) ;
  2. l'échéance (fréquence + heure) vient d'être atteinte et n'a pas déjà été
     déclenchée (état persisté dans scheduler_runs.json) ;
  3. aucun run n'est en cours (pipeline_state.json ne doit pas être `running`) ;
     un run `running` orphelin (processus disparu, VM redémarrée) est d'abord
     marqué en échec, sinon la planification resterait bloquée.

Le lancement se fait en arrière-plan (start_new_session) : le cron revient
aussitôt, le pipeline continue indépendamment et met à jour son propre état.

CLI :
    --check      vérifie l'échéance et lance le pipeline en arrière-plan
    --status     résumé lisible (plan, prochaine échéance, dernier lancement)
    --dry-run    simule --check sans rien lancer ni écrire

Chemins surridables par variables d'environnement (tests) :
    SCHEDULE_PATH, SCHEDULER_STATE_PATH, PIPELINE_STATE_PATH,
    RUN_PIPELINE_CMD
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import subprocess

from provision.scripts.utils import pipeline_state, schedule_logic
from provision.scripts.utils.watermark import load as load_watermark

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", ".."))

DEFAULT_SCHEDULE_PATH = os.path.join(
    PROJECT_ROOT, "provision", "config", "schedule.yaml"
)
DEFAULT_SCHEDULER_STATE_PATH = os.path.join(
    PROJECT_ROOT, "provision", "metadata", "scheduler_runs.json"
)
DEFAULT_RUN_PIPELINE_CMD = [
    "/bin/bash",
    os.path.join(PROJECT_ROOT, "provision", "scripts", "run_pipeline.sh"),
]

_NULL_SCALARS = ("null", "none", "~")


def schedule_path() -> str:
    return os.environ.get("SCHEDULE_PATH") or DEFAULT_SCHEDULE_PATH


def scheduler_state_path() -> str:
    return os.environ.get("SCHEDULER_STATE_PATH") or DEFAULT_SCHEDULER_STATE_PATH


def pipeline_state_path() -> str:
    return os.environ.get("PIPELINE_STATE_PATH") or os.path.join(
        PROJECT_ROOT, "provision", "metadata", "pipeline_state.json"
    )


def _yaml_load_safe(stream):
    """Mini-lecteur YAML des champs utilisés (sans dépendance PyYAML).

    Le planificateur tourne dans l'environnement de la VM où PyYAML peut
    manquer : on ne lit que les clés scalaires de schedule.yaml (mêmes résultats
    que le fichier d'exemple). Le lecteur est volontairement limité, la
    validation reste dans schedule_logic.validate_schedule.
    """
    cfg = {}
    for raw in stream.read().splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value and value[0] in "\"'":
            value = value[1:-1].strip()
        if key == "resume":
            continue  # section : seule ses sous-clés scalaires sont lues
        cfg.setdefault("resume", {})
        if key == "enabled":
            cfg["enabled"] = value.lower() in ("true", "yes", "1")
        elif key == "frequency":
            cfg["frequency"] = value
        elif key == "time":
            cfg["time"] = value
        elif key == "day_of_week":
            cfg["day_of_week"] = int(value) if value else 0
        elif key == "day_of_month":
            cfg["day_of_month"] = int(value) if value else 1
        elif key == "mode":
            cfg["resume"]["mode"] = value
        elif key == "since":
            cfg["resume"]["since"] = None if value.lower() in _NULL_SCALARS else value
    if "resume" not in cfg:
        cfg["resume"] = {}
    return cfg


def load_schedule(path: str = None) -> dict:
    """Charge schedule.yaml ; si absent ou illisible, planification désactivée."""
    path = path or schedule_path()
    if not os.path.exists(path):
        return dict(schedule_logic.DEFAULT_SCHEDULE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = dict(schedule_logic.DEFAULT_SCHEDULE)
            cfg.update(_yaml_load_safe(f))
        return schedule_logic.validate_schedule(cfg)
    except Exception as exc:  # fichier illisible -> décision prudente : ne pas lancer
        print("WARN: schedule.yaml illisible (%s) — planification désactivée" % exc)
        return dict(schedule_logic.DEFAULT_SCHEDULE)


def load_scheduler_state(path: str = None) -> dict:
    path = path or scheduler_state_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_scheduler_state(state: dict, path: str = None) -> str:
    path = path or scheduler_state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return path


def pipeline_is_running() -> bool:
    path = pipeline_state_path()
    state = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, ValueError):
            state = {}
    return state.get("status") == "running"


def reconcile_orphan_run(alive=None, boot_id=None) -> bool:
    """Marque en échec un run resté `running` dont le processus a disparu."""
    path = pipeline_state_path()
    state = pipeline_state.load(path)
    if not state or not pipeline_state.reconcile(state, alive=alive, boot_id=boot_id):
        return False
    pipeline_state.save(state, path)
    print("Run %s orphelin (processus absent) : marqué en échec." % state.get("run_id"))
    return True


def run_pipeline_cmd() -> list:
    if os.environ.get("RUN_PIPELINE_CMD"):
        return list(os.environ["RUN_PIPELINE_CMD"].split(" "))
    return DEFAULT_RUN_PIPELINE_CMD


def launch(flags: list, log_dir: str = None) -> int:
    """Lance run_pipeline.sh en arrière-plan (détaché du cron)."""
    cmd = run_pipeline_cmd() + list(flags)
    log_dir = log_dir or os.path.join(PROJECT_ROOT, "provision", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "scheduler_launch.log")
    with open(log_file, "ab") as log:
        kwargs = {"stdout": log, "stderr": subprocess.STDOUT}
        if os.name == "posix":
            kwargs["start_new_session"] = True  # détaché du cron
        proc = subprocess.Popen(cmd, cwd=PROJECT_ROOT, **kwargs)
    return proc.pid


def _human(now: datetime.datetime, cfg: dict) -> str:
    slot = schedule_logic.current_slot(now, cfg)
    nxt = schedule_logic.next_slot(now, cfg)
    return "échéance courante: %s | prochaine: %s" % (
        slot.isoformat() if slot else "—",
        nxt.isoformat(),
    )


def check(now: datetime.datetime = None) -> int:
    now = now or datetime.datetime.now()
    cfg = load_schedule()

    if not cfg.get("enabled"):
        print("Planification désactivée (schedule.yaml) — rien à lancer.")
        return 0

    reconcile_orphan_run()
    if pipeline_is_running():
        print("Un run pipeline est déjà en cours (status=running) — pas de lancement.")
        return 0

    state = load_scheduler_state()
    launch_now, reason, slot = schedule_logic.should_launch(state, now, cfg)
    if not launch_now:
        print("Aucun lancement : %s (%s)" % (reason, _human(now, cfg)))
        return 0

    flags = schedule_logic.build_run_flags(cfg)
    pid = launch(flags)
    state["last_launched_slot"] = slot.isoformat()
    state["last_launch_at"] = now.replace(microsecond=0).isoformat()
    state["last_pid"] = pid
    runs = state.setdefault("runs", [])
    runs.append(
        {
            "at": state["last_launch_at"],
            "slot": state["last_launched_slot"],
            "flags": flags,
            "pid": pid,
        }
    )
    state["runs"] = runs[-20:]
    save_scheduler_state(state)
    print("✅ Échéance atteinte → run lancé (pid %s, drapeaux: %s)" % (pid, " ".join(flags)))
    return 0


def status() -> int:
    cfg = load_schedule()
    now = datetime.datetime.now()
    state = load_scheduler_state()
    flags = schedule_logic.build_run_flags(cfg)
    watermark = load_watermark()
    print("Plan (schedule.yaml):")
    print("  enabled: %s | fréquence: %s | heure: %s" % (
        cfg.get("enabled"), cfg.get("frequency"), cfg.get("time")))
    if cfg.get("frequency") == "weekly":
        print("  jour de semaine: %s" % cfg.get("day_of_week"))
    if cfg.get("frequency") == "monthly":
        print("  jour du mois: %s" % cfg.get("day_of_month"))
    print("  resume.mode: %s (since: %s)" % (
        cfg.get("resume", {}).get("mode"), cfg.get("resume", {}).get("since")))
    print("  drapeaux au prochain lancement: %s" % " ".join(flags))
    print("  " + _human(now, cfg))
    print("Dernier déclenchement (scheduler_runs.json):")
    print("  slot: %s | à: %s | pid: %s" % (
        state.get("last_launched_slot"), state.get("last_launch_at"),
        state.get("last_pid")))
    print("Pipeline en cours: %s" % pipeline_is_running())
    print("Tables suivies (watermark.json): %s sources" % len(watermark))
    return 0


def dry_run(now: datetime.datetime = None) -> int:
    now = now or datetime.datetime.now()
    cfg = load_schedule()
    launch_now, reason, _slot = schedule_logic.should_launch(
        load_scheduler_state(), now, cfg
    )
    flags = schedule_logic.build_run_flags(cfg)
    print("Mode dry-run — aucun lancement ni écriture.")
    print("  enabled: %s | fréquence: %s | heure: %s" % (
        cfg.get("enabled"), cfg.get("frequency"), cfg.get("time")))
    print("  would_launch: %s (%s)" % (launch_now, reason))
    print("  flags: %s" % " ".join(flags))
    print("  " + _human(now, cfg))
    return 0


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Planificateur du pipeline ELT.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="vérifie et lance si échéance")
    group.add_argument("--status", action="store_true", help="résumé de la planification")
    group.add_argument("--dry-run", action="store_true", help="simulation sans effets")
    args = parser.parse_args(argv)
    if args.check:
        return check()
    if args.status:
        return status()
    return dry_run()


if __name__ == "__main__":
    raise SystemExit(cli())
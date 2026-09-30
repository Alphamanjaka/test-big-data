#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline_state.py — mémoire de reprise d'un run ELT.

Fichier runtime : provision/metadata/pipeline_state.json (jamais versionné).

Le pipeline (run_pipeline.sh) perd sa mémoire entre deux invocations : si une
étape échoue, la prochaine exécution doit pouvoir reprendre là où elle s'est
arrêtée au lieu de tout rejouer. Ce module persiste, pour chaque run :

    run_id, status (running|ok|failed), mode, from_step, started_at,
    finished_at, statut par étape (pending|started|ok|failed),
    dernière étape OK / dernière étape en échec.

CLI (utilisée par run_pipeline.sh) :
    python -m provision.scripts.utils.pipeline_state begin --mode resume \
        [--start-at gen_extract_raw] [--since 2026-01-01] [--run-id ...]
    python -m provision.scripts.utils.pipeline_state step started <étape>
    python -m provision.scripts.utils.pipeline_state step ok <étape>
    python -m provision.scripts.utils.pipeline_state step failed <étape> [erreur]
    python -m provision.scripts.utils.pipeline_state finish ok|failed
    python -m provision.scripts.utils.pipeline_state show
    python -m provision.scripts.utils.pipeline_state resume_start
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", ".."))
DEFAULT_STATE_PATH = os.path.join(
    PROJECT_ROOT, "provision", "metadata", "pipeline_state.json"
)

# Ordre canonique des étapes (commun à run_pipeline.sh et aux helpers).
STEPS = [
    "ensure_generator_data",
    "gen_extract_raw",
    "gen_fhir_mapping",
    "create_silver",
    "create_gold",
]


def _now_iso() -> str:
    # Heure avec son fuseau (la VM est en UTC, l'hôte en UTC+3) : sans lui, la base
    # centrale interprétait l'heure de la VM comme une heure locale de l'hôte.
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def state_path() -> str:
    return os.environ.get("PIPELINE_STATE_PATH") or DEFAULT_STATE_PATH


def load(path: str = None) -> dict:
    path = path or state_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(state: dict, path: str = None) -> str:
    path = path or state_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    return path


def new_state(
    run_id: str,
    mode: str,
    since: str = None,
    from_step: str = None,
    start_at: int = 0,
) -> dict:
    """État initial d'un run : les étapes précédant `start_at` sont héritées OK."""
    steps = {}
    for i, step in enumerate(STEPS):
        steps[step] = "ok" if i < start_at else "pending"
    return {
        "run_id": run_id,
        "status": "running",
        "mode": mode,
        "from_step": from_step,
        "ingest_since": since,
        "started_at": _now_iso(),
        "finished_at": None,
        "steps": steps,
        "last_ok_step": STEPS[start_at - 1] if start_at > 0 else None,
        "last_failed_step": None,
        "last_error": None,
    }


def is_running(state: dict) -> bool:
    return state.get("status") == "running"


def resume_start(state: dict) -> str:
    """Nom de la première étape non 'ok' (à reprendre), ou ''."""
    steps = state.get("steps") or {}
    for step in STEPS:
        if steps.get(step) != "ok":
            return step
    return ""


def mark_step(state: dict, status: str, step: str, error: str = None) -> None:
    if status == "ok":
        state["steps"][step] = "ok"
        state["last_ok_step"] = step
    elif status == "failed":
        state["steps"][step] = "failed"
        state["last_failed_step"] = step
        state["last_error"] = error
    else:  # started
        state["steps"][step] = "started"


def finish(state: dict, status: str) -> None:
    state["status"] = status
    state["finished_at"] = _now_iso()


def _index_of(step: str) -> int:
    if step not in STEPS:
        raise ValueError(
            "étape inconnue (%s) — une des : %s" % (step, ", ".join(STEPS))
        )
    return STEPS.index(step)


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="État d'un run ELT (reprise).")
    sub = parser.add_subparsers(dest="action", required=True)

    p_begin = sub.add_parser("begin", help="nouveau run")
    p_begin.add_argument("--mode", required=True, choices=["resume", "full", "since", "from"])
    p_begin.add_argument("--since")
    p_begin.add_argument("--from", dest="from_step")
    p_begin.add_argument("--start-at", dest="start_at", type=int, default=0)
    p_begin.add_argument("--run-id")

    p_step = sub.add_parser("step", help="statut d'une étape")
    p_step.add_argument("status", choices=["started", "ok", "failed"])
    p_step.add_argument("step")
    p_step.add_argument("error", nargs="?", default=None)

    p_fin = sub.add_parser("finish", help="statut final du run")
    p_fin.add_argument("status", choices=["ok", "failed"])

    sub.add_parser("show", help="affiche l'état JSON")
    sub.add_parser("resume_start", help="première étape non 'ok'")

    args = parser.parse_args(argv)

    if args.action == "begin":
        start_at = args.start_at
        if args.from_step and start_at == 0:
            start_at = _index_of(args.from_step)
        state = new_state(
            run_id=args.run_id or datetime.now().strftime("%Y%m%dT%H%M%S"),
            mode=args.mode,
            since=args.since,
            from_step=args.from_step,
            start_at=start_at,
        )
        print(save(state))
        return 0

    if args.action == "step":
        state = load()
        if not state:
            print("ERREUR: aucun run démarré (begin attendu)", file=os.sys.stderr)
            return 1
        mark_step(state, args.status, args.step, args.error)
        save(state)
        return 0

    if args.action == "finish":
        state = load()
        if not state:
            print("ERREUR: aucun run démarré (begin attendu)", file=os.sys.stderr)
            return 1
        finish(state, args.status)
        save(state)
        return 0

    if args.action == "show":
        print(json.dumps(load(), ensure_ascii=False, indent=2))
        return 0

    if args.action == "resume_start":
        print(resume_start(load()))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(cli())
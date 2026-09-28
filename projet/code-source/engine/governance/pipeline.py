"""engine/governance/pipeline.py — planification et état du pipeline ELT.

Point d'entrée de la page /pipeline (front-optional) et miroir du
planificateur : les fichiers lus/écrits vivent dans le dossier partagé
hôte<->VM, lisible par l'API hôte comme par le cron VM.

    provision/config/schedule.yaml          plan (le cron VM le lit)
    provision/metadata/pipeline_state.json  état du run courant/dernier
    provision/metadata/watermark.json       empreintes d'ingestion (anti-boucle)
    provision/metadata/sync_metadata.json   état des zones Medallion
    provision/metadata/scheduler_runs.json  derniers déclenchements du cron

Le moteur dépend de PyYAML (déclaré) : lecture/écriture YAML ici, alors que le
planificateur VM (provision/scripts/scheduler) garde son mini-lecteur sans
dépendance.

Les chemins sont surridables par variables d'environnement (tests) :
PIPELINE_CONFIG_DIR, PIPELINE_METADATA_DIR, SCHEDULE_PATH,
PIPELINE_STATE_PATH, PIPELINE_WATERMARK_PATH, SCHEDULER_STATE_PATH.
"""

from __future__ import annotations

import datetime
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from provision.scripts.utils import schedule_logic

ROOT = Path(__file__).resolve().parents[2]


def _env(key: str, default: str) -> str:
    return os.environ.get(key) or default


def config_dir() -> Path:
    return Path(_env("PIPELINE_CONFIG_DIR", str(ROOT / "provision" / "config")))


def metadata_dir() -> Path:
    return Path(_env("PIPELINE_METADATA_DIR", str(ROOT / "provision" / "metadata")))


def schedule_path() -> Path:
    return Path(_env("SCHEDULE_PATH", str(config_dir() / "schedule.yaml")))


def state_path() -> Path:
    return Path(_env("PIPELINE_STATE_PATH", str(metadata_dir() / "pipeline_state.json")))


def watermark_path() -> Path:
    return Path(_env("PIPELINE_WATERMARK_PATH", str(metadata_dir() / "watermark.json")))


def scheduler_state_path() -> Path:
    return Path(
        _env("SCHEDULER_STATE_PATH", str(metadata_dir() / "scheduler_runs.json"))
    )


def sync_metadata_path() -> Path:
    return metadata_dir() / "sync_metadata.json"


def _read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def load_schedule() -> Dict[str, Any]:
    """Charge et valide schedule.yaml ; absent -> planification désactivée.

    Lève ValueError si le fichier est invalide (remontée dans /pipeline/status).
    """
    if not schedule_path().exists():
        return dict(schedule_logic.DEFAULT_SCHEDULE)
    import yaml

    with open(schedule_path(), "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return schedule_logic.validate_schedule(data)


def save_schedule(cfg: Any) -> Dict[str, Any]:
    """Valide puis écrit schedule.yaml (fichier lu par le cron VM)."""
    normalized = schedule_logic.validate_schedule(cfg)
    path = schedule_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    import yaml

    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            normalized,
            f,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        )
    return normalized


def _source_summary(tables: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(tables, dict):
        return None
    table_count = 0
    last_extracted_at = None
    for entry in tables.values():
        if not isinstance(entry, dict):
            continue
        last = entry.get("last") or {}
        table_count += 1
        ts = last.get("extracted_at")
        if ts and (last_extracted_at is None or ts > last_extracted_at):
            last_extracted_at = ts
    return {"tables": table_count, "last_extracted_at": last_extracted_at}


def read_status() -> Dict[str, Any]:
    """État complet pour la page /pipeline : plan, prochain run, sources."""
    now = datetime.datetime.now()
    schedule_error = None
    try:
        cfg = load_schedule()
    except ValueError as exc:
        cfg = dict(schedule_logic.DEFAULT_SCHEDULE)
        schedule_error = str(exc)

    scheduler = _read_json(scheduler_state_path())
    sources = {}
    for source, tables in _read_json(watermark_path()).items():
        summary = _source_summary(tables)
        if summary is not None:
            sources[source] = summary

    return {
        "schedule": cfg,
        "schedule_error": schedule_error,
        "next_run": schedule_logic.next_slot(now, cfg).isoformat(),
        "run_flags": schedule_logic.build_run_flags(cfg),
        "pipeline": _read_json(state_path()),
        "scheduler": {
            "last_launched_slot": scheduler.get("last_launched_slot"),
            "last_launch_at": scheduler.get("last_launch_at"),
            "runs": (scheduler.get("runs") or [])[-5:],
        },
        "zones": _read_json(sync_metadata_path()),
        "sources": sources,
    }
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_metrics.py — historique chiffré des runs ELT, conservé en base.

`pipeline_state.json` ne garde que le dernier run, sans compteurs. Ce module
répond à une autre question : « le run du 07/09 a lu combien de lignes dans
chaque source, et combien de patients maîtres en sont sortis ? ».

Deux temps, pour ne jamais faire échouer le pipeline à cause de la base :

1. Pendant le run, chaque étape dépose ses compteurs dans un tampon local
   (provision/metadata/run_metrics.json, jamais versionné), rangé par run_id
   (variable PIPELINE_RUN_ID exportée par run_pipeline.sh) :
       gen_extract_raw -> lignes extraites / sautées par source
       create_silver   -> lignes SILVER, patients maîtres distincts, doublons
       create_gold     -> lignes GOLD (événements, consentements)
2. En fin de run (succès ou échec), `flush` enregistre chaque run en attente
   dans PostgreSQL (tables pipeline_run et pipeline_run_source de
   sql/schema.sql) si DATABASE_URL est définie. Un run enregistré quitte le
   tampon ; sinon il y reste et sera enregistré au prochain flush.

CLI (utilisée par run_pipeline.sh) :
    python -m provision.scripts.utils.run_metrics flush
    python -m provision.scripts.utils.run_metrics show
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from typing import Any, Dict, Iterable, List, Optional

from . import pipeline_state

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", ".."))
DEFAULT_METRICS_PATH = os.path.join(
    PROJECT_ROOT, "provision", "metadata", "run_metrics.json"
)

# Clé utilisée quand une étape est lancée à la main, hors run_pipeline.sh.
MANUAL_RUN_ID = "manual"


def metrics_path() -> str:
    return os.environ.get("PIPELINE_RUN_METRICS_PATH") or DEFAULT_METRICS_PATH


def current_run_id() -> str:
    return os.environ.get("PIPELINE_RUN_ID") or MANUAL_RUN_ID


# ---------------------------------------------------------------------------
# Tampon local
# ---------------------------------------------------------------------------
def load(path: str = None) -> Dict[str, Any]:
    path = path or metrics_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(buffer: Dict[str, Any], path: str = None) -> str:
    path = path or metrics_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(buffer, f, indent=2, ensure_ascii=False, default=str)
    return path


def record(step: str, data: Dict[str, Any], run_id: str = None) -> None:
    """Dépose les compteurs d'une étape dans le tampon du run courant."""
    buffer = load()
    run = buffer.setdefault(run_id or current_run_id(), {})
    run[step] = data
    save(buffer)


def record_safely(step: str, data: Dict[str, Any], logger=None) -> None:
    """`record` qui ne lève jamais : un compteur perdu ne doit pas casser l'ELT."""
    try:
        record(step, data)
    except Exception as exc:  # noqa: BLE001 — l'étape ELT prime sur l'historique
        if logger is not None:
            logger.warning(f"Historique du run non enregistré ({step}) : {exc}")


# ---------------------------------------------------------------------------
# Résumés calculés par les étapes
# ---------------------------------------------------------------------------
def summarize_extract(report: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, int]]:
    """Résumé par source du rapport d'extraction (extract_raw_report.json).

    Une table sautée (empreinte inchangée) n'a pas été relue : ses lignes sont
    comptées à part (`rows_skipped`), jamais comme des lignes extraites.
    """
    summary = {}
    for source, tables in (report or {}).items():
        entry = {
            "tables_extracted": 0,
            "tables_skipped": 0,
            "tables_failed": 0,
            "rows_extracted": 0,
            "rows_skipped": 0,
        }
        for table in tables or []:
            if not isinstance(table, dict):
                continue
            rows = table.get("row_count") or 0
            if "error" in table:
                entry["tables_failed"] += 1
            elif table.get("skipped"):
                entry["tables_skipped"] += 1
                entry["rows_skipped"] += int(rows)
            else:
                entry["tables_extracted"] += 1
                entry["rows_extracted"] += int(rows)
        summary[source] = entry
    return summary


def summarize_dedup(decisions: Iterable[Any]) -> Dict[str, Any]:
    """Compteurs SILVER à partir des décisions du moteur (MatchDecision).

    `master_count` compte les patients maîtres DISTINCTS, pas les lignes
    rattachées à un maître.
    """
    decisions = list(decisions)
    methods = Counter(d.method for d in decisions)
    rows = len(decisions)
    duplicates = rows - methods.get("new_master", 0)
    return {
        "silver_rows": rows,
        "master_count": len({d.master_patient_id for d in decisions}),
        "duplicate_count": duplicates,
        "exact_count": methods.get("exact", 0),
        "probabilistic_count": methods.get("probabilistic", 0),
        "duplicate_rate": round(duplicates * 100.0 / rows, 2) if rows else 0.0,
        "rows_by_source": dict(Counter(d.source_system for d in decisions)),
    }


# ---------------------------------------------------------------------------
# Enregistrement en base
# ---------------------------------------------------------------------------
RUN_COLUMNS = (
    "run_id", "mode", "status", "started_at", "finished_at", "failed_step",
    "silver_rows", "master_count", "duplicate_count", "exact_count",
    "probabilistic_count", "duplicate_rate", "gold_event_rows",
    "gold_consent_rows",
)

SOURCE_COLUMNS = (
    "run_id", "source_system", "tables_extracted", "tables_skipped",
    "tables_failed", "rows_extracted", "rows_skipped", "silver_patient_rows",
)

_UPSERT_RUN = (
    "INSERT INTO pipeline_run (" + ", ".join(RUN_COLUMNS) + ") VALUES ("
    + ", ".join(["%s"] * len(RUN_COLUMNS)) + ") "
    "ON CONFLICT (run_id) DO UPDATE SET "
    + ", ".join(f"{c} = EXCLUDED.{c}" for c in RUN_COLUMNS[1:])
)

_UPSERT_SOURCE = (
    "INSERT INTO pipeline_run_source (" + ", ".join(SOURCE_COLUMNS) + ") VALUES ("
    + ", ".join(["%s"] * len(SOURCE_COLUMNS)) + ") "
    "ON CONFLICT (run_id, source_system) DO UPDATE SET "
    + ", ".join(f"{c} = EXCLUDED.{c}" for c in SOURCE_COLUMNS[2:])
)


def build_record(run_id: str, steps: Dict[str, Any], state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Assemble la ligne `pipeline_run` et ses lignes `pipeline_run_source`."""
    state = state or {}
    run_info = steps.get("run") or {}
    silver = steps.get("create_silver") or {}
    gold = steps.get("create_gold") or {}
    extract = (steps.get("gen_extract_raw") or {}).get("sources") or {}

    status = run_info.get("status") or "running"
    if status not in ("running", "ok", "failed"):
        status = "running"
    run = {
        "run_id": run_id,
        "mode": run_info.get("mode") or "manual",
        "status": status,
        "started_at": run_info.get("started_at"),
        "finished_at": run_info.get("finished_at"),
        "failed_step": run_info.get("failed_step"),
        "silver_rows": silver.get("silver_rows"),
        "master_count": silver.get("master_count"),
        "duplicate_count": silver.get("duplicate_count"),
        "exact_count": silver.get("exact_count"),
        "probabilistic_count": silver.get("probabilistic_count"),
        "duplicate_rate": silver.get("duplicate_rate"),
        "gold_event_rows": gold.get("gold_event_rows"),
        "gold_consent_rows": gold.get("gold_consent_rows"),
    }

    silver_by_source = silver.get("rows_by_source") or {}
    sources = []
    for name in sorted(set(extract) | set(silver_by_source)):
        counts = extract.get(name) or {}
        sources.append({
            "run_id": run_id,
            "source_system": name,
            "tables_extracted": counts.get("tables_extracted", 0),
            "tables_skipped": counts.get("tables_skipped", 0),
            "tables_failed": counts.get("tables_failed", 0),
            "rows_extracted": counts.get("rows_extracted", 0),
            "rows_skipped": counts.get("rows_skipped", 0),
            "silver_patient_rows": silver_by_source.get(name),
        })
    return {"run": run, "sources": sources}


def save_record(conn, rec: Dict[str, Any]) -> None:
    """Écrit un run et ses sources (idempotent : un run réenregistré est mis à jour)."""
    with conn.cursor() as cur:
        cur.execute(_UPSERT_RUN, tuple(rec["run"][c] for c in RUN_COLUMNS))
        for src in rec["sources"]:
            cur.execute(_UPSERT_SOURCE, tuple(src[c] for c in SOURCE_COLUMNS))
    conn.commit()


def attach_state(buffer: Dict[str, Any], state: Dict[str, Any]) -> None:
    """Recopie l'état du run courant (statut, dates, étape en échec) dans le tampon."""
    run_id = state.get("run_id")
    if not run_id:
        return
    buffer.setdefault(run_id, {})["run"] = {
        "mode": state.get("mode"),
        "status": state.get("status"),
        "started_at": state.get("started_at"),
        "finished_at": state.get("finished_at"),
        "failed_step": state.get("last_failed_step"),
    }


def _connect():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return None
    import psycopg

    return psycopg.connect(database_url)


def flush(connect=_connect, out=sys.stdout) -> int:
    """Enregistre en base les runs du tampon ; ne fait jamais échouer le pipeline.

    Retourne le nombre de runs enregistrés.
    """
    buffer = load()
    attach_state(buffer, pipeline_state.load())
    # Les compteurs d'une étape lancée à la main n'appartiennent à aucun run :
    # ils restent dans le tampon, consultables, mais ne sont pas enregistrés.
    pending = sorted(r for r in buffer if r != MANUAL_RUN_ID)
    if not pending:
        save(buffer)
        return 0

    try:
        conn = connect()
    except Exception as exc:  # noqa: BLE001
        conn = None
        print(f"Historique des runs : base injoignable ({exc}) — conservé en attente.", file=out)
    if conn is None:
        save(buffer)
        print(
            f"Historique des runs : DATABASE_URL absente ou base injoignable — "
            f"{len(pending)} run(s) en attente dans {metrics_path()}.",
            file=out,
        )
        return 0

    saved = 0
    try:
        for run_id in pending:
            try:
                save_record(conn, build_record(run_id, buffer[run_id]))
            except Exception as exc:  # noqa: BLE001
                print(f"Historique du run {run_id} non enregistré : {exc}", file=out)
                continue
            saved += 1
            buffer.pop(run_id)
    finally:
        conn.close()
        save(buffer)
    print(f"Historique des runs : {saved} run(s) enregistré(s) en base.", file=out)
    return saved


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Historique chiffré des runs ELT.")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("flush", help="enregistre en base les runs en attente")
    sub.add_parser("show", help="affiche le tampon local")
    args = parser.parse_args(argv)

    if args.action == "flush":
        flush()
        return 0
    if args.action == "show":
        print(json.dumps(load(), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(cli())

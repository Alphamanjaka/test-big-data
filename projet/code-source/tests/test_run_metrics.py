"""Tests de l'historique chiffré des runs (provision/scripts/utils/run_metrics.py).

Aucune base réelle : le tampon local pointe vers un dossier temporaire et la
connexion PostgreSQL est remplacée par une fausse connexion qui enregistre les
requêtes. Les décisions du moteur sont reproduites par de simples objets.
"""

import io
import json
import sys
from collections import namedtuple
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from provision.scripts.utils import run_metrics  # noqa: E402

Decision = namedtuple("Decision", "master_patient_id source_system method")


@pytest.fixture
def run_env(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPELINE_RUN_METRICS_PATH", str(tmp_path / "run_metrics.json"))
    monkeypatch.setenv("PIPELINE_STATE_PATH", str(tmp_path / "pipeline_state.json"))
    monkeypatch.setenv("PIPELINE_RUN_ID", "20260907T030000")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    return tmp_path


class RecordingCursor:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        self.log.append((query, params))


class RecordingConnection:
    def __init__(self):
        self.statements = []
        self.committed = False
        self.closed = False

    def cursor(self):
        return RecordingCursor(self.statements)

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def _state(status="ok"):
    return {
        "run_id": "20260907T030000",
        "status": status,
        "mode": "full",
        "started_at": "2026-09-07T03:00:00",
        "finished_at": "2026-09-07T03:12:00",
        "last_failed_step": "create_gold" if status == "failed" else None,
        "steps": {},
    }


# --- Résumés ---

def test_summarize_extract_separates_extracted_skipped_and_failed():
    report = {
        "pharmacy": [
            {"table_name": "patients", "row_count": 76},
            {"table_name": "purchases", "row_count": 120, "skipped": True},
        ],
        "imaging": [
            {"table_name": "patients", "row_count": 62},
            {"table_name": "exams", "error": "fichier introuvable"},
        ],
    }
    summary = run_metrics.summarize_extract(report)
    assert summary["pharmacy"] == {
        "tables_extracted": 1, "tables_skipped": 1, "tables_failed": 0,
        "rows_extracted": 76, "rows_skipped": 120,
    }
    assert summary["imaging"]["rows_extracted"] == 62
    assert summary["imaging"]["tables_failed"] == 1


def test_summarize_dedup_counts_distinct_masters_not_rows():
    # Cas du run de référence en miniature : 3 lignes, 2 patients maîtres.
    decisions = [
        Decision("M1", "pharmacy", "new_master"),
        Decision("M1", "consultation", "exact"),
        Decision("M2", "imaging", "new_master"),
    ]
    summary = run_metrics.summarize_dedup(decisions)
    assert summary["silver_rows"] == 3
    assert summary["master_count"] == 2
    assert summary["duplicate_count"] == 1
    assert summary["exact_count"] == 1
    assert summary["probabilistic_count"] == 0
    assert summary["duplicate_rate"] == 33.33
    assert summary["rows_by_source"] == {"pharmacy": 1, "consultation": 1, "imaging": 1}


def test_summarize_dedup_empty():
    summary = run_metrics.summarize_dedup([])
    assert summary["silver_rows"] == 0 and summary["duplicate_rate"] == 0.0


# --- Tampon local ---

def test_record_groups_steps_by_run_id(run_env):
    run_metrics.record("create_gold", {"gold_event_rows": 0, "gold_consent_rows": 145})
    run_metrics.record("create_silver", {"master_count": 145})
    buffer = run_metrics.load()
    assert set(buffer) == {"20260907T030000"}
    assert buffer["20260907T030000"]["create_silver"]["master_count"] == 145


def test_record_safely_never_raises(run_env, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disque plein")

    monkeypatch.setattr(run_metrics, "record", boom)
    run_metrics.record_safely("create_silver", {})  # ne lève pas


# --- Assemblage et écriture en base ---

def test_build_record_merges_extract_and_silver_per_source():
    steps = {
        "run": {"mode": "full", "status": "ok", "started_at": "2026-09-07T03:00:00"},
        "gen_extract_raw": {"sources": {"pharmacy": {"tables_extracted": 1, "rows_extracted": 76}}},
        "create_silver": {
            "silver_rows": 214, "master_count": 145, "duplicate_count": 69,
            "exact_count": 69, "probabilistic_count": 0, "duplicate_rate": 32.24,
            "rows_by_source": {"pharmacy": 76, "consultation": 76},
        },
        "create_gold": {"gold_event_rows": 0, "gold_consent_rows": 145},
    }
    rec = run_metrics.build_record("R1", steps)
    assert rec["run"]["master_count"] == 145
    assert rec["run"]["gold_consent_rows"] == 145
    by_source = {s["source_system"]: s for s in rec["sources"]}
    assert by_source["pharmacy"]["rows_extracted"] == 76
    assert by_source["pharmacy"]["silver_patient_rows"] == 76
    # Source vue en SILVER mais absente du rapport d'extraction : zéros, pas d'erreur.
    assert by_source["consultation"]["rows_extracted"] == 0


def test_build_record_unknown_status_falls_back_to_running():
    rec = run_metrics.build_record("R1", {"run": {"status": "bizarre"}})
    assert rec["run"]["status"] == "running"


def test_save_record_upserts_run_then_sources():
    conn = RecordingConnection()
    rec = run_metrics.build_record("R1", {
        "run": {"mode": "full", "status": "ok"},
        "gen_extract_raw": {"sources": {"a": {}, "b": {}}},
    })
    run_metrics.save_record(conn, rec)
    queries = [q for q, _ in conn.statements]
    assert queries[0].startswith("INSERT INTO pipeline_run (")
    assert "ON CONFLICT (run_id) DO UPDATE" in queries[0]
    assert sum(q.startswith("INSERT INTO pipeline_run_source") for q in queries) == 2
    assert conn.committed


# --- flush ---

def test_flush_without_database_keeps_runs_pending(run_env):
    run_metrics.record("create_silver", {"master_count": 145})
    (run_env / "pipeline_state.json").write_text(json.dumps(_state()), encoding="utf-8")
    out = io.StringIO()
    saved = run_metrics.flush(out=out)
    assert saved == 0
    buffer = run_metrics.load()
    assert "20260907T030000" in buffer
    assert buffer["20260907T030000"]["run"]["status"] == "ok"
    assert "en attente" in out.getvalue()


def test_flush_saves_runs_and_empties_buffer(run_env):
    run_metrics.record("create_silver", {"master_count": 145, "silver_rows": 214})
    (run_env / "pipeline_state.json").write_text(json.dumps(_state("failed")), encoding="utf-8")
    conn = RecordingConnection()
    saved = run_metrics.flush(connect=lambda: conn, out=io.StringIO())
    assert saved == 1
    assert conn.closed
    params = conn.statements[0][1]
    record = dict(zip(run_metrics.RUN_COLUMNS, params))
    assert record["status"] == "failed"
    assert record["failed_step"] == "create_gold"
    assert record["master_count"] == 145
    assert run_metrics.load() == {}


def test_flush_ignores_manual_step_counters(run_env, monkeypatch):
    monkeypatch.delenv("PIPELINE_RUN_ID")
    run_metrics.record("create_silver", {"master_count": 3})
    conn = RecordingConnection()
    saved = run_metrics.flush(connect=lambda: conn, out=io.StringIO())
    assert saved == 0
    assert conn.statements == []
    assert run_metrics.MANUAL_RUN_ID in run_metrics.load()


def test_flush_unreachable_database_keeps_buffer(run_env):
    run_metrics.record("create_silver", {"master_count": 145})
    (run_env / "pipeline_state.json").write_text(json.dumps(_state()), encoding="utf-8")

    def refuse():
        raise ConnectionError("connexion refusée")

    out = io.StringIO()
    assert run_metrics.flush(connect=refuse, out=out) == 0
    assert "20260907T030000" in run_metrics.load()
    assert "injoignable" in out.getvalue()

"""Tests des endpoints /pipeline/* de l'API gouvernance FastAPI.

La planification est un fichier partagé (schedule.yaml) : les tests le pointent
vers un dossier temporaire et passent par le vrai chemin d'authentification
(Bearer clé API -> get_current_user -> require_role). Aucune base réelle, aucun
fichier projet modifié.
"""

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.governance.app import app


class FakeCursor:
    def __init__(self, fetch_results=None):
        self._results = fetch_results or []
        self._idx = 0
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, parameters=None):
        self.executed.append((query, parameters))

    def fetchone(self):
        if self._idx < len(self._results):
            row = self._results[self._idx]
            self._idx += 1
            return row
        return None

    def fetchall(self):
        remaining = self._results[self._idx:]
        self._idx = len(self._results)
        return remaining


class FakeConnection:
    def __init__(self, fetch_results=None):
        self._fetch_results = fetch_results or []
        self.closed = False
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self, row_factory=None):
        return FakeCursor(fetch_results=self._fetch_results)

    def close(self):
        self.closed = True

    def commit(self):
        self.committed = True


def _mock_factory(results=None):
    def factory():
        return FakeConnection(fetch_results=results or [])
    return factory


def _patch_auth(monkeypatch, user_row):
    monkeypatch.setattr(
        "engine.governance.auth.connection_factory", _mock_factory([user_row])
    )


ADMIN_ROW = (1, "test_admin", "admin")
ANALYST_ROW = (3, "test_analyst", "analyst")
VIEWER_ROW = (2, "test_viewer", "viewer")
_HEADERS = {"Authorization": "Bearer cle-de-test"}


@pytest.fixture
def pipeline_env(tmp_path, monkeypatch):
    """Point la planification/état/wartermark vers des fichiers temporaires."""
    monkeypatch.setenv("PIPELINE_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("PIPELINE_METADATA_DIR", str(tmp_path / "metadata"))
    (tmp_path / "config").mkdir(exist_ok=True)
    (tmp_path / "metadata").mkdir(exist_ok=True)
    return tmp_path


@pytest.fixture
def audit_sink(monkeypatch):
    statements = []

    class AuditConnection(FakeConnection):
        def cursor(self, row_factory=None):
            cursor = FakeCursor()
            original_execute = cursor.execute

            def execute(query, parameters=None):
                statements.append((query, parameters))
                return original_execute(query, parameters)

            cursor.execute = execute
            return cursor

    monkeypatch.setattr(
        "engine.governance.audit.connection_factory", lambda: AuditConnection()
    )
    return statements


def _write_schedule(tmp_path, cfg):
    path = tmp_path / "config" / "schedule.yaml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(cfg, encoding="utf-8")
    return path


# --- Lecture (admin / analyst) ---

def test_get_schedule_default_when_no_file(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    client = TestClient(app)
    resp = client.get("/pipeline/schedule", headers=_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False


def test_get_schedule_readable_by_analyst(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ANALYST_ROW)
    client = TestClient(app)
    resp = client.get("/pipeline/schedule", headers=_HEADERS)
    assert resp.status_code == 200


def test_get_schedule_denied_for_viewer(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, VIEWER_ROW)
    client = TestClient(app)
    resp = client.get("/pipeline/schedule", headers=_HEADERS)
    assert resp.status_code == 403


# --- Écriture (admin uniquement) ---

def test_put_schedule_writes_file(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    client = TestClient(app)
    payload = {
        "enabled": True,
        "frequency": "weekly",
        "time": "05:30",
        "day_of_week": 2,
        "day_of_month": 1,
        "resume": {"mode": "auto", "since": None},
    }
    resp = client.put("/pipeline/schedule", json=payload, headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert body["enabled"] is True
    assert body["frequency"] == "weekly"
    assert body["time"] == "05:30"

    schedule_file = pipeline_env / "config" / "schedule.yaml"
    assert schedule_file.exists(), "le fichier partagé doit être écrit"
    raw = schedule_file.read_text(encoding="utf-8")
    assert "enabled: true" in raw

    # Lecture : la config persistée est bien renvoyée.
    resp2 = client.get("/pipeline/schedule", headers=_HEADERS)
    assert resp2.json()["frequency"] == "weekly"


def test_put_schedule_rejects_invalid(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    client = TestClient(app)
    resp = client.put(
        "/pipeline/schedule",
        json={"enabled": True, "frequency": "yearly", "time": "03:00"},
        headers=_HEADERS,
    )
    assert resp.status_code == 422
    assert "frequency" in resp.json()["detail"]


def test_put_schedule_denied_for_analyst(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ANALYST_ROW)
    client = TestClient(app)
    resp = client.put("/pipeline/schedule", json={}, headers=_HEADERS)
    assert resp.status_code == 403


# --- État du pipeline ---

def test_pipeline_status_empty(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    client = TestClient(app)
    resp = client.get("/pipeline/status", headers=_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "schedule" in data and "sources" in data and "zones" in data
    assert data["sources"] == {}  # watermark absent -> aucune source


def test_pipeline_status_with_watermark(pipeline_env, monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ANALYST_ROW)
    watermark = {
        "pharmacy": {
            "patients": {
                "last": {
                    "signature": "abc",
                    "row_count": 500,
                    "extracted_at": "2026-09-28T03:00:00",
                }
            }
        }
    }
    (pipeline_env / "metadata" / "watermark.json").write_text(
        json.dumps(watermark), encoding="utf-8"
    )
    client = TestClient(app)
    resp = client.get("/pipeline/status", headers=_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["sources"]["pharmacy"]["tables"] == 1
    assert resp.json()["sources"]["pharmacy"]["last_extracted_at"] == "2026-09-28T03:00:00"

# --- Historique des runs (base PostgreSQL) ---

class _RunsCursor(FakeCursor):
    """Renvoie un jeu de lignes par requête : runs, puis sources."""

    def __init__(self, batches):
        super().__init__()
        self._batches = list(batches)

    def fetchall(self):
        return self._batches.pop(0) if self._batches else []


class _RunsConnection(FakeConnection):
    def __init__(self, batches):
        super().__init__()
        self._batches = batches

    def cursor(self, row_factory=None):
        return _RunsCursor(self._batches)


def _run_row(run_id, started_at, masters):
    # Ordre de engine.governance.pipeline.RUN_FIELDS.
    return (run_id, "full", "ok", started_at, None, None, 214, masters, 69, 69, 0,
            32.24, 0, 145, started_at)


def test_pipeline_runs_returns_history_with_sources(monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ANALYST_ROW)
    runs = [_run_row("20260907T030000", "2026-09-07T03:00:00", 145)]
    sources = [
        ("20260907T030000", "consultation", 1, 0, 0, 76, 0, 76),
        ("20260907T030000", "pharmacy", 1, 0, 0, 76, 0, 76),
    ]
    monkeypatch.setattr(
        "engine.governance.app.connection_factory",
        lambda: _RunsConnection([runs, sources]),
    )
    client = TestClient(app)
    resp = client.get("/pipeline/runs", headers=_HEADERS)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["master_count"] == 145
    assert body[0]["duplicate_rate"] == 32.24
    assert [s["source_system"] for s in body[0]["sources"]] == ["consultation", "pharmacy"]
    assert body[0]["sources"][1]["rows_extracted"] == 76


def test_pipeline_runs_empty_history(monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    monkeypatch.setattr(
        "engine.governance.app.connection_factory", lambda: _RunsConnection([[]])
    )
    client = TestClient(app)
    resp = client.get("/pipeline/runs", headers=_HEADERS)
    assert resp.status_code == 200
    assert resp.json() == []


def test_pipeline_runs_denied_for_viewer(monkeypatch, audit_sink):
    _patch_auth(monkeypatch, VIEWER_ROW)
    client = TestClient(app)
    resp = client.get("/pipeline/runs", headers=_HEADERS)
    assert resp.status_code == 403

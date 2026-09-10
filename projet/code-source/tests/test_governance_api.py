"""Tests de l'API gouvernance FastAPI — fausses connexions PostgreSQL."""

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

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

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self, row_factory=None):
        return FakeCursor(fetch_results=self._fetch_results)

    def close(self):
        pass

    def commit(self):
        pass


def _mock_factory(results=None):
    def factory():
        return FakeConnection(fetch_results=results or [])
    return factory


_FAKE_USER = SimpleNamespace(user_id=1, username="test_admin", role="admin")


def _override_auth():
    """Bypass get_current_user : renvoie un admin directement."""
    from engine.governance.auth import get_current_user
    async def fake_get_current_user():
        return _FAKE_USER
    app.dependency_overrides[get_current_user] = fake_get_current_user


def _clear_auth_overrides():
    app.dependency_overrides.clear()


# --- Tests sans auth (health) ---

def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# --- Tests avec auth mockée ---

def test_metrics():
    _override_auth()
    fake = _mock_factory(results=[(100,), (15,)])
    with patch("engine.governance.app.connection_factory", fake), \
         patch("engine.governance.audit.connection_factory", _mock_factory()):
        client = TestClient(app)
        resp = client.get("/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_patients"] == 100
        assert data["duplicates"] == 15
        assert data["duplicate_rate"] == 15.0
    _clear_auth_overrides()


def test_list_patients():
    _override_auth()
    rows = [("PAT-0001", "pharmacy", False), ("PAT-0002", "consultation", True)]
    fake = _mock_factory(results=rows)
    with patch("engine.governance.app.connection_factory", fake), \
         patch("engine.governance.audit.connection_factory", _mock_factory()):
        client = TestClient(app)
        resp = client.get("/patients")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["master_patient_id"] == "PAT-0001"
    _clear_auth_overrides()


def test_get_patient_not_found():
    _override_auth()
    fake = _mock_factory(results=[None])
    with patch("engine.governance.app.connection_factory", fake), \
         patch("engine.governance.audit.connection_factory", _mock_factory()):
        client = TestClient(app)
        resp = client.get("/patients/PAT-9999")
        assert resp.status_code == 404
    _clear_auth_overrides()

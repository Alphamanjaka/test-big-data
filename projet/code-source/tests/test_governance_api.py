"""Tests de l'API gouvernance FastAPI — fausses connexions PostgreSQL.

Les tests n'imitent plus l'authentification par `dependency_overrides` : ils
passent par le vrai chemin `Authorization: Bearer <clé API>` -> `get_current_user`
-> `require_role`, afin que 401, 403 et refus de consentement soient réellement
couverts. Seul le transport PostgreSQL est simulé.
"""

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


ADMIN_ROW = (1, "test_admin", "admin")
VIEWER_ROW = (2, "test_viewer", "viewer")
_HEADERS = {"Authorization": "Bearer cle-de-test"}


@pytest.fixture
def audit_sink(monkeypatch):
    """Capture les INSERT journalisés par AuditMiddleware."""
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


def _patch_db(monkeypatch, results):
    """Route la connexion de l'API gouvernance vers une fausse base."""
    monkeypatch.setattr("engine.governance.app.connection_factory", _mock_factory(results))


def _patch_auth(monkeypatch, user_row):
    """Fait résoudre une clé API vers `user_row` par le vrai chemin d'authentification."""
    monkeypatch.setattr(
        "engine.governance.auth.connection_factory", _mock_factory([user_row])
    )


def _patch_consent(monkeypatch, granted_rows):
    """Fixe la réponse de la requête de consentement (lignes `granted`)."""
    monkeypatch.setattr(
        "engine.governance.consent.connection_factory",
        _mock_factory(granted_rows),
    )


# --- Sans authentification ---

def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_missing_token_returns_401(audit_sink):
    """Aucun Bearer : 401 — le refus est journalisé avec username=anonymous."""
    client = TestClient(app)
    resp = client.get("/patients", params={"purpose": "research"})
    assert resp.status_code == 401
    assert "manquant" in resp.json()["detail"]
    assert audit_sink, "le refus 401 doit etre journalise"
    _, parameters = audit_sink[0]
    assert "anonymous" in parameters


def test_unknown_api_key_returns_401(monkeypatch, audit_sink):
    """Clé inconnue : 401 — la resolution via api_user echoue proprement."""
    _patch_auth(monkeypatch, None)
    client = TestClient(app)
    resp = client.get("/patients", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 401
    assert "invalide" in resp.json()["detail"]


def test_role_insufficient_returns_403(monkeypatch, audit_sink):
    """Rôle viewer sur un endpoint admin : 403 — require_role est bien execute."""
    _patch_auth(monkeypatch, VIEWER_ROW)
    client = TestClient(app)
    resp = client.get("/audit", headers=_HEADERS)
    assert resp.status_code == 403
    assert "admin" in resp.json()["detail"]


# --- Authentification reelle (admin) ---

def test_metrics(monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_db(monkeypatch, [(100,), (15,)])
    client = TestClient(app)
    resp = client.get("/metrics", headers=_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_patients"] == 100
    assert data["duplicates"] == 15
    assert data["duplicate_rate"] == 15.0


def test_list_patients(monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [
        {"master_patient_id": "PAT-0001", "granted": True},
        {"master_patient_id": "PAT-0002", "granted": True},
    ])
    _patch_db(monkeypatch, [("PAT-0001", "pharmacy", False), ("PAT-0002", "consultation", True)])
    client = TestClient(app)
    resp = client.get("/patients", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert [row["master_patient_id"] for row in data] == ["PAT-0001", "PAT-0002"]


def test_list_patients_filters_without_consent(monkeypatch, audit_sink):
    """Seuls les patients ayant consenti a la finalite sont renvoyes."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [
        {"master_patient_id": "PAT-0001", "granted": True},
        {"master_patient_id": "PAT-0003", "granted": False},
    ])
    _patch_db(monkeypatch, [
        ("PAT-0001", "pharmacy", False),
        ("PAT-0002", "consultation", True),
        ("PAT-0003", "imaging", False),
    ])
    client = TestClient(app)
    resp = client.get("/patients", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 200
    assert [row["master_patient_id"] for row in resp.json()] == ["PAT-0001"]
    # le nombre de patients filtres est trace
    reasons = [p[7] for q, p in audit_sink if "INSERT INTO access_audit" in q]
    assert any("2 patient(s) filtres" in (r or "") for r in reasons)


def test_list_patients_requires_purpose(monkeypatch, audit_sink):
    """Sans finalite declaree : 422 — la finalite est obligatoire."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_db(monkeypatch, [])
    client = TestClient(app)
    resp = client.get("/patients", headers=_HEADERS)
    assert resp.status_code == 422


def test_unknown_purpose_rejected_422(monkeypatch, audit_sink):
    """Une finalite hors liste fermee est refusee (et jamais acceptee « au passage »)."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [])
    client = TestClient(app)
    resp = client.get("/patients/PAT-0001", params={"purpose": "marketing"}, headers=_HEADERS)
    assert resp.status_code == 422
    assert "api_access" in resp.json()["detail"]


def test_get_patient_not_found(monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [{"granted": True}])
    _patch_db(monkeypatch, [None])
    client = TestClient(app)
    resp = client.get("/patients/PAT-9999", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 404


def test_get_patient_allowed(monkeypatch, audit_sink):
    """Consentement accorde : le detail est servi et le motif de refus est vide."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [{"granted": True}])
    _patch_db(monkeypatch, [("PAT-0001", "pharmacy", False)])
    client = TestClient(app)
    resp = client.get("/patients/PAT-0001", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["master_patient_id"] == "PAT-0001"
    reasons = [p[7] for q, p in audit_sink if "INSERT INTO access_audit" in q]
    assert None in reasons


def test_get_patient_denied_without_consent(monkeypatch, audit_sink):
    """Role autorise mais finalite non consentie : 403 ET refus journalise.

    C'est le test qui distingue une mécanique de consentement réellement câblée
    d'un simple contrôle de rôle : il échoue si `enforce_consent` est retiré
    de la route.
    """
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [{"granted": False}])
    _patch_db(monkeypatch, [("PAT-0001", "pharmacy", False)])
    client = TestClient(app)
    resp = client.get("/patients/PAT-0001", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 403
    assert "consentement non accorde" in resp.json()["detail"]

    inserts = [(q, p) for q, p in audit_sink if "INSERT INTO access_audit" in q]
    assert inserts, "le refus doit etre journalise"
    query, parameters = inserts[0]
    assert parameters[4] == 403, "le statut HTTP du refus est journalise"
    assert parameters[6] == "research", "la finalite declaree est journalisee"
    assert "consentement non accorde" in parameters[7]


def test_audit_endpoint_returns_accessed_at(monkeypatch, audit_sink):
    """Régression : l'endpoint /audit interroge `accessed_at` (colonne réelle).

    Le schéma définit `accessed_at` ; une requête sur `recorded_at` échouerait
    sur une vraie base alors que les faux curseurs la laisseraient passer.
    """
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_db(monkeypatch, [
        (1, "test_admin", "/patients", "GET", 403, "127.0.0.1",
         "research", "consentement non accorde", "2026-09-27 10:00:00+00")
    ])
    client = TestClient(app)
    resp = client.get("/audit", headers=_HEADERS)
    assert resp.status_code == 200
    row = resp.json()[0]
    assert row["accessed_at"] == "2026-09-27 10:00:00+00"
    assert row["purpose"] == "research"
    assert row["refusal_reason"] == "consentement non accorde"

"""Tests du module consentement (gouvernance) — fausses connexions."""

import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.governance.consent import (
    PURPOSES,
    ConsentCreate,
    check_consent,
    consented_master_ids,
    create_consent,
    enforce_consent,
    list_consents,
    validate_purpose,
)


class FakeCursor:
    def __init__(self, fetch_result=None):
        self.fetch_result = fetch_result
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, parameters=None):
        self.executed.append((query, parameters))

    def fetchone(self):
        return self.fetch_result

    def fetchall(self):
        return self.fetch_result or []


class FakeConnection:
    def __init__(self, fetch_result=None):
        self._fetch = fetch_result
        self.cursor_instance = None
        self.committed = False
        self.closed = False

    def cursor(self, row_factory=None):
        self.cursor_instance = FakeCursor(self._fetch)
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def _fake_context(user):
    from types import SimpleNamespace
    return SimpleNamespace(username=user, user_id=1, role="admin")


def test_list_consents_admin(monkeypatch):
    conn = FakeConnection([{"consent_id": 1, "purpose": "api_access", "granted": True}])
    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "connection_factory", lambda: conn)

    result = list_consents(_fake_context("admin"))
    assert result == [{"consent_id": 1, "purpose": "api_access", "granted": True}]
    assert conn.closed is True


def test_create_consent_requires_existing_patient(monkeypatch):
    conn = FakeConnection(None)
    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "connection_factory", lambda: conn)

    with pytest.raises(HTTPException) as exc:
        create_consent(
            ConsentCreate(master_patient_id="NOPE", purpose="api_access", granted=True),
            _fake_context("admin"),
        )
    assert exc.value.status_code == 404


def test_create_consent_persists(monkeypatch):
    calls = []

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, q, p=None):
            calls.append((q, p))

        def fetchone(self):
            return None

    class Conn:
        def __init__(self):
            self.committed = False
            self.closed = False
            self._cursor = Cursor()

        def cursor(self, row_factory=None):
            return self._cursor

        def commit(self):
            self.committed = True

        def close(self):
            self.closed = True

    conn = Conn()
    from engine.governance import consent as consent_module
    real_query_one = consent_module._query_one

    def factory():
        return conn

    def patched_query_one(query, parameters=()):
        if "FROM master_patient" in query:
            return {"master_patient_id": "PAT-0001"}
        return real_query_one(query, parameters)

    monkeypatch.setattr(consent_module, "connection_factory", factory)
    monkeypatch.setattr(consent_module, "_query_one", patched_query_one)

    result = create_consent(
        ConsentCreate(master_patient_id="PAT-0001", purpose="research", granted=True),
        _fake_context("admin"),
    )
    assert result["status"] == "created"
    assert conn.committed is True
    assert any("INSERT INTO consent" in q for q, _ in calls)


# --- Finalités normalisées (liste fermée) ---


def test_purposes_are_the_normalized_three():
    assert PURPOSES == ("api_access", "research", "analytics")


@pytest.mark.parametrize("purpose", PURPOSES)
def test_validate_purpose_accepts_known(purpose):
    assert validate_purpose(purpose) == purpose


@pytest.mark.parametrize("purpose", ["marketing", "API_ACCESS", "", "research ", "donnees_sante"])
def test_validate_purpose_rejects_unknown(purpose):
    with pytest.raises(HTTPException) as exc:
        validate_purpose(purpose)
    assert exc.value.status_code == 422
    assert "api_access" in exc.value.detail


def test_create_consent_rejects_unknown_purpose(monkeypatch):
    """Un consentement hors liste fermée est refusé avant écriture."""
    calls = []

    class Cursor:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def execute(self, q, p=None):
            calls.append((q, p))

        def fetchone(self):
            return None

    class Conn:
        def cursor(self, row_factory=None):
            return Cursor()

        def close(self):
            pass

    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "connection_factory", lambda: Conn())
    monkeypatch.setattr(
        consent_module,
        "_query_one",
        lambda q, p=(): {"master_patient_id": "PAT-0001"},
    )

    with pytest.raises(HTTPException) as exc:
        create_consent(
            ConsentCreate(master_patient_id="PAT-0001", purpose="marketing", granted=True),
            _fake_context("admin"),
        )
    assert exc.value.status_code == 422
    assert not any("INSERT INTO consent" in q for q, _ in calls)


# --- Application du consentement (refus par défaut) ---


def test_check_consent_granted(monkeypatch):
    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "_query_one", lambda q, p=(): {"granted": True})
    assert check_consent("PAT-0001", "research") is True


def test_check_consent_refused(monkeypatch):
    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "_query_one", lambda q, p=(): {"granted": False})
    assert check_consent("PAT-0001", "research") is False


def test_check_consent_missing_row_is_refused(monkeypatch):
    """Absence de ligne = refus (fail closed), pas accord implicite."""
    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "_query_one", lambda q, p=(): None)
    assert check_consent("PAT-0001", "research") is False


def test_consented_master_ids_keeps_only_granted(monkeypatch):
    from engine.governance import consent as consent_module
    monkeypatch.setattr(
        consent_module,
        "_query_all",
        lambda q, p=(): [
            {"master_patient_id": "PAT-0001", "granted": True},
            {"master_patient_id": "PAT-0002", "granted": False},
            {"master_patient_id": "PAT-0003", "granted": True},
        ],
    )
    assert consented_master_ids("research") == {"PAT-0001", "PAT-0003"}


def test_consented_master_ids_rejects_unknown_purpose(monkeypatch):
    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "_query_all", lambda q, p=(): [])
    with pytest.raises(HTTPException) as exc:
        consented_master_ids("marketing")
    assert exc.value.status_code == 422


def test_enforce_consent_allows_and_records_purpose(monkeypatch):
    from types import SimpleNamespace

    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "_query_one", lambda q, p=(): {"granted": True})
    request = SimpleNamespace(state=SimpleNamespace())
    assert enforce_consent(request, "PAT-0001", "research") == "research"
    assert request.state.purpose == "research"
    assert request.state.refusal_reason is None


def test_enforce_consent_refuses_and_records_reason(monkeypatch):
    from types import SimpleNamespace

    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "_query_one", lambda q, p=(): None)
    request = SimpleNamespace(state=SimpleNamespace())
    with pytest.raises(HTTPException) as exc:
        enforce_consent(request, "PAT-0001", "analytics")
    assert exc.value.status_code == 403
    assert "consentement non accorde" in exc.value.detail
    # l'audit doit pouvoir expliquer le refus
    assert request.state.purpose == "analytics"
    assert "analytics" in request.state.refusal_reason


def test_enforce_consent_refuses_unknown_purpose(monkeypatch):
    from types import SimpleNamespace

    from engine.governance import consent as consent_module
    monkeypatch.setattr(consent_module, "_query_one", lambda q, p=(): {"granted": True})
    request = SimpleNamespace(state=SimpleNamespace())
    with pytest.raises(HTTPException) as exc:
        enforce_consent(request, "PAT-0001", "marketing")
    assert exc.value.status_code == 422

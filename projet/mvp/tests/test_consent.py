import pytest
from fastapi import HTTPException

from patient_platform.api.consent import create_consent, list_consents
from patient_platform.api.consent import ConsentCreate


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

    from patient_platform.api import consent as consent_module
    monkeypatch.setattr(consent_module, "connection_factory", lambda: conn)

    result = list_consents(_fake_context("admin"))
    assert result == [{"consent_id": 1, "purpose": "api_access", "granted": True}]
    assert conn.closed is True


def test_create_consent_requires_existing_patient(monkeypatch):
    conn = FakeConnection(None)
    from patient_platform.api import consent as consent_module
    monkeypatch.setattr(consent_module, "connection_factory", lambda: conn)

    with pytest.raises(HTTPException) as exc:
        create_consent(ConsentCreate(master_patient_id="NOPE", purpose="api_access", granted=True), _fake_context("admin"))
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

    # first lookup (patient) returns None -> must be a patient, so simulate two queries
    def factory():
        return conn

    from patient_platform.api import consent as consent_module
    # override _query_one to simulate patient exists on first call
    real_query_one = consent_module._query_one

    def patched_query_one(query, parameters=()):
        if "FROM master_patient" in query:
            return {"master_patient_id": "PAT-0001"}
        return real_query_one(query, parameters)

    monkeypatch.setattr(consent_module, "connection_factory", factory)
    monkeypatch.setattr(consent_module, "_query_one", patched_query_one)

    result = create_consent(ConsentCreate(master_patient_id="PAT-0001", purpose="research", granted=True), _fake_context("admin"))
    assert result["status"] == "created"
    assert conn.committed is True
    assert any("INSERT INTO consent" in q for q, _ in calls)

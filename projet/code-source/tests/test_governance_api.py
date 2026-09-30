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
    def __init__(self, default=None, query_map=None):
        self.executed = []
        self._query_map = query_map or {}
        self._default = list(default if default is not None else [])
        self._state = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def _route(self, query):
        for key, rows in self._query_map.items():
            if key in query:
                return key
        return None

    def _rows_of(self, key):
        return self._query_map.get(key) if key is not None else self._default

    def execute(self, query, parameters=None):
        self.executed.append((query, parameters))
        key = self._route(query)
        if key not in self._state:
            self._state[key] = 0

    def fetchone(self):
        for key, idx in self._state.items():
            rows = self._rows_of(key)
            if idx < len(rows):
                self._state[key] = idx + 1
                return rows[idx]
        return None

    def fetchall(self):
        out = []
        for key, idx in list(self._state.items()):
            rows = self._rows_of(key)
            out.extend(rows[idx:])
            self._state[key] = len(rows)
        return out


class FakeConnection:
    def __init__(self, fetch_results=None, query_map=None):
        self._fetch_results = fetch_results or []
        self._query_map = query_map
        self.closed = False
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def cursor(self, row_factory=None):
        return FakeCursor(default=self._fetch_results, query_map=self._query_map)

    def close(self):
        self.closed = True

    def commit(self):
        self.committed = True


def _mock_factory(results=None, query_map=None):
    def factory():
        return FakeConnection(fetch_results=results or [], query_map=query_map)
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


def _patch_db(monkeypatch, results=None, query_map=None):
    """Route les requêtes de l'API gouvernance vers une fausse base.

    `query_map` associe un motif SQL à une liste de lignes, ce qui permet de
    servir plusieurs requêtes distinctes sur une même connexion (dossier via
    `patient_identity_map`/`consent`). Sans `query_map`, toutes les requêtes de
    la connexion partagent `results` (comportement historique).
    """
    monkeypatch.setattr(
        "engine.governance.app.connection_factory",
        _mock_factory(results, query_map),
    )


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


# Colonnes d'identité alignées sur sql/schema.sql :
# master_patient_id, first_name, last_name, full_name, birth_date, cin,
# birth_city, address, gender.
def _master(pid, first, last, birth="1990-01-15", cin="", city="Antananarivo",
            address="", gender="M"):
    return (pid, first, last, f"{last} {first}", birth, cin, city, address, gender)


M1 = _master("PAT-0001", "Jean", "RAKOTO", cin="1102345678")
M2 = _master("PAT-0002", "Marie", "ANDRIANARIVO", birth="1985-03-02", cin="1203456789")
M3 = _master("PAT-0003", "Paul", "RABE", birth="1978-11-20", cin="1304567890")


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
    # 85 patients maîtres ; 100 fiches dont 15 rattachées à une fiche fondatrice.
    _patch_db(monkeypatch, [(85,), (100, 15)])
    client = TestClient(app)
    resp = client.get("/metrics", headers=_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_patients"] == 100
    assert data["total_masters"] == 85
    assert data["duplicates"] == 15
    assert data["duplicate_rate"] == 15.0


def test_list_patients(monkeypatch, audit_sink):
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [
        {"master_patient_id": "PAT-0001", "granted": True},
        {"master_patient_id": "PAT-0002", "granted": True},
    ])
    _patch_db(monkeypatch, results=[M1, M2])
    client = TestClient(app)
    resp = client.get("/patients", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1 and data["page_size"] == 25
    assert [row["master_patient_id"] for row in data["items"]] == ["PAT-0002", "PAT-0001"]
    first = data["items"][0]
    assert first["full_name"] == "ANDRIANARIVO Marie"
    assert first["cin"] == "1203456789"
    assert first["gender"] == "M"
    assert data["total"] == 2


def test_list_patients_filters_without_consent(monkeypatch, audit_sink):
    """Seuls les patients ayant consenti a la finalite sont renvoyes."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [
        {"master_patient_id": "PAT-0001", "granted": True},
        {"master_patient_id": "PAT-0003", "granted": False},
    ])
    _patch_db(monkeypatch, results=[M1, M2, M3])
    client = TestClient(app)
    resp = client.get("/patients", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 200
    assert [row["master_patient_id"] for row in resp.json()["items"]] == ["PAT-0001"]
    # le nombre de patients filtres est trace
    reasons = [p[7] for q, p in audit_sink if "INSERT INTO access_audit" in q]
    assert any("2 patient(s) filtres" in (r or "") for r in reasons)


def test_list_patients_search_by_full_name(monkeypatch, audit_sink):
    """La recherche porte sur le nom complet, insensible à la casse."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [
        {"master_patient_id": pid, "granted": True} for pid in ("PAT-0001", "PAT-0002", "PAT-0003")
    ])
    _patch_db(monkeypatch, results=[M1, M2, M3])
    client = TestClient(app)
    resp = client.get("/patients", params={"purpose": "research", "search": "rako"},
                      headers=_HEADERS)
    assert resp.status_code == 200
    assert [row["master_patient_id"] for row in resp.json()["items"]] == ["PAT-0001"]


def test_list_patients_search_by_cin_and_id(monkeypatch, audit_sink):
    """La recherche fonctionne aussi sur le CIN et l'identifiant master."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [
        {"master_patient_id": pid, "granted": True} for pid in ("PAT-0001", "PAT-0002")
    ])
    _patch_db(monkeypatch, results=[M1, M2])
    client = TestClient(app)
    by_cin = client.get("/patients", params={"purpose": "research", "search": "1203456789"},
                        headers=_HEADERS)
    assert [row["master_patient_id"] for row in by_cin.json()["items"]] == ["PAT-0002"]
    by_id = client.get("/patients", params={"purpose": "research", "search": "PAT-0001"},
                       headers=_HEADERS)
    assert [row["master_patient_id"] for row in by_id.json()["items"]] == ["PAT-0001"]


def test_list_patients_pagination(monkeypatch, audit_sink):
    """Le filtrage par consentement precede la pagination."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    rows = [
        _master("PAT-0001", "Jean", "RAKOTO", cin="1102345678"),
        _master("PAT-0002", "Marie", "ANDRIANARIVO", cin="1203456789"),
        _master("PAT-0003", "Paul", "RABE", cin="1304567890"),
        _master("PAT-0004", "Liva", "RASOA", cin="1405678901"),
        _master("PAT-0005", "Hery", "RAZAFY", cin="1506789012"),
    ]
    _patch_consent(monkeypatch, [
        {"master_patient_id": r[0], "granted": True} for r in rows
    ])
    _patch_db(monkeypatch, results=rows)
    client = TestClient(app)
    page1 = client.get("/patients", params={"purpose": "research", "page": 1, "page_size": 2},
                       headers=_HEADERS)
    page3 = client.get("/patients", params={"purpose": "research", "page": 3, "page_size": 2},
                       headers=_HEADERS)
    data1 = page1.json()
    assert data1["total"] == 5
    assert len(data1["items"]) == 2
    assert data1["items"][0]["full_name"] == "ANDRIANARIVO Marie"
    assert len(page3.json()["items"]) == 1


def test_list_patients_requires_purpose(monkeypatch, audit_sink):
    """Sans finalite declaree : 422 — la finalite est obligatoire."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_db(monkeypatch, results=[])
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
    _patch_db(monkeypatch, query_map={"FROM master_patient": [None]})
    client = TestClient(app)
    resp = client.get("/patients/PAT-9999", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 404


def test_get_patient_allowed(monkeypatch, audit_sink):
    """Consentement accorde : le dossier complet est servi, motif de refus vide."""
    _patch_auth(monkeypatch, ADMIN_ROW)
    _patch_consent(monkeypatch, [{"granted": True}])
    _patch_db(monkeypatch, query_map={
        "FROM master_patient": [M1],
        "FROM patient_identity_map": [
            ("pharmacy", "P-001", "new_master", 1.0),
            ("consultation", "C-002", "probabilistic", 0.95),
        ],
        "FROM consent": [
            ("api_access", True, "2026-09-27 10:00:00+00"),
            ("research", False, "2026-09-25 09:00:00+00"),
        ],
    })
    client = TestClient(app)
    resp = client.get("/patients/PAT-0001", params={"purpose": "research"}, headers=_HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["master_patient_id"] == "PAT-0001"
    assert data["full_name"] == "RAKOTO Jean"
    assert data["birth_date"] == "1990-01-15"
    assert data["cin"] == "1102345678"
    assert [m for m in data["identity_map"]] == [
        {"source_system": "pharmacy", "source_patient_id": "P-001",
         "match_method": "new_master", "match_score": 1.0},
        {"source_system": "consultation", "source_patient_id": "C-002",
         "match_method": "probabilistic", "match_score": 0.95},
    ]
    assert data["consents"] == [
        {"purpose": "api_access", "granted": True, "recorded_at": "2026-09-27 10:00:00+00"},
        {"purpose": "research", "granted": False, "recorded_at": "2026-09-25 09:00:00+00"},
    ]
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
    _patch_db(monkeypatch, query_map={"FROM master_patient": [M1]})
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

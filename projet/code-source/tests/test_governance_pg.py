"""API gouvernance sur un vrai PostgreSQL : consentement, recherche, pagination, audit, index.

Les fausses connexions de test_governance_api.py n'évaluent pas le SQL : ce fichier
rejoue les contrats sur une base réelle, à travers le vrai pool de connexions, dans
un schéma temporaire créé puis supprimé (aucune table existante n'est lue ni
modifiée). Ignoré sans la variable GOVERNANCE_TEST_DATABASE_URL.
"""

import hashlib
import os
import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

URL = os.environ.get("GOVERNANCE_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not URL, reason="GOVERNANCE_TEST_DATABASE_URL absente")

import psycopg  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from psycopg.conninfo import make_conninfo  # noqa: E402

from engine.governance import database  # noqa: E402
from engine.governance.app import app  # noqa: E402

SCHEMA_SQL = (Path(__file__).resolve().parent.parent / "sql" / "schema.sql").read_text(encoding="utf-8")
KEY = "cle-integration-gouvernance"
HEADERS = {"Authorization": f"Bearer {KEY}"}

MASTERS = [
    # id, prénom, nom, nom complet, CIN
    ("PAT-IT-0001", "Jean", "RAKOTO", "RAKOTO Jean", "1102345678"),
    ("PAT-IT-0002", "Marie", "ANDRIANARIVO", "ANDRIANARIVO Marie", "1203456789"),
    ("PAT-IT-0003", "Paul", "RABE", "RABE Paul", "1304567890"),
    ("PAT-IT-0004", "Liva", "RASOA", "RASOA Liva", None),
    ("PAT-IT-0005", "Hery", "ZAFY", "ZAFY Hery", "1506789012"),
]

CONSENTS = [
    # Le dernier avis gagne : refus puis accord -> visible.
    ("PAT-IT-0001", "research", False, "2026-09-01 10:00+00"),
    ("PAT-IT-0001", "research", True, "2026-09-02 10:00+00"),
    # Accord puis retrait -> masqué.
    ("PAT-IT-0002", "research", True, "2026-09-01 10:00+00"),
    ("PAT-IT-0002", "research", False, "2026-09-02 10:00+00"),
    # Aucun avis « research » : refus par défaut, malgré un accord sur une autre finalité.
    ("PAT-IT-0003", "analytics", True, "2026-09-01 10:00+00"),
    ("PAT-IT-0004", "research", True, "2026-09-01 10:00+00"),
    # Même horodatage : l'avis inséré en dernier (consent_id le plus grand) gagne.
    ("PAT-IT-0005", "research", False, "2026-09-03 10:00+00"),
    ("PAT-IT-0005", "research", True, "2026-09-03 10:00+00"),
]


@pytest.fixture(scope="module")
def schema():
    name = "it_governance_" + uuid.uuid4().hex[:8]
    conninfo = make_conninfo(URL, options=f"-c search_path={name}")
    with psycopg.connect(URL, autocommit=True) as conn:
        conn.execute(f"CREATE SCHEMA {name}")
    try:
        with psycopg.connect(conninfo) as conn:
            conn.execute(SCHEMA_SQL)
            conn.execute(SCHEMA_SQL)  # rejouable : le pipeline l'applique à chaque run
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO api_user (username, api_key_hash, role) VALUES (%s, %s, 'admin')",
                    ("it_admin", hashlib.sha256(KEY.encode()).hexdigest()),
                )
                cur.executemany(
                    "INSERT INTO master_patient (master_patient_id, first_name, last_name, full_name, "
                    "birth_date, cin, birth_city, address, gender) "
                    "VALUES (%s, %s, %s, %s, '1990-01-15', %s, 'Antananarivo', '', 'M')",
                    MASTERS,
                )
                cur.executemany(
                    "INSERT INTO consent (master_patient_id, purpose, granted, recorded_at) "
                    "VALUES (%s, %s, %s, %s)",
                    CONSENTS,
                )
                cur.executemany(
                    "INSERT INTO patient_identity_map (master_patient_id, source_system, "
                    "source_patient_id, match_method, match_score, explanation) "
                    "VALUES ('PAT-IT-0001', %s, %s, %s, 1.0, 'test')",
                    [("pharmacy", "pharmacy_PH001", "new_master"),
                     ("consultation", "consultation_MED001", "exact")],
                )
            conn.commit()
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("DATABASE_URL", conninfo)  # le vrai pool de l'API, sur le schéma de test
            database.close_pool()
            yield conninfo
            database.close_pool()
    finally:
        with psycopg.connect(URL, autocommit=True) as conn:
            conn.execute(f"DROP SCHEMA {name} CASCADE")


@pytest.fixture
def client(schema):
    return TestClient(app)


def _ids(resp):
    assert resp.status_code == 200, resp.text
    return [item["master_patient_id"] for item in resp.json()["items"]]


def _last_audit(conninfo):
    with psycopg.connect(conninfo) as conn:
        return conn.execute(
            "SELECT endpoint, response_status, purpose, refusal_reason FROM access_audit "
            "ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()


def test_list_latest_consent_wins_and_default_deny(client, schema):
    resp = client.get("/patients", params={"purpose": "research"}, headers=HEADERS)
    assert _ids(resp) == ["PAT-IT-0001", "PAT-IT-0004", "PAT-IT-0005"]
    assert resp.json()["total"] == 3
    endpoint, status, purpose, reason = _last_audit(schema)
    assert (endpoint, status, purpose) == ("/patients", 200, "research")
    assert reason == "2 patient(s) filtres : consentement non accorde pour research"


@pytest.mark.parametrize("term, expected", [
    ("rako", ["PAT-IT-0001"]),          # nom, casse ignorée
    ("1102345678", ["PAT-IT-0001"]),    # CIN
    ("pat-it-0004", ["PAT-IT-0004"]),   # identifiant master, CIN absent
    ("", ["PAT-IT-0001", "PAT-IT-0004", "PAT-IT-0005"]),
])
def test_search_on_name_cin_and_id(client, term, expected):
    resp = client.get("/patients", params={"purpose": "research", "search": term}, headers=HEADERS)
    assert _ids(resp) == expected


def test_search_on_hidden_patient_counts_it_as_filtered(client, schema):
    resp = client.get("/patients", params={"purpose": "research", "search": "RABE"}, headers=HEADERS)
    assert _ids(resp) == [] and resp.json()["total"] == 0
    assert _last_audit(schema)[3] == "1 patient(s) filtres : consentement non accorde pour research"


def test_pagination_after_consent_filter(client):
    pages = [client.get("/patients", params={"purpose": "research", "page": p, "page_size": 2},
                        headers=HEADERS) for p in (1, 2, 3)]
    assert [_ids(r) for r in pages] == [["PAT-IT-0001", "PAT-IT-0004"], ["PAT-IT-0005"], []]
    assert {r.json()["total"] for r in pages} == {3}


def test_patient_record_allowed_then_denied(client, schema):
    allowed = client.get("/patients/PAT-IT-0001", params={"purpose": "research"}, headers=HEADERS)
    assert allowed.status_code == 200
    data = allowed.json()
    assert [m["source_system"] for m in data["identity_map"]] == ["consultation", "pharmacy"]
    assert [c["granted"] for c in data["consents"]] == [True, False]  # plus récent d'abord

    tie = client.get("/patients/PAT-IT-0005", params={"purpose": "research"}, headers=HEADERS)
    assert tie.status_code == 200

    denied = client.get("/patients/PAT-IT-0002", params={"purpose": "research"}, headers=HEADERS)
    assert denied.status_code == 403
    endpoint, status, purpose, reason = _last_audit(schema)
    assert (endpoint, status, purpose) == ("/patients/PAT-IT-0002", 403, "research")
    assert "consentement non accorde" in reason


def test_metrics_on_real_tables(client):
    resp = client.get("/metrics", headers=HEADERS)
    assert resp.status_code == 200
    assert resp.json() == {"total_patients": 2, "total_masters": 5, "duplicates": 1,
                           "duplicate_rate": 50.0}


def test_governance_indexes_exist(schema):
    with psycopg.connect(schema) as conn:
        names = {r[0] for r in conn.execute(
            "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema()")}
    assert {"api_user_api_key_hash_idx", "patient_identity_map_master_idx",
            "consent_master_purpose_recorded_idx", "access_audit_accessed_at_idx"} <= names

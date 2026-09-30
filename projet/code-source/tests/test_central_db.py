"""Tests du chargement de la base centrale par le pipeline (provision/scripts/utils/central_db.py).

Aucune base réelle : la connexion PostgreSQL est remplacée par une fausse connexion qui
enregistre les requêtes. Les patients et décisions viennent du vrai moteur, sur le cas
de référence « Jean Rakoto », pour vérifier ce qui partirait réellement en base.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.identity.canonical import from_dict  # noqa: E402
from engine.identity.matcher import deduplicate  # noqa: E402
from provision.scripts.utils import central_db  # noqa: E402


def _patients():
    rows = [
        {"source_system": "pharmacy", "source_patient_id": "PH1", "full_name": "Jean Rakoto",
         "birth_date": "1990-01-10", "cin": "101 02404 5", "gender": "H"},
        {"source_system": "consultation", "source_patient_id": "MED1", "full_name": "Rakoto Jean",
         "birth_date": "10/01/1990", "cin": "101024045", "gender": "male"},
        {"source_system": "imaging", "source_patient_id": "IMG1", "full_name": "Hery Rasoa",
         "birth_date": "1975-05-02", "cin": "", "gender": "Femme"},
    ]
    return [from_dict(r) for r in rows]


class RecordingCursor:
    def __init__(self, log):
        self.log = log

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        self.log.append(("execute", query, params))

    def executemany(self, query, rows):
        self.log.append(("executemany", query, list(rows)))


class RecordingConnection:
    def __init__(self, fail=False):
        self.log = []
        self.committed = self.rolled_back = self.closed = False
        self.fail = fail

    def cursor(self):
        if self.fail:
            raise RuntimeError("table absente")
        return RecordingCursor(self.log)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


def test_build_rows_one_master_per_new_master_and_one_link_per_record():
    patients = _patients()
    decisions = deduplicate(patients)
    masters, identities = central_db.build_rows(patients, decisions)
    # Jean Rakoto (deux fiches, même CIN) + Hery Rasoa : deux patients maîtres, trois liens.
    assert len(masters) == 2
    assert len(identities) == 3
    assert {m[0] for m in masters} == {i[0] for i in identities}
    methods = sorted(i[3] for i in identities)
    assert methods == ["exact", "new_master", "new_master"]


def test_build_rows_keeps_gender_within_schema_constraint():
    patients = _patients()
    masters, _ = central_db.build_rows(patients, deduplicate(patients))
    assert {m[8] for m in masters} <= {"M", "F", ""}


def test_save_rows_writes_masters_before_links_and_commits():
    patients = _patients()
    masters, identities = central_db.build_rows(patients, deduplicate(patients))
    conn = RecordingConnection()
    counts = central_db.save_rows(conn, masters, identities, schema_sql="-- schema")
    kinds = [(entry[0], entry[1][:30]) for entry in conn.log]
    assert kinds[0] == ("execute", "-- schema")
    assert conn.log[1][1].startswith("INSERT INTO master_patient")
    assert conn.log[2][1].startswith("INSERT INTO patient_identity_map")
    assert counts == {"master_patient": 2, "patient_identity_map": 3}
    assert conn.committed


def test_load_without_database_url_writes_nothing(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    assert central_db.load_central_db(_patients(), []) is None


def test_load_never_raises_when_database_fails():
    conn = RecordingConnection(fail=True)
    patients = _patients()
    result = central_db.load_central_db(patients, deduplicate(patients), connect=lambda: conn)
    assert result is None
    assert conn.rolled_back and conn.closed


def test_load_never_raises_when_database_unreachable():
    def refuse():
        raise ConnectionError("connexion refusée")

    assert central_db.load_central_db(_patients(), [], connect=refuse) is None

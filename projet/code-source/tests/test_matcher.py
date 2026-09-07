"""Tests du moteur d'identite (exact + probabiliste) et parite Spark."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.identity.canonical import CanonicalPatient
from engine.identity.matcher import deduplicate
from engine.identity.spark_dedup import deduplicate as spark_dedup


def _patient(source_system, source_patient_id, full_name, birth_date, phone, gender="F"):
    return CanonicalPatient(
        source_system=source_system,
        source_patient_id=source_patient_id,
        first_name=full_name.split(" ")[0],
        last_name=full_name.split(" ", 1)[1] if " " in full_name else "",
        full_name=full_name,
        birth_date=date.fromisoformat(birth_date),
        phone=phone,
        address="",
        gender=gender,
        source_file="",
    )


def _decisions(patients):
    return {(d.source_system, d.source_patient_id): d.master_patient_id for d in deduplicate(patients)}


def _spark_decisions(patients):
    rows = [
        {"source_system": p.source_system, "source_patient_id": p.source_patient_id,
         "full_name": p.full_name, "birth_date": p.birth_date, "phone": p.phone}
        for p in patients
    ]
    return {(d["source_system"], d["source_patient_id"]): d["master_patient_id"] for d in spark_dedup(rows)}


def test_exact_duplicate():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "0341234567")
    p2 = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "0341234567")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] == dec[("consultation", "MED001")]
    assert dec[("pharmacy", "PH001")].startswith("PAT-")


def test_exact_inverted_name_same_birth_phone():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "0341234567")
    p2 = _patient("pharmacy", "PH002", "Rakoto Jean", "1990-05-12", "0341234567")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] == dec[("pharmacy", "PH002")]


def test_probabilistic_threshold():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "0341234567")
    p2 = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "0341234468")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] == dec[("consultation", "MED001")]


def test_distinct_patients_stay_separate():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "0341234567")
    p2 = _patient("pharmacy", "PH002", "Marie Rasoa", "1985-01-01", "0321112233")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] != dec[("pharmacy", "PH002")]


def test_spark_parity():
    patients = [
        _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "0341234567"),
        _patient("pharmacy", "PH002", "Rakoto Jean", "1990-05-12", "0341234567"),
        _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "0341234468"),
        _patient("pharmacy", "PH003", "Marie Rasoa", "1985-01-01", "0321112233"),
    ]
    mvp = _decisions(patients)
    spark = _spark_decisions(patients)
    for key in mvp:
        assert spark[key] == mvp[key], f"parite cassée pour {key}"


def test_no_match_creates_new_master():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "0341234567")
    p2 = _patient("pharmacy", "PH002", "Solo Vola", "1980-03-03", "0339998877")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] != dec[("pharmacy", "PH002")]
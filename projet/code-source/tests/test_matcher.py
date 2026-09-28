"""Tests du moteur d'identite (exact + probabiliste) et parite Spark."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.identity.canonical import CanonicalPatient, _cin, _text
from engine.identity.matcher import deduplicate, _similarity
from engine.identity.spark_dedup import deduplicate as spark_dedup
from engine.identity.config import DEFAULT_THRESHOLD, DEFAULT_WEIGHTS, load_dedup_config


def _patient(source_system, source_patient_id, full_name, birth_date, cin, birth_city, gender="F"):
    return CanonicalPatient(
        source_system=source_system,
        source_patient_id=source_patient_id,
        first_name=full_name.split(" ")[0],
        last_name=full_name.split(" ", 1)[1] if " " in full_name else "",
        full_name=full_name,
        birth_date=date.fromisoformat(birth_date),
        cin=_cin(cin),
        birth_city=_text(birth_city),
        address="",
        gender=gender,
        source_file="",
    )


def _decisions(patients):
    return {(d.source_system, d.source_patient_id): d.master_patient_id for d in deduplicate(patients)}


def _spark_decisions(patients):
    rows = [
        {"source_system": p.source_system, "source_patient_id": p.source_patient_id,
         "full_name": p.full_name, "birth_date": p.birth_date,
         "cin": p.cin, "birth_city": p.birth_city}
        for p in patients
    ]
    return {(d["source_system"], d["source_patient_id"]): d["master_patient_id"] for d in spark_dedup(rows)}


def test_exact_duplicate():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "Antananarivo")
    p2 = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "101024045", "Antananarivo")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] == dec[("consultation", "MED001")]
    assert dec[("pharmacy", "PH001")].startswith("PAT-")


def test_exact_inverted_name_same_birth_cin():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "Antananarivo")
    p2 = _patient("pharmacy", "PH002", "Rakoto Jean", "1990-05-12", "101024045", "Fianarantsoa")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] == dec[("pharmacy", "PH002")]


def test_cin_format_normalization():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101 02404 5", "")
    p2 = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "101024045", "")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] == dec[("consultation", "MED001")]


def test_probabilistic_threshold():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "")
    p2 = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "102077713", "")
    dec = _decisions([p1, p2])
    # nom 0.5 + date 0.3 = 0.8 : exactement au seuil.
    assert dec[("pharmacy", "PH001")] == dec[("consultation", "MED001")]


def test_probabilistic_below_threshold_stays_separate():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "", "")
    p2 = _patient("pharmacy", "PH002", "Jean Rakoto", "1985-01-01", "", "")
    dec = _decisions([p1, p2])
    # nom seul = 0.5, sous le seuil : deux masters distincts.
    assert dec[("pharmacy", "PH001")] != dec[("pharmacy", "PH002")]


def test_distinct_patients_stay_separate():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "")
    p2 = _patient("pharmacy", "PH002", "Marie Rasoa", "1985-01-01", "", "Toamasina")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] != dec[("pharmacy", "PH002")]


def test_birth_city_increases_score():
    base = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "", "Antananarivo")
    same_city = _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "", "antananarivo")
    no_city = _patient("consultation", "MED002", "Jean Rakoto", "1990-05-12", "", "")
    assert _similarity(base, same_city) > _similarity(base, no_city)


def test_spark_parity():
    patients = [
        _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101 02404 5", "Antananarivo"),
        _patient("pharmacy", "PH002", "Rakoto Jean", "1990-05-12", "101024045", "Fianarantsoa"),
        _patient("consultation", "MED001", "Jean Rakoto", "1990-05-12", "102077713", ""),
        _patient("pharmacy", "PH003", "Marie Rasoa", "1985-01-01", "", "Toamasina"),
    ]
    mvp = _decisions(patients)
    spark = _spark_decisions(patients)
    for key in mvp:
        assert spark[key] == mvp[key], f"parite cassée pour {key}"


def test_no_match_creates_new_master():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "")
    p2 = _patient("pharmacy", "PH002", "Solo Vola", "1980-03-03", "", "")
    dec = _decisions([p1, p2])
    assert dec[("pharmacy", "PH001")] != dec[("pharmacy", "PH002")]
    assert len({dec[("pharmacy", "PH001")], dec[("pharmacy", "PH002")]}) == 2


def test_load_dedup_config_from_yaml():
    cfg = load_dedup_config()
    assert cfg.threshold == 0.80
    assert cfg.name_prefix_len == 4
    assert dict(cfg.weights) == {"name": 0.5, "birth_date": 0.3, "cin": 0.1, "birth_city": 0.1}


def test_load_dedup_config_fallback_on_missing_file():
    cfg = load_dedup_config("C:/aucun/chemin/deduplication.yaml")
    assert cfg.threshold == DEFAULT_THRESHOLD
    assert dict(cfg.weights) == dict(DEFAULT_WEIGHTS)


def test_weights_override_changes_decision():
    p1 = _patient("pharmacy", "PH001", "Jean Rakoto", "1990-05-12", "101024045", "")
    p2 = _patient("pharmacy", "PH002", "Jean Rakoto", "1990-05-12", "102077713", "")
    # Défauts : nom 0.5 + date 0.3 = 0.8 -> fusion au seuil.
    assert _decisions([p1, p2])[("pharmacy", "PH001")] == _decisions([p1, p2])[("pharmacy", "PH002")]
    # Poids reconfigurés (YAML recommande de les changer ici) : nom 0.4 + date 0.35 = 0.75 -> non fusion.
    custom_weights = {"name": 0.4, "birth_date": 0.35, "cin": 0.05, "birth_city": 0.2}
    dec = deduplicate([p1, p2], weights=custom_weights)
    pairs = {(d.source_system, d.source_patient_id): d.master_patient_id for d in dec}
    assert pairs[("pharmacy", "PH001")] != pairs[("pharmacy", "PH002")]
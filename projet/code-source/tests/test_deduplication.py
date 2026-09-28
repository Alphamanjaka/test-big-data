"""Tests du mapping canonique RAW -> CanonicalPatient (canonical.py)."""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.identity.canonical import CanonicalPatient, _birth_date, _cin, _text, from_dict, map_patient


def test_pharmacy_mapping():
    row = {
        "nom_complet": "Jean Rakoto",
        "client_id": "PH001",
        "cin": "101 02404 5",
        "naissance": "1990-05-12",
        "ville_naissance": "Antananarivo",
        "adresse": "Lot 1 Bis",
        "sexe": "M",
    }
    p = map_patient(row, "pharmacy")
    assert p.source_system == "pharmacy"
    assert p.source_patient_id == "PH001"
    assert p.first_name == "Jean"
    assert p.last_name == "Rakoto"
    assert p.birth_date == date(1990, 5, 12)
    assert p.cin == "101024045"
    assert p.gender == "M"


def test_consultation_mapping():
    row = {
        "prenom": "Jean",
        "nom": "Rakoto",
        "patient_code": "MED001",
        "no_cin": "101024045",
        "date_naiss": "1990/05/12",
    }
    p = map_patient(row, "consultation")
    assert p.source_system == "consultation"
    assert p.first_name == "Jean"
    assert p.last_name == "Rakoto"
    assert p.full_name == "Jean Rakoto"
    assert p.birth_date == date(1990, 5, 12)
    assert p.cin == "101024045"


def test_imaging_mapping():
    row = {
        "patient_name": "Martin Alice",
        "id_personne": "IMG001",
        "cin_number": "98765432109",
        "dob": "1990-11-20",
        "birth_place": "Toamasina",
        "sex": "F",
    }
    p = map_patient(row, "imaging")
    assert p.source_system == "imaging"
    assert p.first_name == "Martin"
    assert p.last_name == "Alice"
    assert p.birth_date == date(1990, 11, 20)
    assert p.cin == "98765432109"
    assert p.gender == "F"


def test_map_missing_birth_date_returns_none():
    row = {"nom_complet": "Doe", "client_id": "PH999", "cin": "", "naissance": None, "adresse": ""}
    p = map_patient(row, "pharmacy")
    assert p.cin == ""
    assert p.birth_date is None


def test_from_dict_roundtrip():
    row = {
        "source_system": "pharmacy",
        "source_patient_id": "PH001",
        "full_name": "Jean Rakoto",
        "birth_date": "1990-05-12",
        "cin": "101024045",
        "birth_city": "Antananarivo",
        "address": "",
        "gender": "M",
        "source_file": "pharmacy_2025.csv",
    }
    p = from_dict(row)
    assert isinstance(p, CanonicalPatient)
    assert p.source_system == "pharmacy"
    assert p.first_name == "Jean"
    assert p.last_name == "Rakoto"
    assert p.birth_date == date(1990, 5, 12)
    assert p.cin == "101024045"


def test_birth_date_iso_and_slash_formats():
    assert _birth_date("1990-05-12") == date(1990, 5, 12)
    assert _birth_date("1990/05/12") == date(1990, 5, 12)
    assert _birth_date("") is None
    assert _birth_date(None) is None
    assert _birth_date("pas-une-date") is None


def test_cin_normalization():
    assert _cin("101 02404 5") == "101024045"
    assert _cin("abc123") == ""
    assert _cin(None) == ""


def test_text_whitespace_normalization():
    assert _text("  Jean   Rakoto ") == "Jean Rakoto"
    assert _text(None) == ""

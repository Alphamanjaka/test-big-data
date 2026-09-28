from datetime import date

import pandas as pd

from patient_platform.transform.canonical import (
    _birth_date,
    _normalized,
    _phone,
    _text,
)


def test_text_handles_none_and_nan():
    assert _text(None) == ""
    assert _text(float("nan")) == ""
    assert _text("  Jean   Dupont  ") == "Jean Dupont"


def test_normalized_handles_none():
    assert _normalized(None) == ""
    assert _normalized("Jean DUPONT") == "jeandupont"


def test_phone_handles_none():
    assert _phone(None) == ""
    assert _phone("+261 34 12 34 567") == "0341234567"


def test_birth_date_handles_none_and_empty():
    assert _birth_date(None) is None
    assert _birth_date("") is None
    assert _birth_date("  ") is None
    assert _birth_date("1990-01-10") == date(1990, 1, 10)


def test_map_patient_survives_missing_values():
    from patient_platform.transform.canonical import map_patient

    row = pd.Series({
        "nom_complet": "Jean Dupont",
        "client_id": "PH001",
        "telephone": None,
        "adresse": None,
        "naissance": None,
        "source_file": "patients.csv",
    })
    patient = map_patient(row, "pharmacy")
    assert patient.phone == ""
    assert patient.address == ""
    assert patient.birth_date is None

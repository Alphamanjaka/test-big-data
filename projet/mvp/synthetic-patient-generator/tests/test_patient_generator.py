"""
Tests de l'Étape 2 — Patient Generator.
"""

import re

from generator.patient_generator import generate_master_patients

EXPECTED_COLUMNS = {
    "master_id",
    "first_name",
    "last_name",
    "birth_date",
    "gender",
    "phone",
    "email",
    "address",
}


def test_generates_requested_number_of_patients():
    df = generate_master_patients(n=50)
    assert len(df) == 50


def test_master_id_format_and_uniqueness():
    df = generate_master_patients(n=20)
    assert df["master_id"].tolist() == [f"GT{i:06d}" for i in range(1, 21)]
    assert df["master_id"].is_unique


def test_expected_columns_present():
    df = generate_master_patients(n=5)
    assert EXPECTED_COLUMNS.issubset(set(df.columns))


def test_phone_number_is_malagasy_format():
    df = generate_master_patients(n=100)
    pattern = re.compile(r"^0(32|33|34|38)\d{7}$")
    assert df["phone"].apply(lambda p: bool(pattern.match(p))).all()


def test_gender_is_m_or_f():
    df = generate_master_patients(n=50)
    assert set(df["gender"].unique()).issubset({"M", "F"})


def test_reproducibility_with_same_seed():
    df1 = generate_master_patients(n=30, seed=123)
    df2 = generate_master_patients(n=30, seed=123)
    assert df1["phone"].tolist() == df2["phone"].tolist()

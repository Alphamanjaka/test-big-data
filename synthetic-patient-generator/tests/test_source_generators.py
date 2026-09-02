"""
Tests de l'Étape 5 — Source Generators (pharmacy, consultation, imaging).
"""

from generator.consultation_generator import generate_consultation_patients, generate_consultations
from generator.distribution_engine import distribute_patients
from generator.imaging_generator import generate_exams, generate_imaging_patients
from generator.patient_generator import generate_master_patients
from generator.pharmacy_generator import generate_pharmacy_patients, generate_pharmacy_purchases

MASTER = generate_master_patients(n=100, seed=10)
PLAN = distribute_patients(MASTER, seed=10)


def test_pharmacy_patients_schema_and_count():
    df = generate_pharmacy_patients(MASTER, PLAN, "medium", seed=10)
    assert list(df.columns) == ["client_id", "nom_complet", "naissance", "telephone", "adresse"]
    expected = (PLAN["source"] == "pharmacy").sum()
    assert len(df) == expected
    assert df["client_id"].str.startswith("PH").all()


def test_pharmacy_purchases_reference_existing_customers():
    patients_df = generate_pharmacy_patients(MASTER, PLAN, "medium", seed=10)
    purchases_df = generate_pharmacy_purchases(patients_df, seed=10)
    assert set(purchases_df["customer_id"]).issubset(set(patients_df["client_id"]))
    assert purchases_df["purchase_id"].is_unique


def test_consultation_patients_schema():
    df = generate_consultation_patients(MASTER, PLAN, "medium", seed=10)
    assert list(df.columns) == [
        "patient_code",
        "prenom",
        "nom",
        "date_naiss",
        "phone_number",
    ]
    assert df["patient_code"].str.startswith("MED").all()


def test_consultations_reference_existing_patients():
    patients_df = generate_consultation_patients(MASTER, PLAN, "medium", seed=10)
    consultations_df = generate_consultations(patients_df, seed=10)
    assert set(consultations_df["patient_id"]).issubset(set(patients_df["patient_code"]))
    assert consultations_df["consultation_id"].is_unique


def test_imaging_patients_schema():
    df = generate_imaging_patients(MASTER, PLAN, "medium", seed=10)
    assert list(df.columns) == ["id_personne", "patient_name", "dob", "tel"]
    assert df["id_personne"].str.startswith("IMG").all()


def test_exams_reference_existing_patients():
    patients_df = generate_imaging_patients(MASTER, PLAN, "medium", seed=10)
    exams_df = generate_exams(patients_df, seed=10)
    assert set(exams_df["patient_code"]).issubset(set(patients_df["id_personne"]))
    assert exams_df["exam_id"].is_unique


def test_hard_difficulty_can_produce_missing_values():
    df = generate_pharmacy_patients(MASTER, PLAN, "hard", seed=10)
    # Sur 100 patients à 50% de variation, il doit statistiquement manquer au moins une valeur.
    assert df["naissance"].isna().any() or df["telephone"].isna().any()


def test_pharmacy_patients_have_address():
    df = generate_pharmacy_patients(MASTER, PLAN, "medium", seed=10)
    assert df["adresse"].notna().all()

"""
Tests de l'Étape 3 — Distribution Engine.
"""

from generator.distribution_engine import distribute_patients
from generator.patient_generator import generate_master_patients


def test_every_master_patient_appears_at_least_once():
    master = generate_master_patients(n=200, seed=1)
    plan = distribute_patients(master, seed=1)
    assert set(plan["master_id"]) == set(master["master_id"])


def test_local_ids_are_unique_per_source():
    master = generate_master_patients(n=200, seed=1)
    plan = distribute_patients(master, seed=1)
    for source in ("pharmacy", "consultation", "imaging"):
        source_ids = plan.loc[plan["source"] == source, "local_id"]
        assert source_ids.is_unique


def test_local_id_prefixes_match_source():
    master = generate_master_patients(n=100, seed=2)
    plan = distribute_patients(master, seed=2)
    prefixes = {"pharmacy": "PH", "consultation": "MED", "imaging": "IMG"}
    for source, prefix in prefixes.items():
        source_ids = plan.loc[plan["source"] == source, "local_id"]
        assert source_ids.str.startswith(prefix).all()


def test_a_patient_can_appear_in_multiple_sources():
    master = generate_master_patients(n=500, seed=3)
    plan = distribute_patients(master, seed=3)
    sources_per_patient = plan.groupby("master_id")["source"].nunique()
    assert sources_per_patient.max() > 1


def test_reproducibility_with_same_seed():
    master = generate_master_patients(n=100, seed=42)
    plan1 = distribute_patients(master, seed=42)
    plan2 = distribute_patients(master, seed=42)
    assert plan1.equals(plan2)

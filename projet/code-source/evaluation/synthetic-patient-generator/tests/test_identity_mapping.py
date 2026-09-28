"""
Tests de l'Étape 6 — Identity Mapping.
"""

from generator.distribution_engine import distribute_patients
from generator.identity_mapping import build_identity_mapping
from generator.patient_generator import generate_master_patients


def test_mapping_columns_match_document_format():
    master = generate_master_patients(n=50, seed=5)
    plan = distribute_patients(master, seed=5)
    mapping = build_identity_mapping(plan)
    assert list(mapping.columns) == ["source", "source_patient_id", "ground_truth_id"]


def test_mapping_covers_every_distribution_row():
    master = generate_master_patients(n=50, seed=5)
    plan = distribute_patients(master, seed=5)
    mapping = build_identity_mapping(plan)
    assert len(mapping) == len(plan)


def test_every_ground_truth_id_is_a_real_master_id():
    master = generate_master_patients(n=50, seed=5)
    plan = distribute_patients(master, seed=5)
    mapping = build_identity_mapping(plan)
    assert set(mapping["ground_truth_id"]).issubset(set(master["master_id"]))


def test_multi_source_patients_are_detectable():
    master = generate_master_patients(n=300, seed=5)
    plan = distribute_patients(master, seed=5)
    mapping = build_identity_mapping(plan)
    sources_per_patient = mapping.groupby("ground_truth_id")["source"].nunique()
    # Avec les probabilités par défaut, certains patients doivent être multi-sources.
    assert (sources_per_patient > 1).any()

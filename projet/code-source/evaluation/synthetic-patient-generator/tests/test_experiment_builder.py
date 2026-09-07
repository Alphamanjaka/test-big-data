"""
Tests de l'Étape 7 — Génération des expériences.
"""

import pandas as pd

from generator.distribution_engine import distribute_patients
from generator.experiment_builder import build_all_experiments, build_experiment
from generator.patient_generator import generate_master_patients


def test_build_experiment_creates_all_expected_files(tmp_path):
    master = generate_master_patients(n=60, seed=9)
    plan = distribute_patients(master, seed=9)
    output_dir = tmp_path / "medium"

    build_experiment("medium", master, plan, output_dir, seed=9)

    expected_files = [
        "pharmacy/patients.csv",
        "pharmacy/achats.csv",
        "consultation/patients.csv",
        "consultation/consultations.csv",
        "imaging/patients.csv",
        "imaging/examens.csv",
        "ground_truth/identity_mapping.csv",
    ]
    for relative_path in expected_files:
        assert (output_dir / relative_path).exists(), relative_path


def test_same_ground_truth_across_difficulty_levels(tmp_path):
    master = generate_master_patients(n=60, seed=9)
    plan = distribute_patients(master, seed=9)

    build_experiment("easy", master, plan, tmp_path / "easy", seed=9)
    build_experiment("hard", master, plan, tmp_path / "hard", seed=9)

    easy_mapping = pd.read_csv(tmp_path / "easy" / "ground_truth" / "identity_mapping.csv")
    hard_mapping = pd.read_csv(tmp_path / "hard" / "ground_truth" / "identity_mapping.csv")

    # Même Ground Truth et même distribution : le mapping ne dépend pas de la difficulté.
    assert easy_mapping.equals(hard_mapping)


def test_hard_dataset_has_more_missing_values_than_easy(tmp_path):
    master = generate_master_patients(n=300, seed=9)
    plan = distribute_patients(master, seed=9)

    build_experiment("easy", master, plan, tmp_path / "easy", seed=9)
    build_experiment("hard", master, plan, tmp_path / "hard", seed=9)

    easy_patients = pd.read_csv(tmp_path / "easy" / "pharmacy" / "patients.csv")
    hard_patients = pd.read_csv(tmp_path / "hard" / "pharmacy" / "patients.csv")

    easy_missing = easy_patients.isna().sum().sum()
    hard_missing = hard_patients.isna().sum().sum()
    assert hard_missing > easy_missing


def test_build_all_experiments_creates_three_datasets(tmp_path, monkeypatch):
    from config import settings

    monkeypatch.setattr(settings, "EXPERIMENTS_DIR", tmp_path)
    build_all_experiments(n_patients=40, seed=3)

    for difficulty in ("easy", "medium", "hard"):
        assert (tmp_path / difficulty / "ground_truth" / "identity_mapping.csv").exists()

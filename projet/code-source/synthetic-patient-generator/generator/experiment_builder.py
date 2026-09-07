"""
Étape 7 — Génération des expériences.

Construit trois jeux de données complets (easy / medium / hard), chacun
avec le même Ground Truth et le même plan de distribution (mêmes patients,
mêmes sources), mais un taux de variation différent :

    data/experiments/
    ├── easy/    (10 % de variations)
    ├── medium/  (30 % de variations)
    └── hard/    (50 % de variations)

Chaque dossier `experiments/<niveau>/` est autonome :

    <niveau>/
    ├── pharmacy/{patients.csv, achats.csv}
    ├── consultation/{patients.csv, consultations.csv}
    ├── imaging/{patients.csv, examens.csv}
    └── ground_truth/identity_mapping.csv   (réservé à l'évaluation)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from config import settings
from generator.consultation_generator import (
    generate_consultation_patients,
    generate_consultations,
    save_consultation_data,
)
from generator.distribution_engine import distribute_patients
from generator.identity_mapping import build_identity_mapping
from generator.imaging_generator import generate_exams, generate_imaging_patients, save_imaging_data
from generator.patient_generator import generate_master_patients
from generator.pharmacy_generator import (
    generate_pharmacy_patients,
    generate_pharmacy_purchases,
    save_pharmacy_data,
)


def build_experiment(
    difficulty: str,
    master_patients: pd.DataFrame,
    distribution_plan: pd.DataFrame,
    output_dir: Path,
    seed: int = settings.RANDOM_SEED,
) -> None:
    """
    Construit un dataset complet (3 sources + identity mapping) pour un
    niveau de difficulté donné, dans `output_dir` (ex: data/experiments/hard).
    """
    # --- Sources hétérogènes, chacune avec ses propres variations ---
    ph_patients = generate_pharmacy_patients(master_patients, distribution_plan, difficulty, seed)
    ph_purchases = generate_pharmacy_purchases(ph_patients, seed)
    save_pharmacy_data(ph_patients, ph_purchases, output_dir=output_dir / "pharmacy")

    co_patients = generate_consultation_patients(
        master_patients, distribution_plan, difficulty, seed
    )
    co_consultations = generate_consultations(co_patients, seed)
    save_consultation_data(co_patients, co_consultations, output_dir=output_dir / "consultation")

    im_patients = generate_imaging_patients(master_patients, distribution_plan, difficulty, seed)
    im_exams = generate_exams(im_patients, seed)
    save_imaging_data(im_patients, im_exams, output_dir=output_dir / "imaging")

    # --- Vérité de référence, propre à ce dataset (réservée à l'évaluation) ---
    mapping = build_identity_mapping(distribution_plan)
    ground_truth_dir = output_dir / "ground_truth"
    ground_truth_dir.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(ground_truth_dir / "identity_mapping.csv", index=False)


def build_all_experiments(
    n_patients: int = settings.DEFAULT_NUM_PATIENTS,
    seed: int = settings.RANDOM_SEED,
) -> None:
    """Génère les trois datasets easy / medium / hard à partir du même Ground Truth."""
    master_patients = generate_master_patients(n=n_patients, seed=seed)
    distribution_plan = distribute_patients(master_patients, seed=seed)

    for difficulty in settings.DIFFICULTY_LEVELS:
        output_dir = settings.EXPERIMENTS_DIR / difficulty
        build_experiment(difficulty, master_patients, distribution_plan, output_dir, seed=seed)
        print(f"✓ Dataset '{difficulty}' généré dans {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère les datasets d'expérimentation easy/medium/hard."
    )
    parser.add_argument("--patients", type=int, default=settings.DEFAULT_NUM_PATIENTS)
    parser.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    args = parser.parse_args()

    build_all_experiments(n_patients=args.patients, seed=args.seed)


if __name__ == "__main__":
    main()

"""
Étape 5 — Source Generator : Consultation.

Produit :
- data/raw/consultation/patients.csv       (patient_code, first_name, last_name, birth_date, telephone)
- data/raw/consultation/consultations.csv  (consultation_id, patient_code, diagnosis, consultation_date)
"""

from __future__ import annotations

import argparse
import random
from datetime import date
from pathlib import Path

import pandas as pd

from config import settings
from generator.common import build_source_patients, random_date_between
from generator.distribution_engine import distribute_patients
from generator.patient_generator import generate_master_patients

DIAGNOSES = [
    "Hypertension",
    "Diabete type 2",
    "Paludisme",
    "Grippe",
    "Bronchite",
    "Gastro-enterite",
    "Anemie",
    "Asthme",
    "Migraine",
    "Dermatite",
]

MIN_CONSULTATIONS_PER_PATIENT = 1
MAX_CONSULTATIONS_PER_PATIENT = 2
CONSULTATION_DATE_RANGE = (date(2025, 1, 1), date(2026, 8, 1))


def generate_consultation_patients(
    master_patients: pd.DataFrame,
    distribution_plan: pd.DataFrame,
    difficulty: str,
    seed: int = settings.RANDOM_SEED,
) -> pd.DataFrame:
    """Génère data/raw/consultation/patients.csv : patient_code, first_name, last_name, birth_date, telephone."""
    varied = build_source_patients(
        master_patients, distribution_plan, "consultation", difficulty, seed
    )

    return pd.DataFrame(
        {
            "patient_code": varied["local_id"],
            "first_name": varied["first_name"],
            "last_name": varied["last_name"],
            "birth_date": varied["birth_date"],
            "telephone": varied["phone"],
        }
    )


def generate_consultations(
    patients_df: pd.DataFrame, seed: int = settings.RANDOM_SEED
) -> pd.DataFrame:
    """Génère data/raw/consultation/consultations.csv : consultation_id, patient_code, diagnosis, consultation_date."""
    rng = random.Random(seed)
    start, end = CONSULTATION_DATE_RANGE
    rows: list[dict] = []
    counter = 0

    for patient_code in patients_df["patient_code"]:
        n_consultations = rng.randint(
            MIN_CONSULTATIONS_PER_PATIENT, MAX_CONSULTATIONS_PER_PATIENT
        )
        for _ in range(n_consultations):
            counter += 1
            rows.append(
                {
                    "consultation_id": f"C{counter:06d}",
                    "patient_code": patient_code,
                    "diagnosis": rng.choice(DIAGNOSES),
                    "consultation_date": random_date_between(start, end, rng).isoformat(),
                }
            )

    return pd.DataFrame(rows)


def save_consultation_data(
    patients_df: pd.DataFrame,
    consultations_df: pd.DataFrame,
    output_dir: Path = settings.CONSULTATION_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    patients_df.to_csv(output_dir / "patients.csv", index=False)
    consultations_df.to_csv(output_dir / "consultations.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère la source Consultation.")
    parser.add_argument("--patients", type=int, default=settings.DEFAULT_NUM_PATIENTS)
    parser.add_argument("--difficulty", choices=list(settings.DIFFICULTY_LEVELS), default="medium")
    parser.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    args = parser.parse_args()

    master_patients = generate_master_patients(n=args.patients, seed=args.seed)
    distribution_plan = distribute_patients(master_patients, seed=args.seed)

    patients_df = generate_consultation_patients(
        master_patients, distribution_plan, args.difficulty, seed=args.seed
    )
    consultations_df = generate_consultations(patients_df, seed=args.seed)
    save_consultation_data(patients_df, consultations_df)

    print(f"✓ Consultation : {len(patients_df)} patients, {len(consultations_df)} consultations")
    print(f"✓ Fichiers : {settings.CONSULTATION_DIR}")


if __name__ == "__main__":
    main()

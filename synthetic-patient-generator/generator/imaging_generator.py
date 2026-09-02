"""
Étape 5 — Source Generator : Imagerie.

Produit :
- data/raw/imaging/patients.csv  (person_identifier, patient_name, dob, tel)
- data/raw/imaging/exams.csv     (exam_id, person_identifier, exam_type, exam_date)
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

EXAM_TYPES = [
    "Radiographie",
    "Echographie",
    "IRM",
    "Scanner",
    "Mammographie",
    "Doppler",
    "Endoscopie",
]

MIN_EXAMS_PER_PATIENT = 1
MAX_EXAMS_PER_PATIENT = 2
EXAM_DATE_RANGE = (date(2025, 1, 1), date(2026, 8, 1))


def generate_imaging_patients(
    master_patients: pd.DataFrame,
    distribution_plan: pd.DataFrame,
    difficulty: str,
    seed: int = settings.RANDOM_SEED,
) -> pd.DataFrame:
    """Génère data/raw/imaging/patients.csv : person_identifier, patient_name, dob, tel."""
    varied = build_source_patients(
        master_patients, distribution_plan, "imaging", difficulty, seed
    )

    def patient_name(row):
        parts = [p for p in (row["first_name"], row["last_name"]) if p]
        return " ".join(parts) if parts else None

    return pd.DataFrame(
        {
            "person_identifier": varied["local_id"],
            "patient_name": varied.apply(patient_name, axis=1),
            "dob": varied["birth_date"],
            "tel": varied["phone"],
        }
    )


def generate_exams(patients_df: pd.DataFrame, seed: int = settings.RANDOM_SEED) -> pd.DataFrame:
    """Génère data/raw/imaging/exams.csv : exam_id, person_identifier, exam_type, exam_date."""
    rng = random.Random(seed)
    start, end = EXAM_DATE_RANGE
    rows: list[dict] = []
    counter = 0

    for person_identifier in patients_df["person_identifier"]:
        n_exams = rng.randint(MIN_EXAMS_PER_PATIENT, MAX_EXAMS_PER_PATIENT)
        for _ in range(n_exams):
            counter += 1
            rows.append(
                {
                    "exam_id": f"E{counter:06d}",
                    "person_identifier": person_identifier,
                    "exam_type": rng.choice(EXAM_TYPES),
                    "exam_date": random_date_between(start, end, rng).isoformat(),
                }
            )

    return pd.DataFrame(rows)


def save_imaging_data(
    patients_df: pd.DataFrame,
    exams_df: pd.DataFrame,
    output_dir: Path = settings.IMAGING_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    patients_df.to_csv(output_dir / "patients.csv", index=False)
    exams_df.to_csv(output_dir / "exams.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère la source Imagerie.")
    parser.add_argument("--patients", type=int, default=settings.DEFAULT_NUM_PATIENTS)
    parser.add_argument("--difficulty", choices=list(settings.DIFFICULTY_LEVELS), default="medium")
    parser.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    args = parser.parse_args()

    master_patients = generate_master_patients(n=args.patients, seed=args.seed)
    distribution_plan = distribute_patients(master_patients, seed=args.seed)

    patients_df = generate_imaging_patients(
        master_patients, distribution_plan, args.difficulty, seed=args.seed
    )
    exams_df = generate_exams(patients_df, seed=args.seed)
    save_imaging_data(patients_df, exams_df)

    print(f"✓ Imagerie : {len(patients_df)} patients, {len(exams_df)} examens")
    print(f"✓ Fichiers : {settings.IMAGING_DIR}")


if __name__ == "__main__":
    main()

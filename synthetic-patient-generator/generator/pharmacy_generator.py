"""
Étape 5 — Source Generator : Pharmacie.

Produit :
- data/raw/pharmacy/patients.csv   (customer_id, full_name, date_birth, phone_number)
- data/raw/pharmacy/purchases.csv  (purchase_id, customer_id, medicine, quantity, purchase_date)
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

MEDICINES = [
    "Paracetamol",
    "Ibuprofene",
    "Amoxicilline",
    "Aspirine",
    "Metformine",
    "Omeprazole",
    "Chloroquine",
    "Vitamine C",
    "Salbutamol",
    "Loperamide",
]

MIN_PURCHASES_PER_PATIENT = 1
MAX_PURCHASES_PER_PATIENT = 3
PURCHASE_DATE_RANGE = (date(2025, 1, 1), date(2026, 8, 1))


def generate_pharmacy_patients(
    master_patients: pd.DataFrame,
    distribution_plan: pd.DataFrame,
    difficulty: str,
    seed: int = settings.RANDOM_SEED,
) -> pd.DataFrame:
    """Génère data/raw/pharmacy/patients.csv : customer_id, full_name, date_birth, phone_number."""
    varied = build_source_patients(
        master_patients, distribution_plan, "pharmacy", difficulty, seed
    )

    def full_name(row):
        parts = [p for p in (row["first_name"], row["last_name"]) if p]
        return " ".join(parts) if parts else None

    return pd.DataFrame(
        {
            "customer_id": varied["local_id"],
            "full_name": varied.apply(full_name, axis=1),
            "date_birth": varied["birth_date"],
            "phone_number": varied["phone"],
        }
    )


def generate_pharmacy_purchases(
    patients_df: pd.DataFrame, seed: int = settings.RANDOM_SEED
) -> pd.DataFrame:
    """Génère data/raw/pharmacy/purchases.csv : purchase_id, customer_id, medicine, quantity, purchase_date."""
    rng = random.Random(seed)
    start, end = PURCHASE_DATE_RANGE
    rows: list[dict] = []
    counter = 0

    for customer_id in patients_df["customer_id"]:
        n_purchases = rng.randint(MIN_PURCHASES_PER_PATIENT, MAX_PURCHASES_PER_PATIENT)
        for _ in range(n_purchases):
            counter += 1
            rows.append(
                {
                    "purchase_id": f"P{counter:06d}",
                    "customer_id": customer_id,
                    "medicine": rng.choice(MEDICINES),
                    "quantity": rng.randint(1, 5),
                    "purchase_date": random_date_between(start, end, rng).isoformat(),
                }
            )

    return pd.DataFrame(rows)


def save_pharmacy_data(
    patients_df: pd.DataFrame,
    purchases_df: pd.DataFrame,
    output_dir: Path = settings.PHARMACY_DIR,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    patients_df.to_csv(output_dir / "patients.csv", index=False)
    purchases_df.to_csv(output_dir / "purchases.csv", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère la source Pharmacie.")
    parser.add_argument("--patients", type=int, default=settings.DEFAULT_NUM_PATIENTS)
    parser.add_argument("--difficulty", choices=list(settings.DIFFICULTY_LEVELS), default="medium")
    parser.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    args = parser.parse_args()

    master_patients = generate_master_patients(n=args.patients, seed=args.seed)
    distribution_plan = distribute_patients(master_patients, seed=args.seed)

    patients_df = generate_pharmacy_patients(
        master_patients, distribution_plan, args.difficulty, seed=args.seed
    )
    purchases_df = generate_pharmacy_purchases(patients_df, seed=args.seed)
    save_pharmacy_data(patients_df, purchases_df)

    print(f"✓ Pharmacie : {len(patients_df)} patients, {len(purchases_df)} achats")
    print(f"✓ Fichiers : {settings.PHARMACY_DIR}")


if __name__ == "__main__":
    main()

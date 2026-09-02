"""
Étape 2 — Patient Generator.

Génère la population de patients maîtres (identité "propre") et
construit le Ground Truth : data/ground_truth/master_patients.csv

Chaque patient reçoit :
- un master_id unique (GT000001, GT000002, ...)
- une identité générée par Faker (nom, prénom, date de naissance, genre,
  téléphone au format malgache, email, adresse)

Ce fichier constitue la "vérité absolue" : il ne doit jamais être fourni
tel quel à l'algorithme de déduplication (voir Règle fondamentale du doc).
"""

from __future__ import annotations

import argparse
import random
from dataclasses import asdict, dataclass

import pandas as pd
from faker import Faker

from config import settings


@dataclass
class MasterPatient:
    master_id: str
    first_name: str
    last_name: str
    birth_date: str
    gender: str
    phone: str
    email: str
    address: str


def _generate_mg_phone_number(rng: random.Random) -> str:
    """Génère un numéro de téléphone malgache réaliste, ex: 0341234567."""
    prefix = rng.choice(settings.MG_PHONE_PREFIXES)
    suffix = "".join(str(rng.randint(0, 9)) for _ in range(7))
    return f"{prefix}{suffix}"


def generate_master_patients(
    n: int = settings.DEFAULT_NUM_PATIENTS,
    seed: int = settings.RANDOM_SEED,
    locale: str = settings.FAKER_LOCALE,
) -> pd.DataFrame:
    """Génère `n` patients maîtres uniques et retourne un DataFrame Ground Truth."""
    faker = Faker(locale)
    Faker.seed(seed)
    rng = random.Random(seed)

    patients: list[MasterPatient] = []
    for i in range(1, n + 1):
        gender = rng.choice(["M", "F"])
        first_name = faker.first_name_male() if gender == "M" else faker.first_name_female()
        last_name = faker.last_name()

        patient = MasterPatient(
            master_id=f"GT{i:06d}",
            first_name=first_name,
            last_name=last_name,
            birth_date=faker.date_of_birth(minimum_age=0, maximum_age=95).isoformat(),
            gender=gender,
            phone=_generate_mg_phone_number(rng),
            email=faker.unique.email(),
            address=faker.city(),
        )
        patients.append(patient)

    return pd.DataFrame([asdict(p) for p in patients])


def save_master_patients(df: pd.DataFrame) -> None:
    """Exporte le Ground Truth vers data/ground_truth/master_patients.csv."""
    settings.GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.MASTER_PATIENTS_FILE, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Génère les patients maîtres (Ground Truth).")
    parser.add_argument(
        "--patients",
        type=int,
        default=settings.DEFAULT_NUM_PATIENTS,
        help="Nombre de patients uniques à générer.",
    )
    parser.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    args = parser.parse_args()

    df = generate_master_patients(n=args.patients, seed=args.seed)
    save_master_patients(df)

    print(f"✓ {len(df)} Ground Truth Patients générés")
    print(f"✓ Fichier : {settings.MASTER_PATIENTS_FILE}")


if __name__ == "__main__":
    main()

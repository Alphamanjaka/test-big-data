"""
Utilitaires partagés par les Source Generators (Étape 5).
"""

from __future__ import annotations

import random
from datetime import date, timedelta

import pandas as pd

from generator.variation_engine import apply_variations


def build_source_patients(
    master_patients: pd.DataFrame,
    distribution_plan: pd.DataFrame,
    source: str,
    difficulty: str,
    seed: int,
) -> pd.DataFrame:
    """
    Sélectionne les patients affectés à `source` dans le plan de distribution,
    et leur applique le Variation Engine (Étape 4) pour "salir" leur identité.

    Retourne un DataFrame avec les colonnes : local_id, master_id, first_name,
    last_name, birth_date, phone — à mapper ensuite vers le schéma propre à
    chaque source (noms de colonnes différents, cf. hétérogénéité volontaire).
    """
    rng = random.Random(seed)
    merged = distribution_plan[distribution_plan["source"] == source].merge(
        master_patients, on="master_id", how="left"
    )

    rows: list[dict] = []
    for _, row in merged.iterrows():
        clean_patient = {
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "birth_date": row["birth_date"],
            "phone": row["phone"],
        }
        varied = apply_variations(clean_patient, difficulty, rng)
        rows.append(
            {
                "local_id": row["local_id"],
                "master_id": row["master_id"],
                "first_name": varied["first_name"],
                "last_name": varied["last_name"],
                "birth_date": varied["birth_date"],
                "phone": varied["phone"],
            }
        )

    return pd.DataFrame(rows)


def random_date_between(start: date, end: date, rng: random.Random) -> date:
    """Tire une date aléatoire (bornes incluses) entre `start` et `end`."""
    delta_days = (end - start).days
    return start + timedelta(days=rng.randint(0, delta_days))

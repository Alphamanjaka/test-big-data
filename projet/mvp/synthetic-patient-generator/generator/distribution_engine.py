"""
Étape 3 — Distribution Engine.

Responsabilités (cf. plan d'implémentation) :
- choisir, pour chaque patient du Ground Truth, dans quelle(s) source(s)
  il apparaît (pharmacie / consultation / imagerie) ;
- distribuer les patients dans ces sources ;
- générer les IDs locaux propres à chaque source
  (ex: GT000001 -> PH000001, MED000001, IMG000001).

Le résultat est un plan de distribution (data/ground_truth/distribution_plan.csv)
qui sert de base à l'Étape 5 (Source Generators, qui génèrent les CSV finaux
par source) et à l'Étape 6 (Identity Mapping).
"""

from __future__ import annotations

import argparse
import random

import pandas as pd

from config import settings
from generator.patient_generator import generate_master_patients


def _generate_local_id(source: str, counter: int) -> str:
    """Génère un ID local propre à une source, ex: PH000001, MED000042."""
    prefix = settings.SOURCE_ID_PREFIXES[source]
    return f"{prefix}{counter:06d}"


def distribute_patients(
    master_patients: pd.DataFrame,
    seed: int = settings.RANDOM_SEED,
) -> pd.DataFrame:
    """
    Distribue chaque patient du Ground Truth dans une ou plusieurs sources.

    Retourne un DataFrame avec une ligne par (master_id, source), colonnes :
    master_id, source, local_id.

    Chaque patient apparaît dans chaque source selon
    `settings.SOURCE_PRESENCE_PROBABILITY`. Un patient qui ne serait tiré
    dans aucune source est forcé à en rejoindre une, aléatoirement, pour
    éviter les patients "fantômes" absents de toute donnée.
    """
    rng = random.Random(seed)
    sources = settings.SOURCES

    # Compteurs séquentiels indépendants par source, pour des IDs locaux stables
    counters = {source: 0 for source in sources}
    rows: list[dict] = []

    for master_id in master_patients["master_id"]:
        chosen_sources = [
            source
            for source in sources
            if rng.random() < settings.SOURCE_PRESENCE_PROBABILITY[source]
        ]

        if not chosen_sources:
            chosen_sources = [rng.choice(sources)]

        for source in chosen_sources:
            counters[source] += 1
            rows.append(
                {
                    "master_id": master_id,
                    "source": source,
                    "local_id": _generate_local_id(source, counters[source]),
                }
            )

    return pd.DataFrame(rows, columns=["master_id", "source", "local_id"])


def save_distribution_plan(df: pd.DataFrame) -> None:
    """Exporte le plan de distribution vers data/ground_truth/distribution_plan.csv."""
    settings.GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(settings.DISTRIBUTION_PLAN_FILE, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description="Distribue les patients dans les sources.")
    parser.add_argument(
        "--patients",
        type=int,
        default=settings.DEFAULT_NUM_PATIENTS,
        help="Nombre de patients maîtres à générer avant distribution.",
    )
    parser.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    args = parser.parse_args()

    master_patients = generate_master_patients(n=args.patients, seed=args.seed)
    plan = distribute_patients(master_patients, seed=args.seed)
    save_distribution_plan(plan)

    print(f"✓ {len(master_patients)} patients distribués dans {len(settings.SOURCES)} sources")
    for source in settings.SOURCES:
        count = (plan["source"] == source).sum()
        print(f"  - {source}: {count} occurrences")
    print(f"✓ Fichier : {settings.DISTRIBUTION_PLAN_FILE}")


if __name__ == "__main__":
    main()

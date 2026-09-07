"""
Étape 6 — Identity Mapping.

Génère automatiquement data/ground_truth/identity_mapping.csv à partir du
plan de distribution (Étape 3) : la correspondance réelle entre chaque
identifiant local (dans une source) et le `master_id` du Ground Truth.

⚠️ Ce fichier ne doit jamais être fourni à l'algorithme de déduplication.
Il est réservé à l'évaluation (calcul de précision / rappel du matching).
"""

from __future__ import annotations

import argparse

import pandas as pd

from config import settings
from generator.distribution_engine import distribute_patients
from generator.patient_generator import generate_master_patients


def build_identity_mapping(distribution_plan: pd.DataFrame) -> pd.DataFrame:
    """
    Construit le fichier de vérité au format exact du document :

        source,source_patient_id,ground_truth_id
        pharmacy,PH000001,GT000001
        consultation,MED000001,GT000001
        imaging,IMG000001,GT000001
    """
    mapping = distribution_plan.rename(
        columns={"local_id": "source_patient_id", "master_id": "ground_truth_id"}
    )
    return mapping[["source", "source_patient_id", "ground_truth_id"]]


def save_identity_mapping(mapping: pd.DataFrame) -> None:
    settings.GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(settings.IDENTITY_MAPPING_FILE, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Génère le fichier de vérité identity_mapping.csv."
    )
    parser.add_argument("--patients", type=int, default=settings.DEFAULT_NUM_PATIENTS)
    parser.add_argument("--seed", type=int, default=settings.RANDOM_SEED)
    args = parser.parse_args()

    master_patients = generate_master_patients(n=args.patients, seed=args.seed)
    distribution_plan = distribute_patients(master_patients, seed=args.seed)
    mapping = build_identity_mapping(distribution_plan)
    save_identity_mapping(mapping)

    sources_per_gt = mapping.groupby("ground_truth_id")["source"].nunique()
    n_multi_source = (sources_per_gt > 1).sum()

    print(f"✓ {len(mapping)} correspondances écrites")
    for source in settings.SOURCES:
        count = (mapping["source"] == source).sum()
        print(f"  - {source}: {count} identités locales")
    print(f"✓ {n_multi_source} patients présents dans plusieurs sources")
    print(f"✓ Fichier : {settings.IDENTITY_MAPPING_FILE}")


if __name__ == "__main__":
    main()

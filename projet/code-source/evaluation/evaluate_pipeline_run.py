"""
Évalue un run du pipeline Big Data complet sur la vérité terrain.

`evaluate_engine.py` mesure le moteur seul, appliqué directement aux fichiers CSV.
Ce script mesure la chaîne entière : extraction RAW, mapping FHIR, SILVER, moteur,
puis chargement de la base centrale. Il lit la table de correspondance
(`patient_identity_map`) écrite par le pipeline et la compare à la vérité terrain
du jeu qui a servi de source (`--level`, ou `--truth` pour un autre jeu), avec les
mêmes métriques par paires.

Prérequis : le pipeline a été lancé sur les fichiers du jeu évalué (copiés dans
`data/raw/`), avec `DATABASE_URL` pointant vers la base centrale.

`--parity` compare en plus la table de correspondance écrite par Spark aux décisions
du moteur de référence (`engine.identity.matcher`) appliqué aux fichiers d'entrée du
pipeline (`data/raw/`) : mêmes identifiants de patients maîtres attendus.

Usage :
    DATABASE_URL=postgresql://... python evaluation/evaluate_pipeline_run.py --level hard [--parity]
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evaluation import evaluate_engine  # noqa: E402
from evaluation.evaluate_engine import ground_truth_path, pairs_metrics  # noqa: E402


def load_truth(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return {(r["source"], r["source_patient_id"]): r["ground_truth_id"] for r in csv.DictReader(f)}


def load_pipeline_predictions(conn) -> tuple:
    """Correspondances écrites par le pipeline ; l'identifiant SILVER porte le préfixe de sa source."""
    pred, methods = {}, {}
    with conn.cursor() as cur:
        cur.execute(
            "SELECT source_system, source_patient_id, master_patient_id, match_method "
            "FROM patient_identity_map"
        )
        for source, source_id, master, method in cur.fetchall():
            prefix = source + "_"
            key = (source, source_id[len(prefix):] if source_id.startswith(prefix) else source_id)
            pred[key] = master
            methods[key] = method
    return pred, methods


def parity(raw_dir: Path, db_masters: dict) -> int:
    """Compare les patients maîtres écrits par le pipeline à ceux du moteur de référence.

    Les identifiants SILVER portent le préfixe de leur source (`pharmacy_PH000001`) :
    le moteur de référence reçoit les mêmes identifiants, pour que les patients
    maîtres des fiches isolées (dérivés de la fiche) soient comparables.
    """
    from dataclasses import replace

    from engine.identity.matcher import deduplicate

    evaluate_engine.experiment_dir = lambda level: raw_dir
    patients = [replace(p, source_patient_id=f"{p.source_system}_{p.source_patient_id}")
                for p in evaluate_engine.load_canonical("raw")]
    reference = {(d.source_system, d.source_patient_id): d.master_patient_id for d in deduplicate(patients)}
    common = [k for k in reference if k in db_masters]
    differences = [k for k in common if reference[k] != db_masters[k]]
    print(f"Parité : {len(common)} fiches comparées (référence {len(reference)}, base {len(db_masters)}), "
          f"{len(differences)} différence(s) de patient maître")
    for key in differences[:10]:
        print(f"  {key} : pipeline {db_masters[key]} / référence {reference[key]}")
    return 0 if common and not differences else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Évalue le run du pipeline sur la vérité terrain.")
    parser.add_argument("--level", default="hard", choices=["easy", "medium", "hard"])
    parser.add_argument(
        "--truth", type=Path, default=None,
        help="identity_mapping.csv d'un autre jeu (ex. data/experiments_12000/easy/ground_truth/...)",
    )
    parser.add_argument("--parity", action="store_true",
                        help="compare aussi au moteur de référence appliqué aux fichiers de data/raw")
    parser.add_argument("--raw-dir", type=Path,
                        default=evaluate_engine.GENERATOR_ROOT / "data" / "raw")
    args = parser.parse_args()

    import psycopg

    truth_path = args.truth or ground_truth_path(args.level)
    truth = load_truth(truth_path)
    print(f"Vérité terrain : {truth_path}")
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        pred, methods = load_pipeline_predictions(conn)
        if args.parity:
            with conn.cursor() as cur:
                cur.execute("SELECT source_system, source_patient_id, master_patient_id FROM patient_identity_map")
                db_masters = {(s, i): m for s, i, m in cur.fetchall()}
    covered = sum(1 for k in truth if k in pred)
    m = pairs_metrics(truth, pred)
    print(f"{len(truth)} fiches de vérité, {covered} retrouvées dans la base centrale")
    print(f"Patients maîtres prédits : {m['n_masters']} (vérité : {m['n_groups_truth']})")
    print(f"TP={m['tp']} FP={m['fp']} FN={m['fn']}  "
          f"précision={m['precision']:.3f} rappel={m['recall']:.3f} F1={m['f1']:.3f}")
    counts = {}
    for k in truth:
        if k in methods:
            counts[methods[k]] = counts.get(methods[k], 0) + 1
    print("Méthodes :", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    if args.parity:
        return parity(args.raw_dir, db_masters)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

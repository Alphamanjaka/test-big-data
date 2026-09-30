"""
Évaluateur par vérité terrain — compare la déduplication du moteur `engine`
(règle d'identité stricte, `engine.identity.matcher`) à la vérité de référence
(identity_mapping.csv) d'un jeu synthétique : niveaux easy / medium / hard, ou
tout dossier de jeu produit par le générateur (`--dir`).

Métriques par paires (standard Entity Resolution) :
    Précision (Pair Quality)     = VP / (VP + FP)
    Rappel   (Pair Completeness) = VP / (VP + FN)
    F1                             = 2.P.R / (P + R)

La variante Spark (`engine.identity.spark_dedup`) applique les mêmes fonctions
de règle ; sa parité se vérifie sur la VM (`evaluate_pipeline_run.py --parity`).

Usage :
    python evaluation/evaluate_engine.py --level hard
    python evaluation/evaluate_engine.py --dir evaluation/synthetic-patient-generator/data/experiments_100000/easy
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

import engine.identity.matcher as matcher
from engine.identity.canonical import map_patient

ROOT = Path(__file__).resolve().parent.parent
GENERATOR_ROOT = ROOT / "evaluation" / "synthetic-patient-generator"
COLS = {
    "pharmacy": ["client_id", "nom_complet", "naissance", "cin", "ville_naissance", "adresse", "sexe"],
    "consultation": ["patient_code", "prenom", "nom", "date_naiss", "no_cin", "ville_nai", "genre"],
    "imaging": ["id_personne", "patient_name", "dob", "cin_number", "birth_place", "sex"],
}
SOURCE_ORDER = ["pharmacy", "consultation", "imaging"]


def experiment_dir(level: str) -> Path:
    return GENERATOR_ROOT / "data" / "experiments" / level


def ground_truth_path(level: str) -> Path:
    return experiment_dir(level) / "ground_truth" / "identity_mapping.csv"


def ensure_dataset(level: str, patients: int, seed: int) -> None:
    """Régénère le dataset du niveau si la vérité de référence est absente."""
    if ground_truth_path(level).exists():
        return
    sys.path.insert(0, str(GENERATOR_ROOT))
    from generator.experiment_builder import build_all_experiments
    build_all_experiments(n_patients=patients, seed=seed)


# ---------------------------------------------------------------------------
# Chargement des sources → patients canoniques (ordre d'ingestion)
# ---------------------------------------------------------------------------
def load_canonical(level: str) -> list:
    root = experiment_dir(level)
    patients: list = []
    for system in SOURCE_ORDER:
        path = root / system / "patients.csv"
        frame = pd.read_csv(path, dtype=str).fillna("")
        patients.extend(
            map_patient(row, system) for _, row in frame.iterrows()
        )
    return patients


# ---------------------------------------------------------------------------
# Prédictions
# ---------------------------------------------------------------------------
def predictions(level: str):
    decisions = matcher.deduplicate(load_canonical(level))
    pred = {(d.source_system, d.source_patient_id): d.master_patient_id for d in decisions}
    methods = {(d.source_system, d.source_patient_id): d.method for d in decisions}
    print(f"[moteur] {len(decisions)} décisions")
    return pred, methods


# ---------------------------------------------------------------------------
# Métriques par paires — implémentation analytique (O(n))
# ---------------------------------------------------------------------------
def _c2(n: int) -> int:
    return n * (n - 1) // 2


def pairs_metrics(truth: dict, pred: dict, relevant: set | None = None) -> dict:
    truth_by_group: dict[str, list] = {}
    for key, group in truth.items():
        truth_by_group.setdefault(group, []).append(key)
    pred_by_group: dict[str, list] = {}
    for key, group in pred.items():
        if key in truth:
            pred_by_group.setdefault(group, []).append(key)

    rel_of = {k: 1 for k in truth}
    if relevant is not None:
        for k in truth:
            rel_of[k] = 1 if k in relevant else 0

    def pairs_in(total: int, rel: int) -> int:
        return _c2(total) - _c2(total - rel)

    cell: dict[tuple[str, str], tuple[int, int]] = {}
    for members in pred_by_group.values():
        for k in members:
            t = (pred[k], truth[k])
            tot, rel = cell.get(t, (0, 0))
            cell[t] = (tot + 1, rel + rel_of[k])

    pred_cells: dict[str, dict[str, tuple[int, int]]] = {}
    for (pg, tg), (tot, rel) in cell.items():
        pred_cells.setdefault(pg, {})[tg] = (tot, rel)
    tp = fp = 0
    for pg, tg_cells in pred_cells.items():
        pred_total = sum(t for t, _ in tg_cells.values())
        pred_rel = sum(r for _, r in tg_cells.values())
        pred_pairs = pairs_in(pred_total, pred_rel)
        truth_same = sum(pairs_in(t, r) for t, r in tg_cells.values())
        tp += truth_same
        fp += pred_pairs - truth_same

    truth_cells: dict[str, dict[str, tuple[int, int]]] = {}
    for (pg, tg), (tot, rel) in cell.items():
        truth_cells.setdefault(tg, {})[pg] = (tot, rel)
    fn = 0
    for tg, pg_cells in truth_cells.items():
        truth_total = sum(t for t, _ in pg_cells.values())
        truth_rel = sum(r for _, r in pg_cells.values())
        truth_pairs = pairs_in(truth_total, truth_rel)
        pred_same = sum(pairs_in(t, r) for t, r in pg_cells.values())
        fn += truth_pairs - pred_same

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "n_masters": len(pred_by_group),
        "n_groups_truth": len(truth_by_group),
    }


def method_breakdown(truth: dict, pred: dict, methods: dict) -> dict[str, dict]:
    out = {}
    for method in sorted(set(methods.values())):
        relevant = {k for k in truth if methods.get(k) == method}
        if not relevant:
            continue
        out[method] = pairs_metrics(truth, pred, relevant=relevant)
    return out


def source_breakdown(truth: dict, pred: dict) -> dict[str, dict]:
    return {
        source: pairs_metrics(truth, pred, relevant={k for k in truth if k[0] == source})
        for source in SOURCE_ORDER
    }


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------
def build_report(level: str) -> str:
    frame = pd.read_csv(ground_truth_path(level), dtype=str)
    truth = {(r["source"], r["source_patient_id"]): r["ground_truth_id"] for _, r in frame.iterrows()}
    pred, methods = predictions(level)
    m = pairs_metrics(truth, pred)

    lines = [
        f"# Évaluation par vérité terrain — jeu `{level}`",
        "",
        f"- Date : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Vérité terrain : {ground_truth_path(level)}",
        "- Moteur : règle d'identité stricte (CIN, genre, date et ville de naissance identiques ; "
        "sans CIN, nom identique en plus)",
        f"- Fiches : {len(truth)}",
        "",
        "| Métrique | Valeur |",
        "|---|---|",
        f"| Patients maîtres prédits | {m['n_masters']} |",
        f"| Groupes de la vérité | {m['n_groups_truth']} |",
        f"| Vrais positifs (paires) | {m['tp']} |",
        f"| Faux positifs (fusions à tort) | {m['fp']} |",
        f"| Faux négatifs (fusions manquées) | {m['fn']} |",
        f"| Précision | {m['precision']:.3f} |",
        f"| Rappel | {m['recall']:.3f} |",
        f"| F1 | {m['f1']:.3f} |",
        "",
        "## Rappel par source",
        "",
        "> Rappel = fraction des paires de référence impliquant la source, correctement regroupées.",
        "",
        "| Source | Rappel |",
        "|---|---|",
    ]
    for source, sm in source_breakdown(truth, pred).items():
        lines.append(f"| {source} | {sm['recall']:.3f} |")
    counts = {}
    for method in methods.values():
        counts[method] = counts.get(method, 0) + 1
    lines += ["", "Décisions : " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())),
              "", f"VP={m['tp']} FP={m['fp']} FN={m['fn']} | Précision={m['precision']:.3f} "
              f"Rappel={m['recall']:.3f} F1={m['f1']:.3f}"]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue la déduplication sur la vérité terrain.")
    parser.add_argument("--level", choices=["easy", "medium", "hard"], default="medium")
    parser.add_argument("--dir", type=Path, default=None,
                        help="dossier d'un autre jeu du générateur (ex. data/experiments_100000/easy)")
    parser.add_argument("--patients", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.dir is not None:
        global experiment_dir
        experiment_dir = lambda level: args.dir  # noqa: E731
        level = str(args.dir)
        print(build_report(level))
        return
    ensure_dataset(args.level, args.patients, args.seed)
    report = build_report(args.level)
    out = ROOT / "evaluation" / "evaluation_truth.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nRapport écrit : {out}")


if __name__ == "__main__":
    main()

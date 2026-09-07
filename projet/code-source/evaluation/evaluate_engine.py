"""
Évaluateur Ground Truth — compare la de-duplication du moteur `engine`
(matcher Pandas N1 et/ou spark_dedup driver-side) à la vérité de référence
(identity_mapping.csv) d'un niveau de difficulté (easy / medium / hard).

Métriques par paires (standard Entity Resolution) :
    Precision (Pair Quality)     = TP / (TP + FP)
    Recall   (Pair Completeness) = TP / (TP + FN)
    F1                             = 2.P.R / (P + R)

Usage :
    python evaluation/evaluate_engine.py --level medium [--only mvp|spark]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

import pandas as pd

import engine.identity.matcher as matcher
import engine.identity.spark_dedup as spark_dedup
from engine.identity.canonical import map_patient

ROOT = Path(__file__).resolve().parent.parent
GENERATOR_ROOT = ROOT / "evaluation" / "synthetic-patient-generator"
COLS = {
    "pharmacy": ["client_id", "nom_complet", "naissance", "telephone", "adresse", "sexe"],
    "consultation": ["patient_code", "prenom", "nom", "date_naiss", "phone_number", "genre"],
    "imaging": ["id_personne", "patient_name", "dob", "tel", "sex"],
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
# Chargement des sources → patients canoniques (ordre d'ingestion MVP)
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
def predictions_mvp(level: str, only: str | None = None):
    if only == "spark":
        return None
    patients = load_canonical(level)
    decisions = matcher.deduplicate(patients)
    pred = {(d.source_system, d.source_patient_id): d.master_patient_id for d in decisions}
    methods = {(d.source_system, d.source_patient_id): d.method for d in decisions}
    print(f"[MVP] {len(decisions)} decisions")
    return pred, methods


def predictions_spark(level: str, only: str | None = None):
    if only == "mvp":
        return None
    patients = load_canonical(level)
    rows = [
        {
            "source_system": p.source_system,
            "source_patient_id": p.source_patient_id,
            "full_name": p.full_name,
            "birth_date": p.birth_date,
            "phone": p.phone,
        }
        for p in patients
    ]
    decisions = spark_dedup.deduplicate(rows)
    pred = {(d["source_system"], d["source_patient_id"]): d["master_patient_id"] for d in decisions}
    methods = {(d["source_system"], d["source_patient_id"]): d["method"] for d in decisions}
    print(f"[Spark] {len(decisions)} decisions")
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
def build_report(level: str, only: str | None = None) -> str:
    frame = pd.read_csv(ground_truth_path(level), dtype=str)
    truth = {(r["source"], r["source_patient_id"]): r["ground_truth_id"] for _, r in frame.iterrows()}

    mvp = predictions_mvp(level, only)
    spark = predictions_spark(level, only)
    mvp_m = pairs_metrics(truth, mvp[0]) if mvp else None
    spark_m = pairs_metrics(truth, spark[0]) if spark else None

    def fmt(cell, nd=3) -> str:
        return "—" if cell is None else f"{cell:.{nd}f}"

    def fmt_count(cell) -> str:
        return "—" if cell is None else str(cell)

    lines = [
        f"# Évaluation Ground Truth — Niveau `{level}`",
        "",
        f"- Date : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Ground Truth : {ground_truth_path(level)}",
        f"- Data root : {experiment_dir(level)}",
        f"- Mode : {'MVP' if only == 'mvp' else ('Spark' if only == 'spark' else 'MVP + Spark')}",
        f"- Enregistrements : {len(truth)}",
        "",
        "## Comparaison MVP (Pandas) vs Spark",
        "",
        "| Métrique | MVP (Pandas) | Spark |",
        "|---|---|---|",
    ]
    for key, label in [
        ("n_masters", "Masters prédits"),
        ("n_groups_truth", "Groupes vérité"),
        ("tp", "Vrais positifs (paires)"),
        ("fp", "Faux positifs (fusion à tort)"),
        ("fn", "Faux négatifs (non-fusion)"),
        ("precision", "Precision (Pair Quality)"),
        ("recall", "Recall (Pair Completeness)"),
        ("f1", "F1"),
    ]:
        if key in ("precision", "recall", "f1"):
            lines.append(f"| {label} | {fmt(mvp_m[key]) if mvp_m else '—'} | {fmt(spark_m[key]) if spark_m else '—'} |")
        else:
            lines.append(f"| {label} | {fmt_count(mvp_m[key]) if mvp_m else '—'} | {fmt_count(spark_m[key]) if spark_m else '—'} |")

    lines += ["", "## Precision / Rappel / F1 par type de match", "", "| Méthode | MVP | Spark |", "|---|---|---|"]
    mvp_bm = method_breakdown(truth, mvp[0], mvp[1]) if mvp else {}
    spark_bm = method_breakdown(truth, spark[0], spark[1]) if spark else {}
    for method in sorted(set(list(mvp_bm) + list(spark_bm))):
        if method == "new_master":
            continue
        m = mvp_bm.get(method)
        s = spark_bm.get(method)
        m_str = f"{m['precision']:.3f}/{m['recall']:.3f}/{m['f1']:.3f}" if m else "—"
        s_str = f"{s['precision']:.3f}/{s['recall']:.3f}/{s['f1']:.3f}" if s else "—"
        lines.append(f"| {method} | {m_str} | {s_str} |")

    lines += ["", "## Contribution par source (rappel)", "", "> Rappel = fraction des paires de reference impliquant la source, correctement regroupees.", "", "| Source | MVP | Spark |", "|---|---|---|"]
    mvp_src = source_breakdown(truth, mvp[0]) if mvp else {}
    spark_src = source_breakdown(truth, spark[0]) if spark else {}
    for source in SOURCE_ORDER:
        mvp_r = f"{mvp_src[source]['recall']:.3f}" if source in mvp_src else "—"
        spark_r = f"{spark_src[source]['recall']:.3f}" if source in spark_src else "—"
        lines.append(f"| {source} | {mvp_r} | {spark_r} |")

    lines.append("")
    if mvp_m:
        lines.append(f"- MVP  : TP={mvp_m['tp']} FP={mvp_m['fp']} FN={mvp_m['fn']} | Precision={mvp_m['precision']:.3f} Recall={mvp_m['recall']:.3f} F1={mvp_m['f1']:.3f}")
    if spark_m:
        lines.append(f"- Spark: TP={spark_m['tp']} FP={spark_m['fp']} FN={spark_m['fn']} | Precision={spark_m['precision']:.3f} Recall={spark_m['recall']:.3f} F1={spark_m['f1']:.3f}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue la déduplication vs Ground Truth.")
    parser.add_argument("--level", choices=["easy", "medium", "hard"], default="medium")
    parser.add_argument("--only", choices=["mvp", "spark"], default=None)
    parser.add_argument("--patients", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    ensure_dataset(args.level, args.patients, args.seed)
    report = build_report(args.level, only=args.only)
    out = ROOT / "evaluation" / "evaluation_truth.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nRapport écrit : {out}")


if __name__ == "__main__":
    main()
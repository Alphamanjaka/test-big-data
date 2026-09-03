"""
Évaluateur Ground Truth — compare le résultat de la déduplication
(MVP Pandas N1 et/ou Spark N2) au regroupement de référence
(identity_mapping.csv) pour un niveau de difficulté donné.

Évaluation par paires (standard Entity Resolution) :
    TP : même master prédit ET même ground_truth_id
    FP : même master prédit, ground_truth différents (fusion à tort)
    FN : ground_truth identiques, masters différents (non-fusion)
    TN : masters différents et ground_truth différents

    Precision (Pair Quality)      = TP / (TP + FP)
    Recall   (Pair Completeness)  = TP / (TP + FN)
    F1                             = 2.P.R / (P + R)

Usage :
    python evaluation_truth.py --level medium [--only mvp|spark] [--patients N --seed S]
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Callable

import pandas as pd

from patient_platform.config import load_data_root, load_sources
from patient_platform.logging_utils import RuntimeLogger
from patient_platform.pipeline import run_pipeline
from patient_platform.spark.csv_extractor import SparkCSVExtractor
from patient_platform.spark.deduplication import deduplicate as spark_deduplicate
from patient_platform.spark.session import get_or_create_session
from patient_platform.spark.transform import standardize_patients

ROOT = Path(__file__).resolve().parent
SOURCE_ORDER = ["pharmacy", "consultation", "imaging"]

LOGGER = RuntimeLogger("logs/runtime.log", "LOGS.md")


def _eval_log(step: str, **fields: object) -> None:
    LOGGER.info(step, **fields)


# ---------------------------------------------------------------------------
# Chargement de la vérité de référence
# ---------------------------------------------------------------------------
def ground_truth_path(level: str) -> Path:
    return ROOT / "synthetic-patient-generator" / "data" / "experiments" / level / \
        "ground_truth" / "identity_mapping.csv"


def ensure_dataset(level: str, patients: int, seed: int) -> None:
    """Régénère le dataset du niveau si la vérité de référence est absente."""
    path = ground_truth_path(level)
    if path.exists():
        return
    import sys
    sys.path.insert(0, str(ROOT / "synthetic-patient-generator"))
    from generator.experiment_builder import build_all_experiments
    build_all_experiments(n_patients=patients, seed=seed)


def load_ground_truth(level: str) -> dict[tuple[str, str], str]:
    path = ground_truth_path(level)
    frame = pd.read_csv(path, dtype=str)
    _eval_log("ground_truth", level=level, path=str(path),
              rows_read=len(frame), status="loaded")
    mapping = {
        (row["source"], row["source_patient_id"]): row["ground_truth_id"]
        for _, row in frame.iterrows()
    }
    for index, (key, group) in enumerate(mapping.items()):
        _eval_log("ground_truth_line", source=key[0],
                  source_patient_id=key[1], ground_truth_id=group,
                  row_number=index + 1, status="registered")
    return mapping


# ---------------------------------------------------------------------------
# Prédictions
# ---------------------------------------------------------------------------
def _decisions_from_pipeline(data_root: Path) -> list:
    result = run_pipeline(data_root, "logs/runtime.log", "LOGS.md")
    return list(result.identity_map)


def predictions_mvp(data_root: Path, level: str,
                    only: str | None = None) -> tuple[dict, dict] | None:
    if only == "spark":
        _eval_log("predictions", engine="mvp", status="skipped")
        return None
    decisions = _decisions_from_pipeline(data_root)
    pred = {(d.source_system, d.source_patient_id): d.master_patient_id for d in decisions}
    methods = {(d.source_system, d.source_patient_id): d.method for d in decisions}
    _eval_log("predictions", engine="mvp", level=level,
              decisions=len(decisions), status="built")
    for index, (key, group) in enumerate(pred.items()):
        _eval_log("prediction_line", engine="mvp", source=key[0],
                  source_patient_id=key[1], master_patient_id=group,
                  method=methods[key], row_number=index + 1, status="predicted")
    return pred, methods


def predictions_spark(sources, level: str,
                      only: str | None = None) -> tuple[dict, dict] | None:
    if only == "mvp":
        _eval_log("predictions", engine="spark", status="skipped")
        return None
    spark = get_or_create_session()
    try:
        frames = [
            standardize_patients(SparkCSVExtractor(
                sources[system]["patient_source"], system).extract(), system)
            for system in SOURCE_ORDER
        ]
        decisions = spark_deduplicate(*frames).collect()
    finally:
        spark.stop()
    pred = {(d.source_system, d.source_patient_id): d.master_patient_id for d in decisions}
    methods = {(d.source_system, d.source_patient_id): d.method for d in decisions}
    _eval_log("predictions", engine="spark", level=level,
              decisions=len(decisions), status="built")
    for index, (key, group) in enumerate(pred.items()):
        _eval_log("prediction_line", engine="spark", source=key[0],
                  source_patient_id=key[1], master_patient_id=group,
                  method=methods[key], row_number=index + 1, status="predicted")
    return pred, methods


# ---------------------------------------------------------------------------
# Métriques par paires — implémentation analytique (O(n), adaptée aux gros volumes)
# ---------------------------------------------------------------------------
def _c2(n: int) -> int:
    """Nombre de paires (i<j) parmi n éléments."""
    return n * (n - 1) // 2


def pairs_metrics(truth: dict[tuple[str, str], str],
                  pred: dict[tuple[str, str], str],
                  relevant: set | None = None) -> dict:
    """
    Métriques par paires (standard Entity Resolution), calculées par comptage
    analytique sur les intersections de groupes (pas de génération de paires).

    TP : paires même master prédit ET même groupe vérité.
    FP : paires même master prédit mais groupes vérité différents.
    FN : paires même groupe vérité mais masters prédits différents.

    `relevant` : set optionnel de clés (source, id). Si fourni, seules les
    paires dont AU MOINS un membre est pertinent sont comptées (sert aux
    décompositions par source / par méthode).
    """
    truth_by_group: dict[str, list] = {}
    for key, group in truth.items():
        truth_by_group.setdefault(group, []).append(key)
    pred_by_group: dict[str, list] = {}
    for key, group in pred.items():
        if key in truth:
            pred_by_group.setdefault(group, []).append(key)

    # Pertinence : 1 si pertinent, sinon 0
    rel_of = {k: 1 for k in truth}
    if relevant is not None:
        for k in truth:
            rel_of[k] = 1 if k in relevant else 0

    def pairs_in_counts(total: int, relevant_count: int) -> int:
        """Paires dont au moins un membre est pertinent, dans un groupe."""
        return _c2(total) - _c2(total - relevant_count)

    # Cellule (master prédit, groupe vérité) : nb total + nb pertinent
    cell: dict[tuple[str, str], tuple[int, int]] = {}
    for mem in pred_by_group.values():
        for k in mem:
            t = (pred[k], truth[k])
            tot, rel = cell.get(t, (0, 0))
            cell[t] = (tot + 1, rel + rel_of[k])

    # TP / FP par master prédit
    pred_cell: dict[str, dict[str, tuple[int, int]]] = {}
    for (pg, tg), (tot, rel) in cell.items():
        pred_cell.setdefault(pg, {})[tg] = (tot, rel)

    tp = 0
    fp = 0
    for pg, tg_cells in pred_cell.items():
        pred_total = sum(t for t, _ in tg_cells.values())
        pred_rel = sum(r for _, r in tg_cells.values())
        pred_pairs = pairs_in_counts(pred_total, pred_rel)
        truth_same = 0
        for tot, rel in tg_cells.values():
            truth_same += pairs_in_counts(tot, rel)
        tp += truth_same
        fp += pred_pairs - truth_same

    # FN par groupe vérité
    truth_cell: dict[str, dict[str, tuple[int, int]]] = {}
    for (pg, tg), (tot, rel) in cell.items():
        truth_cell.setdefault(tg, {})[pg] = (tot, rel)

    fn = 0
    for tg, pg_cells in truth_cell.items():
        truth_total = sum(t for t, _ in pg_cells.values())
        truth_rel = sum(r for _, r in pg_cells.values())
        truth_pairs = pairs_in_counts(truth_total, truth_rel)
        pred_same = 0
        for tot, rel in pg_cells.values():
            pred_same += pairs_in_counts(tot, rel)
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


def source_breakdown(truth: dict, pred: dict) -> dict[str, dict]:
    """
    Rappel par source : parmi les paires de référence (GT) impliquant la
    source, fraction correctement regroupée par l'algo. Indique la
    contribution de chaque source à la résolution.
    """
    out = {}
    for source in SOURCE_ORDER:
        relevant = {k for k in truth if k[0] == source}
        out[source] = pairs_metrics(truth, pred, relevant=relevant)
    return out


def method_breakdown(truth: dict, pred: dict,
                     methods: dict[tuple[str, str], str]) -> dict[str, dict]:
    """
    Métriques par méthode de match : restreint aux paires dont au moins un
    membre a été assigné par cette méthode. (new_master ne fusionne jamais,
    il est donc exclu comme non pertinent — filtré dans le rapport.)
    """
    out = {}
    for method in sorted(set(methods.values())):
        relevant = {k for k in truth if methods.get(k) == method}
        if not relevant:
            continue
        out[method] = pairs_metrics(truth, pred, relevant=relevant)
    return out


# ---------------------------------------------------------------------------
# Rapport
# ---------------------------------------------------------------------------
def format_metrics(metrics: dict) -> str:
    return (
        f"TP={metrics['tp']} FP={metrics['fp']} FN={metrics['fn']} | "
        f"Precision={metrics['precision']:.3f} Recall={metrics['recall']:.3f} "
        f"F1={metrics['f1']:.3f}"
    )


def build_report(level: str, sources, data_root: Path,
                 only: str | None = None) -> str:
    truth = load_ground_truth(level)
    mvp_pred, mvp_methods = predictions_mvp(data_root, level, only) or (None, None)
    spark_pred, spark_methods = predictions_spark(sources, level, only) or (None, None)

    mvp_m = pairs_metrics(truth, mvp_pred) if mvp_pred else None
    spark_m = pairs_metrics(truth, spark_pred) if spark_pred else None
    for index, key in enumerate(sorted(truth)):
        truth_group = truth[key]
        mvp_master = mvp_pred.get(key) if mvp_pred else None
        spark_master = spark_pred.get(key) if spark_pred else None
        _eval_log("compare_line", source=key[0], source_patient_id=key[1],
                  ground_truth_id=truth_group, mvp_master=mvp_master,
                  spark_master=spark_master,
                  mvp_correct=str(mvp_master == truth_group),
                  spark_correct=str(spark_master == truth_group),
                  row_number=index + 1)

    def fmt(cell: dict | None) -> str:
        return "—" if cell is None else f"{cell:.3f}"

    def fmt_count(value) -> str:
        return "—" if value is None else str(value)

    lines = [
        f"# Évaluation Ground Truth — Niveau `{level}`",
        "",
        f"- Date : {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Ground Truth : {ground_truth_path(level)}",
        f"- Data root : {data_root}",
        f"- Mode : {'MVP' if only == 'mvp' else ('Spark' if only == 'spark' else 'MVP + Spark')}",
        f"- Patients source : {len(truth)}",
        "",
        "## Comparaison MVP (N1) vs Spark (N2)",
        "",
        "| Métrique | MVP (Pandas) | Spark |",
        "|---|---|---|",
    ]
    keys = ["n_masters", "n_groups_truth", "tp", "fp", "fn",
            "precision", "recall", "f1"]
    labels = {
        "n_masters": "Masters prédits",
        "n_groups_truth": "Groupes vérité",
        "tp": "Vrais positifs (paires)",
        "fp": "Faux positifs (fusion à tort)",
        "fn": "Faux négatifs (non-fusion)",
        "precision": "Precision (Pair Quality)",
        "recall": "Recall (Pair Completeness)",
        "f1": "F1",
    }
    for key in keys:
        label = labels[key]
        if key in ("precision", "recall", "f1"):
            mvp_val = fmt(mvp_m[key]) if mvp_m else "—"
            spark_val = fmt(spark_m[key]) if spark_m else "—"
            lines.append(f"| {label} | {mvp_val} | {spark_val} |")
        else:
            mvp_val = fmt_count(mvp_m[key]) if mvp_m else "—"
            spark_val = fmt_count(spark_m[key]) if spark_m else "—"
            lines.append(f"| {label} | {mvp_val} | {spark_val} |")

    lines += [
        "",
        "## Précision / Rappel par type de match",
        "",
        "| Méthode | MVP (P/R/F1) | Spark (P/R/F1) |",
        "|---|---|---|",
    ]
    mvp_by_method = method_breakdown(truth, mvp_pred, mvp_methods) if mvp_pred else {}
    spark_by_method = method_breakdown(truth, spark_pred, spark_methods) if spark_pred else {}
    for method in sorted(set(list(mvp_by_method) + list(spark_by_method))):
        if method == "new_master":
            continue  # new_master ne crée aucun lien ; non pertinent ici
        m = mvp_by_method.get(method)
        s = spark_by_method.get(method)
        m_str = f"{m['precision']:.3f}/{m['recall']:.3f}/{m['f1']:.3f}" if m else "—"
        s_str = f"{s['precision']:.3f}/{s['recall']:.3f}/{s['f1']:.3f}" if s else "—"
        lines.append(f"| {method} | {m_str} | {s_str} |")

    lines += [
        "",
        "## Contribution par source (rappel)",
        "",
        "> Rappel = fraction des paires de référence impliquant la source,",
        "> correctement regroupées par l'algo.",
        "",
        "| Source | MVP (R) | Spark (R) |",
        "|---|---|---|",
    ]
    mvp_src = source_breakdown(truth, mvp_pred) if mvp_pred else {}
    spark_src = source_breakdown(truth, spark_pred) if spark_pred else {}
    for source in SOURCE_ORDER:
        mvp_r = f"{mvp_src[source]['recall']:.3f}" if source in mvp_src else "—"
        spark_r = f"{spark_src[source]['recall']:.3f}" if source in spark_src else "—"
        lines.append(f"| {source} | {mvp_r} | {spark_r} |")

    lines += ["", "## Résumé", "",
              f"- MVP  : {format_metrics(mvp_m)}" if mvp_m else "- MVP  : —",
              f"- Spark: {format_metrics(spark_m)}" if spark_m else "- Spark: —", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Évalue la déduplication vs Ground Truth.")
    parser.add_argument("--level", choices=["easy", "medium", "hard"], default="medium")
    parser.add_argument("--only", choices=["mvp", "spark"], default=None)
    parser.add_argument("--patients", type=int, default=500)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    ensure_dataset(args.level, args.patients, args.seed)
    sources = load_sources()
    data_root = load_data_root()
    report = build_report(args.level, sources, data_root, only=args.only)
    out = ROOT / "evaluation_truth.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nRapport écrit : {out}")


if __name__ == "__main__":
    main()
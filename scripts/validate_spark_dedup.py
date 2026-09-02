from patient_platform.config import load_data_root, load_sources
from patient_platform.deduplication.matcher import deduplicate as pandas_deduplicate, MatchDecision
from patient_platform.pipeline import run_pipeline
from patient_platform.spark.csv_extractor import SparkCSVExtractor
from patient_platform.spark.deduplication import deduplicate as spark_deduplicate
from patient_platform.spark.session import get_or_create_session
from patient_platform.spark.transform import standardize_patients

SOURCE_ORDER = ["pharmacy", "consultation", "imaging"]


def validate():
    sources = load_sources()
    data_root = load_data_root()

    expected = run_pipeline(data_root, "logs/runtime-spark-check.log", "LOGS-spark-check.md")
    expected_map = [
        MatchDecision(d.master_patient_id, d.source_system, d.source_patient_id, d.method, d.score, d.explanation)
        for d in expected.identity_map
    ]
    expected_order = [(d.source_system, d.source_patient_id) for d in expected_map]

    spark = get_or_create_session()
    frames = [standardize_patients(
        SparkCSVExtractor(sources[system]["patient_source"], system).extract(), system)
        for system in SOURCE_ORDER]
    spark_decisions = spark_deduplicate(*frames).collect()
    spark.stop()

    actual_order = [(d.source_system, d.source_patient_id) for d in spark_decisions]
    assert actual_order == expected_order, f"ordre decisions: {actual_order} != {expected_order}"

    by_identity_expected = {
        (d.source_system, d.source_patient_id): (d.master_patient_id, d.method, d.score)
        for d in expected_map
    }
    errors = []
    for decision in spark_decisions:
        key = (decision.source_system, decision.source_patient_id)
        got = (decision.master_patient_id, decision.method, round(decision.score, 3))
        want = by_identity_expected[key]
        if got != want:
            errors.append(f"{key}: Spark={got} MVP={want}")
        print(f"{key} -> {got}")

    if errors:
        raise SystemExit("\n".join(errors))

    masters = {d.master_patient_id for d in spark_decisions}
    jean = next(d for d in spark_decisions
                if d.source_system == "imaging" and d.source_patient_id == "IMG001")
    assert jean.master_patient_id == "PAT-0001" and jean.method == "exact", jean
    nirina = next(d for d in spark_decisions
                  if d.source_system == "consultation" and d.source_patient_id == "53")
    assert nirina.master_patient_id == "PAT-0004" and nirina.method == "probabilistic" \
        and nirina.score == 0.8, nirina
    print(f"VALIDATION DEDUPLICATION OK — {len(spark_decisions)} liens, {len(masters)} masters, "
          f"Jean Rakoto et Nirina (typo tel) conformes au MVP")


if __name__ == "__main__":
    validate()
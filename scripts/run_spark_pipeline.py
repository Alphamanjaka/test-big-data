import psycopg
from dotenv import load_dotenv

from patient_platform.config import load_data_root, load_sources
from patient_platform.pipeline import run_pipeline as pandas_run_pipeline
from patient_platform.spark.csv_extractor import SparkCSVExtractor
from patient_platform.spark.deduplication import deduplicate
from patient_platform.spark.postgres_loader import (
    BUSINESS_SPEC,
    SparkPostgresLoader,
    build_business_frame,
    build_identity_frame,
    build_master_frame,
    build_raw_frame,
)
from patient_platform.spark.session import get_or_create_session
from patient_platform.spark.transform import standardize_patients

SOURCE_ORDER = ["pharmacy", "consultation", "imaging"]


def _fetch(query: str, connection) -> list[tuple]:
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def _validate_integrity(connection, decisions_count: int) -> None:
    tables = {
        "raw_patient_record": 18,
        "master_patient": 11,
        "patient_identity_map": decisions_count,
        "medicine_purchase": 6,
        "patient_consultation": 6,
        "imaging_exam": 6,
    }
    for table, expected in tables.items():
        (actual,) = _fetch(
            f"SELECT count(*) FROM {table}", connection)[0]
        assert actual == expected, f"{table}: count={actual} attendu={expected}"
    (orphans,) = _fetch("""
        SELECT count(*) FROM patient_identity_map m
        LEFT JOIN master_patient p ON p.master_patient_id = m.master_patient_id
        WHERE p.master_patient_id IS NULL
    """, connection)[0]
    assert orphans == 0, f"{orphans} identity links orphelins"
    for table in ("medicine_purchase", "patient_consultation", "imaging_exam"):
        (orphans,) = _fetch(f"""
            SELECT count(*) FROM {table} b
            LEFT JOIN master_patient p ON p.master_patient_id = b.master_patient_id
            WHERE p.master_patient_id IS NULL
        """, connection)[0]
        assert orphans == 0, f"{orphans} {'table'} orphelins"


def run():
    load_dotenv()
    sources = load_sources()
    data_root = load_data_root()

    expected = pandas_run_pipeline(data_root, "logs/runtime-spark-load.log", "LOGS-spark-load.md")
    expected_links = {
        (d.source_system, d.source_patient_id): (d.master_patient_id, d.method, round(d.score, 3))
        for d in expected.identity_map
    }

    spark = get_or_create_session()
    canonical_frames = {
        system: standardize_patients(
            SparkCSVExtractor(sources[system]["patient_source"], system).extract(), system)
        for system in SOURCE_ORDER
    }
    decisions = deduplicate(*[canonical_frames[system] for system in SOURCE_ORDER])

    raw_frames = [
        build_raw_frame(SparkCSVExtractor(
            sources[system]["patient_source"], system).extract(), system)
        for system in SOURCE_ORDER
    ]

    business_raw = {
        system: SparkCSVExtractor(sources[system]["business_source"], system).extract()
        for system in SOURCE_ORDER
    }
    business_frames = {
        BUSINESS_SPEC[system]["table"]: build_business_frame(
            business_raw[system], system, decisions)
        for system in SOURCE_ORDER
    }

    load_frames = {
        "raw_patient_record": raw_frames[0].union(raw_frames[1]).union(raw_frames[2]),
        "master_patient": build_master_frame(decisions, canonical_frames),
        "patient_identity_map": build_identity_frame(decisions),
        **business_frames,
    }

    loader = SparkPostgresLoader()
    rows_written = loader.load(load_frames)
    decisions_count = decisions.count()
    spark.stop()
    print("chargement Spark OK:", rows_written)

    with psycopg.connect(loader.url) as connection:
        _validate_integrity(connection, decisions_count)
        db_links = {
            (system, patient): (master, method, float(score))
            for master, system, patient, method, score, _ in _fetch("""
                SELECT master_patient_id, source_system, source_patient_id,
                       match_method, match_score, explanation
                FROM patient_identity_map
            """, connection)
        }
    assert db_links == expected_links, "identity map Spark/DB != pipeline MVP"
    print(f"VALIDATION PANDAS VS SPARK OK — {len(db_links)} liens identiques au MVP")


if __name__ == "__main__":
    run()
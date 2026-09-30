"""Parité de la règle stricte entre Spark (spark_dedup) et la référence Python (matcher).

Nécessite PySpark (VM) : ignoré ailleurs.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

pytest.importorskip("pyspark")

from engine.identity.canonical import from_dict  # noqa: E402
from engine.identity.matcher import deduplicate  # noqa: E402
from engine.identity.spark_dedup import deduplicate_df  # noqa: E402

ROWS = [
    # Jean Rakoto : même CIN, genre, date, ville -> une identité (noms différents).
    ("pharmacy", "pharmacy_PH001", "Jean Rakoto", "1990-05-12", "101 02404 5", "Antananarivo", "male"),
    ("consultation", "consultation_MED001", "Rakotto Jean", "1990-05-12", "101024045", "ANTANANARIVO", "male"),
    # Homonymes parfaits de CIN différents -> séparés.
    ("pharmacy", "pharmacy_PH002", "Georges Grenier", "2022-04-27", "106867407", "Leclercq", "male"),
    ("imaging", "imaging_IMG002", "Georges Grenier", "2022-04-27", "106388848", "Bonnin", "male"),
    # Sans CIN : nom identique en plus -> réunis.
    ("pharmacy", "pharmacy_PH003", "Hery Rasoa", "1975-05-02", None, "Mahajanga", "female"),
    ("imaging", "imaging_IMG003", "HERY RASOA", "1975-05-02", None, "mahajanga", "female"),
    # Identité incomplète (ville manquante) -> seule.
    ("consultation", "consultation_MED004", "Solo Vola", "1980-03-03", "102077713", None, "female"),
]
COLUMNS = ["_source_system", "source_patient_id", "name", "birth_date", "cin", "birth_city", "gender"]


@pytest.fixture(scope="module")
def spark():
    from pyspark.sql import SparkSession

    session = SparkSession.builder.master("local[1]").appName("test_spark_dedup").getOrCreate()
    yield session
    session.stop()


def test_spark_decisions_equal_python_reference(spark):
    df = spark.createDataFrame(ROWS, COLUMNS)
    spark_rows = {(r["_source_system"], r["source_patient_id"]): (r["master_patient_id"], r["match_method"],
                                                                  r["explanation"])
                  for r in deduplicate_df(df).collect()}
    patients = [from_dict({"source_system": s, "source_patient_id": i, "full_name": n, "birth_date": b,
                           "cin": c, "birth_city": v, "gender": g}) for s, i, n, b, c, v, g in ROWS]
    reference = {(d.source_system, d.source_patient_id): (d.master_patient_id, d.method, d.explanation)
                 for d in deduplicate(patients)}
    assert spark_rows == reference
    masters = {v[0] for v in spark_rows.values()}
    assert len(masters) == 5  # Jean, Georges x2, Hery, Solo

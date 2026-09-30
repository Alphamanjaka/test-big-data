"""Tests des tranches d'âge GOLD : aucun âge valide sans tranche, bornes au jour près."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from provision.scripts.utils.age_tranches import UNKNOWN, intervals, label_for
from provision.scripts.utils.paths import AGE_TRANCHES

DAY = 1 / 365.25  # même conversion que create_gold (jours / 365,25)


@pytest.mark.parametrize("age, expected", [
    (4.25, "1-4 ans"),         # âge entre deux bornes entières : « unknown » avant correction
    (4.99, "1-4 ans"),
    (5.0, "5-14 ans"),
    (14.5, "5-14 ans"),
    (24.5, "15-24 ans"),
    (59.5, "25-59 ans"),
    (60.0, "60 ans et plus"),
    (120.0, "60 ans et plus"),
])
def test_ages_between_integer_bounds(age, expected):
    assert label_for(age, AGE_TRANCHES) == expected


@pytest.mark.parametrize("days, expected", [
    (0, "0-28 j"),
    (28, "0-28 j"),
    (29, "29-59 j"),
    (59, "29-59 j"),
    (60, "2-11 m"),
    (364, "2-11 m"),
    (365.25, "1-4 ans"),
])
def test_day_level_bounds(days, expected):
    assert label_for(days * DAY, AGE_TRANCHES) == expected


def test_no_valid_age_without_tranche():
    """Au jour près, de la naissance à 120 ans, chaque âge a une tranche."""
    unknown = [d for d in range(int(120 * 365.25) + 1) if label_for(d * DAY, AGE_TRANCHES) == UNKNOWN]
    assert unknown == []


@pytest.mark.parametrize("age", [None, -0.5, 120.5])
def test_missing_or_out_of_range_age_is_unknown(age):
    assert label_for(age, AGE_TRANCHES) == UNKNOWN


def test_intervals_are_contiguous():
    bounds = intervals(AGE_TRANCHES)
    assert len(bounds) == 8
    for (_, high, closed, _), (low, _, _, _) in zip(bounds, bounds[1:]):
        assert not closed and high == low
    assert bounds[-1][2] is True


def test_spark_expression_matches_reference():
    """Parité de l'expression Spark avec la référence Python (VM : PySpark requis)."""
    pytest.importorskip("pyspark")
    from pyspark.sql import SparkSession
    from pyspark.sql import functions as F

    from provision.scripts.utils.age_tranches import tranche_column

    ages = [None, -0.5, 0.0, 28 * DAY, 29 * DAY, 60 * DAY, 4.25, 14.5, 24.5, 59.5, 60.0, 120.0, 120.5]
    spark = SparkSession.builder.master("local[1]").appName("test_age_tranches").getOrCreate()
    try:
        df = spark.createDataFrame([(a,) for a in ages], "age double")
        rows = df.select("age", tranche_column(F.col("age"), AGE_TRANCHES).alias("t")).collect()
    finally:
        spark.stop()
    assert {r["age"]: r["t"] for r in rows} == {a: label_for(a, AGE_TRANCHES) for a in ages}

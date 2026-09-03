from types import SimpleNamespace
from typing import Any

from pyspark.sql import DataFrame, Row, Window, functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

from patient_platform.deduplication.matcher import _similarity
from patient_platform.logging_utils import RuntimeLogger
from patient_platform.spark.session import get_or_create_session
from patient_platform.transform.canonical import _normalized

DECISION_SCHEMA = StructType([
    StructField("master_patient_id", StringType(), False),
    StructField("source_system", StringType(), False),
    StructField("source_patient_id", StringType(), False),
    StructField("method", StringType(), False),
    StructField("score", DoubleType(), False),
    StructField("explanation", StringType(), False),
])

_normalized_udf = F.udf(_normalized, StringType())
_birth_key_udf = F.udf(lambda value: value.isoformat() if value else "", StringType())


def _patient_like(full_name: str, birth_date, phone: str) -> SimpleNamespace:
    return SimpleNamespace(full_name=full_name or "", birth_date=birth_date, phone=phone or "")


def _score_udf():
    def score(left_name, left_birth, left_phone, right_name, right_birth, right_phone):
        return _similarity(
            _patient_like(left_name, left_birth, left_phone),
            _patient_like(right_name, right_birth, right_phone),
        )
    return F.udf(score, DoubleType())


def _with_row_order(frame: DataFrame, *ordered_frames: DataFrame) -> DataFrame:
    """Union the source canonical frames in MVP ingestion order, then a global order column."""
    spark = get_or_create_session()
    combined = frame
    for other in ordered_frames:
        combined = combined.union(other)
    return combined.coalesce(1).withColumn("__order", F.monotonically_increasing_id())


def _with_matching_key(frame: DataFrame) -> DataFrame:
    return (
        frame
        .withColumn("__normalized_name", _normalized_udf(F.col("full_name")))
        .withColumn("__birth_key", _birth_key_udf(F.col("birth_date")))
        .withColumn("__phone", F.coalesce(F.col("phone"), F.lit("")))
    )


def _exact_anchors(frame: DataFrame) -> DataFrame:
    """Annotate each row with ``is_anchor`` (earliest in its exact-equivalence cluster)
    and ``anchor_order`` (the row order of that earliest row)."""
    cur = _with_matching_key(frame).alias("cur")
    other = cur.select("__order", "__birth_key", "__phone", "__normalized_name").alias("other")

    key_equal = (
        (F.col("cur.__birth_key") == F.col("other.__birth_key"))
        & (F.col("cur.__phone") == F.col("other.__phone"))
        & (F.col("cur.__normalized_name") == F.col("other.__normalized_name"))
        & (F.col("other.__order") < F.col("cur.__order"))
    )
    birth_phone_equal = (
        (F.col("cur.__birth_key") != "")
        & (F.col("cur.__birth_key") == F.col("other.__birth_key"))
        & (F.col("cur.__phone") != "")
        & (F.col("cur.__phone") == F.col("other.__phone"))
        & (F.col("other.__order") < F.col("cur.__order"))
    )

    joined = cur.join(other, key_equal | birth_phone_equal, "left")
    group_exprs = [F.col(f"cur.{column}") for column in cur.columns]
    anchored = (
        joined.groupBy(*group_exprs)
        .agg(F.min("other.__order").alias("_anchor_order"))
    )
    return anchored.withColumn(
        "is_anchor", F.col("_anchor_order").isNull()
    ).withColumnRenamed("_anchor_order", "anchor_order")


def deduplicate(frame: DataFrame, *ordered_frames: DataFrame,
                probabilistic_threshold: float = 0.80) -> DataFrame:
    """Deduplicate MPV-style: exact cluster first, then probabilistic scoring.

    The similarity matrix between potential masters is computed by Spark
    (cross join + shared RapidFuzz scoring); the sequential resolution that
    sizes the master numbering runs on the driver over the small matrix,
    guaranteeing byte-for-byte parity with the MVP for the demo.
    """
    spark = get_or_create_session()
    ordered = _with_row_order(frame, *ordered_frames)
    anchored = _exact_anchors(ordered)

    candidates = anchored.filter(F.col("is_anchor"))
    cur = candidates.alias("cur")
    cand = candidates.alias("cand")
    pairs = (
        cur.crossJoin(cand)
        .select(
            F.col("cur.__order").cast(LongType()).alias("cur_order"),
            F.col("cand.__order").cast(LongType()).alias("cand_order"),
            _score_udf()(
                F.col("cur.full_name"), F.col("cur.birth_date"), F.col("cur.__phone"),
                F.col("cand.full_name"), F.col("cand.birth_date"), F.col("cand.__phone"),
            ).alias("score"),
        )
        .filter(F.col("cur_order") != F.col("cand_order"))
    )
    score_by_pair = {
        (int(row.cur_order), int(row.cand_order)): float(row.score)
        for row in pairs.collect()
    }

    rows = sorted(anchored.collect(), key=lambda row: row["__order"])
    masters: list[dict[str, Any]] = []
    resolved: dict[int, str] = {}
    decisions: list[dict[str, Any]] = []
    logger = RuntimeLogger("logs/runtime.log", "LOGS.md")

    for row in rows:
        if not row["is_anchor"]:
            master_id = resolved[int(row["anchor_order"])]
            decisions.append(dict(
                master_patient_id=master_id,
                source_system=row["source_system"],
                source_patient_id=row["source_patient_id"],
                method="exact",
                score=1.0,
                explanation="nom, date de naissance et telephone normalises identiques",
            ))
            logger.info("spark_identity_line", engine="spark",
                        source=row["source_system"],
                        source_patient_id=row["source_patient_id"],
                        master_patient_id=master_id, method="exact",
                        score=1.0, status="linked")
            resolved[int(row["__order"])] = master_id
            continue

        best = None
        for master in masters:
            score = score_by_pair.get((int(row["__order"]), int(master["__order"])))
            if score is not None and (best is None or score > best[1]):
                best = (master["master_patient_id"], score)

        if best is not None and best[1] >= probabilistic_threshold:
            master_id = best[0]
            decisions.append(dict(
                master_patient_id=master_id,
                source_system=row["source_system"],
                source_patient_id=row["source_patient_id"],
                method="probabilistic",
                score=round(best[1], 3),
                explanation="similarite nom/date/telephone au-dessus du seuil",
            ))
            logger.info("spark_identity_line", engine="spark",
                        source=row["source_system"],
                        source_patient_id=row["source_patient_id"],
                        master_patient_id=master_id, method="probabilistic",
                        score=round(best[1], 3), status="linked")
            resolved[int(row["__order"])] = master_id
        else:
            master_id = f"PAT-{len(masters) + 1:04d}"
            masters.append({**{k: row[k] for k in row.__fields__}, "master_patient_id": master_id})
            decisions.append(dict(
                master_patient_id=master_id,
                source_system=row["source_system"],
                source_patient_id=row["source_patient_id"],
                method="new_master",
                score=1.0,
                explanation="aucun match explicable au-dessus du seuil",
            ))
            logger.info("spark_identity_line", engine="spark",
                        source=row["source_system"],
                        source_patient_id=row["source_patient_id"],
                        master_patient_id=master_id, method="new_master",
                        score=1.0, status="linked")
        resolved[int(row["__order"])] = master_id

    return spark.createDataFrame([Row(**decision) for decision in decisions], DECISION_SCHEMA)
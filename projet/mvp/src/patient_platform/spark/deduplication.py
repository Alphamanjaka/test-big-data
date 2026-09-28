from types import SimpleNamespace
from typing import Any

from pyspark.sql import DataFrame, Row, Window, functions as F
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

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


def _with_row_order(frame: DataFrame, *ordered_frames: DataFrame) -> DataFrame:
    """Union the source canonical frames in MVP ingestion order, then a
    deterministic global order column.

    Uses a deterministic row_order (source rank + row_number over the
    source patient id) instead of ``monotonically_increasing_id()``, whose
    values are regenerated non-deterministically on every evaluation and
    break the anchor determination in ``_exact_anchors``.
    """
    source_rank = {"pharmacy": 0, "consultation": 1, "imaging": 2}

    def _ranked(df: DataFrame) -> DataFrame:
        rank = F.lit(source_rank.get(df.select("source_system").first()[0], 99))
        return df.withColumn("__source_rank", rank)

    combined = _ranked(frame)
    for other in ordered_frames:
        combined = combined.union(_ranked(other))

    window = Window.partitionBy("__source_rank").orderBy("source_patient_id")
    combined = combined.withColumn("__rank", F.row_number().over(window))
    return combined.withColumn(
        "__order",
        F.col("__source_rank") * 1_000_000 + F.col("__rank"),
    )


def _with_matching_key(frame: DataFrame) -> DataFrame:
    return (
        frame
        .withColumn("__normalized_name", _normalized_udf(F.col("full_name")))
        .withColumn("__birth_key", _birth_key_udf(F.col("birth_date")))
        .withColumn("__phone", F.coalesce(F.col("phone"), F.lit("")))
    )


def _exact_anchors(frame: DataFrame) -> DataFrame:
    """Annotate each row with ``is_anchor`` (earliest in its exact-equivalence cluster)
    and ``anchor_order`` (the row order of that earliest row).

    Uses groupBy on matching keys instead of a self-join to avoid
    PySpark conditional left join bugs with derived DataFrames.

    Only rows with at least one non-empty identity component (normalized
    name, birth or phone) participate in exact clustering. Rows with an
    entirely empty matching key stay isolated to avoid collapsing distinct
    patients that share only missing fields.
    """
    mk = _with_matching_key(frame)

    has_identity = (
        (F.length(F.col("__normalized_name")) > 0)
        | (F.length(F.col("__birth_key")) > 0)
        | (F.length(F.col("__phone")) > 0)
    )
    mk = mk.withColumn("__has_identity", has_identity)

    # Find the minimum order per non-empty matching-key group (the anchor)
    anchor_map = (
        mk.filter(F.col("__has_identity"))
        .groupBy("__normalized_name", "__birth_key", "__phone")
        .agg(F.min("__order").alias("_anchor_order"))
    )

    # Join back to add anchor_order
    anchored = mk.join(
        anchor_map,
        ["__normalized_name", "__birth_key", "__phone"],
        "left",
    )
    return anchored.withColumn(
        "is_anchor", F.col("_anchor_order") == F.col("__order")
    ).withColumnRenamed("_anchor_order", "anchor_order")


class _BoundedMasterIndex:
    """Blocage des masters pour la comparaison probabiliste greedy du driver.

    Un ancre n'est comparé qu'aux masters partageant son préfixe de nom
    normalisé, sa date de naissance ou son téléphone — aucun master à fort
    score n'est écarté, ce qui préserve la sémantique du MVP.
    """

    def __init__(self) -> None:
        self._masters: list[tuple[int, dict]] = []
        self._by_prefix: dict[str, list[int]] = {}
        self._by_birth: dict[str, list[int]] = {}
        self._by_phone: dict[str, list[int]] = {}

    def add(self, master_idx: int, row: dict) -> None:
        self._masters.append((master_idx, row))
        name = row.get("__normalized_name") or ""
        self._by_prefix.setdefault(name[:4], []).append(master_idx)
        bd = row.get("birth_date")
        birth_key = bd.isoformat() if hasattr(bd, "isoformat") else (bd or "")
        if birth_key:
            self._by_birth.setdefault(birth_key, []).append(master_idx)
        phone = row.get("__phone") or ""
        if phone:
            self._by_phone.setdefault(phone, []).append(master_idx)

    def candidates(self, row: dict) -> list[int]:
        name = row.get("__normalized_name") or ""
        prefix = name[:4]
        bd = row.get("birth_date")
        birth_key = bd.isoformat() if hasattr(bd, "isoformat") else (bd or "")
        phone = row.get("__phone") or ""
        said: set[int] = set()
        out: list[int] = []
        for bucket in (self._by_prefix.get(prefix, []),
                       self._by_birth.get(birth_key, []) if birth_key else [],
                       self._by_phone.get(phone, []) if phone else []):
            for idx in bucket:
                if idx not in said:
                    said.add(idx)
                    out.append(idx)
        return out

    def representative(self, master_idx: int) -> dict:
        return self._masters[master_idx][1]

    def exact_birth_phone(self, row: dict) -> int | None:
        """Retourne l'index du plus ancien master partageant **à la fois**
        la date de naissance et un téléphone non vide, ou ``None``.

        Reproduit la règle exacte du MVP (matcher.py), qui fusionne en
        ``exact`` deux enregistrements ayant même birth_date et même phone
        même si le nom diffère (ex: ordre prénom/nom inversé).
        """
        bd = row.get("birth_date")
        birth_key = bd.isoformat() if hasattr(bd, "isoformat") else (bd or "")
        phone = row.get("__phone") or ""
        if not birth_key or not phone:
            return None
        for master_idx, rep in self._masters:  # ordre d'insertion = oldest first
            rb = rep.get("birth_date")
            rbk = rb.isoformat() if hasattr(rb, "isoformat") else (rb or "")
            rp = rep.get("__phone") or ""
            if rbk == birth_key and rp and rp == phone:
                return master_idx
        return None


def deduplicate(frame: DataFrame, *ordered_frames: DataFrame,
                probabilistic_threshold: float = 0.80) -> DataFrame:
    """Deduplicate: exact cluster first, then probabilistic greedy matching.

    Scalable implementation: Spark performs exact clustering and canonical
    preparation. Probabilistic matching runs on the driver in pure Python
    using RapidFuzz with blocking — no crossJoin or Spark UDF needed.

    Semantics mirror the MVP (Pandas) pipeline:
      * exact cluster -> one master (the earliest row, the anchor);
      * each subsequent anchor links to the single best-scoring *existing
        master* (greedy by representative) when score >= threshold;
      * otherwise a new master.
    Exactly one decision is emitted per patient row.
    """
    spark = get_or_create_session()
    ordered = _with_row_order(frame, *ordered_frames)
    anchored = _exact_anchors(ordered)

    # ------------------------------------------------------------------
    # Driver: greedy sequential resolution (mirrors MVP matcher)
    # ------------------------------------------------------------------
    rows = sorted((r.asDict() for r in anchored.collect()),
                  key=lambda r: int(r["__order"]))
    masters: list[dict[str, Any]] = []          # representative rows
    resolved: dict[int, str] = {}               # __order -> master_patient_id
    decisions: list[dict[str, Any]] = []
    index = _BoundedMasterIndex()
    logger = RuntimeLogger("logs/runtime.log", "LOGS.md")

    def _new_master_id() -> str:
        return f"PAT-{len(masters) + 1:04d}"

    for row in rows:
        cur_order = int(row["__order"])

        if not row["is_anchor"]:
            anchor_ord = int(row["anchor_order"])
            master_id = resolved.get(anchor_ord)
            if master_id is None:
                master_id = _new_master_id()
                resolved[anchor_ord] = master_id
                logger.info("spark_identity_line", engine="spark",
                            source=row["source_system"],
                            source_patient_id=row["source_patient_id"],
                            master_patient_id=master_id, method="exact",
                            score=1.0, status="linked")
            resolved[cur_order] = master_id
            decisions.append(dict(
                master_patient_id=master_id,
                source_system=row["source_system"],
                source_patient_id=row["source_patient_id"],
                method="exact",
                score=1.0,
                explanation="duplicate exact de l'ancre",
            ))
            continue

        # ---- Anchor: exact birth+phone match (règle MVP), sinon meilleur master ----
        bp_idx = index.exact_birth_phone(row)
        if bp_idx is not None:
            master_id = masters[bp_idx]["master_patient_id"]
            method = "exact"
            score = 1.0
            explanation = "date de naissance et telephone identiques"
            logger.info("spark_identity_line", engine="spark",
                        source=row["source_system"],
                        source_patient_id=row["source_patient_id"],
                        master_patient_id=master_id, method=method,
                        score=score, status="linked")
        else:
            best_idx, best_score = None, 0.0
            for midx in index.candidates(row):
                master_rep = index.representative(midx)
                score = _similarity(
                    _patient_like(row["full_name"], row["birth_date"], row["__phone"]),
                    _patient_like(master_rep["full_name"], master_rep["birth_date"],
                                  master_rep["__phone"]),
                )
                if score > best_score:
                    best_idx, best_score = midx, score

            if best_idx is not None and best_score >= probabilistic_threshold:
                master_id = masters[best_idx]["master_patient_id"]
                method = "probabilistic"
                score = round(best_score, 3)
                explanation = "similarite nom/date/telephone au-dessus du seuil"
                logger.info("spark_identity_line", engine="spark",
                            source=row["source_system"],
                            source_patient_id=row["source_patient_id"],
                            master_patient_id=master_id, method=method,
                            score=score, status="linked")
            else:
                master_id = _new_master_id()
                master_row = dict(row)
                master_row["master_patient_id"] = master_id
                masters.append(master_row)
                index.add(len(masters) - 1, row)
                method = "new_master"
                score = 1.0
                explanation = "aucun match explicable au-dessus du seuil"
                logger.info("spark_identity_line", engine="spark",
                            source=row["source_system"],
                            source_patient_id=row["source_patient_id"],
                            master_patient_id=master_id, method=method,
                            score=score, status="linked")

        resolved[cur_order] = master_id
        decisions.append(dict(
            master_patient_id=master_id,
            source_system=row["source_system"],
            source_patient_id=row["source_patient_id"],
            method=method,
            score=score,
            explanation=explanation,
        ))

    return spark.createDataFrame(
        [Row(**decision) for decision in decisions], DECISION_SCHEMA,
    )
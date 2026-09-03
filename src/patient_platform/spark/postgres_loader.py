import os
from typing import Callable, Iterable

from pyspark.sql import Column, DataFrame, functions as F

from patient_platform.logging_utils import RuntimeLogger
from patient_platform.spark.session import get_or_create_session

PATIENT_ID_COLUMN = {
    "pharmacy": "client_id",
    "consultation": "patient_code",
    "imaging": "id_personne",
}

BUSINESS_SPEC = {
    "pharmacy": {"table": "medicine_purchase", "record": "purchase_id", "patient": "customer_id"},
    "consultation": {"table": "patient_consultation", "record": "consultation_id", "patient": "patient_id"},
    "imaging": {"table": "imaging_exam", "record": "exam_id", "patient": "patient_code"},
}

_BATCH_SIZE = 500

_RAW_SQL = """
    INSERT INTO raw_patient_record (source_system, source_patient_id, source_file, payload)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (source_system, source_patient_id) DO NOTHING
"""

_MASTER_SQL = """
    INSERT INTO master_patient
        (master_patient_id, first_name, last_name, full_name, birth_date, phone, address)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (master_patient_id) DO UPDATE SET
        first_name = EXCLUDED.first_name,
        last_name = EXCLUDED.last_name,
        full_name = EXCLUDED.full_name,
        birth_date = EXCLUDED.birth_date,
        phone = EXCLUDED.phone,
        address = EXCLUDED.address
"""

_IDENTITY_SQL = """
    INSERT INTO patient_identity_map
        (master_patient_id, source_system, source_patient_id,
         match_method, match_score, explanation)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON CONFLICT (source_system, source_patient_id) DO UPDATE SET
        master_patient_id = EXCLUDED.master_patient_id,
        match_method = EXCLUDED.match_method,
        match_score = EXCLUDED.match_score,
        explanation = EXCLUDED.explanation
"""

_BUSINESS_SQL_TEMPLATE = """
    INSERT INTO {table}
        (source_record_id, master_patient_id, source_system, source_patient_id, payload)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (source_system, source_record_id) DO NOTHING
"""

_TABLE_SQL = {
    "raw_patient_record": _RAW_SQL,
    "master_patient": _MASTER_SQL,
    "patient_identity_map": _IDENTITY_SQL,
    "medicine_purchase": _BUSINESS_SQL_TEMPLATE.format(table="medicine_purchase"),
    "patient_consultation": _BUSINESS_SQL_TEMPLATE.format(table="patient_consultation"),
    "imaging_exam": _BUSINESS_SQL_TEMPLATE.format(table="imaging_exam"),
}


def _raw_params(row) -> tuple:
    return (row.source_system, row.source_patient_id, row.source_file, row.payload)


def _master_params(row) -> tuple:
    return (row.master_patient_id, row.first_name, row.last_name, row.full_name,
            row.birth_date, row.phone, row.address)


def _identity_params(row) -> tuple:
    return (row.master_patient_id, row.source_system, row.source_patient_id,
            row.match_method, float(row.match_score), row.explanation)


def _business_params(row) -> tuple:
    return (row.source_record_id, row.master_patient_id, row.source_system,
            row.source_patient_id, row.payload)


_ROW_PARAMS: dict[str, Callable[[object], tuple]] = {
    "raw_patient_record": _raw_params,
    "master_patient": _master_params,
    "patient_identity_map": _identity_params,
    "medicine_purchase": _business_params,
    "patient_consultation": _business_params,
    "imaging_exam": _business_params,
}


def _patient_id_for(table: str, parameters: tuple) -> str:
    if table == "raw_patient_record":
        return parameters[1]
    if table == "patient_identity_map":
        return parameters[2]
    if table == "master_patient":
        return ""
    return parameters[3]


def _master_id_for(table: str, parameters: tuple) -> str:
    if table == "raw_patient_record":
        return ""
    if table == "patient_identity_map":
        return parameters[0]
    if table == "master_patient":
        return parameters[0]
    return parameters[1]


def _write_partition(url: str, table: str, sql: str, params_for_row: Callable, rows: Iterable) -> None:
    import psycopg

    logger = RuntimeLogger("logs/runtime.log", "LOGS.md")
    connection = psycopg.connect(url)
    try:
        batch = []
        with connection.cursor() as cursor:
            for row in rows:
                batch.append(params_for_row(row))
                parameters = batch[-1]
                logger.info(
                    "db_line", engine="spark", table=table,
                    source_patient_id=_patient_id_for(table, parameters),
                    master_patient_id=_master_id_for(table, parameters),
                    row_number=len(batch), status="written",
                )
                if len(batch) >= _BATCH_SIZE:
                    cursor.executemany(sql, batch)
                    batch = []
            if batch:
                cursor.executemany(sql, batch)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


class SparkPostgresLoader:
    """Loads Spark table frames into PostgreSQL using per-partition DB writes.

    The write statements mirror the MVP loader exactly (``ON CONFLICT`` rules),
    so re-runs stay idempotent while the writes are distributed by Spark.
    """

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DATABASE_URL")
        if not self.url:
            raise ValueError("DATABASE_URL is not configured")

    def load(self, frames: dict[str, DataFrame]) -> dict[str, int]:
        spark = get_or_create_session()
        rows_written: dict[str, int] = {}
        for table, frame in frames.items():
            sql = _TABLE_SQL[table]
            params_for_row = _ROW_PARAMS[table]
            url = self.url
            rows_written[table] = frame.count()
            frame.foreachPartition(
                lambda rows, t=table, s=sql, p=params_for_row, u=url:
                _write_partition(u, t, s, p, rows))
        return rows_written


def _payload_column(frame: DataFrame) -> Column:
    return F.to_json(F.struct(*[F.col(column) for column in frame.columns]))


def build_raw_frame(raw_frame: DataFrame, source_system: str) -> DataFrame:
    return (
        raw_frame
        .withColumn("payload", _payload_column(raw_frame))
        .select(
            F.col("source_system"),
            F.col(PATIENT_ID_COLUMN[source_system]).alias("source_patient_id"),
            F.col("source_file"),
            F.col("payload"),
        )
    )


def build_identity_frame(decisions: DataFrame) -> DataFrame:
    return decisions.select(
        F.col("master_patient_id"),
        F.col("source_system"),
        F.col("source_patient_id"),
        F.col("method").alias("match_method"),
        F.col("score").alias("match_score"),
        F.col("explanation"),
    )


def build_master_frame(decisions: DataFrame,
                       canonical_frames: dict[str, DataFrame]) -> DataFrame:
    masters = decisions.filter(F.col("method") == "new_master")
    frames = []
    for source_system, canonical in canonical_frames.items():
        keyed = masters.filter(F.col("source_system") == source_system).select(
            "master_patient_id", "source_system", "source_patient_id")
        frames.append(keyed.join(canonical, ["source_system", "source_patient_id"]))
    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.union(frame)
    return merged.select(
        "master_patient_id", "first_name", "last_name", "full_name",
        "birth_date", "phone", "address",
    )


def build_business_frame(business_frame: DataFrame, source_system: str,
                         decisions: DataFrame) -> DataFrame:
    spec = BUSINESS_SPEC[source_system]
    ready = (
        business_frame
        .withColumn("payload", _payload_column(business_frame))
        .select(
            F.col(spec["record"]).alias("source_record_id"),
            F.col(spec["patient"]).alias("source_patient_id"),
            F.col("source_system"),
            F.col("payload"),
        )
    )
    keyed = decisions.select(
        F.col("master_patient_id"), F.col("source_system"), F.col("source_patient_id"))
    return ready.join(keyed, ["source_system", "source_patient_id"]).select(
        "source_record_id", "master_patient_id", "source_system", "source_patient_id", "payload")
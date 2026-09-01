from fastapi import FastAPI, HTTPException
from psycopg.rows import dict_row

from patient_platform.load.database import connection_factory


app = FastAPI(title="Patient Data Platform API", version="0.1.0")


def query_one(query: str, parameters: tuple = ()) -> dict | None:
    connection = connection_factory()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone()
    finally:
        connection.close()


def query_all(query: str, parameters: tuple = ()) -> list[dict]:
    connection = connection_factory()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return list(cursor.fetchall())
    finally:
        connection.close()


@app.get("/health")
def health() -> dict[str, str]:
    query_one("SELECT 1 AS healthy")
    return {"status": "ok", "database": "connected"}


@app.get("/metrics")
def metrics() -> dict[str, int]:
    row = query_one(
        """
        SELECT
            (SELECT COUNT(*) FROM raw_patient_record) AS raw_records,
            (SELECT COUNT(*) FROM master_patient) AS master_patients,
            (SELECT COUNT(*) FROM patient_identity_map) AS identity_links,
            (SELECT COUNT(*) FROM medicine_purchase) AS purchases,
            (SELECT COUNT(*) FROM patient_consultation) AS consultations,
            (SELECT COUNT(*) FROM imaging_exam) AS exams
        """
    )
    return {key: int(value) for key, value in row.items()}


@app.get("/patients")
def list_patients() -> list[dict]:
    return query_all(
        """
        SELECT master_patient_id, first_name, last_name, full_name, birth_date
        FROM master_patient
        ORDER BY master_patient_id
        """
    )


@app.get("/patients/{master_patient_id}")
def get_patient(master_patient_id: str) -> dict:
    patient = query_one(
        """
        SELECT master_patient_id, first_name, last_name, full_name, birth_date
        FROM master_patient
        WHERE master_patient_id = %s
        """,
        (master_patient_id,),
    )
    if patient is None:
        raise HTTPException(
            status_code=404, detail="Patient master introuvable")

    patient["identity_links"] = query_all(
        """
        SELECT source_system, source_patient_id, match_method, match_score, explanation
        FROM patient_identity_map
        WHERE master_patient_id = %s
        ORDER BY source_system, source_patient_id
        """,
        (master_patient_id,),
    )
    counts = query_one(
        """
        SELECT
            (SELECT COUNT(*) FROM medicine_purchase WHERE master_patient_id = %s) AS purchases,
            (SELECT COUNT(*) FROM patient_consultation WHERE master_patient_id = %s) AS consultations,
            (SELECT COUNT(*) FROM imaging_exam WHERE master_patient_id = %s) AS exams
        """,
        (master_patient_id, master_patient_id, master_patient_id),
    )
    patient["business_counts"] = {
        key: int(value) for key, value in counts.items()}
    return patient

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from psycopg.rows import dict_row

from patient_platform.api.auth import UserContext, get_current_user, require_role
from patient_platform.api.audit import AuditMiddleware
from patient_platform.api.consent import router as consent_router
from patient_platform.load.database import connection_factory


app = FastAPI(title="Patient Data Platform API", version="0.2.0")
app.add_middleware(AuditMiddleware)
app.include_router(consent_router)


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
def metrics(user: Annotated[UserContext, Depends(get_current_user)]) -> dict[str, int]:
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
def list_patients(user: Annotated[UserContext, Depends(get_current_user)]) -> list[dict]:
    return query_all(
        """
        SELECT master_patient_id, first_name, last_name, full_name, birth_date
        FROM master_patient
        ORDER BY master_patient_id
        """
    )


@app.get("/patients/{master_patient_id}")
def get_patient(
    master_patient_id: str,
    user: Annotated[UserContext, Depends(get_current_user)],
) -> dict:
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


@app.get("/users")
def list_users(user: Annotated[UserContext, Depends(require_role("admin"))]) -> list[dict]:
    return query_all(
        """
        SELECT user_id, username, role, active, created_at
        FROM api_user
        ORDER BY user_id
        """
    )


class UserCreate(BaseModel):
    username: str
    role: str


@app.post("/users", status_code=201)
def create_user(
    user_data: UserCreate,
    user: Annotated[UserContext, Depends(require_role("admin"))],
) -> dict:
    import secrets
    import hashlib

    api_key = secrets.token_hex(32)
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO api_user (username, api_key_hash, role)
                VALUES (%s, %s, %s)
                RETURNING user_id
                """,
                (user_data.username, api_key_hash, user_data.role),
            )
            user_id = cursor.fetchone()[0]
        connection.commit()
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=400, detail=f"Erreur création utilisateur: {str(e)}")
    finally:
        connection.close()

    return {
        "user_id": user_id,
        "username": user_data.username,
        "role": user_data.role,
        "api_key": api_key,
        "message": "Conservez cette clé API, elle ne sera plus affichée.",
    }


@app.get("/audit")
def list_audit_logs(user: Annotated[UserContext, Depends(require_role("admin"))]) -> list[dict]:
    return query_all(
        """
        SELECT audit_id, user_id, username, endpoint, method, response_status, ip_address, accessed_at
        FROM access_audit
        ORDER BY accessed_at DESC
        LIMIT 100
        """
    )

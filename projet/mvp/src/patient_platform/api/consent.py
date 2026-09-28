from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg.rows import dict_row

from patient_platform.api.auth import UserContext, get_current_user, require_role
from patient_platform.load.database import connection_factory

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentCreate(BaseModel):
    master_patient_id: str
    purpose: str
    granted: bool


def _query_one(query: str, parameters: tuple = ()) -> dict | None:
    connection = connection_factory()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone()
    finally:
        connection.close()


def _query_all(query: str, parameters: tuple = ()) -> list[dict]:
    connection = connection_factory()
    try:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, parameters)
            return list(cursor.fetchall())
    finally:
        connection.close()


def _execute(query: str, parameters: tuple = ()) -> None:
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute(query, parameters)
        connection.commit()
    finally:
        connection.close()


@router.get("")
def list_consents(user: UserContext = Depends(require_role("admin", "analyst"))) -> list[dict]:
    return _query_all(
        """
        SELECT c.consent_id, c.master_patient_id, c.purpose, c.granted, c.recorded_at
        FROM consent c
        ORDER BY c.recorded_at DESC
        """
    )


@router.get("/{master_patient_id}")
def get_patient_consents(
    master_patient_id: str,
    user: UserContext = Depends(require_role("admin", "analyst")),
) -> list[dict]:
    patient = _query_one(
        "SELECT master_patient_id FROM master_patient WHERE master_patient_id = %s",
        (master_patient_id,),
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient master introuvable")

    return _query_all(
        """
        SELECT consent_id, purpose, granted, recorded_at
        FROM consent
        WHERE master_patient_id = %s
        ORDER BY recorded_at DESC
        """,
        (master_patient_id,),
    )


@router.post("", status_code=201)
def create_consent(
    consent: ConsentCreate,
    user: UserContext = Depends(require_role("admin")),
) -> dict:
    patient = _query_one(
        "SELECT master_patient_id FROM master_patient WHERE master_patient_id = %s",
        (consent.master_patient_id,),
    )
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient master introuvable")

    _execute(
        """
        INSERT INTO consent (master_patient_id, purpose, granted)
        VALUES (%s, %s, %s)
        """,
        (consent.master_patient_id, consent.purpose, consent.granted),
    )

    return {
        "status": "created",
        "master_patient_id": consent.master_patient_id,
        "purpose": consent.purpose,
        "granted": consent.granted,
    }


def check_consent(master_patient_id: str, purpose: str) -> bool:
    row = _query_one(
        """
        SELECT granted FROM consent
        WHERE master_patient_id = %s AND purpose = %s
        ORDER BY recorded_at DESC LIMIT 1
        """,
        (master_patient_id, purpose),
    )
    if row is None:
        return False
    return row["granted"]

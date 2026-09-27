"""Consentement purpose-by-purpose (portage autonome de test_bigdata)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from psycopg.rows import dict_row

from engine.governance.auth import UserContext, require_role
from engine.governance.database import connection_factory

router = APIRouter(prefix="/consent", tags=["consent"])

# Finalités normalisées : liste fermée, alignée sur la contrainte
# `consent_purpose_check` de sql/schema.sql et sur le jeu de démonstration
# produit par provision/db/seed_governance.py. Toute autre valeur est
# rejetée en 422 : une finalité libre rendrait l'audit inexploitable.
PURPOSES = ("api_access", "research", "analytics")


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
    # Refus de valider une finalité hors liste fermée : l'API et la contrainte
    # `consent_purpose_check` doivent accepter exactement le même alphabet.
    validate_purpose(consent.purpose)
    _execute(
        "INSERT INTO consent (master_patient_id, purpose, granted) VALUES (%s, %s, %s)",
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


def validate_purpose(purpose: str) -> str:
    """Valide une finalité déclarée par l'appelant (422 si hors liste fermée)."""
    if purpose not in PURPOSES:
        raise HTTPException(
            status_code=422,
            detail=f"Finalite inconnue. Valeurs autorisees: {', '.join(PURPOSES)}",
        )
    return purpose


def enforce_consent(request: Request, master_patient_id: str, purpose: str) -> str:
    """Applique le consentement à un patient et materialise le refus (403).

    Refus par defaut : l'absence de ligne de consentement vaut refus. La
    finalité est deposée dans `request.state.purpose` et le motif dans
    `request.state.refusal_reason` : AuditMiddleware les relit pour les
    journaliser dans `access_audit` — la conformite se demontre par l'audit,
    pas par une intention.
    """
    validate_purpose(purpose)
    request.state.purpose = purpose
    if check_consent(master_patient_id, purpose):
        request.state.refusal_reason = None
        return purpose
    reason = f"consentement non accorde pour la finalite {purpose}"
    request.state.refusal_reason = reason
    raise HTTPException(status_code=403, detail=reason)


def consented_master_ids(purpose: str) -> set:
    """Masters ayant consenti a `purpose`, le dernier avis de chaque patient.

    Un seul aller-retour SQL. `DISTINCT ON` + `ORDER BY recorded_at DESC`
    applique la meme regle « le dernier avis gagne » que `check_consent`.
    """
    validate_purpose(purpose)
    rows = _query_all(
        """
        SELECT DISTINCT ON (master_patient_id) master_patient_id, granted
        FROM consent
        WHERE purpose = %s
        ORDER BY master_patient_id, recorded_at DESC
        """,
        (purpose,),
    )
    return {row["master_patient_id"] for row in rows if row["granted"]}
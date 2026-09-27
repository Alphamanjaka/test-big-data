"""API gouvernance (FastAPI) — plateforme de données patients synthétiques.

Endpoints :
- GET /health         — liveness probe (pas d'auth)
- GET /metrics        — KPIs dédup (total masters, doublons, taux)
- GET /patients       — liste masters (admin/analyst), filtrée par consentement
- GET /patients/{id}  — détail master (admin/analyst), 403 sans consentement
- GET /audit          — journal d'accès (admin uniquement)
- /consent/*          — monté depuis engine.governance.consent.router

Les endpoints `/patients*` exigent le paramètre `purpose` (finalité déclarée par
l'appelant) : la liste ne renvoie que les patients ayant consenti à cette
finalité, et le détail renvoie 403 sinon. Le refus est journalisé dans
`access_audit` (colonne `refusal_reason`).

Lancement : uvicorn engine.governance.app:app --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from starlette.middleware.cors import CORSMiddleware

from engine.governance.audit import AuditMiddleware
from engine.governance.auth import UserContext, require_role
from engine.governance.consent import (
    PURPOSES,
    consented_master_ids,
    enforce_consent,
)
from engine.governance.consent import router as consent_router
from engine.governance.database import connection_factory

app = FastAPI(title="API Gouvernance", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000",
                   "http://192.168.56.1:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(AuditMiddleware)
app.include_router(consent_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics(user: UserContext = Depends(require_role("admin", "analyst"))):
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM master_patient")
            total = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM master_patient WHERE is_duplicate")
            dups = cur.fetchone()[0]
        return {"total_patients": total, "duplicates": dups,
                "duplicate_rate": round(dups * 100 / total, 2) if total else 0}
    finally:
        conn.close()


PURPOSE_QUERY = Query(
    ...,
    description="Finalite declaree par l'appelant : " + " | ".join(PURPOSES),
)


@app.get("/patients")
def list_patients(
    request: Request,
    purpose: str = PURPOSE_QUERY,
    user: UserContext = Depends(require_role("admin", "analyst")),
):
    """Liste des masters ayant consenti a la finalite demandee.

    Deux requetes : les identifiants consentis (consent.py), puis les masters.
    Le filtrage est applique en mémoire : il porte sur un ensemble d'identifiants
    déjà restreint aux patients consentis. La reponse reste un tableau — les
    patients sans consentement sont absents — et le nombre d'exclusions est
    consigne dans l'audit pour que le silence soit explicable.
    """
    request.state.purpose = purpose
    allowed = consented_master_ids(purpose)
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT master_patient_id, source_system, is_duplicate "
                "FROM master_patient ORDER BY master_patient_id"
            )
            rows = cur.fetchall()
    finally:
        conn.close()
    visible = [r for r in rows if r[0] in allowed]
    hidden = len(rows) - len(visible)
    request.state.refusal_reason = (
        f"{hidden} patient(s) filtres : consentement non accorde pour {purpose}"
        if hidden
        else None
    )
    return [{"master_patient_id": r[0], "source_system": r[1],
             "is_duplicate": r[2]} for r in visible]


@app.get("/patients/{master_patient_id}")
def get_patient(
    request: Request,
    master_patient_id: str,
    purpose: str = PURPOSE_QUERY,
    user: UserContext = Depends(require_role("admin", "analyst")),
):
    enforce_consent(request, master_patient_id, purpose)
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT master_patient_id, source_system, is_duplicate "
                "FROM master_patient WHERE master_patient_id = %s",
                (master_patient_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Patient master introuvable")
            return {"master_patient_id": row[0], "source_system": row[1],
                    "is_duplicate": row[2]}
    finally:
        conn.close()


@app.get("/audit")
def audit_log(user: UserContext = Depends(require_role("admin"))):
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT user_id, username, endpoint, method, "
                "response_status, ip_address, purpose, refusal_reason, accessed_at "
                "FROM access_audit ORDER BY accessed_at DESC LIMIT 200"
            )
            cols = ["user_id", "username", "endpoint", "method",
                    "response_status", "ip_address", "purpose",
                    "refusal_reason", "accessed_at"]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()

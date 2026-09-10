"""API gouvernance (FastAPI) — plateforme de données patients synthétiques.

Endpoints :
- GET /health         — liveness probe (pas d'auth)
- GET /metrics        — KPIs dédup (total masters, doublons, taux)
- GET /patients       — liste masters (admin/analyst)
- GET /patients/{id}  — détail master (admin/analyst)
- GET /audit          — journal d'accès (admin uniquement)
- /consent/*          — monté depuis engine.governance.consent.router

Lancement : uvicorn engine.governance.app:app --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends
from starlette.middleware.cors import CORSMiddleware

from engine.governance.audit import AuditMiddleware
from engine.governance.auth import UserContext, require_role
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


@app.get("/patients")
def list_patients(user: UserContext = Depends(require_role("admin", "analyst"))):
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT master_patient_id, source_system, is_duplicate "
                "FROM master_patient ORDER BY master_patient_id"
            )
            return [{"master_patient_id": r[0], "source_system": r[1],
                     "is_duplicate": r[2]} for r in cur.fetchall()]
    finally:
        conn.close()


@app.get("/patients/{master_patient_id}")
def get_patient(
    master_patient_id: str,
    user: UserContext = Depends(require_role("admin", "analyst")),
):
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
                "response_status, ip_address, recorded_at "
                "FROM access_audit ORDER BY recorded_at DESC LIMIT 200"
            )
            cols = ["user_id", "username", "endpoint", "method",
                    "response_status", "ip_address", "recorded_at"]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
    finally:
        conn.close()

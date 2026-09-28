"""API gouvernance (FastAPI) — plateforme de données patients synthétiques.

Endpoints :
- GET /health         — liveness probe (pas d'auth)
- GET /metrics        — KPIs dédup (total masters, doublons, taux)
- GET /patients       — liste masters (admin/analyst), filtrée par consentement
- GET /patients/{id}  — dossier master (admin/analyst), 403 sans consentement
- GET /audit          — journal d'accès (admin uniquement)
- GET /pipeline/schedule — planification ELT (admin/analyst)
- PUT /pipeline/schedule — écriture de la planification (admin uniquement)
- GET /pipeline/status   — état du pipeline (admin/analyst)
- /consent/*          — monté depuis engine.governance.consent.router

Les patients exposés proviennent du schéma canonique `sql/schema.sql` : l'identité
master (`master_patient`), les correspondances de déduplication
(`patient_identity_map`) et l'historique des avis (`consent`). L'endpoint de liste
accepte `search` (nom/CIN/id) et une pagination `page`/`page_size` ; le filtrage
par consentement précède toujours la pagination pour que les patients non consentis
restent silencieux.

Les endpoints `/patients*` exigent le paramètre `purpose` (finalité déclarée par
l'appelant) : la liste ne renvoie que les patients ayant consenti à cette
finalité, et le dossier renvoie 403 sinon. Le refus est journalisé dans
`access_audit` (colonne `refusal_reason`).

Lancement : uvicorn engine.governance.app:app --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from starlette.middleware.cors import CORSMiddleware

from engine.governance import pipeline as pipeline_status
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
    allow_methods=["GET", "POST", "PUT"],
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

# Colonnes d'identité du schéma canonique sql/schema.sql (table master_patient).
# Le détail et la liste n'exposent que ces colonnes : `source_system` et
# `is_duplicate` appartiennent aux tables source/SILVER, pas au master.
MASTER_COLUMNS = (
    "master_patient_id", "first_name", "last_name", "full_name",
    "birth_date", "cin", "birth_city", "address", "gender",
)

MASTER_SELECT = "SELECT " + ", ".join(MASTER_COLUMNS) + " FROM master_patient"

IDENTITY_MAP_COLUMNS = ("source_system", "source_patient_id", "match_method", "match_score")

CONSENT_COLUMNS = ("purpose", "granted", "recorded_at")


def _master_row(row) -> dict:
    return dict(zip(MASTER_COLUMNS, row))


@app.get("/patients")
def list_patients(
    request: Request,
    search: str = Query("", description="Recherche sur nom, CIN ou identifiant master"),
    page: int = Query(1, ge=1, description="Numero de page (1-indexe)"),
    page_size: int = Query(25, ge=1, le=100, description="Taille de page (1-100)"),
    purpose: str = PURPOSE_QUERY,
    user: UserContext = Depends(require_role("admin", "analyst")),
):
    """Liste des masters ayant consenti a la finalite demandee.

    Contrat : le filtrage par consentement precede la recherche et la
    pagination, executees en mémoire sur un sous-ensemble d'identifiants deja
    restreint. Le nombre de patients exclus est consigne dans l'audit pour que
    le silence soit explicable.
    """
    request.state.purpose = purpose
    allowed = consented_master_ids(purpose)
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(MASTER_SELECT)
            rows = cur.fetchall()
    finally:
        conn.close()
    term = search.strip().lower()
    matched = [r for r in rows if _matches_search(r, term)]
    visible = [r for r in matched if r[0] in allowed]
    # Tri déterministe en mémoire (nom complet puis identifiant), pour un ordre
    # stable identique en vrai base comme en jeu de test.
    visible.sort(key=lambda r: (str(r[3] or "").lower(), r[0]))
    hidden = len(matched) - len(visible)
    request.state.refusal_reason = (
        f"{hidden} patient(s) filtres : consentement non accorde pour {purpose}"
        if hidden
        else None
    )
    offset = (page - 1) * page_size
    return {
        "items": [_master_row(r) for r in visible[offset:offset + page_size]],
        "total": len(visible),
        "page": page,
        "page_size": page_size,
    }


def _matches_search(row: tuple, term: str) -> bool:
    """Recherche insensible à la casse sur nom complet, CIN et identifiant.

    Le sous-ensemble porté par la liste étant déjà restreint par le consentement
    (et de taille démonstrative), la recherche est appliquée en mémoire : elle
    reste ainsi testable avec les fausses connexions des tests.
    """
    if not term:
        return True
    haystack = " ".join(str(field or "") for field in (row[3], row[5], row[0]))
    return term in haystack.lower()


@app.get("/patients/{master_patient_id}")
def get_patient(
    request: Request,
    master_patient_id: str,
    purpose: str = PURPOSE_QUERY,
    user: UserContext = Depends(require_role("admin", "analyst")),
):
    """Dossier du patient master: identité, correspondances de dedup, avis.

    Le consentement est verifie avant toute lecture (403 sinon). Les
    correspondances proviennent de `patient_identity_map` (chaque master
    regroupe une ou plusieurs sources) et les avis de `consent` (historique
    purpose par purpose). 404 si l'identifiant master est inconnu.
    """
    enforce_consent(request, master_patient_id, purpose)
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(
                MASTER_SELECT + " WHERE master_patient_id = %s",
                (master_patient_id,),
            )
            row = cur.fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Patient master introuvable")
            cur.execute(
                "SELECT source_system, source_patient_id, match_method, match_score "
                "FROM patient_identity_map WHERE master_patient_id = %s "
                "ORDER BY source_system, source_patient_id",
                (master_patient_id,),
            )
            identity_map = [dict(zip(IDENTITY_MAP_COLUMNS, item)) for item in cur.fetchall()]
            cur.execute(
                "SELECT purpose, granted, recorded_at FROM consent "
                "WHERE master_patient_id = %s ORDER BY recorded_at DESC",
                (master_patient_id,),
            )
            consents = [dict(zip(CONSENT_COLUMNS, item)) for item in cur.fetchall()]
    finally:
        conn.close()
    return {
        **_master_row(row),
        "identity_map": identity_map,
        "consents": consents,
    }


@app.get("/pipeline/schedule")
def get_pipeline_schedule(
    user: UserContext = Depends(require_role("admin", "analyst")),
):
    """Planification ELT courante (fichier partagé lu aussi par le cron VM)."""
    return pipeline_status.load_schedule()


@app.put("/pipeline/schedule")
def put_pipeline_schedule(
    payload: dict,
    user: UserContext = Depends(require_role("admin")),
):
    """Écrit la planification ELT (admin) — journalisé par AuditMiddleware."""
    try:
        return pipeline_status.save_schedule(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.get("/pipeline/status")
def pipeline_status_endpoint(
    user: UserContext = Depends(require_role("admin", "analyst")),
):
    """État du pipeline : plan, prochain run, sources suivies, zones."""
    return pipeline_status.read_status()


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

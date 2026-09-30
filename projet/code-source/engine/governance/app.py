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
- GET /pipeline/runs     — historique chiffré des runs (admin/analyst)
- /consent/*          — monté depuis engine.governance.consent.router

Les patients exposés proviennent du schéma canonique `sql/schema.sql` : l'identité
master (`master_patient`), les correspondances de déduplication
(`patient_identity_map`) et l'historique des avis (`consent`). L'endpoint de liste
accepte `search` (nom/CIN/id) et une pagination `page`/`page_size` ; recherche,
filtrage par consentement et pagination sont exécutés par PostgreSQL, le filtrage
précédant toujours la pagination pour que les patients non consentis restent
silencieux. Les connexions sont empruntées au pool de `engine.governance.database`,
fermé à l'arrêt de l'API.

Les endpoints `/patients*` exigent le paramètre `purpose` (finalité déclarée par
l'appelant) : la liste ne renvoie que les patients ayant consenti à cette
finalité, et le dossier renvoie 403 sinon. Le refus est journalisé dans
`access_audit` (colonne `refusal_reason`).

Lancement : uvicorn engine.governance.app:app --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, Request
from starlette.middleware.cors import CORSMiddleware

from engine.governance import pipeline as pipeline_status
from engine.governance.audit import AuditMiddleware
from engine.governance.auth import UserContext, require_role
from engine.governance.consent import (
    PURPOSES,
    enforce_consent,
    validate_purpose,
)
from engine.governance.consent import router as consent_router
from engine.governance.database import close_pool, connection_factory


@asynccontextmanager
async def lifespan(_app):
    """Le pool s'ouvre à la première requête ; il est fermé à l'arrêt de l'API."""
    yield
    close_pool()


app = FastAPI(title="API Gouvernance", version="0.1.0", lifespan=lifespan)

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
        # Fiches et doublons viennent de la table de correspondance : `master_patient`
        # ne porte pas d'indicateur de doublon (une ligne par patient maître).
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM master_patient")
            masters = cur.fetchone()[0]
            cur.execute(
                "SELECT COUNT(*), COUNT(*) FILTER (WHERE match_method <> 'new_master') "
                "FROM patient_identity_map"
            )
            records, dups = cur.fetchone()
        return {"total_patients": records, "total_masters": masters, "duplicates": dups,
                "duplicate_rate": round(dups * 100 / records, 2) if records else 0}
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


# Périmètre de la liste, évalué par PostgreSQL : `latest` applique « le dernier avis
# gagne » (même règle que check_consent) ; un patient sans avis pour la finalité est
# refusé par défaut. La recherche (insensible à la casse) porte sur le nom complet, le
# CIN et l'identifiant master.
_PATIENT_SCOPE = """
    WITH latest AS (
        SELECT DISTINCT ON (master_patient_id) master_patient_id, granted
        FROM consent
        WHERE purpose = %(purpose)s
        ORDER BY master_patient_id, recorded_at DESC, consent_id DESC
    ), matched AS (
        SELECT m.*, COALESCE(l.granted, FALSE) AS allowed
        FROM master_patient m
        LEFT JOIN latest l ON l.master_patient_id = m.master_patient_id
        WHERE strpos(lower(coalesce(m.full_name, '') || ' ' || coalesce(m.cin, '') || ' '
                           || m.master_patient_id), lower(%(term)s)) > 0
    )
"""

PATIENT_COUNT_SQL = _PATIENT_SCOPE + (
    "SELECT COUNT(*) FILTER (WHERE allowed), COUNT(*) FILTER (WHERE NOT allowed) FROM matched"
)

# Ordre binaire (COLLATE "C") : stable et indépendant de la locale du serveur.
PATIENT_PAGE_SQL = _PATIENT_SCOPE + (
    "SELECT " + ", ".join(MASTER_COLUMNS) + " FROM matched WHERE allowed "
    "ORDER BY lower(coalesce(full_name, '')) COLLATE \"C\", master_patient_id COLLATE \"C\" "
    "LIMIT %(limit)s OFFSET %(offset)s"
)


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

    Contrat : le filtrage par consentement precede la pagination ; seule la page
    demandée quitte la base. Le nombre de patients exclus (correspondant à la
    recherche mais sans consentement) est consigne dans l'audit pour que le
    silence soit explicable.
    """
    request.state.purpose = purpose
    validate_purpose(purpose)
    params = {
        "purpose": purpose,
        "term": search.strip(),
        "limit": page_size,
        "offset": (page - 1) * page_size,
    }
    conn = connection_factory()
    try:
        with conn.cursor() as cur:
            cur.execute(PATIENT_COUNT_SQL, params)
            total, hidden = cur.fetchone()
            cur.execute(PATIENT_PAGE_SQL, params)
            rows = cur.fetchall()
    finally:
        conn.close()
    request.state.refusal_reason = (
        f"{hidden} patient(s) filtres : consentement non accorde pour {purpose}"
        if hidden
        else None
    )
    return {
        "items": [_master_row(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


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


@app.get("/pipeline/runs")
def pipeline_runs(
    limit: int = Query(20, ge=1, le=200),
    user: UserContext = Depends(require_role("admin", "analyst")),
):
    """Historique des runs : lignes par source, patients maîtres, volumes GOLD."""
    conn = connection_factory()
    try:
        return pipeline_status.list_runs(conn, limit)
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

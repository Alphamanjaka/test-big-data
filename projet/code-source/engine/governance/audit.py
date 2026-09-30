"""Audit d'acces (portage autonome de test_bigdata)."""

from __future__ import annotations

import logging

from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from engine.governance.database import connection_factory

logger = logging.getLogger(__name__)

AUDIT_SQL = """
    INSERT INTO access_audit (
        user_id, username, endpoint, method,
        response_status, ip_address, purpose, refusal_reason
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def record_access(parameters: tuple) -> bool:
    """Écrit une ligne `access_audit` ; False (et avertissement journalisé) si l'écriture échoue.

    Le journal applicatif ne reçoit que la méthode, le statut et le type d'erreur :
    ni chemin (identifiant patient), ni finalité, ni message de la base.
    """
    method, status = parameters[3], parameters[4]
    try:
        connection = connection_factory()
    except Exception as exc:  # noqa: BLE001 — l'audit ne bloque jamais la réponse
        logger.warning("Audit d'accès NON enregistré (%s %s) : base injoignable (%s)",
                       method, status, type(exc).__name__)
        return False
    try:
        with connection.cursor() as cursor:
            cursor.execute(AUDIT_SQL, parameters)
        connection.commit()
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Audit d'accès NON enregistré (%s %s) : écriture en échec (%s)",
                       method, status, type(exc).__name__)
        return False
    finally:
        connection.close()


class AuditMiddleware(BaseHTTPMiddleware):
    """Journalise chaque accès dans `access_audit` (PostgreSQL central), en échec doux.

    Si l'utilisateur est identifié (request.state.user posé par get_current_user),
    son user_id/username est tracé ; sinon 'anonymous'. La finalité déclarée
    (`request.state.purpose`) et le motif de refus (`request.state.refusal_reason`)
    posés par engine.governance.consent sont également journalisés : un refus
    doit être consultable, pas seulement déduit du code HTTP. Le middleware ne doit
    jamais bloquer la réponse : une erreur de traçage ne l'empêche pas, mais elle est
    signalée dans le journal applicatif (une perte d'audit ne reste pas silencieuse).
    L'écriture, bloquante, s'exécute dans le pool de threads, hors boucle d'événements.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        user = getattr(request.state, "user", None)
        parameters = (
            user.user_id if user else None,
            user.username if user else "anonymous",
            str(request.url.path),
            request.method,
            response.status_code,
            request.client.host if request.client else "unknown",
            getattr(request.state, "purpose", None),
            getattr(request.state, "refusal_reason", None),
        )
        await run_in_threadpool(record_access, parameters)
        return response

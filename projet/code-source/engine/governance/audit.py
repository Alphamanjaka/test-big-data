"""Audit d'acces (portage autonome de test_bigdata)."""

from __future__ import annotations

import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from engine.governance.database import connection_factory


class AuditMiddleware(BaseHTTPMiddleware):
    """Journalise chaque accès dans `access_audit` (PostgreSQL central), en échec doux.

    Si l'utilisateur est identifié (request.state.user posé par get_current_user),
    son user_id/username est tracé ; sinon 'anonymous'. Le middleware ne doit
    jamais bloquer la réponse : toute erreur de traçage est avalée (soft fail).
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)

        user = getattr(request.state, "user", None)
        username = user.username if user else "anonymous"
        user_id = user.user_id if user else None
        ip_address = request.client.host if request.client else "unknown"

        try:
            connection = connection_factory()
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO access_audit (user_id, username, endpoint, method, response_status, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (user_id, username, str(request.url.path), request.method, response.status_code, ip_address),
                )
            connection.commit()
            connection.close()
        except Exception:
            pass

        return response
"""Authentification par cles API (portage autonome de test_bigdata)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from engine.governance.database import connection_factory

security = HTTPBearer(auto_error=False)


@dataclass
class UserContext:
    user_id: int
    username: str
    role: str


def _hash_api_key(api_key: str) -> str:
    """Empreinte SHA-256 de la clé API (jamais stockée en clair)."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def _get_user_by_key(api_key: str) -> Optional[UserContext]:
    """Résout une clé API vers son contexte utilisateur, ou None (invalide/inactif).

    Interroge `api_user(api_key_hash, active)`: la clé brute n'est pas
    transmise à PostgreSQL, seul son hash l'est.
    """
    key_hash = _hash_api_key(api_key)
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, username, role FROM api_user WHERE api_key_hash = %s AND active = TRUE",
                (key_hash,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return UserContext(user_id=row[0], username=row[1], role=row[2])
    finally:
        connection.close()


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Security(security)] = None,
) -> UserContext:
    """Dépendance FastAPI : résout le Bearer token (clé API) vers un UserContext.

    401 si aucun token ou si la clé est inconnue/inactive ; le contexte est
    aussi déposé dans `request.state.user` pour le middleware d'audit.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token d'authentification manquant")
    user = _get_user_by_key(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=401, detail="Token invalide ou utilisateur inactif")
    request.state.user = user
    return user


def require_role(*allowed_roles: str):
    """Garde rôle unique (ex. require_role("admin")) ou multi-rôles.

    Construit une dépendance FastAPI à chaîner après get_current_user:
    renvoie 403 si le rôle de l'utilisateur n'est pas dans la liste.
    """
    async def role_checker(user: Annotated[UserContext, Depends(get_current_user)]) -> UserContext:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse. Role requis: " + ", ".join(allowed_roles),
            )
        return user
    return role_checker
"""Connexions PostgreSQL de l'API gouvernance : pool partagé, DATABASE_URL lue dans .env.

Une requête authentifiée ouvrait jusqu'à quatre connexions (clé API, consentement,
lecture, audit) ; elles sont désormais empruntées à un pool `psycopg_pool`, créé au
premier usage et fermé à l'arrêt de l'API (ou du processus).

`connection_factory()` garde son contrat : l'objet rendu s'utilise comme une
connexion psycopg et `close()` la rend au pool. Une transaction laissée ouverte (une
lecture sans commit) est annulée avant restitution, comme le faisait la fermeture.
"""

from __future__ import annotations

import atexit
import os
import threading

from dotenv import load_dotenv
from psycopg.pq import TransactionStatus

POOL_TIMEOUT_S = 5  # attente maximale d'une connexion (base injoignable : erreur rapide)

_pool = None
_lock = threading.Lock()


class _PooledConnection:
    """Connexion empruntée au pool : délègue à psycopg, `close()` la restitue."""

    def __init__(self, pool, connection):
        self._pool = pool
        self._connection = connection

    def __getattr__(self, name):
        return getattr(self._connection, name)

    def close(self) -> None:
        connection, self._connection = self._connection, None
        if connection is None:
            return
        try:
            if connection.info.transaction_status != TransactionStatus.IDLE:
                connection.rollback()
        finally:
            self._pool.putconn(connection)


def get_pool():
    """Pool unique du processus, ouvert au premier appel."""
    global _pool
    with _lock:
        if _pool is None:
            load_dotenv()
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise RuntimeError("DATABASE_URL is not configured")
            from psycopg_pool import ConnectionPool

            _pool = ConnectionPool(
                database_url,
                min_size=1,
                max_size=int(os.getenv("DB_POOL_MAX_SIZE", "10")),
                timeout=POOL_TIMEOUT_S,
                check=ConnectionPool.check_connection,  # connexion morte (base redémarrée) remplacée
                name="governance-api",
                open=True,
            )
            atexit.register(close_pool)
        return _pool


def close_pool() -> None:
    global _pool
    with _lock:
        if _pool is not None:
            _pool.close()
            _pool = None


def connection_factory():
    pool = get_pool()
    return _PooledConnection(pool, pool.getconn())

import os

import psycopg
from dotenv import load_dotenv


def connection_factory():
    """Create a PostgreSQL connection from the local environment configuration."""
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    return psycopg.connect(database_url)

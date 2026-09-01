from pathlib import Path

from patient_platform.load.database import connection_factory
from patient_platform.load.postgres_loader import PostgresLoader
from patient_platform.pipeline import run_pipeline


def apply_schema() -> None:
    schema = Path("sql/schema.sql").read_text(encoding="utf-8")
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute(schema)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    apply_schema()
    result = run_pipeline("data/raw")
    PostgresLoader(connection_factory).load(
        result.patients, result.identity_map)
    print("Schema applique et donnees synthetiques chargees dans PostgreSQL.")

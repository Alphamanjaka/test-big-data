from pathlib import Path

from patient_platform.config import load_data_root
from patient_platform.load.database import connection_factory
from patient_platform.load.postgres_loader import PostgresLoader
from patient_platform.logging_utils import RuntimeLogger
from patient_platform.pipeline import run_pipeline

LOGGER = RuntimeLogger("logs/runtime.log", "LOGS.md")


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
    LOGGER.info("load_database", status="started")
    apply_schema()
    result = run_pipeline(load_data_root(), "logs/runtime.log", "LOGS.md")
    loader = PostgresLoader(connection_factory, "logs/runtime.log", "LOGS.md")
    loader.load(
        result.patients, result.identity_map, result.raw_records,
        result.business_records)
    LOGGER.info("load_database", status="completed")
    print("Schema applique et donnees synthetiques chargees dans PostgreSQL.")

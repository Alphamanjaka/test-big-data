from collections.abc import Callable
from typing import Any

from patient_platform.deduplication.matcher import MatchDecision
from patient_platform.extract.raw_record import RawPatientRecord
from patient_platform.extract.business_record import BusinessRecord
from patient_platform.transform.canonical import CanonicalPatient

from psycopg.types.json import Json


class PostgresLoader:
    """Loads canonical patients and identity decisions through a DB-API connection."""

    def __init__(self, connection_factory: Callable[[], Any]):
        self.connection_factory = connection_factory

    def load(
        self,
        patients: list[CanonicalPatient],
        identity_map: list[MatchDecision],
        raw_records: list[RawPatientRecord] | None = None,
        business_records: list[BusinessRecord] | None = None,
    ) -> None:
        patients_by_source = {
            (patient.source_system, patient.source_patient_id): patient
            for patient in patients
        }
        master_sources: dict[str, tuple[str, str]] = {}
        for decision in identity_map:
            master_sources.setdefault(
                decision.master_patient_id,
                (decision.source_system, decision.source_patient_id),
            )

        connection = self.connection_factory()
        try:
            with connection.cursor() as cursor:
                for raw_record in raw_records or []:
                    cursor.execute(
                        """
                        INSERT INTO raw_patient_record
                            (source_system, source_patient_id, source_file, payload)
                        VALUES (%s, %s, %s, %s)
                        """,
                        (
                            raw_record.source_system,
                            raw_record.source_patient_id,
                            raw_record.source_file,
                            Json(raw_record.payload),
                        ),
                    )

                source_to_master = {
                    (decision.source_system, decision.source_patient_id): decision.master_patient_id
                    for decision in identity_map
                }
                for record in business_records or []:
                    master_patient_id = source_to_master.get(
                        (record.source_system, record.source_patient_id))
                    if master_patient_id is None:
                        raise ValueError(
                            f"No identity mapping for {record.source_system}:{record.source_patient_id}")
                    table_by_domain = {
                        "purchase": "medicine_purchase",
                        "consultation": "patient_consultation",
                        "imaging_exam": "imaging_exam",
                    }
                    cursor.execute(
                        f"""
                        INSERT INTO {table_by_domain[record.domain]}
                            (source_record_id, master_patient_id, source_system,
                             source_patient_id, payload)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (source_system, source_record_id) DO NOTHING
                        """,
                        (record.source_record_id, master_patient_id,
                         record.source_system, record.source_patient_id,
                         Json(record.payload)),
                    )

                for master_patient_id, source_key in master_sources.items():
                    patient = patients_by_source[source_key]
                    cursor.execute(
                        """
                        INSERT INTO master_patient
                            (master_patient_id, first_name, last_name, full_name,
                             birth_date, phone, address)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (master_patient_id) DO UPDATE SET
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            full_name = EXCLUDED.full_name,
                            birth_date = EXCLUDED.birth_date,
                            phone = EXCLUDED.phone,
                            address = EXCLUDED.address
                        """,
                        (
                            master_patient_id,
                            patient.first_name,
                            patient.last_name,
                            patient.full_name,
                            patient.birth_date,
                            patient.phone,
                            patient.address,
                        ),
                    )

                for decision in identity_map:
                    cursor.execute(
                        """
                        INSERT INTO patient_identity_map
                            (master_patient_id, source_system, source_patient_id,
                             match_method, match_score, explanation)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (source_system, source_patient_id) DO UPDATE SET
                            master_patient_id = EXCLUDED.master_patient_id,
                            match_method = EXCLUDED.match_method,
                            match_score = EXCLUDED.match_score,
                            explanation = EXCLUDED.explanation
                        """,
                        (
                            decision.master_patient_id,
                            decision.source_system,
                            decision.source_patient_id,
                            decision.method,
                            decision.score,
                            decision.explanation,
                        ),
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

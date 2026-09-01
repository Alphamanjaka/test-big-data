from collections.abc import Callable
from typing import Any

from patient_platform.deduplication.matcher import MatchDecision
from patient_platform.transform.canonical import CanonicalPatient


class PostgresLoader:
    """Loads canonical patients and identity decisions through a DB-API connection."""

    def __init__(self, connection_factory: Callable[[], Any]):
        self.connection_factory = connection_factory

    def load(
        self,
        patients: list[CanonicalPatient],
        identity_map: list[MatchDecision],
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

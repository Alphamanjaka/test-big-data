from patient_platform.load.database import connection_factory


def reset_database() -> None:
    """Vide toutes les tables (données + API + consentement), schéma conservé."""
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE access_audit, api_user,
                             patient_identity_map, medicine_purchase,
                             patient_consultation, imaging_exam,
                             consent, master_patient, raw_patient_record
                RESTART IDENTITY CASCADE
                """
            )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


if __name__ == "__main__":
    reset_database()
    print("Base PostgreSQL réinitialisée (toutes les tables vidées, schéma conservé).")
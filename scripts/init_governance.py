import hashlib
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from patient_platform.load.database import connection_factory


def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def apply_governance_schema():
    schema_path = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute(schema_path.read_text(encoding="utf-8"))
        connection.commit()
        print("OK | schema | Tables gouvernance appliquees")
    finally:
        connection.close()


def create_demo_users() -> list[dict]:
    users = [
        {"username": "admin", "role": "admin"},
        {"username": "analyst", "role": "analyst"},
        {"username": "viewer", "role": "viewer"},
    ]

    created = []
    connection = connection_factory()
    try:
        for user in users:
            api_key = secrets.token_hex(32)
            api_key_hash = _hash_api_key(api_key)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO api_user (username, api_key_hash, role)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (username) DO UPDATE SET api_key_hash = EXCLUDED.api_key_hash
                        RETURNING user_id
                        """,
                        (user["username"], api_key_hash, user["role"]),
                    )
                    user_id = cursor.fetchone()[0]
                connection.commit()
                created.append({**user, "user_id": user_id, "api_key": api_key})
                print(f"OK | user | {user['username']} ({user['role']}) cree")
            except Exception as e:
                connection.rollback()
                print(f"WARN | user | {user['username']} erreur: {e}")
    finally:
        connection.close()

    return created


def create_demo_consents():
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT master_patient_id FROM master_patient ORDER BY master_patient_id")
            patients = [row[0] for row in cursor.fetchall()]

        if not patients:
            print("WARN | consent | Aucun patient master trouve, consentements non crees")
            return

        purposes = ["api_access", "research", "analytics"]
        for patient_id in patients:
            for purpose in purposes:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO consent (master_patient_id, purpose, granted)
                            VALUES (%s, %s, TRUE)
                            ON CONFLICT DO NOTHING
                            """,
                            (patient_id, purpose),
                        )
                    connection.commit()
                except Exception:
                    connection.rollback()

        print(f"OK | consent | Consentements crees pour {len(patients)} patients")
    finally:
        connection.close()


def main():
    print("=== Initialisation de la gouvernance ===\n")

    apply_governance_schema()

    print("\n--- Creation des utilisateurs de demo ---")
    users = create_demo_users()

    print("\n--- Creation des consentements de demo ---")
    create_demo_consents()

    print("\n=== Cles API a conserver ===")
    for user in users:
        print(f"  {user['username']:10s} ({user['role']:8s}) -> {user['api_key']}")

    print("\n=== Termine ===")


if __name__ == "__main__":
    main()

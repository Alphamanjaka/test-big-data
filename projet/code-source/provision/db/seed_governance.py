"""Seed gouvernance : utilisateurs de démonstration + consentements (données synthétiques).

Alimente la base PostgreSQL centrale (`patient_plateform`) après le pipeline
Medallion, pour rendre la démonstration de gouvernance jouable :

1. applique `sql/schema.sql` (idempotent) ;
2. crée trois utilisateurs de démonstration (`admin`, `analyst`, `viewer`) avec
   des clés API générées à l'exécution ;
3. crée des consentements **partiels et déterministes** sur les finalités
   normalisées de `engine.governance.consent.PURPOSES`.

Le mélange volontaire d'accords et de refus n'est pas décoratif : il permet de
démontrer le 403 de `/patients/{id}` et le filtrage de `/patients`, qui sont le
cœur de la démonstration. Un seed « tout accordé » ne prouverait rien.

Sécurité : aucune clé n'est écrite en dur dans le dépôt ; elles sont générées par
`secrets.token_hex` et affichées une seule fois. Ne pas rediriger cette sortie
vers un fichier versionné.

Usage :
    python -m provision.db.seed_governance          # depuis projet/code-source
    DATABASE_URL=postgresql://... python provision/db/seed_governance.py
"""

from __future__ import annotations

import hashlib
import secrets
import sys
from pathlib import Path

CODE_ROOT = Path(__file__).resolve().parent.parent.parent
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from engine.governance.consent import PURPOSES
from engine.governance.database import connection_factory

# Part d'accords simulée par finalité : le refus doit être démontrable.
#   api_access -> accordé partout (accès opérationnel de l'API)
#   research   -> accordé à 7 patients sur 10
#   analytics  -> accordé à 4 patients sur 10
GRANT_RULE = {
    "api_access": lambda bucket: True,
    "research": lambda bucket: bucket < 7,
    "analytics": lambda bucket: bucket < 4,
}

DEMO_USERS = [
    {"username": "admin", "role": "admin"},
    {"username": "analyst", "role": "analyst"},
    {"username": "viewer", "role": "viewer"},
]


def _hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()


def _bucket(master_patient_id: str) -> int:
    """Bucket déterministe 0-9 : le seed est reproductible d'un run à l'autre."""
    digest = hashlib.sha1(master_patient_id.encode()).hexdigest()[:8]
    return int(digest, 16) % 10


def apply_governance_schema() -> None:
    schema_path = CODE_ROOT / "sql" / "schema.sql"
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute(schema_path.read_text(encoding="utf-8"))
        connection.commit()
        print(f"OK  | schema   | {schema_path.name} applique (idempotent)")
    finally:
        connection.close()


def create_demo_users() -> list:
    created = []
    connection = connection_factory()
    try:
        for user in DEMO_USERS:
            api_key = secrets.token_hex(32)
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO api_user (username, api_key_hash, role)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (username) DO UPDATE
                            SET api_key_hash = EXCLUDED.api_key_hash,
                                role = EXCLUDED.role,
                                active = TRUE
                        RETURNING user_id
                        """,
                        (user["username"], _hash_api_key(api_key), user["role"]),
                    )
                    user_id = cursor.fetchone()[0]
                connection.commit()
                created.append({**user, "user_id": user_id, "api_key": api_key})
                print(f"OK  | user     | {user['username']:8s} ({user['role']}) user_id={user_id}")
            except Exception as exc:
                connection.rollback()
                print(f"WARN| user     | {user['username']} : {exc}")
    finally:
        connection.close()
    return created


def list_master_patients() -> list:
    connection = connection_factory()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT master_patient_id FROM master_patient ORDER BY master_patient_id")
            return [row[0] for row in cursor.fetchall()]
    finally:
        connection.close()


def create_demo_consents() -> dict:
    patients = list_master_patients()
    if not patients:
        print("WARN| consent  | aucun master_patient : lancez d'abord le pipeline (create_gold.py)")
        return {}

    # Idempotent et non destructif : on n'insère que les couples
    # (patient, finalité) encore absents, jamais de DELETE — un historique de
    # consentement ne doit pas être écrasé par un simple rejeu du seed.
    rows = []
    for patient_id in patients:
        bucket = _bucket(patient_id)
        for purpose in PURPOSES:
            rule = GRANT_RULE.get(purpose)
            if rule is None:
                raise ValueError(
                    f"Finalite {purpose} sans regle dans GRANT_RULE : "
                    "mettre a jour le seed en meme temps que PURPOSES"
                )
            rows.append((patient_id, purpose, rule(bucket)))

    inserted = {purpose: 0 for purpose in PURPOSES}
    connection = connection_factory()
    try:
        for patient_id, purpose, granted in rows:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO consent (master_patient_id, purpose, granted)
                    SELECT %s, %s, %s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM consent
                        WHERE master_patient_id = %s AND purpose = %s
                    )
                    """,
                    (patient_id, purpose, granted, patient_id, purpose),
                )
                if cursor.rowcount:
                    inserted[purpose] += cursor.rowcount
        connection.commit()
    finally:
        connection.close()

    for purpose in PURPOSES:
        print(f"OK  | consent  | {purpose:10s} {inserted[purpose]}/{len(patients)} insere(s)")
    return inserted


def main() -> int:
    print("=== Seed gouvernance (donnees synthetiques) ===\n")
    apply_governance_schema()
    print()
    users = create_demo_users()
    print()
    create_demo_consents()

    print("\n=== Cles API de demonstration ( confidentielles : ne pas versionner ) ===")
    for user in users:
        print(f"  {user['username']:8s} ({user['role']:8s}) -> {user['api_key']}")
    print("\n=== Termine ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

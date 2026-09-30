#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""central_db.py — chargement de la base centrale PostgreSQL par le pipeline.

Après la déduplication de l'étape SILVER, les patients maîtres et la table de
correspondance (identity map) sont écrits dans la base centrale décrite par
`sql/schema.sql` : c'est elle que lit l'API de gouvernance. Sans ce chargement, les
décisions du moteur ne vivraient que dans le lac, et l'API n'aurait rien à servir.

- Un patient maître est créé par chaque décision `new_master` ; son identité est celle
  de la fiche qui l'a fondé (modèle canonique).
- Chaque fiche source reçoit sa ligne de correspondance : patient maître, méthode,
  score et explication.
- Les écritures sont idempotentes (`ON CONFLICT`) : rejouer un run met à jour sans
  dupliquer ; le schéma est appliqué avant écriture (`IF NOT EXISTS`).
- Sans `DATABASE_URL`, ou si la base est injoignable, rien n'est écrit et le pipeline
  continue : la base centrale est un aval du lac, pas une condition de son succès.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "sql" / "schema.sql"

MASTER_SQL = (
    "INSERT INTO master_patient (master_patient_id, first_name, last_name, full_name, "
    "birth_date, cin, birth_city, address, gender) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
    "ON CONFLICT (master_patient_id) DO UPDATE SET "
    "first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, "
    "full_name = EXCLUDED.full_name, birth_date = EXCLUDED.birth_date, "
    "cin = EXCLUDED.cin, birth_city = EXCLUDED.birth_city, "
    "address = EXCLUDED.address, gender = EXCLUDED.gender"
)

IDENTITY_SQL = (
    "INSERT INTO patient_identity_map (master_patient_id, source_system, "
    "source_patient_id, match_method, match_score, explanation) "
    "VALUES (%s, %s, %s, %s, %s, %s) "
    "ON CONFLICT (source_system, source_patient_id) DO UPDATE SET "
    "master_patient_id = EXCLUDED.master_patient_id, "
    "match_method = EXCLUDED.match_method, match_score = EXCLUDED.match_score, "
    "explanation = EXCLUDED.explanation, matched_at = NOW()"
)


def build_rows(patients: Iterable[Any], decisions: Iterable[Any]) -> Tuple[List[tuple], List[tuple]]:
    """Lignes `master_patient` et `patient_identity_map` à partir des décisions du moteur."""
    by_key = {(p.source_system, p.source_patient_id): p for p in patients}
    masters: List[tuple] = []
    identities: List[tuple] = []
    for d in decisions:
        if d.method == "new_master":
            p = by_key.get((d.source_system, d.source_patient_id))
            if p is not None:
                masters.append((
                    d.master_patient_id, p.first_name, p.last_name, p.full_name,
                    p.birth_date, p.cin or None, p.birth_city, p.address,
                    p.gender if p.gender in ("M", "F") else "",
                ))
        identities.append((
            d.master_patient_id, d.source_system, d.source_patient_id,
            d.method, round(float(d.score), 3), d.explanation,
        ))
    return masters, identities


def save_rows(conn, masters: List[tuple], identities: List[tuple], schema_sql: str = None) -> Dict[str, int]:
    """Applique le schéma puis écrit les maîtres avant leurs correspondances (clé étrangère)."""
    with conn.cursor() as cur:
        if schema_sql:
            cur.execute(schema_sql)
        if masters:
            cur.executemany(MASTER_SQL, masters)
        if identities:
            cur.executemany(IDENTITY_SQL, identities)
    conn.commit()
    return {"master_patient": len(masters), "patient_identity_map": len(identities)}


def _connect():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return None
    import psycopg

    return psycopg.connect(database_url)


def load_central_db(patients, decisions, connect=_connect, logger=None) -> Optional[Dict[str, int]]:
    """Charge la base centrale ; ne lève jamais. Retourne les volumes écrits, ou None."""
    def log(level, message):
        if logger is not None:
            getattr(logger, level)(message)

    try:
        conn = connect()
    except Exception as exc:  # noqa: BLE001 — la base est un aval, pas une condition
        log("warning", f"Base centrale injoignable ({exc}) — patients maîtres non chargés.")
        return None
    if conn is None:
        log("info", "DATABASE_URL absente — base centrale non chargée.")
        return None
    try:
        masters, identities = build_rows(patients, decisions)
        schema_sql = SCHEMA_PATH.read_text(encoding="utf-8") if SCHEMA_PATH.exists() else None
        counts = save_rows(conn, masters, identities, schema_sql)
        log("info", f"Base centrale : {counts['master_patient']} patients maîtres, "
                    f"{counts['patient_identity_map']} correspondances écrits.")
        return counts
    except Exception as exc:  # noqa: BLE001
        try:
            conn.rollback()
        except Exception:  # noqa: BLE001
            pass
        log("warning", f"Chargement de la base centrale en échec ({exc}).")
        return None
    finally:
        conn.close()

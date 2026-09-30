#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
hive_api.py — API Flask exposant les indicateurs de gouvernance du Data Lake
=============================================================================
Interroge les tables SILVER/GOLD (déduplication, consentement purpose-by-purpose)
via PySpark/Hive et renvoie du JSON pour le frontend Next.js.

Port : défini par FLASK_PORT (pipeline.yaml → api.flask_port)
"""

import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from pyspark.sql import SparkSession

try:
    from ..scripts.utils.paths import (
        SILVER_PATIENT_TABLE, CONSENT_GOLD_TABLE,
        CORS_ORIGINS, SPARK_EXECUTOR_MEMORY, SPARK_DRIVER_MEMORY,
        FLASK_PORT,
    )
except ImportError:
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
    from utils.paths import (
        SILVER_PATIENT_TABLE, CONSENT_GOLD_TABLE,
        CORS_ORIGINS, SPARK_EXECUTOR_MEMORY, SPARK_DRIVER_MEMORY,
        FLASK_PORT,
    )

try:
    from .mock_data import MOCK_GOVERNANCE_DUPLICATES, MOCK_CONSENT
except ImportError:
    from mock_data import MOCK_GOVERNANCE_DUPLICATES, MOCK_CONSENT

app = Flask(__name__)

# --- CORS ---
CORS(app, resources={
    r"/*": {
        "origins": CORS_ORIGINS,
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# --- Spark ---
spark = SparkSession.builder \
    .appName("GOVERNANCE_API") \
    .config("spark.executor.memory", SPARK_EXECUTOR_MEMORY) \
    .config("spark.driver.memory", SPARK_DRIVER_MEMORY) \
    .enableHiveSupport() \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")


def is_empty(data):
    """True si la donnée est vide (None, '', [], {}, etc.)."""
    if data is None:
        return True
    if isinstance(data, (str, list, tuple, dict)):
        return len(data) == 0
    return False


def refresh(table):
    """Invalide le cache de listing de la table avant lecture.

    La session Spark de l'API vit plus longtemps qu'un run du pipeline : après une
    réécriture de la table, elle lirait des fichiers supprimés et retomberait sur le
    mock jusqu'au redémarrage de l'API.
    """
    try:
        spark.catalog.refreshTable(table)
    except Exception as e:  # noqa: BLE001 — table absente : la requête échouera plus loin
        logging.info(f"Rafraîchissement impossible pour {table} ({e}).")


def respond(data, filters=None, mocked=False, **meta):
    """Construit une réponse uniforme, avec indication si les données sont mockées."""
    body = {
        "success": True,
        "filters": filters or {},
        "data": data,
        "mocked": bool(mocked),
    }
    body.update(meta)
    return jsonify(body)

# ============================================================
# ROUTES
# ============================================================

# 1 Gouvernance — indicateurs de déduplication (SILVER patient + moteur)
@app.route("/api/governance/duplicates")
def governance_duplicates():
    """KPIs déduplication : total masters, doublons, taux, répartition par méthode.

    Lecture dans `datalake_silver.patient_fhir` (colonnes master_patient_id,
    is_duplicate, match_method). Fallback MOCK si Spark/Hive indisponible.
    """
    try:
        refresh(SILVER_PATIENT_TABLE)
        row = spark.sql(f"""
            SELECT
                COUNT(*) AS total_patients,
                COUNT(DISTINCT master_patient_id) AS total_masters,
                SUM(CASE WHEN is_duplicate THEN 1 ELSE 0 END) AS duplicates
            FROM {SILVER_PATIENT_TABLE}
        """).collect()[0]
        total = row["total_patients"] or 0
        masters = row["total_masters"] or 0
        duplicates = row["duplicates"] or 0
        rows = spark.sql(f"""
            SELECT match_method, COUNT(*) AS n
            FROM {SILVER_PATIENT_TABLE}
            WHERE match_method IS NOT NULL
            GROUP BY match_method
        """).collect()
        by_method = {r["match_method"]: r["n"] for r in rows}
        rate = round(duplicates * 100.0 / total, 2) if total else 0.0
        data = {
            "total_patients": total,
            "total_masters": masters,
            "duplicates": duplicates,
            "duplicate_rate": rate,
            "by_method": by_method,
        }
        return respond(data, mocked=False)
    except Exception as e:
        logging.warning(f"KPIs déduplication indisponibles ({e}) — fallback mock.")
        return respond(dict(MOCK_GOVERNANCE_DUPLICATES), mocked=True)

# 2 Gouvernance — consentements purpose-by-purpose (GOLD)
@app.route("/api/governance/consent")
def governance_consent():
    """Liste des consentements GOLD (purpose-by-purpose) avec stats agrégées.

    Lit `datalake_gold.patient_consent_gold`, ajoute total_consents /
    granted_count / patients en métadonnées de réponse. Fallback MOCK si la
    table est vide ou indisponible.
    """
    limit = int(request.args.get("limit", 200))
    try:
        refresh(CONSENT_GOLD_TABLE)
        rows = spark.sql(f"""
            SELECT master_patient_id, patient_uuid, name, purpose, granted, recorded_at
            FROM {CONSENT_GOLD_TABLE}
            ORDER BY master_patient_id
            LIMIT {limit}
        """).collect()
        data = [r.asDict() for r in rows]
        if is_empty(data):
            raise ValueError("table consent GOLD vide")
        stats = spark.sql(f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN granted THEN 1 ELSE 0 END) AS granted_count,
                COUNT(DISTINCT master_patient_id) AS patients
            FROM {CONSENT_GOLD_TABLE}
        """).collect()[0]
        meta = {
            "total_consents": stats["total"] or 0,
            "granted_count": stats["granted_count"] or 0,
            "patients": stats["patients"] or 0,
        }
        return respond(data, mocked=False, **meta)
    except Exception as e:
        logging.warning(f"Consentements GOLD indisponibles ({e}) — fallback mock.")
        granted = sum(1 for c in MOCK_CONSENT if c["granted"])
        return respond(
            list(MOCK_CONSENT[:limit]),
            mocked=True,
            total_consents=len(MOCK_CONSENT),
            granted_count=granted,
            patients=len({c["master_patient_id"] for c in MOCK_CONSENT}),
        )

# --- Lancement ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
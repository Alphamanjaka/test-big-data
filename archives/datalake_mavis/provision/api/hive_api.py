#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
hive_api.py — API Flask exposant les données GOLD du Data Lake
===============================================================
Interroge la table datalake_gold.patient_events_gold via PySpark/Hive
et renvoie du JSON pour le frontend Next.js.

Port : 5000
"""

import json
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from pyspark.sql import SparkSession, functions as F
from datetime import datetime, timedelta

try:
    from .mock_data import (
        MOCK_DIAGNOSTICS_HEATMAP,
        MOCK_MORTALITY,
        MOCK_MATERNITE,
        MOCK_LABORATORY,
        MOCK_MALARIA,
        MOCK_ADMISSIONS_SUMMARY,
        MOCK_TOP_DIAGNOSTICS,
        MOCK_LAST_SYNC,
    )
except ImportError:
    from mock_data import (
        MOCK_DIAGNOSTICS_HEATMAP,
        MOCK_MORTALITY,
        MOCK_MATERNITE,
        MOCK_LABORATORY,
        MOCK_MALARIA,
        MOCK_ADMISSIONS_SUMMARY,
        MOCK_TOP_DIAGNOSTICS,
        MOCK_LAST_SYNC,
    )

app = Flask(__name__)

# --- Configuration ---
GOLD_TABLE = "datalake_gold.patient_events_gold"
SYNC_METADATA_PATH = "/home/vagrant/datalake-mavis/provision/metadata/sync_metadata.json"
USE_MOCK_FALLBACK = os.environ.get("RMA_USE_MOCK", "true").lower() == "true"

# --- CORS ---
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://192.168.56.1:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# --- Spark ---
spark = SparkSession.builder \
    .appName("RMA_API") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.memory", "2g") \
    .enableHiveSupport() \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# --- Helpers ---
def get_default_dates():
    today = datetime.today()
    start = (today - timedelta(days=365)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    return start, end

def build_where_clause(start, end, sex=None):
    clauses = [f"admission_date BETWEEN DATE('{start}') AND DATE('{end}')"]
    if sex and sex.lower() in ["male", "female"]:
        clauses.append(f"gender = '{sex.lower()}'")
    return " AND ".join(clauses)

def df_to_json(df):
    return [row.asDict() for row in df.collect()]


def is_empty(data):
    """True si la donnée est vide (None, '', [], {}, etc.)."""
    if data is None:
        return True
    if isinstance(data, (str, list, tuple, dict)):
        return len(data) == 0
    return False

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

@app.route("/rma/last_sync")
def last_sync():
    """Dernière synchronisation du pipeline."""
    if os.path.exists(SYNC_METADATA_PATH):
        try:
            with open(SYNC_METADATA_PATH) as f:
                meta = json.load(f)
            if is_empty(meta):
                return jsonify({"success": True, "last_sync": MOCK_LAST_SYNC, "mocked": True})
            meta.setdefault("success", True)
            return jsonify(meta)
        except (json.JSONDecodeError, OSError):
            pass
    return jsonify({"success": True, "last_sync": MOCK_LAST_SYNC, "mocked": True})

# 1 Dashboard — Admissions summary
@app.route("/rma/admissions_summary")
def admissions_summary():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")

    where = build_where_clause(start_date, end_date, sex)

    df = spark.sql(f"""
        SELECT
            COUNT(*) AS total_admissions,
            ROUND(
                SUM(CASE WHEN mortality = 1 AND DATEDIFF(admission_date, birth_date) <= 365 THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(*), 0), 2
            ) AS mortalite_infantile,
            ROUND(
                SUM(CASE WHEN mortality = 1 AND gender = 'female'
                    AND diagnosis_code LIKE 'O%' THEN 1 ELSE 0 END) * 100.0
                / NULLIF(COUNT(*), 0), 2
            ) AS mortalite_maternelle
        FROM {GOLD_TABLE}
        WHERE {where}
    """).collect()[0]

    data = {
        "total_admissions": df["total_admissions"],
        "mortalite_infantile": df["mortalite_infantile"],
        "mortalite_maternelle": df["mortalite_maternelle"],
    }

    mocked = False
    if USE_MOCK_FALLBACK and (data["total_admissions"] is None or data["total_admissions"] == 0):
        data = dict(MOCK_ADMISSIONS_SUMMARY)
        mocked = True

    return respond(data, filters={"start": start_date, "end": end_date, "sex": sex}, mocked=mocked)

# 2 Dashboard — Top diagnostics
@app.route("/rma/top_diagnostics")
def top_diagnostics():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")
    limit = int(request.args.get("limit", 5))

    where = build_where_clause(start_date, end_date, sex)

    rows = spark.sql(f"""
        SELECT diagnosis_code, diagnosis, COUNT(*) AS total
        FROM {GOLD_TABLE}
        WHERE {where}
          AND diagnosis_code IS NOT NULL
        GROUP BY diagnosis_code, diagnosis
        ORDER BY total DESC
        LIMIT {limit}
    """).collect()

    data = [r.asDict() for r in rows]
    mocked = False
    if USE_MOCK_FALLBACK and is_empty(data):
        data = list(MOCK_TOP_DIAGNOSTICS[:limit])
        mocked = True

    return respond(data, filters={"start": start_date, "end": end_date, "sex": sex}, mocked=mocked)

# 3 Diagnostics heatmap (par tranches d'âge)
@app.route("/rma/diagnostics_heatmap")
def diagnostics_heatmap():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")
    limit = int(request.args.get("limit", 15))

    where = build_where_clause(start_date, end_date, sex)

    rows = spark.sql(f"""
        SELECT
            diagnosis_code,
            diagnosis,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) <= 28 THEN 1 ELSE 0 END) AS age_0_28j,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 29 AND 59 THEN 1 ELSE 0 END) AS age_29_59j,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 60 AND 335 THEN 1 ELSE 0 END) AS age_2_11m,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 336 AND 1460 THEN 1 ELSE 0 END) AS age_1_4a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 1461 AND 5110 THEN 1 ELSE 0 END) AS age_5_14a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 5111 AND 8765 THEN 1 ELSE 0 END) AS age_15_24a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 8766 AND 21548 THEN 1 ELSE 0 END) AS age_25_59a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) > 21548 THEN 1 ELSE 0 END) AS age_60plus,
            COUNT(*) AS total
        FROM {GOLD_TABLE}
        WHERE {where}
          AND diagnosis_code IS NOT NULL
        GROUP BY diagnosis_code, diagnosis
        ORDER BY total DESC
        LIMIT {limit}
    """).collect()

    data = [r.asDict() for r in rows]
    mocked = False
    if USE_MOCK_FALLBACK and is_empty(data):
        data = list(MOCK_DIAGNOSTICS_HEATMAP[:limit])
        mocked = True

    return respond(data, filters={"start": start_date, "end": end_date, "sex": sex}, mocked=mocked)

# 4 Diagnostics list (paginée)
@app.route("/rma/diagnostics_list")
def diagnostics_list():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 20))

    where = build_where_clause(start_date, end_date, sex)

    rows = spark.sql(f"""
        SELECT
            diagnosis_code,
            diagnosis,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) <= 28 THEN 1 ELSE 0 END) AS age_0_28j,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 29 AND 59 THEN 1 ELSE 0 END) AS age_29_59j,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 60 AND 335 THEN 1 ELSE 0 END) AS age_2_11m,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 336 AND 1460 THEN 1 ELSE 0 END) AS age_1_4a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 1461 AND 5110 THEN 1 ELSE 0 END) AS age_5_14a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 5111 AND 8765 THEN 1 ELSE 0 END) AS age_15_24a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) BETWEEN 8766 AND 21548 THEN 1 ELSE 0 END) AS age_25_59a,
            SUM(CASE WHEN DATEDIFF(admission_date, birth_date) > 21548 THEN 1 ELSE 0 END) AS age_60plus,
            COUNT(*) AS total
        FROM {GOLD_TABLE}
        WHERE {where}
          AND diagnosis_code IS NOT NULL
        GROUP BY diagnosis_code, diagnosis
        ORDER BY total DESC
    """).collect()

    start_idx = (page - 1) * limit
    raw_rows = [r.asDict() for r in rows]

    mocked = False
    if USE_MOCK_FALLBACK and is_empty(raw_rows):
        raw_rows = list(MOCK_DIAGNOSTICS_HEATMAP)
        mocked = True

    paginated = raw_rows[start_idx:start_idx + limit]

    return respond(
        paginated,
        filters={"start": start_date, "end": end_date, "sex": sex},
        mocked=mocked,
        page=page,
        limit=limit,
        total=len(raw_rows),
    )

# 5 Morbidité / mortalité (Tableau 9)
@app.route("/api/rma/mortality")
def mortality():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")

    where = build_where_clause(start_date, end_date, sex)

    rows = spark.sql(f"""
        SELECT
            COALESCE(category, 'Autre') AS service,
            diagnosis_code AS code,
            diagnosis AS diagnostic,
            COUNT(*) AS cas,
            SUM(CASE WHEN mortality = 1 THEN 1 ELSE 0 END) AS deces
        FROM {GOLD_TABLE}
        WHERE {where}
          AND diagnosis_code IS NOT NULL
        GROUP BY category, diagnosis_code, diagnosis
        ORDER BY cas DESC
    """).collect()

    data = [r.asDict() for r in rows]
    mocked = False
    if USE_MOCK_FALLBACK and is_empty(data):
        data = list(MOCK_MORTALITY)
        mocked = True

    return respond(data, filters={"start": start_date, "end": end_date, "sex": sex}, mocked=mocked)

# 6 Maternité (Tableaux 11/12) — agrégation mensuelle
@app.route("/api/rma/maternity")
def maternity():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")

    where = build_where_clause(start_date, end_date, sex)

    rows = spark.sql(f"""
        SELECT
            DATE_FORMAT(admission_date, 'yyyy-MM') AS month,
            COUNT(*) AS total,
            SUM(CASE WHEN diagnosis_code LIKE 'O%' THEN 1 ELSE 0 END) AS accouchements,
            SUM(CASE WHEN mortality = 1 AND gender = 'female'
                AND diagnosis_code LIKE 'O%' THEN 1 ELSE 0 END) AS deces_maternels,
            SUM(CASE WHEN live_births IS NOT NULL THEN live_births ELSE 0 END) AS live_births_total
        FROM {GOLD_TABLE}
        WHERE {where}
          AND gender = 'female'
        GROUP BY DATE_FORMAT(admission_date, 'yyyy-MM')
        ORDER BY month
    """).collect()

    data = [r.asDict() for r in rows]
    mocked = False
    if USE_MOCK_FALLBACK and is_empty(data):
        data = list(MOCK_MATERNITE)
        mocked = True

    return respond(data, filters={"start": start_date, "end": end_date, "sex": sex}, mocked=mocked)

# 7 Laboratoire — données non dans GOLD, mock côté backend
@app.route("/api/rma/laboratory")
def laboratory():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")

    return respond(
        list(MOCK_LABORATORY),
        filters={"start": start_date, "end": end_date, "sex": sex},
        mocked=USE_MOCK_FALLBACK,
    )

# 8 Paludisme — données non dans GOLD, mock côté backend
@app.route("/api/rma/malaria")
def malaria():
    start, end = get_default_dates()
    start_date = request.args.get("start", start)
    end_date = request.args.get("end", end)
    sex = request.args.get("sex")

    return respond(
        dict(MOCK_MALARIA),
        filters={"start": start_date, "end": end_date, "sex": sex},
        mocked=USE_MOCK_FALLBACK,
    )

# --- Lancement ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

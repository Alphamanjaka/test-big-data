#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_gold.py
==============
Transformation des tables SILVER vers une table GOLD centralisée
prête pour le dashboard (RMA) avec tranches d'âge spécifiques.
"""

import logging
import os
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StringType, BooleanType

from ..utils.sync_utils import update_sync_metadata
from ..utils.paths import (
    HIVE_SILVER, HIVE_GOLD, GOLD_TABLE, CONSENT_GOLD_TABLE,
    hdfs_warehouse, AGE_TRANCHES,
    LOG_DIR, SPARK_EXECUTOR_MEMORY, SPARK_DRIVER_MEMORY, SPARK_SHUFFLE_PARTITIONS,
)

# -----------------------------
# 🔧 CONFIGURATION
# -----------------------------
# Bases Hive : HIVE_SILVER / HIVE_GOLD (importées de utils.paths)

# -----------------------------
# 🔧 LOGGING
# -----------------------------
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "create_gold.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

logging.info("✅ Début de create_gold.py")

# -----------------------------
# 🔥 INITIALISATION SPARK
# -----------------------------
spark = SparkSession.builder \
    .appName("create_gold") \
    .config("spark.sql.warehouse.dir", hdfs_warehouse("gold")) \
    .config("spark.executor.memory", SPARK_EXECUTOR_MEMORY) \
    .config("spark.driver.memory", SPARK_DRIVER_MEMORY) \
    .config("spark.sql.shuffle.partitions", SPARK_SHUFFLE_PARTITIONS) \
    .enableHiveSupport() \
    .getOrCreate()

spark.sql(f"CREATE DATABASE IF NOT EXISTS {HIVE_GOLD}")
logging.info(f"✅ Base GOLD {HIVE_GOLD} vérifiée")

# -----------------------------
# 📥 LECTURE DES TABLES SILVER
# -----------------------------
from pyspark.sql.types import StructType, StructField

def _lire_silver(table):
    """Lit une table SILVER; retourne None si elle est absente."""
    try:
        df = spark.table(table)
        logging.info(f"✅ Table SILVER chargée : {table} ({df.count()} lignes)")
        return df
    except Exception as e:
        logging.warning(f"⚠️ Table SILVER absente ({table}) — remplacée par une table vide. ({e})")
        return None

def _vide(colonnes):
    """DataFrame vide au schéma attendu."""
    schema = StructType([StructField(c, StringType(), True) for c in colonnes])
    return spark.createDataFrame([], schema)

df_patient = _lire_silver(f"{HIVE_SILVER}.patient_fhir")
df_encounter = _lire_silver(f"{HIVE_SILVER}.encounter_fhir")
df_condition = _lire_silver(f"{HIVE_SILVER}.condition_fhir")
df_observation = _lire_silver(f"{HIVE_SILVER}.observation_fhir")
if df_patient is None:
    logging.error("patient_fhir absente — GOLD impossible.")
    raise SystemExit(1)

# -----------------------------
# 🎯 RÉDUCTION AUX COLONNES UTILES
# -----------------------------
df_patient = df_patient.select(
    "patient_uuid", "source_patient_id", "name", "gender", "birth_date"
)
df_encounter = (df_encounter if df_encounter is not None else _vide(
    ["patient_uuid", "encounter_id", "admission_date", "discharge_date", "visit_type"]
)).select(
    "patient_uuid", "encounter_id", "admission_date", "discharge_date", "visit_type"
)
df_condition = (df_condition if df_condition is not None else _vide(
    ["patient_uuid", "diagnosis_code", "category", "diagnosis"]
)).select(
    F.col("patient_uuid").alias("patient_uuid_cond"),
    "diagnosis_code",
    "category",
    "diagnosis",
)
df_observation = (df_observation if df_observation is not None else _vide(
    ["patient_uuid", "mortality", "parity", "gravida", "live_births"]
)).select(
    F.col("patient_uuid").alias("patient_uuid_obs"),
    "mortality", "parity", "gravida", "live_births",
)

# -----------------------------
# 📅 CALCUL DE L'AGE ET TRANCHE D'AGE
# -----------------------------
df_patient = df_patient.withColumn(
    "birth_date", F.to_date(F.col("birth_date"))
)
df_patient = df_patient.withColumn(
    "age", F.datediff(F.current_date(), F.col("birth_date")) / 365.25
)

def assign_age_tranche(age):
    if age is None:
        return "unknown"
    for min_age, max_age, label in AGE_TRANCHES:
        if min_age <= age <= max_age:
            return label
    return "unknown"

udf_age_tranche = F.udf(assign_age_tranche, StringType())
df_patient = df_patient.withColumn("age_tranche", udf_age_tranche(F.col("age")))

# -----------------------------
# 🔗 JOINTURES PATIENT ↔ ENTITÉS
# -----------------------------
df_encounter = df_encounter.withColumn("admission_date", F.to_date(F.col("admission_date")))
df_encounter = df_encounter.withColumn("discharge_date", F.to_date(F.col("discharge_date")))

df_gold = df_encounter.join(df_patient, on="patient_uuid", how="left")
df_gold = df_gold.join(df_condition, df_gold.patient_uuid == df_condition.patient_uuid_cond, how="left")
df_gold = df_gold.join(df_observation, df_gold.patient_uuid == df_observation.patient_uuid_obs, how="left")

# -----------------------------
# 📌 Sélection finale colonnes GOLD
# -----------------------------
df_gold_final = df_gold.select(
    "patient_uuid",
    "source_patient_id",
    "name",
    "gender",
    "birth_date",
    "age",
    "age_tranche",
    "encounter_id",
    "admission_date",
    "discharge_date",
    "visit_type",
    "diagnosis_code",
    "category",
    "diagnosis",
    "mortality",
    "parity",
    "gravida",
    "live_births"
).dropDuplicates(["patient_uuid", "encounter_id", "diagnosis_code"])

# -----------------------------
# 📝 ÉCRITURE TABLE GOLD
# -----------------------------
df_gold_final.write.mode("overwrite").saveAsTable(GOLD_TABLE)
logging.info(f"🎯 Table GOLD créée : {GOLD_TABLE}")

# -----------------------------
# 🪪 CONSENTEMENT (GOLD)
# -----------------------------
def charger_consent_gold():
    """Alimente patient_consent_gold à partir du SILVER patient et de PostgreSQL."""
    df_patient = spark.table(f"{HIVE_SILVER}.patient_fhir").select(
        "patient_uuid", "master_patient_id", "name"
    ).filter(F.col("master_patient_id").isNotNull()) \
     .dropDuplicates(["master_patient_id"])

    consent_rows, consent_source = [], ""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        try:
            import psycopg
            with psycopg.connect(db_url) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT master_patient_id, purpose, granted, recorded_at::text "
                        "FROM consent ORDER BY master_patient_id"
                    )
                    consent_rows = cur.fetchall()
            consent_source = "postgres"
            logging.info(f"🪪 Consent PostgreSQL : {len(consent_rows)} enregistrements.")
        except Exception as e:
            logging.warning(f"Consent PostgreSQL inaccessible ({e}) — consent vide, mock API.")
    else:
        logging.info("DATABASE_URL absente — consent non alimenté depuis PostgreSQL.")

    if consent_rows:
        df_consent = spark.createDataFrame(
            consent_rows, ["master_patient_id", "purpose", "granted", "recorded_at"]
        )
    else:
        df_consent = df_patient.select(
            F.col("master_patient_id"),
            F.lit(None).cast(StringType()).alias("purpose"),
            F.lit(None).cast(BooleanType()).alias("granted"),
            F.lit(None).cast(StringType()).alias("recorded_at"),
        )
        logging.info("Consent vide — schéma créé, API en fallback mock.")

    df_consent = df_consent.join(
        df_patient.select("master_patient_id", "patient_uuid", "name"),
        on="master_patient_id",
        how="left",
    ).select(
        "master_patient_id", "patient_uuid", "name", "purpose", "granted", "recorded_at"
    )

    df_consent.write.mode("overwrite").saveAsTable(CONSENT_GOLD_TABLE)
    logging.info(f"🪪 Table GOLD consent créée : {CONSENT_GOLD_TABLE} "
                 f"({df_consent.count()} lignes, source={consent_source or 'vide'})")

charger_consent_gold()

update_sync_metadata("GOLD", status="ok")
logging.info(f"🎯 Table GOLD créée : {GOLD_TABLE}")

spark.stop()
logging.info("✅ create_gold.py terminé")

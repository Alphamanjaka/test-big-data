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

# -----------------------------
# 🔧 CONFIGURATION
# -----------------------------
SILVER_HIVE_DB = "datalake_silver"
GOLD_HIVE_DB = "datalake_gold"
GOLD_TABLE = f"{GOLD_HIVE_DB}.patient_events_gold"
CONSENT_GOLD_TABLE = f"{GOLD_HIVE_DB}.patient_consent_gold"

# Tranches d'âge spécifiques pour le dashboard
AGE_TRANCHES = [
    (0, 28/365, "0-28 j"),         # nouveau-nés < 28 jours
    (29/365, 59/365, "29-59 j"),   # 29-59 jours
    (2/12, 11/12, "2-11 m"),       # 2-11 mois
    (1, 4, "1-4 ans"),             # 1-4 ans
    (5, 14, "5-14 ans"),           # 5-14 ans
    (15, 24, "15-24 ans"),         # 15-24 ans
    (25, 59, "25-59 ans"),         # 25-59 ans
    (60, 120, "60 ans et plus")    # 60 ans et plus
]

# -----------------------------
# 🔧 LOGGING (makedirs AVANT basicConfig)
# -----------------------------
LOG_DIR = "/home/vagrant/datalake-final/provision/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "create_gold.log")

# -----------------------------
# 🔧 LOGGING
# -----------------------------
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
    .config("spark.sql.warehouse.dir", "hdfs://localhost:9000/datalake/gold/warehouse") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .enableHiveSupport() \
    .getOrCreate()

spark.sql(f"CREATE DATABASE IF NOT EXISTS {GOLD_HIVE_DB}")
logging.info(f"✅ Base GOLD {GOLD_HIVE_DB} vérifiée")

# -----------------------------
# 📥 LECTURE DES TABLES SILVER
# Tolérance aux entités absentes (mode patients-only) : les tables d'événements
# manquantes sont remplacées par un DataFrame vide au schéma attendu, afin que
# le GOLD reste stable (démarrage en douceur du dashboard/API).
# -----------------------------
from pyspark.sql.types import StructType, StructField

def _lire_silver(table):
    try:
        df = spark.table(table)
        logging.info(f"✅ Table SILVER chargée : {table} ({df.count()} lignes)")
        return df
    except Exception as e:
        logging.warning(f"⚠️ Table SILVER absente ({table}) — remplacée par une table vide. ({e})")
        return None

def _vide(colonnes):
    schema = StructType([StructField(c, StringType(), True) for c in colonnes])
    return spark.createDataFrame([], schema)

df_patient = _lire_silver(f"{SILVER_HIVE_DB}.patient_fhir")
df_encounter = _lire_silver(f"{SILVER_HIVE_DB}.encounter_fhir")
df_condition = _lire_silver(f"{SILVER_HIVE_DB}.condition_fhir")
df_observation = _lire_silver(f"{SILVER_HIVE_DB}.observation_fhir")
if df_patient is None:
    logging.error("patient_fhir absente — GOLD impossible.")
    raise SystemExit(1)

# -----------------------------
# 🎯 RÉDUCTION AUX COLONNES UTILES
# (évite AMBIGUOUS_REFERENCE : `name` existe dans Patient ET Condition)
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
# Calcul âge en années fractionnaires
df_patient = df_patient.withColumn(
    "birth_date", F.to_date(F.col("birth_date"))
)
df_patient = df_patient.withColumn(
    "age", F.datediff(F.current_date(), F.col("birth_date")) / 365.25
)

# Fonction pour assigner la tranche d'âge
def assign_age_tranche(age):
    if age is None:
        return "unknown"
    for min_age, max_age, label in AGE_TRANCHES:
        if min_age <= age <= max_age:
            return label
    return "unknown"

# UDF Spark
udf_age_tranche = F.udf(assign_age_tranche, StringType())
df_patient = df_patient.withColumn("age_tranche", udf_age_tranche(F.col("age")))

# -----------------------------
# 🔗 JOINTURES PATIENT ↔ ENTITÉS
# -----------------------------
# Convertir dates des encounters
df_encounter = df_encounter.withColumn("admission_date", F.to_date(F.col("admission_date")))
df_encounter = df_encounter.withColumn("discharge_date", F.to_date(F.col("discharge_date")))

# Jointure Encounter + Patient
df_gold = df_encounter.join(df_patient, on="patient_uuid", how="left")

# Jointure Condition + Patient
df_gold = df_gold.join(df_condition, df_gold.patient_uuid == df_condition.patient_uuid_cond, how="left")

# Jointure Observation + Patient
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
# 🪪 CONSENTEMENT (GOLD) — reflète la gouvernance purpose-by-purpose
# -----------------------------
def charger_consent_gold():
    """
    Alimente patient_consent_gold à partir du SILVER patient (master_patient_id
    produit par le moteur) et de la table consent du PostgreSQL central
    (engine/governance). Si le PostgreSQL central n'est pas joignable, la table
    est créée quand même (schéma stable) afin que l'API bascule proprement.
    """
    df_patient = spark.table(f"{SILVER_HIVE_DB}.patient_fhir").select(
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

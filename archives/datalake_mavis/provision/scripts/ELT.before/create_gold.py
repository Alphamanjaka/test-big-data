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
from pyspark.sql.types import StringType

from ..utils.sync_utils import update_sync_metadata

# -----------------------------
# 🔧 CONFIGURATION
# -----------------------------
LOG_DIR = "/home/vagrant/datalake-mavis/provision/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "create_gold.log")

SILVER_HIVE_DB = "datalake_silver"
GOLD_HIVE_DB = "datalake_gold"
GOLD_TABLE = f"{GOLD_HIVE_DB}.patient_events_gold"

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
    .enableHiveSupport() \
    .getOrCreate()

spark.sql(f"CREATE DATABASE IF NOT EXISTS {GOLD_HIVE_DB}")
logging.info(f"✅ Base GOLD {GOLD_HIVE_DB} vérifiée")

# -----------------------------
# 📥 LECTURE DES TABLES SILVER
# -----------------------------
try:
    df_patient = spark.table(f"{SILVER_HIVE_DB}.patient_fhir")
    df_encounter = spark.table(f"{SILVER_HIVE_DB}.encounter_fhir")
    df_condition = spark.table(f"{SILVER_HIVE_DB}.condition_fhir")
    df_observation = spark.table(f"{SILVER_HIVE_DB}.observation_fhir")
    logging.info("✅ Tables SILVER chargées")
except Exception as e:
    logging.error(f"Erreur lecture tables SILVER : {e}")
    raise

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
df_condition = df_condition.withColumnRenamed("patient_uuid", "patient_uuid_cond")
df_gold = df_gold.join(df_condition, df_gold.patient_uuid == df_condition.patient_uuid_cond, how="left")

# Jointure Observation + Patient
df_observation = df_observation.withColumnRenamed("patient_uuid", "patient_uuid_obs")
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
update_sync_metadata("GOLD", status="ok")
logging.info(f"🎯 Table GOLD créée : {GOLD_TABLE}")

spark.stop()
logging.info("✅ create_gold.py terminé")

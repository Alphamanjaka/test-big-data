#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_silver.py
==================
Transformation des données de la Zone RAW vers la Zone SILVER (modèle FHIR harmonisé)
Patient UUID généré uniquement pour Patient et propagé aux entités enfants.
"""

import json
import os
import logging
from typing import List
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StringType, IntegerType, DoubleType, DateType
from ..utils.fhir_schema import FHIR_FIELDS
from ..utils.sync_utils import update_sync_metadata
from pyspark.sql import DataFrame

try:
    from rapidfuzz import fuzz
    from sentence_transformers import SentenceTransformer, util as st_util
    ST_AVAILABLE = True
except Exception:
    fuzz = None
    SentenceTransformer = None
    st_util = None
    ST_AVAILABLE = False

from difflib import SequenceMatcher
import heapq

# Seuils / paramètres
FUZZY_THRESHOLD = 60            # ton seuil fuzzy existant (0-100)
SEMANTIC_THRESHOLD = 0.65      # seuil cos_sim (0..1) pour accepter match sémantique
CANDIDATE_TOP_N = 6            # nombre maximal de candidats fuzzy à tester sémantiquement

# -----------------------------
# CONFIGURATION
# -----------------------------
MAPPING_PATH = "/home/vagrant/datalake-mavis/provision/metadata/fhir_mapping.json"
LOG_DIR = "/home/vagrant/datalake-mavis/provision/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "create_silver.log")
SILVER_HIVE_DB = "datalake_silver"
RAW_PARQUET_BASE = "/datalake/raw"
FUZZY_THRESHOLD = 60
COLONNES_EXCLUES = ["write_date", "create_date", "create_uid", "write_uid"]

# -----------------------------
# LOGGING
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

# -----------------------------
# INITIALISATION SPARK
# -----------------------------
spark = SparkSession.builder \
    .appName("create_silver") \
    .config("spark.sql.parquet.binaryAsString", "true") \
    .config("spark.sql.parquet.enableVectorizedReader", "false") \
    .config("spark.sql.warehouse.dir", "hdfs://localhost:9000/datalake/silver/warehouse") \
    .enableHiveSupport() \
    .getOrCreate()

spark.sql(f"CREATE DATABASE IF NOT EXISTS {SILVER_HIVE_DB}")
logging.info("✅ Spark initialisé et base Hive Silver vérifiée")

# -----------------------------
# Lecture mapping FHIR
# -----------------------------
with open(MAPPING_PATH) as f:
    fhir_mapping = json.load(f)
logging.info("✅ Mapping FHIR chargé")

SYNONYMES_COURTS = {
    "birth_date": ["dob", "bdate", "birthday"],
    "phone": ["tel", "telephone", "mobile"],
    "email": ["mail"],
    "gender": ["sex"],
    "source_patient_id": ["id", "patient_id", "id_patient"]
}

CLES_CANDIDATES = ["patient_id", "id", "id_patient", "source_patient_id"]

# -----------------------------
# Fonctions utilitaires
# -----------------------------
def fuzzy_score(a: str, b: str) -> int:
    a, b = (a or "").lower(), (b or "").lower()
    if fuzz:
        try:
            return int(fuzz.token_sort_ratio(a, b))
        except Exception:
            pass
    # fallback simple
    if a == b:
        return 100
    if a in b or b in a:
        return 80
    # ratio basique difflib

def meilleure_colonne_attendue(champ_fhir: str, candidates: List[str], champ_type: str = "string", fk_cols: List[str] = None, df=None) -> str:
    champ = champ_fhir.lower()
    fk_cols = fk_cols or []
    candidates = [c for c in candidates if c.lower() not in [e.lower() for e in fk_cols + COLONNES_EXCLUES]]

    # 🔹 Filtrer par type Spark
    if df is not None:
        type_map = {
            "string": ["string"],
            "int": ["int", "bigint", "long", "smallint"],
            "double": ["double", "float", "decimal"],
            "date": ["date", "timestamp"]
        }
        allowed_types = type_map.get(champ_type, [])
        candidates = [
            c for c in candidates
            if df.schema[c].dataType.simpleString().lower() in allowed_types
        ]

    for syn in SYNONYMES_COURTS.get(champ, []):
        for c in candidates:
            if c.lower() == syn.lower():
                return c
    for c in candidates:
        if c.lower() == champ:
            return c

    meilleure, meilleur_score = None, -1
    for c in candidates:
        score = fuzzy_score(c, champ)
        if score > meilleur_score:
            meilleur_score = score
            meilleure = c
    return meilleure if meilleur_score >= FUZZY_THRESHOLD else None

def detecter_cle_primaire(df):
    cols = [c.lower() for c in df.columns]
    for cle in CLES_CANDIDATES: 
        if cle in cols:
            return [c for c in df.columns if c.lower() == cle][0]
    return df.columns[0] if df.columns else None

def lire_table(source: str, nom_table: str):
    logging.info(f"***************************Lecture de la table {nom_table} pour la source {source}")
    candidats = [
        f"{source}.{nom_table}",
        nom_table,
        f"{RAW_PARQUET_BASE}/{source}/{nom_table}.parquet"
    ]
    last_error = None
    for c in candidats:
        try:
            if c.endswith(".parquet") or os.path.isdir(c):
                df = spark.read.option("mergeSchema", "true").option("parquet.binaryAsString", "true").parquet(c)
                return df
            else:
                return spark.table(c)
        except Exception as e:
            last_error = e
            continue
    raise FileNotFoundError(f"❌ Table {nom_table} introuvable pour la source {source}. Last error: {last_error}")

def dynamic_cast(df, entite):
    logging.info(f"Application du schéma FHIR pour l’entité {entite}")
    for champ, typ in FHIR_FIELDS.get(entite, {}).items():
        logging.info(f" ----------------------------- Traitement du champ {champ} de type {typ}")
        col_name = f"fhir__{champ}"
        if col_name in df.columns:
            if typ == "date":
                df = df.withColumn(col_name, F.to_date(F.col(col_name)))
            elif typ == "int":
                df = df.withColumn(col_name, F.col(col_name).cast(IntegerType()))
            elif typ in ["double", "float", "decimal"]:
                df = df.withColumn(col_name, F.col(col_name).cast(DoubleType()))
            else:
                df = df.withColumn(col_name, F.col(col_name).cast(StringType()))
        else:
            if typ == "date":
                df = df.withColumn(col_name, F.lit(None).cast(DateType()))
            elif typ == "int":
                df = df.withColumn(col_name, F.lit(None).cast(IntegerType()))
            elif typ in ["double", "float", "decimal"]:
                df = df.withColumn(col_name, F.lit(None).cast(DoubleType()))
            else:
                df = df.withColumn(col_name, F.lit(None).cast(StringType()))
    return df

def dynamic_join(df_entite: DataFrame, df_sel: DataFrame, table_name: str = "") -> DataFrame:
    """
    Fusionne df_sel dans df_entite en détectant dynamiquement la clé de jointure.
    Évite toutes les ambiguïtés Spark (dans df_entite et df_sel).
    """

    logging.info(f"🔄 Fusion dynamique de la table '{table_name}', et df_entite'{df_entite}'")
    if df_entite is None:
        logging.info(f"⚡ Initialisation avec la table '{table_name}'")
        return df_sel

    # 🧹 Étape 1 — nettoyer les doublons internes de df_entite
    cols = df_entite.columns
    if len(cols) != len(set(cols)):
        seen = set()
        new_cols = []
        for c in cols:
            if c in seen:
                new_name = f"{c}_entite_dup"
                logging.warning(f"Renommage colonne dupliquée dans df_entite : {c} -> {new_name}")
                new_cols.append(F.col(c).alias(new_name))
            else:
                new_cols.append(F.col(c))
                seen.add(c)
        df_entite = df_entite.select(*new_cols)

    # Colonnes communes
    common_cols = set(df_entite.columns) & set(df_sel.columns)

    # 🧩 Étape 2 — renommer les doublons dans df_sel
    if common_cols:
        key_candidates = {"id", "patient_id", "source_patient_id", "fhir__source_patient_id"}
        rename_map = {}
        for c in common_cols:
            if c not in key_candidates:
                rename_map[c] = f"{c}_{table_name}_dup"
        if rename_map:
            logging.info(f"🧩 Renommage des colonnes dupliquées avant détection clé: {rename_map}")
            for old, new in rename_map.items():
                df_sel = df_sel.withColumnRenamed(old, new)
        common_cols = set(df_entite.columns) & set(df_sel.columns)

    if not common_cols:
        logging.info(f"⬆️ Pas de colonnes communes entre df_entite et '{table_name}' — unionByName()")
        return df_entite.unionByName(df_sel, allowMissingColumns=True)

    # -----------------------
    # Étape 3 — Détection automatique de la meilleure clé
    # -----------------------
    best_col = None
    max_matches = 0
    sample_size = 1000

    for col_name in common_cols:
        try:
            df1_vals = set(row[col_name] for row in df_entite.select(col_name).limit(sample_size).collect())
            df2_vals = set(row[col_name] for row in df_sel.select(col_name).limit(sample_size).collect())
            matches = len(df1_vals & df2_vals)
            if matches > max_matches:
                max_matches = matches
                best_col = col_name
        except Exception as e:
            logging.debug(f"Ignoring {col_name} during key detection: {e}")
            continue

    MIN_MATCHES = 2
    if best_col and max_matches >= MIN_MATCHES:
        logging.info(f"🔗 Jointure sur '{best_col}' ({max_matches} valeurs communes) entre df_entite et '{table_name}'")

        # 🧹 Supprimer les doublons restants sauf clé
        duplicate_cols = [c for c in df_entite.columns if c in df_sel.columns and c != best_col]
        if duplicate_cols:
            logging.info(f"🧹 Suppression des colonnes dupliquées avant jointure : {duplicate_cols}")
            df_sel = df_sel.drop(*duplicate_cols)

        return df_entite.join(df_sel, on=best_col, how="left")

    else:
        logging.info(f"⬆️ Pas de clé fiable détectée pour '{table_name}' — unionByName()")
        return df_entite.unionByName(df_sel, allowMissingColumns=True)

# -----------------------------
# Boucle principale sur les sources et entités
# -----------------------------
for source, entites in fhir_mapping.items():
    logging.info(f"--- Source : {source}")
    for entite, tables in entites.items():
        logging.info(f"Traitement de l’entité FHIR : {entite}")
        champs_fhir = list(FHIR_FIELDS.get(entite, {}).keys())
        df_entite = None

        for nom_table, colonnes in (tables or {}).items():
            try:
                df = lire_table(source, nom_table)
            except FileNotFoundError:
                logging.warning(f"⚠️ Table {nom_table} non trouvée — ignorée.")
                continue

            mapping_local = {
                champ: meilleure_colonne_attendue(champ, df.columns, FHIR_FIELDS[entite].get(champ, "string"), df=df)
                for champ in champs_fhir
                if meilleure_colonne_attendue(champ, df.columns, FHIR_FIELDS[entite].get(champ, "string"), df=df)
            }

            if not mapping_local:
                logging.warning(f"⚠️ Aucun mapping trouvé pour {nom_table} — table ignorée.")
                continue

            pk = detecter_cle_primaire(df)
            if entite == "Patient" and "source_patient_id" not in mapping_local:
                mapping_local["source_patient_id"] = pk

            colonnes_a_lire = list(set(mapping_local.values()))
            if pk and pk not in colonnes_a_lire:
                colonnes_a_lire.append(pk)
            try:
                df_sel = df.select(*colonnes_a_lire)
            except Exception:
                existantes = [c for c in colonnes_a_lire if c in df.columns]
                df_sel = df.select(*existantes)

            for champ, col_src in mapping_local.items():
                if col_src in df_sel.columns:
                    df_sel = df_sel.withColumnRenamed(col_src, f"fhir__{champ}")
            df_sel = df_sel.withColumn("_source_table", F.lit(nom_table))
            df_sel = dynamic_cast(df_sel, entite)

            logging.info(f"🧩 Ajout des données de la table '{nom_table}' à l’entité '{entite}'")
            if df_entite is None:
                df_entite = df_sel
            else:
                df_entite = dynamic_join(df_entite, df_sel, table_name=entite)

        if df_entite is None:
            logging.info(f"Aucune donnée trouvée pour {entite} dans {source}")
            continue

        # 🧩 Ajout du préfixe du nom de la source au source_patient_id
        if "fhir__source_patient_id" in df_entite.columns:
            logging.info(f"Ajout du nom de la source '{source}' dans fhir__source_patient_id")
            df_entite = df_entite.withColumn(
                "fhir__source_patient_id",
                F.concat_ws("_", F.lit(source), F.col("fhir__source_patient_id"))
            )
            
        # -----------------------------
        # Patient UUID pour Patient uniquement
        # -----------------------------
        if entite == "Patient" and "fhir__source_patient_id" in df_entite.columns:
            df_entite = df_entite.withColumn(
                "fhir__patient_uuid",
                F.expr(f"sha2(concat('{source}', '|', cast(fhir__source_patient_id as string)), 256)")
            )

        # -----------------------------
        # Propagation patient_uuid vers enfants
        # -----------------------------
        if entite in ["Encounter", "Condition", "Observation"]:
            patient_id_col = next((c for c in df_entite.columns if c.lower() in ["patient_id", "source_patient_id", "id_patient"]), None)
            if patient_id_col:
                df_patient = spark.table(f"{SILVER_HIVE_DB}.patient_fhir").select("fhir__patient_uuid", "fhir__source_patient_id")
                df_entite = df_entite.join(
                    df_patient,
                    df_entite[patient_id_col] == df_patient["fhir__source_patient_id"],
                    how="left"
                ).drop("fhir__source_patient_id")
                df_entite = df_entite.withColumnRenamed("fhir__patient_uuid", "patient_uuid")
                logging.info(f"Propagation de patient_uuid vers {entite} effectuée")
            else:
                logging.warning(f"⚠️ Aucun patient_id trouvé pour {entite} dans {source}. patient_uuid non propagé")

        # Sélection finale et écriture
        colonnes_finales = [F.col(f"fhir__{c}").alias(c) for c in champs_fhir]
        if "_source_table" in df_entite.columns:
            colonnes_finales.append(F.col("_source_table"))
        if entite != "Patient" and "patient_uuid" in df_entite.columns:
            colonnes_finales.append(F.col("patient_uuid"))

        df_final = df_entite.select(*colonnes_finales).dropDuplicates()
        table_cible = f"{SILVER_HIVE_DB}.{entite.lower()}_fhir"
        # --- Vérification d’existence de la table (compatible toutes versions) ---
        db_name, tbl_name = table_cible.split(".")
        table_exists = any(t.name == tbl_name and t.database == db_name for t in spark.catalog.listTables(db_name))
        if table_exists:
            df_final.write.mode("append").insertInto(table_cible, overwrite=False)
        else:
            df_final.write.mode("overwrite").saveAsTable(table_cible)
        update_sync_metadata("SILVER", status="ok")
        logging.info(f"📤 Table SILVER {table_cible} écrite avec succès")

logging.info("🎯 Transformation Silver (FHIR) terminée")
spark.stop()

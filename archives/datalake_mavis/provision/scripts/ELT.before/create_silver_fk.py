#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_silver_fk.py
===================
Pipeline RAW → SILVER harmonisé FHIR avec FK automatique et insertInto Hive sécurisé
"""

import json, os, logging
from datetime import datetime
from typing import List, Dict
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StringType, IntegerType, DoubleType, DateType
from pyspark.sql import DataFrame

from ..utils.fhir_schema import FHIR_FIELDS
from ..utils.sync_utils import update_sync_metadata

try:
    from rapidfuzz import fuzz
    from sentence_transformers import SentenceTransformer, util as st_util
    ST_AVAILABLE = True
except Exception:
    fuzz = None
    SentenceTransformer = None
    st_util = None
    ST_AVAILABLE = False

# -----------------------------
# CONFIG
# -----------------------------
DATASOURCES_PATH = "/home/vagrant/datalake-mavis/provision/config/data_sources.json"
MAPPING_PATH = "/home/vagrant/datalake-mavis/provision/metadata/fhir_mapping.json"
EXTRACT_RAW_PATH = "/home/vagrant/datalake-mavis/provision/metadata/extract_raw_report.json"
LOG_DIR = "/home/vagrant/datalake-mavis/provision/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "create_silver_fk.log")

SILVER_HIVE_DB = "datalake_silver"
RAW_PARQUET_BASE = "/datalake/raw"
COLONNES_EXCLUES = ["write_date", "create_date", "create_uid", "write_uid"]
CLES_CANDIDATES = ["patient_id", "id", "id_patient", "source_patient_id"]

# Seuils / paramètres
FUZZY_THRESHOLD = 60            # ton seuil fuzzy existant (0-100)
SEMANTIC_THRESHOLD = 0.65      # seuil cos_sim (0..1) pour accepter match sémantique
CANDIDATE_TOP_N = 6            # nombre maximal de candidats fuzzy à tester sémantiquement

SYNONYMES_COURTS = {
    "birth_date": ["dob", "bdate", "birthday"],
    "phone": ["tel", "telephone", "mobile"],
    "email": ["mail"],
    "gender": ["sex"],
    "source_patient_id": ["id", "patient_id", "id_patient"]
}

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
# SPARK INIT
# -----------------------------
spark = SparkSession.builder \
    .appName("create_silver_fk") \
    .config("spark.sql.parquet.binaryAsString", "true") \
    .config("spark.sql.parquet.enableVectorizedReader", "false") \
    .config("spark.sql.warehouse.dir", f"hdfs://localhost:9000/datalake/silver/warehouse") \
    .enableHiveSupport() \
    .getOrCreate()
spark.sql(f"CREATE DATABASE IF NOT EXISTS {SILVER_HIVE_DB}")
logging.info("✅ Spark initialisé et base Hive Silver vérifiée")

# -----------------------------
# LOAD FHIR MAPPING ET EXTRACT_RAW
# -----------------------------
with open(MAPPING_PATH) as f:
    fhir_mapping: Dict = json.load(f)
with open(EXTRACT_RAW_PATH) as f:
    extract_raw: Dict = json.load(f)
logging.info("✅ Mapping FHIR et extract_raw.json chargés")
print(extract_raw["MAVIS"])

# Construire fk_map[source][table] = {col: fk_table}
fk_map = {}
for source_name, tables_meta in extract_raw.items():
    fk_map[source_name] = {}
    for tbl in tables_meta:
        col_fk = {col['name']: col['fk'] for col in tbl.get('columns', []) if 'fk' in col}
        fk_map[source_name][tbl['table_name']] = col_fk

# -----------------------------
# UTILS
# -----------------------------
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
    
def detecter_cle_primaire(df: DataFrame) -> str:
    cols = [c.lower() for c in df.columns]
    for cle in CLES_CANDIDATES:
        if cle in cols:
            return [c for c in df.columns if c.lower() == cle][0]
    return df.columns[0] if df.columns else None

def lire_table(source: str, nom_table: str) -> DataFrame:
    candidats = [
        f"{source}.{nom_table}",
        nom_table,
        f"{RAW_PARQUET_BASE}/{source}/{nom_table}.parquet"
    ]
    last_error = None
    for c in candidats:
        try:
            if c.endswith(".parquet") or os.path.isdir(c):
                df = spark.read.option("mergeSchema", "true").parquet(c)
                return df
            else:
                return spark.table(c)
        except Exception as e:
            last_error = e
            continue
    raise FileNotFoundError(f"❌ Table {nom_table} introuvable pour la source {source}. Last error: {last_error}")

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

def resolve_via_fk(source: str, df_src: DataFrame, col_fk: str, fk_def: str, champ_fhir: str):
    """
    Résout une colonne manquante (ex: email) via FK. Ajoute un suffixe pour éviter 
    les colonnes dupliquées dans df_src.
    """
    if "." in fk_def:
        fk_table, fk_col = fk_def.split(".", 1)
    else:
        fk_table, fk_col = fk_def, "id"

    try:
        df_fk = lire_table(source, fk_table)
    except FileNotFoundError as e:
        # logging.warning(f"⚠️ Impossible de résoudre {champ_fhir} via FK {fk_def}: {e}")
        return df_src

    if fk_col not in df_fk.columns:
        logging.warning(f"⚠️ Colonne {fk_col} inexistante dans {fk_table} pour FK {col_fk}")
        return df_src

    cible_col = meilleure_colonne_attendue(
        champ_fhir, 
        df_fk.columns, 
        FHIR_FIELDS["Patient"].get(champ_fhir, "string"), 
        df=df_fk
    )
    if not cible_col:
        logging.warning(f"⚠️ Aucune colonne correspondante à {champ_fhir} trouvée dans {fk_table}")
        return df_src

    alias_col = f"fhir__{champ_fhir}_{fk_table}"  # ⚡ suffixe unique
    logging.info(f"🔗 Résolution {champ_fhir} via FK {col_fk} → {fk_table}.{cible_col} (alias {alias_col})")

    try:
        df_src = df_src.join(
            df_fk.select(F.col(fk_col).alias(col_fk), F.col(cible_col).alias(alias_col)),
            on=col_fk,
            how="left"
        )
    except Exception as e:
        logging.warning(f"⚠️ Échec de la jointure FK {col_fk}→{fk_table}.{fk_col} pour {champ_fhir}: {e}")

    return df_src

def dynamic_join(df_entite: DataFrame, df_sel: DataFrame, table_name: str = "") -> DataFrame:
    """
    Joint df_sel à df_entite en évitant les colonnes dupliquées.
    """
    if df_entite is None:
        return df_sel

    # Colonnes communes
    common_cols = set(df_entite.columns) & set(df_sel.columns)
    key_candidates = {"id", "patient_id", "source_patient_id", "fhir__source_patient_id"}
    best_key = next((c for c in key_candidates if c in common_cols), None)

    if best_key:
        # On supprime les colonnes communes sauf la clé
        cols_to_drop = [c for c in common_cols if c != best_key]
        df_sel = df_sel.drop(*cols_to_drop)

        # ⚡ On renomme les colonnes restantes en suffixant pour éviter ambiguïté
        for c in df_sel.columns:
            if c != best_key and c in df_entite.columns:
                df_sel = df_sel.withColumnRenamed(c, f"{c}_dup")

        return df_entite.join(df_sel, on=best_key, how="outer")

    # Si pas de clé, union en autorisant colonnes manquantes
    return df_entite.unionByName(df_sel, allowMissingColumns=True)

def dynamic_cast(df: DataFrame, entite: str) -> DataFrame:
    for champ, typ in FHIR_FIELDS.get(entite, {}).items():
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

# -----------------------------
# MAIN LOOP
# -----------------------------
for source, entites in fhir_mapping.items():
    logging.info(f"--- Source : {source}")
    for entite, tables in entites.items():
        logging.info(f"Traitement entité FHIR : {entite}")
        champs_fhir = list(FHIR_FIELDS.get(entite, {}).keys())
        df_entite = None

        for nom_table, colonnes in (tables or {}).items():
            try:
                df = lire_table(source, nom_table)
            except FileNotFoundError:
                logging.warning(f"⚠️ Table {nom_table} introuvable — ignorée")
                continue

            mapping_local = {champ: champ for champ in df.columns if champ not in COLONNES_EXCLUES}
            df_sel = df.select(*df.columns)

            extract_tables = [t for t in extract_raw.get(source, []) if t["table_name"] == nom_table]

            for champ in champs_fhir:
                if f"fhir__{champ}" not in df_sel.columns:
                    for tdef in extract_tables:
                        for col_meta in tdef["columns"]:
                            if "fk" in col_meta:
                                df_sel = resolve_via_fk(
                                    source=source,
                                    df_src=df_sel,
                                    col_fk=col_meta["name"],
                                    fk_def=col_meta["fk"],
                                    champ_fhir=champ
                                )

            df_sel = dynamic_cast(df_sel, entite)
            df_entite = dynamic_join(df_entite, df_sel, table_name=entite)

        if df_entite is None:
            logging.info(f"Aucune donnée trouvée pour {entite} dans {source}")
            continue

        # Préfixe source + source_patient_id
        if "fhir__source_patient_id" in df_entite.columns:
            df_entite = df_entite.withColumn(
                "fhir__source_patient_id",
                F.concat_ws("_", F.lit(source), F.col("fhir__source_patient_id"))
            )

        # Patient UUID
        if entite == "Patient" and "fhir__source_patient_id" in df_entite.columns:
            df_entite = df_entite.withColumn(
                "fhir__patient_uuid",
                F.expr(f"sha2(concat('{source}','|',cast(fhir__source_patient_id as string)),256)")
            )

        # Propagation UUID vers enfants
        if entite in ["Encounter", "Condition", "Observation", "Procedure"]:
            patient_id_col = next((c for c in df_entite.columns if "patient_id" in c.lower()), None)
            if patient_id_col:
                try:
                    df_patient = spark.table(f"{SILVER_HIVE_DB}.patient_fhir").select(
                        "fhir__patient_uuid", "fhir__source_patient_id"
                    )
                    df_entite = df_entite.join(
                        df_patient,
                        df_entite[patient_id_col] == df_patient["fhir__source_patient_id"],
                        how="left"
                    ).withColumnRenamed("fhir__patient_uuid", "patient_uuid")
                    logging.info(f"Propagation patient_uuid vers {entite} OK")
                except Exception as e:
                    logging.warning(f"⚠️ Échec propagation UUID pour {entite}: {e}")

        # -----------------------------
        # Insertion minimale patient_fhir
        # -----------------------------
        table_cible = f"{SILVER_HIVE_DB}.patient_fhir"
        db_name, tbl_name = table_cible.split(".")
        try:
            hive_cols = [t.name for t in spark.catalog.listColumns(db_name, tbl_name)]
        except Exception:
            hive_cols = []

        # Créer df_final avec toutes les colonnes Hive
        df_final = df_entite.select(
            F.col("fhir__source_patient_id")  # seule colonne réelle pour le moment
        ).dropDuplicates()

        # Générer patient_uuid à partir de source_patient_id
        df_final = df_final.withColumn(
            "patient_uuid",
            F.expr("sha2(fhir__source_patient_id, 256)")
        )

        # Ajouter toutes les colonnes manquantes avec null
        for col in hive_cols:
            if col not in df_final.columns:
                df_final = df_final.withColumn(col, F.lit(None))

        # Réordonner selon Hive
        df_final = df_final.select(*hive_cols)

        # Écriture Hive
        table_exists = any(t.name == tbl_name and t.database == db_name for t in spark.catalog.listTables(db_name))
        if table_exists:
            logging.info(f"⬆️ Table existante détectée, insertion minimale: {table_cible}")
            df_final.write.mode("append").insertInto(table_cible)
        else:
            logging.info(f"📤 Table inexistante, création et écriture minimale: {table_cible}")
            df_final.write.mode("overwrite").saveAsTable(table_cible)

        logging.info(f"✅ Insertion minimale terminée pour {table_cible}")

        update_sync_metadata("SILVER", status="ok")
        logging.info(f"✅ Table SILVER {table_cible} écrite avec succès")

logging.info("🎯 Transformation Silver (FHIR) terminée")
spark.stop()

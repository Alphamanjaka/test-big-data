#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
create_silver.py
================
Transformation des données de la Zone RAW vers la Zone SILVER (modèle FHIR harmonisé)

MVP Module 1 :
  - Normalisation des valeurs (gender via GENDER_MAP)
  - Identification des doublons patients (is_duplicate, sans fusion)
  - Idempotence (écriture en mode overwrite) et traçabilité (_source_table)
"""

import json
import os
import sys
import logging
from typing import List
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import StringType, IntegerType, DoubleType, DateType
from pyspark.sql.window import Window
from ..utils.fhir_schema import FHIR_FIELDS
from ..utils.sync_utils import update_sync_metadata

# Optionnel : RapidFuzz pour similarité (libre et open-source)
try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

# -----------------------------
# 🔧 CONFIGURATION GLOBALE
# -----------------------------
DATASOURCES_PATH = "/home/vagrant/datalake-final/provision/config/data_sources.json"
MAPPING_PATH = "/home/vagrant/datalake-final/provision/metadata/fhir_mapping.json"
LOG_DIR = "/home/vagrant/datalake-final/provision/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "gen_fhir_silver.log")

# Nom de la base Hive pour la zone Silver
SILVER_HIVE_DB = "datalake_silver"

# Dossier des fichiers RAW (si les tables ne sont pas dans Hive)
RAW_PARQUET_BASE = "/datalake/raw"

# Seuil minimal de similarité pour fuzzy matching (0 à 100)
FUZZY_THRESHOLD = 60

# Moteur de déduplication explicable (dossier engine du repo code-source)
ENGINE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "engine")
if ENGINE_PATH not in sys.path:
    sys.path.insert(0, ENGINE_PATH)

# -----------------------------
# 🎚️ NORMALISATION DES VALEURS (MVP Étape 1)
# -----------------------------
# Dictionnaire de mapping : valeur source (minuscule) -> valeur normalisée FHIR
GENDER_MAP = {
    "m": "male", "h": "male", "homme": "male", "male": "male",
    "f": "female", "femme": "female", "female": "female",
}

def normaliser_gender(df):
    """
    Normalise la colonne 'gender' vers les valeurs FHIR (male/female).
    Les valeurs inconnues sont conservées (en minuscule) plutôt que perdues.
    """
    if "gender" not in df.columns:
        return df
    col_clean = F.lower(F.trim(F.col("gender")))
    expr = col_clean
    for src, dst in GENDER_MAP.items():
        expr = F.when(col_clean == src, F.lit(dst)).otherwise(expr)
    logging.info("🎚️ Normalisation de la colonne gender appliquée")
    return df.withColumn("gender", expr)

# -----------------------------
# 👥 DÉTECTION DES DOUBLONS PATIENT (MVP Étape 2)
# -----------------------------
def marquer_doublons_patients(df):
    """
    Ajoute une colonne booléenne 'is_duplicate' : true si un autre enregistrement
    partage la même clé (name, birth_date, gender). Pas de fusion (MVP).
    """
    w_dup = Window.partitionBy("name", "birth_date", "gender")
    df_marked = df.withColumn("is_duplicate", F.count(F.lit(1)).over(w_dup) > 1)
    nb_doublons = df_marked.filter(F.col("is_duplicate")).count()
    logging.info(f"👥 Doublons patients détectés (name, birth_date, gender) : {nb_doublons}")
    return df_marked

# -----------------------------
# 🔗 DÉDUPLICATION EXPLICABLE (moteur engine — master patient)
# -----------------------------
def enrichir_dedup_moteur():
    """
    Enrichit patient_fhir AVEC le master patient explicable du moteur engine.
    Colonnes ajoutées : master_patient_id, match_method, match_score.
    is_duplicate est recalculé côté moteur (une seule occurrence = master,
    les autres = doublons liés à un master existant).

    Si le moteur n'est pas importable (environnement sans engine), les colonnes
    SILVER brutes (is_duplicate par clé name/birth_date/gender) sont conservées.
    """
    table_patient = f"{SILVER_HIVE_DB}.patient_fhir"
    df_patient = spark.table(table_patient)
    try:
        from engine.identity.canonical import from_dict
        from engine.identity.matcher import deduplicate
    except ImportError as e:
        logging.warning(f"Moteur engine indisponible ({e}) — enrichissement dédup sauté.")
        return

    colonnes = ["_source_system", "source_patient_id", "name", "birth_date", "phone"]
    presentes = [c for c in colonnes if c in df_patient.columns]
    rows = [r.asDict() for r in df_patient.select(*presentes).collect()]

    patients = [
        from_dict({
            "source_system": r.get("_source_system") or "",
            "source_patient_id": r.get("source_patient_id") or "",
            "full_name": r.get("name") or "",
            "birth_date": r.get("birth_date"),
            "phone": r.get("phone"),
            "address": "",
            "gender": "",
            "source_file": "",
        })
        for r in rows
    ]
    if not patients:
        logging.warning("Aucun patient SILVER à analyser — enrichissement dédup sauté.")
        return

    decisions = deduplicate(patients)
    dedup_rows = [
        (d.source_system, d.source_patient_id, d.master_patient_id, d.method,
         float(d.score), 1 if d.method != "new_master" else 0)
        for d in decisions
    ]
    df_dedup = spark.createDataFrame(
        dedup_rows,
        ["_source_system", "source_patient_id", "master_patient_id",
         "match_method", "match_score", "iso_dup"],
    )

    df_patient = df_patient.join(df_dedup, on=["_source_system", "source_patient_id"], how="left")
    df_patient = df_patient.withColumn("is_duplicate", F.col("iso_dup") == 1) \
                           .drop("iso_dup")
    df_patient.write.mode("overwrite").saveAsTable(table_patient)

    nb_doublons = df_patient.filter(F.col("is_duplicate")).count()
    nb_masters = df_patient.filter(F.col("master_patient_id").isNotNull()).count()
    logging.info(f"🔗 Moteur : {len(patients)} patients analysés, {nb_masters} maîtrisés "
                 f"({nb_doublons} doublons liés à un master existant).")

# -----------------------------
# 🪵 CONFIGURATION DU LOGGING (console + fichier)
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
# 🔥 Initialisation de Spark
# -----------------------------
# Important: disable vectorized reader and read binary as string to avoid FIXED_LEN_BYTE_ARRAY issues
spark = SparkSession.builder \
    .appName("gen_fhir_silver") \
    .config("spark.sql.parquet.binaryAsString", "true") \
    .config("spark.sql.parquet.enableVectorizedReader", "false") \
    .config("spark.sql.warehouse.dir", "hdfs://localhost:9000/datalake/silver/warehouse") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "8") \
    .enableHiveSupport() \
    .getOrCreate()

spark.sql(f"CREATE DATABASE IF NOT EXISTS {SILVER_HIVE_DB}")
logging.info("✅ Spark initialisé et base Hive Silver vérifiée")

# -----------------------------
# 📂 Lecture des fichiers de configuration
# -----------------------------
with open(MAPPING_PATH, encoding="utf-8-sig") as f:
    fhir_mapping = json.load(f)
logging.info("✅ Mapping FHIR chargé")


# Quelques synonymes utiles pour les abréviations courtes
SYNONYMES_COURTS = {
    "birth_date": ["dob", "bdate", "birthday", "naissance", "date_naiss"],
    "phone": ["tel", "telephone", "mobile", "phone_number"],
    "email": ["mail"],
    "gender": ["sex", "sexe", "genre"],
    # nom de préférence : nom complet / nom de famille avant le prénom
    "name": ["full_name", "nom_complet", "patient_name", "nom", "prenom"],
    # priorité aux colonnes FK vers le patient : ne jamais confondre avec la PK de la table
    "source_patient_id": ["patient_id", "id_patient", "id", "client_id", "patient_code", "id_personne"],
    "encounter_id": ["id", "visit_id", "consultation_id"]
}

# Champs possibles pour identifiant principal
CLES_CANDIDATES = ["patient_id", "id", "id_patient", "source_patient_id",
                   "client_id", "patient_code", "id_personne"]

# -----------------------------
# 🧩 FONCTIONS UTILITAIRES
# -----------------------------
def fuzzy_score(a: str, b: str) -> int:
    a, b = (a or "").lower(), (b or "").lower()
    if fuzz:
        return int(fuzz.token_sort_ratio(a, b))
    if a == b:
        return 100
    if a in b or b in a:
        return 80
    return 0

def meilleure_colonne_attendue(champ_fhir: str, candidates: List[str]) -> str:
    champ = champ_fhir.lower()
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
    if meilleur_score >= FUZZY_THRESHOLD:
        return meilleure
    return None

def meilleure_colonne_patient_id(df):
    """
    Repère la colonne FK qui relie une table d'événement (Encounter/Condition/
    Observation) au patient. Priorité : patient_id / id_patient / *_patient_id,
    puis toute colonne patient suffixée _id. Évite de prendre la PK `id`
    de la table elle-même (uuid orphelin côté GOLD).
    """
    for c in df.columns:
        cl = c.lower()
        if cl in ("patient_id", "id_patient") or cl.endswith("_patient_id"):
            return c
    for c in df.columns:
        cl = c.lower()
        if "patient" in cl and cl.endswith("_id"):
            return c
    return None

def detecter_cle_primaire(df):
    cols = [c.lower() for c in df.columns]
    for cle in CLES_CANDIDATES:
        if cle in cols:
            return [c for c in df.columns if c.lower() == cle][0]
    return df.columns[0] if df.columns else None

# -----------------------------
# 📥 Lecture sécurisée des tables RAW (Hive / Parquet)
# -----------------------------
def lire_table(source: str, nom_table: str):
    """
    Tente de lire une table dans plusieurs emplacements possibles :
      1. Table Hive : source.table
      2. Table Hive simple : table
      3. Fichier Parquet : /datalake/raw/<source>/<table>.parquet
    Pour Parquet, on applique des stratégies dynamiques pour éviter FIXED_LEN_BYTE_ARRAY.
    """
    candidats = [
        f"{source}.{nom_table}",
        nom_table,
        f"{RAW_PARQUET_BASE}/{source}/{nom_table}.parquet"
    ]
    last_error = None
    for c in candidats:
        try:
            if c.endswith(".parquet") or os.path.isdir(c):
                logging.info(f"Lecture Parquet : {c}")
                # option mergeSchema et binaryAsString pour robustesse
                df = spark.read \
                    .option("mergeSchema", "true") \
                    .option("parquet.binaryAsString", "true") \
                    .parquet(c)
                return df
            else:
                logging.info(f"Lecture Hive : {c}")
                return spark.table(c)
        except Exception as e:
            last_error = e
            msg = str(e)
            logging.warning(f"[WARN] lecture {c} échouée: {msg}")
            # Si on détecte le type d'erreur connu, tenter une reprise intelligente
            if "FIXED_LEN_BYTE_ARRAY" in msg or "Parquet column cannot be converted" in msg or "decimal" in msg:
                logging.info(f"➡️ Tentative de lecture de secours pour {c} (cast/détection des colonnes binaires/décimales).")
                try:
                    tmp_df = spark.read.option("mergeSchema", "true").parquet(c)
                    # Inspecter le schema et cast/droper automatiquement les colonnes problématiques
                    for field in tmp_df.schema.fields:
                        dt = field.dataType.simpleString().lower()
                        colname = field.name
                        if "binary" in dt or "fixed_len_byte_array" in dt or "decimal" in dt:
                            logging.info(f"   - Casting colonne {colname} (type {dt}) en string pour sécurité.")
                            try:
                                tmp_df = tmp_df.withColumn(colname, F.col(colname).cast(StringType()))
                            except Exception as e2:
                                logging.warning(f"     -> cast échoué pour {colname}: {e2}. Suppression de la colonne.")
                                tmp_df = tmp_df.drop(colname)
                    return tmp_df
                except Exception as e2:
                    logging.warning(f"Échec de la lecture de secours pour {c}: {e2}")
                    # on continue les candidats
                    continue
            # sinon : passer au candidat suivant
            continue
    # si aucun candidat n'a marché
    raise FileNotFoundError(f"❌ Table {nom_table} introuvable pour la source {source}. Last error: {last_error}")

# -----------------------------
# Fonction dynamique pour cast + ajouter colonnes manquantes
# -----------------------------
def dynamic_cast(df, entite):
    """
    Cast toutes les colonnes FHIR selon FHIR_FIELDS.
    Crée les colonnes manquantes avec le type correct.
    """
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
# Boucle principale sur les sources et entités
# -----------------------------
tables_ecrites = set()  # 1re écriture = overwrite (idempotence), suivantes = append (fusion multi-sources)

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

            # Mapping dynamique FHIR → colonne source
            mapping_local = {}
            for champ in champs_fhir:
                meilleur = meilleure_colonne_attendue(champ, df.columns)
                if meilleur:
                    mapping_local[champ] = meilleur

            # Lien FK → patient (entités non-Patient) : privilégier la colonne
            # dédiée (patient_id...) plutôt que la PK `id` de la table, pour que
            # patient_uuid soit aligné sur celui du Patient (logique GOLD).
            if entite != "Patient":
                patient_link = meilleure_colonne_patient_id(df)
                if patient_link:
                    mapping_local["source_patient_id"] = patient_link
                    logging.info(f"🔗 Lien patient détecté pour {nom_table} : {patient_link}")

            if not mapping_local:
                logging.warning(f"⚠️ Aucun mapping trouvé pour {nom_table} — table ignorée.")
                continue

            # Détection clé primaire
            pk = detecter_cle_primaire(df)
            if entite == "Patient" and "source_patient_id" not in mapping_local:
                logging.info(f"Détection de la clé primaire pour Patient : {pk}")
                mapping_local["source_patient_id"] = pk

            # Sélection et renommage des colonnes
            colonnes_a_lire = list(set(mapping_local.values()))
            if pk and pk not in colonnes_a_lire:
                colonnes_a_lire.append(pk)
            logging.info(f"Colonnes à lire dans {nom_table} : {colonnes_a_lire}")

            # Sélection sécurisée : ignorer colonne manquante si select échoue
            try:
                df_sel = df.select(*colonnes_a_lire)
            except Exception as e:
                logging.warning(f"[WARN] select échoué sur {nom_table}: {e}. Tentative de lecture colonne par colonne.")
                # fallback: sélectionner uniquement les colonnes existantes
                existantes = [c for c in colonnes_a_lire if c in df.columns]
                df_sel = df.select(*existantes)

            for champ, col_src in mapping_local.items():
                if col_src in df_sel.columns:
                    df_sel = df_sel.withColumnRenamed(col_src, f"fhir__{champ}")
            df_sel = df_sel.withColumn("_source_table", F.lit(nom_table))

            # Cast dynamique avant union
            df_sel = dynamic_cast(df_sel, entite)
            if df_entite is None:
                df_entite = df_sel
            else:
                df_entite = dynamic_cast(df_entite, entite)
                df_entite = df_entite.unionByName(df_sel)

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

        if "fhir__source_patient_id" in df_entite.columns:
            logging.info(f"Ajout de fhir__patient_uuid basé sur source_patient_id")
            df_entite = df_entite.withColumn(
                "fhir__patient_uuid",
                F.expr(f"sha2(concat('{source}', '|', cast(fhir__source_patient_id as string)), 256)")
            )
            logging.info(f"   - Exemple patient_uuid: {df_entite.select('fhir__patient_uuid').where(F.col('fhir__patient_uuid').isNotNull()).limit(1).collect()}")
        else:
            logging.warning(f"⚠️ Aucune colonne source_patient_id détectée pour {entite} dans {source}. patient_uuid ne sera pas généré.")

        # 🧩 Traçabilité source système (nécessaire au moteur de déduplication)
        df_entite = df_entite.withColumn("_source_system", F.lit(source))

        # Sélection finale et drop duplicates
        colonnes_finales = [F.col(f"fhir__{c}").alias(c) for c in champs_fhir]
        if "_source_table" in df_entite.columns:
            colonnes_finales.append(F.col("_source_table"))
        if "_source_system" in df_entite.columns:
            colonnes_finales.append(F.col("_source_system"))
        df_final = df_entite.select(*colonnes_finales).dropDuplicates()

        # 🎚️ Normalisation des valeurs (MVP Étape 1) : gender -> male/female
        df_final = normaliser_gender(df_final)

        # 👥 Détection des doublons patients (MVP Étape 2), sans fusion
        if entite == "Patient":
            df_final = marquer_doublons_patients(df_final)

        # Écriture dynamique dans Hive
        # NB : overwrite au premier passage puis append, sinon chaque source écrase la précédente
        table_cible = f"{SILVER_HIVE_DB}.{entite.lower()}_fhir"
        mode = "overwrite" if table_cible not in tables_ecrites else "append"
        logging.info(f"📤 Écriture dans la table : {table_cible} (mode={mode})")
        df_final.write.mode(mode).saveAsTable(table_cible)
        tables_ecrites.add(table_cible)

# 🔗 Enrichissement final : master patient explicable (moteur engine)
if f"{SILVER_HIVE_DB}.patient_fhir" in tables_ecrites:
    enrichir_dedup_moteur()

update_sync_metadata("SILVER", status="ok")
logging.info("🎯 Transformation Silver (FHIR) terminée avec succès.")
spark.stop()

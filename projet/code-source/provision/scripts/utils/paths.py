#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paths.py — Point d'entrée central pour la configuration du pipeline.
=========================================================
Charge pipeline.yaml une seule fois, expose les constantes et helpers.
Tout script du pipeline importe ses chemins/configs depuis ici.

Usage:
    from ..utils.paths import PROJECT_ROOT, HIVE_SILVER, GOLD_TABLE, AGE_TRANCHES, hdfs_raw
"""

import os
import yaml

# ── PROJECT_ROOT ──
# Résolu depuis ce fichier : utils/ → ../../.. → racine du projet (code-source / datalake-final)
# Si pipeline.yaml définit project_root, cette valeur est prioritaire.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_DEFAULT_ROOT = os.path.normpath(os.path.join(_THIS_DIR, "..", "..", ".."))

_CFG_PATH = os.path.join(_DEFAULT_ROOT, "provision", "config", "pipeline.yaml")

with open(_CFG_PATH, encoding="utf-8") as _f:
    CFG = yaml.safe_load(_f)

# project_root explicite dans YAML > résolution par défaut
_raw_root = CFG.get("project_root", "") or ""
PROJECT_ROOT = os.path.normpath(_raw_root) if _raw_root else _DEFAULT_ROOT

# ── Raccourcis ──
CONFIG_DIR = os.path.join(PROJECT_ROOT, "provision", "config")
METADATA_DIR = os.path.join(PROJECT_ROOT, "provision", "metadata")
FHIR_ENTITIES_PATH = os.path.join(CONFIG_DIR, "fhir_entities.json")
DATASOURCES_PATH = os.path.join(CONFIG_DIR, "data_sources.json")

# ── HDFS ──
HDFS_NAMENODE = CFG["hdfs"]["namenode"]
HDFS_BASE = CFG["hdfs"]["base_path"]

def hdfs_raw(source, table):
    return f"{HDFS_NAMENODE}{HDFS_BASE}/raw/{source}/{table}"

def hdfs_warehouse(zone):
    return f"{HDFS_NAMENODE}{HDFS_BASE}/{zone}/warehouse"

# ── Hive DB names ──
HIVE_SILVER = CFG["hive_dbs"]["silver"]
HIVE_GOLD = CFG["hive_dbs"]["gold"]

# ── Tables cibles ──
GOLD_TABLE = CFG["tables"]["gold"]
CONSENT_GOLD_TABLE = CFG["tables"]["consent_gold"]
SILVER_PATIENT_TABLE = CFG["tables"]["silver_patient"]

# ── Spark defaults ──
SPARK_EXECUTOR_MEMORY = CFG["spark"]["executor_memory"]
SPARK_DRIVER_MEMORY = CFG["spark"]["driver_memory"]
SPARK_SHUFFLE_PARTITIONS = CFG["spark"]["shuffle_partitions"]

# ── GOLD age tranches ──
AGE_TRANCHES = [
    (row[0], row[1], row[2]) for row in CFG["gold"]["age_tranches"]
]

# ── SILVER ──
FUZZY_THRESHOLD = CFG["silver"]["fuzzy_threshold"]

# ── API ──
CORS_ORIGINS = CFG["api"]["cors_origins"]
FLASK_PORT = CFG["api"]["flask_port"]
DEFAULT_DATE_RANGE_DAYS = CFG["api"]["default_date_range_days"]

# ── Logs ──
LOG_DIR = os.path.join(PROJECT_ROOT, CFG["logs"]["dir"])
LOG_DIR_EXTRACT = os.path.join(LOG_DIR, CFG["logs"]["extract_subdir"])

# ── Sync metadata ──
SYNC_METADATA_PATH = os.path.join(METADATA_DIR, "sync_metadata.json")

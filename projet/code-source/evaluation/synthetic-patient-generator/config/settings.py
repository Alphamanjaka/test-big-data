"""
Configuration centrale du Synthetic Patient Data Generator.

Ce fichier regroupe tous les paramètres réutilisés par les modules
du générateur (patient_generator, distribution_engine, variation_engine,
source generators, etc.), conformément au plan d'implémentation.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Chemins de base
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
GROUND_TRUTH_DIR = DATA_DIR / "ground_truth"
RAW_DIR = DATA_DIR / "raw"
EXPERIMENTS_DIR = DATA_DIR / "experiments"

PHARMACY_DIR = RAW_DIR / "pharmacy"
CONSULTATION_DIR = RAW_DIR / "consultation"
IMAGING_DIR = RAW_DIR / "imaging"

MASTER_PATIENTS_FILE = GROUND_TRUTH_DIR / "master_patients.csv"
IDENTITY_MAPPING_FILE = GROUND_TRUTH_DIR / "identity_mapping.csv"
DISTRIBUTION_PLAN_FILE = GROUND_TRUTH_DIR / "distribution_plan.csv"

# ---------------------------------------------------------------------------
# Paramètres de génération (Étape 1 — Patients maîtres)
# ---------------------------------------------------------------------------
DEFAULT_NUM_PATIENTS = 10_000
FAKER_LOCALE = "fr_FR"   # peut être ajusté (ex: "fr_FR", "en_US")
RANDOM_SEED = 42          # pour la reproductibilité des expériences

# ---------------------------------------------------------------------------
# Sources hétérogènes (Étape 3)
# ---------------------------------------------------------------------------
SOURCES = ["pharmacy", "consultation", "imaging"]

# Probabilité qu'un patient du Ground Truth apparaisse dans chaque source
SOURCE_PRESENCE_PROBABILITY = {
    "pharmacy": 0.8,
    "consultation": 0.7,
    "imaging": 0.6,
}

# Préfixes des ID locaux générés par source (Étape 3 — Distribution Engine)
# ex: GT000001 -> PH000001 / MED000001 / IMG000001
SOURCE_ID_PREFIXES = {
    "pharmacy": "PH",
    "consultation": "MED",
    "imaging": "IMG",
}

# ---------------------------------------------------------------------------
# CIN (Carte Nationale d'Identité) — fichiers Patients maîtres (Étape 1)
# ---------------------------------------------------------------------------
# Couverture réaliste : ~75 % des patients maîtres possèdent un CIN. Un patient
# SANS CIN est absent de toutes les sources (cohérence cross-source). Format
# malgache "DDD DDDDD D" (province + n° d'ordre + clé), ex: 101 024045 2.
CIN_COVERAGE = 0.75
CIN_PROVINCE_MIN = 101
CIN_PROVINCE_MAX = 122
CIN_SERIAL_LENGTH = 5

# ---------------------------------------------------------------------------
# Niveaux de difficulté (Étape 4 — Variation Engine)
# ---------------------------------------------------------------------------
DIFFICULTY_LEVELS = {
    "easy": 0.10,
    "medium": 0.30,
    "hard": 0.50,
}

# Types de variations débloqués progressivement par niveau (cf. section
# "Niveaux de difficulté" du document). Chaque type actif a une probabilité
# d'être appliqué égale au taux de DIFFICULTY_LEVELS pour ce niveau.
DIFFICULTY_VARIATION_TYPES = {
    "easy": ["case", "spacing", "date_format", "cin_format"],
    "medium": [
        "case",
        "spacing",
        "date_format",
        "cin_format",
        "name_inversion",
        "typo_light",
    ],
    "hard": [
        "case",
        "spacing",
        "date_format",
        "cin_format",
        "name_inversion",
        "typo_light",
        "typo",
        "abbreviation",
        "missing_value",
    ],
}

# Probabilités individuelles de variation, utilisées par le Variation Engine
VARIATION_PROBABILITIES = {
    "name_variation": 0.30,
    "cin_variation": 0.20,
    "missing_value": 0.10,
}

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging
from rapidfuzz import fuzz
from ..utils.fhir_schema import FHIR_FIELDS
from ..utils.fhir_synonyms import FHIR_SYNONYMS

# -----------------------------
# Logging
# -----------------------------
LOG_DIR = "/home/vagrant/datalake-final/provision/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "generate_fhir_mapping_hybrid.log")

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
# Fichiers
# -----------------------------
DATASOURCES_PATH = "/home/vagrant/datalake-final/provision/config/data_sources.json"
REPORT_PATH = "/home/vagrant/datalake-final/provision/metadata/extract_raw_report.json"
OUTPUT_PATH = "/home/vagrant/datalake-final/provision/metadata/fhir_mapping.json"

# -----------------------------
# Charger datasources.json
# -----------------------------
with open(DATASOURCES_PATH, encoding="utf-8-sig") as f:
    datasources = json.load(f)
logging.info("✅ datasources.json chargé")

# -----------------------------
# Charger extract_raw_report.json
# -----------------------------
with open(REPORT_PATH, encoding="utf-8-sig") as f:
    report_list = json.load(f)
logging.info("✅ extract_raw_report.json chargé")

# Regrouper par source_name
report = {}
if isinstance(report_list, list):
    for table_entry in report_list:
        src_name = table_entry["source_name"]
        if src_name not in report:
            report[src_name] = []
        report[src_name].append(table_entry)
else:
    report = report_list

# -----------------------------
# Carte EXPLICITE table -> (entité FHIR, colonne lien patient ou None)
# Les tables hors carte sont EXCLUES du mapping :
#   - anti-régression : plus de "patients" parasites (ir_attachment,
#     product_product, res_users, hr_employee, acs_ethnicity, ...)
#   - les entités non-Patient doivent exposer une colonne de lien vers
#     le patient (FK) pour générer un patient_uuid aligné sur le Patient.
# -----------------------------
LINK_ENTITY_OVERRIDE = {
    "MAVIS": {
        "hms_patient": ("Patient", None),                 # main_table (canonique : id)
        "res_partner": ("Patient", None),                 # identité (name/gender/birthday/...)
        "account_move": ("Encounter", "patient_id"),      # visites/factures liées au patient
        "patient_death_register": ("Observation", "patient_id"),
    },
    "MMT_DB": {
        "gnuhealth_patient": ("Patient", None),           # main_table (canonique : id)
        "party_party": ("Patient", None),                 # identité (dob/gender/lastname)
    },
    "CLINIQUE": {
        "patients": ("Patient", None),                    # main_table (canonique : id)
        "visits": ("Encounter", "patient_id"),            # visites liées au patient
        "diagnoses": ("Condition", "patient_id"),         # diagnostics liés au patient
        "observations": ("Observation", "patient_id"),    # indicateurs liés au patient
    },
    # Sources intérimaires CSV (modèle test_bigdata) : patients uniquement
    # (les événements achats/consultations/examens resteront en RAW et seront
    #  mappés plus tard dès que les vraies bases seront connectées).
    "pharmacy": {
        "patients": ("Patient", None),                    # identité (client_id → source_patient_id)
    },
    "consultation": {
        "patients": ("Patient", None),                    # identité (patient_code → source_patient_id)
    },
    "imaging": {
        "patients": ("Patient", None),                    # identité (id_personne → source_patient_id)
    },
}

# -----------------------------
# Sélection des colonnes avec synonymes
# link_col : colonne FK vers le patient (forcée sur source_patient_id)
# use_id_fallback : autorise le fallback sur la PK `id` pour source_patient_id
# -----------------------------
def select_columns(columns, fhir_field_types, link_col=None, use_id_fallback=False):
    """Associe chaque champ FHIR attendu à la colonne source la plus proche.

    Stratégie dans l'ordre :
    1. force `link_col` sur la clé étrangère (source_patient_id) si fournie ;
    2. correspondance exacte (insensible à la casse) ;
    3. correspondance via FHIR_SYNONYMES ;
    4. fallback sur la PK 'id/uuid/patient_id' (uniquement pour Patient
       si use_id_fallback est demandé).

    Retourne la liste de colonnes (doublons supprimés via dict.fromkeys).
    """
    selected = []
    forced = {"source_patient_id": link_col} if link_col else {}
    for fhir_field in fhir_field_types.keys():
        if fhir_field in forced:
            selected.append(forced[fhir_field])
            continue
        found = False
        for col in columns:
            col_name = col["name"].lower()
            # correspondance exacte
            if col_name == fhir_field.lower():
                selected.append(col["name"])
                found = True
                break
            # correspondance via synonymes
            elif fhir_field in FHIR_SYNONYMS:
                for syn in FHIR_SYNONYMS[fhir_field]:
                    if col_name == syn.lower():
                        selected.append(col["name"])
                        found = True
                        break
            if found:
                break
        # fallback raisonnable sur l'identifiant patient (boîte à outils gratuite)
        if not found and use_id_fallback and fhir_field == "source_patient_id":
            for col in columns:
                if col["name"].lower() in ("id", "uuid", "patient_id"):
                    selected.append(col["name"])
                    break
    return list(dict.fromkeys(selected))

# -----------------------------
# Génération FHIR mapping
# -----------------------------
fhir_mapping = {}

for source_cfg in datasources:
    source_name = source_cfg["name"]
    main_table = source_cfg.get("main_table", "")
    fhir_mapping[source_name] = {entity: {} for entity in FHIR_FIELDS.keys()}

    tables = report.get(source_name, [])
    seen_cols = {}

    for table_entry in tables:
        if "table_name" not in table_entry:
            if "error" in table_entry:
                logging.warning(f"⚠️ Source {source_name}: ignorée ({table_entry['error']})")
            continue
        table_name = table_entry["table_name"]
        columns = table_entry.get("columns", [])

        # Carte explicite : seules les tables mappées sont traitées
        override = LINK_ENTITY_OVERRIDE.get(source_name, {}).get(table_name)
        if override is not None:
            entity, link_col = override
        elif table_name == main_table:
            entity, link_col = "Patient", None
        else:
            logging.info(f"⏭️ Table {source_name}.{table_name} ignorée (hors carte explicite)")
            continue

        use_id_fallback = (entity == "Patient")
        selected_cols = select_columns(columns, FHIR_FIELDS[entity],
                                       link_col=link_col, use_id_fallback=use_id_fallback)

        final_cols = []
        for col in selected_cols:
            if col not in seen_cols:
                final_cols.append(col)
                seen_cols[col] = table_name
            else:
                final_cols.append(f"{table_name}.{col}")

        fhir_mapping[source_name][entity][table_name] = final_cols

# -----------------------------
# Réorganiser main_table en premier
# -----------------------------
for source_name, entities in fhir_mapping.items():
    main_table = next((src.get("main_table") for src in datasources if src["name"] == source_name), None)
    if not main_table:
        continue
    for entity, tables in entities.items():
        if main_table in tables:
            ordered = {main_table: tables[main_table]}
            for tname, cols in tables.items():
                if tname != main_table:
                    ordered[tname] = cols
            fhir_mapping[source_name][entity] = ordered

# -----------------------------
# Sauvegarde JSON
# -----------------------------
with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(fhir_mapping, f, indent=2, ensure_ascii=False)

print(f"✅ FHIR mapping généré : {OUTPUT_PATH}")
logging.info(f"✅ FHIR mapping généré : {OUTPUT_PATH}")

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import logging
from rapidfuzz import fuzz
from ..utils.fhir_schema import FHIR_FIELDS, FHIR_SYNONYMS
from ..utils.paths import DATASOURCES_PATH, FHIR_ENTITIES_PATH, LOG_DIR, METADATA_DIR

# -----------------------------
# Logging
# -----------------------------
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
REPORT_PATH = os.path.join(METADATA_DIR, "extract_raw_report.json")
OUTPUT_PATH = os.path.join(METADATA_DIR, "fhir_mapping.json")

# -----------------------------
# Charger datasources.json
# -----------------------------
with open(DATASOURCES_PATH, encoding="utf-8-sig") as f:
    datasources = json.load(f)
logging.info("✅ datasources.json chargé")

# -----------------------------
# Charger fhir_entities.json (schéma + mappings + synonymes)
# -----------------------------
with open(FHIR_ENTITIES_PATH, encoding="utf-8") as f:
    fhir_entities_cfg = json.load(f)
TABLE_MAPPINGS = fhir_entities_cfg.get("table_mappings", {})
logging.info("✅ fhir_entities.json chargé")

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
# Sélection des colonnes avec synonymes
# -----------------------------
def select_columns(columns, fhir_field_types, link_col=None, use_id_fallback=False):
    """Associe chaque champ FHIR attendu à la colonne source la plus proche."""
    selected = []
    forced = {"source_patient_id": link_col} if link_col else {}
    for fhir_field in fhir_field_types.keys():
        if fhir_field in forced:
            selected.append(forced[fhir_field])
            continue
        found = False
        for col in columns:
            col_name = col["name"].lower()
            if col_name == fhir_field.lower():
                selected.append(col["name"])
                found = True
                break
            elif fhir_field in FHIR_SYNONYMS:
                for syn in FHIR_SYNONYMS[fhir_field]:
                    if col_name == syn.lower():
                        selected.append(col["name"])
                        found = True
                        break
            if found:
                break
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

        override = TABLE_MAPPINGS.get(source_name, {}).get(table_name)
        if override is not None:
            entity = override["entity"]
            link_col = override.get("fk_to_patient")
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

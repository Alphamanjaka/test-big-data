import json
import os
import logging
from rapidfuzz import fuzz
from ..utils.fhir_schema import FHIR_FIELDS

# -----------------------------
# Logging
# -----------------------------
LOG_DIR = "/home/vagrant/datalake-mavis/provision/logs"
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
DATASOURCES_PATH = "/home/vagrant/datalake-mavis/provision/config/data_sources.json"
REPORT_PATH = "/home/vagrant/datalake-mavis/provision/metadata/extract_raw_report.json"
OUTPUT_PATH = "/home/vagrant/datalake-mavis/provision/metadata/fhir_mapping.json"

fhir_synonyms = {
    "birth_date": ["birth_date", "dob", "birthday", "bdate"],
    "gender": ["gender", "sex"],
    "name": ["name", "full_name"],
    "phone": ["phone", "tel", "mobile"],
    "email": ["email", "mail"]
}

# -----------------------------
# Charger datasources.json
# -----------------------------
with open(DATASOURCES_PATH) as f:
    datasources = json.load(f)
logging.info("✅ datasources.json chargé")

# -----------------------------
# Charger extract_raw_report.json
# -----------------------------
with open(REPORT_PATH) as f:
    report_list = json.load(f)
logging.info("✅ extract_raw_report.json chargé")

# Regrouper par source_name si nécessaire
report = {}
if isinstance(report_list, list):
    for table_entry in report_list:
        source_name = table_entry["source_name"]
        if source_name not in report:
            report[source_name] = []
        report[source_name].append(table_entry)
else:
    report = report_list

# -----------------------------
# Fonctions utilitaires
# -----------------------------
def detect_fhir_entity(table_name, main_table):
    table_lower = table_name.lower()
    if table_lower == main_table.lower():
        return "Patient"
    if any(k in table_lower for k in ["pathology", "disease", "diagnosis"]):
        return "Condition"
    if any(k in table_lower for k in ["observation", "measurement", "death", "register"]):
        return "Observation"
    if "maternity" in table_lower or "family" in table_lower:
        return "Observation"
    if any(k in table_lower for k in ["encounter", "visit", "consultation", "admission", "appointment"]):
        return "Encounter"
    return "Patient"


def select_columns_hybrid(columns, fhir_field_types, fhir_synonyms=None):
    selected = {}
    for fhir_field, expected_type in fhir_field_types.items():
        candidates = [col for col in columns if expected_type.lower() in col.get("type", "").lower()]
        if not candidates:
            candidates = columns

        # Vérifier d’abord les synonymes
        if fhir_synonyms and fhir_field in fhir_synonyms:
            for syn in fhir_synonyms[fhir_field]:
                for col in candidates:
                    if col["name"].lower() == syn.lower():
                        selected[fhir_field] = col["name"]
                        break
                if fhir_field in selected:
                    break

        # Sinon, fuzzy match
        if fhir_field not in selected and candidates:
            best_col = max(candidates, key=lambda c: fuzz.ratio(c["name"].lower(), fhir_field.lower()))
            selected[fhir_field] = best_col["name"]
    return list(selected.values())

# -----------------------------
# Générer fhir_mapping
# -----------------------------
fhir_mapping = {}

for source_cfg in datasources:
    source_name = source_cfg["name"]
    main_table = source_cfg.get("main_table", "")
    fhir_mapping[source_name] = {entity: {} for entity in FHIR_FIELDS.keys()}

    tables = report.get(source_name, [])
    seen_cols = {}  # {col_name: table_name}

    for table_entry in tables:
        table_name = table_entry["table_name"]
        columns = table_entry.get("columns", [])
        entity = detect_fhir_entity(table_name, main_table)
        selected_cols = select_columns_hybrid(columns, FHIR_FIELDS[entity], fhir_synonyms)
        
        # 🚀 Supprimer les doublons de colonnes tout de suite
        selected_cols = list(dict.fromkeys(selected_cols))
        if len(selected_cols) != len(set(selected_cols)):
            logging.warning(f"⚠️ Doublons détectés dans {table_name}: {selected_cols}")

        # Ajouter la clé primaire si table principale
        if entity == "Patient":
            primary_key = next((col["name"] for col in columns if col["name"].lower() in ["id", "patient_id"]), None)
            if primary_key and primary_key not in selected_cols:
                selected_cols.insert(0, primary_key)

        final_cols = []
        for col in selected_cols:
            # 🧠 Si la colonne n'a jamais été vue → garder sans préfixe
            if col not in seen_cols:
                final_cols.append(col)
                seen_cols[col] = table_name
            else:
                # Si déjà vue → préfixer
                final_cols.append(f"{table_name}.{col}")

        fhir_mapping[source_name][entity][table_name] = final_cols
        logging.info(f"Table {table_name} → {entity} : {final_cols}")

# -----------------------------
# Réorganiser : main_table d'abord
# -----------------------------
for source_name, entities in fhir_mapping.items():
    logging.info(f"Réorganisation des tables pour la source {source_name}")
    main_table = next((src.get("main_table") for src in datasources if src["name"] == source_name), None)
    if not main_table:
        continue

    for entity, tables in entities.items():
        if not isinstance(tables, dict):
            continue

        if main_table in tables:
            ordered = {main_table: tables[main_table]}
            for tname, cols in tables.items():
                if tname != main_table:
                    ordered[tname] = cols
            fhir_mapping[source_name][entity] = ordered

# -----------------------------
# Sauvegarde finale
# -----------------------------
with open(OUTPUT_PATH, "w") as f:
    json.dump(fhir_mapping, f, indent=2)

logging.info(f"🎯 FHIR mapping généré avec succès : {OUTPUT_PATH}")
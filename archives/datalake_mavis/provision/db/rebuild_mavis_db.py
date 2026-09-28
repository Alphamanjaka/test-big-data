#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_mavis_db.py
===================
Reconstruit la base PostgreSQL `mavis_notheme` (source Odoo/HMS du Data Lake Mavis)
sur l'hôte Windows (Laragon, localhost:5432), afin de disposer d'une réplique
LOCALE et STABLE de MAVIS pour le développement, sans dépendre du serveur distant
(102.16.7.154), qui est instable.

Le schéma provient des tables externes Hive `MAVIS.*` capturées depuis la VM
(script `provision/scripts/capture_mavis_schema.sh` -> provision/metadata/mavis_schema.json).
Les types Hive sont retraduits en types PostgreSQL de façon à rester compatibles
avec le mapping `pg_to_hive` de `gen_extract_raw.py`.

Les données sont générées de façon SYNTHÉTIQUE mais réaliste (identités malgaches,
CIM-10 réelle, FK cohérentes), à un ordre de grandeur voisin de MMT_DB (~60k lignes).

Usage (hôte Windows, Python 3.13 + psycopg2-binary) :
    python provision/db/rebuild_mavis_db.py
"""

import json
import os
import random
import sys
from datetime import date, datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values

try:  # python-dotenv (dépendance du projet) : lit le .env gitignoré de projet/code-source/
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", ".env"))
except ImportError:
    pass

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(BASE_DIR, "metadata", "mavis_schema.json")
CIM10_PATH = os.path.join(BASE_DIR, "config", "cim10_liste.csv")

# Identifiants lus depuis l'environnement (.env gitignoré) — jamais en dur.
PG = dict(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", "5432")),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD", ""),
    dbname="mavis_notheme",
)
if not PG["password"]:
    sys.exit(
        "PGPASSWORD non défini : créer un fichier `.env` gitignoré à la racine de "
        "projet/code-source/ avec PGPASSWORD=<mot de passe postgres> (voir provision/.env.example)."
    )

random.seed(42)

# Volumes cibles par table (ordre de grandeur ~ MMT_DB, ~60-75k lignes)
VOLUMES = {
    "res_partner": 15000,          # patients + médecins + compagnies (identité)
    "hms_patient": 9791,           # patients (canonique, ~ MMT_DB)
    "hms_physician": 300,          # médecins
    "acs_ethnicity": 8,            # groupes ethniques (référentiel)
    "hms_diseases": 14341,         # pathologies (CIM-10)
    "ir_attachment": 800,          # pièces jointes
    "hr_employee": 800,            # employés
    "res_users": 50,               # utilisateurs
    "patient_death_register": 1500,  # registre des décès
    "product_product": 500,        # produits/prestations
    "account_move": 30000,         # visites/factures (Encounter)
}

TABLE_ORDER = [
    "res_partner",
    "acs_ethnicity",
    "hms_physician",
    "res_users",
    "hms_diseases",
    "hr_employee",
    "product_product",
    "ir_attachment",
    "hms_patient",
    "patient_death_register",
    "account_move",
]

# FKs réalistes (modèle Odoo/HMS) : (table enfant, colonne, table parente)
FOREIGN_KEYS = [
    ("hms_patient", "partner_id", "res_partner", "id"),
    ("hms_patient", "primary_doctor", "hms_physician", "id"),
    ("hms_patient", "ethnic_group_id", "acs_ethnicity", "id"),
    ("hms_patient", "user_id", "res_users", "id"),
    ("hms_patient", "create_uid", "res_users", "id"),
    ("hms_patient", "write_uid", "res_users", "id"),
    ("patient_death_register", "patient_id", "hms_patient", "id"),
    ("patient_death_register", "physician_id", "hms_physician", "id"),
    ("account_move", "patient_id", "hms_patient", "id"),
]

# ------------------------------------------------------------------
# Types Hive -> PostgreSQL (retranscription pour pg_to_hive de gen_extract_raw)
# ------------------------------------------------------------------
def hive_to_pg(hive_type):
    t = hive_type.strip().lower()
    mapping = {
        "int": "integer",
        "bigint": "bigint",
        "smallint": "smallint",
        "tinyint": "smallint",
        "string": "text",
        "boolean": "boolean",
        "double": "double precision",
        "float": "real",
        "date": "date",
        "timestamp": "timestamp without time zone",
    }
    if t in mapping:
        return mapping[t]
    if t.startswith("decimal"):
        # decimal(p,s) -> numeric(p,s)
        inner = t[len("decimal"):].strip("()")
        if inner:
            return f"numeric({inner})"
        return "numeric"
    if t.startswith("varchar"):
        inner = t[len("varchar"):].strip("()")
        if inner:
            return f"character varying({inner})"
        return "character varying"
    if t.startswith("char"):
        inner = t[len("char"):].strip("()")
        if inner:
            return f"character({inner})"
        return "character"
    return "text"

# ------------------------------------------------------------------
# Pools de valeurs réalistes
# ------------------------------------------------------------------
NAMES_M = [
    "Rakoto", "Rabe", "Andry", "Nirina", "Fara", "Tojo", "Hery", "Mamy", "Rado",
    "Faniry", "Tiana", "Manoa", "Sitraka", "Rija", "Lova", "Fenosoa", "Jaona",
    "Randria", "Herizo", "Tovo", "Miora", "Naina", "Fidy", "Soa", "Rivo",
]
NAMES_F = [
    "Lalao", "Miora", "Tantely", "Voahangy", "Nirina", "Hanitra", "Ravaka",
    "Fara", "Onja", "Sandra", "Miadana", "Hasina", "Fanja", "Noro", "Vero",
    "Mialy", "Sahondra", "Hanta", "Fenosoa", "Lanto", "Soavinina", "Toky",
]
LAST_NAMES = [
    "Rakotoarimanana", "Rasolofo", "Rabemananjara", "Randriamasinoro", "Razafindrakoto",
    "Ramanantsalama", "Rakotomalala", "Rasoanaivo", "Rabemananjara", "Ranaivoson",
    "Ratsimbazafy", "Rakotonandrasana", "Rasamuel", "Ravelomanana", "Rakotoarisolo",
    "Andrianarisoa", "Razafimahatratra", "Rakotobe", "Ramamonjisoa", "Rasolofoson",
    "Randrianarivelo", "Rakotoson", "Razanamalala", "Rabetokotany", "Rakotoarison",
    "Rasolondraibe", "Ramaroson", "Rakotozanakolona", "Ratsimba", "Rajaonarivelo",
]
SPECIALTIES = [
    "Médecine Générale", "Pédiatrie", "Gynécologie", "Cardiologie",
    "Chirurgie", "Ophtalmologie", "Dermatologie", "ORL",
]
ETHNICITIES = ["Merina", "Betsileo", "Antandroy", "Antanosy", "Betsimisaraka", "Sakalava", "Tsimihety", "Antaimoro"]
EDUCATIONS = ["primary", "secondary", "university", "other", ""]
MARITAL = ["single", "married", "divorced", "widowed", "separated", ""]
OCCUPATIONS = ["farmer", "teacher", "trader", "student", "driver", "nurse", "civil servant", ""]
BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", ""]
CITIES = ["Antananarivo", "Toamasina", "Mahajanga", "Fianarantsoa", "Antsirabe"]
LANG = ["fr_FR", "en_US", ""]


def malagasy_full_name(gender=None):
    g = gender or random.choice(["m", "f"])
    first = random.choice(NAMES_M if g == "m" else NAMES_F)
    return f"{random.choice(LAST_NAMES)} {first}".strip()


def rand_date(start_year=1940, end_year=2016):
    return date(start_year, 1, 1) + timedelta(days=random.randint(0, 365 * (end_year - start_year)))


def rand_ts():
    return datetime(2013, 1, 1) + timedelta(seconds=random.randint(0, 4 * 365 * 24 * 3600))


def load_cim10():
    entries = []
    try:
        import csv
        with open(CIM10_PATH, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append((row.get("cim10") or "", row.get("lib_long") or ""))
        entries = [(c.strip(), l.strip()) for c, l in entries if c and l]
    except Exception as exc:
        print(f"⚠️ CIM10 indisponible ({exc}), fallback sur une liste réduite")
    if not entries:
        entries = [
            ("A09", "Diarrhée et gastro-entérite présumée d'origine infectieuse"),
            ("O80", "Accouchement unique spontané"),
            ("J18.9", "Pneumonie, germe non précisé"),
            ("I10", "Hypertension essentielle (bénigne)"),
            ("E11", "Diabète non insulino-dépendant"),
            ("B54", "Paludisme à Plasmodium falciparum"),
            ("K35", "Appendicite aiguë"),
            ("N39.0", "Infection urinaire, siège non précisé"),
        ]
    return entries


CIM10 = load_cim10()


# ------------------------------------------------------------------
# Génération générique + surcharges sémantiques
# ------------------------------------------------------------------
def gen_value(col_name, col_type, ctx):
    """Génère une valeur plausible pour une colonne (types PostgreSQL)."""

    # --- FK int -> id de la table référencée ---
    fk_map = {
        "partner_id": "res_partner",
        "patient_id": "hms_patient",
        "primary_doctor": "hms_physician",
        "physician_id": "hms_physician",
        "ethnic_group_id": "acs_ethnicity",
        "specialty_id": "hms_diseases",
        "registration_product_id": "product_product",
        "product_id": "product_product",
        "invoice_id": "account_move",
        "company_id": "res_partner",
        "parent_id": "res_partner",
        "create_uid": "res_users",
        "write_uid": "res_users",
        "user_id": "res_users",
    }
    if col_name in fk_map:
        n = VOLUMES[fk_map[col_name]]
        # create_uid/write_uid souvent 1 (admin)
        if col_name in ("create_uid", "write_uid") and random.random() < 0.6:
            return 1
        return random.randint(1, n)

    lower = col_name.lower()

    if lower in ("name", "display_name", "company_name", "commercial_company_name"):
        pool = ctx.get("name_pool", malagasy_full_name)
        return pool() if callable(pool) else pool
    if lower == "gender":
        return random.choice(["m", "f"])
    if lower in ("birthday", "date_of_death", "dob", "date"):
        return rand_date()
    if lower in ("create_date", "write_date", "last_time_entries_checked", "calendar_last_notif_ack",
                 "membership_start", "membership_stop", "membership_cancel", "signup_expiration"):
        return rand_ts() if random.random() < 0.7 else None
    if lower in ("email", "email_normalized"):
        return f"{random.choice(NAMES_M).lower()}.{random.choice(LAST_NAMES).lower()}@example.mg"
    if lower in ("phone", "mobile", "phone_sanitized"):
        return f"03{random.choice(['2', '3', '4'])} {random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"
    if lower == "street":
        return f"Lot {random.randint(1, 999)} II{random.choice(['A', 'B', 'C', 'D', 'E'])}{random.randint(1, 99)}"
    if lower == "street2":
        return random.choice(["Ankadifotsy", "Isoraka", "Analakely", "Ivandry", ""])
    if lower == "city":
        return random.choice(CITIES)
    if lower == "zip":
        return str(random.randint(101, 601))
    if lower == "country":  # pas présent, garde si besoin
        return "Madagascar"
    if lower == "lang":
        return random.choice(LANG)
    if lower in ("occupation",):
        return random.choice(OCCUPATIONS)
    if lower in ("marital_status",):
        return random.choice(MARITAL)
    if lower in ("education", "husband_edu"):
        return random.choice(EDUCATIONS)
    if lower in ("blood_group",):
        return random.choice(BLOOD_GROUPS)
    if lower in ("state_id", "country_id", "title", "state", "type", "function", "ref",
                 "vat", "siret", "code", "barcode", "gov_code", "emp_code", "pension",
                 "type_paid", "first_determination", "second_determination"):
        return None
    if lower.startswith("is_") or lower in ("active", "hospitalized", "discharged", "is_child",
                                             "mammography", "breast_self_examination", "pap_test",
                                             "colposcopy", "fertile", "currently_pregnant",
                                             "is_vip", "chk_print_service_card", "free_member",
                                             "provide_commission", "plan_to_change_car",
                                             "is_published", "partner_share", "employee",
                                             "is_company", "is_locked", "is_referring_doctor",
                                             "is_driver", "is_receiver", "is_donor",
                                             "est_patient", "allow_home_appointment",
                                             "show_fee_on_booking", "allowed_online_booking",
                                             "medecin_smi", "is_primary_surgeon", "is_prestataire",
                                             "prest_commission", "is_cash_paid", "is_corpo_tieup"):
        return random.random() < 0.7

    if col_type == "boolean":
        return random.random() < 0.7
    if col_type in ("integer", "bigint", "smallint"):
        return random.randint(0, 100) if random.random() < 0.4 else None
    if col_type == "date":
        return rand_date()
    if col_type.startswith("timestamp"):
        return rand_ts() if random.random() < 0.7 else None
    if col_type.startswith("numeric") or col_type.startswith("decimal"):
        return round(random.uniform(0, 100), 2)
    if col_type.startswith("double") or col_type in ("double precision", "real"):
        return round(random.uniform(0, 100), 2)
    if col_type.startswith("character") or col_type == "text":
        return random.choice(["value A", "value B", "", ""])
    return None


def special_table_rows(table, cols, ctx):
    """Construit des lignes cohérentes pour les tables clés (relations + identité)."""
    n = VOLUMES[table]
    col_names = [c["name"] for c in cols]
    col_types = {c["name"]: c["type"] for c in cols}
    rows = []

    if table == "res_partner":
        n_prof = VOLUMES["hms_physician"]
        n_pat = VOLUMES["hms_patient"]
        # identifiants partenaires : patients dans une plage contiguë
        ctx["patient_partner_ids"] = list(range(1, n_pat + 1))
        ctx["prof_partner_ids"] = list(range(n_pat + 1, n_pat + n_prof + 1))
        for i in range(1, n + 1):
            if i in ctx["patient_partner_ids"]:
                kind = "patient"
            elif i in set(ctx["prof_partner_ids"]):
                kind = "doctor"
            else:
                kind = random.choice(["company", "company", "person"])
            gender = random.choice(["m", "f"]) if kind != "company" else None
            if kind == "company":
                name = f"{random.choice(LAST_NAMES)} Établissement #{i}"
            else:
                name = malagasy_full_name(gender)
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname == "name":
                    val = name
                elif cname == "display_name":
                    val = name
                elif cname == "company_name":
                    val = name if kind == "company" else None
                elif cname == "gender":
                    val = gender
                elif cname == "is_company":
                    val = kind == "company"
                elif cname == "employee":
                    val = kind == "doctor"
                elif cname == "is_referring_doctor":
                    val = kind == "doctor"
                elif cname == "birthday":
                    val = rand_date() if kind != "company" else None
                elif cname == "vat":
                    val = f"MG{random.randint(1000, 9999)}{random.randint(1000, 9999)}" if kind == "company" else ""
                row[cname] = val
            rows.append(row)

    elif table == "hms_patient":
        pat_partners = ctx["patient_partner_ids"]
        docs = range(1, VOLUMES["hms_physician"] + 1)
        eths = range(1, VOLUMES["acs_ethnicity"] + 1)
        users = range(1, VOLUMES["res_users"] + 1)
        for i in range(1, n + 1):
            partner_id = pat_partners[(i - 1) % len(pat_partners)]
            row = {"id": i}
            gender = random.choice(["m", "f"])
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname == "partner_id":
                    val = partner_id
                elif cname == "primary_doctor":
                    val = random.choice(list(docs))
                elif cname == "ethnic_group_id":
                    val = random.choice(list(eths))
                elif cname in ("user_id", "create_uid"):
                    val = random.choice(list(users))
                elif cname == "write_uid":
                    val = 1
                elif cname in ("gravida", "full_term", "premature", "abortions", "stillbirths",
                               "ectopic", "vaginal_birth", "cesarean_birth", "menarche", "menopause"):
                    val = random.randint(0, 8) if gender == "f" and random.random() < 0.4 else None
                elif cname == "currently_pregnant":
                    val = (gender == "f") and random.random() < 0.1
                elif cname == "medical_history":
                    val = random.choice(["", "", "HTA", "Diabète", "Asthme"]) if random.random() < 0.3 else ""
                elif cname == "occupation":
                    val = random.choice(OCCUPATIONS)
                row[cname] = val
            rows.append(row)

    elif table == "hms_physician":
        prof_partners = ctx["prof_partner_ids"]
        users = range(1, VOLUMES["res_users"] + 1)
        for i in range(1, n + 1):
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname == "partner_id":
                    val = prof_partners[(i - 1) % len(prof_partners)]
                elif cname == "user_id":
                    val = min(i + 1, VOLUMES["res_users"])
                elif cname == "code":
                    val = f"MED{i:05d}"
                elif cname == "medical_license":
                    val = f"LIC-{random.randint(1000, 9999)}"
                elif cname == "basic_info":
                    val = random.choice(SPECIALTIES)
                elif cname == "id_employee":
                    val = f"EMP{i:05d}"
                row[cname] = val
            rows.append(row)

    elif table == "acs_ethnicity":
        for i in range(1, n + 1):
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname == "name":
                    val = ETHNICITIES[i - 1] if i <= len(ETHNICITIES) else f"Ethnie {i}"
                row[cname] = val
            rows.append(row)

    elif table == "hms_diseases":
        for i in range(1, n + 1):
            code, libelle = CIM10[(i - 1) % len(CIM10)]
            if i > len(CIM10):
                code = f"{code}.{i // len(CIM10)}"
                libelle = f"{libelle} (variante {i // len(CIM10)})"
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname == "name":
                    val = libelle
                elif cname == "code":
                    val = code
                row[cname] = val
            rows.append(row)

    elif table in ("ir_attachment", "hr_employee", "res_users", "product_product"):
        # Tables génériques : valeurs par défaut + libellé
        for i in range(1, n + 1):
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname in ("name", "display_name"):
                    val = malagasy_full_name()
                elif cname == "login":
                    val = f"user{i}"
                elif cname == "code":
                    val = f"{table[:4].upper()}{i:05d}"
                elif cname == "create_uid":
                    val = 1
                row[cname] = val
            rows.append(row)

    elif table == "patient_death_register":
        patients = range(1, VOLUMES["hms_patient"] + 1)
        docs = range(1, VOLUMES["hms_physician"] + 1)
        for i in range(1, n + 1):
            patient_id = random.choice(list(patients))
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname == "name":
                    val = f"Registre décès {i}"
                elif cname == "patient_id":
                    val = patient_id
                elif cname == "physician_id":
                    val = random.choice(list(docs))
                elif cname == "date_of_death":
                    val = rand_date(2000, 2024)
                elif cname == "patient_age":
                    val = str(random.randint(0, 100))
                elif cname == "patient_gender":
                    val = random.choice(["m", "f"])
                elif cname == "state":
                    val = random.choice(["confirmed", "draft", "done"])
                elif cname == "reason":
                    val = random.choice(CIM10)[1]
                row[cname] = val
            rows.append(row)

    elif table == "account_move":
        patients = range(1, VOLUMES["hms_patient"] + 1)
        products = range(1, VOLUMES["product_product"] + 1)
        for i in range(1, n + 1):
            patient_id = random.choice(list(patients))
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                if cname == "patient_id":
                    val = patient_id
                elif cname == "name":
                    val = f"INV/{i:06d}"
                elif cname == "ref":
                    val = f"INV/{i:06d}"
                elif cname == "create_uid":
                    val = 1
                elif cname == "partner_id":
                    val = random.choice(list(patients))
                row[cname] = val
            rows.append(row)

    else:
        for i in range(1, n + 1):
            row = {"id": i}
            for cname in col_names:
                if cname == "id":
                    continue
                val = gen_value(cname, col_types[cname], ctx)
                row[cname] = val
            rows.append(row)

    return rows


def insert_rows(cur, table, cols, rows):
    col_names = [c["name"] for c in cols]
    quoted = ", ".join(f'"{c}"' for c in col_names)
    placeholders = ", ".join(["%s"] * len(col_names))
    tuples = [tuple(r.get(c) for c in col_names) for r in rows]
    execute_values(cur, f'INSERT INTO "{table}" ({quoted}) VALUES %s', tuples, page_size=1000)


def main():
    print(f"Lecture du schéma : {SCHEMA_PATH}")
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    schemas = {entry["table_name"]: entry for entry in schema}

    missing = [t for t in TABLE_ORDER if t not in schemas]
    if missing:
        sys.exit(f"❌ Tables absentes du schéma : {missing}")

    conn = psycopg2.connect(**PG)
    conn.autocommit = False
    cur = conn.cursor()
    total_rows = sum(VOLUMES.values())
    done = 0

    print(">>> Suppression des anciennes tables")
    cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")

    print(">>> Création des tables (schéma retraduit en PostgreSQL)")
    for table in TABLE_ORDER:
        cols = schemas[table]["columns"]
        defs = []
        for c in cols:
            pg_type = hive_to_pg(c["type"])
            defs.append(f'"{c["name"]}" {pg_type}')
        defs.append('PRIMARY KEY ("id")')
        cur.execute(f'CREATE TABLE "{table}" ({", ".join(defs)})')
    print(f"    {len(TABLE_ORDER)} tables créées")

    ctx = {
        "patient_partner_ids": list(range(1, VOLUMES["hms_patient"] + 1)),
        "prof_partner_ids": list(range(VOLUMES["hms_patient"] + 1,
                                       VOLUMES["hms_patient"] + VOLUMES["hms_physician"] + 1)),
        "name_pool": malagasy_full_name,
    }

    for table in TABLE_ORDER:
        n = VOLUMES[table]
        print(f">>> {table:<30} génération de {n:>6} lignes...", flush=True)
        cols = schemas[table]["columns"]
        rows = special_table_rows(table, cols, ctx)
        insert_rows(cur, table, cols, rows)
        done += n
        print(f"    insérées ✔ ({done}/{total_rows})")

    print(">>> Ajout des clés étrangères")
    for child, col, parent, pcol in FOREIGN_KEYS:
        try:
            cur.execute(
                f'ALTER TABLE "{child}" ADD CONSTRAINT "fk_{child}_{col}" '
                f'FOREIGN KEY ("{col}") REFERENCES "{parent}"("{pcol}")'
            )
        except Exception as e:
            print(f"    ⚠️ FK {child}.{col} non ajoutée : {e}")

    conn.commit()

    print("\n=== Vérification des volumes ===")
    for table in TABLE_ORDER:
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        real = cur.fetchone()[0]
        flag = "OK " if real == VOLUMES[table] else "⚠️ "
        print(f"  {flag}{table:<32} {real:>6} / {VOLUMES[table]}")

    cur.close()
    conn.close()
    print(f"\n✅ Base mavis_notheme reconstruite ({done} lignes au total)")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_mmt_db.py
=================
Reconstruit la base PostgreSQL `mmt_db` (source GNU Health du projet Data Lake Mavis)
à partir des schémas exacts capturés dans l'ancien rapport d'extraction :
    provision/metadata/extract/MMT_DB_extract_raw_report.json

Le dump d'origine n'existant plus, les données sont régénérées de façon SYNTHÉTIQUE
mais réaliste : mêmes tables, mêmes colonnes/types, mêmes volumes (~60 000 lignes),
identités malgaches cohérentes et clés étrangères respectées (modèle GNU Health).

Usage (hôte Windows, Python 3.13 + psycopg2-binary) :
    python provision/db/rebuild_mmt_db.py
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
REPORT_PATH = os.path.join(BASE_DIR, "metadata", "extract", "MMT_DB_extract_raw_report.json")
CIM10_PATH = os.path.join(BASE_DIR, "config", "cim10_liste.csv")

# Identifiants lus depuis l'environnement (.env gitignoré) — jamais en dur.
PG = dict(
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", "5432")),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD", ""),
    dbname="mmt_db",
)
if not PG["password"]:
    sys.exit(
        "PGPASSWORD non défini : créer un fichier `.env` gitignoré à la racine de "
        "projet/code-source/ avec PGPASSWORD=<mot de passe postgres> (voir provision/.env.example)."
    )

random.seed(42)

VOLUMES = {
    "party_party": 15465,
    "gnuhealth_vegetarian_types": 5,
    "gnuhealth_diet_belief": 7,
    "gnuhealth_pathology": 14341,
    "gnuhealth_family": 2,
    "gnuhealth_patient": 9791,
    "gnuhealth_healthprofessional": 5116,
    "gnuhealth_insurance": 59,
    "party_address": 15485,
}

TABLE_ORDER = [
    "party_party",
    "gnuhealth_vegetarian_types",
    "gnuhealth_diet_belief",
    "gnuhealth_pathology",
    "gnuhealth_family",
    "gnuhealth_patient",
    "gnuhealth_healthprofessional",
    "gnuhealth_insurance",
    "party_address",
]

FOREIGN_KEYS = [
    ("gnuhealth_patient", "name", "party_party", "id"),
    ("gnuhealth_patient", "family", "gnuhealth_family", "id"),
    ("party_address", "party", "party_party", "id"),
    ("gnuhealth_healthprofessional", "name", "party_party", "id"),
    ("gnuhealth_insurance", "name", "party_party", "id"),
]

# ------------------------------------------------------------------
# Pools de valeurs réalistes
# ------------------------------------------------------------------
NAMES_M = [
    "Rakoto", "Rabe", "Andry", "Nirina", "Fara", "Tojo", "Hery", "Mamy", "Rado",
    "Faniry", "Tiana", "Manoa", "Sitraka", "Rija", "Lova", "Fenosoa", "Jaona",
    "Randria", "Herizo", "Tovo", "Miora", "Naina", "Fidy", "Soa", "Rivo",
]
NAMES_F = [
    "Lalao", "Miora", "Tantely", "Voahangy", "NirISO", "Hanitra", "Ravaka",
    "Fara", "Onja", "Sandra", "Miadana", "Hasina", "Fanja", "Noro", "Vero",
    "Mialy", " Sahondra", "Hanta", "Fenosoa", "Lanto", "Soavinina", "Toky",
]
LAST_NAMES = [
    "Rakotoarimanana", "Rasolofo", "Rabemananjara", "Randriamasinoro", "Razafindrakoto",
    "Ramanantsalama", "Rakotomalala", "Rasoanaivo", "Rabemananjara", "Ranaivoson",
    "Ratsimbazafy", "Rakotonandrasana", "Rasamuel", "Ravelomanana", "Rakotoarisolo",
    "Andrianarisoa", "Razafimahatratra", "Rakotobe", "Ramamonjisoa", "Rasolofoson",
    "Randrianarivelo", "Rakotoson", "Razanamalala", "Rabetokotany", "Rakotoarison",
    "Rasolondraibe", "Ramaroson", "Rakotozanakolona", "Ratsimba", "Rajaonarivelo",
    "Ranaivoharisoa", "Rasendra", "Rakotojoelinandrasana", "Razafindratsimba", "Raharivelomanana",
]
INSTITUTIONS = [
    "CSB II Ambohipo", "CHRD2 Antananarivo", "CHRD2 Toamasina", "CHRD2 Mahajanga",
    "Clinique Fiaro", "Polyclinique Ilafy", "Espace Medical", "Pharmacie Ankorondrano",
    "OSIE Ambatomena", "Centre Sante Manakambahiny", "Dispensaire Ivato",
    "Hopital Joseph Ravoahangy", "Clinique des Soeurs Franciscaines", "Cabinet Dr Rakoto",
    "Assurance Ny Havana", "Mutuelle Santé Fihavanana", "COSFA Santé", "Aro Antananarivo",
]
EDUCATIONS = ["primary", "secondary", "university", "other", None]
MARITAL = ["single", "married", "divorced", "widowed", "separated", None]
OCCUPATIONS = ["farmer", "teacher", "trader", "student", "driver", "nurse", None]

VEGETARIAN_TYPES = ["none", "vegetarian", "vegan", "lacto vegetarian", "pescetarian"]
DIET_BELIEFS = [
    "No special diet", "Halal", "Kosher", "Hindu diet", "Buddhist diet",
    "Seventh-day Adventist", "Rastafarian",
]


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
            ("B54", "Paludisme à Plasmodium falciparum, sans mention de complication"),
            ("K35", "Appendicite aiguë"),
            ("N39.0", "Infection urinaire, siège non précisé"),
        ]
    return entries


CIM10 = load_cim10()

# ------------------------------------------------------------------
# Génération par table (colonne par colonne, guidée par le type + le nom)
# ------------------------------------------------------------------


def gen_value(col_name, col_type, samples):
    """Génère une valeur plausible pour une colonne générique."""
    if col_type == "bytea":
        return None
    non_null_samples = [s for s in samples if s is not None] if samples else []
    # Colonnes énumérées : réutiliser les valeurs observées dans l'ancienne base
    if (
        non_null_samples
        and col_type in ("character varying", "text")
        and len({str(s) for s in non_null_samples}) <= 12
        and not col_name.endswith(("name", "code"))
    ):
        return random.choice(non_null_samples)
    if col_name in ("create_date", "write_date"):
        return rand_ts() if col_name == "create_date" or random.random() < 0.7 else None
    if col_name == "activation_date":
        return rand_ts().date()
    if col_name == "deactivation_date":
        return rand_ts().date() if random.random() < 0.05 else None
    if col_name in ("code",):
        return None  # renseigné spécifiquement (str(id))
    if col_name == "code_length":
        return 1
    if col_name in ("citizenship",):
        return random.choice([None, None, None, "MG"]) if col_type in ("character varying", "text") else None
    if col_name in ("education",):
        return random.choice(EDUCATIONS) if col_type in ("character varying", "text") else None
    if col_name in ("marital_status",):
        return random.choice(MARITAL) if col_type in ("character varying", "text") else None
    if col_name in ("occupation",):
        return random.choice(OCCUPATIONS) if col_type in ("character varying", "text") else None
    if col_type == "boolean":
        return random.random() < 0.75
    if col_type in ("integer", "smallint", "bigint"):
        return None
    if col_type == "date":
        return rand_date()
    if col_type.startswith("timestamp"):
        return rand_ts()
    if col_type.startswith("numeric"):
        return round(random.uniform(0, 100), 2)
    if col_type.startswith("character varying") or col_type == "text":
        return None
    return None


def build_table_rows(table, cols, ctx):
    """Construit les lignes d'une table en tenant compte des relations."""
    n = VOLUMES[table]
    col_defs = [(c["name"], c["type"], c.get("samples") or []) for c in cols]
    rows = []

    if table == "party_party":
        n_prof, n_ins, n_pat = (
            VOLUMES["gnuhealth_healthprofessional"],
            VOLUMES["gnuhealth_insurance"],
            VOLUMES["gnuhealth_patient"],
        )
        for i in range(1, n + 1):
            if i <= n_prof:
                kind = "prof"
            elif i <= n_prof + n_ins:
                kind = "ins"
            elif i <= n_prof + n_ins + n_pat:
                kind = "pat"
            elif i <= n_prof + n_ins + n_pat + 300:
                kind = "inst"
            else:
                kind = random.choice(["person", "person", "inst"])
            gender = random.choice(["m", "f"]) if kind != "ins" else None
            is_person = kind in ("prof", "pat", "person")
            if kind == "ins":
                disp = f"{random.choice(['Ny Havana', 'COSFA', 'ARO', 'SEECO'])} Assurance #{i}"
            elif kind == "inst":
                disp = f"{random.choice(INSTITUTIONS)} #{i}"
            else:
                disp = malagasy_full_name(gender)
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = disp
                elif cname == "lastname":
                    val = ""
                elif cname == "code":
                    val = str(i)
                elif cname == "is_person":
                    val = is_person
                elif cname == "is_patient":
                    val = kind == "pat"
                elif cname == "is_healthprof":
                    val = kind == "prof"
                elif cname == "is_insurance_company":
                    val = kind == "ins"
                elif cname == "is_institution":
                    val = kind in ("inst", "ins")
                elif cname == "gender":
                    val = gender if is_person else None
                elif cname == "dob":
                    val = rand_date(1940, 2014) if is_person else None
                elif cname in ("create_uid", "write_uid", "internal_user"):
                    val = 1 if cname == "create_uid" else None
                elif cname == "fsync":
                    val = True
                row[cname] = val
            rows.append(row)

    elif table == "gnuhealth_patient":
        pat_parties = ctx["patient_party_ids"]
        fam_ids = ctx["family_ids"]
        veg_ids = ctx["veg_ids"]
        for i in range(1, n + 1):
            party_id = pat_parties[(i - 1) % len(pat_parties)]
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = party_id
                elif cname == "family":
                    val = random.choice(fam_ids) if fam_ids and random.random() < 0.02 else None
                elif cname == "vegetarian_type":
                    val = random.choice(veg_ids) if veg_ids else None
                elif cname in ("create_uid", "write_uid"):
                    val = 1 if cname == "create_uid" else None
                elif cname == "code":
                    val = str(party_id) if ctype in ("character varying", "text") else None
                row[cname] = val
            rows.append(row)

    elif table == "gnuhealth_pathology":
        for i in range(1, n + 1):
            code, libelle = CIM10[(i - 1) % len(CIM10)]
            if i > len(CIM10):
                code = f"{code}.{i // len(CIM10)}"
                libelle = f"{libelle} (variante {i // len(CIM10)})"
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = libelle
                elif cname == "code":
                    val = code
                elif cname == "active" and ctype == "boolean":
                    val = True
                row[cname] = val
            rows.append(row)

    elif table == "party_address":
        all_parties = ctx["all_party_ids"]
        for i in range(1, n + 1):
            row = {"id": i}
            addr_name = malagasy_full_name() if random.random() < 0.8 else random.choice(INSTITUTIONS)
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "party":
                    val = random.choice(all_parties)
                elif cname == "name":
                    val = addr_name
                elif cname in ("street", "city", "country", "zip", "phone", "mobile") and ctype not in ("character varying", "text"):
                    val = None
                elif cname == "street":
                    val = f"Lot {random.randint(1, 999)} II{random.choice(['A', 'B', 'C', 'D', 'E'])}{random.randint(1, 99)}"
                elif cname == "city":
                    val = random.choice(["Antananarivo", "Toamasina", "Mahajanga", "Fianarantsoa", "Antsirabe"])
                elif cname == "country":
                    val = "Madagascar"
                elif cname == "zip":
                    val = str(random.randint(101, 601))
                elif cname in ("phone", "mobile"):
                    val = f"03{random.choice(['2', '3', '4'])} {random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}"
                row[cname] = val
            rows.append(row)

    elif table == "gnuhealth_healthprofessional":
        prof_parties = ctx["prof_party_ids"]
        spec_pool = ["Médecine Générale", "Pédiatrie", "Gynécologie", "Cardiologie", "Chirurgie"]
        for i in range(1, n + 1):
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = prof_parties[(i - 1) % len(prof_parties)]
                elif cname == "code":
                    val = f"HP{i:05d}"
                elif cname in ("info", "specialty") and ctype in ("character varying", "text"):
                    val = random.choice(spec_pool)
                row[cname] = val
            rows.append(row)

    elif table == "gnuhealth_insurance":
        ins_parties = ctx["ins_party_ids"]
        for i in range(1, n + 1):
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = ins_parties[(i - 1) % len(ins_parties)]
                elif cname == "plan_id":
                    val = f"PLAN-{random.randint(10000, 99999)}" if ctype in ("character varying", "text") else None
                elif cname == "number":
                    val = f"POL{i:06d}"
                row[cname] = val
            rows.append(row)

    elif table == "gnuhealth_family":
        fam_names = ["Famille Rakoto Andrianina", "Famille Rabe Hantanirina"]
        for i in range(1, n + 1):
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = fam_names[i - 1]
                row[cname] = val
            rows.append(row)

    elif table == "gnuhealth_vegetarian_types":
        for i in range(1, n + 1):
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = VEGETARIAN_TYPES[(i - 1) % len(VEGETARIAN_TYPES)]
                row[cname] = val
            rows.append(row)

    elif table == "gnuhealth_diet_belief":
        for i in range(1, n + 1):
            row = {"id": i}
            for cname, ctype, samples in col_defs:
                if cname == "id":
                    continue
                val = gen_value(cname, ctype, samples)
                if cname == "name":
                    val = DIET_BELIEFS[(i - 1) % len(DIET_BELIEFS)]
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
    print(f"Lecture du rapport : {REPORT_PATH}")
    with open(REPORT_PATH, encoding="utf-8") as f:
        report = json.load(f)
    schemas = {entry["table_name"]: entry for entry in report}

    missing = [t for t in TABLE_ORDER if t not in schemas]
    if missing:
        sys.exit(f"❌ Tables absentes du rapport : {missing}")

    conn = psycopg2.connect(**PG)
    conn.autocommit = False
    cur = conn.cursor()
    total_rows = sum(VOLUMES.values())
    done = 0

    print(">>> Suppression des anciennes tables")
    cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")

    print(">>> Création des tables (schéma fidèle à l'ancien projet)")
    for table in TABLE_ORDER:
        cols = schemas[table]["columns"]
        defs = ", ".join(f'"{c["name"]}" {c["type"]}' for c in cols)
        cur.execute(f'CREATE TABLE "{table}" ({defs}, PRIMARY KEY ("id"))')
    print(f"    {len(TABLE_ORDER)} tables créées")

    # --- party_party d'abord : blocs d'ids par rôle ---
    n_prof = VOLUMES["gnuhealth_healthprofessional"]
    n_ins = VOLUMES["gnuhealth_insurance"]
    n_pat = VOLUMES["gnuhealth_patient"]
    ctx = {
        "prof_party_ids": list(range(1, n_prof + 1)),
        "ins_party_ids": list(range(n_prof + 1, n_prof + n_ins + 1)),
        "patient_party_ids": list(range(n_prof + n_ins + 1, n_prof + n_ins + n_pat + 1)),
        "family_ids": list(range(1, VOLUMES["gnuhealth_family"] + 1)),
        "veg_ids": list(range(1, VOLUMES["gnuhealth_vegetarian_types"] + 1)),
    }
    ctx["all_party_ids"] = list(range(1, VOLUMES["party_party"] + 1))

    for table in TABLE_ORDER:
        n = VOLUMES[table]
        print(f">>> {table:<30} génération de {n:>6} lignes...", flush=True)
        rows = build_table_rows(table, schemas[table]["columns"], ctx)
        insert_rows(cur, table, schemas[table]["columns"], rows)
        done += n
        print(f"    insérées ✔ ({done}/{total_rows})")

    print(">>> Ajout des clés étrangères")
    fk_sql = []
    for child, col, parent, pcol in FOREIGN_KEYS:
        fk_sql.append(
            f'ALTER TABLE "{child}" ADD CONSTRAINT "fk_{child}_{col}" '
            f'FOREIGN KEY ("{col}") REFERENCES "{parent}"("{pcol}")'
        )
    for stmt in fk_sql:
        cur.execute(stmt)

    conn.commit()

    print("\n=== Vérification des volumes ===")
    for table in TABLE_ORDER:
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        real = cur.fetchone()[0]
        flag = "OK " if real == VOLUMES[table] else "⚠️ "
        print(f"  {flag}{table:<32} {real:>6} / {VOLUMES[table]}")

    cur.close()
    conn.close()
    print(f"\n✅ Base mmt_db reconstruite ({done} lignes au total)")


if __name__ == "__main__":
    main()

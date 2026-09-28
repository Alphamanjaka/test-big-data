#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_clinique_sqlite.py
==========================
Crée / régénère la base SQLite `clinique.db` utilisée comme NOUVELLE SOURCE
de données du Data Lake (source "CLINIQUE"), indépendante de MAVIS et MMT_DB.

4 tables alignées sur les 4 entités FHIR (SILVER) :
    - patients      (Patient)     -> main_table
    - visits        (Encounter)   -> patient_id
    - diagnoses     (Condition)   -> patient_id
    - observations  (Observation) -> patient_id

Données synthétiques réalistes (identités malgaches, CIM-10, FK cohérentes),
à un ordre de grandeur proche des autres sources (~9 800 patients).

Usage (hôte Windows, sqlite3 stdlib) :
    python provision/db/rebuild_clinique_sqlite.py
"""

import os
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(BASE_DIR, "db", "data")
DB_PATH = os.path.join(DB_DIR, "clinique.db")
CIM10_PATH = os.path.join(BASE_DIR, "config", "cim10_liste.csv")

random.seed(7)

VOLUMES = {
    "patients": 9791,
    "visits": 20000,
    "diagnoses": 15000,
    "observations": 9791,
}

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
]
CITIES = ["Antananarivo", "Toamasina", "Mahajanga", "Fianarantsoa", "Antsirabe"]
VISIT_TYPES = ["consultation", "hospitalisation", "urgence", "suivi"]
DIAG_CATEGORIES = ["maladie", "symptome", "chronique", "aigu"]


def malagasy_full_name(gender=None):
    g = gender or random.choice(["m", "f"])
    first = random.choice(NAMES_M if g == "m" else NAMES_F)
    return f"{random.choice(LAST_NAMES)} {first}".strip()


def rand_date(start_year=1940, end_year=2016):
    return date(start_year, 1, 1) + timedelta(days=random.randint(0, 365 * (end_year - start_year)))


def rand_ts_date():
    return (datetime(2013, 1, 1) + timedelta(seconds=random.randint(0, 4 * 365 * 24 * 3600))).date()


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


def build_patients(n):
    rows = []
    for i in range(1, n + 1):
        g = random.choice(["m", "f"])
        rows.append((
            i,
            malagasy_full_name(g),
            g,
            rand_date().isoformat(),
            f"03{random.choice(['2', '3', '4'])} {random.randint(10, 99)} {random.randint(100, 999)} {random.randint(100, 999)}",
            f"{random.choice(NAMES_M).lower()}.{random.choice(LAST_NAMES).lower()}@example.mg",
            f"Lot {random.randint(1, 999)} II{random.choice(['A', 'B', 'C', 'D', 'E'])}{random.randint(1, 99)}",
            random.choice(CITIES),
        ))
    return rows


def build_visits(n, patient_ids):
    rows = []
    for i in range(1, n + 1):
        adm = rand_ts_date()
        dur = random.randint(0, 15)
        dis = adm + timedelta(days=dur)
        rows.append((
            i,
            random.choice(patient_ids),
            adm.isoformat(),
            dis.isoformat(),
            adm.isoformat(),
            random.choice(VISIT_TYPES),
        ))
    return rows


def build_diagnoses(n, patient_ids):
    rows = []
    for i in range(1, n + 1):
        code, libelle = CIM10[(i - 1) % len(CIM10)]
        rows.append((
            i,
            random.choice(patient_ids),
            libelle,
            code,
            random.choice(DIAG_CATEGORIES),
            code,
            libelle,
            libelle,
        ))
    return rows


def build_observations(n, patient_ids):
    rows = []
    for i in range(1, n + 1):
        rows.append((
            i,
            random.choice(patient_ids),
            random.randint(0, 1),
            random.randint(0, 6),
            random.randint(0, 6),
            random.randint(0, 6),
        ))
    return rows


def main():
    os.makedirs(DB_DIR, exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE patients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            gender TEXT,
            birth_date TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            city TEXT
        );

        CREATE TABLE visits (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            admission_date TEXT,
            discharge_date TEXT,
            create_date TEXT,
            visit_type TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE diagnoses (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            diagnosis TEXT,
            diagnosis_code TEXT,
            category TEXT,
            code TEXT,
            info TEXT,
            name TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE observations (
            id INTEGER PRIMARY KEY,
            patient_id INTEGER,
            mortality INTEGER,
            parity INTEGER,
            gravida INTEGER,
            live_births INTEGER,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );
    """)

    patient_ids = list(range(1, VOLUMES["patients"] + 1))

    print(">>> patients")
    cur.executemany("INSERT INTO patients VALUES (?,?,?,?,?,?,?,?)", build_patients(VOLUMES["patients"]))
    print(">>> visits")
    cur.executemany("INSERT INTO visits VALUES (?,?,?,?,?,?)", build_visits(VOLUMES["visits"], patient_ids))
    print(">>> diagnoses")
    cur.executemany("INSERT INTO diagnoses VALUES (?,?,?,?,?,?,?,?)", build_diagnoses(VOLUMES["diagnoses"], patient_ids))
    print(">>> observations")
    cur.executemany("INSERT INTO observations VALUES (?,?,?,?,?,?)", build_observations(VOLUMES["observations"], patient_ids))

    conn.commit()

    print("\n=== Vérification des volumes ===")
    total = 0
    for t in VOLUMES:
        cur.execute(f'SELECT COUNT(*) FROM {t}')
        real = cur.fetchone()[0]
        flag = "OK " if real == VOLUMES[t] else "⚠️ "
        print(f"  {flag}{t:<14} {real:>6} / {VOLUMES[t]}")
        total += real

    # FK integrity check
    cur.execute("PRAGMA foreign_key_check")
    fk_issues = cur.fetchall()
    if fk_issues:
        print(f"  ⚠️ Violations de FK : {len(fk_issues)}")
    else:
        print("  ✅ Aucune violation de FK")

    cur.close()
    conn.close()
    print(f"\n✅ Base SQLite clinique.db reconstruite ({total} lignes) : {DB_PATH}")


if __name__ == "__main__":
    main()

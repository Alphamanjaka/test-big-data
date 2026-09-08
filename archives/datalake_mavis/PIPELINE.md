# PIPELINE.md — Fonctionnement complet du pipeline DataLake Mavis

## Vue d'ensemble

Le pipeline ELT convertit des donnees medicales brutes issues de **2 bases PostgreSQL** en une table analytique **GOLD** prete pour le dashboard. L'architecture suit le modele **Medallion** (RAW, SILVER, GOLD) avec **PySpark + Hive** sur une VM Vagrant (Hadoop).

```
PostgreSQL (MAVIS, MMT_DB)
        |
        v
   [RAW Zone]  -->  [SILVER Zone]  -->  [GOLD Zone]  -->  [API Flask]  -->  [Next.js]
   (HDFS/Parquet)   (Hive FHIR)        (Hive Analytics)    (port 5000)      (port 3000)

   gen_extract_raw.py    create_silver.py     create_gold.py       hive_api.py
   gen_fhir_mapping.py
```

---

## Pre-requis

### Infrastructure

| Composant          | Role                                        |
| ------------------ | ------------------------------------------- |
| Vagrant + VMware   | VM isolee (192.168.56.1)                    |
| Java 8             | Runtime Hadoop/Hive/Spark                   |
| Hadoop 3.3.6       | HDFS (port 9000), YARN                      |
| Hive 3.1.3         | Metastore (thrift:9083), HiveServer2 (10000)|
| Spark 3.4.2        | Moteur de transformation, integree Hive     |
| Python 3 + venv    | Scripts ELT + API                           |

### Demarrage de l'environnement

```bash
# 1. Demarrer la VM
vagrant up

# 2. Demarrer les services big data (dans la VM)
start-dfs.sh
start-yarn.sh
# Hive Metastore + HiveServer2 (lances par bootstrap.sh au provisioning)
```

### Dependances Python

```bash
pip install pyspark sshtunnel paramiko flask flask-cors rapidfuzz pytz retrying
```

---

## Sources de donnees

Definies dans `provision/config/data_sources.json`.

> **Installation** : ce fichier contient des identifiants et n'est **pas committe** (ignore par git).
> Sur un nouveau clone : `cp provision/config/data_sources.example.json provision/config/data_sources.json`
> puis renseigner les identifiants. Les mots de passe restent surchargeables par variables
> d'environnement (`POSTGRES_PASSWORD_MAVIS`, `POSTGRES_PASSWORD_MMT_DB`).

### Source 1 : MAVIS

| Champ       | Valeur                                             |
| ----------- | -------------------------------------------------- |
| Type        | PostgreSQL distant                                 |
| Connexion   | SSH tunnel (102.16.7.154:8090 vers localhost:5432) |
| Base        | mavis_notheme                                      |
| Table principale | hms_patient                                   |
| Tables extraites | 11 (hms_patient, res_partner, hms_diseases, hr_employee, etc.) |

### Source 2 : MMT_DB

| Champ       | Valeur                                    |
| ----------- | ----------------------------------------- |
| Type        | PostgreSQL local                          |
| Connexion   | TCP direct (192.168.56.1:5432)            |
| Base        | mmt_db                                    |
| Table principale | gnuhealth_patient                     |
| Tables extraites | 3 (gnuhealth_patient, party_party, gnuhealth_family) |

> Les mots de passe sont dans `data_sources.json` ou surcharges par variables d'environnement (`POSTGRES_PASSWORD_MAVIS`, `POSTGRES_PASSWORD_MMT_DB`).

---

## Etapes du pipeline

### Etape 1/4 : Extraction RAW

**Script :** `provision/scripts/ELT/gen_extract_raw.py` (332 lignes)
**Execution :** `python3 -m provision.scripts.ELT.gen_extract_raw`

**Role :** Extraire les donnees brutes des sources PostgreSQL vers HDFS + creer des tables Hive externes.

#### Fonctionnement detaille

1. **Connexion**
   - Pour MAVIS : cree un tunnel SSH (3 tentatives, sshtunnel), puis JDBC via le port local
   - Pour MMT_DB : JDBC direct
   - Driver PostgreSQL : postgresql-42.7.3.jar

2. **Decouverte des tables** (via information_schema)
   - Liste toutes les tables/views du schema public
   - Detecte les cles etrangeres (information_schema.table_constraints)
   - Filtre les tables a extraire : table principale + tables reliees par FK

3. **Extraction parallele** (4 workers via ThreadPoolExecutor)
   - Pour chaque table :
     - Lecture complete via JDBC
     - Ecriture Parquet sur HDFS : `hdfs://localhost:9000/datalake/raw/{source}/{table}`
     - Creation d'une table Hive externe : `{source}.{table}` (type PostgreSQL via mapping pg_to_hive)
     - Collecte : schema, nombre de lignes, echantillon (5 lignes)

4. **Sorties**
   - `provision/metadata/extract_raw_report.json` — rapport complet
   - `provision/metadata/extract/{SOURCE}_extract_raw_report.json` — rapport par source
   - `provision/metadata/extract/{SOURCE}_failed_tables.json` — tables en echec
   - Mise a jour de `data_sources.json` (ajoute tables_to_detectees automatiquement)
   - Mise a jour de `sync_metadata.json` (zone RAW, status=ok)

#### Fichiers generes

```
hdfs://localhost:9000/datalake/raw/
  MAVIS/
    hms_patient/
    res_partner/
    hms_diseases/
    ... (11 tables)
  MMT_DB/
    gnuhealth_patient/
    party_party/
    gnuhealth_family/

provision/metadata/
  extract_raw_report.json
  sync_metadata.json
  extract/
    MAVIS_extract_raw_report.json
    MAVIS_failed_tables.json
    MMT_DB_extract_raw_report.json
    MMT_DB_failed_tables.json
```

---

### Etape 2/4 : Mapping FHIR

**Script :** `provision/scripts/ELT/gen_fhir_mapping.py` (171 lignes)
**Execution :** `python3 -m provision.scripts.ELT.gen_fhir_mapping`

**Role :** Generer la correspondance entre les colonnes PostgreSQL et le schema FHIR minimal.

#### Fonctionnement detaille

1. **Chargement**
   - `data_sources.json` (liste des sources et tables)
   - `extract_raw_report.json` (schema de chaque table extrait)

2. **Detection de l'entite FHIR** pour chaque table :
   - Table principale --> `Patient`
   - Nom contient `pathology/disease/diagnosis` --> `Condition`
   - Nom contient `observation/measurement/death/register/maternity` --> `Observation`
   - Nom contient `encounter/visit/consultation/admission` --> `Encounter`
   - Overrides manuels : `gnuhealth_family` --> Encounter, `party_party` --> Encounter, etc.

3. **Selection des colonnes** via :
   - Correspondance exacte (champ FHIR = nom colonne)
   - Dictionnaire de synonymes (`fhir_synonyms.py`) : birth_date equiv dob, birthday, bdate
   - Fallback : premiere colonne de la table

4. **Resolution de conflits** : si un nom de colonne apparait dans plusieurs tables, prefixe avec `table_name.colonne`

5. **Tri** : la table principale (main_table) est placee en premier dans le mapping

#### Schema FHIR cible (4 entites)

Defini dans `provision/scripts/utils/fhir_schema.py` :

| Entite     | Champs                                                                      |
| ---------- | --------------------------------------------------------------------------- |
| Patient    | patient_uuid, source_patient_id, name, birth_date, gender, address, phone, email |
| Encounter  | patient_uuid, encounter_id, admission_date, discharge_date, create_date, visit_type |
| Condition  | patient_uuid, diagnosis, diagnosis_code, category, code, info, name         |
| Observation| patient_uuid, mortality, parity, gravida, live_births                       |

#### Sortie

Fichier : `provision/metadata/fhir_mapping.json`

Format :

```json
{
  "MAVIS": {
    "Patient": {
      "hms_patient": ["hms_patient.id", "hms_patient.name", "res_partner.gender"],
      "res_partner": ["res_partner.phone", "res_partner.email"]
    },
    "Encounter": { "..." },
    "Condition": { "..." },
    "Observation": { "..." }
  },
  "MMT_DB": { "..." }
}
```

---

### Etape 3/4 : Transformation SILVER

**Script :** `provision/scripts/ELT/create_silver.py` (375 lignes)
**Execution :** `python3 -m provision.scripts.ELT.create_silver`

**Role :** Transformer les donnees RAW en tables FHIR harmonisees dans la zone SILVER.

#### Fonctionnement detaille

1. **Lecture du mapping** (`fhir_mapping.json`)

2. **Boucle** sur chaque source x entite x table :
   - **Lecture securisee** de la table RAW (3 fallbacks) :
     1. Table Hive `{source}.{table}`
     2. Table Hive `{table}`
     3. Fichier Parquet `/datalake/raw/{source}/{table}`
   - Gestion des erreurs FIXED_LEN_BYTE_ARRAY (cast automatique en String)

3. **Mapping dynamique** :
   - Pour chaque champ FHIR, trouve la meilleure colonne source via :
     - Synonymes courts (birth_date equiv dob, bdate, birthday)
     - Fuzzy matching (RapidFuzz, seuil 60%)
   - Detection automatique de la cle primaire (patient_id, id, etc.)

4. **Renommage** : colonnes renommees en convention `fhir__{champ}`

5. **Cast type** selon FHIR_FIELDS :
   - date --> to_date()
   - int --> IntegerType()
   - double/float --> DoubleType()
   - Autres --> StringType()

6. **Union** des tables d'une meme entite via unionByName() (colonnes manquantes = NULL)

7. **Post-traitement Patient** :
   - Prefixe source au source_patient_id : `MAVIS_123`, `MMT_DB_456`
   - Generation patient_uuid : `SHA-256(source + "|" + source_patient_id)`

8. **Normalisation du genre** (GENDER_MAP) :
   - m/h/homme/male --> male
   - f/femme/female --> female

9. **Detection des doublons** (Patient uniquement) :
   - Window sur (name, birth_date, gender)
   - Colonne booleenne `is_duplicate` = true si compteur > 1

10. **Ecriture Hive** :
    - 1ere source : overwrite (idempotence)
    - Sources suivantes : append (fusion multi-sources)
    - Tables : `datalake_silver.{entity}_fhir`

#### Tables SILVER generees

| Table | Contenu |
| ----- | ------- |
| `datalake_silver.patient_fhir` | Patients unifies, genre normalise, doublons flagges |
| `datalake_silver.encounter_fhir` | Consultations/hospitalisations |
| `datalake_silver.condition_fhir` | Diagnostics CIM-10 |
| `datalake_silver.observation_fhir` | Indicateurs (mortalite, parite, gravida) |

#### Colonnes Silver (exemple Patient)

| Colonne | Type | Description |
| ------- | ---- | ----------- |
| patient_uuid | STRING | UUID unique (SHA-256) |
| source_patient_id | STRING | ID source prefixed (MAVIS_123) |
| name | STRING | Nom complet |
| birth_date | DATE | Date de naissance |
| gender | STRING | male / female (normalise) |
| address | STRING | Adresse |
| phone | STRING | Telephone |
| email | STRING | Email |
| is_duplicate | BOOLEAN | true si doublon detecte |
| _source_table | STRING | Table d'origine |

---

### Etape 4/4 : Table GOLD

**Script :** `provision/scripts/ELT/create_gold.py` (181 lignes)
**Execution :** `python3 -m provision.scripts.ELT.create_gold`

**Role :** Produire une table denormalisee et agreggee pour le dashboard.

#### Fonctionnement detaille

1. **Lecture** des 4 tables SILVER (via Hive)

2. **Reduction** des colonnes pour eviter les conflits (AMBIGUOUS_REFERENCE)

3. **Calcul de l'age** :
   - age = (current_date - birth_date) / 365.25
   - age_tranche via UDF avec 8 tranches RMA :

| Tranche | Plage |
| ------- | ----- |
| 0-28 j | Nouveau-nes < 28 jours |
| 29-59 j | 29 a 59 jours |
| 2-11 m | 2 a 11 mois |
| 1-4 ans | 1 a 4 ans |
| 5-14 ans | 5 a 14 ans |
| 15-24 ans | 15 a 24 ans |
| 25-59 ans | 25 a 59 ans |
| 60 ans et plus | 60 ans et plus |

4. **Jointures** LEFT JOIN sur patient_uuid :
   - Encounter LEFT JOIN Patient
   - Result LEFT JOIN Condition
   - Result LEFT JOIN Observation

5. **Deduplication** : dropDuplicates sur (patient_uuid, encounter_id, diagnosis_code)

6. **Ecriture** : `datalake_gold.patient_events_gold` (mode overwrite)

#### Table GOLD generee

`datalake_gold.patient_events_gold` — 17 colonnes :

| Colonne | Type | Description |
| ------- | ---- | ----------- |
| patient_uuid | STRING | UUID patient |
| source_patient_id | STRING | ID source |
| name | STRING | Nom |
| gender | STRING | Genre |
| birth_date | DATE | Date de naissance |
| age | DOUBLE | Age en annees |
| age_tranche | STRING | Tranche d'age RMA |
| encounter_id | STRING | ID consultation |
| admission_date | DATE | Date d'entree |
| discharge_date | DATE | Date de sortie |
| visit_type | STRING | Type de visite |
| diagnosis_code | STRING | Code CIM-10 |
| category | STRING | Categorie diagnostic |
| diagnosis | STRING | Libelle diagnostic |
| mortality | INT | Mortalite (0/1) |
| parity | INT | Parite |
| gravida | INT | Gravida |
| live_births | INT | Enfants vivants |

---

## Orchestration

### Script principal : run_pipeline.sh

**Fichier :** `provision/scripts/run_pipeline.sh`

Lance les 4 etapes sequentiellement depuis la racine du projet. Arrete le pipeline en cas d'erreur sur une etape.

```bash
cd /home/vagrant/datalake-mavis
bash provision/scripts/run_pipeline.sh
```

Les logs sont rediriges vers `provision/logs/elt.log`.

### Fichier de suivi : sync_metadata.json

Mis a jour a la fin de chaque etape par `sync_utils.py`. Contient le timestamp (UTC+3) et le statut de chaque zone.

```json
{
  "RAW": { "last_sync": "2026-08-28T09:52:18+03:00", "status": "ok" },
  "SILVER": { "last_sync": "2026-08-28T09:55:02+03:00", "status": "ok" },
  "GOLD": { "last_sync": "2026-08-28T09:57:45+03:00", "status": "ok" }
}
```

### Flux de fichiers intermediaires

```
data_sources.json ─────────────> [Step 1] ──> extract_raw_report.json
                                              data_sources.json (mis a jour)
                                                     |
                                                     v
                                        [Step 2] ──> fhir_mapping.json
                                                     |
                                                     v
                                        [Step 3] ──> Hive datalake_silver.*_fhir
                                              sync_metadata.json (SILVER)
                                                     |
                                                     v
                                        [Step 4] ──> Hive datalake_gold.patient_events_gold
                                              sync_metadata.json (GOLD)
```

---

## Couche API

**Script :** `provision/api/hive_api.py` (378 lignes)
**Execution :** `python3 provision/api/hive_api.py` (Flask, port 5000)

Lecture de `datalake_gold.patient_events_gold` via PySpark/Hive. Fallback sur donnees mock si la table GOLD est vide (variable `RMA_USE_MOCK`).

### Endpoints

| Endpoint | Donnee |
| -------- | ------ |
| GET /rma/last_sync | Timestamps de synchro (sync_metadata.json) |
| GET /rma/admissions_summary | Resume admissions |
| GET /rma/top_diagnostics | Top diagnostics CIM-10 |
| GET /rma/diagnostics_heatmap | Heatmap tranches d'age x diagnostics |
| GET /rma/diagnostics_list | Liste diagnostiques (paginee) |
| GET /api/rma/mortality | Donnees mortalite |
| GET /api/rma/maternity | Donnees maternite (mensuelles) |
| GET /api/rma/laboratory | Examen labo (mock uniquement) |
| GET /api/rma/malaria | KPI paludisme (mock uniquement) |

---

## Fichiers utilitaires

| Fichier | Role |
| ------- | ---- |
| `provision/scripts/utils/fhir_schema.py` | Definition des 4 entites FHIR et leurs types |
| `provision/scripts/utils/fhir_synonyms.py` | Dictionnaire de synonymes pour le matching colonnes |
| `provision/scripts/utils/sync_utils.py` | Gestion de sync_metadata.json (timestamps UTC+3) |
| `provision/config/data_sources.json` | Configuration des sources PostgreSQL |
| `provision/db/rebuild_mmt_db.py` | Generateur de donnees synthetiques pour MMT_DB |

---

## Problemes connus

1. **Gender NULL pour MMT_DB** : la table gnuhealth_patient n'a pas de colonne gender mappee
2. **Encounters/Conditions sans patient_uuid** : le mapping FHIR ne reussit pas toujours a lier les entites aux patients via FK
3. **Laboratory et Malaria** : retournent uniquement des donnees mock (pas encore dans GOLD)
4. **MAVIS res_partner.gender** : les donnees reelles ont souvent des champs gender vides

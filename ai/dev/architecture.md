# Architecture & Système (consignes)

Source : fusion des `.ai_context/01_architecture.md` (Mavis) et consignes d'architecture du moteur.

## 1. Contexte

Plateforme Big Data de gestion et de gouvernance de données patients synthétiques pour MMT. Deux volets
cohabitent : **pipeline Medallion** (RAW→SILVER→GOLD, Hive/HDFS/Spark) et **moteur de déduplication +
gouvernance** (`engine/`, PostgreSQL central).

## 2. Stack stricte

- Pipeline (VM Ubuntu 20.04, Python 3.8 système `/usr/bin/python3`) : **PySpark 3.4.2**, **Hive 3.1.3**,
  **Hadoop 3.3.6** (Java 8), RapidFuzz + synonymes pour le mapping FHIR.
- API données : **Flask 3.0.3** + PySpark, venv `~/api-venv` de la VM, port 5000.
- Moteur : Python 3.8+ (Pandas + PySpark), RapidFuzz, SQLAlchemy/psycopg + PostgreSQL central.
- Frontend (optionnel) : Next.js 15 (App Router), React 19, TypeScript, Tailwind 4, D3.js 7, shadcn/ui,
  next-auth 4 + Prisma 6 (`datalake_user_db`).
- Interopérabilité : schéma pivot **FHIR** (4 entités) côté Data Lake ; modèle **canonique**
  (`CanonicalPatient`) côté moteur.
- Interdiction : `sentence_transformers` (crash Python 3.8).

## 3. Ports & ordre de démarrage (VM)

| Service | Port | Note |
|---|---|---|
| HDFS NameNode | 9000 | `start-dfs.sh` en premier |
| YARN | 8088 | `start-yarn.sh` ensuite |
| Hive Metastore | 9083 | DISTANTE (bug Derby sinon) |
| HiveServer2 | 10000 | `beeline -u jdbc:hive2://localhost:10000 -n vagrant` |
| API Flask | 5000 | `python -m provision.api.hive_api` (CORS localhost:3000) |
| Frontend Next.js | 3000 | hôte Windows |

**Ordre STRICT** : `start-dfs.sh` → `start-yarn.sh` → metastore → HiveServer2 → jobs Spark/API.
PostgreSQL hôte (Laragon) n'est pas un service Windows : `pg_ctl -D C:\laragon\data\postgresql start` après reboot.

## 4. Sources de données

| Source | Base | Connexion |
|---|---|---|
| MAVIS | mavis_notheme | SSH tunnel (102.16.7.154:8090) + JDBC, ou réplique locale Laragon (`rebuild_mavis_db.py`, 73 090 lignes) |
| MMT_DB | mmt_db | TCP direct (192.168.56.1:5432), base synthétique recréée (`rebuild_mmt_db.py`) |
| CLINIQUE | clinique.db | SQLite local (4 tables FHIR) |
| Plateforme | CSV synthétiques | `synthetic-patient-generator` (pharmacy, consultation, imaging) |

Config : `provision/config/data_sources.json` (**non committé**, secrets) — template
`data_sources.example.json`, mots de passe surchargés par env `POSTGRES_PASSWORD_<SOURCE>`.

## 5. Zones et schémas pivots

### Data Lake (Hive)

- **SILVER** (`datalake_silver.*_fhir`) :
  - Patient : patient_uuid (SHA-256), source_patient_id, name, birth_date, gender, address, phone, email
    (+ is_duplicate, _source_table)
  - Encounter : patient_uuid, encounter_id, admission_date, discharge_date, create_date, visit_type
  - Condition : patient_uuid, diagnosis, diagnosis_code, category, code, info, name
  - Observation : patient_uuid, mortality, parity, gravida, live_births
- **GOLD** : `datalake_gold.patient_events_gold` — 17 colonnes (patient_uuid, source_patient_id, name,
  gender, birth_date, age, age_tranche[8 RMA], encounter_id, admission_date, discharge_date, visit_type,
  diagnosis_code, category, diagnosis, mortality, parity, gravida, live_births).

### PostgreSQL central (`projet/code-source/sql/schema.sql`)

```text
raw_patient_record · master_patient (+gender) · patient_identity_map · consent · api_user · access_audit
```

## 6. Répertoires clés

```
projet/code-source/
├── provision/scripts/ELT/    ← gen_extract_raw, gen_fhir_mapping, create_silver, create_gold
├── provision/scripts/utils/  ← fhir_schema.py, fhir_synonyms.py, sync_utils.py
├── provision/api/            ← hive_api.py, mock_data.py, test_api.py
├── provision/config/         ← data_sources.json (non committé) + data_sources.example.json
├── provision/metadata/       ← artefacts générés (non committés)
├── engine/identity/          ← canonical.py, matcher.py, spark_dedup.py
├── engine/governance/        ← database.py, auth.py, consent.py, audit.py
├── evaluation/               ← generateur + evaluate_engine.py + truth
├── tests/                    ← test_matcher.py, test_consent.py
├── sql/schema.sql            ← schéma PostgreSQL central
└── front-optional/           ← Next.js (optionnel)
```

Ne jamais commiter : `data_sources.json`, `.env`, `provision/metadata/`, `data/`, `*.db`, venv, node_modules, .next.
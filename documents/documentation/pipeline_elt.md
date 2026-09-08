# Pipeline ELT — fonctionnement complet

Le pipeline ELT convertit des données médicales synthétiques issues de **3 sources** (PostgreSQL MAVIS,
PostgreSQL MMT_DB, SQLite CLINIQUE) en une table analytique **GOLD** prête pour l'API/le dashboard.
Architecture **Medallion** (RAW → SILVER → GOLD) avec **PySpark + Hive** sur la VM Vagrant (Hadoop).

```
PostgreSQL (MAVIS, MMT_DB) + SQLite (CLINIQUE)
        |
        v
   [RAW Zone]  -->  [SILVER Zone]  -->  [GOLD Zone]  -->  [API Flask]  -->  [Web]
   (HDFS/Parquet)   (Hive FHIR)        (Hive Analytics)    (port 5000)      (optionnel)

   gen_extract_raw.py   create_silver.py    create_gold.py       hive_api.py
   gen_fhir_mapping.py
```

Orchestration : `bash provision/scripts/run_pipeline.sh` (4 étapes séquentielles, arrêt sur erreur).
Logs : `provision/logs/elt.log`. Suivi : `provision/metadata/sync_metadata.json` (UTC+3).

## Environnement

| Composant | Rôle |
|---|---|
| Vagrant + VirtualBox | VM isolée (ubuntu/focal64, 8 Go, 192.168.56.1) |
| Java 8 | Runtime Hadoop/Hive/Spark |
| Hadoop 3.3.6 | HDFS (port 9000), YARN (8088) |
| Hive 3.1.3 | Metastore (9083), HiveServer2 (10000) |
| Spark 3.4.2 | Moteur de transformation, Hive intégré |
| Python 3 venv | Scripts ELT + API |

```bash
vagrant up && vagrant ssh
start-dfs.sh; start-yarn.sh      # HDFS puis YARN
# metastore (9083) + HiveServer2 (10000) lancés par bootstrap.sh
```

## Étape 1/4 — Extraction RAW

`python3 -m provision.scripts.ELT.gen_extract_raw` — `gen_extract_raw.py`

1. **Connexion** : MAVIS via tunnel SSH (3 tentatives, sshtunnel) puis JDBC ; MMT_DB en JDBC direct ;
   CLINIQUE via lecture SQLite (`discover_sqlite`). Driver `postgresql-42.7.3.jar`.
2. **Découverte** (`information_schema`) : tables/views du schéma public, clés étrangères, filtrage des
   tables reliées par FK à la table principale.
3. **Extraction parallèle** (4 workers) : lecture JDBC → Parquet HDFS
   `hdfs://localhost:9000/datalake/raw/{source}/{table}` + table Hive externe `{source}.{table}`
   (type PostgreSQL via mapping `pg_to_hive`) + collecte du schéma/compte/échantillon.
4. **Sorties** : `provision/metadata/extract_raw_report.json`, rapports par source et échecs ;
   `data_sources.json` mis à jour (`tables_to_detectees`) ; `sync_metadata.json` (RAW, status ok).

## Étape 2/4 — Mapping FHIR

`python3 -m provision.scripts.ELT.gen_fhir_mapping` — `gen_fhir_mapping.py`

1. Lit `data_sources.json` + `extract_raw_report.json`.
2. **Détection de l'entité FHIR** par table : principale → `Patient` ; `pathology/disease/diagnosis` →
   `Condition` ; `observation/measurement/death/register/maternity` → `Observation` ;
   `encounter/visit/consultation/admission` → `Encounter` ; surcharges manuelles (`gnuhealth_family`,
   `party_party` → Encounter).
3. **Sélection des colonnes** : correspondance exacte → synonymes (`fhir_synonyms.py`) → fuzzy
   (RapidFuzz, seuil 60 %) → première colonne.
4. **Conflits** : préfixe `table.column` si le nom de colonne apparaît dans plusieurs tables ;
   la table principale sort en premier.
5. **Sortie** : `provision/metadata/fhir_mapping.json`.

## Étape 3/4 — Transformation SILVER

`python3 -m provision.scripts.ELT.create_silver` — `create_silver.py`

1. Lecture du mapping puis boucle source × entité × table avec **lecture sécurisée** :
   table Hive `{source}.{table}` → table Hive `{table}` → Parquet. Gestion de l'erreur
   `FIXED_LEN_BYTE_ARRAY` (cast String des colonnes binary/decimal).
2. **Mapping dynamique** : meilleure colonne source par champ FHIR (synonymes courts + RapidFuzz) ;
   détection auto de la clé primaire. Renommage en convention `fhir__{champ}`.
3. **Cast types** selon `FHIR_FIELDS` : date → `to_date()`, int → `IntegerType()`, double → `DoubleType()`,
   autres → `StringType()`.
4. **Union** des tables d'une même entité via `unionByName()` (colonnes manquantes = NULL).
5. **Post-traitement Patient** :
   - `source_patient_id` préfixé (`MAVIS_123`, `MMT_DB_456`) ;
   - `patient_uuid` = `SHA-256(source + "|" + source_patient_id)` ;
   - genre normalisé (`GENDER_MAP` : m/h/homme/male → male ; f/femme/female → female).
6. **Doublons Patient — master patient explicable (moteur engine)** : après la boucle,
   `enrichir_dedup_moteur()` relit `patient_fhir`, reconstruit les patients canoniques
   (`engine.identity`) et applique `deduplicate()` (exact → probabiliste, seuil 0.80).
   Colonnes ajoutées : `master_patient_id` (PAT-xxxx), `match_method` (`new_master`/`exact`/`probabilistic`),
   `match_score` ; `is_duplicate` recalculé (une seule occurrence = master). Si le moteur est
   indisponible, le flag brut (Window `partitionBy(name, birth_date, gender)`) est conservé.
7. **Écriture Hive** : 1re source `overwrite`, suivantes `append` (idempotence multi-source — CRITIQUE).
   Tables : `datalake_silver.{entity}_fhir`.

| Table | Contenu |
|---|---|
| `datalake_silver.patient_fhir` | Patients unifiés, genre normalisé, doublons flaggés + `master_patient_id`/`match_method`/`match_score` |
| `datalake_silver.encounter_fhir` | Consultations / hospitalisations |
| `datalake_silver.condition_fhir` | Diagnostics CIM-10 |
| `datalake_silver.observation_fhir` | Indicateurs (mortalité, parité, gravida) |

## Étape 4/4 — Table GOLD

`python3 -m provision.scripts.ELT.create_gold` — `create_gold.py`

1. Lecture des 4 tables SILVER (via Hive).
2. **Réduction des colonnes** AVANT jointures (évite `AMBIGUOUS_REFERENCE: name`).
3. **Âge** : `age = (current_date - birth_date) / 365.25` ; `age_tranche` via UDF (8 tranches RMA) :

| Tranche | Plage |
|---|---|
| 0-28 j | Nouveau-nés < 28 jours |
| 29-59 j | 29 à 59 jours |
| 2-11 m | 2 à 11 mois |
| 1-4 ans | 1 à 4 ans |
| 5-14 ans | 5 à 14 ans |
| 15-24 ans | 15 à 24 ans |
| 25-59 ans | 25 à 59 ans |
| 60+ | 60 ans et plus |

   (gérer `age` NULL → `"unknown"`).
4. **Jointures** LEFT JOIN sur `patient_uuid` : Encounter → Patient → Condition → Observation.
5. **Déduplication** : `dropDuplicates(patient_uuid, encounter_id, diagnosis_code)`.
6. **Consentement GOLD** : `charger_consent_gold()` alimente `datalake_gold.patient_consent_gold`
   depuis le PostgreSQL central (`engine/governance`, table `consent`) joint aux masters SILVER
   (`master_patient_id`, `patient_uuid`, `name`). Sans `DATABASE_URL` ou si PostgreSQL inaccessible,
   le schéma est créé vide → l'API bascule en fallback mock.
7. **Écriture** : `datalake_gold.patient_events_gold` + `datalake_gold.patient_consent_gold`
   (overwrite). Sortie : `sync_metadata.json` (GOLD).

## Flux des fichiers intermédiaires

```
data_sources.json ─> [Step 1] ─> extract_raw_report.json + data_sources.json (à jour)
                                     │
                                     v
                               [Step 2] ─> fhir_mapping.json
                                     │
                                     v
                               [Step 3] ─> Hive datalake_silver.*_fhir (+ master_patient_id)
                               sync_metadata.json (SILVER) ─> [Step 4] ─> datalake_gold.patient_events_gold
                               PostgreSQL consent ───────────> [Step 4] ─> datalake_gold.patient_consent_gold
                               sync_metadata.json (GOLD)
```

## Utilitaires

| Fichier | Rôle |
|---|---|
| `provision/scripts/utils/fhir_schema.py` | Définition des 4 entités FHIR et leurs types |
| `provision/scripts/utils/fhir_synonyms.py` | Dictionnaire de synonymes pour le matching colonnes |
| `provision/scripts/utils/sync_utils.py` | Gestion de `sync_metadata.json` (timestamps UTC+3) |
| `provision/config/data_sources.json` | Configuration des sources (non commité) |
| `provision/db/rebuild_mmt_db.py` | Générateur de données synthétiques pour MMT_DB |
| `provision/scripts/run_pipeline.sh` | Orchestration 4 étapes + logs |

## Pièges connus (règles anti-régression)

1. **Pas d'`overwrite` dans la boucle par source** — accumulation par entité puis **une seule écriture**
   `mode="overwrite"` par table cible (sinon listing périmé overwrite+append dans la même session).
2. **`patient_uuid` exclu du mapping FHIR dynamique** — `meilleure_colonne_attendue("patient_uuid", …)`
   peut détourner une colonne ID source (`client_id`/`patient_code`/`patient_name`) → `source_patient_id`
   NULL → préfixe source seul → jointure moteur en croisement « 76×76 ». Colonnes source renommées
   **une seule fois** (garde-fou `colonnes_source_utilisees`).
3. **Pas d'overwrite d'une table en cours de lecture** (`Cannot overwrite table that is also being read`) —
   écrire l'enrichissement dans `patient_fhir__dedup_tmp` puis `DROP TABLE` + `ALTER TABLE … RENAME TO`.
4. **Warehouse Spark sur HDFS** uniquement (`hdfs://localhost:9000/datalake/{silver|gold}/warehouse`).
5. `hive.metastore.uris=thrift://localhost:9083` (métastore distante, sinon conflit Derby).
6. Si une ancienne base GOLD existe en local : `DROP DATABASE datalake_gold CASCADE` avant reconfiguration.
7. **Interdiction** : `sentence_transformers` (crash Python 3.8).
8. Mémoire Spark : executor 4g / driver 2g / `shuffle.partitions=8`.

## Validation VM (interim CSV, 07/09/2026)

`run_pipeline.sh` → **4/4 vert**. Comptages contrôlés par `provision/metadata/check_data.py` (scripts Spark ;
beeline HS2 instable dans la VM, contourné) :

| Table | Comptage |
|---|---|
| `datalake_silver.patient_fhir` | **214** lignes (76 pharmacy + 76 consultation + 62 imaging) |
| masters distincts | 145 |
| doublons (`is_duplicate`, méthode `exact`) | 69 |
| `match_method` | exact 69 / new_master 145 ; `match_score` 1.0 |
| `datalake_gold.patient_events_gold` | 0 (patients-only, attendu) |
| `datalake_gold.patient_consent_gold` | 145 |

## Problèmes connus (dettes qualité)

- Gender NULL pour MMT_DB (gnuhealth_patient sans colonne gender mappée).
- Encounters/Conditions sans `patient_uuid` : liens FK à enrichir (interim patients-only → `patient_events_gold` vide).
- Laboratory et Malaria : données uniquement mock (sources hors GOLD).
- Consentement PostgreSQL non alimenté en interim → `patient_consent_gold` construit depuis les masters SILVER
  (`granted`/`purpose` NULL) ; endpoints duplicates/consent servis hors mock (`mocked: false`).
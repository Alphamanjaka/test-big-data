# Consignes pipeline ELT & Big Data

Source : fusion de `.ai_context/02_pipeline_elt.md` (Mavis) + consignes pipeline.

## 1. Architecture Medallion

- **RAW (Bronze)** : extraction PostgreSQL/SQLite → Parquet HDFS (`/datalake/raw/{source}/{table}`) +
  tables Hive externes `{source}.{table}`.
- **SILVER (Argent)** : 4 tables Hive harmonisées FHIR (`datalake_silver.*_fhir`). Genre normalisé
  (male/female), flag `is_duplicate`.
- **GOLD (Or)** : `datalake_gold.patient_events_gold` — préparation pour l'API/la visualisation.

## 2. Étapes et orchestration (4/4)

| Étape          | Script                                      | Entrée → Sortie                                                              |
| -------------- | ------------------------------------------- | ---------------------------------------------------------------------------- |
| 1/4 Extraction | `provision/scripts/ELT/gen_extract_raw.py`  | `data_sources.json` → Parquet HDFS, Hive externes, `extract_raw_report.json` |
| 2/4 Mapping    | `provision/scripts/ELT/gen_fhir_mapping.py` | `extract_raw_report.json` → `fhir_mapping.json` (RapidFuzz + synonymes)      |
| 3/4 Silver     | `provision/scripts/ELT/create_silver.py`    | `fhir_mapping.json` + RAW → `datalake_silver.*_fhir`                         |
| 4/4 Gold       | `provision/scripts/ELT/create_gold.py`      | 4 tables Silver → `datalake_gold.patient_events_gold`                        |

Depuis la racine projet (imports relatifs obligent le `-m`) :

```bash
bash provision/scripts/run_pipeline.sh               # les 4 étapes, arrêt sur erreur
python3 -m provision.scripts.ELT.create_gold         # étape seule
```

Logs : `provision/logs/elt.log` · Suivi : `provision/metadata/sync_metadata.json` (UTC+3, `utils/sync_utils.py`).

## 3. Directives de codage PySpark — règles Silver

- **Idempotence multi-source (CRITIQUE)** : 1re écriture d'une table = `mode("overwrite")`, sources
  suivantes = `append` (set `tables_ecrites`). Écrire `overwrite` DANS la boucle = la dernière source
  écrase les autres (incident log n°11).
- **`patient_uuid`** = `sha2(concat(source, '|', source_patient_id), 256)` ; `source_patient_id` préfixé
  (ex `MAVIS_123`).
- **Genre** `GENDER_MAP` : m/h/homme/male → male ; f/femme/female → female (inconnues conservées en minuscule).
- **Doublons** : Window `partitionBy(name, birth_date, gender)` → `is_duplicate = count > 1`.
  En fusion : enrichir avec le moteur (`master_patient_id`, `match_method`, `match_score`).
- **Traçabilité** : colonne `_source_table` + `update_sync_metadata("<ZONE>")` en fin de script.
- **Union** entre tables d'une même entité : `unionByName()` (colonnes manquantes = NULL), pas de join dynamique.
- **Lectures RAW robustes** : fallbacks Hive `{src}.{table}` → Hive `{table}` → Parquet ; gérer
  `FIXED_LEN_BYTE_ARRAY` (cast String des colonnes binary/decimal).
- **GOLD** : réduire explicitement les colonnes AVANT jointures (sinon `AMBIGUOUS_REFERENCE: name`),
  tranches d'âge RMA via UDF, `age` NULL → `"unknown"`.

## 4. Optimisation VM (8 Go) — dans CHAQUE session Spark

```python
.config("spark.executor.memory", "4g")
.config("spark.driver.memory", "2g")
.config("spark.sql.shuffle.partitions", "8")
```

**WAREHOUSE OBLIGATOIRE SUR HDFS** (jamais vboxsf) :

```python
.config("spark.sql.warehouse.dir", "hdfs://localhost:9000/datalake/{silver|gold}/warehouse")
```

## 5. Pièges connus

- Driver JDBC : `provision/jars/postgresql-42.7.3.jar` (copié dans `$SPARK_HOME/jars` par bootstrap.sh).
- Tunnel MAVIS : `sshtunnel` + 3 retries ; MMT_DB en connexion directe (try/except par source).
- `hive-site.xml` → `hive.metastore.uris=thrift://localhost:9083` (métastore DISTANTE, sinon conflit Derby).
- Ancienne base GOLD locale : `DROP DATABASE datalake_gold CASCADE` avant reconfigurer le warehouse.
- **Interdiction** : `sentence_transformers`.

Détails : `documents/documentation/pipeline_elt.md`.

## Performance et capacité

Toute mesure de pipeline doit conserver : durée par étape, volume en entrée et en sortie, nombre de
partitions, mémoire observée ou configurée, erreurs et environnement d'exécution. Utiliser au moins
trois scénarios de charge (petit, moyen, grand) lorsque les données le permettent.

Comparer Pandas et Spark sur un jeu identique seulement si le périmètre, les résultats et la méthode de
mesure sont identiques. Documenter séparément l'optimisation de la VM 8 Go et la scalabilité distribuée.
Pour la déduplication, mesurer l'effet du blocking sur le nombre de candidats et expliquer pourquoi une
comparaison naïve O(n²) ne convient pas lorsque le volume augmente. Ne fixer aucun seuil de performance
sans mesure reproductible et sans préciser qu'il s'agit d'un critère du PoC ou d'une cible future.

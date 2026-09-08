# Chapitre 5 — Réalisation

> **Statut** : rédigé (08/09/2026)

## Objectif

Restituer l'implémentation effective de la plateforme : générateur de données avec
vérité terrain, pipeline ELT Medallion en 4 étapes, moteur de déduplication
(Pandas + Spark), chargement PostgreSQL, gouvernance et API, puis difficultés
rencontrées sur la VM et leur résolution.

---

## 5.1 Générateur de données et vérité terrain

Le générateur
[`synthetic-patient-generator`](../projet/code-source/evaluation/synthetic-patient-generator)
est implémenté en 7 étapes, déterministe (seed 42) :

| Module | Rôle réalisé |
|---|---|
| `patient_generator.py` | 500 patients maîtres + `master_patients.csv` (vérité absolue) |
| `distribution_engine.py` | plan de distribution 0.8 / 0.7 / 0.6 → 3 sources |
| `variation_engine.py` | injection d'erreurs easy 10 % / medium 30 % / hard 50 % |
| `pharmacy/consultation/imaging_generator.py` | fichiers patients + transactions |
| `identity_mapping.py` | `identity_mapping.csv` : source → source_patient_id → ground_truth_id |
| `experiment_builder.py` | datasets easy / medium / hard |

Types de variations réels : casse, espaces, inversion prénom/nom, abréviation,
typo (suppression/duplication/permutation), formats téléphone (+261 / espacés) et
dates (ISO, DD/MM/YYYY…), valeurs manquantes. Résultat pour le dataset hard :
**1 057 enregistrements, 500 groupes de vérité, répartition 404 / 353 / 300**, et
792 achats / 519 consultations / 450 examens. Le fichier de vérité est **réservé à
l'évaluation** — jamais fourni à l'algorithme [deduplication.md — règle métier].

## 5.2 Pipeline ELT Medallion en 4 étapes

Orchestration par `run_pipeline.sh` (arrêt sur erreur, logs `elt.log`) : run
**4/4 vert** sur la VM le 07/09/2026 [contexte_projet.md].

```mermaid
flowchart LR
    DS[data_sources.json] --> R[1/4 gen_extract_raw<br/>parquet HDFS + tables Hive externes]
    R --> M[2/4 gen_fhir_mapping<br/>fhir_mapping.json]
    M --> S[3/4 create_silver<br/>4 tables FHIR + dédup moteur]
    S --> G[4/4 create_gold<br/>patient_events_gold + patient_consent_gold]
    R -. extract_raw_report.json .-> M
```

| Étape | Script | Sortie réelle |
|---|---|---|
| **1 — Extraction RAW** | `gen_extract_raw.py` | parquet `/datalake/raw/{source}/{table}`, tables Hive externes, `extract_raw_report.json` |
| **2 — Mapping FHIR** | `gen_fhir_mapping.py` | `fhir_mapping.json` (table→entité FHIR, cartes explicites) |
| **3 — SILVER FHIR** | `create_silver.py` | `datalake_silver.{patient,encounter,condition,observation}_fhir` |
| **4 — GOLD** | `create_gold.py` | `patient_events_gold` (8 tranches RMA), `patient_consent_gold` |

Résultats du run de référence (sources CSV synthétiques, 214 enregistrements) :
**`datalake_silver.patient_fhir` = 214 lignes** (76 + 76 + 62) ; **145 masters** ;
**69 doublons liés** (`is_duplicate`), tous `match_method = exact` ; `duplicate_rate`
**32.24 %** ; `patient_consent_gold` = **145** lignes. `patient_events_gold` reste à
**0 ligne** en intermédiaire (jointures FHIR non rattachées — dette identifiée au
chapitre 6).

L'étape 3 intègre la **fusion des doublons dans le Data Lake** : le moteur relit
`patient_fhir`, réapplique `deduplicate()` et enrichit chaque ligne des colonnes
`master_patient_id`, `match_method`, `match_score` et `is_duplicate` — la fusion
reste explicable *dans* le lac, pas seulement dans un script séparé.

## 5.3 Moteur de déduplication : Pandas et Spark

Le moteur `engine/identity/` est la pièce centrale, deux implantations alignées :

| Aspect | `matcher.py` (Pandas) | `spark_dedup.py` (PySpark driver-side) |
|---|---|---|
| Canonique | `canonical.py` (`map_patient`, `from_dict`) | réutilise `matcher`/`canonical` |
| Exact | `matching_key` + naissance/téléphone | clusters par `groupBy` de la clé |
| Probabiliste | `_MasterIndex` (3 buckets) | `_BoundedMasterIndex` sur ancres de clusters |
| Score | `fuzz.ratio(nom)×0.5 + naissance×0.3 + tél×0.2` | identique |
| Décision | `exact` / `probabilistic` / `new_master`, seuil 0.80 | identique |
| Sortie | `MatchDecision` | dicts `(master_patient_id, method, score, explanation)` |

La **sémantique est strictement alignée** et la **parité est vérifiée** : démo 18
patients → 11 masters identiques Pandas et Spark, et évaluation ground-truth
« modes MVP+Spark identiques » (TP=209, FP=0, FN=518 pour les deux)
[`evaluation_truth.md`] — voir chapitre 6.

## 5.4 Chargement PostgreSQL et GOLD du consentement

- **Chargement central** : le schéma (`sql/schema.sql`) est créé de façon
  **idempotente** (`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`,
  `ON CONFLICT`) — le pipeline est rejouable sans état résiduel.
- **`patient_consent_gold`** : l'étape GOLD joint le PostgreSQL central (table
  `consent`, via `psycopg`) aux masters SILVER ; si la base est inaccessible, le
  schéma est créé vide et l'API bascule en mode `mock` — le consentement reste un
  composant formel de l'architecture.

## 5.5 Gouvernance et API

L'API de données (Flask, port 5000) expose **11 endpoints** — 9 « RMA » (`/rma/*`,
`/api/rma/*`) + 2 gouvernance (`/api/governance/duplicates`, `/api/governance/consent`)
— avec une réponse unifiée portant l'indicateur **`mocked`** (vrai uniquement en
secours backend, jamais côté frontend). `test_api.py` couvre les 11 endpoints +
cas d'usage et retourne **14/14 PASS** en données réelles (`RMA_USE_MOCK=false`)
[contexte_projet.md].

La gouvernance est implémentée dans le moteur : `auth.py` (authentification par
clé hachée SHA-256 + rôles `admin`/`analyst`/`viewer`), `consent.py` (router FastAPI
`/consent`, décision *purpose-by-purpose*), `audit.py` (middleware journalisant
chaque requête, refus compris). Les **payloads RAW ne sont jamais exposés** par
l'API — seuls les maîtres consolidés le sont [consentement_gouvernance.md §7].

## 5.6 Difficultés rencontrées et résolutions

| Problème réel | Cause | Correctif |
|---|---|---|
| SILVER explosait à **11 614 lignes** | `patient_uuid` capturé par le mapping FHIR dynamique → `source_patient_id` NULL → jointure **76×76** du moteur | `patient_uuid` **exclu** du mapping dynamique + colonne source utilisée une seule fois |
| Listing périmé (overwrite+append par source) | écritures répétées dans la boucle source | accumulation par entité, **une seule écriture `overwrite` par table** ; phase 5 en table temp puis `DROP` + `RENAME TO` |
| Parquet corrompu sur partage vboxsf | warehouse Spark écrit sur le montage partagé | `spark.sql.warehouse.dir = hdfs://localhost:9000/...` (toujours HDFS) |
| Spark ne démarrait pas | `JAVA_HOME` avec `\bin` en trop | normalisation `_resolve_java_home()` dans `spark/session.py` |
| HiveServer2/beeline instable sur la VM | service HS2 fragile | validation des comptages par **scripts Spark** (`check_data.py`) |
| NLP lourd inutilisable | `sentence_transformers` crash Python 3.8 | RapidFuzz + dictionnaire de synonymes (`fhir_synonyms.py`) |

Environnement d'exécution: VM `ubuntu/focal64` 8 Go / 4 cœurs — Hadoop 3.3.6,
Hive 3.1.3 (métastore distant 9083 pour éviter le conflit Derby), Spark 3.4.2,
Java 8 ; Spark configuré `executor 4g / driver 2g / shuffle.partitions=8`
[Vagrantfile, bootstrap.sh].

## Conclusion et transition

La plateforme est réalisée et opérationnelle : 4/4 pipeline vert, dédup enregistrée
dans le lac, API 14/14, gouvernance mécanisée. Reste à **démontrer la qualité** :
le chapitre 6 présente la stratégie de test, l'évaluation ground-truth (P/R/F1) et
les limites honnêtes du prototype (rappel « hard », GOLD incomplet).

### Références

- `provision/scripts/ELT/*` + `run_pipeline.sh` ; `provision/api/hive_api.py`,
  `mock_data.py`, `test_api.py`.
- `engine/identity/{canonical,matcher,spark_dedup}.py` ; `engine/governance/{auth,consent,audit}.py`.
- `sql/schema.sql` ; `ai/memoire/contexte_projet.md` (run 07/09/2026).
- `documents/documentation/pipeline_elt.md` (pièges anti-régression).
# projet/code-source — Guide technique

Code fusionné de la plateforme de centralisation et de gouvernance des données patients
(dépôt unique consolidé). Deux volets :

- **Big Data (Medallion)** : VM Hadoop/Hive/Spark + pipeline ELT (via `provision/`) — porté de `datalake_mavis`.
- **Déduplication + gouvernance** : moteur `engine/` (canonique, règle d'identité stricte, master
  patient, consentement, audit) — porté de `test_bigdata` et rendu autonome.

## Structure

```
projet/code-source/
├── provision/            VM Big Data + ELT + API Flask
│   ├── Vagrantfile       VM (ubuntu/focal64, 8 Go, Hadoop/Hive/Spark)
│   ├── bootstrap.sh      provisioning (Java, Hadoop, Hive, Spark, JDBC, venv)
│   ├── config/           pipeline.yaml (commité) · fhir_entities.json · data_sources.json (NON COMMITÉ) + data_sources.example.json / data_sources.mavis.example.json
│   ├── scripts/ELT/      gen_extract_raw · gen_fhir_mapping · create_silver · create_gold
│   ├── scripts/utils/    paths.py (config centrale) · fhir_schema (schéma + synonymes) · sync_utils · age_tranches (tranches GOLD)
│   ├── scripts/run_pipeline.sh    orchestration 5 étapes (arrêt sur erreur)
│   ├── scripts/ensure_generator_data.sh  étape 0 : régénère les CSV du générateur (seed 42)
│   ├── api/              hive_api.py (Flask, port 5000) · mock_data.py · test_api.py
│   ├── db/               rebuild_mmt_db.py (base synthétique) · seed_governance.py (utilisateurs + consentements)
│   ├── jars/             postgresql-42.7.3.jar
│   └── test_startup.sh   health check MAVIS/Hive/API/métadonnées
├── engine/               moteur de déduplication + gouvernance (Python 3.8+, autonome)
│   ├── identity/         canonical.py · rules.py (règle stricte) · matcher.py (référence Python) · spark_dedup.py (Spark)
│   └── governance/       database.py (pool psycopg) · auth.py (clés SHA-256) · consent.py · audit.py
├── evaluation/           ground-truth P/R/F1
│   ├── synthetic-patient-generator/   générateur easy/medium/hard (+ ground truth)
│   ├── evaluation_truth.py            calcul P/R/F1 + breakdown
│   └── evaluate_engine.py             évaluateur adapté au moteur engine/
├── tests/                moteur, consentement, API (fausses connexions), pipeline ; test_governance_pg.py (vrai PostgreSQL, si GOVERNANCE_TEST_DATABASE_URL) ; parités Spark (VM)
├── sql/schema.sql        schéma PostgreSQL central (RAW, master, identity map, consent, api_user, audit)
└── front-optional/       visualisation Next.js (optionnel — ex visualisation_app)
```

## Démarrage rapide (moteur + tests)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m pytest -q        # hôte : tout réussi ; tests Spark et PostgreSQL ignorés sans PySpark / base de test
.venv\Scripts\python evaluation\evaluate_engine.py --level hard   # évaluation ground-truth
```

## Démarrage Big Data (VM)

```bash
vagrant up && vagrant ssh
start-dfs.sh; start-yarn.sh              # HDFS puis YARN (ordre STRICT)
beeline -u jdbc:hive2://localhost:10000 -n vagrant -e "SHOW DATABASES"
bash provision/scripts/run_pipeline.sh   # RAW → SILVER → GOLD (logs provision/logs/elt.log)
python -m provision.api.hive_api         # API Flask — port 5000
python -m provision.api.test_api         # 14/14 PASS attendu
```

> Préalable : `cp provision/config/data_sources.example.json provision/config/data_sources.json` puis
> **aucune édition** : les sources sont les CSV du générateur synthétique (`type=csv`, seed 42) ;
> l'étape 0 de `run_pipeline.sh` les régénère si absents. Sources avancées MAVIS/MMT_DB : utiliser
> `data_sources.mavis.example.json`. Warehouse Spark = HDFS uniquement.
>
> Config pipeline (chemins HDFS, bases Hive, tables cibles, mémoire Spark, tranches d'âge, port API) :
> `provision/config/pipeline.yaml` (commité). Schéma FHIR + synonymes + mapping table→entité :
> `provision/config/fhir_entities.json` (commité). Les deux sont chargés par
> `provision/scripts/utils/paths.py` (résolution dynamique de `PROJECT_ROOT`).

## PostgreSQL central

```bash
.venv\Scripts\python -m sqlfluff # (non requis) — le schéma s'applique via : \
psql -d patient_plateform -f sql/schema.sql
```

Tables : `raw_patient_record` · `master_patient` (+gender) · `patient_identity_map` · `consent`
(`purpose` en liste fermée : `api_access`, `research`, `analytics`) · `api_user` (clés SHA-256) ·
`access_audit` (+ `purpose`, `refusal_reason`). Idempotent (`ON CONFLICT`,
`ADD COLUMN IF NOT EXISTS`, `DROP CONSTRAINT IF EXISTS`).

Jeux de démonstration (utilisateurs + consentements mixtes accords/refus) :

```bash
.venv\Scripts\python provision\db\seed_governance.py    # lit DATABASE_URL (.env)
```

Les clés API sont générées à l'exécution et affichées une seule fois : ne pas
versionner cette sortie.

## Moteur — API publique

```python
from engine.identity.canonical import CanonicalPatient
from engine.identity.rules import identity_key, master_id  # règle stricte et identifiant dérivé
from engine.identity.matcher import deduplicate            # référence Python (liste de fiches)
from engine.identity.spark_dedup import deduplicate_df     # même règle dans Spark (DataFrame)
```

Règle (v2, 30/09/2026) : deux fiches sont réunies si et seulement si CIN, genre, date et ville de
naissance sont identiques (sans CIN des deux côtés : nom identique en plus). Aucun score ni seuil ; une
identité incomplète n'est jamais fusionnée. Chaque décision expose `master_patient_id` (dérivé de la clé,
permanent ; HMAC si `PATIENT_ID_SECRET` est défini), `method` (exact|new_master), `score` (1,0) et
`explanation`.

## API de gouvernance — contrôle d'accès et consentement

```bash
uvicorn engine.governance.app:app --port 8000
curl -H "Authorization: Bearer <clé>" "http://localhost:8000/patients?purpose=research"
```

`purpose` est **obligatoire** sur `/patients` et `/patients/{id}` :

| Situation | Réponse |
|---|---|
| aucun `Authorization` / clé inconnue | **401** |
| rôle insuffisant | **403** |
| `purpose` absent ou hors liste fermée | **422** |
| finalité non consentie | **403**, `refusal_reason` journalisé |
| `/patients` | seuls les patients consentis sont renvoyés |

Refus par défaut : l'absence de ligne de consentement vaut refus.

## Règles

- Données **synthétiques** uniquement.
- **Ne pas commiter** : `provision/config/data_sources.json`, `.env`, `provision/metadata/`, `data/`, `*.db`.
- Compatibilité Python 3.8 (VM) : `from __future__ import annotations`, RapidFuzz (pas de NLP lourd).
- Parité Pandas/Spark **obligatoire** pour toute évolution de la déduplication.

## Documentation

- Guide conceptuel : `documents/documentation/` (architecture, bigdata, pipeline, dédup, gouvernance, api, évaluation).
- Consignes de dev : `ai/dev/` — suivi : `ai/dev/suivi_avancement.md` · journal : `ai/dev/logs.md`.

# projet/code-source — Guide technique

Code fusionné de la plateforme de centralisation et de gouvernance des données patients
(`data_lake_final`). Deux volets :

- **Big Data (Medallion)** : VM Hadoop/Hive/Spark + pipeline ELT (via `provision/`) — porté de `datalake_mavis`.
- **Déduplication + gouvernance** : moteur `engine/` (canonique, matching exact/probabiliste, master
  patient, consentement, audit) — porté de `test_bigdata` et rendu autonome.

## Structure

```
projet/code-source/
├── provision/            VM Big Data + ELT + API Flask
│   ├── Vagrantfile       VM (ubuntu/focal64, 8 Go, Hadoop/Hive/Spark)
│   ├── bootstrap.sh      provisioning (Java, Hadoop, Hive, Spark, JDBC, venv)
│   ├── config/           data_sources.json (NON COMMITÉ) + data_sources.example.json
│   ├── scripts/ELT/      gen_extract_raw · gen_fhir_mapping · create_silver · create_gold
│   ├── scripts/utils/    fhir_schema · fhir_synonyms · sync_utils
│   ├── scripts/run_pipeline.sh    orchestration 4 étapes (arrêt sur erreur)
│   ├── api/              hive_api.py (Flask, port 5000) · mock_data.py · test_api.py
│   ├── db/               rebuild_mmt_db.py (base synthétique)
│   ├── jars/             postgresql-42.7.3.jar
│   └── test_startup.sh   health check MAVIS/Hive/API/métadonnées
├── engine/               moteur de déduplication + gouvernance (Python 3.8+, autonome)
│   ├── identity/         canonical.py · matcher.py (Pandas) · spark_dedup.py (Spark)
│   └── governance/       database.py · auth.py (clés SHA-256) · consent.py · audit.py
├── evaluation/           ground-truth P/R/F1
│   ├── synthetic-patient-generator/   générateur easy/medium/hard (+ ground truth)
│   ├── evaluation_truth.py            calcul P/R/F1 + breakdown
│   └── evaluate_engine.py             évaluateur adapté au moteur engine/
├── tests/                test_matcher.py (6) · test_consent.py (3)
├── sql/schema.sql        schéma PostgreSQL central (RAW, master, identity map, consent, api_user, audit)
└── front-optional/       visualisation Next.js (optionnel — ex visualisation_app)
```

## Démarrage rapide (moteur + tests)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m pytest -q        # 9/9 attendu (matcher + consentement)
.venv\Scripts\python evaluation\evaluate_engine.py --level hard   # évaluation ground-truth
```

## Démarrage Big Data (VM)

```bash
vagrant up && vagrant ssh
start-dfs.sh; start-yarn.sh              # HDFS puis YARN (ordre STRICT)
beeline -u jdbc:hive2://localhost:10000 -n vagrant -e "SHOW DATABASES"
bash provision/scripts/run_pipeline.sh   # RAW → SILVER → GOLD (logs provision/logs/elt.log)
python -m provision.api.hive_api         # API Flask — port 5000
python -m provision.api.test_api         # 12/12 PASS attendu
```

> Préalable : `cp provision/config/data_sources.example.json provision/config/data_sources.json` puis
> renseigner les identifiants (fichier NON commité). Warehouse Spark = HDFS uniquement.

## PostgreSQL central

```bash
.venv\Scripts\python -m sqlfluff # (non requis) — le schéma s'applique via : \
psql -d patient_plateform -f sql/schema.sql
```

Tables : `raw_patient_record` · `master_patient` (+gender) · `patient_identity_map` · `consent` ·
`api_user` (clés SHA-256) · `access_audit`. Idempotent (`ON CONFLICT`, `ADD COLUMN IF NOT EXISTS`).

## Moteur — API publique

```python
from engine.identity.canonical import CanonicalPatient
from engine.identity.matcher import deduplicate            # Pandas (explicable)
from engine.identity.spark_dedup import deduplicate as s_dedup  # Spark (parité stricte)
```

Chaque décision expose `master_patient_id`, `method` (exact|probabilistic|new_master), `score` et
`explanation` — logique toujours **explicable**.

## Règles

- Données **synthétiques** uniquement.
- **Ne pas commiter** : `provision/config/data_sources.json`, `.env`, `provision/metadata/`, `data/`, `*.db`.
- Compatibilité Python 3.8 (VM) : `from __future__ import annotations`, RapidFuzz (pas de NLP lourd).
- Parité Pandas/Spark **obligatoire** pour toute évolution de la déduplication.

## Documentation

- Guide conceptuel : `documents/documentation/` (architecture, bigdata, pipeline, dédup, gouvernance, api, évaluation).
- Consignes de dev : `ai/dev/` — suivi : `ai/dev/suivi_avancement.md` · journal : `ai/dev/logs.md`.
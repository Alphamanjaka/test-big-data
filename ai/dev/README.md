# ai/dev — Consignes de développement

> **Lire ce dossier au début de chaque session de travail sur le dépôt unique `Mon_Memoire`.** Il centralise les
> consignes opérationnelles (fusion des `.ai_context` des deux projets sources). Il **est** commité
> (contrairement aux anciens `.ai_context` du projet Mavis).

## Règle unique

Plateforme de centralisation et de gouvernance de **données patients synthétiques** : pipeline Big Data
**Medallion** (RAW→SILVER→GOLD) sur Hive/HDFS/Spark, **déduplication explicable** exact+probabiliste
(master patient + identity map), **consentement purpose-by-purpose**, **audit d'accès**, rôles + clés API.

Priorités : **maîtriser le sujet** (concepts Big Data et consentement) plutôt que perfectionner le
frontend. Données toujours fictives. Structure simple et minimale.

## Fichiers du dossier

| Fichier               | Contenu                                                          | À consulter quand                           |
| --------------------- | ---------------------------------------------------------------- | ------------------------------------------- |
| `README.md`           | Index + contexte projet + environnement                          | Début de session, contrefactuel             |
| `architecture.md`     | Stack, architecture, ports, sources, schémas, répertoires        | Avant toute modification d'architecture     |
| `pipeline_elt.md`     | Consignes PySpark/Hive/Medallion, règles Silver/Gold, pièges     | Travail sur `projet/code-source/provision/` |
| `deduplication.md`    | Consignes moteur d'identité (canonique, matching, seuil, parité) | Travail sur `projet/code-source/engine/`    |
| `methode_codage.md`   | Qualité du code, conventions, tests                              | Avant/ pendant l'écriture de code           |
| `security.md`         | Données, consentement, secrets, audit, web/RBAC                  | Travail sur API, gouvernance, frontend      |
| `logs.md`             | Journalisation (LOGS) et traçabilité                             | Toute activité                              |
| `suivi_avancement.md` | Feuille de route, priorités, règles anti-régression              | Avant de choisir la prochaine tâche         |

## Contexte projet

- **Moteur** : `projet/code-source/engine/` — déduplication + gouvernance (porté de `test_bigdata`).
- **Pipeline ELT** : `projet/code-source/provision/` — VM + Hive/HDFS/Spark (porté de `datalake_mavis`).
- **Évaluation** : `projet/code-source/evaluation/` — ground-truth P/R/F1 (adaptée à `engine/`).
- **Frontend** : `projet/code-source/front-optional/` — Next.js conservé **optionnel**, zéro effort.

## Environnement

### VM Big Data (provision)

```bash
vagrant up && vagrant ssh
start-dfs.sh; start-yarn.sh                          # ordre STRICT
beeline -u jdbc:hive2://localhost:10000 -n vagrant -e "SHOW DATABASES"
```

### Pipeline ELT

```bash
bash provision/scripts/run_pipeline.sh               # 4 étapes, arrêt sur erreur
python3 -m provision.scripts.ELT.create_gold         # une étape seule (chemin relatif en -m)
# Logs : provision/logs/elt.log · suivi : provision/metadata/sync_metadata.json
```

### API & Frontend

```bash
python -m provision.api.hive_api                     # Flask port 5000, CORS localhost:3000
python -m provision.api.test_api                     # 14/14 PASS attendu
# front-optional : npm run dev · npm run build · npm run lint · npx prisma migrate deploy && prisma db seed
```

### Moteur & tests

```powershell
# venv
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m pytest -q                    # 23/23 attendu (matcher + consentement + canonique)
.venv\Scripts\python evaluation\evaluate_engine.py --level hard
```

## Pièges anti-régression (à ne JAMAIS refaire)

1. **Ne pas réintroduire `sentence_transformers`** (crash Python 3.8) → RapidFuzz + synonymes.
2. **Ne jamais écrire le warehouse Spark sur vboxsf** (corruption parquet) → toujours
   `spark.sql.warehouse.dir = hdfs://localhost:9000/...`.
3. **Pas d'`overwrite` dans la boucle par source** (dernière source écrase les autres) → 1re `overwrite`,
   suivantes `append`.
4. **Pas de mocks côté frontend** — les données fictives vivent côté backend (`mock_data.py`, flag `mocked`).
5. **PAS de `DOCTOR`** — rôles alignés (`ADMIN`/`MEDECIN` web ; `admin`/`analyst`/`viewer` plateforme).
6. **Jamais de vraies données patients** ; clés/secrets via env, jamais commités.
7. Mémoire Spark VM 8 Go : `executor_memory=4g`, `driver_memory=2g`, `spark.sql.shuffle.partitions=8`.
8. Route params Next.js 15 = **Promise** (await obligatoire).

## Références

- État des lieux complet : `documents/` (cahier + manuel conceptuel).
- Code : `projet/code-source/README.md` (guide technique) + `sql/schema.sql`.
- Traçabilité : `ai/dev/logs.md` (journal) — ne pas créer d'autres fichiers de suivi.

## Workflow obligatoire pour l'agent

1. Lire `AGENTS.md`, ce fichier et le document propriétaire du composant touché.
2. Vérifier `git status` et ne pas écraser les modifications existantes.
3. Identifier le code qui décide réellement du comportement avant de modifier un simple relais ou
   contrôleur.
4. Faire une modification minimale, puis exécuter immédiatement le contrôle ciblé le moins coûteux.
5. Journaliser toute session, correction, incident ou exécution dans `logs.md` sans secret ni donnée
   patient.

## Qualité, performance et preuve

- Toute fonctionnalité importante doit avoir des tests unitaires, d'intégration ou système adaptés ;
  les tests négatifs et les cas limites sont obligatoires pour consentement, permissions, audit et
  déduplication.
- Les performances ne sont pas déduites de la présence de Spark : mesurer au minimum durée, volume
  entrée/sortie, partitions, mémoire et erreurs, et distinguer optimisation de la VM et scalabilité.
- Toute conclusion du mémoire ou de la documentation doit indiquer sa preuve et ses limites. Ne jamais
  inventer de métriques ni présenter une hypothèse comme un résultat.

## Git et archives

- Le hook `githooks/pre-commit` et les vérifications ciblées constituent le minimum avant commit.
- Les artefacts générés, secrets, fichiers `.env`, données et métadonnées locales restent hors commit.
- Les dossiers `projet/mvp/` et `archives/datalake_mavis/` sont consultables pour comprendre l'historique ;
  ils ne redéfinissent pas les chemins, journaux ou commandes du code consolidé.

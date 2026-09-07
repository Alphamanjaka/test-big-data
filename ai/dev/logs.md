# Logs — journal d'activité

Journal unique de toutes les sessions, fixes, incidents et runs du projet `data_lake_final`.
Format : entrée datée (tableau action/fichiers/détail) + vérifications + résultat.
Ne jamais y mettre de données sensibles.

---

## 07/09/2026 — Fusion docs (Phase 1) + instructions IA (Phase 2) + guide technique

**Contexte :** poursuite de la fusion `datalake_mavis` + `test_bigdata` → `data_lake_final`.
Les docs des deux projets ont été consolidées en un seul jeu logique (pas de doublons LOG.md/LOGS.md,
SUIVI_AVANCEMENT/SUIVI-AVANCEMENT).

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Lecture des sources doc | `datalake_mavis/*.md`, `.ai_context/*`, `provision/api/README.md` ; `Mon_Memoire/projet/code-source/*.md`, `ai_context/*.md` ; `Plateforme…(1).md` | Extraction du contenu utile des 2 projets |
| 2 | Cahier des charges consolidé | `documents/cahier_des_charges.md` | Fusion CAHIER_DE_CHARGE Mavis + Plateforme test_bigdata ; périmètre, architecture, planning, métriques |
| 3 | Manuel conceptuel (7 thèmes) | `documents/documentation/architecture.md`, `bigdata_concepts.md`, `pipeline_elt.md`, `deduplication.md`, `consentement_gouvernance.md`, `api.md`, `evaluation.md` | Une doc par thème, sources croisées des 2 projets |
| 4 | Instructions IA mémoire | `ai/memoire/README.md`, `contexte_projet.md`, `methode.md` | Rédaction du mémoire, pointe vers `Mon_Memoire/` |
| 5 | Instructions IA dev | `ai/dev/README.md`, `architecture.md`, `pipeline_elt.md`, `deduplication.md`, `methode_codage.md`, `security.md`, `logs.md`, `suivi_avancement.md` | Fusion des `.ai_context` des 2 projets (commités ici) |
| 6 | Guide technique code | `projet/code-source/README.md` + `pyproject.toml` | Packaging `engine` local (`pip install -e ".[test]"`), structure, démarrage VM |

**Vérifications :** `pytest` moteur déjà 9/9 avant session (matcher 6 + consent 3) ; lecture complète des
sources effectuée ; chemin relatifs des liens inter-docs contrôlés.

**Résultat :** Phases 1 et 2 terminées. Prochaine étape : Phase 5 (intégration SILVER/GOLD + API
gouvernance) puis Phase 6 (évaluation + commit git initial).

---

## 07/09/2026 — Phase 5 : intégration SILVER/GOLD + API gouvernance

**Contexte :** relier le pipeline ELT au moteur de déduplication explicable et refléter le consentement
en couche GOLD, avec endpoints de gouvernance (fallback mock), puis uniformiser les chemins VM
(`/home/vagrant/datalake-mavis` → `/home/vagrant/datalake-final`).

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Enrichissement SILVER / moteur | `provision/scripts/ELT/create_silver.py` | `_source_system` par source ; fin de boucle → `enrichir_dedup_moteur()` (engine `deduplicate`) → colonnes `master_patient_id`, `match_method`, `match_score` ; `is_duplicate` recalculé côté moteur ; garde si moteur/patient vide |
| 2 | Consentement GOLD | `provision/scripts/ELT/create_gold.py` | `charger_consent_gold()` : `datalake_gold.patient_consent_gold` = consent PostgreSQL central (`DATABASE_URL`, psycopg) LEFT JOIN masters SILVER ; schéma créé même si vide (API → mock) |
| 3 | Endpoints gouvernance | `provision/api/hive_api.py` + `provision/api/mock_data.py` | `GET /api/governance/duplicates` (KPI SILVER + by_method) et `GET /api/governance/consent` (list + stats) ; mocks `MOCK_GOVERNANCE_DUPLICATES` + `MOCK_CONSENT` |
| 4 | Chemins VM uniformisés | `create_silver.py`, `create_gold.py`, `gen_extract_raw.py`, `gen_fhir_mapping.py`, `sync_utils.py`, `hive_api.py`, `Vagrantfile`, `bootstrap.sh`, `run_pipeline.sh`, `capture_mavis_schema.sh`, `test_api.sh`, `api/test_api.py`, `api/README.md` | `/home/vagrant/datalake-mavis` → `datalake-final` ; Vagrantfile monte `data_lake_final/projet/code-source` ; `ELT.before/` et `front-optional/todo.md` laissés tels quels (archives) |
| 5 | Docs mises à jour | `documents/documentation/pipeline_elt.md`, `api.md` | Étapes 3/4 SILVER-GOLD (moteur + consent GOLD), endpoints gouvernance, flux fichiers |

**Vérifications :** `ast.parse` OK sur les 4 fichiers Python modifiés ; aucune chaîne `datalake-mavis`
restante dans les scripts opérationnels (hors archives).

**Résultat :** Phase 5 terminée. Prochaine étape : Phase 6 (évaluation easy/medium/hard, tests API/parité,
commit git initial).

---

## 07/09/2026 — Phase 6 (partiel) : évaluation + tests

**Contexte :** valider localement le moteur fusionné avant commit git initial.

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Correction TOML | `projet/code-source/pyproject.toml` | `description` reformatée (contenu multi-lignes invalide → une seule chaîne) |
| 2 | Tests unitaires | `projet/code-source` | `pytest` → **9/9 PASS** (matcher 6 + consent 3) |
| 3 | Évaluation ground truth | `evaluation/evaluate_engine.py` (easy/medium/hard) | P/R/F1 : easy & medium 1.000/1.000/1.000 ; hard 1.000/0.287/0.447 (zéro FP) ; **parité MVP=Spark parfaite** ; rapport régénéré `evaluation_truth.md` |
| 4 | 2 issues locales | `documents/documentation/evaluation.md`, `ai/dev/suivi_avancement.md` | Résultats de référence documentés ; warning : console Windows cp1252 → lancer avec `PYTHONIOENCODING=utf-8` |

**Vérifications :** `ast.parse` OK (Phase 5) ; `pytest` 9/9 ; évaluation 3 niveaux exécutée ;
données générées (`synthetic-patient-generator/data/`, `provision/metadata/`) non commitables
(vérifié `.gitignore`).

**Résultat :** tests + évaluation OK en local. Reste (Phase 6 / VM) : re-run `run_pipeline.sh` avec le
moteur intégré, `test_api.sh`, puis commit git initial.
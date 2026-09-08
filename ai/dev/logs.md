# Logs — journal d'activité

Journal unique de toutes les sessions, fixes, incidents et runs du projet (dépôt unique `Mon_Memoire`).
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

---

## 08/09/2026 — Mémoire : chapitres 01→06 rédigés + bibliographie (phase rédaction)

**Contexte :** rédaction du mémoire dans `Mon_Memoire/chapters/` (séquentielle, validation du style
sur ch.01), sur la base des chiffres harmonisés de `ai/memoire/contexte_projet.md`. Recherche web
préalable pour référencer Fellegi & Sunter, Elmagarmid, Christen, FHIR, Medallion, RapidFuzz, CNIL/RGPD.

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Harmonisation chiffrée | `ai/memoire/contexte_projet.md`, `documents/cahier_des_charges.md` | Éval 07/09 : P 1.000 / R 0.287 / F1 0.447, exact 1.000/0.737/0.848, probabilistic 1.000/0.667/0.800, rappel par source 0.299/0.286/0.276, TP209/FP0/FN518, 869 masters, 500 groupes, 1 057 enreg. ; run fusion 214/145/69 doc. |
| 2 | Chapitre 1 rédigé (07/09) | `Mon_Memoire/chapters/01-introduction.md` | Contexte MMT, problématique, objectifs, démarche 3 niveaux (1 Mermaid), périmètre, plan du mémoire |
| 3 | Chapitre 2 + bibliographie (08/09) | `Mon_Memoire/chapters/02-etat-de-l-art.md`, `references/bibliographie.md` | ER/Record Linkage, similarités (RapidFuzz), blocking, MPI + FHIR, RGPD, HDFS/Spark/Hive, Medallion, positionnement + 1 Mermaid ; réf. [B1..B12] |
| 4 | Chapitre 3 rédigé | `Mon_Memoire/chapters/03-analyse.md` | Sources + hétérogénéité (colonnes réelles), générateur seed 42 (500 masters, 404/353/300, easy/medium/hard 10/30/50 %), exigences, contraintes VM/MAVIS + 1 Mermaid |
| 5 | Chapitre 4 rédigé | `Mon_Memoire/chapters/04-conception.md` | Architecture 3 niveaux + 1 Mermaid, `CanonicalPatient`, blocking + exact/probabiliste (0.50/0.30/0.20, seuil 0.80), schéma PG, gouvernance, Medallion |
| 6 | Chapitre 5 rédigé | `Mon_Memoire/chapters/05-realisation.md` | Générateur, ELT 4 étapes + 1 Mermaid, moteur Pandas/Spark, PG/GOLD, API 11 endpoints + 14/14, incidents (11 614, vboxsf, JAVA_HOME, HS2) |
| 7 | Chapitre 6 rédigé | `Mon_Memoire/chapters/06-tests.md` | Stratégie + 1 Mermaid, éval ground-truth P/R/F1 (easy/medium/hard), breakdown, parité MVP=Spark, limites (recall hard, GOLD sparse) |
| 8 | Faits collectés | 2 rapports agents explore | Sources/générateur/contraintes (ch.03) ; moteur/pipeline/schéma/gouvernance/API/incidents (ch.04/05) + doc `evaluation.md` |

**Vérifications :** tous les chiffres cités retrouvés dans le dépôt (`contexte_projet.md`,
`evaluation_truth.md`, `evaluation.md`, scripts, `schema.sql`) ; gabarit/style aligné sur ch.01 ;
1 Mermaid par chapitre technique ; liens conceptuels `documents/documentation/*`.

**Résultat :** jalons rédaction 01→06 ✅ + bibliographie (12 réf. vérifiées). Reste : relecture/conversion
docx par l'utilisateur ; mise à jour `suivi_avancement.md` (commit initial ✅ 2004865).

---

## 07/09/2026 — Run pipeline vert VM + validation SILVER/GOLD + API 14/14 (Phase 6 / VM)

**Contexte :** exécuter le pipeline réaligné en VM (`datalake_mavis`, sources CSV synthétiques,
interim patients-only) — le run précédent produisait **11 614 lignes** (explosion 76×76 dans la
jointure du moteur) — puis valider les comptages SILVER/GOLD et l'API sur vraies données.

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Cause racine + fix explosion 11614 | `provision/scripts/ELT/create_silver.py` | `patient_uuid` **exclu du mapping FHIR dynamique** (`meilleure_colonne_attendue` le détournait sur la colonne ID → `source_patient_id` renommée/`name` NULL → préfixe concat = `"pharmacy"` → join moteur 76×76) ; garde-fou `colonnes_source_utilisees` (une colonne source renommée une seule fois) |
| 2 | Écritures SILVER fiabilisées | `create_silver.py` | Accumulation par entité (`accum_par_entite`) + **une seule écriture `mode="overwrite"`** par table cible ; enrichissement moteur via `patient_fhir__dedup_tmp` + `DROP TABLE` + `ALTER TABLE … RENAME TO` (évite `Cannot overwrite table being read`) ; compteurs moteur pré-écriture ; `marquer_doublons_patients` sur l'union toutes sources |
| 3 | GOLD tolérant (patients-only) | `provision/scripts/ELT/create_gold.py` | `_lire_silver` tolérant + `_vide` (Encounter/Condition/Observation absents) ; `SystemExit(1)` si `patient_fhir` absente ; consent `dropDuplicates(["master_patient_id"])` |
| 4 | Run pipeline | `provision/scripts/run_pipeline.sh` | 4 étapes vertes : **`✅ Pipeline ELT complet : RAW -> SILVER -> GOLD OK`** (logs `provision/logs/{elt.log, create_gold.log}`) |
| 5 | Validation Spark | `provision/metadata/check_data.py` + `run_check.sh` | `silver_patient_fhir` **214** (76/76/62), masters 145, doublons 69, méthodes exact 69 / new_master 145, scores 1.0, uuids uniques ; gold patients-only → events 0, consent 145 |
| 6 | API réelle | `provision/metadata/start_api.sh` | `RMA_USE_MOCK=false` ; health `GET /rma/last_sync` 200 ; `python -m provision.api.test_api` → **14/14 PASS (0 FAIL)** |
| 7 | KPIs gouvernance réels | `provision/api/hive_api.py` | `duplicates`: exact 69 / new_master 145, taux 32.24 % ; `consent`: 145 patients (`granted` NULL, PostgreSQL non alimenté) — `mocked: false` |
| 8 | Doc pipeline mise à jour | `documents/documentation/pipeline_elt.md` | Section « Validation VM (interim CSV) » + pièges anti-régression (patient_uuid, overwrite unique, tmp+rename) |

**Vérifications :** pipeline 4/4 vert ; comptages SILVER/GOLD cohérents (214 = 76+76+62, 214 − 69 = 145) ;
API 14/14 sur données réelles ; `ast.parse` OK avant run. beeline HS2 instable contourné (scripts Spark) ;
quoting PowerShell → scripts dans `provision/metadata/`.

**Résultat :** jalon Phase 6 VM atteint — pipeline vert + validation + API 14/14. Reste : commit git
initial (après accord) + suite rédaction du mémoire.

---
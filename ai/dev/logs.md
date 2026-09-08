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

## 09/09/2026 — Consolidation : dépôt unique `Mon_Memoire`

**Contexte :** rapatrier `data_lake_final` et `datalake_mavis` dans un **dépôt unique** `Mon_Memoire`
(validation utilisateur : « une organisation unique »), en préservant l'historique git de `data_lake_final`
via `git subtree`, puis supprimer les anciens répertoires.

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Import `data_lake_final` | `git subtree add --prefix=atelier` (commit `3a303dd`) + commit `8a0a217` | Historique git préservé (a2c7250→2004865) ; renaming `git mv` (atelier→documents/, ai/, projet/) ; 219 fichiers |
| 2 | PoC `test_bigdata` → `projet/mvp/` | commit `3b31559` | 112 fichiers, rename 100 % ; purge `.venv`/`.pytest_cache`/`.env` |
| 3 | Secret/artefacts hors suivi | `data_sources.json`, `cim_embeddings.pkl`, `documents/*.docx`, `.gitignore` | `git rm --cached` conformément AGENTS ; règles `.gitignore` ajoutées (pkl, docx externe utilisateur) |
| 4 | Archive `datalake_mavis` | `archives/datalake_mavis/` (commit `ad862c5`) | Source seule (docs, provision, visualisation_app) ; exclus `.git`, venv/node_modules, logs, metadata, rapports d'autres étudiants (docs/ 47 Mo) ; ~5 Mo |
| 5 | Références dépôt unique | `chapters/02/03/05`, `README.md`, `AGENTS.md`, `cahier_des_charges.md`, `ai/memoire/*`, `documentation/*`, `Vagrantfile` (commit `a15deda`) | Liens chapitres réécrits (`../projet/code-source`, `../documents`), prose ch.01 neutralisée, chemin hôte Vagrantfile → `Mon_Memoire/projet/code-source` |
| 6 | Suppression anciens répertoires | `datalake_mavis` (supprimé) ; `data_lake_final` (vidé) | `datalake_mavis` supprimé ; coquille `data_lake_final` vide verrouillée par un process externe (suppression manuelle restante) |

**Vérifications :** `pytest` moteur **9/9** + générateur **44/44** re-passés dans `Mon_Memoire` (`.venv`
recréé) ; liens des chapitres `Test-Path` OK ; `git log` montre l'historique importé ; parité archive vs
source vérifiée (seuls exclusions prévues : .pyc, logs, metadata, .pkl, .db, docs externes) ; tree propre.

**Résultat :** **dépôt unique `Mon_Memoire`** = mémoires (`chapters/`), docs (`documents/`), code
(`projet/code-source/`), PoC (`projet/mvp/`), archive (`archives/datalake_mavis/`), références
(`references/`), consignes (`ai/`).

---

## 08/09/2026 — Rework déduplication : clé CIN + ville de naissance (chaîne live)

**Contexte :** décision utilisateur de remplacer le téléphone par le **CIN** (~75 % de couverture, clé
forte) et d'ajouter la **ville de naissance** (poids faible) dans le matching, **uniquement sur la
chaîne live** (`projet/code-source/`, hors `projet/mvp/` PoC archivé), puis recalculer l'évaluation et
mettre à jour toute la documentation.

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Générateur (CIN/ville) | `evaluation/synthetic-patient-generator/config/settings.py`, `patient_generator.py`, `common.py`, `variation_engine.py`, 3 générateurs sources | `MasterPatient.cin/birth_city` ; `_generate_mg_cin` ; CIN absent décidé au maître (jamais « sali ») ; `make_missing` cible naissance/ville ; `cin_format` remplace `phone_format` ; tests → **pytest 44/44** |
| 2 | Moteur (canonical + matcher) | `engine/identity/canonical.py`, `matcher.py`, `spark_dedup.py`, `__init__.py` | `CanonicalPatient` cin/birth_city ; `matching_key (birth_date, cin, nom)` ; poids **0.5/0.3/0.1/0.1** ; règle exacte « naissance + CIN non vide » ; `_MasterIndex._by_cin` ; `_cin` remplace `_phone` ; **parité Spark** conservée ; `tests/test_matcher.py` **9 cas** (dont formats CIN, ville, CIN différents→non fusion) → **pytest moteur 12/12** (matcher 9 + consent 3) |
| 3 | Pipeline/schéma | `sql/schema.sql`, `provision/scripts/utils/fhir_schema.py`, `fhir_synonyms.py`, `provision/scripts/ELT/create_silver.py`, `evaluate_engine.py`, `README.md` | colonnes `cin`/`birth_city` ; Patient FHIR (sans phone) ; synonymes ; `from_dict` COLS ; compteurs 12/12 |
| 4 | Réévaluation | données régénérées (seed 42) ; `evaluate_engine.py` easy/medium/hard ; `evaluation_truth.md` | Nouveaux chiffres hard : **TP 307 / FP 0 / FN 420, 804 masters → P 1.000 / R 0.422 / F1 0.594** ; exact 1.000/0.854/0.921 ; probabilistic 1.000/0.533/0.696 ; rappel source 0.422/0.422/0.423 ; medium 554/643/84 → 1.000/0.884/0.939 |
| 5 | Docs & mémoire (harmonisation) | `chapters/01..06.md`, `documents/cahier_des_charges.md`, `documents/documentation/{deduplication,architecture,evaluation}.md`, `ai/memoire/contexte_projet.md`, `ai/dev/{deduplication,architecture}.md` | suppression téléphone → CIN/ville ; poids 0.5/0.3/0.1/0.1 ; seuil 0.80 ; cas Jean Rakoto (exact CIN) ; nouveaux chiffres éval ; compteurs 12/12 |
| 6 | Legacy | `provision/db/rebuild_*.py`, `provision/scripts/ELT.before/` | **non modifiés** (outils démo de bases legacy, hors chaîne master-patient active) |

**Vérisable :** `pytest` moteur **12/12** (9 matcher + 3 consent) + générateur **44/44** ; évaluation 3
niveaux régénérée ; recherche grep des références `phone`/`0.287`/`0.447`/`0.3/0.2`/`9/9` purgée dans
`chapters/` et `documents/`.

**Résultat :** rappel hard relevé de 0.287 → **0.422** sans aucun faux positif (P 1.000 intact) grâce à
la clé CIN. Commits par lots non poussés sur `origin` (en attente d'accord, branche `develop_spark`).

---

## 08/09/2026 — Config YAML des poids / seuil (source de vérité déduplication)

**Contexte :** l'ajout précédent d'un champ (CIN) avait imposé des modifications documentaires répétées
(11 fichiers docs pour refléter les valeurs). Décision utilisateur : extraire les **paramètres métier**
hors du code vers un **YAML unique lu réellement par le moteur** (matcher, spark, évaluation, SILVER),
afin qu'une calibration future = 1 édit de fichier.

| # | Action | Fichiers | Détail |
|---|---|---|---|
| 1 | Config YAML créée | `projet/code-source/config/deduplication.yaml` | `threshold: 0.80` ; `weights {name 0.5, birth_date 0.3, cin 0.1, birth_city 0.1}` ; `blocking.name_prefix_len: 4` |
| 2 | Loader engine | `engine/identity/config.py` | `DedupConfig` + `load_dedup_config()` (cache) ; résolution du YAML relative au dépôt code-source ; **fallback défauts** si fichier absent/illisible/PyYAML absent (aucun crash, comportement inchangé) ; compatible Python 3.8 |
| 3 | matcher.py | `engine/identity/matcher.py` | `_similarity(..., weights)` ; `_name_prefix(..., prefix_len)` ; `_MasterIndex(prefix_len)` ; `deduplicate(patients, probabilistic_threshold=None, weights, name_prefix_len)` — rétro-compatible (`deduplicate(patients)` et `(patients, 0.80)` valides) |
| 4 | spark_dedup.py | `engine/identity/spark_dedup.py` | Même threading `threshold/weights/name_prefix_len` ; `_BoundedMasterIndex(prefix_len)` ; partage `_similarity(..., weights)` — **parité préservée** |
| 5 | Lecture réelle du YAML | `evaluation/evaluate_engine.py`, `provision/scripts/ELT/create_silver.py` | MVP et Spark dédup parametrés par le config chargé ; SILVER garde le fallback ImportError existant (VM sans PyYAML/moteur → mode dégradé) |
| 6 | Dépendance | `pyproject.toml` | `PyYAML>=6.0,<7.0` ajouté aux `dependencies` |
| 7 | Tests +3 | `tests/test_matcher.py` | lecture du YAML (valeurs courantes), fallback sur fichier manquant, changement de décision via override `weights` |
| 8 | Docs | `documents/documentation/deduplication.md`, `ai/dev/deduplication.md` | Poids/seuil référencés **par le YAML** (source de vérité), valeurs courantes affichées pour lecture |

**Vérifications :** `pytest` moteur **15/15 PASS** (matcher 12 + consent 3) + générateur **44/44** ;
`evaluate_engine.py --level hard` → **parité exacte avec le run précédent** : TP=307 FP=0 FN=420,
P 1.000 / R 0.422 / F1 0.594, 804 masters, rappel source 0.422/0.422/0.423 (preuve : refactor sans
changement de comportement) ; `evaluation_truth.md` régénéré (mêmes chiffres).

**Résultat :** la calibration de la déduplication est désormais **déclarative** (1 fichier YAML) — le
coût d'une future modification de poids/seuil/préfixe est ramené à l'édition du YAML + le tableau de
référence dans `deduplication.md`, sans toucher au code ni aux chapitres. Commits en attente.
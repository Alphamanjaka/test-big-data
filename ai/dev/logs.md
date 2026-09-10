# Logs — journal d'activité

Journal unique de toutes les sessions, fixes, incidents et runs du projet (dépôt unique `Mon_Memoire`).
Format : entrée datée (tableau action/fichiers/détail) + vérifications + résultat.
Ne jamais y mettre de données sensibles.

---

## 10/09/2026 — GOLD alimenté par le générateur synthétique (sources CSV + événements)

**Contexte :** `patient_events_gold` vide (0 ligne) : le run ne mappait que `patients → Patient`
(local `data_sources.json` ne listait que `patients` ; `fhir_entities.json` ne mappait aucune table
d'événements). Objectif utilisateur : le pipeline consomme **toujours** les données du générateur
(le générateur produit déjà des tables d'événements avec FK patients : achats, consultations, examens).

| # | Fichier | Modification |
| - | ------- | ------------ |
| 1 | `provision/config/fhir_entities.json` | `table_mappings` : `pharmacy.achats`→Encounter (`fk_to_patient=customer_id`), `consultation.consultations`→Encounter (`fk_to_patient=patient_id`), `imaging.examens`→Encounter (`fk_to_patient=patient_code`) ; `synonyms` : `encounter_id`↔[consultation_id, purchase_id, exam_id], `admission_date`↔[consultation_date, purchase_date, exam_date] |
| 2 | `provision/scripts/utils/paths.py` | Nouveau helper `expand_path(value)` : résout le token `{PROJECT_ROOT}` dans les chemins de config |
| 3 | `provision/scripts/ELT/gen_extract_raw.py` | `discover_csv` : `base_dir = expand_path(db_cfg["dir"])` → fin des chemins absolus VM en dur |
| 4 | `provision/scripts/ELT/create_silver.py` | Lien FK patient : priorité `table_mappings[source][table].fk_to_patient` (chargé depuis `fhir_entities.json`) sinon heuristique (`meilleure_colonne_patient_id`) — l'heuristique seule rate `customer_id`/`patient_code` |
| 5 | `provision/config/data_sources.example.json` | Remplacé par les 3 sources CSV du générateur (`type=csv`, `dir={PROJECT_ROOT}/evaluation/...`, tables patients + événement) |
| 6 | `provision/config/data_sources.mavis.example.json` | Nouveau : exemples avancés MAVIS + MMT_DB (postgres), documentés comme optionnels |
| 7 | `provision/config/data_sources.json` | (non committé) mis à jour à l'identique de l'exemple |
| 8 | `provision/scripts/ensure_generator_data.sh` | Nouveau — étape 0 : vérifie les CSV des 3 sources, régénère avec `--seed 42` (`GENERATOR_PATIENTS`, défaut 500) si un fichier manque |
| 9 | `provision/scripts/run_pipeline.sh` | Étapes renumérotées [0/5]→[4/5] ; ajout de l'appel `ensure_generator_data.sh` |
| 10 | `GUIDE/guide-vagrant.md` | Schéma flux (générateur + étapes 0-4/5), §3 (token `{PROJECT_ROOT}`, MAVIS/MMT_DB optionnels), §5 (données générateur auto), §6 (durées), §7 (validation SILVER encounters + GOLD), §7 fichiers, §8 ports, §2 avertissements |
| 11 | `GUIDE/guide-generateur-donnees.md` | §3.3 « Lien avec le pipeline ELT » : les CSV `data/raw/` sont le point d'entrée du pipeline (jamais `ground_truth`) |
| 12 | `projet/code-source/README.md` | Structure (5 étapes + mavis example) ; note data_sources = générateur par défaut |
| 13 | `GUIDE/README.md` | Ligne guide-vagrant mise à jour (générateur au lieu de MMT_DB) |

**Vérifications :** `py_compile` OK (paths, gen_extract_raw, create_silver) ; les 4 JSON valides
(`fhir_entities.json` : nouvelles tables → Encounter + FK, nouveaux synonymes chargés via `fhir_schema`) ;
`expand_path` testé (`{PROJECT_ROOT}` → root réel, chemin simple inchangé) ; `bash -n` (Git Bash) OK sur
les 2 scripts ; `select_columns` (gen_fhir_mapping) simulé : encounter_id/admission_date détectés pour les
3 tables événements — note : `source_patient_id` est forcé par `create_silver` (FK config), le mapping
`gen_fhir_mapping` ne contient pas ce champ (FHIR_FIELDS Encounter sans source_patient_id) → cohérent.

**Résultat :** config-only pour les mappings événements + étape 0 déterministe (seed 42). Validation finale
sur VM : `ensure_generator_data.sh` → `run_pipeline.sh` → attendre `datalake_silver.encounter_fhir > 0` et
`datalake_gold.patient_events_gold > 0`. Commits : doc sync en attente (9 fichiers), celui-ci à créer.

---

## 10/09/2026 — Synchronisation de la documentation avec la refonte config (onboarding nouveau dev)

**Contexte :** rendre le dépôt « auto-lançable » par un développeur qui dispose déjà de Vagrant et des
librairies Python installées : la doc doit refléter `pipeline.yaml`, `fhir_entities.json` et `paths.py`
(commés), et la seule config à créer doit rester `data_sources.json`.

| # | Fichier | Modification |
| - | ------- | ------------ |
| 1 | `projet/code-source/README.md` | Structure : `config/` = pipeline.yaml + fhir_entities.json (commités) ; `scripts/utils/` += `paths.py`. Note démarrage : pipeline.yaml/fhir_entities.json chargés par `paths.py`, pas besoin de les créer |
| 2 | `ai/dev/architecture.md` | Répertoires clés : `utils/` += paths.py ; `config/` = commités + non commité |
| 3 | `documents/documentation/architecture.md` | Ajout lignes « Configuration pipeline » (pipeline.yaml) et « Config FHIR déclarative » (fhir_entities.json) ; utils += paths.py |
| 4 | `documents/documentation/pipeline_elt.md` | Table utilitaires réécrite (pipeline.yaml, fhir_entities.json, paths.py, fhir_schema depuis JSON) ; piège mémoire → « via pipeline.yaml » |
| 5 | `ai/dev/pipeline_elt.md` | §4 : valeurs Spark désormais centralisées dans pipeline.yaml via paths.py |
| 6 | `GUIDE/guide-vagrant.md` | Schéma flux : CFG = pipeline.yaml + data_sources.json ; §3 : seul `data_sources.json` à créer, pipeline.yaml/fhir_entities.json commités ; §7 fichiers : 2 lignes ajoutées |
| 7 | `GUIDE/README.md` | Bonne pratique : pipeline.yaml + fhir_entities.json commités/modifiables sans toucher au code |
| 8 | `documents/cahier_des_charges.md` | Risque « Mapping incomplet » : `fhir_synonyms.py` + `TABLE_OVERRIDE` → `fhir_entities.json` (synonyms, table_mappings) |

**Vérifications :** greps doc active (GUIDE/, projet/code-source/, ai/dev/ hors logs) : 0 occurrence de
`TABLE_OVERRIDE`, `LINK_ENTITY_OVERRIDE`, `SYNONYMES_COURTS`, `spark_defaults`. Seuls les logs d'historique
les mentionnent (volontaire). `pipeline.yaml`, `fhir_entities.json`, `paths.py` confirmés trackés par git.

**Résultat :** un nouveau développeur (Vagrant + libs Python déjà installés) suit `GUIDE/guide-vagrant.md`
§3→§6 puis `GUIDE/guide-backend.md` avec une seule config à créer (`data_sources.json`) ; le reste du
paramétrage vit dans `pipeline.yaml` et `fhir_entities.json` (commités, tunables). Réalisé.

---

## 10/09/2026 — Refonte config centralisée (pipeline.yaml + paths.py) + entités FHIR déclaratives

**Contexte :** objectif → ajouter une nouvelle table/entité sans "avalanche de fichiers". Consolidation
des configs éparpillées (chemins absolus, noms Hive, Spark, CORS, tranches d'âge, seuils) et des
mappings FHIR (schéma + synonymes + table→entité) dans des fichiers uniques.

| # | Action | Fichiers | Détail |
| - | ------ | -------- | ------ |
| 1 | Config FHIR unique | `provision/config/fhir_entities.json` (nouveau) | Schéma (`entities.*.fields`), synonymes (`synonyms`), mapping table→entité (+FK) (`table_mappings`). Source de vérité pour SILVER |
| 2 | `fhir_schema.py` | `provision/scripts/utils/fhir_schema.py` | `FHIR_FIELDS`/`FHIR_SYNONYMS` désormais chargés depuis `fhir_entities.json` (plus de dict hardcodé) |
| 3 | `fhir_synonyms.py` | `provision/scripts/utils/fhir_synonyms.py` | Simple ré-export (compatibilité imports) |
| 4 | Mapping sans hardcode | `provision/scripts/ELT/gen_fhir_mapping.py` | Suppression de `LINK_ENTITY_OVERRIDE` (dict Python) → lecture `table_mappings` depuis `fhir_entities.json` |
| 5 | Suppression `SYNONYMES_COURTS` | `provision/scripts/ELT/create_silver.py` | Les synonymes proviennent de `FHIR_SYNONYMS` (chargé du JSON) ; import centralisé paths |
| 6 | Config pipeline YAML | `provision/config/pipeline.yaml` (nouveau) | `hdfs`, `hive_dbs`, `tables`, `spark`, `gold.age_tranches`, `silver.fuzzy_threshold`, `api` (CORS/port), `logs` |
| 7 | Chargeur central | `provision/scripts/utils/paths.py` (nouveau) | `PROJECT_ROOT` résolu dynamiquement (plus de `/home/vagrant/...`), constantes + helpers (`hdfs_raw`, `hdfs_warehouse`) |
| 8 | `create_gold.py` | `provision/scripts/ELT/create_gold.py` | `AGE_TRANCHES`, noms Hive, warehouse HDFS, config Spark depuis `paths.py` |
| 9 | `hive_api.py` | `provision/api/hive_api.py` | Noms de tables, `SYNC_METADATA_PATH`, `CORS_ORIGINS`, config Spark depuis `paths.py`. Bug pré-existant corrigé : docstring de `diagnostics_heatmap` non fermée (IndentationError) |
| 10 | `gen_extract_raw.py` | `provision/scripts/ELT/gen_extract_raw.py` | Chemins logs/metadata/config/HDFS depuis `paths.py` (HDFS namenode centralisé) |
| 11 | `sync_utils.py` | `provision/scripts/utils/sync_utils.py` | `SYNC_METADATA_PATH` depuis `paths.py` |
| 12 | `run_pipeline.sh` | `provision/scripts/run_pipeline.sh` | `PROJECT_ROOT` résolu depuis la position du script (`../..`) ou variable d'environnement |

**Vérifications :** `py_compile` OK sur les 9 fichiers modifiés ; chargement de `paths.py` (PROJECT_ROOT,
Hive, GOLD, AGE_TRANCHES, hdfs_raw) OK ; `fhir_schema`/`fhir_synonyms` cohérents (4 entités, 11 synonymes).
Le chemin `run_pipeline.sh → code-source` et le chargement de `pipeline.yaml` ont été testés.
Le test d'import complet échoue uniquement sur l'absence d'`extract_raw_report.json` (métadonnée d'exécution
générée par l'étape RAW sur la VM) — comportement pré-existant, les scripts restent exécutés en module.

**Résultat :** ajouter une table = 1 entrée `table_mappings` + champs dans `fhir_entities.json` + `data_sources.json` ;
plus besoin de toucher aux scripts Python ni aux chemins absolus. Réalisé (refonte) vs à valider (run VM).

---

## 10/09/2026 — Passe lisibilité post-refonte (suppression indirections et doublons)

**Contexte :** après la refonte config centralisée, relecture dans l'objectif « meilleure lecture du code,
sans embrouiller ». Règles appliquées : un seul nom par chose, zéro helper inutilisé,
zéro réaffectation `X = Y`, zéro valeur de config résiduelle en dur.

| # | Action | Fichiers | Détail |
| - | ------ | -------- | ------ |
| 1 | Docstrings/commentaires corrigés | `provision/scripts/utils/paths.py` | `Usage:` avec les vrais noms (`PROJECT_ROOT`, `HIVE_SILVER`, `GOLD_TABLE`, `AGE_TRANCHES`, `hdfs_raw`) ; commentaire de résolution chemin exact (utils → ../../..) |
| 2 | Helper mort supprimé | `provision/scripts/utils/paths.py` | `spark_defaults()` retiré (le style `.config(...)` explicite est plus lisible qu'un dict étalé) |
| 3 | Helper `hdfs_raw` utilisé | `provision/scripts/ELT/gen_extract_raw.py` | 3 constructions `f"{HDFS_NAMENODE}{HDFS_BASE}/raw/..."` → `hdfs_raw(source_name, table_name)` ; imports `HDFS_NAMENODE`/`HDFS_BASE` retirés |
| 4 | Helper `hdfs_warehouse` utilisé | `provision/scripts/ELT/create_gold.py`, `provision/scripts/ELT/create_silver.py` | `f"{HDFS_NAMENODE}{HDFS_BASE}/{zone}/warehouse"` → `hdfs_warehouse("gold"/"silver")` |
| 5 | Doubles noms supprimés | `provision/scripts/ELT/create_gold.py`, `provision/scripts/ELT/create_silver.py` | `SILVER_HIVE_DB = HIVE_SILVER` / `GOLD_HIVE_DB = HIVE_GOLD` supprimés → usage direct de `HIVE_SILVER`/`HIVE_GOLD` |
| 6 | Import inutilisé retiré | `provision/scripts/ELT/create_silver.py` | `DATASOURCES_PATH` importé mais jamais utilisé |
| 7 | API branchée sur la config | `provision/api/hive_api.py` | `timedelta(days=365)` → `DEFAULT_DATE_RANGE_DAYS` ; `port=5000` → `FLASK_PORT` ; docstring « Port : 5000 » → référence `pipeline.yaml` |

**Vérifications :** `py_compile` OK sur les 5 fichiers ; greps : plus aucun `SILVER_HIVE_DB`/`GOLD_HIVE_DB`,
plus aucun `spark_defaults`, plus aucun `days=365`/`port=5000`/`/home/vagrant` résiduel ; chaque import de
`paths.py` = au moins 2 occurrences (import + usage) ; chargement réel de `paths.py` OK
(`hdfs_raw`=hdfs://localhost:9000/datalake/raw/..., `hdfs_warehouse("silver")`=.../silver/warehouse,
FLASK_PORT=5000, DEFAULT_DAYS=365, AGE_TRANCHES chargées). Clés `flask_port`, `default_date_range_days`
présentes dans `pipeline.yaml`.

**Résultat :** un seul nom par chose, helper déclaré = helper utilisé, zéro hardcodé résiduel côté
API/ELT. Réalisé ; run VM inchangé (toujours à valider).

---

## 09/09/2026 — Regroupement des guides techniques dans `GUIDE/`

**Contexte :** création de guides complets (Vagrant, générateur de données, frontend, backend), avec
vérification des documents existants et améliorations ciblées. Regroupés dans le nouveau répertoire
`GUIDE/`.

| # | Action | Fichiers | Détail |
| - | ------ | -------- | ------ |
| 1 | Guide Vagrant | `GUIDE/guide-vagrant.md` (nouveau) | Basé sur l'archive `archives/datalake_mavis/demarrage vagrant.md`, adapté au dépôt consolidé : chemins `Mon_Memoire/projet/code-source`, synced folder, VM `/home/vagrant/datalake-final`, `data_sources.example.json`, run de référence 214/145/69, section dépannage |
| 2 | Guide générateur | `GUIDE/guide-generateur-donnees.md` (nouveau) | Modules réels (`generator.*`), seed/patients, niveaux easy/medium/hard, paramètres `config/settings.py`, `evaluate_engine.py` comme point d'entrée, résultats P/R/F1 de référence |
| 3 | Guide frontend | `GUIDE/guide-frontend.md` (nouveau) | Next.js : installation, `.env`, Prisma, comptes seed, structure, RBAC, routes RMA, dépannage |
| 4 | Guide backend | `GUIDE/guide-backend.md` (nouveau) | API Flask : prérequis GOLD/Hive, lancement, `test_startup.sh`, endpoints RMA + gouvernance, flag `RMA_USE_MOCK`, tests, limites |
| 5 | Index | `GUIDE/README.md` (nouveau) | Index croisé + schéma de flux + table des chemins consolidés + bonnes pratiques transverse |
| 6 | Améliorations existants | `projet/code-source/provision/api/README.md`, `projet/code-source/evaluation/synthetic-patient-generator/README.md` | API : sortie `12/12` → `14/14` (14 tests réels des endpoints). Générateur : retrait des références inexistantes `main.py` et `pytest.ini`, ajout de `evaluate_engine.py` comme chemin officiel, lien vers `GUIDE/` |

**Vérifications :** comptage réel des tests du générateur (`tests/` = **44 collectés**) ; endpoints API
(11 `@app.route` + 3 variantes paramétrées = **14 tests**) ; flag `RMA_USE_MOCK` lu dans
`hive_api.py:55` ; chemins du synced folder croisés avec `Vagrantfile` ; run de référence croisé avec
`ai/memoire/contexte_projet.md` (214/145/69, total_admissions). Aucune donnée sensible ajoutée.

**Résultat :** 5 fichiers `GUIDE/` créés, 2 README existants corrigés. Guides cohérents avec le dépôt
consolidé (chemins actuels), réalisé vs simulé distingué.

---

## 09/09/2026 — Volet académique : harmonisation + rapport + slides + docx

**Contexte :** focus sur le livrable académique (mémoire) après validation de la fusion technique.
Quatre volets exécutés, toutes les données re-vérifiées contre le code.

| # | Action | Fichiers | Détail |
| - | ------ | -------- | ------ |
| 1 | Harmonisation comptes tests | `chapters/06-tests.md`, `ai/memoire/contexte_projet.md`, `projet/code-source/README.md`, `ai/dev/README.md`, `ai/dev/methode_codage.md` | Moteur passé de « 12/12 (matcher 9) » / « 15/15 » à **23/23** (matcher 12 + consent 3 + canonique 8, `test_deduplication.py`) — chiffres réels comptés dans les fichiers de test |
| 2 | Vérification cohérence | `chapters/04-conception.md`, `chapters/05-realisation.md` | Confirmés : weights 0.5/0.3/0.1/0.1, `matching_key=(birth_date,cin,nom)`, run VM 214/145/69, P-R-F1 hard 1.000/0.422/0.594 ; datations chapitres OK |
| 3 | Rapport de stage | `documents/rapport_stage.md` (nouveau) | Synthèse MBDS : contexte, problématique, démarche 3 niveaux, conception, réalisation chiffrée, évaluation, limites honnêtes, perspectives |
| 4 | Slides soutenance | `documents/slides_soutenance.md` (nouveau) | Esquisse ~13 slides en 4 parties (métier / technique / démo reproductible / conclusion) avec supports et preuves par slide |
| 5 | Conversion docx | `projet/code-source/scripts/dev/export_memoire_docx.py` (nouveau) → `documents/memoire_M2_MBDS.docx` | Convertisseur Markdown→docx (python-docx) : titres, tableaux (27), listes, blocs code ; Mermaid conservés en texte ; validé (6 chapitres, accents OK) |

**Vérifications :** comptage réel des tests (`def test_` = matcher 12 · consent 3 · canonique 8 = 23) ;
lecture intégrity du `.docx` par python-docx (6 titres H1, 27 tables, 37 296 caractères, accents UTF-8
préservés) ; aucune donnée sensible ajoutée.

**Résultat :** livrables académiques complétés (rapport + slides + docx) ; comptes de tests alignés sur
le code dans toute la doc. Reste pour l'utilisateur : relecture mémoire, ajustement des slides, mise en
page finale du `.docx`.

---

## 09/09/2026 — Diagramme de flux : sources génériques + évaluation ground-truth

**Contexte :** mise à jour de `diagramme_flux_donnees.md` (schéma Mermaid du mémoire) pour refléter deux
écarts entre le plan et l'état réel du code : sources non figées aux trois bases de démo et module
d'évaluation absent du schéma.

| # | Action | Fichiers | Détail |
| - | ------ | -------- | ------ |
| 1 | Sources génériques | `diagramme_flux_donnees.md` | `Base A` / `Base B` / `Base C` au lieu de PostgreSQL MAVIS / MMT_DB / SQLite CLINIQUE (plateforme agnostique, sources configurables) |
| 2 | Évaluation intégrée | `diagramme_flux_donnees.md` | Sous-graphe `EVAL` : générateur synthétique easy/medium/hard → ground truth → comparateur P/R/F1 → `evaluation_truth.md` ; relié au moteur de déduplication (`evaluate_engine.py`, Spark+MVP) ; ground truth jamais fourni au moteur |
| 3 | Validation Mermaid | `diagramme_flux_donnees.md` | Re-parsing via harnais jsdom + mermaid → `PARSE_OK` ; indices `linkStyle` recalculés (5 dédup, 9 RBAC, 18 comparaison GT) |

**Vérifications :** `node validate.mjs` sur le bloc mermaid extrait du fichier → `PARSE_OK` ; aucun
changement de code source ; état Git contrôlé avant modification.

**Résultat :** schéma du mémoire cohérent avec `projet/code-source/evaluation/` (ground truth réservé à
l'évaluation) et la généricité des sources (AGENTS.md / `data_sources.json`).

---

## 08/09/2026 — Renforcement des instructions AI

**Contexte :** mise en cohérence des consignes du dépôt avec les règles de projet fournies, sans
modifier le code applicatif.

| #   | Action                    | Fichiers                                                                                                     | Détail                                                                                            |
| --- | ------------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------- | ----- | -------------- |
| 1   | Consignes globales        | `AGENTS.md`, `ai/dev/README.md`                                                                              | Hiérarchie, validation ciblée, Git, preuves, archives et périmètre des données synthétiques       |
| 2   | Qualité et sécurité       | `ai/dev/methode_codage.md`, `ai/dev/security.md`                                                             | Pyramide de tests, tests négatifs, modèle de menace, moindre privilège et cycle de vie des tokens |
| 3   | Big Data et déduplication | `ai/dev/pipeline_elt.md`, `ai/dev/deduplication.md`                                                          | Mesures de performance, blocking, calibration et nomenclature `new_master                         | exact | probabilistic` |
| 4   | Mémoire et archives       | `ai/memoire/README.md`, `ai/memoire/methode.md`, `projet/mvp/AGENTS.md`, `archives/datalake_mavis/AGENTS.md` | Vocabulaire MPI, démonstration reproductible et portée historique explicite                       |

**Vérifications :** `new_master`, `exact` et `probabilistic` confirmés dans le moteur et `sql/schema.sql`;
état Git contrôlé avant modification; aucune donnée sensible ajoutée.

**Résultat :** instructions AI enrichies et cohérence documentaire renforcée. Les compteurs et statuts
du suivi existant n'ont pas été réécrits afin de préserver les modifications déjà présentes.

---

## 07/09/2026 — Fusion docs (Phase 1) + instructions IA (Phase 2) + guide technique

**Contexte :** poursuite de la fusion `datalake_mavis` + `test_bigdata` → `data_lake_final`.
Les docs des deux projets ont été consolidées en un seul jeu logique (pas de doublons LOG.md/LOGS.md,
SUIVI_AVANCEMENT/SUIVI-AVANCEMENT).

| #   | Action                       | Fichiers                                                                                                                                                          | Détail                                                                                                 |
| --- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| 1   | Lecture des sources doc      | `datalake_mavis/*.md`, `.ai_context/*`, `provision/api/README.md` ; `Mon_Memoire/projet/code-source/*.md`, `ai_context/*.md` ; `Plateforme…(1).md`                | Extraction du contenu utile des 2 projets                                                              |
| 2   | Cahier des charges consolidé | `documents/cahier_des_charges.md`                                                                                                                                 | Fusion CAHIER_DE_CHARGE Mavis + Plateforme test_bigdata ; périmètre, architecture, planning, métriques |
| 3   | Manuel conceptuel (7 thèmes) | `documents/documentation/architecture.md`, `bigdata_concepts.md`, `pipeline_elt.md`, `deduplication.md`, `consentement_gouvernance.md`, `api.md`, `evaluation.md` | Une doc par thème, sources croisées des 2 projets                                                      |
| 4   | Instructions IA mémoire      | `ai/memoire/README.md`, `contexte_projet.md`, `methode.md`                                                                                                        | Rédaction du mémoire, pointe vers `Mon_Memoire/`                                                       |
| 5   | Instructions IA dev          | `ai/dev/README.md`, `architecture.md`, `pipeline_elt.md`, `deduplication.md`, `methode_codage.md`, `security.md`, `logs.md`, `suivi_avancement.md`                | Fusion des `.ai_context` des 2 projets (commités ici)                                                  |
| 6   | Guide technique code         | `projet/code-source/README.md` + `pyproject.toml`                                                                                                                 | Packaging `engine` local (`pip install -e ".[test]"`), structure, démarrage VM                         |

**Vérifications :** `pytest` moteur déjà 9/9 avant session (matcher 6 + consent 3) ; lecture complète des
sources effectuée ; chemin relatifs des liens inter-docs contrôlés.

**Résultat :** Phases 1 et 2 terminées. Prochaine étape : Phase 5 (intégration SILVER/GOLD + API
gouvernance) puis Phase 6 (évaluation + commit git initial).

---

## 07/09/2026 — Phase 5 : intégration SILVER/GOLD + API gouvernance

**Contexte :** relier le pipeline ELT au moteur de déduplication explicable et refléter le consentement
en couche GOLD, avec endpoints de gouvernance (fallback mock), puis uniformiser les chemins VM
(`/home/vagrant/datalake-mavis` → `/home/vagrant/datalake-final`).

| #   | Action                         | Fichiers                                                                                                                                                                                                                                          | Détail                                                                                                                                                                                                                             |
| --- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Enrichissement SILVER / moteur | `provision/scripts/ELT/create_silver.py`                                                                                                                                                                                                          | `_source_system` par source ; fin de boucle → `enrichir_dedup_moteur()` (engine `deduplicate`) → colonnes `master_patient_id`, `match_method`, `match_score` ; `is_duplicate` recalculé côté moteur ; garde si moteur/patient vide |
| 2   | Consentement GOLD              | `provision/scripts/ELT/create_gold.py`                                                                                                                                                                                                            | `charger_consent_gold()` : `datalake_gold.patient_consent_gold` = consent PostgreSQL central (`DATABASE_URL`, psycopg) LEFT JOIN masters SILVER ; schéma créé même si vide (API → mock)                                            |
| 3   | Endpoints gouvernance          | `provision/api/hive_api.py` + `provision/api/mock_data.py`                                                                                                                                                                                        | `GET /api/governance/duplicates` (KPI SILVER + by_method) et `GET /api/governance/consent` (list + stats) ; mocks `MOCK_GOVERNANCE_DUPLICATES` + `MOCK_CONSENT`                                                                    |
| 4   | Chemins VM uniformisés         | `create_silver.py`, `create_gold.py`, `gen_extract_raw.py`, `gen_fhir_mapping.py`, `sync_utils.py`, `hive_api.py`, `Vagrantfile`, `bootstrap.sh`, `run_pipeline.sh`, `capture_mavis_schema.sh`, `test_api.sh`, `api/test_api.py`, `api/README.md` | `/home/vagrant/datalake-mavis` → `datalake-final` ; Vagrantfile monte `data_lake_final/projet/code-source` ; `ELT.before/` et `front-optional/todo.md` laissés tels quels (archives)                                               |
| 5   | Docs mises à jour              | `documents/documentation/pipeline_elt.md`, `api.md`                                                                                                                                                                                               | Étapes 3/4 SILVER-GOLD (moteur + consent GOLD), endpoints gouvernance, flux fichiers                                                                                                                                               |

**Vérifications :** `ast.parse` OK sur les 4 fichiers Python modifiés ; aucune chaîne `datalake-mavis`
restante dans les scripts opérationnels (hors archives).

**Résultat :** Phase 5 terminée. Prochaine étape : Phase 6 (évaluation easy/medium/hard, tests API/parité,
commit git initial).

---

## 07/09/2026 — Phase 6 (partiel) : évaluation + tests

**Contexte :** valider localement le moteur fusionné avant commit git initial.

| #   | Action                  | Fichiers                                                              | Détail                                                                                                                                               |
| --- | ----------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Correction TOML         | `projet/code-source/pyproject.toml`                                   | `description` reformatée (contenu multi-lignes invalide → une seule chaîne)                                                                          |
| 2   | Tests unitaires         | `projet/code-source`                                                  | `pytest` → **9/9 PASS** (matcher 6 + consent 3)                                                                                                      |
| 3   | Évaluation ground truth | `evaluation/evaluate_engine.py` (easy/medium/hard)                    | P/R/F1 : easy & medium 1.000/1.000/1.000 ; hard 1.000/0.287/0.447 (zéro FP) ; **parité MVP=Spark parfaite** ; rapport régénéré `evaluation_truth.md` |
| 4   | 2 issues locales        | `documents/documentation/evaluation.md`, `ai/dev/suivi_avancement.md` | Résultats de référence documentés ; warning : console Windows cp1252 → lancer avec `PYTHONIOENCODING=utf-8`                                          |

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

| #   | Action                             | Fichiers                                                                  | Détail                                                                                                                                                                                                                         |
| --- | ---------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Harmonisation chiffrée             | `ai/memoire/contexte_projet.md`, `documents/cahier_des_charges.md`        | Éval 07/09 : P 1.000 / R 0.287 / F1 0.447, exact 1.000/0.737/0.848, probabilistic 1.000/0.667/0.800, rappel par source 0.299/0.286/0.276, TP209/FP0/FN518, 869 masters, 500 groupes, 1 057 enreg. ; run fusion 214/145/69 doc. |
| 2   | Chapitre 1 rédigé (07/09)          | `Mon_Memoire/chapters/01-introduction.md`                                 | Contexte MMT, problématique, objectifs, démarche 3 niveaux (1 Mermaid), périmètre, plan du mémoire                                                                                                                             |
| 3   | Chapitre 2 + bibliographie (08/09) | `Mon_Memoire/chapters/02-etat-de-l-art.md`, `references/bibliographie.md` | ER/Record Linkage, similarités (RapidFuzz), blocking, MPI + FHIR, RGPD, HDFS/Spark/Hive, Medallion, positionnement + 1 Mermaid ; réf. [B1..B12]                                                                                |
| 4   | Chapitre 3 rédigé                  | `Mon_Memoire/chapters/03-analyse.md`                                      | Sources + hétérogénéité (colonnes réelles), générateur seed 42 (500 masters, 404/353/300, easy/medium/hard 10/30/50 %), exigences, contraintes VM/MAVIS + 1 Mermaid                                                            |
| 5   | Chapitre 4 rédigé                  | `Mon_Memoire/chapters/04-conception.md`                                   | Architecture 3 niveaux + 1 Mermaid, `CanonicalPatient`, blocking + exact/probabiliste (0.50/0.30/0.20, seuil 0.80), schéma PG, gouvernance, Medallion                                                                          |
| 6   | Chapitre 5 rédigé                  | `Mon_Memoire/chapters/05-realisation.md`                                  | Générateur, ELT 4 étapes + 1 Mermaid, moteur Pandas/Spark, PG/GOLD, API 11 endpoints + 14/14, incidents (11 614, vboxsf, JAVA_HOME, HS2)                                                                                       |
| 7   | Chapitre 6 rédigé                  | `Mon_Memoire/chapters/06-tests.md`                                        | Stratégie + 1 Mermaid, éval ground-truth P/R/F1 (easy/medium/hard), breakdown, parité MVP=Spark, limites (recall hard, GOLD sparse)                                                                                            |
| 8   | Faits collectés                    | 2 rapports agents explore                                                 | Sources/générateur/contraintes (ch.03) ; moteur/pipeline/schéma/gouvernance/API/incidents (ch.04/05) + doc `evaluation.md`                                                                                                     |

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

| #   | Action                             | Fichiers                                            | Détail                                                                                                                                                                                                                                                                                                                                         |
| --- | ---------------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Cause racine + fix explosion 11614 | `provision/scripts/ELT/create_silver.py`            | `patient_uuid` **exclu du mapping FHIR dynamique** (`meilleure_colonne_attendue` le détournait sur la colonne ID → `source_patient_id` renommée/`name` NULL → préfixe concat = `"pharmacy"` → join moteur 76×76) ; garde-fou `colonnes_source_utilisees` (une colonne source renommée une seule fois)                                          |
| 2   | Écritures SILVER fiabilisées       | `create_silver.py`                                  | Accumulation par entité (`accum_par_entite`) + **une seule écriture `mode="overwrite"`** par table cible ; enrichissement moteur via `patient_fhir__dedup_tmp` + `DROP TABLE` + `ALTER TABLE … RENAME TO` (évite `Cannot overwrite table being read`) ; compteurs moteur pré-écriture ; `marquer_doublons_patients` sur l'union toutes sources |
| 3   | GOLD tolérant (patients-only)      | `provision/scripts/ELT/create_gold.py`              | `_lire_silver` tolérant + `_vide` (Encounter/Condition/Observation absents) ; `SystemExit(1)` si `patient_fhir` absente ; consent `dropDuplicates(["master_patient_id"])`                                                                                                                                                                      |
| 4   | Run pipeline                       | `provision/scripts/run_pipeline.sh`                 | 4 étapes vertes : **`✅ Pipeline ELT complet : RAW -> SILVER -> GOLD OK`** (logs `provision/logs/{elt.log, create_gold.log}`)                                                                                                                                                                                                                  |
| 5   | Validation Spark                   | `provision/metadata/check_data.py` + `run_check.sh` | `silver_patient_fhir` **214** (76/76/62), masters 145, doublons 69, méthodes exact 69 / new_master 145, scores 1.0, uuids uniques ; gold patients-only → events 0, consent 145                                                                                                                                                                 |
| 6   | API réelle                         | `provision/metadata/start_api.sh`                   | `RMA_USE_MOCK=false` ; health `GET /rma/last_sync` 200 ; `python -m provision.api.test_api` → **14/14 PASS (0 FAIL)**                                                                                                                                                                                                                          |
| 7   | KPIs gouvernance réels             | `provision/api/hive_api.py`                         | `duplicates`: exact 69 / new_master 145, taux 32.24 % ; `consent`: 145 patients (`granted` NULL, PostgreSQL non alimenté) — `mocked: false`                                                                                                                                                                                                    |
| 8   | Doc pipeline mise à jour           | `documents/documentation/pipeline_elt.md`           | Section « Validation VM (interim CSV) » + pièges anti-régression (patient_uuid, overwrite unique, tmp+rename)                                                                                                                                                                                                                                  |

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

| #   | Action                             | Fichiers                                                                                                                                    | Détail                                                                                                                                                  |
| --- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Import `data_lake_final`           | `git subtree add --prefix=atelier` (commit `3a303dd`) + commit `8a0a217`                                                                    | Historique git préservé (a2c7250→2004865) ; renaming `git mv` (atelier→documents/, ai/, projet/) ; 219 fichiers                                         |
| 2   | PoC `test_bigdata` → `projet/mvp/` | commit `3b31559`                                                                                                                            | 112 fichiers, rename 100 % ; purge `.venv`/`.pytest_cache`/`.env`                                                                                       |
| 3   | Secret/artefacts hors suivi        | `data_sources.json`, `cim_embeddings.pkl`, `documents/*.docx`, `.gitignore`                                                                 | `git rm --cached` conformément AGENTS ; règles `.gitignore` ajoutées (pkl, docx externe utilisateur)                                                    |
| 4   | Archive `datalake_mavis`           | `archives/datalake_mavis/` (commit `ad862c5`)                                                                                               | Source seule (docs, provision, visualisation_app) ; exclus `.git`, venv/node_modules, logs, metadata, rapports d'autres étudiants (docs/ 47 Mo) ; ~5 Mo |
| 5   | Références dépôt unique            | `chapters/02/03/05`, `README.md`, `AGENTS.md`, `cahier_des_charges.md`, `ai/memoire/*`, `documentation/*`, `Vagrantfile` (commit `a15deda`) | Liens chapitres réécrits (`../projet/code-source`, `../documents`), prose ch.01 neutralisée, chemin hôte Vagrantfile → `Mon_Memoire/projet/code-source` |
| 6   | Suppression anciens répertoires    | `datalake_mavis` (supprimé) ; `data_lake_final` (vidé)                                                                                      | `datalake_mavis` supprimé ; coquille `data_lake_final` vide verrouillée par un process externe (suppression manuelle restante)                          |

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

| #   | Action                         | Fichiers                                                                                                                                                                                                 | Détail                                                                                                                                                                                                                                                                                                                                                                        |
| --- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Générateur (CIN/ville)         | `evaluation/synthetic-patient-generator/config/settings.py`, `patient_generator.py`, `common.py`, `variation_engine.py`, 3 générateurs sources                                                           | `MasterPatient.cin/birth_city` ; `_generate_mg_cin` ; CIN absent décidé au maître (jamais « sali ») ; `make_missing` cible naissance/ville ; `cin_format` remplace `phone_format` ; tests → **pytest 44/44**                                                                                                                                                                  |
| 2   | Moteur (canonical + matcher)   | `engine/identity/canonical.py`, `matcher.py`, `spark_dedup.py`, `__init__.py`                                                                                                                            | `CanonicalPatient` cin/birth_city ; `matching_key (birth_date, cin, nom)` ; poids **0.5/0.3/0.1/0.1** ; règle exacte « naissance + CIN non vide » ; `_MasterIndex._by_cin` ; `_cin` remplace `_phone` ; **parité Spark** conservée ; `tests/test_matcher.py` **9 cas** (dont formats CIN, ville, CIN différents→non fusion) → **pytest moteur 12/12** (matcher 9 + consent 3) |
| 3   | Pipeline/schéma                | `sql/schema.sql`, `provision/scripts/utils/fhir_schema.py`, `fhir_synonyms.py`, `provision/scripts/ELT/create_silver.py`, `evaluate_engine.py`, `README.md`                                              | colonnes `cin`/`birth_city` ; Patient FHIR (sans phone) ; synonymes ; `from_dict` COLS ; compteurs 12/12                                                                                                                                                                                                                                                                      |
| 4   | Réévaluation                   | données régénérées (seed 42) ; `evaluate_engine.py` easy/medium/hard ; `evaluation_truth.md`                                                                                                             | Nouveaux chiffres hard : **TP 307 / FP 0 / FN 420, 804 masters → P 1.000 / R 0.422 / F1 0.594** ; exact 1.000/0.854/0.921 ; probabilistic 1.000/0.533/0.696 ; rappel source 0.422/0.422/0.423 ; medium 554/643/84 → 1.000/0.884/0.939                                                                                                                                         |
| 5   | Docs & mémoire (harmonisation) | `chapters/01..06.md`, `documents/cahier_des_charges.md`, `documents/documentation/{deduplication,architecture,evaluation}.md`, `ai/memoire/contexte_projet.md`, `ai/dev/{deduplication,architecture}.md` | suppression téléphone → CIN/ville ; poids 0.5/0.3/0.1/0.1 ; seuil 0.80 ; cas Jean Rakoto (exact CIN) ; nouveaux chiffres éval ; compteurs 12/12                                                                                                                                                                                                                               |
| 6   | Legacy                         | `provision/db/rebuild_*.py`, `provision/scripts/ELT.before/`                                                                                                                                             | **non modifiés** (outils démo de bases legacy, hors chaîne master-patient active)                                                                                                                                                                                                                                                                                             |

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

| #   | Action                 | Fichiers                                                                  | Détail                                                                                                                                                                                                                                                  |
| --- | ---------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Config YAML créée      | `projet/code-source/config/deduplication.yaml`                            | `threshold: 0.80` ; `weights {name 0.5, birth_date 0.3, cin 0.1, birth_city 0.1}` ; `blocking.name_prefix_len: 4`                                                                                                                                       |
| 2   | Loader engine          | `engine/identity/config.py`                                               | `DedupConfig` + `load_dedup_config()` (cache) ; résolution du YAML relative au dépôt code-source ; **fallback défauts** si fichier absent/illisible/PyYAML absent (aucun crash, comportement inchangé) ; compatible Python 3.8                          |
| 3   | matcher.py             | `engine/identity/matcher.py`                                              | `_similarity(..., weights)` ; `_name_prefix(..., prefix_len)` ; `_MasterIndex(prefix_len)` ; `deduplicate(patients, probabilistic_threshold=None, weights, name_prefix_len)` — rétro-compatible (`deduplicate(patients)` et `(patients, 0.80)` valides) |
| 4   | spark_dedup.py         | `engine/identity/spark_dedup.py`                                          | Même threading `threshold/weights/name_prefix_len` ; `_BoundedMasterIndex(prefix_len)` ; partage `_similarity(..., weights)` — **parité préservée**                                                                                                     |
| 5   | Lecture réelle du YAML | `evaluation/evaluate_engine.py`, `provision/scripts/ELT/create_silver.py` | MVP et Spark dédup parametrés par le config chargé ; SILVER garde le fallback ImportError existant (VM sans PyYAML/moteur → mode dégradé)                                                                                                               |
| 6   | Dépendance             | `pyproject.toml`                                                          | `PyYAML>=6.0,<7.0` ajouté aux `dependencies`                                                                                                                                                                                                            |
| 7   | Tests +3               | `tests/test_matcher.py`                                                   | lecture du YAML (valeurs courantes), fallback sur fichier manquant, changement de décision via override `weights`                                                                                                                                       |
| 8   | Docs                   | `documents/documentation/deduplication.md`, `ai/dev/deduplication.md`     | Poids/seuil référencés **par le YAML** (source de vérité), valeurs courantes affichées pour lecture                                                                                                                                                     |

**Vérifications :** `pytest` moteur **15/15 PASS** (matcher 12 + consent 3) + générateur **44/44** ;
`evaluate_engine.py --level hard` → **parité exacte avec le run précédent** : TP=307 FP=0 FN=420,
P 1.000 / R 0.422 / F1 0.594, 804 masters, rappel source 0.422/0.422/0.423 (preuve : refactor sans
changement de comportement) ; `evaluation_truth.md` régénéré (mêmes chiffres).

**Résultat :** la calibration de la déduplication est désormais **déclarative** (1 fichier YAML) — le
coût d'une future modification de poids/seuil/préfixe est ramené à l'édition du YAML + le tableau de
référence dans `deduplication.md`, sans toucher au code ni aux chapitres. Commits en attente.

---

## 08/09/2026 — Incident secrets en dur : purge + externalisation + garde anti-fuite

**Contexte :** audit de l'arbre de travail → `provision/mavis_diag.py` (2 copies, code-source + archive)
contenait un couple SSH réel en dur (identifiant et mot de passe, hôte distant),
committé et **poussé sur `origin`** (dépôt privé). Les scripts `provision/db/rebuild_{mmt,mavis}_db.py`
(4 copies) contenaient aussi le mot de passe PG local. Décisions utilisateur : dépôt privé →
**pas de réécriture d'historique** ; purge de l'arbre de travail + rotation ; suppression/externalisation ;
prévention oui ; purge **y compris l'archive**.

| #   | Action                       | Fichiers                                                                                                                               | Détail                                                                                                                                                                                                                                                                     |
| --- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Suppression                  | `projet/code-source/provision/mavis_diag.py`, `archives/datalake_mavis/provision/mavis_diag.py`                                        | Script SSH de diagnostic **orphelin** (0 référence) → supprimé (2 copies)                                                                                                                                                                                                  |
| 2   | Externalisation mot de passe | `projet/code-source/provision/db/rebuild_mmt_db.py`, `rebuild_mavis_db.py` + copies `archives/datalake_mavis/provision/db/`            | Affectation du mot de passe remplacée par `os.getenv("PGPASSWORD")` (chargé via `dotenv.load_dotenv` depuis `projet/code-source/.env`, gitignoré) ; fail fast `sys.exit` si absent ; `PGHOST/PGPORT/PGUSER` overridables ; `dbname` conservé en dur (propre à chaque base) |
| 3   | Template env                 | `projet/code-source/provision/.env.example`                                                                                            | Variables `PGHOST/PGPORT/PGUSER/PGPASSWORD` documentées — le vrai `.env` reste gitignoré                                                                                                                                                                                   |
| 4   | Trouage docs                 | `archives/datalake_mavis/demarrage vagrant.md`, `LOG.md`, `visualisation_app/README.md`, `projet/code-source/front-optional/README.md` | Valeurs sensibles remplacées par des placeholders (DSN sans mot de passe) ; `NEXTAUTH_SECRET` remplacé par un placeholder de génération                                                                                                                                    |
| 5   | Garde anti-fuite             | `githooks/pre-commit`, `AGENTS.md`, `.gitattributes`                                                                                   | Hook pre-commit (sh) bloquant les identifiants connus, les affectations littérales et les DSN avec mot de passe ; activé `git config core.hooksPath githooks` ; `eol=lf` forcé (`.gitattributes`) ; règle AGENTS enrichie                                                  |

**Vérifications :** hook testé 3 scénarios — (1) secret réel et DSN contenant un mot de passe → **bloqués
(exit 1)** ; (2) placeholders `<PASSWORD>` / `<GENERATE_A_RANDOM_64_HEX_VALUE>` → **acceptés** ; (3)
auto-scan du hook lui-même → **passé** (marqueurs `# secret-scan:ignore`) ; `git grep` final : **0
occurrence** d'identifiants connus et d'affectations de mots de passe littérales dans l'arbre de travail.

**Résultat :** dépôt exempt de secrets en dur (chaîne live + archive, placeholders documentés).
**À faire côté utilisateur :** faire tourner les identifiants du serveur distant (le couple a été
poussé sur GitHub, même privé) et recréer `projet/code-source/.env` avec `PGPASSWORD`.

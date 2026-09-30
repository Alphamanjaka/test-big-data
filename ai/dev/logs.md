# Logs — journal d'activité

Journal unique de toutes les sessions, fixes, incidents et runs du projet (dépôt unique `Mon_Memoire`).
Format : entrée datée (tableau action/fichiers/détail) + vérifications + résultat.
Ne jamais y mettre de données sensibles.

---

## 10/09/2026 — Documentation : schémas Mermaid ajoutés (4 documents conceptuels)

**Contexte :** enrichir le manuel conceptuel avec des schémas rendus (GitHub/VS Code) en remplacement
de chaînes de texte / diagrammes ASCII.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `documents/documentation/evaluation.md` | §1 flowchart générateur → ground truth (jamais fourni à l'algo) → P/R/F1 ; §2 flowchart TP/FP/FN → métriques ; §3 pie chart contribution par source (rappel hard) |
| 2 | `documents/documentation/deduplication.md` | §1 flowchart chaîne de traitement ; §5 flowchart décision exact → probabiliste → seuil 0.80 ; §6 flowchart identity map → master patient (exemple Jean Rakoto) |
| 3 | `documents/documentation/architecture.md` | §1 flowchart TB d'ensemble (diagramme ASCII remplacé) : sources → RAW/SILVER/GOLD → moteur → PostgreSQL → API → frontend ; §4 flowchart Medallion avec enrichissement Phase 5 |
| 4 | `documents/documentation/bigdata_concepts.md` | §1 flowchart progressivité ; §3 flowchart Medallion ; §8 flowchart pivot FHIR (4 entités) ; §9 flowchart Master Data Management / identity map |

**Vérifications :** nombre de blocs ````mermaid` par fichier (2/3/3/4) ; fences ouvertes/fermées
équilibrées (total pair par fichier : 6/8/16/12) ; BOM UTF-8 éliminé sur `architecture.md` (fichier
modifié via PowerShell) pour rester cohérent avec les autres fichiers. Aucun changement de code.

**Résultat :** manuel conceptuel illustré. Commit en attente.

---

## 10/09/2026 — Recension des tables : nouveau doc `documents/documentation/bases_de_donnees.md`

**Contexte :** question utilisateur sur les tables créées en base → inventaire complet des **deux**
systèmes de stockage (PostgreSQL central vs Hive Medallion), jusqu'ici éparpillé entre `schema.sql`,
`fhir_entities.json`, `pipeline.yaml` et les scripts.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Créé `documents/documentation/bases_de_donnees.md` | Recension PostgreSQL (9 tables, ER diagram Mermaid, clés/contraintes) + Hive RAW (bases par source, tables actives générateur + options MAVIS/MMT_DB) + SILVER (4 tables `{entity}_fhir`, colonnes, traçabilité, enrichissement master) + GOLD (`patient_events_gold`, `patient_consent_gold`) + synthèse des flux |
| 2 | `documents/documentation/architecture.md` | Lien §7 + ligne « Pipeline ELT » passée à 5 étapes |
| 3 | `documents/documentation/pipeline_elt.md` | Étapes renumérotées [0/5]→[4/5] (ajout §0 générateur), orchestration/table utilitaires, dette « events vide » marquée résolue (à revalider VM), section « Voir aussi » |

**Vérifications :** colonnes vérifiées à la source (fhir_entities.json, schema.sql, create_silver.py
lignes 86-492, create_gold.py lignes 93-231, gen_extract_raw.py lignes 260-561) ; grep du nombre
d'étapes dans la doc → cohérent (5). Aucun changement de code.

**Résultat :** inventaire unique et à jour du catalogue de tables. Commit en attente.

---

## 10/09/2026 — Archivage : `provision/scripts/ELT.before/` déplacé vers `archives/elt.before/`

**Contexte :** le dossier `projet/code-source/provision/scripts/ELT.before/` (copie des scripts ELT
« avant refonte », committée à l'import `8a0a217`, contenant `create_silver_fk.py` et `gen_metadata.py`)
créait du bruit dans le code actif.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `git mv .../ELT.before → archives/elt.before` | 7 fichiers (7 renames détectés) ; trace historique conservée, hors chemin d'import des modules `provision.scripts.ELT` |

**Vérifications :** `git status` → 7 renommages `R`, aucun import des scripts actifs ne pointe vers
`ELT.before` ; références historiques (`suivi_avancement.md`, entrées précédentes de `logs.md`,
`archives/datalake_mavis/LOG.md`) laissées telles quelles (elles décrivent l'état passé).

**Résultat :** code actif nettoyé ; archive conservée. Commit en attente avec le reste des modifications.

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

## 27/09/2026 - Mémoire : restructuration 01→08, étude de l'existant (ch.3) et conclusion (ch.8)

**Contexte :** le plan du mémoire ne couvrait pas explicitement l'**étude de l'existant** ni la
**conclusion générale** (critères : plan, introduction, état de l'art, étude de l'existant,
architecture, conclusion). Décision utilisateur : chapitre 3 dédié, conclusion autonome en ch.8,
plan étendu en §1.7 uniquement (pas d'ajout de pages liminaires).

| #   | Action                        | Fichiers                                                                                                                                                                                                                              | Détail                                                                                                                                                                                                                                                                  |
| --- | ----------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Renumérotation en 8 chapitres  | `chapters/03-analyse.md`→`04-analyse.md`, `04-conception.md`→`05-conception.md`, `05-realisation.md`→`06-realisation.md`, `06-tests.md`→`07-tests.md`      | `git mv` ; titres, numérotation des sections (3.x→4.x … 6.x→7.x) et renvois internes/externes corrigés dans les 8 chapitres et dans les slides de soutenance                                                                     |
| 2   | Étude de l'existant rédigée   | `chapters/03-etude-existant.md`                                                                                                                                                                                                         | §3.1 systèmes en place : MAVIS (73 090 lignes réplique, 11 tables retenues, 1 260 tables sur le nœud distant, jointure `hms_patient`↔`res_partner` 9 791/9 791), MMT_DB (60 271 lignes, 9 tables GNU Health), CLINIQUE (54 582 lignes, 4 tables SQLite) ; §3.2 solutions du domaine ; §3.3 grille 6 critères ; §3.4 verdict + 1 Mermaid. **Étude documentaire** : aucun produit installé ni exécuté |
| 3   | Bibliographie étendue         | `references/bibliographie.md`                                                                                                                                                                                                            | `[B13..B20]` : InterSystems EMPI, Talend MDM, Splink (IJPDS 2022), HAPI FHIR, Azure Health Data Services, Apache Atlas, GNU Health, applications Odoo — URLs vérifiées ; en-tête redaté        |
| 4   | Plan du mémoire étendu        | `chapters/01-introduction.md`                                                                                                                                                                                                            | §1.7 : une ligne par chapitre (8) + transition explicite vers le ch.8                                                                                                                                                                                                 |
| 5   | Architecture renforcée       | `chapters/05-conception.md`                                                                                                                                                                                                              | §5.1 : chaîne de bout en bout (sources → RAW → SILVER → dédup → GOLD + PostgreSQL) et tableau des composants/ports (HiveServer2 10001, Spark History/UI, PostgreSQL 5432, Flask 5000, FastAPI 8000)                                 |
| 6   | Conclusion générale rédigée  | `chapters/08-conclusion.md`                                                                                                                                                                                                              | §8.1 réponse à la problématique (volet → réalisation → preuve), §8.2 ce que le projet démontre, §8.3 limites assumées (rappel 0.422, `patient_events_gold` 0 ligne, `purpose`/`granted` NULL en GOLD, comparaison documentaire), §8.4 perspectives CT/MT/LT, §8.5 bilan de formation |
| 7   | Synchronisation documentaire | `README.md`, `ai/memoire/README.md`, `ai/memoire/methode.md`, `ai/memoire/contexte_projet.md`, `documents/rapport_stage.md`, `documents/slides_soutenance.md`, `projet/code-source/scripts/dev/export_memoire_docx.py` | Structure 01→08 ; renvois des slides (`05-conception.md` §5.1/§5.3, `06-realisation.md` §6.6, `07-tests.md` §7.2/§7.5) ; chiffres de l'existant ajoutés au contexte projet ; docstring de l'export 01..08                                                  |
| 8   | Correctif encodage UTF-8      | `chapters/01,02,04,05,06,07`, `documents/rapport_stage.md`, `documents/slides_soutenance.md`                                                                                                                                           | `Set-Content -Encoding UTF8` (PS 5.1) avait préfixé un **BOM** : les titres `# Chapitre N` n'étaient plus reconnus et le DOCX ne contenait que **2 H1 sur 8**. BOM retiré sur les 8 fichiers                     |

**Vérifications :** `export_memoire_docx.py` relancé → **8 H1**, 34 tableaux, 50 605 caractères ; scan
de tous les `chapters/0*.md` → 0 anomalie (ni caractères CJK, ni `counted`/`treatée`/`rarely`
résiduels ; les `·` restants sont des séparateurs Mermaid ou de tableaux) ; les 10 renvois
`chapters/0[3-6]-*.md` subsistants sont **dans l'historique de ce fichier** (non modifiés) ;
§8.3 « consentement non alimenté » = `purpose`/`granted` NULL, cohérent avec
`patient_consent_gold` = 145 lignes (`documents/documentation/pipeline_elt.md`, ch.7 §7.5) ;
faux positif écarté sur `documents/documentation/pipeline_elt.md` (BOM préexistant, fichier non
modifié par cette session).

**Résultat :** plan 8 chapitres conforme aux 6 critères ; les 2 chapitres manquants sont rédigés et
le support de soutenance pointe sur les bons fichiers. **Non commité** (validation utilisateur
attendue).

---

## 27/09/2026 — Commit `fb5582c` puis câblage réel du consentement (FastAPI) + axes d'état de l'art

**Contexte :** l'audit du plan d'état de l'art (20 axes) a révélé que le contrôle de consentement
était **conçu mais non appliqué** : `check_consent()` n'était appelée par aucun endpoint. Décision
utilisateur : câbler réellement le consentement, périmètre **FastAPI uniquement** (l'API Flask du PoC
reste hors périmètre), finalités normalisées `api_access` / `research` / `analytics`, preuve par
**tests uniquement** (pas de revendication d'exécution VM).

| # | Action | Fichiers | Détail |
| - | ------ | -------- | ------ |
| 1 | Contrôle de consentement appliqué | `engine/governance/consent.py` | `PURPOSES` (liste fermée), `validate_purpose()` (422), `enforce_consent()` (403, refus par défaut, motif posé sur `request.state`), `consented_master_ids()` (filtrage liste, `DISTINCT ON` + dernier avis) ; `create_consent()` valide aussi la finalité |
| 2 | Endpoints câblés | `engine/governance/app.py` | `purpose` **obligatoire** sur `/patients` et `/patients/{id}` ; liste filtrée, refus 403 ; **correction d'un bug** : `/audit` interrogeait `recorded_at`, colonne inexistante → `accessed_at` |
| 3 | Schéma | `sql/schema.sql` | `consent_purpose_check` (`CHECK` sur la liste fermée, recréé par `DROP CONSTRAINT IF EXISTS`) ; `access_audit` += `purpose`, `refusal_reason` (`ADD COLUMN IF NOT EXISTS`) |
| 4 | Audit tracé | `engine/governance/audit.py` | persistance de `purpose` et `refusal_reason` ; suppression d'un `duration_ms` calculé mais jamais persisté |
| 5 | Seed de démonstration | `provision/db/seed_governance.py` (créé) | schéma idempotent + 3 utilisateurs (clés `secrets.token_hex`, jamais en dur) + consentements **mixtes** déterministes (`api_access` 100 %, `research` 70 %, `analytics` 40 %) ; insertion `WHERE NOT EXISTS` — **aucun** `DELETE` de consentement existant |
| 6 | Tests | `tests/test_governance_api.py`, `tests/test_consent.py` | 13 + 18 cas : 401 (token/clé), 403 rôle, 403 consentement, 422 finalité absente/inconnue, filtrage de liste, régression `accessed_at`, refus par défaut. **Suppression des `dependency_overrides`** : les tests empruntent le vrai chemin `Bearer` → `get_current_user` → `require_role` |
| 7 | Environnement | `provision/.env.example` | `DATABASE_URL` déclaré (exigé par `engine/governance/database.py`) ; **mojibake d'accents** corrigé dans le fichier |
| 8 | Mémoire — axes retenus | `chapters/02-etat-de-l-art.md`, `04-analyse.md`, `08-conclusion.md` | axe 0 (§2.10 protocole de veille + tableau de couverture des 20 axes) · axe 6 (§2.11 matrice de sélection pondérée, 3 arbitrages) · axe 14 (§4.5 contexte local, droit non vérifié signalé) · axe 15 (§4.6 jalons J1→J5) · axe 19 (§8.1 synthèse des arbitrages avec risque résiduel) |
| 9 | Mémoire — corrections de fond | `chapters/02-etat-de-l-art.md` §2.5, `05-conception.md` §5.4/§5.5, `07-tests.md` | l'ancien §2.5 décrivait `data_scope`, validité et `revoked` **inexistants** dans le schéma, et l'audit d'une « durée » non persistée : décrit désormais le comportement réel et nomme les écarts |
| 10 | Synchronisation | `chapters/07-tests.md`, `08-conclusion.md`, `documents/rapport_stage.md`, `documents/slides_soutenance.md`, `ai/memoire/contexte_projet.md`, `ai/dev/methode_codage.md`, `ai/dev/README.md`, `projet/code-source/README.md`, `documents/documentation/consentement_gouvernance.md` | comptes de tests **23/23 → 54/54** (12 + 21 + 8 + 13) ; doc gouvernance alignée sur le code (codes 401/403/422, colonnes, seed) |

**Vérifications :** `pytest projet/code-source/tests` → **54 passed, 2 warnings in 2.48s** (12 matcher +
21 consentement + 8 dédup + 13 API gouvernance). **Sensibilité vérifiée par mutation** : neutraliser
`enforce_consent` dans `app.py` fait **échouer** `test_get_patient_denied_without_consent`
(returncode 1) — le test prouve le câblage, pas l'implémentation. Scores pondérés de la matrice
§2.11 **recalculés** (4.80 / 4.35 / 4.25 et 4.65 / 4.50). Scan des caractères CJK sur les 6 fichiers
Python touchés : 0. Structure du mémoire recontrôlée : 8 chapitres à 1 H1, fences Mermaid équilibrées,
**45 tableaux** (34 → 45), **20/20 références** définies et citées, aucun renvoi local cassé.
`export_memoire_docx.py` relancé → **8 H1**, 45 tableaux, **59 586 caractères**. Aucun commit sans
demande explicite.

**Résultat :** le contrôle de consentement est **effectif** sur l'API de gouvernance (403 + motif
journalisé) et prouvé par tests. **Limite assumée :** `schema.sql` et `seed_governance.py` n'ont pas pu
être exécutés (`.env` absent, pas de VM) — la validation en base réelle reste à faire.

## 27/09/2026 - Robustesse : retrait des BOM UTF-8 residuels (seuil : logs seuls)

**Constat :** 4 fichiers versionnes du depot principal conservaient un BOM UTF-8 en tete, present
dans les blobs Git (verifie par git show HEAD:<fichier>) et pas seulement dans la copie de travail.
Deux impacts measures avant correction :
- engine/governance/__init__.py : `ast.parse()` en echouait (SyntaxError: invalid non-printable
  character U+FEFF) alors que l'import Python, lui, tolerait le BOM ;
- documents/documentation/pipeline_elt.md, README.md, projet/mvp/AGENTS.md : le titre de niveau 1
  devenait invisible aux parseurs Markdown naifs (line.startswith('# ')), un commentaire bash d'un
  bloc de code pouvant alors etre pris pour un titre.

**Correction :** retrait du prefixe EF BB BF au niveau octet uniquement, sans reencodage ni
modification de fin de ligne. git diff --stat = 4 fichiers, 1 ligne chacun.

**Verifications :** scan global du depot principal (extensions .md/.py/.sql/.json/.yaml/.toml/.sh/
.txt/.cfg/.ini/.example/.csv) = **0 BOM** ; 0 fichier indecodable en UTF-8 ; `ast.parse()` sur
__init__.py = OK ; titres H1 de pipeline_elt.md, README.md et mvp/AGENTS.md de nouveau
detectes ; import engine.governance + engine.governance.app = OK ; pytest
projet/code-source/tests = **54 passed, 2 warnings in 2.55s**.

**Perimetre volontairement exclu :** projet/mvp/src/patient-data-platform/ (2 fichiers avec BOM)
est un **depot git imbrique autonome** (.git present) : sa copie de travail n'affecte pas le depot
principal, la modifier polluerait son propre historique. Le DOCX n'etait pas impacte
(export_memoire_docx.py ne lit que chapters/0*.md, aucun BOM). Les CRLF des 80 fichiers .md/.py/
.sql sont un artefact de core.autocrlf=true (blobs en LF) : non modifies. core.autocrlf inchange.
documents/Etat-de-l-art-M2-pro-stage.docx.md reste une **reference non versionnee**, non modifiee.
Aucun garde-fou ajoute (correction ponctuelle) ; seuil AGENTS.md "fix robustesse" : pas de mise a
jour de suivi_avancement.md.
- Note de suivi (27/09, apres coup) : `documents/Etat-de-l-art-M2-pro-stage.docx.md` a ete
  **versionne par l'utilisateur** (commit `bc6c7f4`) et n'a pas ete modifie par mes commits
  (`430e9e2`, `4d3c417`) : il reste une reference, simplement desormais suivie par Git.

## 27/09/2026 - Memoire : glossaire (chapitre 9) + passe de lisibilite du vocabulaire

**Constat.** Aucun glossaire n'existait dans le depot (0 fichier glossaire / lexique / vocabulaire).
La premiere occurrence de la plupart des termes techniques n'etait pas dans une phrase mais dans
les **tableaux et diagrammes du chapitre 1** (objectifs, plan, Mermaid) : Medallion, ELT,
RAW/SILVER/GOLD, MPI, MDM, DMP, RBAC, purpose-by-purpose, master patient, identity map. Le
lecteur rencontrait donc le jargon **avant** toute explication. Analyse de la prose existante :
26 a 32 mots par phrase en moyenne, style deja conforme a la methode du projet -> passe
**chirurgicale** et non reecriture massive, le risque de detruire des chiffres verifies etant
disproportionne.

**Realise.**
- `chapters/09-glossaire.md` : ~60 entrees en francais courant, sections 9.2 donnees et qualite /
  9.3 architecture Big Data / 9.4 gouvernance et droit, plus 9.5 les objets du depot (tables
  `raw_patient_record`, `master_patient`, `patient_identity_map`, `consent`, `api_user`,
  `access_audit`, les 3 tables metier ; scripts `run_pipeline.sh`, `gen_extract_raw.py`,
  `gen_fhir_mapping.py`, `create_silver.py`, `create_gold.py`, `hive_api.py`,
  `seed_governance.py`, `sql/schema.sql` ; couches `engine/identity/*` et `engine/governance/*`).
  Chaque entree donne le mot, l'explication en francais courant et le renvoi a la section qui
  detaille le sujet. Inclus automatiquement dans le DOCX (glob `0*.md`).
- **Chapitre 1** : tableau « En clair » (6 mots-cles : ELT, Medallion, MPI, deduplication, RBAC,
  consentement par finalite) insere avant le tableau des objectifs.
- **Definition a la premiere occurrence en prose** : `metastore` (§2.6), `rejeu` et
  `schema-on-read` (§2.7), MPI / DMP / MDM (§3.2), `idempotence` (§5.4), `purpose-by-purpose`
  (§5.5). Le vocabulaire technique est **conserve** (regle 3 de `ai/memoire/README.md`) : on ajoute
  du francais courant a cote du terme, on ne supprime aucun terme.
- Regles actees : `ai/memoire/methode.md` (definition obligatoire a la premiere occurrence, glossaire
  au checklist, structure 01..09), `ai/memoire/README.md` (ligne 09 + regle 3 completee),
  `README.md`, `documents/rapport_stage.md`.

**Verifications.**
- **Non-regression** : comparaison avant/apres, chapitre par chapitre, de tous les **nombres**,
  identifiants en code, chemins de fichiers et references `[B#]` -> **0 perte**. Les seuls
  ajouts : le nombre 9 et 6 jetons de code du nouveau tableau du chapitre 1.
- **22 renvois de section du glossaire verifies un par un** contre l'inventaire reel des 56
  sections : 0 renvoi casse. 15 renvois pointant vers la mauvaise section ont ete corriges
  (ex. `metastore` §5.6 -> §5.1, `partitions` §4.3 -> §4.4, scripts ELT §6.3 -> §6.2,
  `volumetrie` §4.2 -> §4.5).
- Chaque terme du glossaire existe dans les chapitres 01-08 (verification par motif) ; les termes
  absents n'ont pas ete forces (FDR, quasi-identifiant, pseudonymisation), et « faux negatif » est
  explique dans l'entree « faux positif » puisque le mot n'apparait pas tel quel dans le texte.
- Structure : **9 chapitres** a 1 H1 chacun, fences equilibrees, **51 tableaux** (45 -> 51),
  references **20/20** definies et citees, tables du glossaire a 3 colonnes sans separateur interne.
- `export_memoire_docx.py` : DOCX regenere = **9 H1**, 51 tableaux, **61 908 caracteres**.
- `pytest projet/code-source/tests` = **54 passed, 2 warnings in 2.33s** (inchange : aucun code
  de production modifie).

**Limite.** La passe porte sur la prose ; tableaux, chiffres et schemas Mermaid sont restes
intacts. Relecture humaine de la nouvelle prose recommandee avant impression.

## 27/09/2026 - Memoire : correction des 9 incoherences de fond (lot 1)

**Constat.** Audit des 9 chapitres, du DOCX et des documents de soutenance apres le glossaire.
8 incoherences de fond et 1 defilement de document, sans consequence sur le code. La plus grave :
la synthese de couverture de l'etat de l'art ne correspondait plus a son propre tableau.

**Realise (9 corrections, aucune reecriture).**
1. `chapters/02-etat-de-l-art.md` §2.10 : la phrase de synthese annoncait « 6 traites, 8
   partiels, 5 hors perimetre, 1 optionnel » alors que le tableau 7 lignes plus bas donne
   **11 traites / 7 partiels / 1 hors perimetre / 1 optionnel** (= 20 axes). Recompte a partir du
   tableau lui-meme, et les deux axes non traites sont nommes (personas, sobriete). Le resume
   n'avait pas ete mis a jour lors de l'ajout des axes 0, 6, 14, 15 et 19.
2. `chapters/02-etat-de-l-art.md` §2.10 : les blocs annonces (« existant, concepts, choix, vie du
   projet, soutenance ») ne correspondaient pas au tableau (« 1 Existant, 2 Concepts, 3 Choix,
   4 Soutenance, **5 Methodologie** »). Noms alignes sur le tableau.
3. `chapters/04-analyse.md` §4.6 : « demarche incrementale en **trois niveaux** » suivi d'un tableau
   **J1 a J5** -> « en **cinq jalons** ». C'etait la seule occurrence reellement cassee : le mot
   « trois niveaux » est employees ailleurs avec 3 autres sens (demarche technologique §1.4,
   architecture technique, niveaux de difficulte easy/medium/hard).
4. `chapters/04-analyse.md` §4.6 : jalon J5 « structuration en **8 chapitres** » -> « en **9
   chapitres** (glossaire inclus) ».
5. `chapters/01-introduction.md` §1.7 : le **plan du memoire** s'arretait a « Conclusion generale »
   non numerotee et ignorait le glossaire -> lignes **1 a 9** completes, dont
   « **9 — Glossaire** ».
6. `chapters/01-introduction.md` §1.4 : le schema Mermaid decrit 5 etapes alors que le tableau n'en
   comptait que 3 -> ajout d'une ligne « **Transverse** » (validation des algorithmes, puis
   gouvernance) et d'un paragraphe qui relie explicitement le schema au tableau.
7. `chapters/01-introduction.md` §1.4 vs §1.5 : le niveau 1 annoncait un « dashboard » que la
   section perimetre déclarait hors perimetre -> precise « dashboard de demonstration du PoC
   d'origine », non repris dans le depot consolide.
8. `chapters/01-introduction.md` §1.5 : l'API de gouvernance n'etait pas nommee -> **FastAPI**,
   « lecture seule, avec controle de consentement » (elle est comparee a Flask en §2.11).
9. `projet/code-source/scripts/dev/export_memoire_docx.py` : docstring « `01..08.md` » -> « `01..09.md` ».
   `documents/slides_soutenance.md` S4 : chaine de demarche completee par
   « GOUVERNANCE (consentement + audit) », absente alors que le schema §1.4 se termine dessus.

**Verifications.**
- **Non-regression** : 12 fichiers compares avant/apres sur nombres, references `[B#]`,
  identifiants de code et chemins -> **0 perte**. Les 3 « pertes » signalees par l'outil sont la
  correction voulue elle-meme (`chapters/01..08.md` -> `chapters/01..09.md`).
- Structure inchangee et verifiee : **9 chapitres** a 1 H1, **51 tableaux**, fences equilibrees,
  references **20/20** definies et citees.
- `pytest projet/code-source/tests` = **54 passed, 2 warnings in 2.41s**.
- DOCX regenere = **9 H1**, 51 tableaux, **62 445 caracteres** ; controle des **cellules** de
  tableau (et non des paragraphes) confirme la presence des lignes « Transverse », « 1 — Introduction »
  et « 9 — Glossaire », et des phrases corrigees (« traite directement 11 », « en cinq jalons »).

**Reste a faire (lots 2 et 3, non engages).** Rendu des **8 diagrammes Mermaid en images** dans le
DOCX (aujourd'hui 66 lignes de code brut ; Node 22 + `npx` disponibles) ; page de garde complete,
table des matieres, pagination ; bibliographie consolidee (`references/bibliographie.md` n'est pas
exportee : le DOCX ne contient que des formes courtes par chapitre et 0 URL) ; elargissement des
  chapitres les plus courts en prose (6 : 675 mots, 7 : 821, 3 : 949). Ces trois lots demandent un
  arbitrage explicite et modifient l'exporteur, pas seulement les documents.

---

## 27/09/2026 - Memoire : figures Mermaid rendues + DOCX A4 complet (lot 2)

**Contexte.** Lot 2 arbitre avec l'utilisateur : rendu **local** des diagrammes (pas de service
tiers), page de garde complete, sommaire, pagination, bibliographie consolidee, PNG versionnes,
et chainage direct sur le lot 3. Identite de l'auteur et des encadrants fournie pour la garde.

**Realise.**
| # | Action | Detail |
| - | ------ | ------ |
| 1 | `scripts/dev/render_mermaid_figures.py` (nouveau) | Extrait les 8 blocs `mermaid` des chapitres (source unique de verite), rend un PNG par diagramme via `npx @mermaid-js/mermaid-cli@11`, ecrit `manifest.json` (dimensions + config). Deux commandes, rien dans le depot (`node_modules/` absent). |
| 2 | `scripts/dev/export_memoire_docx.py` | Blocs `mermaid` -> images ; numerotation lue dans la legende Markdown (pas de compteur, donc pas de derives possibles) ; page de garde ; champ `TOC` + `updateFields` ; pied de page `Page X / Y` ; bibliographie consolidee ; lignes de continuation indentees ; **A4** (le gabarit python-docx sortait en Letter). |
| 3 | 7 chapitres | Une legende `> **Figure N — ...**` apres chaque diagramme (8 legendes, numerotation 1 a 8 dans l'ordre de lecture). |
| 4 | `documents/figures/` | `fig-1..8.png` (1,3 Mo) + `manifest.json`, **versionnes** : le DOCX illustre se reconstruit sans Node ni reseau. |

**Trois difficultes trouvees, toutes corrigees ou signalees.**
1. **Figure 7 ne se rendait pas** : `Lexical error on line 6`. Le libelle d'arete
   `extract_raw_report.json` contient des points, or le `.` est le delimiteur de la syntaxe
   `-. texte .->`. Corrige en putsant le libelle entre guillemets, forme deja utilisee par les
   5 autres aretes en pointilles du depot. Libelle inchange a l'affichage.
2. **Figures 1, 4 et 6 etaient tronquees** : la fenetre de rendu (1600 px) etait plus etroite que
   la largeur naturelle des diagrammes (**1812**, **1606**, **2904 px**) — du contenu sortait du
   cadre. Le moteur mesure d'abord la taille naturelle dans une fenetre large, puis rend le PNG
   dans cette fenetre. Aucune troncature restante (verifie sur les 8).
3. **Lisibilite** : a 16 cm de large, les libelles d'un diagramme allonge tombaient a **2.9-6.3 pt**.
   Deux leviers mesures puis appliques : (a) resserrer les libelles des diagrammes dont le rapport
   largeur/hauteur depasse 5 ; (b) page paysage dediee si la figure resterait sous **9 pt** dans la
   colonne. Resultat : 2 figures dans le texte (fig. 2 a 10.0 pt, fig. 8 a 13.0 pt) et 6 en paysage
   (8.7 a 13.3 pt), **sauf la figure 6 qui reste a 5.7 pt** (12 rangs de noeuds : aucune disposition
   tient sur une page — deux mises en page « serpentin » testees puis ecartees). Signale, non masque.

**Verifications.**
- DOCX : **8 images** (`inline_shapes`), **0 residu** de code Mermaid (`flowchart` : 0 occurrence),
  **10 H1** (9 chapitres + Bibliographie), 79 H2, 51 tableaux, **13 sections A4** (7 portrait /
  6 paysage), un seul `footer1.xml` (champs `PAGE` + `NUMPAGES`), `updateFields=true`, champ `TOC`
  present, 24 URL de la bibliographie dans le texte.
- Couverture : les 3 noms (auteur, encadrant professionnel, encadrant pedagogique) + MMT + session.
- **Non-regression vs HEAD** : 12 fichiers compares sur nombres, identifiants, chemins, codes et
  references `[B#]` -> **0 perte**. Les seuls ajouts sont les numeros des 8 legendes.
- Structure : **9 chapitres** a 1 H1, **51 tableaux**, **8 diagrammes**, **20/20** references.
- `pytest projet/code-source/tests` : **54 tests, 0 echec, 0 erreur** (XML JUnit, code de sortie 0).
- Encodage : 10 fichiers UTF-8, **sans BOM**, 0 caractere de controle ; **aucun secret** detecte.
- DOCX regenere = **104 386 caracteres** (contre 62 445 avant : + bibliographie + legendes,
  - 66 lignes de code Mermaid).

**Limites.** Le sommaire et la pagination sont des champs Word : ils se remplissent a la premiere
ouverture (ou clic droit > « Mettre a jour les champs »). La figure 6 reste a 5.7 pt. La validation
PostgreSQL / VM reste hors de ce lot (`.env` absent).

---

## 27/09/2026 - Memoire : elargissement de la prose des chapitres 3, 6 et 7 (lot 3)

**Contexte.** Apres les lots 1 et 2, le diagnostic sur la prose etait net : les trois chapitres les
plus courts etaient **tableaux denses, analyse absente**. Les tableaux portaient l'argument, la
prose se contente de l'annoncer. Cibles : ch. 6 (496 mots), ch. 7 (607), ch. 3 (664) — les trois
plus courts du corpus.

**Methode retenue :** ajouter de la prose qui **interprete** ce que les tableaux montrent, et non
de nouveaux tableaux ni de nouvelles affirmations. Regle appliquee sans exception : chaque fait
ecrit est verifie dans le code ou dans une sortie de commande ; aucune affirmation qui ne puisse
pas etre rejouee.

**Realise (1 475 mots de prose ajoutes, 6 372 -> 7 847).**

*Chapitre 3 (+545 mots) — du constat a la decision.*
- **Methode de la capture** : ce que l'introspection prouve et ne prouve pas. 1 260 tables
  detectees / 11 retenues (l'etendue, pas l'exhaustivite) ; une jointure verifiee ligne a ligne
  (9 791 / 9 791) qui montre l'integrite **interne** a une source ; 5 cles etrangeres decouvertes
  automatiquement dans GNU Health et 0 violation dans CLINIQUE, donc l'heterogeneite n'est pas un
  defaut de qualite ; volumes de MAVIS pris sur la **replique locale** (noeud instable).
- **Le contrat de normalisation** (nouveau tableau) : l'etude avait constate 3 encodages du genre,
  le code y repond par des listes fermees — 5 libelles masculins / 4 feminins, CIN reduit aux
  chiffres et rejete hors 6-12 chiffres, date ISO ou jour-mois-annee, nom sans accents ni
  ponctuation. Regle commune : **aucune valeur n'est devinee** — un champ douteux devient vide et
  renvoie l'enregistrement vers la branche probabiliste au lieu de corrompre une cle exacte.
  Precision d'honnetete : ce contrat est teste sur les 3 sources synthetiques, son application a
  MAVIS et CLINIQUE est **hors du run de reference** (sources CSV).
- **Lecture de la grille** : la colonne du projet n'est pas soumise au meme regime de preuve que
  les 6 produits (`teste` quand une mesure existe, `concu` quand elle n'existe pas — cas de la
  ligne gouvernance) ; `◐` = partiel selon la documentation, pas doute sur l'existence.
- **Reversibilite** : la decision sur mesure se paie en maintenabilite, pas en risque
  algorithmique. Poids, seuil et blocage vivent dans `config/deduplication.yaml`, lu par le matcher,
  Spark, l'evaluation et SILVER (verifie : imports dans `matcher.py`, `spark_dedup.py`,
  `evaluate_engine.py`, `create_silver.py`). Contrepoids assume et ecrit : le meme fichier alimente
  l'evaluation, donc **modifier un poids invalide les metriques publiees** tant qu'elle n'a pas
  ete rejouee.

*Chapitre 6 (+619 mots) — ce que la realisation prouve.*
- **Le determinisme comme precondition d'evaluation** : les 3 jeux viennent des **memes 500
  masters** (`--seed 42`) et ne different que par le taux de variation — la degradation est donc
  attribuable a un seul facteur, et deux executions sont comparables ligne a ligne. Les tables de
  transactions alimentent les entites FHIR autres que `patient` : leur rattachement est exactement
  la dette `patient_events_gold`.
- **Lecture de l'entonnoir 214 -> 145** : `214 − 69 = 145` se verifie par un **comptage sur le
  lac**, sans consulter la logique de fusion — c'est la correspondance « un master = un
  enregistrement non duplique » qui est testee. `patient_consent_gold` aligne 145 lignes sur 145
  masters ; mais GOLD ne certifie que l'**identite**, pas les evenements de soin.
- **La parite est structurelle, pas fortuite** : `canonical.py` partage, memes poids et meme seuil
  lus du YAML ; les implementations ne different que par le **regroupement** (index de blocage
  Pandas sur 3 criteres : prefixe de nom normalise, naissance, CIN ; Spark : `groupBy` sur la cle
  exacte puis comparaison des **ancres de clusters** seulement — arbitrage de montee en charge).
  Seul un protocole qui rejoue les deux chemins detecte une derive entre eux.
- **Les deux couches de gouvernance** (distinction absente du chapitre) : l'API **Flask** est une
  surface de *reporting* — `/api/governance/consent` **liste** les consentements et n'impose rien,
  sans authentification (verifie : aucune logique d'auth dans `hive_api.py`), lancee avec
  `debug=True` et rendant le nom du patient. L'API **FastAPI** est le seul point d'**application**
  de la regle (401 / 403 / 422, journalises par `audit.py`). Dette assumee et ecrite.
- **Les 6 incidents regroupes en 3 familles** : donnees (2 incidents -> documentes comme pieges
  anti-regression, ils se reproduisent), infrastructure (3 -> on **contourne** : toujours HDFS,
  validation par scripts Spark et non par beeline), outillage (1 -> le correctif change la methode :
  vecteurs abandonnes pour score pondere + synonymes).

*Chapitre 7 (+311 mots) — la preuve et ses angles morts.*
- La pyramide suit le **cout de retour a l'echec** et se substitue a une CI hors perimetre : la
  preuve est reproductible manuellement (`pytest` / `run_pipeline.sh` / `test_api.py`).
- **Les 14/14 de l'API sont un test de fumee** : `test_api.py` n'assert que le code de statut et
  n'envoie aucun en-tete d'authentification — il prouve la **joignabilite** des 11 endpoints, pas le
  controle d'acces (verifie dans le source). Le controle d'acces est prouve ailleurs, par les 13
  cas de l'API de gouvernance. Ni l'un ni l'autre ne remplace l'autre.
- **Mode de calcul des metriques** : comptage **analytique** sur les intersections de groupes, sans
  generation de paires (evite l'explosion combinatoire) ; meme decompte reutilise pour la
  decomposition par methode et par source via l'ensemble des paires pertinentes.
- **Honnetete sur le zero faux positif** : le generateur ne fait que ** degrader** des
  enregistrements existants (8 variations) et ne cree **jamais** deux personnes distinctes qui se
  ressemblent ; le cas adversariaire n'est donc pas sollicite par la verite terrain. La precision
  affichee est un **plancher**, pas une borne.
- **2 nouvelles lignes dans le tableau des limites (§7.5)** : homophones non sollicites ; controle
  d'acces de l'API Flask non teste.

**Verifications.**
- **Non-regression** : chaque token de preuve (nombres, identifiants en backticks, chemins,
  references `[B#]`) present avant le lot 3 est toujours present -> **0 perte** sur les 3
  chapitres ; 104 tokens ajoutes, tous traces.
- Structure : 9 chapitres a 1 H1, **52 tableaux** (51 + le nouveau contrat de normalisation),
  8 diagrammes, 8 legendes **1..8 sans trou ni doublon**, fences equilibrees, **20/20** references.
- Encodage : UTF-8 **sans BOM**, 0 caractere de controle, **0 secret** sur les 3 fichiers.
- `pytest projet/code-source/tests` : **54 tests, 0 echec, 0 erreur, 0 ignore**, code de sortie 0.
- DOCX regenere : **1 178 paragraphes**, 52 tableaux, **8 images**, 10 H1, 79 H2, 14 H3,
  **13 sections A4** (7 portrait / 6 paysage), champ TOC + `updateFields`, pied `PAGE`/`NUMPAGES`,
  **0 residu** de code Mermaid, 24 URL, 74 859 caracteres de texte.
- **Manifeste** : les 8 blocs Mermaid et leurs 8 legendes sont **inchanges** par rapport au commit
  (compare fichier par fichier) -> les PNG versionnes restent valides, **aucun re-rendu** (donc
  aucun bruit binaire). Seuls 2 numeros de ligne avaient derive (figures 3 et 7, dans les chapitres
  elargis) : corriges dans `manifest.json` avec la fonction du moteur elle-meme, pour obtenir
  exactement ce qu'il ecrirait aujourd'hui.

**Limites.** La relecture humaine reste a faire (style, transitions, longueur des chapitres) et les
champs du DOCX se remplissent a l'ouverture dans Word. La figure 6 reste a 5.7 pt. La validation
PostgreSQL / VM reste hors des trois lots (`.env` absent, Vagrant indisponible).

---

## 27/09/2026 - Soutenance : plan de temps refait pour un expose de 20 min, demo en video

**Contexte.** L'utilisateur fixe le format : **20 min d'expose, demonstration comprise**, questions
sur un creneau separe, et **pas de demonstration en direct** — une video preparee a la maison.
Question posee : « est-ce que notre avancement couvre ce delai ? ».

**Reponse : le fond couvre, le script de temps non.** Mesures faites sur
`documents/slides_soutenance.md` :
- 13 slides pour 20 min : le **nombre** de slides est bien calibre.
- **658 mots** de texte (hors code et hors lignes « Support ») = **4,4 a 5,1 min** de parole a
  130-150 mots/min. Les slides sont un squelette : il reste 10 a 14 min a developper a l'oral.
- Budget ecrit : « 15 min + 10 min questions » = **25 min**, incompatible avec 20 min si les
  questions sont dans le meme creneau.
- **Partie B annonce 7 min, or S5 (2) + S6 (2) + S7 (1) + S8 (2) = 7 min deja consommees** ->
  **S9 n'avait aucun budget**, alors que c'est la slide d'honnetete (difficultes, dettes, nuances).

**Trois defauts reels, corriges.**
1. **Les 2 premieres commandes de la demo n'existaient pas** : la slide citait
   `evaluation\evaluate_engine.py` et `provision\scripts\run_pipeline.sh` (verifie `Test-Path` =
   `False`) ; les vrais chemins portent le prefixe `projet\code-source\`. Elles se seraient
   arretes sur « No such file or directory » **devant le jury**, en plein budget. Les 4 cibles
   (2 scripts, `tests/`, interpreteur du venv) sont desormais verifiees `True`.
2. **Demo budgitee 2 min en live pour 3 commandes**, dont un pipeline Spark en 4 etapes sur une VM
   indisponible. Reecrite en **storyboard video 4:00** (4 plans : pytest 1:00, evaluation hard
   1:00, pipeline 1:30, repli 0:30) + **slide de repli obligatoire** (captures datees : `patient_fhir`
   214 lignes / 145 masters / 69 doublons / 32.24 %, `evaluation_truth.md`, sortie API). La video
   supprime le point de failure VM du jour J, mais impose de **filmer a la maison, VM allumee**.
3. **Aucune image sur les slides** alors que les 8 PNG existent depuis le lot 2, et la note de fin
   (« les schemas peuvent etre exportes en PNG/SVG ») etait **obsolete** : supprimee. 4 figures sont
   desormais projetees (fig-3 sur S2, fig-1 sur S4, fig-5 sur S5, fig-7 sur S7), 3 en reserve, et
   **fig-6 volontairement exclue** : a 5,7 pt elle est illisible sur un videoprojecteur (elle reste
   dans le DOCX en page paysage, et ne passe qu'en pause zoomee dans la video).

**Coherence avec le memoire (indispensable).** S8 disait « zero faux positif sur tous les niveaux »
et « parite parfaite », alors que le lot 3 presente desormais la precision comme un **plancher**
(le generateur ne cree pas d'homophones quasi identiques) et la parite comme des **decisions
identiques sur les jeux testes**. Sans cette correction, le jury pouvait opposer la slide au
chapitre 7. S9 porte aussi desormais la nuance « les 14/14 sont un test de fumee » et la
distinction API Flask (reporting) / API FastAPI (application de la regle).

**Nouveau budget, verifie par sommation : 16:00 + 4:00 de marge = 20:00.**
A 4:00 (S1 0:30, S2 1:15, S3 1:00, S4 1:15) · B 6:00 (S5 1:30, S6 1:30, S7 1:00, S8 1:15,
**S9 0:45**) · C 4:00 (S10 video) · D 2:00 (S11 1:00, S12 0:45, S13 0:15). Les 13 slides portent
une duree ; les 4 en-tetes de partie correspondent a la somme de leurs slides.

**Verifications.** 13/13 slides avec duree, somme 16:00, marge 4:00 ; 8 figures referencees et
toutes presentes ; commandes verifiees `True` ; UTF-8 **sans BOM**, 0 caractere de controle ; aucun
token de preuve perdu sans justification (les ecarts sont le format de duree `1.5` -> `1:15`, la
suppression de « 15 min + 10 min questions », et les 2 chemins de commande errones remplaces par
les bons). Distinction conservee : les *commandes a filmer* sont qualificationes chemin complet,
les *renvois de support* gardent la forme courte relative a `projet/code-source` (convention
anterieure du fichier).

**Reste a faire par l'utilisateur :** filmer la video a la maison (VM allumee, `pytest` rejoue juste
avant pour montrer 54/54, film <= 4 min), construire la slide de repli, et convertir le Markdown
dans l'outil de presentation. Aucun changement au memoire ni au code.

---

## 27/09/2026 - Soutenance : script de passage oral ecrit, puis debit mesure et corrige

**Contexte.** L'utilisateur accepte le script de passage oral slide par slide, en complement du deck
(`documents/slides_soutenance.md`, commit `9eccd36`). Le deck dit **quoi** montrer ; il manquait le
**texte a dire**, et donc la preuve que les 16:00 planifiees sont tenables a l'oral.

**Livrable.** `documents/soutenance_script_oral.md` (nouveau, 378 lignes) : pour chaque slide, la
duree, le repere `[debut] -> [fin]`, le texte « a dire » en citation, la ligne « a montrer » (y
compris les figures de reserve), et la transition vers la slide suivante. S'y ajoutent un
chronometrage (`[4:00]` fin de A, `[10:00]` fin de B, `[14:00]` fin de demo, `[16:00]` fin de D,
arret a `[20:00]`), un bloc « avant de repeter » (les 3 commandes, les contraintes video, les figures
projetees / reserve / exclue, et **trois interdictions de parole**), une regle de sacrifice en cas
de depassement, et le tableau de debit.

**Defaut reel trouve a la premiere mesure : deux slidesWere illisibles a l'oral.** S1 a
**164 mots/min** et S9 **189 mots/min** (mesure sur le texte « a dire » seul, hors gestes) : un orateur
neutre ne tient pas 189 mots/min, et S9 est precisement la slide d'honnetete, qui doit etre lisible.
Ratures : S1 ramenee de 82 a 72 mots, S9 de 142 a 112, S8 de 182 a 169, S13 de 38 a 34 mots. Les
titres de section du fichier annoncaient des **objectifs** de mots (175, 210...) qui ne
correspondaient pas au reel : les 13 en-tetes ont ete reecrits avec les valeurs mesurees, et une
coherence en-tete / tableau est verifiee automatiquement (seul S10 reste avec un format special,
« narration + video »).

**Debit final mesure : 1 548 mots sur 12:00 de slides de parole, 129 mots/min de moyenne, aucune
slide au-dessus de 150.** Les trois plus rapides sont S9 (149), S6 (146) et S1 (144) — le detail y
est porte par la figure ou le tableau projete, pas par la bouche. Avec les 12 transitions (121 mots)
et la video de 3:30, l'expose court **15:25 sur 16:00** a 140 mots/min, donc 35 s de filet dans le
plan et 19:25 sur 20:00 en tout. Conclusion inscrite dans le fichier : **ne pas ajouter de texte**
avant la premiere repetition, le temps disponible se depense en ralentissant.

**Trois familles d artefacts de redaction eliminees** avant mesure : un mot colle (« DataLakeMedallion », « deuxProofs of Concept »), des caracteres chinois inseres dans une phrase francaise (« Pour [caractere] cet objectif », « l architecture qui [caractere] cette... »), et des mots anglais residuels (« they re », « improvement »). Controles : 0 caractere CJK residuel, 0 mot anglais residuel dans la prose, UTF-8 **sans BOM**, 0 caractere de controle.

**Coherence deck / script verifiee : 0 divergence de duree sur 13 slides** (le script reprend les
durees du deck au mot pres), les 7 figures citees existent, MPI est nomme en S6 comme dans le deck.
Chiffres cles presents : 214, 145, 69, 32,24, 11 614, 0,422, 9 791, 54.

**Non-regression.** `pytest projet/code-source/tests` : **54 passed in 2.39s**, code de sortie 0.
Aucun fichier du memoire, du code ou des figures modifie : ajout documentaire seul.

**Reste a faire par l'utilisateur :** repeter a voix haute avec un chronometre, produire la video et
la slide de repli, convertir le Markdown. Le memoire n'a pas ete touche.

## 27/09/2026 - Memoire : piece liminaire complete (resume, abstract, listes, acronymes) + dette SHA-256 declaree

**Contexte.** L'utilisateur impose le plan des deux rapports de reference (documents/RAPPORT_HASINA_1613.docx,
documents/Rapport de stage ETU 1156 RAMANANTSAFIDY Jonah Fitia.docx) et demande explicitement la premiere
page, le resume et la version anglaise. Metadonnees validees par l'utilisateur : soutenance **Octobre 2026**,
**aucune ligne service**, encadrant professionnel M. Harena Ny Aina Rabemanoela, encadrant pedagogique
M. RABENANAHARY Rojo, autrice RANOMENJANAHARY Manjaka Alpha. Les RMA du front sont **conserves**
(decision de l'utilisateur).

**Dette declaree (etape 0).** La documentation evaluait « cles API hachees en SHA-256 » sans dire que le
hachage n'est ni sale ni lent. Verifie dans le code : engine/governance/auth.py:26 et
provision/db/seed_governance.py:57 appellent hashlib.sha256(...).hexdigest() sans sel ni iteration.
Corrige en trois endroits, sans dramatisation ni retrait de l'affirmation vraie (la cle en clair n'est
jamais stockee) : nouvelle ligne du tableau des limites (§ 8.3) avec la cause et la correction (sel par cle,
ou crypt deja utilise cote frontend pour les mots de passe) ; glossaire § 9 ; renvoi au § 8.3 en § 5.5.

**Questions anticipees (§ 8.6, nouveau).** 10 objections probables du jury, chacune avec reponse verifiee
et renvoi de chapitre : precision 1,000 non garante (jeu adverse non sollicite) ; rappel 0,422 assume ;
absence d'estimation EM (donnees synthetiques non identifiantes, § 3.4) ; VM 8 Go non passable a
l'echelle ; consentement = mecanique prouvee / donnee absente ; frontieres Flask vs FastAPI ; cles non
salees ; les 14 tests API ne prouvent pas le controle d'acces (13 cas dedies) ; generation a racine fixe
RANDOM_SEED = 42 ; separation HDFS/Spark vs PostgreSQL.

**Piece liminaire (etape 1).** scripts/dev/export_memoire_docx.py (461 -> 793 lignes) :
- dd_cover() reecrite sur le modele de reference : titre, « par », autrice, « Memoire presente » +
  libelle **exact** du diplome, encadrement, Octobre, 2026, copyright. Plus aucune mention « Master 2
  MBDS (specialite Big Data) », ni « Session septembre 2026 », ni ligne service.
- dd_abstract() produit « Resume » + « Mots-cles » (179 mots) et « Abstract » + « Keywords » (145
  mots), en paragraphes justifies avec retrait de premiere ligne, texte justifie en Times New Roman.
- collect_captions() + dd_listes() : liste des figures alimentee depuis les legendes des chapitres
  (8 entrees), jamais recomptee a l'export. **La liste des tableaux n'est pas emise** : aucune legende
  **Tableau N — ...** n'existe encore (0 trouvee), donc la section est omise plutot qu'affichee vide.
  Elle apparaitra des l'etape 2 (legendes des tableaux retenus).
- dd_acronymes() : 27 sigles en tableau a deux colonnes, order par progression du texte.
- Pagination fidele au modele : piece liminaire en chiffres romains, corps repart a 1, page de garde sans
  numero, pied « Page X » seul. Verification : les references n'utilisent que PAGE (pas de total), et
  dd_section recopiant le sectPr, chaque section paysage aurait reinitialise le compteur a 1 --
  d'ou clear_page_numbering() sur les sections 2..n.

**Trois pieges rencontres et corriges en cours de route.** (1) dd_abstract prenait 	ext[0] comme
titre, ce qui aurait affiche « R » ; le titre est desormais un parametre. (2) ill_footer remettait
different_first_page_header_footer a False apres que l'appelant l'ait pose, donc la couverture
portait un numero ; le choix est desormais laisse a l'appelant. (3) La lecture des legendes de figures
s'arretait sur l'asterisque d'ouverture et produisait « Figure 1 — Figure 1 — » avec un titre coupe en
milieu de mot ; le bloc est desormais recolle jusqu'a la **fermeture** du **, le prefixe « Figure N — »
retire, et la liste tronquee a une virgule ou un point-virgule.

**Preuves.** Export : documents/memoire_M2_MBDS.docx, 9 chapitres, 8 figures, 14 sections, 53 tableaux
(52 + acronymes), 1 365 Ko. Controle structurel : sectPr des sections 0 et 1 en ordre de schema valide
(pgNumType present, monotonique), sections 2..13 sans pgNumType (numerotation continue),
updateFields=true (Word recalcule sommaire et pagination a l'ouverture), pied PAGE seul, page de garde
sans numero, XML de document.xml / settings.xml / ooter1.xml bien forme, CRC du zip valide.
Non-regression : pytest projet/code-source/tests = **54 passed**, code de sortie 0. Aucun chiffre
invente : le resume et l'abstract ne citent que 214 -> 145, 69 doublons, 32,24 %, precision 1,000, rappel
0,578 / 0,422, 420 faux negatifs.

**Reste a faire (etapes non lancees).** Etape 2 : reduction des tableaux au critere jury + legendes des
tableaux retenus (la liste des tableaux suivra automatiquement). Etape 3 : 3 pages de front (Doublons,
Gouvernance, Synthese) **en plus** des RMA, bandeau mocked sur les vues RMA, correction du KPI CPN4
qui affiche 0 %, puis les deux corrections du memoire qui en dependent (§ 1 L129 : les endpoints /rma/*
ne sont pas « sur les donnees GOLD » mais avec repli mocked, laboratory et malaria en mock
inconditionnel ; § 1 L78 et § 4 L27 : le dashboard RMA n'est pas notre livrable). Relecture humaine du
DOCX dans Word ; toute edition de chapitre decale les lignes de documents/figures/manifest.json a
mettre a jour apres restructuration.

## 28/09/2026 - Memoire : etape 2, 52 -> 40 tableaux, 35 legendes, liste des tableaux active

**Cible.** Les deux rapports de reference (8 a 12 tableaux numerotes) et le plan impose
demandent de reduire les tableaux au strict necessaire, sans perdre une preuve. Etat de
depart : **52 tableaux de chapitre, 0 legende**, donc **aucune liste des tableaux** dans
le liminaire.

**Ce qui a ete converti en prose ou fusionne (12 tableaux en moins).** Ch. 1 : le
vocabulaire d'introduction et les trois niveaux de la demarche. Ch. 2 : les 5 etapes de
l'ER, les poids du score de similarite (doublon du 2.11, renvoi conserve), les briques
Big Data, les zones Medallion, et surtout les **3 grilles de notation fusionnees en une
seule** avec une colonne `Arbitrage` (8 lignes au lieu de 3 tableaux). Ch. 4 : colonne
`Champs patients` retiree du tableau des sources, le mapping champ par champ restant au
5.2. Ch. 7 : definitions des metriques, breakdown par methode, et le tableau des limites.

**Doublons entre chapitres supprimes (2 tableaux en moins).** Les arbitrages existaient
en double au 2.8 et au 8.2 : le tableau de la conclusion, plus riche (preuve + risque
residuel), a ete conserve et **complete des 3 choix qui n'existaient qu'au 2.8** (MPI local
+ pivot FHIR, 3 niveaux MVP -> Spark -> Big Data, parite Pandas = Spark) -- il compte
maintenant **11 arbitrages**. Les limites existaient en double au 7.5 et au 8.3 : celui de
la conclusion a ete conserve et **complete de la limite des homophones**, qui n'existait
qu'au 7.5 et qui est une des honestites les plus fortes du memoire (la precision 1.000
est un plancher, pas une borne). Aucun tableau n'a ete supprime sans que son contenu soit
retrouve ailleurs.

**Ce qui a ete conserve et legende (35 legendes).** Les 40 tableaux restants (2 / 7 / 5 /
5 / 6 / 4 / 3 / 3 puis 5 dans le glossaire) portent une legende `**Tableau N - ...**`
placee sur **une seule ligne** juste avant l'en-tete, numerotee 1..35 en continu. Les
**5 tableaux du glossaire ne sont volontairement pas legendes** : c'est du materiel de
reference consulte, pas de l'argumentaire, et les 27 acronymes du liminaire jouent le
meme role. C'est cette presence de legendes qui **active la liste des tableaux**, absente
jusqu'ici faute de legendes a lister.

**Preuves.** Controle structurel sur les 9 chapitres : chaque separateur de tableau est
precede d'un en-tete et suivi d'au moins une ligne de donnees, **aucun tableau casse** ;
numerotation **1..35 continue, sans doublon** ; le nombre de lignes de tableau par
chapitre ne differe de HEAD que du montant exact des coupes et des 4 lignes ajoutees au
8.2. Scan des lignes modifiees : **aucun mot sans accent**. `pytest
projet/code-source/tests` = **54 passed** (code de sortie 0). DOCX regenere : 9
chapitres, 8 figures, 14 sections, **41 tableaux** (40 + 1 acronymes), liminaire listant
**8 figures et 35 tableaux**, resume 179 mots, abstract 145, 27 acronymes, archive zip
INTEGRE et 18 parties XML bien formees.

**Effet de bord corrige.** `documents/figures/manifest.json` positionne les figures par
numero de ligne : les legendes et conversions ont decale **6 positions** (fig. 1, 2, 3, 4,
6, 7), recalculees avec la meme logique d'extraction que le moteur, et verifiees en
relisant chaque ligne citee. Les PNG n'ont pas ete re-rendus (les diagrammes sont
inchanges).

**Incident et pieges rencontres pendant cette etape.** (1) Un script de renumerotation a
supprime les `**` fermants des legendes ; le script de correction a ensuite consomme
l'en-tete et la premiere ligne de 13 tableaux. Detection par controle systematique
avant tout commit, **restauration depuis HEAD**, puis reprise a la main des 7 editions
structurelles et re-insertion des legendes par un script qui n'ecrit que des lignes
nouvelles. (2) Le meme script inserait la legende entre l'en-tete et le separateur au
lieu de l'edans de les devancer. (3) Les premieres legendes ecrites par script etaient
**sans accents** ; scan systematique et reecriture des 13 concernees. (4) Les
conversions en prose avaient laisse trois redondances (intro orpheline au 7.3, phrase
repetee au 7.2, reformulation en double au 2.11) ; relues et corrigees.
Leçon appliquée : ne jamais resumer un chapitre par une substitution de motif regex
silencieuse, et **toujours controler structure et accents avant commit**.

**Reste a faire (etapes non lancees).** Etape 3 : 3 pages de front (Doublons,
Gouvernance, Synthese) **en plus** des RMA, bandeau `mocked` sur les vues RMA, correction
du KPI CPN4 qui affiche 0 %, puis les corrections du memoire qui en dependent (1.3 : le
dashboard RMA n'est pas notre livrable ; 1.5 : les endpoints /rma/* ne sont pas « sur les
donnees GOLD » mais avec repli `mocked`, `laboratory` et `malaria` en mock inconditionnel ;
4.1 : le dashboard RMA). Relecture humaine du DOCX dans Word. La figure 6 reste a
5,7 pt en paysage et n'est pas projetable.

## 28/09/2026 - Memoire : complement d'etape 2, glossaire 5 -> 1 tableau (40 -> 36 tableaux)

**Demande.** Reduire encore le nombre de tableaux, en suivant le plan des deux rapports de
reference.

**Cible de calibration.** Les deux references ont ete relues avec python-docx :
RAPPORT_HASINA_1613 = **12 tableaux** (dont 1 vide, la bibliographie en tableau), RAMANANTSAFIDY
= **8 tableaux** (dont 1 vide, les acronymes 21x2 en liminaire). Leur usage des tableaux se
limite a sept categories : grille comparative, outils/techno, contraintes et risques, budget,
taches/cas d'utilisation, modules et roles, plus acronymes et bibliographie. Le vocabulaire et
les inventaires de code y sont **en prose**, pas en tableaux. Notre 5 tableaux de glossaire
etaient donc plus lourds que ceux des references.

**Coupure (4 tableaux).** Les 3 tableaux de vocabulaire (donnees/identite 18 entrees,
architecture 24, gouvernance/droit 21) sont fusionnes en **un seul** tableau a 4 colonnes
`Domaine | Mot | En clair | Ou c'est detaille` (63 entrees, colonne Domaine = famille du
mot) : -3 tableaux, +1 colonne. Les 2 inventaires d'objets du depot (tables de la base
centrale 7 entrees, scripts/couches 15 entrees) sont passes **en prose** (listes de
definition dans 9.3.1 et 9.3.2) : leur contenu est deja argumente dans les ch. 5 et 6, un
tableau ici ne faisait que le repeter. Aucun mot, aucune table, aucun script n'a ete perdu.
Nouveau glossaire : **1 tableau**.

**Resultat.** 40 -> **36 tableaux** de chapitre : 2 (ch. 1), 7 (ch. 2), 5, 5, 6, 4, 3, 3, et
1 dans le glossaire. Les 35 legendes d'argument (Tableau 1..35) sont **inchangees** : le
glossaire n'etait pas legende, la fusion ne touche donc pas a la numerotation ni a la liste
des tableaux.

**Preuves.** Controle structurel : glossaire = 1 tableau, 65 lignes (1 en-tete + 1 separateur +
63 entrees), 0 legende. Les 7 autres chapitres sont inchanges (seul ecart = le glossaire).
`pytest` = **54 passed**. DOCX regenere : 14 sections, **37 tableaux dans le corps** (36 +
acronymes), liminaire listant **8 figures et 35 tableaux**, archive zip INTEGRE, 18 parties
XML bien formees, mentions Tableau 1..35 presentes.

**Plan des references : alignement confirme et ecarts releves.** Les 9 chapitres suivent bien
le plan des deux references (introduction, etat de l'art avec grille comparative, existant +
solutions, demarche projet, exigences realisees, conception, tests, conclusion, glossaire) :
l'ecart a corriger porte non sur les chapitres mais sur des **sous-sections** que les
references traitent et que le memoire n'a pas encore :
- **Budget / couts** : present dans les 2 references (3 tableaux chez HASINA, 1 chez
  RAMANANTSAFIDY) ; absent du memoire (seule mention : "budget nul" dans la grille de
  criteres, ch. 2).
- **Cas d'utilisation** : present chez RAMANANTSAFIDY (tableau 18 lignes) ; le memoire n'a que
  les etapes ELT (ch. 6) et les exigences fonctionnelles (ch. 4).
- **Roles / parties prenantes et equipe projet** : present chez HASINA (tableau 6 lignes) ; le
  memoire n'a que les roles *RBAC applicatifs* (admin/analyst/viewer), pas les roles projet.
- **Gestion de la configuration** : sous-section chez HASINA ; absente du memoire.
- **Annexes** : HASINA en a 4 (script de deploiement, Spark, NLP, structure BDD) ;
  RAMANANTSAFIDY en a aussi ; le memoire n'a **aucune annexe**.

Ces ecarts restent a traiter (etape suivante, en prose pour ne pas re-inflater le nombre de
tableaux) ; ils sont notes ici pour tracer le plan-vs-references.

## 28/09/2026 - Memoire : 5 sous-sections du plan des references + 6 annexes, tableau Budget (36 -> 37 tableaux)

**Demande.** Reduire encore les tableaux et suivre le plan des deux rapports de reference.
Apres reduction du glossaire (40 -> 36 tableaux), les references ont ete relues une seconde
fois, cette fois par **contenu de tableau** (extraction des 20 tableaux des deux .docx), pour
identifier les rubriques qu'elles traitent et que le memoire n'a pas.

**Ce que les references contiennent comme tableaux (et que nous n'avions pas).** HASINA :
grille comparative, outils/versions, contraintes, risques, **budget en 3 tableaux** (couts
humains, materiels, total), taches, modules, roles, bibliographie. RAMANANTSAFIDY :
acronymes, grille comparative, **livrables**, **outils/techno par categorie**,
**contraintes / risques / mesures** en un seul tableau, **budget**, bibliographie. Le point
commun est net : **budget, roles, livrables et outils sont dans leurs tableaux**, alors que
notre memoire n'en avait aucun.

**Cinq sous-sections ajoutees au chapitre 4, toutes en prose sauf le budget.**
- **4.7 Roles, parties prenantes et equipe projet** : les 4 parties prenantes (commanditaire
  MMT, encadrant professionnel, encadrant pedagogique, stagiaire), avec la distinction
  explicite entre **roles du projet** (qui decide quoi) et **roles d'execution** (admin /
  analyst / viewer, § 2.5 et 5.5) que les references traitent separement. Encadre
  d'honnetete : l'equipe est **une seule personne**, donc pas de revue de code ni de tests
  de revue mutuelle, et la seule relecture est celle de l'auteur.
- **4.8 Cas d'utilisation** : CU1 ingestion, CU2 normalisation canonique, CU3 deduplication,
  CU4 application du consentement, CU5 interrogation de l'API (403 journalise),
  CU6 dashboard RMA. Chacun en acteurs / prerequis / deroulement / resultat attendu /
  cas limite, ecrit comme un scenario. CU5 rappelle qu'un refus renvoie 403 et non une
  reponse muette ; CU6 rappelle que le dashboard est optionnel et servi en repli mock.
- **4.9 Gestion de la configuration** : ce qui est versionne (Git, seed 42, secrets hors
  depot), ce qui est declare (fichiers de config lus au demarrage, seuil 0.80, poids,
  finalites, manifeste des figures), ce qui est verifie (tests verts comme critere de sortie
  de jalon, `elt.log`, idempotence, rejeu depuis SILVER). Encadre d'honnetete : ni
  l'exploitabilite ni le deploiement sur serveur du commanditaire ne sont demontres.
- **4.10 Budget du projet** : **seul tableau ajoute**, conforme a la forme des references.
  Montants en Ariary, **explicitement etiquetes hypotheses de travail** dans la legende, le
  corps et un encadre, a remplacer par les chiffres reels du commanditaire. Ce qui est
  reellement etaye est distingue : budget logiciel et materiel **reellement nul** (100 %
  open source, materiel deja acquis) ; cout humain **non etaye** (hypothese ; stage non
  remuneration). Point releve : la ligne la plus sous-estimee n'est pas l'infrastructure
  mais le temps de reconciliation Pandas / Spark impose par la parite stricte.
- **4.11 Synthese de l'analyse** : l'ancienne 4.7, renumerotee.

**Six annexes ajoutees** (`references/annexes.md`, nouveau fichier, **apres** la
bibliographie comme dans les deux references) : A pipeline ELT et journaux, B structure de la
base centrale, C moteur de rapprochement, D API de gouvernance, E API REST GOLD et vues RMA,
F donnees synthetiques et verite terrain. Redigees **en prose** : elles disent ou se trouve le
code et ce qu'il prouve, sans le recopier (le depot et son historique sont la preuve, pas un
extrait fige). Chaque annexe renvoie au chapitre qui explique la chose. Aucun chemin cite
n'a ete invente : les 9 tables de `sql/schema.sql`, les fonctions de `matcher.py` et
`canonical.py`, et les 4 fichiers de `engine/governance/` ont ete verifies avant redaction ;
`run_pipeline.sh` et `evaluation/synthetic-patient-generator/` ont ete localises (sous
`provision/scripts/` et `evaluation/`), deux chemins differant de l'_intuition initiale.

**Renumerotation.** L'insertion du tableau Budget en 4.10 a decale les numeros aval : les
legendes des ch. 5 a 8 ont ete decalees de +1 par script (20..35 -> 21..36) et la nouvelle
legende prend le numero 20. Controle prealable : **aucun renvoi en texte** vers un numero de
tableau n'existait (0 occurrence en dehors des legendes), donc rien d'autre n'etait a corriger.
Sequence finale verifiee : **1..36 continue, sans doublon**.

**Exporteur.** `export_memoire_docx.py` accepte maintenant `references/annexes.md`, insere
apres la bibliographie, avec la meme tolerance que la bibliographie (fichier absent ->
avertissement, pas de page vide). Le plan du chapitre 1 (Tableau 2) mentionne desormais les
annexes, et la ligne du chapitre 4 cite les 6 sous-sections.

**Preuves.** Structure : 2 / 7 / 5 / **6** / 6 / 4 / 3 / 3 / 1 = **37 tableaux**, legendes
**1..36** continues. `pytest` = **54 passed**. DOCX regenere : 9 chapitres, **H1 = 9
chapitres + Bibliographie + Annexes**, 38 tableaux dans le corps (37 + acronymes), liminaire
listant 8 figures et **36 tableaux**, annexes **A a F** presentes, archive zip INTEGRE, 18
parties XML bien formees, 14 sections. Manifeste des figures : 8 positions **reverifiees une a
une** apres les decalages de lignes (le nouveau script de controlecorrige detectait un faux
negatif parce qu'il cherchait la legende *avant* le bloc mermaid, alors qu'elle est *apres*).

**Point de methode.** Le validateur testait `Tableau 1..35` **en dur** : l'ajout du tableau 36
y est passe inapercu, et le controle est meme remonte "1..0 True" quand le calcul de maximum
a echoue silencieusement. Corrige : le maximum est desormais deduit des legendes des
chapitres, avec detection explicite des numeros manquants ou en double, plus le controle de
presence de la bibliographie, des annexes et des annexes A a F. Un controle qui peut
reussir a vide ne prouve rien.

---

## 28/09/2026 - Front etape 3 : pages Doublons / Gouvernance / Synthese, flag mock partout, CPN4 en n/d

**Demande.** "On continue", etape 3 du front au sens utilisateur : ajouter les trois pages a
cote des 5 vues RMA et du dashboard, signaler les donnees de demonstration et corriger
l'affichage CPN4.

| # | Action | Detail |
| - | ------ | ------ |
| 1 | `front-optional/src/lib/api.ts` | `ApiResult<T>` = `{ data, mocked }` ; `resultOf()` lit `mocked` **dans l'enveloppe** du backend (jamais infere cote front) ; `getDuplicates()` et `getConsent()` (stats `total_consents`/`granted_count`/`patients` en meta) ; finalites typees (`api_access`/`research`/`analytics`) + libelles FR |
| 2 | `front-optional/src/components/MockedBanner.tsx` (nouveau) | Bandeau ambre "Donnees de demonstration" visible des que `mocked=true` ; `{source}` decrit la table attendue (GOLD / identities / consentements) |
| 3 | Pages RMA + dashboard | Bandeau branche sur `mocked` pour `/rma`, morbidite, maternite, laboratoire, paludisme, dashboard |
| 4 | `front-optional/src/app/rma/maternite/page.tsx` | `CPN4` (et Avortements) passent en `number \| null` : le backend ne fournit pas CPN4, l'interface affiche **n/d** ("non renseigne par la source") au lieu de `0 %` |
| 5 | `front-optional/src/app/dashboard/DashboardClient.tsx` | KPIs mortalite infantil./matern. en `number \| null` affiches **n/d** (au lieu de `?? 0`), unite explicite count/percent (fini le `< 10 => %`) |
| 6 | `front-optional/src/app/doublons/page.tsx` (nouveau) | KPIs patients / patients maîtresses / doublons / taux + repartition par methode (exacte/probabiliste) avec justification de fusion ; aucune valeur recalculée (API telle quelle) |
| 7 | `front-optional/src/app/gouvernance/page.tsx` (nouveau) | Stats consentements + tableau par (patient, finalite) + filtre par finalite (purpose-by-purpose) ; `patient_uuid` affiche n/d quand absent (mock) ; rappel noms synthetiques |
| 8 | `front-optional/src/app/synthese/page.tsx` (nouveau) | Trois volets (admissions+mortalites, dedup, consentement) en `Promise.all`, bandeau si **l'un** des trois est mock, bloc RAW/SILVER/GOLD |
| 9 | `front-optional/src/components/Sidebar.tsx` | Entrees Synthese / Doublons / Gouvernance dans le menu principal |
| 10 | `front-optional/src/middleware.ts` | Les trois nouvelles routes passees en routes authentifiees (matcher + regex) |
| 11 | `provision/api/mock_data.py` | `MOCK_CONSENT` aligne sur `PURPOSES = (api_access, research, analytics)` du moteur (`engine/governance/consent.py`) : l'ancien jeu (`recherche`/`qualite`/`reglementation`) affichait des etats que `validate_purpose` refuserait |
| 12 | `front-optional/FONCTIONNALITES.md` | Sections 4 (indicateur mock), 6 (doublons), 7 (gouvernance), 8 (synthese), statuts RMA passes a "Actif", routes protegees et endpoints ajoutes |

**Verifications.** `npx tsc --noEmit` = 0 erreur. `next build` = compilation OK, 18 routes
(3 nouvelles presents). `next lint` = 18 erreurs, **meme compte qu'au commit `ab5a631`**
(mesure precise apres `git stash push --include-untracked -- src`) : aucun nouveau defaut
linters introduce ; les erreurs restantes sont pre-existantes (`any` d3, `react/no-unescaped-entities`,
`ui/*`). `pytest projet/code-source/tests` = **54 passed, 2 warnings**. Controle de coherence :
les types front correspondent a l'enveloppe reelle (`respond()` : `success/filters/data/mocked` ;
mortality/maternity passe fallback `mocked=True` ; laboratory/malaria `mocked=USE_MOCK_FALLBACK`
; governance_duplicates/consent fallback `mocked=True` + meta consent).

**Point de methode.** Le build Next demande `prisma generate` (client absent de `node_modules`),
pas d'erreur de code. `npm ci` et `prisma generate` ont ete executes (541 paquets installes).
`mock_data.py` : la finalite inventee `reglementation` est un exemple de valeur que le moteur
rejetterait en 422 - corrige afin que le jeu de demo reste un etat GU accessible par le moteur.

**Rappel / limite.** Les chiffres mockes (65214 / 62180 / 3034 / 4,65) restent coherents entre
eux mais differents du run reel (145 masters / 69 doublons) : les pages les portent avec le
bandeau, jamais comme resultats. `documents/slide_soudenance/` (2 PPTX) reste non suivi.
Commit en attente ; passages memoire §1.3 / §1.5 / §4.1, Aligner front restent a jour en
fin d'etape.

---

## 28/09/2026 — Retrait radical du RMA : front + backend + documents memoire

**Contexte :** a la demande explicite de l'utilisateur, la fonctionnalite de visualisation RMA
(dashboard, vues `/rma/*` et `/api/rma/*`, documentation afferente) est retiree du perimetre
consolide. Le front est recentre sur les vraies fonctionnalites : deduplication, consentement,
gouvernance (`/synthese`, `/doublons`, `/gouvernance`). Le modele de donnees est conserve
(8 tranches d'age dans `create_gold.py`) ; `archives/datalake_mavis/` non touche ; les entres
historiques de ce journal ne sont pas modifiees (traces conservees).

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Front suppressions (git rm, staged D) | `src/app/rma/` (5 pages), `src/components/rma/` (4 composants), `src/app/dashboard/`, `pages/api/rma/diagnostics.ts`, `src/context/FiltersContext.tsx`, `src/components/ui/date-range-picker.tsx`, `front-optional/graphes.md` |
| 2 | Front recentrage | `Header.tsx` (session seule, imports `Button`), `AppWrapper.tsx` (sans `FiltersProvider`), `layout.tsx` (titre "DataViz Gouvernance"), `login.tsx` (redirect `/synthese`), `app/page.tsx` (redirect `/synthese`), `middleware.ts` (routes protegees : settings/doublons/gouvernance/synthese/users ; `/users` admin-only ; denied → `/synthese?denied=1`), `users/page.tsx`, `settings/page.tsx` ; nouvelles pages `doublons/`, `gouvernance/`, `synthese/` (KPIs dedup + consent + chaine RAW/SILVER/GOLD), `MockedBanner.tsx` ; `tsconfig.json` (entree `dashboard/page.old.tsx.old` supprimee) |
| 3 | Backend | `provision/api/hive_api.py` reecrit (2 endpoints : `/api/governance/duplicates`, `/api/governance/consent` ; import `json` supprime, `os` deplace dans la branche `except ImportError`) ; `mock_data.py` reduit (MOCK_GOVERNANCE_DUPLICATES + MOCK_CONSENT, finalites alignees sur `PURPOSES`) ; `test_api.py` = 3 tests ; `provision/api/README.md` + `provision/test_startup.sh` (health `/api/governance/duplicates`) |
| 4 | Docs front | `FONCTIONNALITES.md`, `README.md`, `structure_interface.md` reecrits ; `todo.md` tableau final mis a jour |
| 5 | Memoire | ch. 01 (objectif 5, "dashboard/RMA du PoC non repris", 3/3 PASS), 02, 04 (F5, CU6), 05, 06 (§6.5, "API gouvernance 3/3"), 07-tests (Tableau 31, figure 8, conclusion : 3/3 PASS), 09-glossaire (entree `hive_api.py`), `references/annexes.md` (Annexe E renommee) ; `documents/rapport_stage.md` + `slides_soutenance.md` (3/3 PASS) ; `cahier_des_charges.md`, `documents/documentation/*` (api.md reecrit, architecture.md, bases_de_donnees.md, bigdata_concepts.md, consentement_gouvernance.md, pipeline_elt.md) ; GUIDE (`guide-backend.md` reecrit, `guide-frontend.md` + `README.md` recentres) ; `ai/dev/architecture.md`, `ai/dev/pipeline_elt.md`, `ai/dev/suivi_avancement.md`, `ai/memoire/contexte_projet.md` alignes ; `scripts/dev/export_memoire_docx.py` (entree glossaire RMA supprimee) |

**Verifications.** `npx tsc --noEmit` = 0 erreur (apres purge `.next`) ; `next build` = OK, 12 routes
(plus de `/rma` ni `/dashboard`) ; `py_compile` OK sur `hive_api.py`, `mock_data.py`, `test_api.py` ;
`pytest` = **54 passed** (venv racine). Recherche residue contrôlee : plus aucune reference RMA hors
`archives/` et hors entrees historiques de ce journal (`front-optional/bokt.new` : notes utilisateur
conservees).

**Reste :** regeneration du DOCX (`export_memoire_docx.py`) a executer, relecture humaine dans Word,
`documents/slide_soudenance/` (2 PPTX) non suivi, commit en attente de validation utilisateur.

---

## 28/09/2026 — Deck de soutenance PowerPoint 21 slides (charte MMT)

**Contexte :** l'utilisateur dispose de `documents/slide_soutenance/V2soutenance_m2_hasina.pptx`
(7,1 Mo, 21 slides — presentation Ingenosya « Mapping Intelligente » utilisee comme gabarit de
structure) et demande un deck pour le projet patients, calque sur cette structure, avec contenu du
projet et personnalisation charte. Charte choisie par l'utilisateur : logo = placeholder texte «
MMT », auteur = RANOMENJANAHARY M. Alpha, couleurs « bleu sante » (PRIMARY #106D8E, SECOND #2FA8B5,
GOLD #E8A82E, DARK #0B2E4F, BG #F0F6F9).

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Design du fichier de référence | `sldSz` 16:9 (14 630 400 × 8 229 600 EMU), polices Calibri/Aptos, accent #4472C4 (non repris), footer répété par slide ; aucun logo MMT dans le dépôt → placeholder textuel choisi |
| 2 | Dépendance dev | `python-pptx` 1.0.2 installé dans le venv racine uniquement (hors deps du projet, Python 3.8 préservé) ; PIL déjà présent (transitivement) pour le calcul des ratios d'images |
| 3 | Script générateur | `projet/code-source/scripts/dev/build_soutenance_pptx.py` (nouveau) : 21 slides alignées 1:1 sur le gabarit (cover, contenu, sommaire, tableaux, cards, `code_card`, figures `fig-3.png` slide 4 et `fig-5.png` slide 13, footer auteur/MMT) ; première version produite remaniée pour coller au gabarit (suppression de 4 diviseurs de section) |
| 4 | Sortie | `documents/slide_soutenance/V2soutenance_m2_mmt_alpha.pptx` régénéré |

**Vérifications.** extraction de la génération : `Slides : 21` ; relecture du PPTX par python-pptx :
21 slides titrées conformes au plan (1 cover, CONTEXTE/QUESTION/PROBLÉMATIQUE/OBJECTIFS/SOMMAIRE,
3× ÉTAT DE L'ART, 3× ÉTUDE DE L'EXISTANT, SOLUTION, FONCTIONNALITÉS, 3× CAS D'UTILISATION,
DÉMONSTRATION, PERSPECTIVES, CONCLUSION, MERCI) ; 2 images intégrées (slides 4 et 13) ; accents
français corrects (le fichier source a été réécrit en UTF-8 après une corruption d'encodage liée à
un `Set-Content -Encoding UTF8` PowerShell — ne plus éditer ce script via PowerShell).

**Reste :** relecture humaine dans PowerPoint (débordements, rendu des images) ; script + sortie non
suivis (commit en attente de validation utilisateur).

---

## 28/09/2026 — État d'avancement rédigé pour le supérieur

**Contexte :** à la demande de l'utilisateur, une synthèse d'avancement destinée à son supérieur,
rédigée en langage courant (peu de jargon), à partir du cahier des charges, de
`ai/dev/suivi_avancement.md` et de `ai/dev/logs.md`.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Nouveau document | `documents/etat_avancement_superieur.md` : approche générale (MVP puis passage à l'échelle), avancement des 6 objectifs du cahier, fiabilité (tests 54/54, API 3/3, générateur 44/44), livrables, mémoire/soutenance, points d'attention restants, verdict global, ordre de priorité des actions restantes |

**Vérifications :** synthèse alignée sur les chiffres réels du suivi (214 → 145 masters, 69 doublons,
32 %, précision sans faux positif, rappel hard 0.422, tests 54/54, API 3/3, 44/44, 9 chapitres, 37
tableaux, deck 21 slides). Aucune modification de code.

**Reste :** rien.

---

## 28/09/2026 — ELT : planification automatique + ingestion incrémentale (scheduler, watermark, API, front)

**Contexte :** automatiser les relances du pipeline ELT (le cahier des charges exige de ne pas
retraiter les données inchangées en boucle) : planification cron quotidienne/hebdo/mensuelle à heure
fixe, reprise après échec, incrémental par empreinte, pilotage via API + page web.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Logique planification pure | `provision/scripts/utils/schedule_logic.py` : validation (`frequency` daily/weekly/monthly, `time` HH:MM, `day_of_week` 0=lundi, `day_of_month` borné, `resume.mode` auto/since/full), calcul des échéances, `should_launch`, `build_run_flags` (→ `--resume`/`--since`/`--full`) |
| 2 | État de reprise | `provision/scripts/utils/pipeline_state.py` : `pipeline_state.json` (run_id, status running/ok/failed, mode, depuis quelle étape, début/fin) + CLI `begin/step/finish/show/resume_start` ; statut `running` = verrou anti-double-lancement |
| 3 | Watermark anti-retraitement | `provision/scripts/utils/watermark.py` : `file_signature` (sha256+taille+mtime), `should_extract` (priorité : `ingest.mode` source `full` > mode pipeline `full`/`since` > empreinte), `remember` (cap 50 lots), `report_from_watermark` |
| 4 | Scheduler cron | `provision/scripts/scheduler/scheduler.py` (+`install_cron.sh`) : vérification chaque minute, mini-lecteur YAML (pas de PyYAML dans `api-venv`), état `scheduler_runs.json`, lancement `run_pipeline.sh` en `start_new_session` (POSIX) ; plan désactivé par défaut |
| 5 | Orchestrateur | `provision/scripts/run_pipeline.sh` réécrit : modes `--resume` / `--full` / `--since` / `--from` / `--dry-run` ; parse le nom de l'étape pour `--from` ; exporte `PIPELINE_MODE`, `INGEST_SINCE`, `PIPELINE_RUN_ID` |
| 6 | Extraction incrémentale | `ELT/gen_extract_raw.py` : `PIPELINE_MODE` (défaut `full`), skip des tables CSV inchangées, rapport reconstruit via `report_from_watermark` (aval inchangé), `watermark.json` chargé/sauvegardé, compteur skipped en fin de run ; docstring orphelin cassant le `py_compile` corrigé |
| 7 | API gouvernance | `engine/governance/pipeline.py` (lecture/écriture `schedule.yaml`, statut pipeline) + `app.py` : `GET/PUT /pipeline/schedule` (écriture admin, 422 si invalide), `GET /pipeline/status` ; CORS `allow_methods` étendu à PUT |
| 8 | Frontend | `src/app/pipeline/` (page + client), `src/lib/api.ts` (GOVERNANCE_API_URL/KEY, types, fetchGovernance), `src/middleware.ts` (+`/pipeline`), `src/components/Sidebar.tsx` (menu « Pipeline ELT ») ; édition admin uniquement |
| 9 | Config | `provision/config/schedule.example.yaml` (committé) ; `schedule.yaml` runtime ajouté au `.gitignore` ; `data_sources.example.json` documente `"ingest": {"mode": "signature"}` |
| 10 | Tests | `tests/test_schedule_logic.py`, `test_watermark.py`, `test_pipeline_state.py`, `test_pipeline_api.py` (fixtures FakeCursor/FakeConnection, auth patchée, chemins surchargés en env) |
| 11 | Docs | `documents/cahier_des_charges.md` §4.1 (incrémental + planification), §4.4 (endpoints) ; `GUIDE/guide-vagrant.md` (drapeaux, §6bis cron, fichiers clés), `guide-backend.md` (API :8000 + modes de reprise), `guide-frontend.md` (page `/pipeline`, env) ; `ai/dev/suivi_avancement.md` point 13 |

**Vérifications.** `bash -n` → `run_pipeline.sh` OK, `install_cron.sh` OK (git-bash hôte) ; dry-run
hôte (git-bash, `PIPELINE_PYTHON` = python) → plans corrects pour full / resume / from=create_silver /
since+resume ; `python -m provision.scripts.scheduler.scheduler --dry-run` et `--status` OK ;
`py_compile` OK sur les 6 modules ; pytest ciblés **37 passed** (schedule_logic/watermark/state) et
**8 passed** (pipeline_api) ; **suite complète verte (~99 tests, 0 échec, deprecation warnings
seulement)**. Sémantique fixée pendant le dev : `--resume` ne continue qu'un run **échoué** (repère
la 1ʳᵉ étape non-ok), sinon nouveau run incrémental.

**Reste :** validation VM réelle (cron minute + run incrémental après reboot NameNode) ;
**commit `2c6a17f` (28 fichiers, +2665) réalisé le 28/09 après validation utilisateur**
(logs/docs du lot mis à jour : guide-vagrant, guide-backend, guide-frontend, cahier des charges,
suivi point 13).

## 28/09/2026 — Patients : interface liste + dossier (lecture seule, API FastAPI + frontend)

**Contexte :** il n'existait aucune interface de gestion des patients (liste ou dossier) ; l'API
FastAPI de gouvernance retournait des payloads minimaux. Ajout d'un périmètre **lecture seule**
(ADMIN + MEDECIN, base PostgreSQL centrale uniquement, pas de Hive) avec le contrôle de
consentement appliqué côté API : identité + correspondances de déduplication + avis par finalité.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `engine/governance/app.py` | `MASTER_COLUMNS` (9 colonnes réelles de `master_patient`), `MASTER_SELECT`, `IDENTITY_MAP_COLUMNS`, `CONSENT_COLUMNS`, helper `_master_row` ; `list_patients` : `purpose` obligatoire, `search` (nom complet / CIN / identifiant master), `page`/`page_size` (défaut 25, max 100), **filtrage par consentement avant pagination** (non-consentis silencieux, nombre exclu journalisé via `refusal_reason`), tri mémoire `(full_name.lower(), id)`, réponse `{items,total,page,page_size}` ; `get_patient` : enforce_consent d'abord, 404 si master absent, identité + `identity_map` (méthode/score) + `consents` ; docstrings corrigés (duplicata retiré, `dict_row` → tuples nommés) |
| 2 | `tests/test_governance_api.py` | FakeCursor/FakeConnection réécrits avec routage par motif SQL (`query_map`) + comportement partagé conservé pour les métriques ; `_patch_db(results, query_map)` ; fixtures `_master`/`M1/M2/M3` (9 colonnes) ; tests adaptés (tri) + nouveaux : recherche nom, recherche CIN/id, pagination (5 lignes, page_size=2, totals), `purpose` requis 422, master inconnu 404, dossier détaillé (identity_map + consents), dossier refusé 403 + audit |
| 3 | Frontend | `src/lib/api.ts` : `ApiError` (statut HTTP), types `PatientSummary`/`PatientList`/`IdentityMapEntry`/`PatientConsentRow`/`PatientDetail`, `listPatients` (search/page/purpose) et `getPatient` (403 typé) ; `src/app/patients/page.tsx` + `PatientsClient.tsx` (recherche différée 350 ms, pagination, message « silencieux » quand liste vide, lien dossier) ; `src/app/patients/[id]/page.tsx` + `PatientDetailClient.tsx` (carte identité, tableau identity_map avec badges méthode exact/new_master/probabilistic + score %, badges de consentement par finalité, états 403/404/erreur) ; `src/middleware.ts` (+`/patients/:path*`) ; `src/components/Sidebar.tsx` (menu « Patients », icône UserRound) |
| 4 | Docs | `GUIDE/guide-backend.md` §12 (patients, tableau endpoints, sémantique consentement, curls) + §13 Dépannage (ligne 403) + renumérotation 13/14 ; `GUIDE/guide-frontend.md` (arborescence, RBAC, tableau Pages `/patients` + `/patients/[id]`, dépannage, suite logique) ; `documents/documentation/api.md` (endpoints patients enrichis) ; `ai/dev/suivi_avancement.md` point 14 |

**Vérifications.** `py_compile` app.py OK ; pytest ciblés `test_governance_api.py` + `test_consent.py`
exit 0 ; **suite complète 102/102 tests, 0 échec** (`--junitxml` : tests=102 failures=0 errors=0
skipped=0) ; `npx tsc --noEmit` dans `front-optional/` → exit 0.

**Reste :** run réel sur une base PostgreSQL (VM indisponible) ; **commit `4e1f2d0` réalisé le
28/09 après validation utilisateur** (`documents/slide_soutenance/` reste non committé).

## 28/09/2026 — Tableau de bord pipeline : page `/dashboard` (rendu visuel de `/pipeline/status`)

**Contexte :** le statut du pipeline n'était représenté que par des badges texte sur `/pipeline` ;
demande d'une lecture visuelle « d'un coup d'œil » et de contenus de dashboard pertinents.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Aucun changement backend | `GET /pipeline/status` fournit déjà tout : plan/next_run/run_flags, run (statut, étapes, started/finished, last_error), zones Medallion (RAW/SILVER/GOLD : status + last_sync), sources watermark (tables + last_extracted_at), derniers 5 déclenchements cron |
| 2 | `src/lib/api.ts` | Types `PipelineStatus` affinés : zones `{status, last_sync}`, pipeline `started_at/finished_at/last_error/ingest_since`, steps typés pending/started/ok/failed |
| 3 | `src/app/dashboard/page.tsx` | Garde `getServerSession` → login sinon ; rend `DashboardClient` |
| 4 | `src/app/dashboard/DashboardClient.tsx` | Bannière état global (OK / en cours pulsation / échec / jamais exécuté, run_id + mode + last_error) ; 5 KPIs (étapes OK /5, durée du run, zones /3, sources + tables, compte à rebours prochain run) ; **schéma Medallion** 3 cartes zones reliées par flèches (statut, last_sync relatif, étape liée) ; **stepper 5 étapes** (nœuds pending/started pulsation/ok/failed, durée, dernière étape OK / échec, ingest_since) ; **fraîcheur des sources** (nb tables + barre d'âge : <7 j vert / 7–30 j ambre / >30 j ou jamais rouge) ; **planification** (activée/désactivée, fréquence, heure, jour, mode, prochain run, run_flags, schedule_error) ; **historique cron** (5 derniers : slot/heure/drapeaux/PID) ; **état de santé** (alertes consolidées) ; **polling auto 10 s désactivable** + bouton Actualiser ; helpers `fmtRelative`/`fmtCountdown`/`fmtDuration`/`fmtTime` ; Tailwind + SVG inline, aucune dépendance ajoutée |
| 5 | `src/middleware.ts` + `src/components/Sidebar.tsx` | Route `/dashboard/:path*` protégée ; entrée menu « Tableau de bord » (icône Gauge) en tête de la sidebar |
| 6 | Docs | `GUIDE/guide-frontend.md` (arborescence, RBAC, tableau Pages, dépannage, suite logique) ; `ai/dev/suivi_avancement.md` point 15 |

**Vérifications.** `npx tsc --noEmit` dans `front-optional/` → exit 0 ; `npm run build` → exit 0
(route `/dashboard` : 7.13 kB, 115 kB First Load JS) ; aucun test Python touché (suite inchangée
**102/102**). Décisions validées par l'utilisateur : nouvelle page dédiée (pas de refonte de
`/pipeline`), accueil `/synthese` inchangé, polling 10 s désactivable.

**Reste :** commit en attente de validation utilisateur.

## 28/09/2026 — Mémoire : restructuration selon le plan MBDS (rapports de référence Hasina / Jonah)

**Contexte :** analyse des rapports de référence `documents/RAPPORT_HASINA_1613.docx` et
`documents/Rapport de stage ETU 1156 … .docx` fournie par l'utilisateur ; décision : réorganiser
`chapters/` selon le plan MBDS (rendu final `documents/memoire_M2_MBDS.docx`). Informations
fournies par l'utilisateur : présentation MMT (2009, Siemens Healthineers, département R&D 2024),
dates du stage 06/07/2026 → 06/10/2026, motivation personnelle, budget en hypothèses structuré
humain / matériel-logiciel / total, périmètre non déployé.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Nouveaux fichiers de corps | `00-introduction` (générale, non numérotée : contexte, motivation, mission, problématique, plan) ; `01-presentation-stage` ; `02-etat-de-l-art` (2.1 notions + critères, 2.2 solutions, 2.3 comparatif, 2.4 pertinence — ex-ch.3 §3.2-3.4 intégré) ; `03-existant-solution` ; `04-demarche-projet` ; `05-exigences` (exigences par étapes du pipeline + CU1-CU8, ENF par qualité, interfaces IHM/API) ; `06-architecture` ; `07-conception` (plate-forme, structure du code, données, composants, déploiement, réalisation des étapes) ; `08-tests` ; `09-conclusion` (générale, non numérotée) |
| 2 | Liminaires | `remerciements.md` (brouillon à personnaliser) et `glossaire.md` hors du motif `0*.md` ; exporteur : insertion après la page de garde / après les acronymes ; acronymes + CU, ETP, JWT, PoC |
| 3 | Anciens fichiers supprimés | `01-introduction`, `03-etude-existant`, `04-analyse`, `05-conception`, `06-realisation`, `07-tests`, `08-conclusion`, `09-glossaire` (contenu repris, disponible dans `HEAD` = `830c231`) |
| 4 | Contenus neufs | activités d'ingénierie, méthode, outils (§4.1) ; risques projet (Tableau 20, cahier §11) ; Gantt par quinzaine (Tableau 22 : périodes sans trace avant le 23/08 figurées comme telles) ; budget 3 mois (Tableaux 23-25 : 3 450 000 Ar d'hypothèses, 0 Ar réel) + `documents/budget.md` ; vision utilisateur de l'existant (§3.1.1) ; livrables et état (Tableau 15) ; ENF (Tableau 28) ; pages IHM (Tableau 29, vérifiées dans `front-optional/src/app`) ; points d'entrée FastAPI avec rôles (Tableau 30, vérifiés dans `app.py`/`consent.py`) ; structure du code (§7.2.1) ; déploiement (§7.2.4) ; difficultés et apports personnels en conclusion |
| 5 | Corrections de fond | limite « endpoints `laboratory`/`malaria` » retirée (Flask n'a plus que 2 routes depuis le retrait du RMA) ; « 14 statuts » → 3 cas (`test_api.py`) ; « 420 faux positifs manqués » → faux négatifs ; ligne « Absents du périmètre » corrigée (frontend réalisé partiellement) |
| 6 | Annexes | renvois réaffectés ; **Annexe G** = questions anticipées (ex-§8.6) |
| 7 | Figures | renumérotées dans l'ordre de lecture (ancien→nouveau 1→2, 2→6, 3→1, 4→3, 5→4, 6→5, 7, 8) ; rendu relancé (8/8 OK, manifeste régénéré) ; `slides_soutenance.md`, `soutenance_script_oral.md`, `build_soutenance_pptx.py` réalignés |
| 8 | Consignes | `ai/memoire/README.md`, `methode.md`, `README.md`, `references/bibliographie.md` |

**Vérifications.** Contrôle scripté : 10 fichiers de corps × 1 H1, fences équilibrées, aucun `####`,
**48 tableaux numérotés 1→48 sans trou**, **8 figures 1→8**, aucun renvoi `§` interne orphelin.
Export DOCX (copie scratchpad) : H1 = Remerciements, Glossaire, Introduction générale, Chapitres
1-8, Conclusion générale, Bibliographie, Annexes ; 50 tableaux (48 + acronymes + glossaire),
8 images, 48 tableaux et 8 figures listés.

**Reste :** `documents/memoire_M2_MBDS.docx` **non régénéré** (fichier verrouillé, ouvert dans Word)
— relancer `python projet/code-source/scripts/dev/export_memoire_docx.py` après fermeture ;
remerciements à personnaliser ; périodes du Gantt avant le 23/08 à confirmer par l'utilisateur ;
écart à signaler : le cahier des charges docx cite « 4 mois » (§2.3) contre 3 mois réels ; captures
d'écran IHM absentes ; commit en attente de validation.

## 28/09/2026 — Mémoire : durée 4 mois, Gantt enrichi, nettoyage de `chapters/`, DOCX régénéré

**Contexte :** précisions de l'utilisateur sur la restructuration MBDS : stage de **4 mois** (début
juillet → fin octobre 2026) ; avant le 23/08, phase d'analyse **itérative** (discussions avec le chef,
compréhension du sujet, analyse de l'existant, documentation, état de l'art ≥ 3 semaines, problèmes et
contraintes réels), activités revenant en boucle ; captures IHM fournies par l'utilisateur plus tard.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Durée | intro « du 6 juillet à fin octobre 2026 », §4.3 et §4.4 ; l'écart avec « 4 mois » du cahier des charges (§2.3) disparaît |
| 2 | Gantt (Tableau 22) | 8 quinzaines jusqu'au 31/10 ; phases Cadrage / Existant et contraintes / Documentation et état de l'art / Développement / Tests / Rédaction / Finalisation ; □ = **déclaré** par le stagiaire sans trace datée, ■ = daté dans les journaux, ○ = prévu ; paragraphe sur l'analyse itérative en boucle |
| 3 | Budget | 4 mois : humain 4 600 000 Ar (hypothèses), matériel/logiciel 0 Ar, total 4 600 000 Ar (§4.4 + `documents/budget.md`) |
| 4 | Nettoyage `chapters/` | le répertoire ne contient que les 12 fichiers du plan ; lignes « > **Statut** » retirées des 10 fichiers de corps (elles s'imprimaient dans le DOCX) ; convention mise à jour dans `ai/memoire/README.md` |

**Vérifications.** `export_memoire_docx.py` → `documents/memoire_M2_MBDS.docx` écrit : H1 conformes au
plan MBDS, 50 tableaux (48 légendés + acronymes + glossaire), 8 images, 0 occurrence « Statut ».

**Reste :** captures d'écran IHM (§5.3.1, fournies par l'utilisateur) ; commit en attente de validation.

## 28/09/2026 — Soutenance : deck refondu sur le modèle du deck de référence (Hasina)

**Contexte :** revue du deck `V2soutenance_m2_mmt_alpha.pptx` contre `V2soutenance_m2_hasina.pptx`
(rendus PowerPoint slide par slide). Trame identique (21 slides) mais défauts bloquants : contenu
placé sur un canevas 13,3 x 7,5 dans un fichier 16 x 9 (bande vide, pied de page flottant),
`**gras**` et `code` affichés en brut (gras traité seulement en début de ligne), texte passant sous
les figures, slides en listes de texte ~11 pt, pas de bandeau de logos ; contenus : S2 ne présentait
pas l'entreprise, S10 « Existant — Modules » listait les modules de la plateforme, S18 annonçait 54/54.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Générateur réécrit | `scripts/dev/build_soutenance_pptx.py` : canevas réel 16 x 9 ; bandeau de logos (ITuniversity, MBDS, Université Côte d'Azur, MMT) + filet sur chaque slide ; pied de page « titre » présenté par … / date ; parseur **gras** / `code` en ligne ; vraies puces PowerPoint (retrait suspendu) ; cartes, pastilles numérotées, chips, bandeaux, chiffres clés, flèches ; images ajustées dans leur boîte sans chevauchement |
| 2 | Logos | `documents/image/logo-ituniversity.png`, `logo-mbds.jpg`, `logo-uca.png` extraits du deck de référence ; `mmt-logo.png` recadré automatiquement sur son contenu |
| 3 | Contenus | S2 = présentation MMT (2009, Siemens Healthineers, R&D 2024) ; S7 = 6 solutions du mémoire (§2.2) ; S8 = grille comparative ✔/◐/✖ (§2.3) ; S10 = systèmes existants (MAVIS, MMT_DB, CLINIQUE, sources de démo) ; S11 = chiffres clés ; S15 = 4 étapes / 8 CU (ch. 5) ; S16 = chiffres du run + 102/102 ; S17 = avant/après + métriques ; S18 = 102/102 ; date « Octobre 2026 » (constante `DATE`) |
| 4 | `documents/slides_soutenance.md` | 54/54 → 102/102 ; Septembre → Octobre 2026 |

**Vérifications.** Génération OK (21 slides) ; export PowerPoint (COM) des 21 slides en PNG et
contrôle visuel : aucun débordement, aucun `**`/backtick résiduel, logos et pieds de page alignés ;
`py_compile` OK. Validateur XML de la compétence non exécuté (`defusedxml` absent, non installé).

**Reste :** confirmer la date de soutenance (constante `DATE`) ; commit en attente de validation.

## 28/09/2026 — Dépôt : retrait du répertoire `archives/` (journal du PoC conservé)

**Contexte :** demande utilisateur de retirer `archives/` (PoC `datalake_mavis` + `elt.before`, 4,9 Mo,
173 fichiers suivis). Option retenue par l'utilisateur : retirer, mais **conserver le journal du PoC**,
cité comme preuve par le mémoire (captures de schémas §3.1.2, dates du Gantt §4.3).

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Journal conservé | `git mv archives/datalake_mavis/LOG.md documents/journal_poc_datalake_mavis.md` (historique Git préservé) |
| 2 | Retrait | `git rm -r archives` (173 fichiers) + suppression des fichiers ignorés restants (`.ai_context/`, `provision/config/data_sources.json`, `tsconfig.tsbuildinfo`) ; le code du PoC reste consultable dans l'historique Git |
| 3 | Renvois | chapitres 3 et 4 (8 renvois vers le nouveau chemin) ; `AGENTS.md`, `README.md`, `GUIDE/README.md`, `ai/dev/README.md`, `ai/memoire/README.md`, `ai/memoire/methode.md` |
| 4 | Non modifié | entrées historiques de `ai/dev/logs.md` et `ai/dev/suivi_avancement.md` (traces de l'état passé) |

**Vérifications.** Aucun code n'importait depuis `archives/` ; plus aucun renvoi vivant vers `archives/`
hors traces historiques ; DOCX **non régénéré** (fichier ouvert dans Word).

**Reste :** logos de la page de garde (ajout manuel) ; commit en attente de validation.

## 28/09/2026 — Mémoire : section « Les objets du dépôt » remplacée par un schéma entité-relation

**Contexte :** demande utilisateur de retirer ou d'améliorer la section « Les objets du dépôt » du
glossaire (inventaire de tables et de scripts, sans intérêt pour le jury), ou de la remplacer par des
schémas.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Glossaire | section « Les objets du dépôt » supprimée ; remplacée par un renvoi vers §7.2.1 (structure du code), §7.2.2 (Figure 7) et §7.2.3 (Figure 8) |
| 2 | Nouvelle Figure 7 (§7.2.2) | diagramme entité-relation Mermaid des 9 tables de `sql/schema.sql` : `master_patient` au centre, clés étrangères en trait plein, lien logique `raw_patient_record` ↔ `patient_identity_map` en pointillé, `api_user` → `access_audit` ; disposition `direction LR` (1re version horizontale 2931 px illisible, refaite) |
| 3 | Renumérotation | pipeline ELT 7 → 8, stratégie de test 8 → 9 ; `slides_soutenance.md` et `soutenance_script_oral.md` alignés (fig-7 → fig-8, fig-8 → fig-9) ; le générateur du deck (fig-1, fig-4) n'est pas concerné |

**Vérifications.** Rendu 9/9 figures OK (Figure 7 : 1518 x 1007 px, page paysage à l'export) ;
figures 1 → 9 et tableaux 1 → 48 sans trou ; DOCX régénéré (9 figures, 48 tableaux listés).
Attention : la régénération réécrit la page de garde (logos placés à la main perdus s'ils l'étaient).

**Reste :** commit en attente de validation.

## 28/09/2026 — Mémoire : glossaire court (section « Le vocabulaire du projet » retirée)

**Contexte :** demande utilisateur de retirer la section « Le vocabulaire du projet » ; choix : un
glossaire court, « le mémoire ne doit pas être un guide de lecture ».

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `chapters/glossaire.md` réécrit | une seule table terme / définition de 17 termes clés (Big Data, Data Lake, Medallion, ELT, HDFS, Hive, Spark, FHIR, déduplication, blocking, score et seuil, master patient, identity map, vérité terrain, P/R/F1, consentement par finalité, RBAC et audit) ; supprimés : mode d'emploi, colonnes Domaine et renvois, table des ~60 entrées, renvoi vers les objets du dépôt |
| 2 | Renvois | introduction (phrase courte), §1.2.2 (plus de renvoi au glossaire) ; consignes `ai/memoire/README.md` et `methode.md` (glossaire = termes clés ; pas de guide de lecture) |

**Vérifications.** Export DOCX de contrôle (copie scratchpad) : glossaire réduit à la table, aucun
« Comment lire » ni « Où c'est détaillé ». `documents/memoire_M2_MBDS.docx` **non régénéré**
volontairement (logos de page de garde placés à la main par l'utilisateur).

**Reste :** régénérer le DOCX quand l'utilisateur le décide ; commit en attente de validation.

## 28/09/2026 — Mémoire : phrases de consigne retirées des chapitres

**Contexte :** remarque utilisateur : chaque section du mémoire contenait une ou plusieurs phrases
d'instruction (consignes de rédaction restées dans le texte).

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Blocs « Objectif » | retirés des 10 fichiers de corps (`## Objectif` + consigne « Présenter… / Décrire… » + séparateur `---`) ; au ch. 2, l'encadré « Portée de l'étude » (contenu) est conservé |
| 2 | Consignes internes | citations `[AGENTS.md]` retirées (§1.2.2, encadré ch. 2, §7.2.1) ; méta-phrases reformulées : « Cette section présente… » (§2.1), « ce qui doit être dit » et « doivent rester explicites » (§4.2) |
| 3 | Conservé | transitions de prose (« le tableau ci-dessous… »), encadrés de limites, conclusions de chapitre |
| 4 | Consignes | `ai/memoire/README.md` et `methode.md` : plus de bloc « Objectif » ni de consigne dans le texte |

**Vérifications.** Aucun `## Objectif` ni `AGENTS.md` restant dans `chapters/0*.md` ; export DOCX de
contrôle (scratchpad) : 0 paragraphe « Objectif », 0 mention d'AGENTS.md, 9 figures et 48 tableaux
listés. `documents/memoire_M2_MBDS.docx` non régénéré (logos de page de garde placés à la main).

**Reste :** régénérer le DOCX quand l'utilisateur le décide ; commit en attente de validation.

## 28/09/2026 — Mémoire : phrases adressées au lecteur retirées (sommaire, annexes)

**Contexte :** l'utilisateur refuse les phrases d'aide à la lecture dans le mémoire (exemple : « Si le
sommaire reste vide : clic droit dessus puis « Mettre à jour les champs » »).

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Exporteur | `add_toc()` : note d'aide sous le sommaire supprimée (le champ TOC et `updateFields` restent) |
| 2 | `references/annexes.md` | introduction « comment lire les annexes » supprimée ; 6 lignes « *À lire avec* » supprimées ; annexe G : « elle ne remplace pas le développement : elle indique où le chercher » supprimé ; reformulations : « point d'attention du jury » (C), « le point à retenir » (D), « chez le lecteur » (F) |
| 3 | Chapitres 2 et 3 | renvois « Voir `references/bibliographie.md` » supprimés |

**Vérifications.** Export DOCX de contrôle (scratchpad) : aucune occurrence de « clic droit »,
« Mettre à jour les champs », « À lire avec », « le lecteur », « references/bibliographie ».
`documents/memoire_M2_MBDS.docx` non régénéré (logos placés à la main).

**Constat hors demande (non traité) :** l'exporteur crée un paragraphe par ligne Markdown (lignes
coupées), laisse les liens `[texte](chemin)` et l'italique `*…*` en brut, et ne rend pas un gras qui
court sur deux lignes.

**Reste :** régénérer le DOCX quand l'utilisateur le décide ; commit en attente de validation.

## 28/09/2026 — Mémoire : exporteur DOCX corrigé (paragraphes, liens, italique) + glossaire en liste

**Contexte :** demande utilisateur « corrige tout » (défauts de rendu relevés dans le DOCX) et glossaire
réduit à une simple liste terme / signification, sans définition du glossaire ni mode d'emploi.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `merge_lines()` (nouveau) | recolle les lignes coupées du Markdown en paragraphes logiques (texte, suites d'éléments de liste, citations) ; blocs de code, tableaux, titres, séparateurs intacts. Effet : ~1 180 → 801 paragraphes, plus de phrases coupées en fin de ligne ; le gras sur deux lignes est désormais rendu |
| 2 | `add_runs()` réécrit | gras, *italique*, `code` et liens `[texte](chemin)` (seul le texte est gardé), imbrication gras/italique/code |
| 3 | Paragraphes de texte | justifiés, comme dans les rapports de référence |
| 4 | `chapters/glossaire.md` | table → liste `**terme** : signification` (17 termes) ; 3 doubles « : » reformulés |
| 5 | Tableau 46 (conclusion) | `sha2(source|source_patient_id)` coupait la cellule sur le `|` → reformulé |

**Vérifications.** Export de contrôle (scratchpad) : 0 occurrence de `**`, `` ` ``, `](` ou d'italique
brut dans les paragraphes et les cellules ; 9 figures et 48 tableaux listés ; `py_compile` OK.
`documents/memoire_M2_MBDS.docx` régénéré ensuite (28/09/2026 14:56) après fermeture de Word : 0 markup brut.

**Reste :** logos de la page de garde (ajout manuel) ; commit en attente de validation.

## 28/09/2026 — Mémoire : liste des acronymes fusionnée dans le glossaire

**Contexte :** l'utilisateur veut retirer ou remplacer la liste des acronymes (recouvrement avec le
glossaire : HDFS, FHIR, ELT, MPI, RBAC). Choix : fusionner dans une seule section « Glossaire ».

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `chapters/glossaire.md` | liste alphabétique unique de 42 entrées : 17 termes + 30 sigles (5 doublons fusionnés), forme « **sigle (développé)** : signification » ; RBAC développé ; MBDS = Mobiquité (aligné sur la page de garde) |
| 2 | Exporteur | page « Acronymes » supprimée (`ACRONYMES`, `add_acronymes()`, appel et compteur retirés) ; le glossaire suit les listes des tableaux et figures |
| 3 | Consignes | `ai/memoire/README.md` : glossaire = termes et sigles, plus de liste d'acronymes séparée |

**Vérifications.** Export de contrôle (scratchpad) : pas de page « Acronymes », glossaire de 42 entrées,
0 markup brut ; `py_compile` OK. `documents/memoire_M2_MBDS.docx` **non régénéré** : ouvert dans Word.

**Reste :** régénérer le DOCX (avant l'ajout manuel des logos) ; commit en attente de validation.

## 28/09/2026 — Soutenance : supports alignés sur l'ELT en 5 étapes et 102/102

**Contexte :** après la restructuration MBDS du mémoire (ch. 06-07, planification/watermark, dashboard,
102/102), les supports de soutenance et les annexes gardaient des nombres périmés (54/54, 13 cas,
14/14, 4 plans, pipeline « en 4 étapes »).

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `documents/slides_soutenance.md` | S7 : pipeline « 4/4 au run de référence · orchestration en 5 étapes (reprise + incrémentale) », fig-8 « en cinq étapes (la 1re, préparatoire, est idempotente) », renvoi `chapters/07-conception.md §7.3.2` ; S9 : 16 tests = test d'intégration (statuts 401, 403, 422), contrôle d'accès vérifié par cas dédiés (rôle, consentement, finalité) ; S10 : 5 plans (102 tests 0:45 · éval hard 0:45 · pipeline 5 étapes 1:00 · tableau de bord `/dashboard` 0:30 · repli 0:30), note « plans 3 et 4 exigent VM + front-optional » |
| 2 | `documents/soutenance_script_oral.md` | en-tête « 16/16 = tests d'intégration » ; bloc commandes + plan 4 dashboard ; « trois choses à ne pas dire » : 16 tests prouvent joignabilité + statuts, le contrôle d'accès = cas dédiés ; S7 122 mots mesurés ; S10 85 mots de narration + vidéo 3:30 ; parole 1 558 (130/min) ; conclusion 11:08 → 15:30/16:00 (30 s filet), 19:30/20:00 |
| 3 | `scripts/dev/build_soutenance_pptx.py` | chip s16 « Pipeline **5 étapes** · run **4/4** » ; `s18_demo` : 5 plans (dashboard ajouté), durées 0:45/0:45/1:00/0:30/0:30, `row_h` 0.72→0.6 ; PPTX régénéré (21 slides) |
| 4 | `references/annexes.md` | Annexe A : 5 programmes (+ `ensure_generator_data.sh` préparatoire/idempotente) + reprise `--resume`/watermark/cron → §7.3.2 ; Annexe D : recherche/pagination/filtrage silencieux des patients + `/pipeline/schedule` (GET/PUT) + `/pipeline/status` ; Annexe G : 13 → 16 cas API gouvernance |
| 5 | `scripts/dev/export_memoire_docx.py` | RESUME/ABSTRACT : clause « pipeline rejouable, incrémental (empreinte des sources), planifiable (cron) » ; DOCX non régénéré |
| 6 | `documents/rapport_stage.md` | tests 54/54 → 102/102 (matcher 12 · consentement 21 · canonique 8 · API gouvernance 16 · planification/reprise 45) ; API données 14/14 → 3/3 ; §3.1 « ELT 4 étapes » → 5 étapes (reprise, watermark, cron) |
| 7 | `documents/etat_avancement_superieur.md` | 54 tests → 102/102 ; orchestration 4 → 5 étapes (run de référence 4/4) ; tableau de bord = pilotage `/dashboard` (distinct des tableaux d'analyse du PoC) ; verdict « 102/102 » |

**Vérifications.** Grep ciblé sur les 5 fichiers du lot : 0 résidu « 54/54 », « 13 cas », « 14/14 »,
« quatre programmes », « pipeline en 4 étapes » (seul résidu apparent : « quatre étapes sur quatre au
run de référence », voulu — l'orchestration en compte cinq). `py_compile` build + export OK. Pytest
fraîcheur `-p no:warnings --junitxml` : tests=102 failures=0 errors=0 (2,81 s). PPTX régénéré
(21 slides, 610 810 o). Non touchés à dessein : mentions « four/four 4/4 » historiques des chapitres
04/09, `cahier_des_charges.md` (spécification PoC datalake_mavis), `journal_poc_datalake_mavis.md`
(suppression interdite), glossaire figé (décision utilisateur).

**Reste :** filmer la vidéo de démo 3:30 (5 plans) ; régénérer le DOCX quand l'utilisateur le décide
(logos hand-placés) ; commit en attente de validation.

## 28/09/2026 — Mémoire : glossaire allégé (42 → 23 entrées)

**Demande utilisateur :** retirer du glossaire les termes déjà définis et argumentés dans le corps
(stack technique dans la partie outils, notions du sujet) : API, Big Data, CI, consentement par finalité,
Data Lake, déduplication, ETL, Hive, HDFS, JWT, MBDS, MDM, Medallion, MMT, REST, score pondéré et seuil,
SHA-256, SQL, vérité terrain. Lève le « glossaire figé » noté plus haut (nouvelle décision utilisateur).

| # | Fichier | Changement |
| - | ------- | ---------- |
| 1 | `chapters/glossaire.md` | 19 entrées supprimées ; 23 restent, ordre alphabétique inchangé |

| 2 | `documents/memoire_M2_MBDS.docx` | mêmes 19 paragraphes retirés directement dans le DOCX (python-docx), sans régénération, pour conserver les logos de la page de garde placés à la main |

**Vérifications.** Script de retrait : 19 lignes supprimées dans le Markdown et 19 paragraphes dans le DOCX ; glossaire DOCX relu (23 entrées) ; images, tableaux et reste du document inchangés (comparaison avec une copie de sauvegarde).

## 28/09/2026 — Suivi : Gantt Excel reconstruit (`documents/Gantt_suivi_projet.xlsx`)

**Constat sur `documents/Agile Gantt chart1.xlsx`** (non modifié) : modèle Microsoft ré-enregistré par
`wijmo.xlsx`, mise en forme conditionnelle perdue (0 règle : aucune barre), grille ne testant que
« Objectif »/« Jalon », chronologie décalée d'un jour (07/07) et limitée à 56 jours, dates `mm-dd-yy`,
soutenance calculée au 07/11/2026 (mémoire : fin octobre, Tableau 22).

| # | Élément | Contenu |
| - | ------- | ------- |
| 1 | Feuille « Gantt » | colonnes Description du jalon / Catégorie / Progression / Début / Jours ; légende 5 catégories ; début 06/07/2026 (C6) et décalage en semaines (C7) nommés |
| 2 | Chronologie | 119 jours depuis le lundi de début (06/07 → 01/11), mois épelés, initiales des jours, week-ends grisés, trait rouge « aujourd'hui » |
| 3 | Barres | 14 règles : couleur pleine = part faite, teinte = reste, par catégorie ; barre bleu pétrole pour les phases (catégorie vide) |
| 4 | Phase 1 « Étude du projet » | 7 tâches alignées sur le Tableau 22 ; dates sans trace datée commentées « à confirmer » ; phase calculée (début, durée, progression pondérée) |
| 5 | Feuille « Mode d'emploi » | cellules à saisir, règles de couleur, défilement |

**Vérifications.** Ouverture et recalcul dans Excel (COM) : 0 erreur de formule ; H7 = 06/07/2026, dernière
colonne = 01/11 ; phase 1 = 84 jours (06/07 → 28/09), 100 % ; rendu image contrôlé (barres, légende, mois).
Script de génération : scratchpad de session (`build_gantt.py`), non versionné.

## 28/09/2026 — Suivi : Gantt, phase 2 « Analyse et conception » ajoutée

Validée par l'utilisateur. 8 tâches (besoins et exigences, cas d'utilisation et rôles, modèle de données et
flux, architecture Medallion, gouvernance, moteur de déduplication, plan d'évaluation, jalon). Seul le jalon
est daté (fusion en dépôt unique, 07/09) ; les autres dates sont estimées et commentées « à confirmer »,
en cohérence avec le journal du PoC (démarrage 23/08, auth + RBAC 24/08) et le Tableau 21 (J1 01/09, J2 07–08/09).
**Vérifications.** Recalcul Excel : 0 erreur ; phase 2 = 10/08 → 07/09 (29 jours), 100 % ; rendu image contrôlé.

## 28/09/2026 — Suivi : Gantt, phase 3 « Réalisation » ajoutée

Validée par l'utilisateur. 10 lignes : PoC Big Data (23/08–01/09), auth + RBAC + API Flask + interface (24–27/08),
générateur + vérité terrain + MVP, fusion en dépôt unique (07/09), moteur de déduplication (07–08/09),
gouvernance complète (01/09–28/09) et jalons J1 à J4 du Tableau 21. Dates tirées du journal du PoC, de
`ai/dev/logs.md` et du Tableau 21 ; seul le début du générateur (29/08) est estimé et commenté.
**Vérifications.** Recalcul Excel : 0 erreur ; phase 3 = 23/08 → 28/09 (37 jours), 100 % ; rendu image contrôlé.

## 28/09/2026 — Suivi : Gantt, phases 4 « Tests et évaluation » et 5 « Rédaction et soutenance » ajoutées

Validées par l'utilisateur. Phase 4 : runs VM et API (07/09), évaluation vérité terrain (07–08/09), pytest
23/23 → 102/102 (07/09 → 28/09), recette prévue (29/09, 0 %). Phase 5 : rédaction (31/08 → 11/10, 70 %
estimé), slides et script oral (09/09 → 28/09, 80 % estimé), vidéo de démo, relecture encadrant, jalons
dépôt (26/10) et soutenance (30/10) prévus, catégorie « Non attribué », commentés « à confirmer ».
Couleur « Non attribué » foncée (barres confondues avec les week-ends).
**Vérifications.** Recalcul Excel : 0 erreur ; phase 4 = 35 jours, 66 % ; phase 5 = 31/08 → 30/10, 53 % ; rendu contrôlé.

## 28/09/2026 — Suivi : Gantt, thème modernisé

Demande utilisateur : thème et polices plus modernes et plus visuels. Données des phases inchangées.
Police Segoe UI (titres Segoe UI Semibold) ; bandeau de titre pleine largeur ; 4 tuiles d'indicateurs
calculées (prochain jalon, avancement global pondéré, tâches terminées, jours restants jusqu'à la
soutenance) ; catégories en pastilles colorées ; progression en barre de données ; jalons en losange ◆
coloré ; bande des mois en teintes alternées ; jour courant en pastille rouge + trait ; séparateurs de
semaine ; feuille « Mode d'emploi » restylée. Script scratchpad séparé en `build_gantt.py` + `gantt_data.py`.
**Vérifications.** Recalcul Excel : 0 erreur ; tuiles = J4 le 28/09 (aujourd'hui), 88 %, 28 / 35, 32 j ;
rendu image contrôlé. Correctif : recherche du prochain jalon passée de SUMPRODUCT(MAX(...)) (#VALUE!) à
MATCH(1, INDEX(...,0), 0).

## 28/09/2026 — Rapport de stage : nouveau document Word sur le gabarit des rapports de référence

Demande utilisateur : un rapport de stage plus propre et plus professionnel, au niveau des deux rapports
de référence (`RAPPORT_HASINA_1613.docx`, `Rapport de stage ETU 1156 … .docx`).

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `documents/rapport_stage_source.md` (nouveau) | réécriture condensée des chapitres 00–09 (~11 000 mots contre ~21 500) selon le plan MBDS ; renvois de fichiers du dépôt retirés du texte ; chiffres repris à l'identique ; bibliographie renumérotée [1]–[20] ; annexes A–C |
| 2 | `projet/code-source/scripts/dev/build_rapport_stage_docx.py` (nouveau) | part du rapport ETU 1156 comme gabarit (styles, page de garde à 4 logos, sections romain/arabe), en retire tout le contenu, les images, l'étiquette de sensibilité « Confidential » et les propriétés de l'autre organisation ; légendes à champs SEQ, sommaire et listes des tableaux et figures mis à jour par Word (COM) |
| 3 | `documents/Rapport_de_stage_RANOMENJANAHARY_Manjaka_Alpha.docx` (généré) | 61 pages, 40 tableaux, 5 figures (dont 1 page paysage), Gantt en cases colorées |

**Vérifications :** rendu PDF via Word relu page par page ; numérotation i… puis 1… contrôlée ;
paquet scanné (aucune trace du nom, des images ni de l'étiquette du gabarit). Le mémoire
(`chapters/`, `export_memoire_docx.py`) et `documents/rapport_stage.md` sont inchangés.

**Résultat :** rapport généré ; budget humain toujours présenté comme hypothèse de travail. Commit en attente.

## 28/09/2026 — Rapport de stage : emplacements de captures et extraits de code

Demande utilisateur : réserver des emplacements pour les captures d'interface et extraits de code qu'il prépare.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `build_rapport_stage_docx.py` | directive `Capture:` (image de `documents/captures/` si présente, sinon cadre « EMPLACEMENT RÉSERVÉ » avec consigne, légende numérotée) ; directive `Code:` (code réel du dépôt extrait par nom de fonction via `ast` ou par plage de lignes, numéros de ligne, docstring omise ; remplacé par une image si fournie) ; liste des extraits de code ; état des emplacements affiché à chaque génération |
| 2 | `documents/rapport_stage_source.md` | 16 emplacements de captures (C01–C16 : existant, Gantt, 7 écrans de l'interface, Swagger, HDFS, run du pipeline, comptages, refus 403, pytest, évaluation) et 7 extraits de code (X01–X07, dont annexe D) |
| 3 | `documents/captures/README.md` (nouveau) | liste des captures à préparer, noms de fichiers, priorité, règles (aucune donnée réelle, aucun secret visible) |

**Vérifications :** génération OK (72 pages, 21 figures dont 16 cadres réservés, 7 extraits) ; rendu PDF d'un cadre
réservé et d'un extrait contrôlé. C14 (refus 403) marqué « seulement si la base est peuplée » : elle ne l'a pas été
pendant le stage.

## 28/09/2026 — Rapport de stage : schéma des quatre notions clés (section 1.2.2)

Demande utilisateur : transformer le paragraphe de définitions (ELT, Medallion, MPI, consentement par finalité)
en schéma illustratif.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `documents/figures/src/notions_cles.html` (nouveau) | planche 2 × 2 en HTML/CSS/SVG : ELT contre ETL, zones RAW → SILVER → GOLD, fusion des trois fiches « Jean Rakoto » vers PAT-0102, finalités accordées/refusée avec refus par défaut (données fictives) |
| 2 | `projet/code-source/scripts/dev/render_html_figures.py` (nouveau) | rendu PNG par le Chrome/Edge du poste en headless (rien d'installé) → `documents/figures/notions_cles.png` (3000 × 2300 px) |
| 3 | `documents/rapport_stage_source.md` | paragraphe remplacé par une phrase d'introduction et la figure, placée avant le tableau des objectifs (évite un blanc de page) |
| 4 | `build_rapport_stage_docx.py` | message explicite si le .docx est verrouillé (ouvert dans Word) |

**Vérifications :** taille des textes calculée pour l'impression (≥ 18 px CSS, soit ≈ 7 pt à 16 cm) ; rendu contrôlé
en PNG puis dans le PDF d'une copie de contrôle (figure 1, page 4). Le .docx du dépôt n'a pas été régénéré :
il était ouvert dans Word.

## 28/09/2026 — Rapport de stage : tableau des outils avec logos (section 4.1.4)

Demande utilisateur : représenter les outils par leur logo ; colonnes Usage, Outil (logo), Version, Description.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `documents/icon/` | 12 logos manquants ajoutés : VS Code, Node.js, Git, VirtualBox, Ubuntu, Laragon, OpenJDK, pandas, FastAPI, pytest, Mermaid (Simple Icons, CC0, couleurs de marque officielles), RapidFuzz (dépôt GitHub du projet) |
| 2 | `projet/code-source/scripts/dev/build_logos.py` (nouveau) | normalise 24 logos (png, jpg, webp, avif, svg) dans un cadre identique 400 × 140 via Chrome headless → `documents/figures/logos/<id>.png` ; agrandissement pour les images à marges |
| 3 | `build_rapport_stage_docx.py` | tableaux `{logos}` : cellule `logo:<id> Nom` (logo + nom), `^` fusionne la cellule d'usage avec celle du dessus, groupe d'usage maintenu sur une page, largeurs fixes |
| 4 | `documents/rapport_stage_source.md` | tableau des outils refait : 24 outils en 6 usages, versions tirées du dépôt (Vagrantfile, bootstrap.sh, package.json, pyproject.toml) ou du poste, et note sur l'origine des versions |

**Vérifications :** planche des 24 logos contrôlée ; rendu du tableau relu dans le PDF d'une copie de contrôle (pages 18–20).
Non utilisés dans le projet et donc écartés : MongoDB, HBase, VMware, Siemens. Version de Laragon non déterminée (« — »).
Le .docx du dépôt n'est pas régénéré tant qu'il est ouvert dans Word.

## 28/09/2026 — Rapport de stage : dates de consultation dans la bibliographie

Demande utilisateur : dater la consultation des références en ligne, dont le contenu peut changer.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `documents/rapport_stage_source.md` | bibliographie réécrite : « En ligne : URL (consulté le …) » pour les 16 ressources web ; dates reprises de `references/bibliographie.md` (8/09/2026 pour [1]–[12], 27/09/2026 pour [13]–[20]) ; URL complètes rétablies ; DOI pour [2], [3], [15] ; référence du Journal officiel pour le RGPD [10] ; version citée quand elle est connue (RapidFuzz 3.14.5, FHIR 5.0.0, Talend MDM 8.0) ; note d'introduction sur l'évolution possible des pages |

**Vérifications :** rapport régénéré (75 pages) ; rendu des pages 54–55 contrôlé. Aucun lien n'a été re-vérifié en ligne
dans cette session : les dates sont celles des vérifications consignées.

## 28/09/2026 — Soutenance : nouveau deck refondu (20 slides)

Demande utilisateur : slides plus propres et plus belles. Choix validés : nouveau deck, 15–20 min, plan de la
référence (Hasina) conservé, style aligné sur le rapport.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `projet/code-source/scripts/dev/build_soutenance_deck.py` (nouveau) | deck 16:9 (13,33 × 7,5 po) généré en python-pptx : 20 slides dans l'ordre de la référence, titre affirmatif et un message par slide, visuels natifs (cartes, flux, tableau comparatif coloré, graphique P/R/F1 modifiable), schéma des notions, logos des outils, emplacement vidéo/capture C07, notes de présentation sur chaque slide ; contrôle de géométrie avant écriture |
| 2 | `documents/slide_soutenance/Soutenance_M2_MBDS_RANOMENJANAHARY.pptx` (généré) | nouveau deck ; l'ancien `V2soutenance_m2_mmt_alpha.pptx` et `build_soutenance_pptx.py` sont inchangés |

**Incident :** premier fichier refusé par PowerPoint — une zone de texte de largeur négative (slide 11). Isolé par
génération slide par slide ; corrigé, et un contrôle de géométrie bloque désormais ce cas à la génération.
**Vérifications :** ouverture et export PDF par PowerPoint ; 20 slides relues visuellement ; validateur OOXML OK ;
étiquettes du graphique en virgule décimale indépendamment de la langue du poste.
**Reste :** le script oral (`documents/soutenance_script_oral.md`, 13 slides) ne suit pas encore ce deck.

## 28/09/2026 — Soutenance : animations (essai sur la slide 2)

Demande utilisateur : gérer les animations, tester d'abord sur la slide 2.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | `projet/code-source/scripts/dev/pptx_anim.py` (nouveau) | écrit le XML de minutage PowerPoint (`p:timing`, `p:bldLst`, `p:transition`) que python-pptx ne gère pas : modèle clics → étapes « après la précédente » → groupes « avec la précédente » ; effets fondu, balayage, zoom ; transition de slide |
| 2 | `build_soutenance_deck.py` | repères `mark`/`since` pour grouper les formes ; slide 2 : clic 1 = trois chiffres clés en cascade, clic 2 = domaines d'activité, clic 3 = encart du stage ; transition en fondu ; option `--out` |

**Vérifications :** validateur OOXML OK ; relecture par PowerPoint (COM) de la séquence de la slide 2 : 14 effets de
fondu, 3 déclenchements au clic, enchaînements « avec » / « après la précédente » conformes, transition en fondu.
Le deck du dépôt n'a pas été régénéré : il était ouvert dans PowerPoint (test sur une copie de contrôle).

## 28/09/2026 — Dépôt : rangement de `documents/`

Plan validé par l'utilisateur.

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Supprimé | `documents/Agile Gantt chart1.xlsx` (remplacé par `Gantt_suivi_projet.xlsx` ; récupérable dans l'historique Git) |
| 2 | Déplacés vers `documents/references/` | `RAPPORT_HASINA_1613.docx`, `Rapport de stage ETU 1156 RAMANANTSAFIDY Jonah Fitia.docx` (non versionnés), `V2soutenance_m2_hasina.pptx`, `Etat-de-l'art-M2-pro-stage.docx.md` (`git mv`) |
| 3 | Renvois | `build_rapport_stage_docx.py` (TEMPLATE + docstring), `build_soutenance_pptx.py` (docstring), `ai/memoire/README.md` |
| 4 | `.gitignore` | ajout de `documents/references/*.docx` (les rapports d'autres étudiants restent hors Git) |

**Vérifications.** `py_compile` des deux scripts OK ; le chemin TEMPLATE résolu depuis `ROOT` existe ; plus aucun
renvoi vers les anciens chemins hors `ai/dev/logs.md` (historique conservé). Non touchés : verrous `~$` (fichiers
ouverts), ancien deck `V2soutenance_m2_mmt_alpha.pptx` (encore utilisé par deux scripts). Pas de commit.

## 28/09/2026 — Dépôt : nettoyage profond (lot 1, sans risque)

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Caches supprimés (ignorés, régénérables) | 28 dossiers `__pycache__` / `.pytest_cache`, `front-optional/.next`, `tsconfig.tsbuildinfo`, `patient_data_platform.egg-info` |
| 2 | Versionnés supprimés (récupérables via Git) | `front-optional/todo.md` (réponse de chat de juillet 2025), `front-optional/bokt.new` (brouillon du sujet initial), `projet/mvp/.agents/skills/…` et `.claude/skills/…` (liens vers un skill Streamlit du `.venv`) |

Conservés à dessein : données générées (`data/`), journaux (`logs/`, règle « ne jamais supprimer de traces »),
`.vagrant/` (état de la VM), `.venv/`, `node_modules/`, `cim_embeddings.pkl`, `data_sources.json`.
`projet/mvp/src/patient-data-platform` : dépôt Git imbriqué (historique propre, 483 Ko), référencé comme gitlink
sans `.gitmodules` — laissé en place en attente de décision utilisateur.

## 28/09/2026 — Dépôt : nettoyage profond (lot 2, validé par l'utilisateur)

| # | Action | Détail |
| - | ------ | ------ |
| 1 | Ancien deck retiré | `documents/slide_soutenance/V2soutenance_m2_mmt_alpha.pptx` + `scripts/dev/build_soutenance_pptx.py` (remplacés par `Soutenance_M2_MBDS_RANOMENJANAHARY.pptx` / `build_soutenance_deck.py`, dont le docstring est mis à jour) |
| 2 | 13 icônes inutilisées | `documents/icon/` : 410687, MongoDB, database, diusalisation, elt, entonnoir, goal, haddop_hdfs, hbase_logo, logo siemens, logo-sm, puits-deau, vmware |
| 3 | Dépôt imbriqué supprimé | `projet/mvp/src/patient-data-platform` (ancienne copie du MVP, gitlink sans `.gitmodules`, historique local de 483 Ko perdu — décision utilisateur) |
| 4 | Renommé | spec du MVP sans le suffixe « (1) » |

**Vérifications.** `py_compile` de `build_soutenance_deck.py` et `build_logos.py` OK ; toutes les sources de
`build_logos.py` existent encore dans `documents/icon/` ; plus aucun renvoi vers les fichiers retirés
(hors historique de `ai/dev/logs.md`). Pas de commit.

## 28/09/2026 — Mémoire : affinage de l'état de l'art (chapitre 2)

| # | Fichier | Changement |
| - | ------- | ---------- |
| 1 | `chapters/02-etat-de-l-art.md` | détails d'implémentation (fichiers, poids, config VM, tableau RGPD → fichiers) retirés et renvoyés au § 7.2.3 ; § 2.1.1 : mots-clés, biais commercial, tableau 5 réaligné sur les blocs A-E de la grille (12 traités, 6 partiels, 1 hors périmètre, 1 optionnel) ; § 2.1.2 : EM, Ditto, LLM ; § 2.1.3 : phonétique, version RapidFuzz sous Python 3.8 ; § 2.1.6 : loi n° 2014-038 (art. 13-15, 17, 18, 20, 28, 43, 46), CMIL non opérationnelle, tableau loi malgache / RGPD, FHIR Consent, PPRL ; § 2.1.8 : lakehouse, ACID ; § 2.2.1 : OpenCR, coût et dépendance (Talend Open Studio retiré le 31/01/2024) ; § 2.2.2 (nouveau) : briques alternatives ; § 2.3 : grille E1-E2 / Q1-Q5, Splink explicable (graphique en cascade), HAPI ◐ en gouvernance (cadre de consentement à programmer), Q4 du projet ◐ |
| 2 | `references/bibliographie.md` | B4 corrigée (3.14.5 exige Python ≥ 3.10 ; 3.9.7 = dernière pour 3.8) ; B15, B16 complétées ; B21-B31 ajoutées avec date de consultation |
| 3 | `chapters/07-conception.md` | matrice du § 7.1 : arbitrage 4 « moteur d'appariement » (moteur propre 4.50, Splink 4.05, recordlinkage 3.85, dedupe 3.70, Ditto/LLM 1.70) + lecture honnête ; renvoi § 2.1.3 → § 7.2.3 |
| 4 | `chapters/04-demarche-projet.md`, `chapters/09-conclusion.md` | contexte juridique : « non traité » → « partiel » (loi étudiée, formalités CMIL non accomplies) |
| 5 | `chapters/08-tests.md` | preuve des tests d'API rattachée au § 7.2.3 |
| 6 | `chapters/03..09` | tableaux renumérotés (le chapitre 2 compte un tableau de plus) : 49 légendes, renvoi « Tableau 17 » → 18 |

**Vérifications.** Articles de la loi lus dans le texte officiel (PDF AFAPDP) ; compatibilité Python 3.8 lue dans
les métadonnées PyPI (`requires_python`) ; export DOCX de contrôle dans le scratchpad : 10 chapitres, 49 tableaux,
9 figures. **Incohérence relevée, non corrigée dans le code** : la bibliographie citait RapidFuzz 3.14.5, qui ne
s'installe pas sous Python 3.8 ; la version réellement installée sur la VM n'est tracée nulle part.
`documents/rapport_stage_source.md` (rapport Word) non resynchronisé. Pas de commit.

## 29/09/2026 — Soutenance : slide « Architecture technique » (13/21)

| # | Élément | Détail |
| - | ------- | ------ |
| 1 | Méthode | slide insérée **directement dans le .pptx** (duplication de la slide 12 puis python-pptx), sans relancer `build_soutenance_deck.py`, pour préserver les animations et transitions ajoutées à la main dans PowerPoint |
| 2 | Contenu | six couches (exposition et gouvernance, base centrale, moteur de déduplication, traitement distribué, lac de données, infrastructure), chacune avec icône, technologies, rôle et logos (`documents/figures/logos/`, marges rognées) ; bandeau « aucune licence, aucun abonnement, aucune donnée hors de l'établissement » ; notes de l'orateur |
| 3 | Faits vérifiés | Vagrantfile (`ubuntu/focal64`, 8192 Mo, 4 CPU), `bootstrap.sh` (Hadoop 3.3.6, Hive 3.1.3, Spark 3.4.2, OpenJDK 8), § 7.1 (FastAPI, Flask, Next.js optionnel), § 4.4 (logiciels : 0 Ar) |
| 4 | Pied de page | numérotation « N / 20 » → « N / 21 » sur toutes les slides |

**Vérifications.** `validate.py --original` : PASSED ; rendu PowerPoint de la slide 13 contrôlé (pas de débordement) ;
transition conservée sur la nouvelle slide ; animations de la slide 14 intactes (24 effets). La nouvelle slide n'a
**pas d'animation** (la chronologie héritée de la slide 12 visait des formes supprimées). Le générateur
`build_soutenance_deck.py` ne contient pas cette slide : le relancer écraserait les retouches manuelles.
Sauvegarde du deck avant modification dans le scratchpad de session. Pas de commit.

## 29/09/2026 — Mémoire : mots-clés retirés du Résumé

`projet/code-source/scripts/dev/export_memoire_docx.py` : constante `MOTS_CLES` supprimée ; `add_abstract()` rend la
ligne de mots-clés optionnelle et le Résumé est appelé sans elle. L'Abstract anglais garde ses « Keywords ».

**Vérifications.** `python -m py_compile` : OK. DOCX régénéré (`documents/memoire_M2_MBDS.docx`, 10 chapitres, 9 figures, 49 tableaux ; Résumé 191 mots, Abstract 154 mots) : plus aucune ligne « Mots-clés », « Keywords » présente. Pas de commit.

## 29/09/2026 — Rapport de stage : mots-clés retirés du Résumé

`documents/rapport_stage_source.md` : ligne « **Mots-clés** : … » supprimée du Résumé (les « Keywords » de l'Abstract
sont conservés). Rapport régénéré par `build_rapport_stage_docx.py` : 75 pages, 16 963 mots ; plus aucune ligne
« Mots-clés » dans le .docx, contrôlé par relecture du fichier produit. Pas de commit.

## 29/09/2026 — Mémoire : introduction générale réécrite (contexte humain)

`chapters/00-introduction.md` : la section « Contexte général » s'ouvre sur le parcours d'une patiente (pharmacie,
consultation, imagerie) avant le contexte technique ; elle précise que les sources ne sont pas figées (réorganisation
des services, nouvelles technologies de base) et pose le besoin du patient (consultations autorisées, imagerie refusée).
« Mission confiée » : ajout de l'état réel du consentement, contrôlé **par finalité** ; le contrôle **par type de
dossier** est en cours (aucune trace dans `projet/code-source/` à ce jour). Textes validés par l'auteur.

**Vérifications.** Mémoire régénéré (10 chapitres, 9 figures, 49 tableaux) ; nouveaux passages présents dans le .docx.
`documents/rapport_stage_source.md` resynchronisé (mêmes passages dans son Introduction) ; rapport régénéré :
75 pages, 17 149 mots, passages présents dans le .docx. Pas de commit.
- Plan de l'Introduction du rapport mis en liste à puces (un point par chapitre). Génération du .docx refusée : fichier ouvert dans Word ; rendu vérifié sur une copie hors dépôt (puces présentes, 75 pages).
- Rapport régénéré après fermeture de Word : 75 pages, 17 163 mots, plan en puces présent dans le .docx.

## 29/09/2026 — Rapport de stage : allègement du chapitre 7 (Conception)

`documents/rapport_stage_source.md`, chapitre 7 : sept coupes validées par l'auteur. Gouvernance regroupée dans une
seule section (7.3.3) ; tableau des tables de la base centrale remplacé par une phrase (figure 7 et extrait X02
conservés) ; vue statique du code en une phrase ; paragraphe « parité Spark » et paragraphe FastAPI/Flask supprimés
(redondants avec leurs tableaux) ; déploiement renvoyé au chapitre 6 ; phrase sur le protocole de parité retirée.
Renvoi de la section 3 vers les rôles corrigé (7.2.3 → 7.3.3). Aucun fait nouveau introduit.

**Vérifications.** Chapitre 7 : 2 397 → 2 053 mots. Rapport régénéré : 75 → 74 pages, 17 163 → 16 792 mots.
Sauvegarde de la source avant coupe dans le scratchpad. `chapters/07-conception.md` (mémoire) non modifié. Pas de commit.

## 29/09/2026 — Rapport de stage : allègement du chapitre 4 (Démarche projet)

`documents/rapport_stage_source.md`, chapitre 4 : cinq coupes validées par l'auteur. Tableaux « contraintes » et
« risques » fusionnés en un seul (contrainte ou risque, traitement, constat), lignes Python 3.8 et partage vboxsf
renvoyées au tableau des difficultés du chapitre 7 ; gestion de la configuration en un paragraphe ; origine des
versions en une phrase ; lignes TypeScript, Tailwind et D3.js regroupées dans la ligne Next.js ; tableau « Coût total »
remplacé par une phrase (4 600 000 Ar). Ligne « Reproductibilité » : constat « appliqué » (l'ancien tableau n'en
donnait pas). Aucun autre fait nouveau.

**Vérifications.** Chapitre 4 : 2 048 → 1 784 mots. Rapport régénéré : 74 → 73 pages, 16 792 → 16 507 mots.
Sauvegarde de la source avant coupe dans le scratchpad. Mémoire (`chapters/04-*.md`) non modifié. Pas de commit.

## 29/09/2026 — Rapport de stage : retouches du chapitre 2 et allègement du chapitre 5

`documents/rapport_stage_source.md` (coupes validées par l'auteur) :
- **Chapitre 2** (état de l'art, jugé prioritaire) : deux retouches seulement ; mention de `sentence_transformers`
  retirée (déjà deux fois au chapitre 7) ; dernière phrase des « écarts assumés » raccourcie avec renvoi au chapitre 7.
  Aucune source, aucun produit, aucun chiffre retiré.
- **Chapitre 5** : captures d'IHM ramenées de sept à trois (C04 synthèse, C07 pipeline, C09 fiche patient ;
  C03, C05, C06, C08 retirées, les écrans restant décrits dans le tableau des pages) ; CU7 réduit à la vision
  utilisateur ; phrase redondante de CU3 retirée ; distinction Flask/FastAPI conservée au chapitre 5 et remplacée
  par un renvoi en 7.3.3.
- `documents/captures/README.md` : C03, C05, C06, C08 marquées « retiré du rapport ».

**Vérifications.** Rapport régénéré : 73 → 71 pages, 16 507 → 16 210 mots. Sauvegardes de la source avant chaque
coupe dans le scratchpad. Mémoire non modifié. Pas de commit.

## 29/09/2026 — Chapitre 1 relu ; introduction et contexte métier alignés (mémoire et rapport)

Relecture du chapitre 1 du rapport : renvois 4.1.5, 7.2.3, 8.3, 8.4 justes après les coupes ; faits sur MMT
identiques au mémoire ; `documents/figures/notions_cles.png` présent. Retouches validées par l'auteur :
- introduction (`chapters/00-introduction.md` et `documents/rapport_stage_source.md`) : « Une patiente » →
  « Un patient », pour que Jean Rakoto (chapitre 1) illustre le même récit ;
- contexte métier (`chapters/01-presentation-stage.md` et rapport) : première phrase, redondante avec
  l'introduction, remplacée par « Le cas de référence de la plateforme en donne un exemple concret… » ; dans le
  mémoire, la mention « Exemple réel » (contradictoire avec des données fictives) est supprimée.

**Vérifications.** Régénération des .docx non exécutée dans cette session (vérification de sécurité de l'outil
indisponible) : relancer `export_memoire_docx.py` et `build_rapport_stage_docx.py`. Pas de commit.

## 29/09/2026 — Introduction sur une page ; script oral réécrit pour le deck de 20 slides

Demande de l'auteur : introduction et annonce du plan sur **une seule page** ; le récit et la motivation passent
à l'oral.
- `chapters/00-introduction.md` : sous-titres supprimés ; contexte humain, mission (consentement par finalité
  réalisé, par type de dossier en cours), contraintes, problématique, plan (tableau 1 conservé, raccourci, pour
  ne pas décaler la numérotation des 49 tableaux). Motivation personnelle retirée.
- `documents/rapport_stage_source.md` : même introduction ; plan en quatre puces groupées (chapitres 1-2, 3-4,
  5-7, 8 et conclusion), la version à neuf puces débordant de deux lignes.
- `ai/memoire/README.md` : description de l'introduction mise à jour (une page, motivation à l'oral).
- `documents/soutenance_script_oral.md` : réécrit pour les 20 slides du deck présent sur disque (l'ancien script
  suivait 13 slides et contenait un fragment corrompu) ; récit du patient (S3), motivation (S2), consentement par
  type de dossier annoncé comme en cours (S14, S18), trois choses à ne pas dire, questions probables du jury ;
  1 587 mots comptés par script, 16:30 prévues sur 20:00.

**Vérifications.** Pagination contrôlée dans Word (COM) : mémoire, introduction et plan sur la page 13 ; rapport
(copie générée hors dépôt), introduction et plan sur la page 15, chapitre 1 en page 16 ; rapport 70 pages,
15 872 mots. Mémoire régénéré. `documents/Rapport_de_stage_RANOMENJANAHARY_Manjaka_Alpha.docx` **non régénéré**
(ouvert dans Word).
**Constat, non corrigé :** le deck sur disque (1 197 754 octets, modifié le 29/09 à 19:27) est identique à la
version commitée (`bf0171c`, 20 slides) : la version de 21 slides avec la slide « Architecture technique » et les
animations manuelles n'est plus dans l'arbre de travail. Deck non modifié en attendant l'avis de l'auteur.
Pas de commit.

## 29/09/2026 — Deck : notes de l'orateur alignées sur le script ; perspective ajoutée (slide 18)

Accord de l'auteur. Sur le deck présent sur disque (20 slides) : notes des 20 slides remplacées par le texte
« à dire » et la transition de `documents/soutenance_script_oral.md` (slide 17 : narration de la vidéo) ;
slide 18, « Court terme » : ajout de « consentement par type de dossier » (texte d'un seul run modifié, formes et
animations non touchées). Copie du deck avant modification dans le dossier temporaire.

**Vérifications.** Deck rouvert par PowerPoint (COM) : 20 slides ; slide 18 exportée en image et relue : pas de
débordement. Rapport régénéré après fermeture de Word : 70 pages, 15 872 mots. Pas de commit.

## 29/09/2026 — Rapport de stage : légendes raccourcies ; symboles du tableau comparatif retirés

`documents/rapport_stage_source.md`, à la demande de l'auteur :
- 57 légendes (tableaux, figures, captures, extraits de code) ramenées à un intitulé court (2 à 8 mots) ;
  listes des tableaux et des figures mises à jour d'elles-mêmes à la génération.
- Tableau comparatif (chapitre 2) : ✔ / ◐ / ✖, rendus dans une police de symboles différente du texte, remplacés
  par « oui », « partiel », « non » ; légende des symboles supprimée.
- Gantt : la légende des couleurs, retirée de l'intitulé, passe dans la phrase qui présente le diagramme.

**Vérifications.** Copie PDF générée hors dépôt et relue (liste des tableaux, page du comparatif) ; aucun
symbole ✔ ◐ ✖ restant dans la source ; copie : 70 pages. Rapport du dépôt régénéré ensuite (70 pages, 15 152 mots). Mémoire
(`chapters/`) non modifié. Pas de
commit.

## 29/09/2026 — Rapport de stage : légendes courtes pour les extraits de code

`projet/code-source/scripts/dev/build_rapport_stage_docx.py` (`code()`) : la référence « fichier, l. X–Y » n'est
plus ajoutée à la légende ; elle ouvre l'encadré de code en gris italique. Pour un extrait remplacé par une
capture, la légende reste courte (référence non affichée).

**Vérifications.** Copie PDF hors dépôt relue : liste des extraits sans chemins, encadré de l'extrait 1 correct
(page 34). Rapport régénéré (70 pages). Pas de commit.

## 29/09/2026 — Rapport de stage : figures, tableaux et captures redondants supprimés ou fusionnés

`documents/rapport_stage_source.md`, neuf changements validés par l'auteur :
1. figure « La stratégie de test » (fig-9) supprimée : doublon du tableau des niveaux de test, avec deux
   incohérences (« API gouvernance 3/3 » au lieu de l'API des indicateurs ; planification rangée sous « moteur ») ;
2. figure « Des concepts aux briques techniques » (fig-6) supprimée, renvoi à la section 2.5 ;
3. tableau des six objectifs (chapitre 1) remplacé par une phrase, renvoi au chapitre 5 ;
4. extrait X03 (YAML des poids) supprimé, chemin du fichier cité dans le texte ;
5. coûts humains et matériels fusionnés en un tableau « Budget du projet sur quatre mois » avec total ;
6.–8. captures C02 (Gantt détaillé), C13 (comptages) et C14 (refus 403, irréalisable sans base peuplée) retirées ;
9. annexe B : tableau des modules du générateur remplacé par un renvoi à la section 5.1.5.
`documents/captures/README.md` : C02, C13, C14 et X03 marquées « retiré du rapport ».

**Vérifications.** Rapport régénéré : 70 → 67 pages, 15 152 → 14 647 mots ; page du budget relue sur une copie PDF
hors dépôt. Figures `fig-6.png` et `fig-9.png` conservées dans `documents/figures/` (encore utilisées par le
mémoire). Mémoire non modifié. Pas de commit.

## 29/09/2026 — Mémoire : figure 9 (stratégie de test) corrigée

`chapters/08-tests.md` : diagramme Mermaid de la figure 9 corrigé. Les tests de planification et de reprise (45)
forment leur propre bloc au lieu d'être rangés sous « moteur + gouvernance », qui compte 57 tests. Le bloc
système indique « API des indicateurs (Flask) » et non « API gouvernance » : `provision/api/test_api.py` teste bien
l'API Flask (port 5000). La légende de la figure et la ligne « API » du tableau 44 sont alignées.

**Vérifications.** `render_mermaid_figures.py` : 9 figures rendues, figure 9 relue. Les autres PNG, régénérés sans
changement de contenu, ont été remis à leur version commitée ; seuls `fig-9.png` et `manifest.json` (numéros de
ligne des sources) changent. Mémoire régénéré (9 figures, 49 tableaux). Pas de commit.

## 29/09/2026 — Pipeline : historique chiffré des runs conservé en base (nouvelle fonctionnalité)

Demande de l'auteur : savoir, pour un run daté, combien de lignes ont été lues dans chaque source et combien
de patients maîtres en sont sortis, et **conserver ces chiffres en base**. Constat préalable : aucun historique
n'existait (`pipeline_state.json` et les rapports d'extraction sont écrasés à chaque run ; le seul run reconstituable
est celui du 07/09, par ce journal).

| # | Fichier | Détail |
| - | ------- | ------ |
| 1 | `projet/code-source/sql/schema.sql` | tables `pipeline_run` (un run par ligne, statut contraint) et `pipeline_run_source` (détail par source), idempotentes |
| 2 | `provision/scripts/utils/run_metrics.py` (nouveau) | résumés `summarize_extract` / `summarize_dedup` ; tampon local `provision/metadata/run_metrics.json` rangé par `PIPELINE_RUN_ID` ; `flush` : enregistrement en base (upsert) si `DATABASE_URL`, sinon run conservé en attente ; ne lève jamais |
| 3 | `gen_extract_raw.py`, `create_silver.py`, `create_gold.py` | dépôt des compteurs de chaque étape via `record_safely` |
| 4 | `create_silver.py` | **correctif** : le log « maîtrisés » comptait les lignes rattachées à un maître (214 au run du 07/09) au lieu des maîtres distincts (145) ; compteurs désormais tirés des décisions du moteur |
| 5 | `provision/scripts/run_pipeline.sh` | `run_metrics flush` en fin de run, succès comme échec (sortie dans `elt.log`, jamais bloquant) |
| 6 | `engine/governance/pipeline.py`, `app.py` | `GET /pipeline/runs?limit=` (admin, analyst) : runs du plus récent au plus ancien, avec leurs sources |
| 7 | tests | `tests/test_run_metrics.py` (12) ; `tests/test_pipeline_api.py` (+3 : lecture, historique vide, refus viewer) |
| 8 | documentation | `pipeline_elt.md` (section « Historique des runs »), `api.md`, `bases_de_donnees.md` (tables 10 et 11), `ai/dev/suivi_avancement.md` (point 18) |

**Vérifications.** `pytest projet/code-source/tests` : **117 passed** (102 + 15). Un premier passage a révélé un
défaut réel (colonne `run_id` absente de la requête des sources), corrigé. Syntaxe Python 3.8 contrôlée (`ast`,
`feature_version=(3, 8)`) ; `bash -n run_pipeline.sh` OK.
**Non fait / limites :** `schema.sql` non appliqué sur une base ; **aucun run réel enregistré** (VM indisponible) ;
pas d'affichage dans `/dashboard`. Le mémoire et le rapport parlent encore de « neuf tables » pour la base centrale.
Pas de commit.

## 29/09/2026 — Tableau de bord : carte « Historique des runs »

`front-optional/src/lib/api.ts` : types `PipelineRun`, `PipelineRunSource` et appel `getPipelineRuns(limit)`
(`GET /pipeline/runs`). `front-optional/src/app/dashboard/DashboardClient.tsx` : carte « Historique des runs »
(10 derniers runs : début, mode, statut et étape en échec, lignes SILVER, patients maîtres distincts, doublons
exacts / probabilistes, taux, volumes GOLD) ; un clic déplie le détail par source (lignes extraites, lignes non
relues, tables extraites / sautées / en échec, lignes patient en SILVER). L'historique est chargé à part : une base
indisponible affiche un avertissement sans masquer l'état du pipeline ; historique vide → message explicite.

**Vérifications.** `npx tsc --noEmit` : aucune erreur ; ESLint sur les deux fichiers : aucune remarque. Rendu
**non vu à l'écran** (demande l'API, la base et une session connectée). Pas de commit.

## 29/09/2026 — Jeu de données vérifié ; sources CSV précisées comme sources de test

Vérification des CSV du dépôt (`evaluation/synthetic-patient-generator/data/experiments/`) : par niveau (easy,
medium, hard), 404 / 353 / 300 fiches patient (1 057), 792 achats, 519 consultations, 450 examens ; vérité terrain
1 057 lignes, 500 groupes (113 patients dans 1 source, 217 dans 2, 170 dans 3) ; CIN absent 111 / 101 / 80.
Les fichiers du run de référence (76 / 76 / 62) ne sont pas dans le dépôt (générés sur la VM) ; le script actuel
(`ensure_generator_data.sh`, 500 patients) produirait 1 057 fiches.
- `chapters/03-existant-solution.md` et rapport (chap. 3) : les CSV sont des **sources de test**, fictives, qui ne
  représentent pas les sources de production.
- `chapters/07-conception.md` et rapport (chap. 7) : écart entre le jeu du run de référence (214) et le jeu actuel
  (1 057) expliqué.

**À trancher par l'auteur :** MAVIS, MMT_DB et CLINIQUE « ne sont pas dans ses plans et n'ont jamais été utilisés »,
alors que le mémoire, le rapport, le script oral et la slide 9 en font l'existant étudié (le rapport écrit
« 3 sources réelles capturées »). Origine dans le dépôt : `documents/journal_poc_datalake_mavis.md` et les entrées
du 24/08 au 01/09 de ce journal (PoC `datalake_mavis`, retiré le 28/09). L'auteur vérifie avant toute réécriture.
Pas de commit.

## 29/09/2026 — Relecture du mémoire, étape 1/9 : introduction, chapitre 1, remerciements, glossaire

Plan validé : `C:\Users\alpha\.claude\plans\dans-chaque-section-de-snazzy-cupcake.md` (relecture chapitre par
chapitre, pièges vérifiés contre le code). Étape 1 :
- introduction : renvois `[cahier_des_charges.md §n]` → « (cahier des charges, § n) » ; toujours sur une page
  (page 13 du .docx, contrôlé dans Word) ;
- chapitre 1 : « équipe dynamique et passionnée » retiré ; phrase « en donne un exemple » rendue autonome ;
  « trois enjeux » → **quatre** (le tableau en compte quatre) ; notions et tableau 2 sans renvois internes ni
  anglicismes ; décimale française (1,000) ; slogan sur la confidentialité retiré. Paragraphe MAVIS / GNU Health
  **non modifié** (décision en attente de l'auteur) ;
- remerciements : noms au format du rapport (Prénom NOM) ;
- glossaire : DMP retiré (sigle mal défini : en santé, DMP = Dossier Médical Partagé) et sa seule occurrence au
  chapitre 9 remplacée ; définitions ER, EMPI, RBAC, MPI corrigées. Spark (stack technique) laissé, à proposer.
Mots : 1 932 → 1 853. Pas de commit.

## 29/09/2026 — Relecture du mémoire, étape 2/9 : chapitre 2 (état de l'art)

`chapters/02-etat-de-l-art.md` : aucune source, aucun produit ni aucun critère retiré. Pièges corrigés :
« un modèle de langage plante sous Python 3.8 » → c'est `sentence_transformers` ; « RapidFuzz et un dictionnaire
de synonymes » (les synonymes servent au mapping FHIR, pas au rapprochement) ; FHIR « § 8.1.11 » retiré (opération
`$match` de la ressource Patient) ; dates absolues → « consulté en septembre 2026 » / « version 5.0.0 consultée » ;
Splink et Ditto : « selon sa documentation / ses auteurs » ; EMPI « conçu pour les systèmes nord-américains » et
Azure « 27 types d'entités » retirés (non indispensables, difficiles à défendre) ; « quelques centaines de lignes »
→ « un millier de fiches au plus ». Forme : symboles ✔ ◐ ✖ du tableau 11 → oui / partiel / non ; décimales à la
française ; renvois internes `[*.md]` retirés ; légendes raccourcies ; méta-phrases d'ouverture retirées ; liste
« Références citées » supprimée (doublon de la bibliographie). Tableau 5 (grille des 20 axes) déplacé en
**annexe G** (`references/annexes.md`), une phrase le résume ; l'ancienne annexe G devient H (à retirer à
l'étape 9). Glossaire : Spark retiré (validé par l'auteur).
Mots du chapitre : 6 727 → 6 065. Export .docx OK (48 tableaux ; renumérotation prévue en fin de relecture).
Pas de commit.

## 29/09/2026 — Relecture du mémoire, étapes 3 et 4 : chapitres 3 et 4 ; Gantt coloré dans le mémoire

L'auteur, absent environ six heures, a confié la suite (relecture, VM, captures, commits) ; passages MAVIS /
MMT_DB / CLINIQUE toujours laissés en l'état (décision en attente).
- Chapitre 3 (2 784 → 2 504 mots) : « six critères » → **sept** ; API FastAPI « lecture seule » corrigée (elle
  enregistre consentements et planification, réservés à l'administrateur) ; « API Flask pour traiter des volumes
  réels » retiré ; paragraphe redisant la figure 2 fusionné ; « Repères chiffrés » (doublon des chapitres 5 à 8,
  dont « 3/3 sur données réelles ») supprimé ; conclusion et liste de références internes allégées.
- Chapitre 4 (3 741 → 2 864 mots) : rôles sans formules invérifiables (« évalue ce mémoire », « question
  ouverte ») ; encadré sur la taille de l'équipe réduit à la revue de code (phrase sur la « piste d'audit
  consigne / autonomie » retirée) ; « 20 références, aucun chiffre non vérifiable » → 31 références ; contraintes
  reformulées (synonymes = mapping des colonnes) ; budget : **estimation neutre** validée par l'auteur (plus de
  « à remplacer », de renvoi aux rapports de référence, de « non rémunéré » ni de « VM fournie par le
  commanditaire »), trois tableaux fusionnés en un ; manifeste des figures et environnement redondant retirés.
- `scripts/dev/export_memoire_docx.py` : marqueur `{gantt}` dans la légende → cellules ■ / □ / ○ colorées (mêmes
  teintes que le rapport) ; rendu contrôlé sur PDF (page 45).
Pas de commit à ce stade (commit groupé ci-après).

## 30/09/2026 — VM relancée : runs réels, base centrale alimentée, défauts de données corrigés, captures

Travail autonome confié par l'auteur. **Données synthétiques uniquement.**

**Environnement.**
- VM démarrée (`vagrant up`). Le NameNode ne redémarrait plus : ses métadonnées étaient dans `/tmp`, vidé à chaque
  redémarrage (contenu du lac perdu, reconstruit par le pipeline). Correctif : `hadoop.tmp.dir=/home/vagrant/hadoop-data`
  (VM et `provision/bootstrap.sh`), `hdfs namenode -format`, puis HDFS, YARN, metastore Hive et HiveServer2 démarrés.
- `api-venv` de la VM : `pandas`, `pyyaml`, `python-dotenv` et `psycopg` absents ; sans pandas, le moteur n'était pas
  importable et l'étape SILVER aurait sauté la déduplication en silence. Installés (compatibles Python 3.8).
- Base centrale de **test** : instance PostgreSQL temporaire (binaires Laragon) sur le port 5433, dans le dossier
  temporaire de session, sans mot de passe, écoutant sur `localhost` et `192.168.56.1` ; aucun secret versionné.
- Données de test : jeu « difficile » du générateur copié dans `data/raw/` (non versionné) pour pouvoir mesurer le run.

**Code (constats du run → correctifs).**
- `provision/scripts/utils/central_db.py` (nouveau) : **le pipeline consolidé n'écrivait jamais les patients maîtres
  en base** (seul l'ancien MVP le faisait) ; l'étape SILVER charge désormais `master_patient` et
  `patient_identity_map` (idempotent, jamais bloquant). Tests : `tests/test_central_db.py` (6).
- `gen_extract_raw.py` : les dates de naissance mélangent quatre formats ; seul le format dominant était lu,
  **~20 % des dates devenaient vides**. Lecture valeur par valeur (4 formats, `MM/dd/yyyy` exclu car ambigu).
- `create_silver.py` : la source consultation porte le nom en deux colonnes ; le mapping FHIR n'en gardait qu'une
  (**noms tronqués**). Reconstitution `full_name` = prénom + nom. Le genre SILVER est aussi transmis au moteur.
- `pipeline_state.py` : heures des runs avec fuseau (la VM est en UTC, l'hôte en UTC+3 : la base décalait de 3 h).
- `evaluation/evaluate_pipeline_run.py` (nouveau) : évalue le run du pipeline complet sur la vérité terrain.
- `tests/test_watermark.py` : ne suppose plus l'absence du fichier réel `watermark.json`.
- `scripts/dev/export_memoire_docx.py` : insertion de captures (`![](chemin)` + légende Figure N) ; annexes lues
  pour la liste des figures. Interface : « Patients maîtresses » → « Patients maîtres ».

**Résultats mesurés.**

| Run | Mode | Données | Résultat |
|---|---|---|---|
| 20260929T203418 | complet | jeu généré (moyen), avant correctifs | 1 057 fiches SILVER, 767 patients maîtres, 290 doublons (282 exacts, 8 probabilistes), GOLD 1 761 événements |
| 20260929T204439 | complet | jeu difficile, après correctifs | 1 057 fiches, **803** patients maîtres, 254 doublons (245 / 9), 24,03 % ; durée 2 min 56 s |
| 20260929T204829 | reprise | inchangé | **6 tables sur 6 sautées** (empreinte identique) : incrémental validé sur la VM ; durée faussée par une mise en veille de l'hôte |

Évaluation du run complet sur la vérité terrain (jeu difficile) : **précision 1,000, rappel 0,424, F1 0,595**,
803 patients maîtres — le moteur seul donnait 1,000 / 0,422 / 0,594 et 804 : la chaîne Big Data ne dégrade plus
la déduplication. Table GOLD des événements : **1 761 lignes** (vide au run du 07/09). Seed de gouvernance exécuté :
3 comptes d'API, 2 409 consentements (803 × 3 finalités) ; `patient_consent_gold` porte désormais finalité et accord.
Contrôle d'accès vérifié **sur base peuplée** : 422 (finalité absente ou inconnue), 401 (sans clé), 403 (rôle),
403 + motif en audit (finalité refusée), liste « analytics » : 294 renvoyés, 509 écartés et journalisés.
Captures réelles : C04, C07, C09, C10, C11 (`documents/captures/`). `pytest` : 123 passed.

## 30/09/2026 — Relecture du mémoire, étapes 5 à 9 : chapitres 5 à 9, annexes, tableaux et figures

Relecture critique poursuivie, en intégrant les faits établis sur la VM le 29–30/09 (entrée précédente).
- **Pièges corrigés.** Ch. 5 : un fichier absent « interrompt le lot » (faux : l'extraction consigne et continue) ;
  « aucune donnée sans consentement n'atteint GOLD » (faux : le contrôle est à l'API) ; CU5 et CU8 contradictoires
  (403 pour la fiche, liste filtrée) ; paramètres `q` / `limit` → `search` / `page_size` ; identity map traduite
  « carte d'identité ». Ch. 6 : figure 5 corrigée (plus de flèche SILVER → PostgreSQL ; flux moteur → base et base
  → GOLD exacts depuis le chargement central) et redessinée à la verticale (2,8 pt → 12,7 pt) ; `explanation`
  n'est pas une colonne SILVER. Ch. 7 : `fuzz.ratio` présenté comme insensible à l'ordre (faux) ; critère C1
  « éliminatoire » mais pondéré (reformulé) ; `difflib` présenté comme Levenshtein ; « driver-side … d'où la
  montée en charge » nuancé ; `spark/session.py` (absent du dépôt) retiré ; explication douteuse du caractère
  invisible retirée. Ch. 8 : précision « plancher » → estimation **optimiste** (raisonnement inversé) ; référence
  PoC « 10 669 patients / 5 000 masters » (non vérifiable) retirée. Ch. 9 : gain de rappel attribué au CIN « dans
  le blocking » → clé exacte ; « les deux derniers points » ne désignait pas les bonnes lignes ; risque du hachage
  sans sel nuancé (clés aléatoires de 64 caractères) ; consentement par type de dossier ajouté aux limites et
  perspectives.
- **Faits nouveaux intégrés** : runs du 29–30/09 (tableau des runs réels au § 7.3.2), évaluation du pipeline
  complet (P 1,000 / R 0,424 / F1 0,595), base centrale alimentée (test), 123 tests, trois incidents découverts
  sur la VM (tableau des difficultés), limites mises à jour (événements GOLD et consentements n'y figurent plus ;
  cron non exécuté, base de test seulement).
- **Annexes** : A (journal), B (onze tables), D (phrase cassée et contradictoire réécrite), F (fichier de vérité
  terrain corrigé) ; annexe « questions anticipées du jury » retirée ; **nouvelle annexe H : neuf captures**
  (figures 10 à 18). Export : images `![](chemin)` + légende.
- **Forme** : décimales françaises, `masters` → patients maîtres, renvois internes et listes de références de fin
  de chapitre supprimés, légendes raccourcies, auto-labels « honnête » retirés.
- **Numérotation** : 47 tableaux renumérotés dans l'ordre de lecture, renvois compris, aucun orphelin (script).
  Figures 3, 4, 5, 6 et 9 re-rendues ; les autres PNG inchangés.
Mots (ch. 5 à 9) : 13 245 → 12 804 (ch. 5 : 2 714 → 2 646 ; ch. 6 : 928 → 928 ; ch. 7 : 5 131 → 4 927 ;
ch. 8 : 2 221 → 2 103 ; ch. 9 : 2 251 → 2 200). Export : 100 pages, 18 figures, 47 tableaux.

## 30/09/2026 — Soutenance : script oral et deck alignés sur les résultats réels

- `documents/soutenance_script_oral.md` : « c'est un plancher » → estimation **optimiste** (erreurs simulées) ;
  S15 et S17 sur le run du 29/09 (1 057 fiches, 803 patients, 254 doublons, 24 %, 123 tests) ; S16 ajoute
  l'évaluation du pipeline complet (précision 1,000, rappel 0,424) ; S18 : limites à jour (cron non activé, base
  de test) ; « choses à ne pas dire » mises à jour. 1 608 mots pour 16 min 30 (compte par script).
- Deck : slides 15, 17, 18 et 19 (texte des runs uniquement, formes et animations inchangées) ; notes de
  l'orateur régénérées depuis le script. Rendu PowerPoint contrôlé (slides 15, 18, 19). Copie du deck avant
  modification dans le dossier temporaire.

## 30/09/2026 — Rapport de stage et Résumés alignés ; erreur de rappel corrigée dans le Résumé du mémoire

- `export_memoire_docx.py` (Résumé et Abstract du mémoire) : **erreur corrigée** — le rappel annoncé sur le jeu
  facile était 0,578 alors que l'évaluation donne 1,000 (chapitre 8) ; chiffres du run du 29/09 (1 057 fiches,
  803 patients) à la place du jeu de 214 fiches.
- `documents/rapport_stage_source.md` : mêmes corrections que le mémoire (CU1, CU4, CU5, `fuzz.ratio` sensible à
  l'ordre, précision « plancher » → optimiste, livrable base centrale, risques, ENF, tests 123), tableau des runs
  réels, trois incidents du 30/09, limites et conclusion à jour, capture C14 réintégrée ; « 3 sources réelles
  capturées » (inexact) → « 3 sources de test ; extraction PostgreSQL et SQLite implémentée ».
- Rapport régénéré : 69 pages, 14 957 mots, captures C04, C07, C09, C10, C11, C12, C14, C15, C16 insérées ; C01
  (schéma MAVIS) en attente de la décision de l'auteur. `documents/captures/README.md` à jour.

## 30/09/2026 — Nettoyage de `documents/` : trois documents périmés retirés

- Inventaire : les autres fichiers sont des entrées ou sorties de scripts (`icon/` → `figures/logos/` par
  `build_logos.py`, 24/24 ; `figures/` ↔ `manifest.json`, 9 figures ; `captures/` ↔ son README ; `image/` et
  gabarit `references/*.docx` lus par les générateurs du rapport et du deck) : conservés.
- Retirés (non référencés hors historique de `suivi_avancement.md`, chiffres antérieurs aux runs du 29-30/09 :
  102 tests au lieu de 123, 32 % de doublons au lieu de 24 %) :
  `documents/rapport_stage.md` (remplacé par `rapport_stage_source.md` → docx),
  `documents/slides_soutenance.md` (esquisse 13 slides, remplacée par le deck 20 slides + `soutenance_script_oral.md`),
  `documents/etat_avancement_superieur.md` (point du 28/09 pour le supérieur). Récupérables dans l'historique Git.
- `README.md` : ligne `documents/` et « Documents clés » complétées (rapport de stage, soutenance).
- Non traités, laissés à la décision de l'auteur : `references/V2soutenance_m2_hasina.pptx` (7 Mo, versionné)
  et le dossier vide `documents/articles/` (encore cité par `ai/memoire/methode.md`).

## 30/09/2026 — Redémarrage des services après redémarrage du PC ; jeu « facile » de 12 000 patients

- Services relancés : base PostgreSQL de test (port 5433, données conservées : 803 patients maîtres, 5 runs),
  VM (`vagrant up`), HDFS, YARN, metastore Hive, HiveServer2, API Flask (5000, `mocked: false`), API de gouvernance
  (8000), interface web (3000). **HDFS a conservé le lac après redémarrage** (`/datalake/raw|silver|gold`
  présents) : le correctif `hadoop.tmp.dir` hors de `/tmp` est validé.
- Demande de l'auteur : générer 12 000 patients, niveau facile. La commande par défaut
  (`experiment_builder`) réécrit les trois jeux de référence (500 patients) cités dans le mémoire : appel direct de
  `build_experiment('easy', …)` vers `data/experiments_12000/easy/` (non versionné, graine 42), en 54 s.
  Résultat : 12 000 patients maîtres, **25 587 fiches** (pharmacy 9 765, consultation 8 543, imaging 7 279),
  transactions 19 488 achats, 12 762 consultations, 10 891 examens ; patients présents dans 1 / 2 / 3 sources :
  2 541 / 5 331 / 4 128 ; vérité terrain `ground_truth/identity_mapping.csv` et `master_patients.csv`.

## 30/09/2026 — Pipeline complet sur le jeu « facile » de 12 000 patients ; évaluation sur vérité terrain

- Entrée : `data/experiments_12000/easy/{pharmacy,consultation,imaging}/*.csv` copiés dans `data/raw/<source>/`
  (remplace le jeu difficile ; `data/` non versionné). Base centrale : PostgreSQL de test (port 5433).
- `evaluation/evaluate_pipeline_run.py` : option `--truth <identity_mapping.csv>` pour évaluer un jeu hors des
  trois jeux de référence (`--level` inchangé par défaut).
- **Run 20260930T063345 (complet) : échec** à `create_silver`. Cause : blocage des processeurs virtuels de la VM
  (noyau : `soft lockup - CPU#2 stuck for 119s`, `rcu_sched self-detected stall`), JVM Spark sans heartbeat
  (127 s > 120 s) puis perdue (`Answer from Java side is empty`). Pas d'OOM dans la VM ; hôte : ~2 Go de RAM
  libre sur 16 (VM 8 Go, serveur Next.js ~1 Go). La déduplication et le chargement de la base centrale avaient
  abouti avant la perte de la JVM. Run enregistré `failed` dans `pipeline_run` (historique conservé).
- Next.js arrêté pendant le run (≈ 3 Go libres), relancé ensuite.
- **Run 20260930T065246 (complet) : succès**, 06:52:46 → 07:08:01 (UTC VM), **15 min 15 s**. Un nouveau
  heartbeat manqué (217 s) toléré. Extraction sans perte : pharmacy 29 253 lignes (9 765 + 19 488),
  consultation 21 305 (8 543 + 12 762), imaging 18 170 (7 279 + 10 891). SILVER 25 587 fiches → **12 000
  patients maîtres**, 13 587 doublons (tous exacts, 0 probabiliste), 53,10 % ; GOLD : 43 141 événements
  (= somme des transactions), 2 409 consentements.
- Évaluation (`evaluate_pipeline_run.py --truth …/experiments_12000/easy/ground_truth/identity_mapping.csv`) :
  25 587 / 25 587 fiches retrouvées, 12 000 patients maîtres (vérité 12 000), VP 17 715, FP 0, FN 0,
  **précision 1,000, rappel 1,000, F1 1,000** (jeu facile : aucune variation de saisie).
- API Flask : sa session Spark avait disparu pendant le blocage (réponses `mocked: true`) ; redémarrée,
  `mocked: false`, mêmes chiffres (25 587 / 12 000 / 53,1 %).
- **Constat 1 — passage à l'échelle du moteur** : l'étape SILVER dure ≈ 13 min 50 s, presque entièrement dans
  `engine/identity/matcher.deduplicate`. Mesure hôte, moteur seul, même jeu : `matcher` 887 s, `spark_dedup`
  244 s, décisions identiques (P = R = F1 = 1,000). Cause : la passe exacte de `matcher` (l. 127-134) parcourt
  **tous** les patients maîtres pour chaque fiche en recalculant `matching_key` (coût quadratique, ≈ 25 587 ×
  12 000) ; l'index de blocage ne sert qu'à la passe probabiliste. `spark_dedup` a le même défaut, atténué
  (`exact_birth_cin`, `representative` : parcours linéaires). Correctif possible à sémantique identique :
  dictionnaires `matching_key → premier indice` et `(naissance, CIN) → premier indice`. **Non appliqué** (moteur
  cœur du mémoire) : en attente de décision de l'auteur.
- **Constat 2 — identifiants de patients maîtres non stables** : `PAT-0001…` sont des numéros de session (ordre
  de traitement). Après ce run, `PAT-0001` désigne une autre personne qu'avant ; les 2 409 consentements de test
  (créés pour les 803 patients maîtres du jeu difficile) sont donc rattachés à d'autres personnes (données
  fictives, sans conséquence ici). Limite absente du mémoire ; à décider par l'auteur (identifiant persistant
  repris de la base centrale, ou mention en limite).

## 30/09/2026 — Passe exacte du moteur en coût constant ; limite des identifiants non permanents

- Accord de l'auteur sur les deux constats de l'entrée précédente.
- `engine/identity/matcher.py` : `_MasterIndex.exact()` (dictionnaires `matching_key → premier indice` et
  `(naissance, CIN) → premier indice`) remplace le parcours de tous les patients maîtres.
  `engine/identity/spark_dedup.py` : `exact_birth_cin` et `representative` par dictionnaire. Sémantique
  inchangée (premier patient maître dans l'ordre de création).
- Preuve d'identité : décisions (fiche → patient maître, méthode) enregistrées avec la version commitée
  (copie `git archive HEAD`) puis avec la version corrigée, sur easy / medium / hard (500 patients) et sur le
  jeu de 12 000, pour `matcher` et `spark_dedup` : **8 comparaisons sur 8 identiques**. `pytest` 123/123.
- Temps du moteur seul (hôte, 25 587 fiches) : `matcher` 887 s → **12,8 s** ; `spark_dedup` 244 s → 28,7 s.
- Run VM 20260930T074237 (complet, jeu de 12 000, moteur corrigé) : **4 min 57 s** (contre 15 min 15 s), dont
  environ 3 min de gel de la VM (`rcu_sched self-detected stall` à 07:46:59, entre SILVER et GOLD) ; SILVER
  (Spark + moteur + base centrale) en 42 s. Évaluation inchangée : 12 000 patients maîtres, P = R = F1 = 1,000.
- Mémoire : tableau 41 (onzième incident), § 7.3.2 (run sur 12 000 patients), ch9 (« Onze incidents », limite
  « Identifiants de patients maîtres non permanents », volume démontré 25 587 fiches, perspective 2
  « identifiants permanents », perspectives renumérotées 1 à 10), ch2 (volume), ch5 (performance). Rapport :
  mêmes points. `documents/documentation/deduplication.md` et `pipeline_elt.md` complétés.

## 30/09/2026 — Question de l'auteur : durée, millions de lignes, puissance de la VM ; run orphelin corrigé

- Analyse (code + runs du 30/09) : la **durée** ne fait pas échouer un run (aucune limite de temps) ; l'échec
  du run 20260930T063345 vient d'un gel de la VM. Avec des **millions de lignes**, le goulot est la conception
  de SILVER : `create_silver.py` rapatrie toutes les fiches sur un processus (`collect()`), puis le moteur
  Python les traite une par une, sur toutes les fiches à chaque run ; incrémental à la table seulement. Spark
  tourne en `local[*]` (un processus de 2 Go ; `executor_memory` sans effet ; YARN non utilisé). Mesure :
  0,9 Ko par fiche dans le moteur (25 587 fiches) ; 195 seaux de préfixe, 61 patients maîtres par seau en
  moyenne à 12 000 patients.
- Choix de l'auteur : corriger le **run orphelin** et mesurer **100 000 patients**.
- Run orphelin : `pipeline_state` enregistre `pid` (`begin --pid $$`) et `boot_id` ; `is_orphan`,
  `reconcile`, `effective_status` (+ CLI) ; `run_pipeline.sh --resume` utilise le statut effectif ;
  `scheduler.check()` appelle `reconcile_orphan_run()` avant le contrôle anti-double-run. État sans PID
  (ancien format) : comportement inchangé. `os.kill(pid, 0)` limité à POSIX (sous Windows il enverrait un
  Ctrl+C). Tests : +7 (`test_pipeline_state.py` 6, `test_schedule_logic.py` 1) ; `pytest` **130/130**.
  Vérification VM sur un fichier d'état temporaire : PID inexistant → statut effectif `failed`,
  `--resume --dry-run` repart de `gen_extract_raw` (index 1), `reconcile` marque l'échec avec son motif ; PID
  vivant → `running`.
- Jeu de 100 000 patients généré (graine 42, 41 s) dans `data/experiments_100000/easy/` : **212 523 fiches**
  (pharmacy 80 809, consultation 70 951, imaging 60 763), 359 299 transactions (achats 162 026, consultations
  106 339, examens 90 934).
- `documents/documentation/pipeline_elt.md` : pièges 13 (Spark en local) et 14 (run orphelin).

## 30/09/2026 — Test de charge à 100 000 patients ; premières fusions à tort ; mémoire corrigé sur l'échelle

- Moteur seul sur l'hôte (`matcher`, 212 523 fiches) : chargement 66,7 s, **déduplication 331,5 s** (contre
  12,8 s pour 25 587 fiches : 8,3 fois plus de fiches, 26 fois plus de temps), pic mémoire du processus 407 Mo ;
  seaux de préfixe : 205, 488 patients maîtres en moyenne (61,5 à 12 000), plus gros 2 266.
- Run VM **20260930T082016** (complet, Next.js arrêté) : **réussi en 7 min 03 s**. Extraction 571 822 lignes
  (pharmacy 242 835, consultation 177 290, imaging 151 697 : fiches + transactions, aucune perte) ; SILVER
  212 523 → 99 998 patients maîtres (112 520 exacts, 5 probabilistes), 52,95 % ; GOLD 359 299 événements,
  2 409 consentements ; moteur dans la VM ≈ 5 min (08:21:26 → 08:26:29) ; pic 4,8 Go utilisés sur 7,9 ;
  trois gels de la VM (08:22:47, 08:24:15 avec `soft lockup` de 65 s, 08:25:58) traversés sans échec. API Flask :
  `mocked: false`, mêmes chiffres.
- Évaluation (`evaluate_pipeline_run.py --truth …/experiments_100000/…`) : VP 146 186, **FP 13**, FN 0 ;
  précision 0,99991, rappel 1,000. **Premières fusions à tort** : deux paires d'homonymes parfaits (même nom,
  même date de naissance) fusionnées par la passe probabiliste, score 0,80 = seuil (nom 0,5 + date 0,3) :
  « Georges Grenier » (CIN différents : 106867407 / 106388848) et « Émile Marty » (CIN absent d'un côté, villes
  différentes). Les 5 décisions probabilistes du run sont exactement ces fusions. Données fictives.
- Simulation d'un **veto CIN** (deux CIN non vides différents interdisent la fusion ; fonction de score
  remplacée en mémoire, moteur non modifié) : easy / medium / hard / 12 000 inchangés (mêmes VP, FP, FN) ;
  100 000 : 9 paires à tort au lieu de 13 (« Georges Grenier » évité). Veto « ville différente » : aucun effet
  sur nos jeux, mais le générateur ne varie pas les villes (non concluant, non retenu). **Veto non appliqué** :
  décision de l'auteur.
- Mémoire : ch2 (volume 212 523), ch4 (Spark en mode local, gels), ch5 (performance 7 min 03 s ; déduplication
  sur une machine), ch6 (YARN non utilisé, mode local, 2 Go), ch7 (§ 7.2.3 déduplication sur une machine,
  tableau 40, run de 100 000 patients), ch8 (« aucune paire à tort sur les trois niveaux » ; paragraphe
  « Premières fusions à tort »), ch9 (limites « Environnement de démonstration », « Déduplication centralisée,
  recalculée à chaque run », « Reprise par étape », « Précision : estimation optimiste » réécrite ;
  perspective 4 + veto et validation humaine ; perspective 7 réécrite). Résumé et abstract nuancés
  (`export_memoire_docx.py`). Rapport : mêmes points. Script oral : réponse « Pourquoi Spark » corrigée,
  3 questions ajoutées, conclusion nuancée ; notes de S19 du deck corrigées.
- Exports : mémoire (47 tableaux, 18 figures, résumé 227 mots) ; rapport 71 pages. `pytest` 130/130.
- État laissé : `data/raw/` contient le jeu de 100 000 patients ; base de test : 99 998 patients maîtres
  (anciens numéros réattribués). Retour au jeu difficile de la démonstration : à décider par l'auteur.

## 30/09/2026 — Règle d'identité stricte (v2), exécutée dans Spark ; identifiants dérivés de la clé

- Demande de l'auteur : « le CIN, genre, birthday, ville d'origine doivent être exactement pareils, pas de
  probabilité ». Choix (questions) : sans CIN des deux côtés, nom identique en plus ; score supprimé ; règle
  dans Spark ; mémoire en « évolution mesurée » ; identifiant de patient maître dérivé de la clé.
- Simulation préalable (lecture seule) puis moteur v2 sur l'hôte (`evaluate_engine.py`) :
  easy P 1,000 R 1,000 (500 maîtres) ; medium P 1,000 R 0,824 (589) ; hard P 1,000 R **0,179** (942 ;
  VP 130, FN 597) ; 12 000 : P = R = 1,000 ; **100 000 : 100 000 maîtres, FP 0** (v1 : 13). La baisse de
  rappel vient des dates et villes effacées par le générateur (jeu difficile) : une valeur manquante n'est
  jamais identique.
- Code : `engine/identity/rules.py` (clé, `master_id` = `PAT-` + 20 hexa de SHA-256 de la clé, ou HMAC si
  `PATIENT_ID_SECRET` ; explications) ; `matcher.deduplicate(patients)` réécrit (référence Python, sans
  score) ; `spark_dedup.deduplicate_df` en vrai Spark (UDF appelant `from_dict` + `rules`, `row_number` par
  clé, aucun `collect()`) ; `config/deduplication.yaml` et `engine/identity/config.py` supprimés ;
  `matching_key` retiré. `create_silver.py` : décisions par Spark, compteurs agrégés
  (`run_metrics.summarize_counts`), base centrale en flux (`central_db.load_central_db_rows`,
  `toLocalIterator`, lots de 5 000) ; `PYTHONPATH` et `PYSPARK_PYTHON` des processus UDF fixés.
  `evaluate_engine.py` (option `--dir`, variante Spark retirée de l'hôte) ; `evaluate_pipeline_run.py
  --parity` ; `evaluation_truth.md` régénéré (hard). README du code mis à jour.
- Tests : hôte **131** réussis (`test_matcher.py` réécrit : 10 cas ; `test_central_db.py` +2 ;
  `test_run_metrics.py` +1 ; `test_spark_dedup.py` ignoré sans PySpark). VM : `pytest` installé dans
  `api-venv` (8.3.5) ; `test_spark_dedup.py` + `test_matcher.py` : 11 réussis (parité Spark = Python).
- Nouvelles bases de test (PostgreSQL 5433) : `patient_platform_scale`, `patient_platform_demo` ; l'ancienne
  `patient_platform` est conservée intacte (historique, consentements, audit).
- Run VM **20260930T091617** (100 000 patients → `scale`) : **2 min 48 s** (v1 : 7 min 03 s) ; SILVER ≈ 1 min 30
  (base centrale comprise) ; 100 000 maîtres, 112 523 rattachements ; pic VM 4,46 Go ; aucun gel. Évaluation :
  FP 0, R 1,000 ; **parité : 212 523 fiches, 0 différence** d'identifiant entre Spark et la référence.
- Run VM **20260930T092111** (jeu difficile → `demo`, `data/raw/` remis sur le jeu difficile) : 1 min 30 s ;
  942 maîtres, 115 rattachements ; P 1,000, R 0,179 ; parité 1 057 fiches, 0 différence.

## 30/09/2026 — Démonstration sur la base `patient_platform_demo` ; deux défauts d'API corrigés ; captures v2

- `seed_governance` sur `patient_platform_demo` : 3 utilisateurs, 942 × 3 = 2 826 consentements. Clés dans le
  scratchpad (`seed_output_demo.txt`) et `front-optional/.env` (non versionné) ; FastAPI relancé sur `demo`.
  Run `--from create_gold` (20260930T092710) : consentements GOLD 2 826.
- **Défaut 1 — `/metrics` (FastAPI) en erreur 500** : la requête lisait `master_patient.is_duplicate`, colonne
  absente de `sql/schema.sql` (et de l'ancienne base) ; l'endpoint n'avait donc jamais fonctionné sur une base
  réelle (le test simulait la base). Corrigé : fiches et doublons lus dans `patient_identity_map`
  (`total_patients`, `total_masters`, `duplicates`, `duplicate_rate`) ; test adapté. Vérifié : 1 057 / 942 /
  115 / 10,88 %.
- **Défaut 2 — API Flask retombée sur le mock après un run** : sa session Spark gardait la liste des fichiers
  de `patient_consent_gold` réécrite par le pipeline (`SparkFileNotFoundException`). Corrigé : `refresh(table)`
  (`spark.catalog.refreshTable`) avant chaque lecture. Vérifié : consentements réels (`mocked: false`).
- Contrôle d'accès rejoué sur `demo` : 401 / 422 / 422 / 403 (rôle) / 200 (395 patients, analytics) / 403
  (finalité refusée, motif en audit) / 200 (fiche à 3 fiches source).
- Front : sous-titre de `/synthese` (« règle d'identité stricte »). Captures refaites : C04, C07, C09, C12, C14,
  C15 (131 réussis, 1 ignoré), C16 (évaluation + parité). Première tentative web ratée (connexion non
  terminée au bout de 4 s) : attente explicite de la sortie de `/login`.

## 30/09/2026 — Mémoire, rapport, soutenance et documentation : règle stricte (v2) en « évolution mesurée »

- Principe retenu avec l'auteur : la v1 (voie exacte + score pondéré, seuil 0,80) est présentée comme
  première version, résultats conservés en comparaison ; la v2 (règle stricte, 30/09) est le moteur actuel.
  État de l'art du ch2 inchangé, sauf les phrases énonçant le choix du projet.
- Mémoire : résumé et abstract ; ch1 (objectif 3) ; ch2 (blocking, `$match`, arbitrages, EM, maintenance) ;
  ch3 (figure 1, contrat « aucune valeur devinée », périmètre, réponse 2) ; ch4 (paramètres, contraintes,
  volumétrie) ; ch5 (F3, CU3, qualité : scalabilité, maintenance, fiabilité 76 tests, `/doublons`) ; ch6
  (tableau 29, figure 5) ; ch7 (figure 6, révision de l'arbitrage 4, arborescence sans `config/`, clé
  d'identité, § 7.2.3 v1 → v2 avec tableau 36 renommé « score de la v1 », Spark sans `collect()`, runs v2,
  tableau 40 réécrit, 12e incident « homonymes », familles) ; ch8 (figure 9 et tableau 42 : 55 + 76 = 131
  tests, tableau 44 v1 / v2 avec la ligne 100 000 patients, lecture, pipeline v2, homonymes → v2, décomposition,
  cas de référence du PoC, limites) ; ch9 (bilan, arbitrages dont « règle stricte », « CIN au cœur de la
  clé », « identifiant dérivé de la clé », démonstrations, 12 incidents, limites : rappel 0,179, identifiant
  dérivé, précision optimiste, déduplication recalculée ; perspectives 2, 4, 7) ; annexes (C, figures 15, 17,
  18) ; glossaire (+ HMAC, UDF). Figures re-rendues : 1, 5, 6, 9 (3, 4, 7, 8 remises à leur version
  commitée). Export : 47 tableaux, 18 figures, résumé 222 mots.
- Rapport : mêmes points ; extraits X04 (`rules.py::identity_key,master_id`) et X06 régénérés ; 72 pages.
- Script oral : S13, S15, S16, S17, S18 et questions du jury ; tableau du débit recompté avec une seule
  méthode (1 501 mots ; l'ancien décompte de 1 608 n'était pas reproductible). Deck : S13 (cases égales,
  trait de seuil retiré, exemple des homonymes), S15, S16 (données du graphique et étiquettes figées
  régénérées), S17, S18 et notes ; vérifié par export PNG (PowerPoint).
- Documentation : `deduplication.md` (section 0 « règle en vigueur », v1 en historique, implémentation,
  tests), `evaluation.md` (résultats v2 sur 5 jeux, v1 en historique, options), `architecture.md`,
  `bases_de_donnees.md`, `api.md` (`/metrics`), README des captures (X04).
- Non modifiable ici : la vidéo de démonstration (S17), si elle a déjà été enregistrée avec les anciens
  chiffres.

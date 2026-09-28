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

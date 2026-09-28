# Chapitre 6 — Réalisation

> **Statut** : rédigé (08/09/2026, actualisé 27/09/2026)

## Objectif

Restituer l'implémentation effective de la plateforme : générateur de données avec
vérité terrain, pipeline ELT Medallion en 5 étapes (exécution reprise et
planifiée), moteur de déduplication (Pandas + Spark), chargement PostgreSQL,
gouvernance et API, puis difficultés rencontrées sur la VM et leur résolution.

---

## 6.1 Générateur de données et vérité terrain

Le générateur
[`synthetic-patient-generator`](../projet/code-source/evaluation/synthetic-patient-generator)
est implémenté en 7 étapes, déterministe (seed 42) :

**Tableau 27 — Les six modules du générateur synthétique et le rôle réel de chacun.**

| Module | Rôle réalisé |
|---|---|
| `patient_generator.py` | 500 patients maîtres + `master_patients.csv` (vérité absolue) |
| `distribution_engine.py` | plan de distribution 0.8 / 0.7 / 0.6 → 3 sources |
| `variation_engine.py` | injection d'erreurs easy 10 % / medium 30 % / hard 50 % |
| `pharmacy/consultation/imaging_generator.py` | fichiers patients + transactions |
| `identity_mapping.py` | `identity_mapping.csv` : source → source_patient_id → ground_truth_id |
| `experiment_builder.py` | datasets easy / medium / hard |

Types de variations réels : casse, espaces, inversion prénom/nom, abréviation,
typo (suppression/duplication/permutation), formats CIN (espacé / compact) et
dates (ISO, DD/MM/YYYY…), valeurs manquantes (naissance ou ville de naissance).
Résultat pour le dataset hard :
**1 057 enregistrements, 500 groupes de vérité, répartition 404 / 353 / 300**, et
792 achats / 519 consultations / 450 examens. Le CIN est porté par ~75 % des
maîtres, stable entre les sources (autoritatif). Le fichier de vérité est **réservé à
l'évaluation** — jamais fourni à l'algorithme [deduplication.md — règle métier].

Le déterminisme n'est pas un détail d'implémentation : c'est ce qui rend l'évaluation
**comparable**. Les trois jeux easy / medium / hard sont produits à partir des
**mêmes 500 maîtres** (`--seed 42`) et ne diffèrent que par le **taux de variation**
appliqué (10 % / 30 % / 50 %). La dégradation de la qualité est ainsi attribuable à
un seul facteur, et deux exécutions sont comparables ligne à ligne — condition
nécessaire pour établir la parité Pandas/Spark (ch. 7) et pour rejouer une
évaluation après un changement de poids. Les tables de transactions (792 achats,
519 consultations, 450 examens sur le jeu hard) alimentent les entités FHIR autres
que `patient` : c'est leur rattachement au patient qui fait la dette
`patient_events_gold` du chapitre 7.

## 6.2 Pipeline ELT Medallion en 5 étapes

Orchestration par `run_pipeline.sh` (arrêt sur erreur, logs `elt.log`) : le run
de référence du 07/09/2026 est **4/4 vert** sur la VM ; l'orchestration compte
désormais **cinq étapes**, l'ajout de `ensure_generator_data` étant préparatoire
et sans effet quand les sources existent [contexte_projet.md].

```mermaid
flowchart LR
    DS[data_sources.json] --> I[1/5 ensure_generator_data<br/>sources de démo régénérées si absentes seed 42]
    I --> R[2/5 gen_extract_raw<br/>parquet HDFS + tables Hive externes]
    R --> M[3/5 gen_fhir_mapping<br/>fhir_mapping.json]
    M --> S[4/5 create_silver<br/>4 tables FHIR + dédup moteur]
    S --> G[5/5 create_gold<br/>patient_events_gold + patient_consent_gold]
    R -. "extract_raw_report.json" .-> M
```

> **Figure 7 — Le pipeline ELT en cinq étapes, de la préparation des sources au
> chargement GOLD, piloté par `data_sources.json` et contrôlé par `extract_raw_report.json`.**
> L'étape 1/5 est préparatoire : si les fichiers de démonstration existent déjà,
> elle ne ré-écrit rien (idempotence).

**Tableau 28 — Les cinq étapes du pipeline ELT, le script qui les exécute et la sortie réellement produite.**

| Étape | Script | Sortie réelle |
|---|---|---|
| **1 — Préparation (préparatoire)** | `ensure_generator_data.sh` | régénère les CSV synthétiques (seed 42) s'ils sont absents ; sans effet sinon |
| **2 — Extraction RAW** | `gen_extract_raw.py` | parquet `/datalake/raw/{source}/{table}`, tables Hive externes, `extract_raw_report.json` |
| **3 — Mapping FHIR** | `gen_fhir_mapping.py` | `fhir_mapping.json` (table→entité FHIR, cartes explicites) |
| **4 — SILVER FHIR** | `create_silver.py` | `datalake_silver.{patient,encounter,condition,observation}_fhir` |
| **5 — GOLD** | `create_gold.py` | `patient_events_gold` (8 tranches d'âge), `patient_consent_gold` |

Chaque étape est un programme distinct plutôt qu'une fonction d'un programme
unique : une étape qui échoue ne laisse pas la zone suivante dans un état
intermédiaire, ce qui est la condition pour que le pipeline reste **relançable**
et **rejouable**.

### 6.2.1 Reprise de run et ingestion incrémentale (watermark)

Le cahier des charges ajoute une exigence : **pas de retraitement en boucle**.
Deux mécanismes la réalisent [cahier_des_charges.md §4.1] :

- **Reprise de run** — l'état de chaque exécution (identifiant `run_id`, statut
  `running` / `ok` / `failed`, statut par étape) est persisté dans
  `provision/metadata/pipeline_state.json`. En mode `resume`, un run échoué
  repart de la **première étape non terminée** au lieu de tout rejouer ; un run
  `running` **verrouille** tout lancement concurrent (le planificateur ne lance
  pas de doublon).
- **Watermark anti-retraitement** — chaque source de type CSV conserve une
  empreinte (SHA-256 + taille + `mtime`) dans `provision/metadata/watermark.json`.
  À un nouveau run, une table dont l'empreinte n'a pas changé est **sautée** ;
  le rapport d'extraction est reconstruit pour que le pipeline côté aval reste
  strictement identique. Priorité de décision : `ingest.mode` de la source
  (`full`) > mode du pipeline (`full` / `since`) > comparaison d'empreinte —
  l'ordre garantit qu'on rejoue **par choix**, jamais par oubli.

`run_pipeline.sh` combine les deux : `--resume` (reprise), `--full` (purge et
tout rejouer), `--since YYYY-MM-DD` (ré-extraction forcée à partir d'une date),
`--from <étape>` (repartir d'une étape nommée) et `--dry-run` (afficher le plan
sans rien exécuter ni écrire).

### 6.2.2 Planification automatique (scheduler cron)

Le lancement régulier est confié au crontab de la VM, qui vérifie **chaque
minute** `python -m provision.scripts.scheduler.scheduler --check`
[`cahier_des_charges.md` §4.1]. Le pipeline n'est lancé que si :

1. la planification est **active** (`enabled: true` dans `provision/config/schedule.yaml`,
   fichier runtime gitignoré, template committé `schedule.example.yaml`) ;
2. l'**échéance** (fréquence `daily` / `weekly` / `monthly`, heure fixe fuseau VM)
   vient d'être atteinte et n'a pas déjà été déclenchée (état persisté dans
   `scheduler_runs.json`) ;
3. **aucun run** n'est en cours (`pipeline_state.json` pas à `running`).

Le lancement se fait en arrière-plan (`start_new_session`) : le cron revient
aussitôt, le pipeline continue indépendamment et met à jour son propre état. La
même planification est lisible et modifiable par l'API `/pipeline/schedule` (§ 6.5),
dans un format identique à celui attendu par le cron de la VM.

> **Honnêteté d'exécution.** La mécanique (scheduler, watermark, reprise) est
> **écrite et testée** (chapitre 7), mais la VM étant indisponible sur le poste de
> préparation, **aucune exécution réelle planifiée d'un run incrémental n'a encore
> été rejouée sur la VM** : c'est une re-validation en attente, assumée en § 7.5
> et § 8.4.

Résultats du run de référence (sources CSV synthétiques, 214 enregistrements) :
**`datalake_silver.patient_fhir` = 214 lignes** (76 + 76 + 62) ; **145 masters** ;
**69 doublons liés** (`is_duplicate`), tous `match_method = exact` ; `duplicate_rate`
**32.24 %** ; `patient_consent_gold` = **145** lignes. `patient_events_gold` reste à
**0 ligne** en intermédiaire (jointures FHIR non rattachées — dette identifiée au
chapitre 7).

L'étape 3 intègre la **fusion des doublons dans le Data Lake** : le moteur relit
`patient_fhir`, réapplique `deduplicate()` et enrichit chaque ligne des colonnes
`master_patient_id`, `match_method`, `match_score` et `is_duplicate` — la fusion
reste explicable *dans* le lac, pas seulement dans un script séparé.

Le passage **214 → 145** est le contrôle de cohérence le plus utile du run : 214
enregistrements, 69 doublons liés, 145 masters, et `214 − 69 = 145` se vérifie par un
simple comptage sur le lac, sans consulter la logique de fusion — c'est la
correspondance « un master = un enregistrement non dupliqué » qui est testée, pas la
décision elle-même. Le taux de 32.24 % est ce même rapport exprimé en pourcentage,
et `patient_consent_gold` aligne **145 lignes sur 145 masters**. Le tableau reste
néanmoins asymétrique et le dit explicitement : `patient_events_gold` est vide, donc
la zone GOLD ne certifie pour l'instant que **l'identité**, pas les événements de
soin rattachés.

## 6.3 Moteur de déduplication : Pandas et Spark

Le moteur `engine/identity/` est la pièce centrale, deux implantations alignées :

**Tableau 29 — Les deux implantations du moteur côte à côte : la sémantique est alignée, seule la mécanique change.**

| Aspect | `matcher.py` (Pandas) | `spark_dedup.py` (PySpark driver-side) |
|---|---|---|
| Canonique | `canonical.py` (`map_patient`, `from_dict`) | réutilise `matcher`/`canonical` |
| Exact | `matching_key` + naissance/CIN | clusters par `groupBy` de la clé |
| Probabiliste | `_MasterIndex` (3 buckets) | `_BoundedMasterIndex` sur ancres de clusters |
| Score | `fuzz.ratio(nom)×0.5 + naissance×0.3 + CIN×0.1 + ville×0.1` | identique |
| Décision | `exact` / `probabilistic` / `new_master`, seuil 0.80 | identique |
| Sortie | `MatchDecision` | dicts `(master_patient_id, method, score, explanation)` |

La **sémantique est strictement alignée** et la **parité est vérifiée** : démo 18
patients → 11 masters identiques Pandas et Spark, et évaluation ground-truth
« modes MVP+Spark identiques » (TP=307, FP=0, FN=420 pour les deux)
[`evaluation_truth.md`] — voir chapitre 7.

Cette parité n'est pas une coïncidence de développement mais une **propriété
structurelle** : les deux implantations partagent le même `canonical.py`, lisent les
**mêmes poids et le même seuil** dans `config/deduplication.yaml`, et ne diffèrent que
par la **stratégie de regroupement**. Le matcher Pandas indexe les masters sur trois
critères de blocage (préfixe de nom normalisé, date de naissance, CIN) pour borner les
comparaisons ; l'implantation Spark regroupe d'abord les enregistrements par clé
exacte (`groupBy`), puis ne compare que les **ancres de clusters** — un choix assumé
pour la montée en charge, au prix d'une comparaison moins exhaustive. Le protocole de
test rejoue les deux chemins sur le même jeu et compare les décisions méthode par
méthode : c'est le seul moyen de détecter une dérive entre les deux
implémentations, qu'aucune des deux ne peut détecter seule.

## 6.4 Chargement PostgreSQL et GOLD du consentement

- **Chargement central** : le schéma (`sql/schema.sql`) est créé de façon
  **idempotente** (`CREATE TABLE IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`,
  `ON CONFLICT`) — le pipeline est rejouable sans état résiduel.
- **`patient_consent_gold`** : l'étape GOLD joint le PostgreSQL central (table
  `consent`, via `psycopg`) aux masters SILVER ; si la base est inaccessible, le
  schéma est créé vide et l'API bascule en mode `mock` — le consentement reste un
  composant formel de l'architecture.

## 6.5 Gouvernance et API

L'API d'indicateurs du warehouse (Flask, port 5000) expose **2 endpoints** de
gouvernance (`/api/governance/duplicates` sur la table SILVER `patient_fhir`,
`/api/governance/consent` sur la table GOLD `patient_consent_gold`), avec une
réponse unifiée portant l'indicateur **`mocked`** (vrai uniquement en secours
backend, jamais côté frontend). `test_api.py` couvre les 2 endpoints (+ la limite
`limit` du consentement) et retourne **3/3 PASS** en données réelles
[contexte_projet.md].

La gouvernance est implémentée dans le moteur : `auth.py` (authentification par
clé hachée SHA-256 + rôles `admin`/`analyst`/`viewer`), `consent.py` (router FastAPI
`/consent`, décision *purpose-by-purpose*), `audit.py` (middleware journalisant
chaque requête, refus compris). Les **payloads RAW ne sont jamais exposés** par
l'API — seuls les maîtres consolidés le sont [consentement_gouvernance.md §7].

**API plateforme (FastAPI, port 8000).** Au-delà des patients et de l'audit, l'API
expose la planification et l'état du pipeline : `GET /pipeline/schedule` (lecture
admin/analyst), `PUT /pipeline/schedule` (écriture **admin** uniquement, validation
stricte ; format identique à celui attendu par le cron de la VM) et
`GET /pipeline/status` (plan, prochain run, sources suivies par watermark, zones
RAW/SILVER/GOLD, état du dernier run) [`engine/governance/app.py`]. Les endpoints
`/patients` et `/patients/{id}` ont été enrichis : recherche plein texte,
pagination, et **filtrage silencieux** — un master sans consentement pour la
finalité demandée est retiré de la réponse, et le nombre d'exclusions est
journalisé (§ 5.5).

**Frontend `front-optional/` (Next.js, hôte Windows).** Trois pages de pilotage sont
réalisées : `/pipeline` (statut en badges texte), `/dashboard` (vue d'exploitation
visuelle de `GET /pipeline/status` : zones Medallion, étapes du run, fraîcheur des
sources, planification et dernier déclenchements cron) et `/patients` +
`/patients/{id}` (recherche, pagination, fiche d'identité, identity map et badges
de consentement par finalité). L'accès est contrôlé par JWT avec les rôles
**ADMIN** et **MEDECIN** (frontend), et `purpose` reste un paramètre obligatoire.
Cette interface de pilotage est distinguée au § 1.5 des **dashboards d'analyse**
du PoC (visualisation_app), hors périmètre.

Il faut distinguer deux couches qui portent le même mot « gouvernance » sans avoir le
même rôle. L'API **Flask** est une surface de *consommation et de reporting* : ses
endpoints lisent le GOLD et en rendent des agrégats ; `/api/governance/consent` en
particulier **liste** les consentements et leurs statistiques, mais **n'impose
rien** — ni authentification, ni contrôle de finalité. L'API **FastAPI** du moteur est
le seul point d'**application** de la règle : c'est là que se produisent les 401 (clé
inconnue), 403 (rôle insuffisant ou finalité non consentie) et 422 (`purpose`
obligatoire), chacun journalisé par `audit.py`. Cette frontière est assumée et
documentée : l'API Flask reste une dette — lancée avec `debug=True`, elle rend en outre
le nom du patient dans sa réponse de consentement — et le contrôle de consentement
s'applique à l'API de gouvernance, comme le rappelle `ai/dev/suivi_avancement.md`.

## 6.6 Difficultés rencontrées et résolutions

**Tableau 30 — Les sept difficultés réellement rencontrées, leur cause et le correctif testé.**

| Problème réel | Cause | Correctif |
|---|---|---|
| SILVER explosait à **11 614 lignes** | `patient_uuid` capturé par le mapping FHIR dynamique → `source_patient_id` NULL → jointure **76×76** du moteur | `patient_uuid` **exclu** du mapping dynamique + colonne source utilisée une seule fois |
| Listing périmé (overwrite+append par source) | écritures répétées dans la boucle source | accumulation par entité, **une seule écriture `overwrite` par table** ; phase 5 en table temp puis `DROP` + `RENAME TO` |
| Parquet corrompu sur partage vboxsf | warehouse Spark écrit sur le montage partagé | `spark.sql.warehouse.dir = hdfs://localhost:9000/...` (toujours HDFS) |
| Spark ne démarrait pas | `JAVA_HOME` avec `\bin` en trop | normalisation `_resolve_java_home()` dans `spark/session.py` |
| HiveServer2/beeline instable sur la VM | service HS2 fragile | validation des comptages par **scripts Spark** (`check_data.py`) |
| NLP lourd inutilisable | `sentence_transformers` crash Python 3.8 | RapidFuzz + dictionnaire de synonymes (`fhir_synonyms.py`) |
| `gen_extract_raw` ne passait pas `py_compile` | caractère insécable dans sa docstring, interprété comme fin de fichier | docstring corrigée, script recompilé (aucun drapeau d'encodage requis) |

Ces sept incidents se répartissent en trois familles, et la famille conditionne le
correctif. Les **données** (les deux premières lignes) produisent les correctifs les
plus structurés : ils sont documentés dans `pipeline_elt.md` comme des pièges
anti-régression, avec le symptôme, la cause et la parade, précisément parce qu'ils
se reproduisent. L'**infrastructure** (parquet sur partage, démarrage de Spark,
HiveServer2 instable) impose des choix de configuration qui n'ont pas à être
justifiés fonction par fonction : la règle retenue est de **contourner** — écrire
toujours sur HDFS plutôt que sur le partage vboxsf, valider les comptages par scripts
Spark plutôt que par beeline. L'**outillage** (NLP trop lourd) est le seul cas où le
correctif change la méthode : l'approche par vecteurs a été abandonnée pour un score
pondéré et un dictionnaire de synonymes, arbitrage dicté par la contrainte Python
3.8 et rendu lisible par l'exigence d'explicabilité.

Environnement d'exécution: VM `ubuntu/focal64` 8 Go / 4 cœurs — Hadoop 3.3.6,
Hive 3.1.3 (métastore distant 9083 pour éviter le conflit Derby), Spark 3.4.2,
Java 8 ; Spark configuré `executor 4g / driver 2g / shuffle.partitions=8`
[Vagrantfile, bootstrap.sh].

## Conclusion et transition

La plateforme est réalisée et opérationnelle : pipeline ELT en 5 étapes (4/4 au
run de référence, reprise et watermark implémentées, planification cron intégrée),
dédup enregistrée dans le lac, API gouvernance 3/3, gouvernance mécanisée et
interface de pilotage (API et frontend) enrichie. Reste à **démontrer la qualité** :
le chapitre 7 présente la stratégie de test, l'évaluation ground-truth (P/R/F1) et
les limites honnêtes du prototype (rappel « hard », GOLD incomplet, re-validation
VM de la planification en attente).

### Références

- `provision/scripts/ELT/*` + `run_pipeline.sh` ; `provision/api/hive_api.py`,
  `mock_data.py`, `test_api.py`.
- `engine/identity/{canonical,matcher,spark_dedup}.py` ; `engine/governance/{auth,consent,audit,app,pipeline}.py`.
- `provision/scripts/utils/{pipeline_state,watermark,schedule_logic}.py` ;
  `provision/scripts/scheduler/scheduler.py` ; `provision/config/schedule.example.yaml`.
- `sql/schema.sql` ; `ai/memoire/contexte_projet.md` (run 07/09/2026).
- `documents/documentation/pipeline_elt.md` (pièges anti-régression).
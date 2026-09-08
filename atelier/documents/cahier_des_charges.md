# Cahier des Charges — Plateforme de centralisation et de gouvernance des données patients

| Champ | Valeur |
|---|---|
| **Session** | Sep-2026 |
| **Parcours** | Master MBDS |
| **Thème de stage** | Conception d'une plateforme Big Data de gestion et de gouvernance des données patients : nettoyage, déduplication et contrôle d'accès basé sur le consentement du patient |
| **Société** | Madagascar Medical Technology (MMT) |
| **Stagiaire** | 1 |
| **Type de projet** | Nouveau — fusion de 2 PoC (`datalake_mavis` + `test_bigdata`) |

---

## 1. Contexte et problématique

Les établissements de santé utilisent plusieurs systèmes d'information indépendants (consultations,
pharmacies, laboratoires, imagerie, dossiers médicaux), avec des structures, formats et identifiants
différents. Un même patient peut donc être enregistré plusieurs fois, sous des formes différentes :

```text
Pharmacie     → Jean Rakoto
Consultation  → Rakoto Jean
Imagerie      → J. RAKOTO
```

Les données sont dispersées, non standardisées, non dédupliquées et non gouvernées. Ceci entraîne des
risques d'erreurs médicales, des difficultés d'analyse et des failles de confidentialité.

> **Problématique :** comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et
> centraliser des données patients issues de sources hétérogènes, tout en assurant la traçabilité des
> identités et la gouvernance des accès basée sur le consentement du patient ?

## 2. Principe général

Approche progressive : **résoudre d'abord le problème métier**, puis introduire les technologies Big
Data uniquement lorsque le besoin de passage à l'échelle le justifie.

```text
PROBLÈME MÉTIER → MVP FONCTIONNEL → VALIDATION DES ALGORITHMES → PASSAGE À L'ÉCHELLE → ARCHITECTURE BIG DATA
```

Le présent dépôt **`data_lake_final`** est la fusion des deux projets :

| Projet source | Apport |
|---|---|
| `datalake_mavis/` | Architecture Big Data complète : VM Hadoop/Hive/Spark, pipeline ELT Medallion (RAW→SILVER→GOLD), mapping FHIR, API Flask, frontend Next.js |
| `Mon_Memoire/projet/code-source/` (ex `test_bigdata`) | Déduplication exacte + probabiliste (master patient, identity map), consentement + audit + clés API, générateur de données + évaluation ground-truth |

## 3. Objectifs du projet

1. **Centraliser** des données médicales hétérogènes dans une architecture Big Data (Medallion).
2. **Nettoyer et standardiser** selon un modèle commun : modèle canonique (`CanonicalPatient`) côté
   déduplication, schéma pivot **FHIR** côté pipeline ELT.
3. **Dédupliquer intelligemment** : matching exact puis probabiliste, master patient, identity map,
   **logique toujours explicable** (score + méthode + seuil).
4. **Gouverner les accès** : rôles (RBAC), **consentement purpose-by-purpose**, audit d'accès, clés API.
5. **Visualiser** les données (dashboard RMA) et les indicateurs de gouvernance — frontend considéré
   **optionnel** (l'essentiel du stage porte sur les concepts Big Data et le consentement).
6. **Évaluer** la déduplication sur données synthétiques avec vérité terrain (précision / rappel / F1).

## 4. Périmètre fonctionnel

### 4.1 Pipeline ELT Big Data (RAW → SILVER → GOLD)

| Étape | Script | Entrée → Sortie |
|---|---|---|
| 1/4 Extraction RAW | `provision/scripts/ELT/gen_extract_raw.py` | `data_sources.json` → Parquet HDFS + tables Hive externes + `extract_raw_report.json` |
| 2/4 Mapping FHIR | `provision/scripts/ELT/gen_fhir_mapping.py` | `extract_raw_report.json` → `fhir_mapping.json` (RapidFuzz + synonymes) |
| 3/4 Silver | `provision/scripts/ELT/create_silver.py` | RAW + mapping → `datalake_silver.*_fhir` (4 entités, genre normalisé, doublons) |
| 4/4 Gold | `provision/scripts/ELT/create_gold.py` | 4 tables Silver → `datalake_gold.patient_events_gold` |

Orchestration : `bash provision/scripts/run_pipeline.sh` (arrêt sur erreur), logs `provision/logs/elt.log`,
suivi `sync_metadata.json` (UTC+3).

### 4.2 Déduplication (moteur `engine/`)

- Modèle canonique `CanonicalPatient` (source, id source, nom, naissance, tél, adresse, genre).
- Nettoyage/standardisation : casse, accents, téléphones, dates, genre.
- **Exact matching** puis **probabilistic matching** (scoring RapidFuzz) avec **blocking** (candidats
  partageant préfixe nom / date / tél).
- Score pondéré : nom 0.5 · naissance 0.3 · tél 0.2 — seuil **0.80**.
- Sorties : `master_patient`, `patient_identity_map` (source_system → source_patient_id → master_patient_id,
  avec `matching_method` et `matching_score`).
- Implémentation en **Pandas** et en **PySpark** (driver-side, strictement identiques).
- Les doublons sont également flaggés dans la zone SILVER (`is_duplicate`).

### 4.3 Gouvernance et consentement

| Composant | Description | État |
|---|---|---|
| RBAC | Rôles ADMIN / MEDECIN (JWT + checkRole côté frontend ; rôles `admin`/`analyst`/`viewer` côté plateforme) | Livré |
| Consentement | Table `consent`, purpose-by-purpose, liée au `master_patient_id` | Livré |
| Audit d'accès | Table `access_audit` — qui, quoi, quand, autorisé/refusé | Livré |
| Clés API | Hachées SHA-256 (jamais stockées en clair) | Livré |
| Page governance frontend | Indicateurs doublons, qualité, consentements, accès | À créer (optionnel) |

### 4.4 Backend API

- **API données (Flask + PySpark + Hive)** sur GOLD : endpoints `/rma/*` et `/api/rma/*` (mocks backend si GOLD sparse).
- **API plateforme (lecture seule)** : `/health`, `/metrics`, `/patients`, `/patients/{master_patient_id}`, `/audit`, `/consent` — payloads RAW jamais exposés.

### 4.5 Frontend (optionnel)

- `front-optional/` : Next.js (dashboard KPI, 5 pages RMA D3.js, gestion utilisateurs, settings).
- Conservé tel que `visualisation_app/` du projet Mavis, sans effort supplémentaire.

## 5. Architecture technique

```
Sources (PostgreSQL / SQLite / CSV synthétiques)
        │
        ▼
[RAW Zone] ──> [SILVER Zone · FHIR] ──> [GOLD Zone] ──> [API Flask] ──> [Web/visualisation]
(HDFS/Parquet)  (Hive 4 entités)         (Hive agrégé)    (port 5000)      (optionnel)
        └──────────────┐
        engine/ (déduplication exact + probabiliste · Pandas / Spark)
                       │
                       ▼
        PostgreSQL central : master_patient · patient_identity_map · raw_patient_record
                            consent · api_user · access_audit
```

| Couche | Technologie | Rôle |
|---|---|---|
| Big Data | Hadoop HDFS 3.3.6 · Hive 3.1.3 · Spark 3.4.2 (Java 8) | Data Lake + warehouse + traitement distribué |
| Pipeline | PySpark, RapidFuzz | ELT Medallion, mapping FHIR, déduplication |
| Moteur dédup | Python (Pandas + PySpark), RapidFuzz | Master patient + identity map + évaluation |
| Base centrale | PostgreSQL | Master patient, consentement, audit, clés API |
| API | Flask (données) + FastAPI (gouvernance) | Exposition REST |
| Frontend | Next.js 15 + D3.js (optionnel) | Visualisation |
| Infra | Vagrant/VirtualBox Ubuntu 20.04 (8 Go) | VM reproductible (`bootstrap.sh`) |

> **Choix clés :** mapping FHIR avec RapidFuzz + synonymes (jamais de modèle NLP lourd — crash Python 3.8) ;
> warehouse Spark toujours sur HDFS (`hdfs://localhost:9000/...`) et jamais sur le montage vboxsf ;
> écritures Hive : première source `overwrite`, suivantes `append`.

## 6. Sources de données

| Source | Base | Connexion | Tables extraites |
|---|---|---|---|
| MAVIS | mavis_notheme | SSH tunnel (102.16.7.154:8090) + JDBC (ou réplique locale Laragon `rebuild_mavis_db.py`, 73 090 lignes) | 11 tables (hms_patient, res_partner, hms_diseases…) |
| MMT_DB | mmt_db | PostgreSQL local hôte (192.168.56.1:5432) | 3 tables (gnuhealth_patient, party_party, gnuhealth_family) — base synthétique recréée (~60 271 lignes) |
| CLINIQUE | clinique.db | SQLite local | 4 tables FHIR (54 582 lignes) |
| Plateforme dédup | CSV synthétiques | `synthetic-patient-generator` (easy / medium / hard, seed reproductible) | pharmacy, consultation, imaging |

> `provision/config/data_sources.json` contient des identifiants et n'est **jamais commité**.
> Modèle : `data_sources.example.json`. Mots de passe surchargeables par variables d'environnement.

## 7. Modèles de données

### 7.1 Modèle canonique (déduplication)

```text
CanonicalPatient : source_system · source_patient_id · first_name · last_name · full_name
                   · birth_date · phone · address · gender
```

Normalisation : `" Jean Rakoto " / "JEAN RAKOTO" / "jean rakoto"` → `jean rakoto` ; téléphones,
dates et genre standardisés (`H`/`male`/`Homme` → `M` ; `F`/`female`/`femme` → `F`).

### 7.2 Schéma pivot FHIR (zones SILVER / GOLD)

**SILVER** (`datalake_silver.*_fhir`) :

| Entité | Champs |
|---|---|
| Patient | patient_uuid (SHA-256), source_patient_id, name, birth_date, gender, address, phone, email (+ `is_duplicate`, `_source_table`) |
| Encounter | patient_uuid, encounter_id, admission_date, discharge_date, create_date, visit_type |
| Condition | patient_uuid, diagnosis, diagnosis_code, category, code, info, name |
| Observation | patient_uuid, mortality, parity, gravida, live_births |

**GOLD** (`datalake_gold.patient_events_gold`, 17 colonnes) : patient_uuid, source_patient_id, name,
gender, birth_date, age, age_tranche (8 tranches RMA), encounter_id, admission_date, discharge_date,
visit_type, diagnosis_code, category, diagnosis, mortality, parity, gravida, live_births.

### 7.3 PostgreSQL central (plateforme)

```text
raw_patient_record · master_patient (+ gender) · patient_identity_map · consent · api_user · access_audit
```

(Schéma complet : `projet/code-source/sql/schema.sql`.)

## 8. Évaluations et métriques de succès

| Métrique | Cible | Constat |
|---|---|---|
| Pipeline ELT bout en bout | < 30 min, idempotent | Atteint |
| Précision déduplication | ≥ 0.95 | 1.000 (easy → hard) |
| Rappel déduplication | diagnostic de l'algo (dataset hard) | 0.287 (hard, 50 % de variations — éval. 07/09/2026, `evaluation_truth.md`) |
| F1 déduplication | ≥ 0.80 (easy/medium) | 0.447 (hard) — dataset volontairement dur |
| Normalisation genre | ≥ 95 % | male/female (reste NULL côté MMT_DB selon source) |
| Tests | ≥ 80 % | tests moteur + consentement + API PASS |
| Zéro accès non autorisé | 0 violation | audit + RBAC testés |

## 9. Planning

| Phase | Contenu |
|---|---|
| Niveau 1 (test_bigdata) | MVP Pandas + PostgreSQL : extraction, mapping, nettoyage, déduplication, master patient, dashboard — terminé |
| Niveau 2 (test_bigdata) | PySpark local, résultats strictement identiques au MVP — terminé |
| Niveau 3 (datalake_mavis) | Architecture Big Data complète HDFS + Hive + Spark, pipeline ELT 4 étapes, API Flask, frontend — terminé (~85 %) |
| Fusion `data_lake_final` | Un seul repo autonome : docs consolidées, moteur porté, évaluation ground-truth, consentement GOLD | **en cours** |
| Finalisation | Export VM `.box`, rapport de stage, slides, commit initial git | à venir |

## 10. Livrables

1. Code source complet (repo `data_lake_final`).
2. Pipeline ELT Big Data (provision + scripts PySpark).
3. Moteur de déduplication + évaluation ground-truth.
4. PostgreSQL central (master patient, consentement, audit).
5. API données + API gouvernance.
6. Documentation technique + manuel conceptuel (`documents/`).
7. Frontend optionnel (Next.js).
8. Rapport de stage + slides de soutenance.

## 11. Risques et contraintes

| Contrainte | Impact | Mitigation |
|---|---|---|
| VM 8 Go | Performance Spark | executor 4g / driver 2g, `shuffle.partitions=8` |
| MAVIS distant instable | Blockage pipeline | Sources locales de dev (Laragon, SQLite) |
| Hétérogénéité des sources | Mapping FHIR | Synonymes + RapidFuzz, liens FK à enrichir |
| Données sensibles | Confidentialité | Données **synthétiques** uniquement, RBAC + audit + consentement |
| Mapping incomplet (encounters non reliés aux patients) | GOLD peu alimenté (16 lignes) | Enrichir `fhir_synonyms.py` + `TABLE_OVERRIDE` |
# Chapitre 6 — Architecture du système

## 6.1 Architecture logicielle

### 6.1.1 Une architecture en trois niveaux

L'architecture suit la démarche progressive du § 3.3 : chaque niveau réutilise
la **même logique métier**, seule l'infrastructure d'exécution change.

```mermaid
flowchart TB
    subgraph N1["Niveau 1 — MVP (résoudre le métier)"]
        CSV1[CSV pharmacy / consultation / imaging]
        P1[Pandas : CanonicalPatient + deduplicate]
        PG1[(PostgreSQL central)]
        CSV1 --> P1 --> PG1
    end
    subgraph N2["Niveau 2 — Spark (passer à l'échelle)"]
        P2[PySpark : mêmes algorithmes, parité stricte]
        P2 --> PGish[(résultats identiques MVP)]
    end
    subgraph N3["Niveau 3 — Big Data Medallion (chaîne complète)"]
        RAW[(RAW parquet HDFS)] --> SILVER[(SILVER 4 tables FHIR)]
        SILVER --> GOLD[(GOLD patient_events + consent)]
        SILVER --> ENG[engine/identity : dédup + master_patient_id]
        ENG --> GOLD
    end
    P1 -. "parité vérifiée" .-> P2
    P2 -. "même moteur porté" .-> ENG
```

> **Figure 4 — L'architecture en trois niveaux : le MVP Pandas, la parité PySpark
> vérifiée, puis le Data Lake Medallion RAW → SILVER → GOLD, qui porte le moteur et la
> gouvernance.**

Conception retenue pour chaque brique (cahier des charges, § 4) :

**Tableau 32 — Les briques de la chaîne et leur conception.**

| Brique | Conception |
|---|---|
| **Extraction** | couche d'extraction abstraite (CSV / PostgreSQL / SQLite) → RAW |
| **Normalisation** | modèle canonique `CanonicalPatient` |
| **Interopérabilité** | schéma pivot **FHIR** (4 entités) |
| **Déduplication** | blocking, passe exacte, passe probabiliste (RapidFuzz), seuil 0,80 |
| **Consolidation** | patient maître et table de correspondance traçable |
| **Chargement** | base PostgreSQL centrale, écriture idempotente (`ON CONFLICT`, `IF NOT EXISTS`) |
| **Exposition** | API REST et espace de gouvernance |

### 6.1.2 Chaîne de bout en bout (niveau 3 retenu)

La conception retenue est le **niveau 3** : une seule chaîne, de la source hétérogène à l'API
gouvernée. Le schéma ci-dessous relie les trois zones Medallion, le moteur de déduplication et
la gouvernance ; il sert de référence à la réalisation (§ 7.3).

```mermaid
flowchart LR
    subgraph SRC["Sources"]
        S1["pharmacy CSV"] --- S2["consultation CSV"] --- S3["imaging CSV"]
        S0["MAVIS PG · MMT_DB PG · CLINIQUE SQLite<br/>(sources avancées, optionnelles)"]
    end
    RAW["RAW · parquet HDFS<br/>/datalake/raw/{source}/{table}<br/>tables Hive externes STRING"]
    MAP["gen_fhir_mapping<br/>fhir_mapping.json"]
    SIL["SILVER · datalake_silver<br/>patient / encounter / condition / observation _fhir"]
    DED["Moteur engine/identity<br/>exact + probabiliste · seuil 0,80"]
    GOLD["GOLD · datalake_gold<br/>patient_events_gold · patient_consent_gold"]
    PG[("PostgreSQL central<br/>master_patient · identity_map<br/>consent · api_user · access_audit")]
    API["API REST (Flask 5000)<br/>+ gouvernance FastAPI"]
    S1 & S2 & S3 & S0 --> RAW --> MAP --> SIL --> DED --> GOLD
    DED -- "patients maîtres · correspondances" --> PG
    PG -. "consentements" .-> GOLD
    GOLD --> API
    PG --> API
    API -. "RBAC + consentement + audit" .-> AUD[("access_audit")]
```

> **Figure 5 — Le chemin d'une donnée, de la source à l'API.**

Traçabilité de bout en bout : chaque ligne SILVER conserve sa source (`_source_system`,
`_source_table`), son identifiant d'origine et une empreinte unique (`patient_uuid`), ainsi que
le patient maître, la méthode et le score de la décision. L'explication de chaque décision est
conservée dans la table de correspondance de la base centrale, que l'étape SILVER alimente.

Les deux magasins n'ont pas le même rôle : HDFS, Hive et Spark portent le lac **rejouable** et
ses trois zones de qualité ; PostgreSQL porte l'**état de référence** — patients maîtres,
consentements, journal d'audit, comptes. C'est une séparation de rôles, pas une redondance.

## 6.2 Architecture technique

L'architecture est installée sur **une VM unique** (`ubuntu/focal64`, Vagrant, 8 Go, 4 cœurs) ;
l'ordre de démarrage des services est strict :

**Tableau 33 — Les composants de la VM et leurs ports.**

| Composant | Rôle | Port / chemin |
|---|---|---|
| HDFS NameNode | entrepôt du Data Lake (parquet RAW/SILVER/GOLD) | 9000 — `start-dfs.sh` en premier |
| YARN | exécution des jobs Spark | 8088 — `start-yarn.sh` ensuite |
| Hive Metastore | métadonnées des bases `datalake_*` | 9083 (distant, évite le conflit Derby) |
| HiveServer2 | accès SQL (`beeline`) | 10000 |
| Moteur `engine/` | déduplication + gouvernance (PostgreSQL) | — |
| API données (Flask) | exposition de GOLD | 5000 |
| API gouvernance (FastAPI) | `/health`, `/metrics`, `/patients`, `/audit`, `/consent`, `/pipeline/schedule`, `/pipeline/status`, `/pipeline/runs` | 8000 (hôte Windows) |
| Planificateur ELT | déclenche `run_pipeline.sh` selon `schedule.yaml` (`daily` / `weekly` / `monthly`), échéance vérifiée chaque minute, anti-double-run | cron VM + `provision/scripts/scheduler/scheduler.py` |
| Watermark / état | empreinte des sources (`watermark.json`) pour l'incrémental ; état du run (`pipeline_state.json`) pour la reprise ; compteurs du run (`run_metrics.json`) avant leur enregistrement en base | `provision/metadata/` |
| Frontend Next.js | pages de pilotage et de consultation (§ 5.3.1) : RBAC ADMIN/MEDECIN, `purpose` obligatoire | 3000 (hôte Windows) |

> **Ordre strict :** `start-dfs.sh` → `start-yarn.sh` → metastore (9083) → HiveServer2 (10000) →
> jobs Spark → API. Toute inversion produit des erreurs d'écriture ou de métadonnées (§ 7.3.6).

Versions installées : Hadoop 3.3.6, Hive 3.1.3, Spark 3.4.2 et Java 8. Spark dispose de 4 Go
pour l'exécuteur, 2 Go pour le driver et 8 partitions. Les données HDFS sont stockées hors de
`/tmp`, que la VM vide à chaque redémarrage (§ 7.3.6). Les ports 9870 (interface HDFS), 10000
(Hive) et 5000 (API des indicateurs) sont redirigés vers l'hôte.

## Conclusion et transition

L'architecture fixe deux choses : une **logique métier unique** portée par trois niveaux
d'infrastructure, et une **chaîne de bout en bout** où chaque donnée garde sa trace d'origine et
chaque accès sa trace d'audit. Le chapitre 7 descend d'un niveau : la plate-forme technique, la
structure du code, le modèle de données, les composants et la réalisation de chaque étape.

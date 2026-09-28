# 🏥 Plateforme de Centralisation et de Gouvernance des Données Patients

## 📌 Contexte

Les établissements de santé utilisent souvent plusieurs systèmes d'information indépendants pour gérer différentes activités :

- consultations médicales ;
- pharmacies ;
- laboratoires ;
- services d'imagerie ;
- dossiers médicaux.

Ces systèmes sont généralement indépendants et utilisent des structures de données différentes. Un même patient peut donc être enregistré dans plusieurs systèmes avec :

- des identifiants différents ;
- des noms de tables différents ;
- des noms de colonnes différents ;
- des formats de données différents ;
- des relations métier différentes.

Par exemple, le même patient peut apparaître comme :

```text
Pharmacie     → Jean Rakoto
Consultation  → Rakoto Jean
Imagerie      → J. RAKOTO
```

Le défi consiste à déterminer s'il s'agit réellement du même patient, puis à centraliser ses informations tout en conservant la traçabilité de leur origine.

Ce projet propose donc la conception et le développement d'une **plateforme de centralisation et de gouvernance des données patients**.

---

# 🎯 Objectif du projet

L'objectif principal est de construire une plateforme capable de :

- intégrer des données provenant de sources hétérogènes ;
- gérer des structures de données différentes ;
- mapper les données vers un modèle commun ;
- nettoyer et standardiser les données ;
- détecter les doublons de patients ;
- créer une identité patient unique ;
- préserver les relations entre les patients et leurs données médicales ;
- centraliser les données dans une base PostgreSQL ;
- assurer la traçabilité des données ;
- préparer une gestion du consentement et du contrôle d'accès ;
- permettre une évolution vers une architecture Big Data distribuée.

---

# 🔬 Problématique

> **Comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des données patients provenant de sources hétérogènes, tout en assurant la traçabilité des identités et la gouvernance des accès basée sur le consentement du patient ?**

---

# 💡 Principe général

Le projet suit une approche progressive.

L'objectif n'est pas d'utiliser immédiatement toutes les technologies Big Data.

La priorité est :

```text
1. Résoudre correctement le problème métier
                ↓
2. Construire un MVP fonctionnel
                ↓
3. Valider les algorithmes
                ↓
4. Faire évoluer l'architecture
                ↓
5. Ajouter les technologies Big Data lorsque nécessaire
```

Cette approche permet d'éviter une architecture trop complexe dès le début.

---

# 🚀 Stratégie de développement

Le projet est développé en trois niveaux.

```text
NIVEAU 1
MVP fonctionnel
CSV + Pandas + PostgreSQL
        │
        ▼
NIVEAU 2
Scalabilité
PySpark + traitement distribué
        │
        ▼
NIVEAU 3
Architecture Big Data complète
Data Lake + HDFS + Hive + Spark
```

---

# 🥇 Niveau 1 — MVP rapide

## Objectif

Développer rapidement une solution fonctionnelle avant d'introduire la complexité des technologies Big Data.

Architecture :

```text
                SOURCES CSV

       ┌────────────┬─────────────┬─────────────┐
       │            │             │             │
       ▼            ▼             ▼

    Pharmacie   Consultation   Imagerie

       └────────────┬─────────────┬─────────────┘
                    │
                    ▼
             CSV EXTRACTOR
                    │
                    ▼
              PANDAS DATAFRAME
                    │
                    ▼
             DATA MAPPING
                    │
                    ▼
             DATA CLEANING
                    │
                    ▼
          ENTITY RESOLUTION
                    │
                    ▼
           MASTER PATIENT INDEX
                    │
                    ▼
            POSTGRESQL CENTRAL
                    │
                    ▼
                DASHBOARD
```

---

## Technologies MVP

| Technologie | Rôle |
|---|---|
| Python | Langage principal |
| CSV | Sources initiales |
| Pandas | Manipulation des données |
| RapidFuzz | Similarité et matching |
| PostgreSQL | Base centrale |
| SQLAlchemy | Accès aux bases |
| Streamlit | Dashboard |
| Git | Gestion de versions |

---

# 📂 Sources de données

Pour le MVP, les sources sont représentées par des fichiers CSV.

Cela permet de développer rapidement tout en simulant des systèmes indépendants.

```text
data/
│
├── raw/
│   │
│   ├── pharmacie/
│   │   ├── patients.csv
│   │   └── achats.csv
│   │
│   ├── consultation/
│   │   ├── patients.csv
│   │   └── consultations.csv
│   │
│   └── imagerie/
│       ├── patients.csv
│       └── examens.csv
```

Chaque source possède volontairement une structure différente.

---

# 💊 Source 1 — Pharmacie

## Patients

```text
patients.csv
```

Structure :

| client_id | nom_complet | naissance | telephone | adresse |
|---|---|---|---|---|

## Achats

```text
achats.csv
```

Structure :

| purchase_id | customer_id | medicine_name | quantity | purchase_date |
|---|---|---|---|---|

Relation :

```text
PATIENT
   │
   │ client_id
   ▼
ACHATS
```

---

# 👨‍⚕️ Source 2 — Consultations

## Patients

```text
patients.csv
```

Structure :

| patient_code | prenom | nom | date_naiss | phone_number |
|---|---|---|---|---|

## Consultations

```text
consultations.csv
```

Structure :

| consultation_id | patient_id | diagnostic | consultation_date |
|---|---|---|---|

Relation :

```text
PATIENT
   │
   │ patient_code
   ▼
CONSULTATIONS
```

---

# 🩻 Source 3 — Imagerie

## Patients

```text
patients.csv
```

Structure :

| id_personne | patient_name | dob | tel |
|---|---|---|---|

## Examens

```text
examens.csv
```

Structure :

| exam_id | patient_code | exam_type | exam_date |
|---|---|---|---|

Relation :

```text
PATIENT
   │
   │ id_personne
   ▼
EXAMENS
```

---

# 🔌 Architecture des sources

Les sources doivent être indépendantes du pipeline.

Le pipeline ne doit pas savoir si les données proviennent :

- d'un CSV ;
- de MySQL ;
- de PostgreSQL ;
- de SQLite ;
- d'une API.

Architecture :

```text
                    DATA SOURCES

          ┌───────────┼───────────┐
          │           │           │

         CSV        MySQL      PostgreSQL
          │           │           │
          └───────────┼───────────┘
                      │
                      ▼
              EXTRACTION LAYER
                      │
                      ▼
                 DATAFRAME
                      │
                      ▼
                PIPELINE
```

---

# 🧩 Architecture des Extracteurs

Une abstraction permet de rendre les sources interchangeables.

```text
                 BaseExtractor
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼

    CSVExtractor  MySQLExtractor  PostgresExtractor
         │             │             │
         └─────────────┼─────────────┘
                       │
                       ▼
                  DataFrame
```

Le résultat de chaque extracteur doit être compatible avec le pipeline de transformation.

---

# 🔄 Pipeline de traitement

Le pipeline suit les étapes suivantes :

```text
1. EXTRACTION
        ↓
2. RAW DATA
        ↓
3. DATA MAPPING
        ↓
4. STANDARDISATION
        ↓
5. DATA CLEANING
        ↓
6. VALIDATION
        ↓
7. BLOCKING
        ↓
8. DEDUPLICATION
        ↓
9. MASTER PATIENT INDEX
        ↓
10. IDENTITY MAPPING
        ↓
11. CENTRALISATION
        ↓
12. DATA GOVERNANCE
        ↓
13. VISUALISATION
```

---

# 🗂️ Raw Layer

Les données originales doivent être conservées avant transformation.

```text
SOURCE
   │
   ▼
RAW DATA
   │
   ▼
TRANSFORMATION
```

La zone RAW permet :

- de conserver la donnée originale ;
- d'assurer la traçabilité ;
- de rejouer le pipeline ;
- de corriger les erreurs ;
- de comparer avant/après transformation.

---

# 🔗 Data Mapping

Chaque source possède ses propres noms de colonnes.

| Concept | Pharmacie | Consultation | Imagerie |
|---|---|---|---|
| Identifiant | client_id | patient_code | id_personne |
| Nom | nom_complet | prenom + nom | patient_name |
| Naissance | naissance | date_naiss | dob |
| Téléphone | telephone | phone_number | tel |

Toutes les données doivent être converties vers un modèle commun.

---

# 📐 Modèle Canonique

Après extraction, les données sont transformées vers un modèle standard.

```text
CanonicalPatient

source_system
source_patient_id

first_name
last_name
full_name

birth_date
phone
address
gender
```

Exemple :

```json
{
    "source_system": "pharmacy",
    "source_patient_id": "15",
    "full_name": "Jean Rakoto",
    "birth_date": "1990-01-10",
    "phone": "0341234567"
}
```

Le modèle canonique constitue le contrat entre :

```text
SOURCES
   ↓
TRANSFORMATION
   ↓
DEDUPLICATION
```

---

# 🧹 Data Cleaning

Les données peuvent contenir des incohérences.

Exemple :

```text
" Jean Rakoto "
"JEAN RAKOTO"
"jean rakoto"
```

Après normalisation :

```text
jean rakoto
```

Les opérations comprennent :

- suppression des espaces ;
- uniformisation des majuscules/minuscules ;
- normalisation des accents ;
- standardisation des téléphones ;
- standardisation des dates ;
- traitement des valeurs manquantes ;
- suppression des caractères inutiles.

---

# 🧠 Entity Resolution et Déduplication

La déduplication constitue le cœur intelligent du projet.

Exemple :

```text
PHARMACIE

Jean Rakoto
0341234567
1990-01-10
```

```text
CONSULTATION

Rakoto Jean
+261341234567
10/01/1990
```

```text
IMAGERIE

J. RAKOTO
034 123 4567
1990/01/10
```

La question est :

> S'agit-il du même patient ?

---

## Niveau 1 — Exact Matching

Comparaison exacte d'informations fiables.

Exemples :

```text
Téléphone identique
Email identique
Identifiant national identique
```

---

## Niveau 2 — Fuzzy Matching

Lorsque les informations ne sont pas identiques.

Exemple :

```text
Jean Rakoto
Jean RAKOTO
J Rakoto
Rakoto Jean
```

Une mesure de similarité est calculée.

---

# 📊 Similarity Score

Un score global est calculé.

| Critère | Poids |
|---|---:|
| Nom | 40% |
| Date de naissance | 30% |
| Téléphone | 20% |
| Adresse | 10% |

```text
Score =
Nom × 0.40
+
Date de naissance × 0.30
+
Téléphone × 0.20
+
Adresse × 0.10
```

Décision :

```text
Score >= 90%
        │
        ▼
MATCH AUTOMATIQUE


Score 70% - 90%
        │
        ▼
REVIEW


Score < 70%
        │
        ▼
NO MATCH
```

---

# 🚧 Blocking — Préparation à la scalabilité

Comparer chaque patient avec tous les autres patients est inefficace.

Exemple :

```text
1 000 000 patients

Comparaison complète :

1 000 000 × 1 000 000
```

Le nombre de comparaisons devient énorme.

La technique de **Blocking** consiste à créer des groupes de candidats.

Exemple :

```text
TOUS LES PATIENTS
        │
        ▼
     BLOCKING
        │
   ┌────┼─────┐
   │    │     │
   ▼    ▼     ▼

BLOCK A BLOCK B BLOCK C
   │
   ▼
MATCHING
```

Exemple de règles :

- même année de naissance ;
- première lettre du nom ;
- même zone géographique ;
- préfixe du téléphone.

Le matching est ensuite effectué uniquement entre les candidats d'un même groupe.

Cette approche est particulièrement importante lors du passage à Apache Spark.

---

# 👤 Master Patient Index

Après déduplication, un patient unique est créé.

```text
MASTER PATIENT

ID : 102

Nom : Jean Rakoto
Date de naissance : 1990-01-10
Téléphone : 0341234567
```

Le Master Patient Index représente l'identité centrale du patient.

---

# 🔑 Identity Mapping

Chaque identifiant provenant d'une source est relié au Master Patient.

```text
patient_identity_map

source_system
source_patient_id
master_patient_id
matching_score
matching_method
```

Exemple :

| Source | ID Source | Master ID | Score |
|---|---|---|---:|
| Pharmacie | 15 | 102 | 100% |
| Consultation | 88 | 102 | 95% |
| Imagerie | IMG-20 | 102 | 92% |

Cette table permet de conserver :

- l'origine des données ;
- la traçabilité ;
- les identifiants historiques ;
- les relations métier.

---

# 🗃️ PostgreSQL Central

La base centrale contient :

```text
central_db

├── master_patient
│
├── patient_identity_map
│
├── pharmacy_purchase
│
├── consultation
│
├── imaging_exam
│
├── patient_consent
│
└── audit_log
```

Architecture :

```text
                    MASTER PATIENT
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼

        PHARMACIE     CONSULTATION   IMAGERIE
```

---

# 🔒 Data Governance et Consentement

Le système prévoit une gestion du consentement.

```text
Demande d'accès
       │
       ▼
Vérification du consentement
       │
   ┌───┴────┐
   │        │
   ▼        ▼

AUTORISÉ  REFUSÉ
   │        │
   ▼        ▼

ACCÈS    ACCESS DENIED
```

Exemple :

| Patient | Donnée | Autorisation |
|---|---|---|
| Patient 102 | Consultation | Oui |
| Patient 102 | Pharmacie | Oui |
| Patient 102 | Imagerie | Non |

---

# 🥈 Niveau 2 — Évolution vers Apache Spark

Une fois le MVP fonctionnel, le pipeline peut évoluer vers Apache Spark.

## Pourquoi Spark ?

Spark devient intéressant lorsque :

- le volume de données augmente ;
- les traitements deviennent longs ;
- plusieurs sources doivent être traitées simultanément ;
- les comparaisons de patients deviennent nombreuses ;
- le traitement distribué devient nécessaire.

Architecture :

```text
CSV / DATABASES
       │
       ▼
   APACHE SPARK
       │
       ├── Extraction
       │
       ├── Data Cleaning
       │
       ├── Standardisation
       │
       ├── Blocking
       │
       └── Deduplication
               │
               ▼
       MASTER PATIENT INDEX
               │
               ▼
        POSTGRESQL CENTRAL
```

---

# 🐼 Pandas vs ⚡ Spark

| Critère | Pandas | Apache Spark |
|---|---|---|
| Petit volume | Excellent | Possible mais excessif |
| Prototype rapide | Excellent | Plus complexe |
| Machine unique | Oui | Oui |
| Cluster | Non | Oui |
| Gros volume | Limité par RAM | Très adapté |
| Traitement distribué | Non | Oui |
| MVP | Recommandé | Option |
| Big Data | Limité | Recommandé |

## Stratégie adoptée

```text
MVP
CSV
+
Pandas
        │
        ▼
Validation du pipeline
        │
        ▼
PySpark
        │
        ▼
Scalabilité
```

---

# 🥉 Niveau 3 — Architecture Big Data complète

Lorsque les volumes deviennent importants, une architecture Data Lake peut être introduite.

```text
                         DATA SOURCES

             ┌──────────────┼──────────────┐
             │              │              │

           MySQL       PostgreSQL        APIs
             │              │              │
             └──────────────┼──────────────┘
                            │
                            ▼
                      INGESTION
                            │
                            ▼
                     DATA LAKE
                       HDFS
                            │
            ┌───────────────┼───────────────┐
            │                               │
            ▼                               ▼

       APACHE HIVE                     APACHE SPARK
       SQL ANALYTICS                   DATA PROCESSING
                                             │
                                       Cleaning
                                       Mapping
                                       Blocking
                                       Matching
                                             │
            └───────────────┼───────────────┘
                            │
                            ▼
                      CURATED DATA
                            │
                            ▼
                    MASTER PATIENT
                            │
                            ▼
                   POSTGRESQL CENTRAL
                            │
                            ▼
                      DASHBOARD
```

---

# 🐘 Quand utiliser Hadoop / HDFS ?

HDFS est utile lorsque :

- les données sont très volumineuses ;
- plusieurs machines doivent stocker les données ;
- une architecture distribuée est nécessaire ;
- un Data Lake doit être construit.

Exemple :

```text
Sources
   │
   ▼
HDFS

/raw
/staging
/processed
/curated
```

Pour le MVP initial, HDFS n'est pas nécessaire.

---

# 🐝 Quand utiliser Apache Hive ?

Hive est principalement utilisé pour :

- interroger de grandes quantités de données ;
- utiliser SQL sur un Data Lake ;
- faire des analyses ;
- créer des tables externes sur les données stockées.

Exemple :

```sql
SELECT
    birth_date,
    COUNT(*)
FROM patients
GROUP BY birth_date;
```

Dans ce projet, Hive devient intéressant dans une architecture Big Data complète.

Il n'est pas indispensable au MVP.

---

# 💻 Quand utiliser VirtualBox ?

VirtualBox n'est pas une technologie Big Data.

C'est un logiciel de virtualisation.

Il permet par exemple de créer :

```text
PC Windows
     │
     ▼
VirtualBox
     │
     ▼
Machine virtuelle Ubuntu
     │
     ├── Java
     ├── Hadoop
     ├── Spark
     └── Hive
```

VirtualBox peut être utile pour créer un environnement isolé destiné à tester une architecture Hadoop.

Cependant, il n'est pas recommandé comme point de départ pour ce MVP.

---

# 🐳 Docker comme alternative

Docker peut être utilisé pour simplifier le déploiement.

Exemple :

```text
Docker Compose

├── PostgreSQL
├── Spark
├── Streamlit
└── FastAPI
```

Pour le MVP :

```text
Docker
   │
   ├── PostgreSQL
   ├── Application Python
   └── Streamlit
```

Docker peut être ajouté après le fonctionnement du pipeline principal.

---

# 📊 Dashboard

Le dashboard permet de visualiser les résultats.

Indicateurs :

- nombre de sources ;
- nombre de patients extraits ;
- nombre de patients nettoyés ;
- nombre de doublons détectés ;
- nombre de patients uniques ;
- taux de déduplication ;
- nombre de matchs exacts ;
- nombre de matchs fuzzy ;
- nombre de cas nécessitant une vérification.

Exemple :

```text
┌───────────────────────────────────┐
│ SOURCES                    3      │
├───────────────────────────────────┤
│ PATIENTS EXTRAITS          2 450  │
├───────────────────────────────────┤
│ MATCHS EXACTS                320  │
├───────────────────────────────────┤
│ MATCHS FUZZY                 230  │
├───────────────────────────────────┤
│ PATIENTS UNIQUES           1 900  │
└───────────────────────────────────┘
```

---

# 📁 Structure du projet

```text
patient-data-platform/

├── README.md
├── requirements.txt
├── main.py
│
├── data/
│   │
│   ├── raw/
│   │   ├── pharmacie/
│   │   │   ├── patients.csv
│   │   │   └── achats.csv
│   │   │
│   │   ├── consultation/
│   │   │   ├── patients.csv
│   │   │   └── consultations.csv
│   │   │
│   │   └── imagerie/
│   │       ├── patients.csv
│   │       └── examens.csv
│   │
│   ├── staging/
│   └── processed/
│
├── config/
│   ├── sources.json
│   └── mappings.json
│
├── extractors/
│   ├── base_extractor.py
│   ├── csv_extractor.py
│   ├── mysql_extractor.py
│   ├── postgres_extractor.py
│   └── sqlite_extractor.py
│
├── pipeline/
│   ├── mapper.py
│   ├── cleaner.py
│   ├── validator.py
│   └── orchestrator.py
│
├── deduplication/
│   ├── blocker.py
│   ├── exact_matcher.py
│   ├── fuzzy_matcher.py
│   └── matcher.py
│
├── load/
│   └── postgres_loader.py
│
├── database/
│   └── central_schema.sql
│
├── dashboard/
│   └── app.py
│
├── api/
│   └── main.py
│
└── tests/
```

---

# 📅 Planning de développement — 1 mois

## Semaine 1 — Fondations et sources

### Objectifs

- Création du repository.
- Architecture du projet.
- Création des CSV.
- Génération de données fictives.
- Création volontaire de doublons.
- Configuration PostgreSQL.
- Définition du modèle canonique.

### Livrable

```text
3 sources hétérogènes
+
Base PostgreSQL
+
Architecture du projet
```

---

## Semaine 2 — Pipeline ETL

### Objectifs

- CSV Extractor.
- Data Mapping.
- Standardisation.
- Data Cleaning.
- Validation.
- Zone RAW.
- Zone Staging.

### Livrable

```text
SOURCES
   ↓
EXTRACTION
   ↓
TRANSFORMATION
   ↓
CLEAN DATA
```

---

## Semaine 3 — Entity Resolution

### Objectifs

- Exact Matching.
- Fuzzy Matching.
- Similarity Score.
- Blocking.
- Détection des doublons.
- Master Patient Index.
- Identity Mapping.

### Livrable

```text
PATIENTS SOURCES
       │
       ▼
ENTITY RESOLUTION
       │
       ▼
MASTER PATIENT
```

---

## Semaine 4 — Centralisation et démonstration

### Objectifs

- Chargement PostgreSQL.
- Migration des relations métier.
- Consentement basique.
- Dashboard Streamlit.
- Tests.
- Documentation.
- Préparation soutenance.

### Livrable

```text
MVP COMPLET
ET
DÉMONTRATION FONCTIONNELLE
```

---

# 🔮 Évolutions futures

Après validation du MVP :

## Sources

```text
CSV
 ↓
MySQL
 ↓
PostgreSQL
 ↓
SQLite
 ↓
API REST
```

## Scalabilité

```text
Pandas
   ↓
PySpark
   ↓
Spark Cluster
```

## Data Lake

```text
PostgreSQL Central
       +
HDFS / Object Storage
       +
Hive
```

## Gouvernance

- contrôle d'accès basé sur les rôles ;
- consentement avancé ;
- audit complet ;
- chiffrement des données ;
- anonymisation ;
- pseudonymisation.

---

# 🛠️ Technologies et justification

| Technologie | Utilisation | Niveau |
|---|---|---|
| Python | Pipeline principal | MVP |
| CSV | Simulation des sources | MVP |
| Pandas | Traitement local | MVP |
| RapidFuzz | Similarité | MVP |
| PostgreSQL | Base centrale | MVP |
| Streamlit | Dashboard | MVP |
| Docker | Conteneurisation | Extension |
| PySpark | Scalabilité | Extension |
| HDFS | Data Lake distribué | Évolution |
| Hive | SQL analytique Big Data | Évolution |
| VirtualBox | Environnement virtualisé | Optionnel |

---

# 🎓 Positionnement académique

Le projet adopte une démarche progressive inspirée des pratiques de Data Engineering.

```text
PROBLÈME MÉTIER
       │
       ▼
MVP FONCTIONNEL
       │
       ▼
VALIDATION DES ALGORITHMES
       │
       ▼
PASSAGE À L'ÉCHELLE
       │
       ▼
ARCHITECTURE BIG DATA
```

Le projet ne cherche donc pas à utiliser Hadoop, Hive ou Spark uniquement pour afficher des technologies Big Data.

Chaque technologie est introduite en fonction d'un besoin précis :

| Besoin | Technologie |
|---|---|
| Prototype rapide | Pandas |
| Données hétérogènes | Extractor Layer |
| Déduplication | RapidFuzz / Entity Resolution |
| Passage à l'échelle | Apache Spark |
| Stockage distribué | HDFS |
| SQL analytique sur Data Lake | Hive |
| Environnement isolé | VirtualBox / Docker |

---

# 🎯 MVP final attendu

Le MVP doit démontrer la chaîne complète :

```text
                SOURCES HÉTÉROGÈNES
                     CSV (MVP)
                          │
                          ▼
                    EXTRACTION
                          │
                          ▼
                     RAW DATA
                          │
                          ▼
                    DATA MAPPING
                          │
                          ▼
                  STANDARDISATION
                          │
                          ▼
                   DATA CLEANING
                          │
                          ▼
                      BLOCKING
                          │
                          ▼
                  ENTITY RESOLUTION
                          │
                          ▼
                  MASTER PATIENT INDEX
                          │
                          ▼
                    IDENTITY MAP
                          │
                          ▼
                 POSTGRESQL CENTRAL
                          │
                          ▼
                      DASHBOARD
```

---

# 📌 Conclusion

Ce projet ne consiste pas simplement à déplacer des données vers PostgreSQL.

Il répond à un problème de **Data Integration et Master Data Management appliqué aux données de santé**.

Le MVP est volontairement développé avec une architecture légère :

```text
CSV
+
Python
+
Pandas
+
Entity Resolution
+
PostgreSQL
```

Cette première version permet de valider :

- l'intégration des sources ;
- le modèle canonique ;
- la qualité des données ;
- la déduplication ;
- le Master Patient Index ;
- la centralisation.

L'architecture est ensuite conçue pour évoluer progressivement vers une plateforme Big Data :

```text
Pandas
   ↓
PySpark
   ↓
Data Lake
   ↓
HDFS
   ↓
Hive
   ↓
Architecture distribuée
```

> **Le principe fondamental du projet est de résoudre d'abord correctement le problème métier, puis d'introduire progressivement les technologies Big Data lorsque le besoin de passage à l'échelle le justifie.**
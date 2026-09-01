# 🏥 Plateforme de Centralisation et de Gouvernance des Données Patients

## 📌 Contexte

Les établissements de santé utilisent souvent plusieurs systèmes d'information indépendants pour gérer leurs activités : consultations médicales, pharmacies, laboratoires et services d'imagerie.

Ces systèmes possèdent généralement leurs propres structures de données. Un même patient peut donc être enregistré plusieurs fois avec des identifiants, des noms de colonnes et des formats différents.

Ce projet propose la conception et le développement d'un **MVP (Minimum Viable Product)** permettant d'intégrer, nettoyer, dédupliquer et centraliser les données patients provenant de plusieurs sources hétérogènes vers une base centrale PostgreSQL.

Le MVP utilise initialement des **fichiers CSV** afin d'accélérer le développement. L'architecture est cependant conçue pour permettre le remplacement progressif des fichiers CSV par de véritables bases de données telles que **MySQL, PostgreSQL ou SQLite**, sans modifier le pipeline principal.

---

# 🎯 Objectif du projet

L'objectif principal est de construire une plateforme capable de :

- Lire des données provenant de plusieurs sources.
- Gérer des structures de données différentes.
- Identifier les informations relatives aux patients.
- Transformer les données vers un modèle commun.
- Nettoyer et standardiser les données.
- Détecter les doublons de patients.
- Créer une identité patient unique.
- Préserver les relations entre les patients et leurs données médicales.
- Centraliser les données dans PostgreSQL.
- Assurer la traçabilité des données.
- Prévoir une gestion du consentement et du contrôle d'accès.

---

# 💡 Approche MVP

Afin de développer rapidement un prototype fonctionnel, le projet adopte une approche progressive.

## Phase 1 — MVP avec fichiers CSV

Les différentes sources sont représentées par des fichiers CSV hétérogènes.

```text
CSV Sources
     │
     ▼
Extraction
     │
     ▼
Data Mapping
     │
     ▼
Cleaning
     │
     ▼
Deduplication
     │
     ▼
Master Patient Index
     │
     ▼
PostgreSQL Central
```

Cette approche permet de concentrer le développement sur les problématiques principales :

- intégration de données ;
- hétérogénéité des structures ;
- nettoyage ;
- standardisation ;
- déduplication ;
- centralisation.

---

## Phase 2 — Remplacement progressif par des bases de données

Une fois le pipeline validé avec les CSV, les sources pourront être remplacées progressivement.

```text
                    DATA SOURCES

        ┌─────────────┬──────────────┬──────────────┐
        │             │              │              │
       CSV          MySQL       PostgreSQL       SQLite
        │             │              │              │
        └─────────────┴───────┬──────┴──────────────┘
                              │
                              ▼
                     EXTRACTION LAYER
                              │
                              ▼
                         DATAFRAME
                              │
                              ▼
                      PIPELINE COMMUN
```

Le principe fondamental est que le reste du pipeline ne dépend pas directement du type de source.

---

# 🏗️ Architecture globale

```text
                         DATA SOURCES

       ┌────────────┬─────────────┬─────────────┐
       │            │             │             │
       ▼            ▼             ▼

   CSV / MySQL  CSV/PostgreSQL  CSV/SQLite
   Pharmacie    Consultation     Imagerie

       └────────────┬─────────────┬─────────────┘
                    │
                    ▼
          ┌────────────────────┐
          │ EXTRACTION LAYER   │
          │                    │
          │ CSVExtractor       │
          │ MySQLExtractor     │
          │ PostgresExtractor  │
          │ SQLiteExtractor    │
          └─────────┬──────────┘
                    │
                    ▼
               DATAFRAME
                    │
                    ▼
          ┌────────────────────┐
          │ TRANSFORMATION     │
          │                    │
          │ Data Mapping       │
          │ Standardisation    │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │ DATA CLEANING      │
          │                    │
          │ Normalisation      │
          │ Validation         │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │ ENTITY RESOLUTION  │
          │                    │
          │ Deduplication      │
          │ Similarity Score   │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │ MASTER PATIENT     │
          │ INDEX              │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │ POSTGRESQL CENTRAL │
          │                    │
          │ Patients           │
          │ Consultations      │
          │ Médicaments        │
          │ Imagerie           │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │ DATA GOVERNANCE    │
          │                    │
          │ Consentement       │
          │ Contrôle d'accès   │
          │ Audit              │
          └────────────────────┘
```

---

# 📂 Sources de données

Pour le MVP, trois domaines médicaux sont simulés.

| Source | Domaine | Format initial |
|---|---|---|
| Source 1 | Pharmacie | CSV |
| Source 2 | Consultations | CSV |
| Source 3 | Imagerie | CSV |

Chaque source possède volontairement une structure différente.

---

# 💊 Source 1 — Pharmacie

## Patients

Fichier :

```text
patients_pharmacie.csv
```

Structure :

| client_id | nom_complet | naissance | telephone | adresse |
|---|---|---|---|---|

Exemple :

```text
1,Jean Rakoto,1990-01-10,0341234567,Antananarivo
2,Marie Rasoanaivo,1985-05-20,0329876543,Antananarivo
```

## Achats de médicaments

Fichier :

```text
achats_medicaments.csv
```

Structure :

| purchase_id | customer_id | medicine_name | quantity | purchase_date |
|---|---|---|---|---|

Relation :

```text
patients_pharmacie
        │
        │ client_id
        ▼
achats_medicaments
```

---

# 👨‍⚕️ Source 2 — Consultations

## Patients

Fichier :

```text
patients_consultation.csv
```

Structure :

| patient_code | prenom | nom | date_naiss | phone_number |
|---|---|---|---|---|

Exemple :

```text
50,Jean,Rakoto,10/01/1990,+261341234567
51,Marie,Rasoanaivo,20/05/1985,+261329876543
```

## Consultations

Fichier :

```text
consultations.csv
```

Structure :

| consultation_id | patient_id | diagnostic | consultation_date |
|---|---|---|---|

Relation :

```text
patients_consultation
        │
        │ patient_code
        ▼
consultations
```

---

# 🩻 Source 3 — Imagerie

## Patients

Fichier :

```text
patients_imagerie.csv
```

Structure :

| id_personne | patient_name | dob | tel |
|---|---|---|---|

Exemple :

```text
IMG001,J. Rakoto,1990/01/10,034 123 4567
IMG002,Marie Rasoanaivo,1985/05/20,032 987 6543
```

## Examens

Fichier :

```text
examens.csv
```

Structure :

| exam_id | patient_code | exam_type | exam_date |
|---|---|---|---|

Relation :

```text
patients_imagerie
        │
        │ id_personne
        ▼
examens
```

---

# 🔄 Pipeline de traitement

Le pipeline suit les étapes suivantes :

```text
1. CONNECTER / LIRE LA SOURCE
        ↓
2. EXTRAIRE
        ↓
3. STOCKER RAW
        ↓
4. DATA MAPPING
        ↓
5. STANDARDISER
        ↓
6. NETTOYER
        ↓
7. DÉDUPLIQUER
        ↓
8. CRÉER MASTER PATIENT
        ↓
9. CRÉER IDENTITY MAP
        ↓
10. MIGRER LES DONNÉES LIÉES
        ↓
11. CENTRALISER
        ↓
12. APPLIQUER LA GOUVERNANCE
        ↓
13. VISUALISER
```

---

# 🔌 Architecture des Extracteurs

Le projet utilise une couche d'abstraction afin de rendre les sources interchangeables.

```text
                 BaseExtractor
                       │
          ┌────────────┼────────────┐
          │            │            │
          ▼            ▼            ▼

     CSVExtractor  MySQLExtractor  PostgresExtractor
          │            │            │
          └────────────┼────────────┘
                       │
                       ▼
                  DataFrame
```

Chaque extracteur doit retourner un format commun.

```python
DataFrame Pandas
```

Ainsi, le pipeline de transformation ne dépend pas de la technologie source.

---

# 🧩 Base Extractor

Tous les extracteurs suivent une interface commune.

```python
from abc import ABC, abstractmethod


class BaseExtractor(ABC):

    @abstractmethod
    def extract(self):
        pass
```

---

# 📄 CSV Extractor

Pour le MVP initial :

```python
import pandas as pd
from .base_extractor import BaseExtractor


class CSVExtractor(BaseExtractor):

    def __init__(self, file_path):
        self.file_path = file_path

    def extract(self):
        return pd.read_csv(self.file_path)
```

Utilisation :

```python
extractor = CSVExtractor(
    "data/raw/pharmacie/patients.csv"
)

df = extractor.extract()
```

Sortie :

```text
DataFrame Pandas
```

---

# 🗄️ Migration future vers MySQL

Plus tard, un extracteur MySQL pourra remplacer le CSV.

```python
import pandas as pd
from sqlalchemy import create_engine
from .base_extractor import BaseExtractor


class MySQLExtractor(BaseExtractor):

    def __init__(self, connection_string, table_name):
        self.connection_string = connection_string
        self.table_name = table_name

    def extract(self):

        engine = create_engine(
            self.connection_string
        )

        query = f"SELECT * FROM {self.table_name}"

        return pd.read_sql(
            query,
            engine
        )
```

Le résultat reste identique :

```text
DataFrame Pandas
```

Le pipeline principal ne change donc pas.

---

# ⚙️ Configuration des sources

Les sources sont définies dans un fichier de configuration.

## `config/sources.json`

### Phase CSV

```json
{
    "pharmacy": {
        "type": "csv",
        "patient_source": "data/raw/pharmacie/patients.csv",
        "purchase_source": "data/raw/pharmacie/achats.csv"
    },

    "consultation": {
        "type": "csv",
        "patient_source": "data/raw/consultation/patients.csv",
        "consultation_source": "data/raw/consultation/consultations.csv"
    },

    "imaging": {
        "type": "csv",
        "patient_source": "data/raw/imagerie/patients.csv",
        "exam_source": "data/raw/imagerie/examens.csv"
    }
}
```

Plus tard, une source pourra être remplacée par une base de données :

```json
{
    "pharmacy": {
        "type": "mysql",
        "connection": "mysql+pymysql://user:password@localhost/pharmacy_db",
        "patient_table": "pharmacy_customers",
        "purchase_table": "medicine_purchases"
    }
}
```

---

# 🔗 Data Mapping

Les différentes sources utilisent des noms de colonnes différents.

| Concept | Pharmacie | Consultation | Imagerie |
|---|---|---|---|
| ID | client_id | patient_code | id_personne |
| Nom | nom_complet | prenom + nom | patient_name |
| Naissance | naissance | date_naiss | dob |
| Téléphone | telephone | phone_number | tel |

Un mécanisme de mapping permet de transformer toutes les données vers un modèle commun.

Exemple :

```json
{
    "pharmacy": {
        "id": "client_id",
        "name": "nom_complet",
        "birthdate": "naissance",
        "phone": "telephone"
    },

    "consultation": {
        "id": "patient_code",
        "first_name": "prenom",
        "last_name": "nom",
        "birthdate": "date_naiss",
        "phone": "phone_number"
    },

    "imaging": {
        "id": "id_personne",
        "name": "patient_name",
        "birthdate": "dob",
        "phone": "tel"
    }
}
```

---

# 📐 Modèle Canonique

Après extraction et mapping, toutes les données patients sont transformées vers un modèle commun.

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

---

# 🧹 Nettoyage des données

Les données provenant des différentes sources peuvent contenir des incohérences.

Exemple :

```text
" Jean Rakoto "
"JEAN RAKOTO"
"jean rakoto"
```

Après nettoyage :

```text
jean rakoto
```

Les opérations principales sont :

- Suppression des espaces inutiles.
- Conversion en minuscules.
- Normalisation des numéros de téléphone.
- Standardisation des dates.
- Suppression des caractères inutiles.
- Gestion des valeurs manquantes.
- Correction de certains formats incohérents.

---

# 🧠 Déduplication des patients

Le cœur du projet repose sur la détection des patients présents dans plusieurs sources.

Exemple :

```text
Source Pharmacie
Jean Rakoto

Source Consultation
Rakoto Jean

Source Imagerie
JEAN RAKOTO
```

Ces trois enregistrements peuvent représenter le même patient.

---

## Matching déterministe

Identification basée sur des informations identiques.

Exemples :

- Numéro de téléphone.
- Adresse email.
- Identifiant national.
- Combinaison de plusieurs attributs.

```text
phone_A == phone_B

→ Patient probablement identique
```

---

## Matching probabiliste / Fuzzy Matching

Lorsque les données ne sont pas exactement identiques, un score de similarité est calculé.

| Critère | Poids |
|---|---:|
| Nom | 40% |
| Date de naissance | 30% |
| Téléphone | 20% |
| Adresse | 10% |

Formule :

```text
Score =
(Nom × 0.40)
+
(Date naissance × 0.30)
+
(Téléphone × 0.20)
+
(Adresse × 0.10)
```

Décision :

```text
Score >= 90%
    → MATCH automatique

Score entre 70% et 90%
    → Vérification manuelle

Score < 70%
    → Patients différents
```

---

# 👤 Master Patient Index

Après déduplication, chaque patient possède une identité unique dans la base centrale.

```text
MASTER PATIENT

ID : 102

Nom : Jean Rakoto
Date de naissance : 1990-01-10
Téléphone : 0341234567
```

Ce patient peut être relié à plusieurs systèmes sources.

---

# 🔑 Identity Mapping

Les identifiants locaux doivent être associés à l'identifiant central.

```text
patient_identity_map

id
source_system
source_patient_id
master_patient_id
matching_score
matching_method
```

Exemple :

| Source | Source ID | Master ID | Score |
|---|---|---|---:|
| Pharmacie | 15 | 102 | 100% |
| Consultation | 88 | 102 | 95% |
| Imagerie | IMG-20 | 102 | 92% |

Cette table est essentielle pour préserver la traçabilité.

---

# 🗃️ Base PostgreSQL centrale

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

        Pharmacy      Consultation   Imaging
```

---

# 🔒 Gouvernance et Consentement

Le système prévoit une gestion du consentement concernant l'accès aux données du patient.

```text
Patient
   │
   ▼
Demande d'accès
   │
   ▼
Vérification du consentement
   │
 ┌─┴───────────┐
 │             │
 ▼             ▼
Autorisé      Refusé
 │             │
 ▼             ▼
Accès       Access Denied
```

Exemple :

| Patient | Type de données | Autorisation |
|---|---|---|
| Jean Rakoto | Consultation | Oui |
| Jean Rakoto | Pharmacie | Oui |
| Jean Rakoto | Imagerie | Non |

---

# 🛠️ Technologies

## Phase MVP

- Python
- Pandas
- RapidFuzz
- PostgreSQL
- SQLAlchemy
- CSV

## API

- FastAPI

## Dashboard

- Streamlit

## Évolution future

- MySQL
- SQLite
- PostgreSQL Sources
- Apache Spark
- Docker

---

# 📁 Structure du projet

```text
patient-data-platform/

├── README.md
│
├── data/
│   │
│   ├── raw/
│   │   │
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
│   │
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
├── tests/
│
├── main.py
│
└── requirements.txt
```

---

# 📊 Dashboard MVP

Le dashboard permettra de visualiser :

- Nombre de sources.
- Nombre de patients extraits.
- Nombre de doublons détectés.
- Nombre de patients uniques.
- Taux de déduplication.
- Qualité des données.
- Résultats du matching.
- Historique consolidé d'un patient.

Exemple :

```text
┌──────────────────────────────┐
│ SOURCES CONNECTÉES        3  │
├──────────────────────────────┤
│ PATIENTS EXTRAITS      2 450 │
├──────────────────────────────┤
│ DOUBLONS DÉTECTÉS        550 │
├──────────────────────────────┤
│ PATIENTS UNIQUES       1 900 │
└──────────────────────────────┘
```

---

# 🚀 Évolution CSV → Database

L'architecture est conçue pour permettre cette évolution :

## Aujourd'hui

```text
CSV
 │
 ▼
CSVExtractor
 │
 ▼
DataFrame
 │
 ▼
Pipeline
```

## Plus tard

```text
MySQL
 │
 ▼
MySQLExtractor
 │
 ▼
DataFrame
 │
 ▼
Pipeline
```

Ou :

```text
PostgreSQL
 │
 ▼
PostgresExtractor
 │
 ▼
DataFrame
 │
 ▼
Pipeline
```

Le principe est :

> **Le pipeline métier ne doit pas savoir si les données proviennent d'un CSV, d'une base MySQL, PostgreSQL ou SQLite.**

Toutes les sources doivent être converties vers un format commun avant d'entrer dans le pipeline.

---

# 📅 Planning MVP — 1 mois

## Semaine 1 — Sources CSV et Architecture

- Création de la structure du projet.
- Création des trois sources CSV.
- Création de données fictives.
- Introduction volontaire de doublons.
- Configuration du projet.
- Mise en place de l'architecture des extracteurs.

### Livrable

Trois sources CSV hétérogènes fonctionnelles.

---

## Semaine 2 — ETL et Transformation

- Extraction des CSV.
- Création du modèle canonique.
- Data Mapping.
- Nettoyage.
- Normalisation.
- Validation.

### Livrable

Pipeline de transformation fonctionnel.

---

## Semaine 3 — Déduplication

- Exact Matching.
- Fuzzy Matching.
- Similarity Scoring.
- Création du Master Patient.
- Identity Mapping.

### Livrable

Système de déduplication fonctionnel.

---

## Semaine 4 — Centralisation et Interface

- Création de la base PostgreSQL centrale.
- Chargement des données.
- Migration des relations métier.
- Gestion basique du consentement.
- Dashboard.
- Tests.
- Préparation de la démonstration.

### Livrable

MVP complet et présentable.

---

# 🎓 Pourquoi développer cette solution ?

Des solutions professionnelles existent déjà dans les domaines de :

- ETL ;
- Data Integration ;
- Data Quality ;
- Master Data Management ;
- Entity Resolution.

Cependant, le développement d'un MVP personnalisé présente plusieurs avantages.

## 1. Adaptation aux données hétérogènes

Chaque système peut avoir :

- des noms de tables différents ;
- des noms de colonnes différents ;
- des identifiants différents ;
- des formats différents ;
- des relations métier différentes.

Une solution personnalisée permet d'adapter le pipeline à ces contraintes.

---

## 2. Maîtrise de la logique de déduplication

Le système permet de contrôler :

- les critères de matching ;
- les poids ;
- les scores ;
- les seuils de décision ;
- les règles métier.

La décision est donc transparente et explicable.

---

## 3. Rapidité de prototypage et évolutivité

L'utilisation initiale de CSV permet de développer rapidement le MVP.

L'architecture modulaire permet ensuite de connecter de véritables bases de données sans modifier le cœur du système.

---

## 4. Valeur académique

Le projet permet de démontrer des compétences en :

- Data Engineering ;
- ETL ;
- Data Integration ;
- Data Cleaning ;
- Data Quality ;
- Entity Resolution ;
- Master Data Management ;
- Architecture logicielle ;
- Bases de données ;
- Data Governance.

---

# 🔬 Problématique

> **Comment concevoir une plateforme capable d'intégrer et de centraliser des données patients provenant de sources hétérogènes, tout en assurant leur qualité, la détection des doublons, la traçabilité des identités et la gouvernance des accès basée sur le consentement du patient ?**

---

# 🎯 MVP attendu

Le MVP final doit démontrer la chaîne complète :

```text
SOURCES CSV HÉTÉROGÈNES
            │
            ▼
       EXTRACTION
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
      DEDUPLICATION
            │
            ▼
   MASTER PATIENT INDEX
            │
            ▼
    IDENTITY MAPPING
            │
            ▼
   CENTRALISATION POSTGRESQL
            │
            ▼
       DASHBOARD
```

---

# 🔮 Perspectives d'évolution

Après validation du MVP, plusieurs évolutions sont possibles :

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

Ainsi que :

- Apache Spark pour le traitement distribué.
- Apache Airflow pour l'orchestration.
- Docker pour la conteneurisation.
- Gestion avancée des rôles.
- Chiffrement des données sensibles.
- Audit complet.
- Machine Learning pour améliorer la déduplication.
- Intégration de standards médicaux comme HL7/FHIR.

---

# 📌 Conclusion

Ce projet ne consiste pas simplement à déplacer des fichiers CSV vers PostgreSQL.

L'utilisation des fichiers CSV constitue une **première implémentation du MVP**, permettant de valider rapidement la logique métier.

L'objectif principal reste :

> **Intégrer, nettoyer, réconcilier et centraliser des données patients hétérogènes tout en conservant la traçabilité des sources et des identités.**

L'architecture modulaire permet ensuite de faire évoluer progressivement les sources CSV vers de véritables systèmes de bases de données.

Le principe fondamental du projet est donc :

> **Changer la source sans changer le pipeline métier.**
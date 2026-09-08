# Conception Globale du Projet "DataLake Mavis"

Ce document décrit l'architecture globale de la plateforme et le découpage du projet en modules fonctionnels priorisés pour atteindre les objectifs du MVP (Minimum Viable Product).

## 1. Rappel des Objectifs

Le projet vise à construire une plateforme Big Data pour la gouvernance des données patient, incluant :

- **Qualité des données** : Nettoyage et standardisation.
- **Déduplication** : Identification et gestion des doublons.
- **Gouvernance** : Contrôle d'accès basé sur les rôles et, à terme, sur le consentement patient.
- **Visualisation** : Un tableau de bord pour le suivi des données métier et de la gouvernance.

## 2. Architecture Cible (Medallion)

L'architecture suit le modèle Medallion pour organiser les données en couches successives de qualité croissante.

- **`Zone RAW (Bronze)`**
  - **Rôle** : Stockage des données brutes, telles qu'extraites des sources.
  - **État** : ✅ **Fonctionnel**. Le script `discovery_sources.py` remplit ce rôle.

- **`Zone SILVER (Argent)`**
  - **Rôle** : Contient les données nettoyées, normalisées, et standardisées selon le schéma pivot FHIR. Les doublons sont identifiés à ce niveau.
  - **État** : ✅ **Fonctionnel**. Le script `create_silver.py` normalise le genre, détecte les doublons, et traite 2 sources.

- **`Zone GOLD (Or)`**
  - **Rôle** : Contient les données agrégées et prêtes pour l'analyse et la visualisation. C'est la source de données pour l'application web.
  - **État** : ✅ **Fonctionnel**. Le script `create_gold.py` produit la table `patient_events_gold` avec jointures 4 tables Silver.

## 3. Composants Majeurs de la Plateforme

1.  **Pipeline de Données (ELT avec Spark)** : Le cœur du système, responsable de l'extraction, du chargement et de la transformation des données à travers les zones RAW, SILVER et GOLD.
2.  **Couche de Gouvernance** : Le mécanisme qui sécurise l'accès aux données. Dans le cadre du MVP, il s'agira d'un contrôle d'accès basé sur les rôles (RBAC).
3.  **API Backend (Flask/Python)** : Le service qui expose les données de la couche GOLD au frontend via PySpark/Hive, tout en appliquant les règles de la couche de gouvernance.
4.  **Frontend (Next.js / D3.js)** : L'application web qui permet aux utilisateurs de visualiser les données et, pour les administrateurs, de suivre les indicateurs de gouvernance.

## 4. Découpage en Modules (Priorités MVP)

Pour garantir une livraison en 40 jours, le développement sera séquencé en modules prioritaires.

### **Priorité 1 : Finalisation du Pipeline RAW -> SILVER**

- **Objectif** : Assurer que les données dans la zone Silver sont propres, standardisées et que les doublons sont marqués.
- **MVP** : Normaliser les valeurs pour les champs critiques (ex: `gender`), identifier les doublons avec un flag `is_duplicate`.
- **Post-MVP** : Implémenter la logique de fusion des doublons, enrichir avec des règles de nettoyage plus complexes.
- **Fichier de suivi** : `MODULE_1_PIPELINE_RAW_SILVER.md`

### **Priorité 2 : Implémentation de la Gouvernance Simplifiée (RBAC)**

- **Objectif** : Mettre en place un contrôle d'accès simple basé sur deux rôles (ex: `MEDECIN`, `ADMIN`) et l'intégrer dans l'API.
- **MVP** : Créer un middleware dans l'API qui vérifie un rôle défini statiquement (ex: dans un fichier JSON).
- **Post-MVP** : Développer le système complet de gestion du consentement patient, avec une base de données dédiée et des journaux d'audit.
- **Fichier de suivi** : `MODULE_2_GOUVERNANCE_SIMPLIFIEE.md`

### **Priorité 3 (Post-MVP si le temps le permet) : Adaptation du Tableau de Bord**

- **Objectif** : Ajouter un indicateur simple de gouvernance sur le frontend (ex: nombre de doublons détectés).
- **MVP** : Créer une nouvelle route d'API et un composant simple pour afficher le nombre de doublons.
- **Post-MVP** : Développer un tableau de bord de gouvernance complet (qualité des données, logs d'accès, gestion des consentements).

### **Modules Futurs (Hors MVP)**

- **Déduplication Avancée** : Implémentation de la logique de fusion automatique des doublons.
- **Gestion du Consentement Patient** : Développement du module complet de gestion du consentement.

# Cahier des Charges

## Plateforme Big Data de Gestion et de Gouvernance des Données Patients

| Champ               | Valeur                                                                              |
| ------------------- | ----------------------------------------------------------------------------------- |
| **Session**         | Sep-2026                                                                            |
| **Parcours**        | Master MBDS                                                                         |
| **Thème de stage**  | Conception d'une plateforme Big Data de gestion et de gouvernance des données patients : nettoyage, déduplication et contrôle d'accès basé sur le consentement du patient |
| **Société**         | Madagascar Medical Technology (MMT)                                                 |
| **Date**            | Du 06-07-2026 au 06-10-2026                                                        |
| **Durée**           | 4 mois                                                                              |
| **Stagiaire**       | 1                                                                                   |
| **Type de projet**  | Nouveau                                                                             |
| **État document**   | Version actualisée au 28-08-2026 (alignée sur l'implémentation réelle)              |

---

## 1. Contexte et Problématique

Les établissements médicaux de Madagascar génèrent des volumes importants de données hétérogènes provenant de sources multiples (hôpitaux, cliniques, laboratoires, pharmacies). Ces données sont souvent :
- **Dispersées** dans des systèmes hétérogènes (PostgreSQL, fichiers Excel, bases legacy)
- **Non standardisées** (formats différents, codes CIM-10 non normalisés, valeurs de genre incohérentes)
- **Non dédupliquées** (un même patient peut avoir plusieurs dossiers)
- **Non gouvernées** (pas de contrôle d'accès par rôle ni par consentement)

Ces problèmes entraînent des risques d'erreurs médicales, des difficultés d'analyse et des failles de confidentialité.

---

## 2. Objectifs du Projet

### 2.1 Objectif Principal
Concevoir et développer une plateforme Big Data interopérable capable de :
1. **Centraliser** les données médicales de sources multiples dans un Data Lake
2. **Nettoyer et standardiser** les données selon un schéma pivot FHIR
3. **Déduplier** les dossiers patients intelligemment
4. **Sécuriser** l'accès par contrôle basé sur les rôles (RBAC), puis à terme sur le consentement patient
5. **Visualiser** les données et les indicateurs de gouvernance via une application web

### 2.2 Objectifs Spécifiques

| # | Objectif | Indicateur de réussite | Statut (28/08/2026) |
|---|----------|------------------------|---------------------|
| O1 | Pipeline ELT automatisé (RAW → SILVER → GOLD) | Données ingérées, nettoyées et exposées en < 30 min | Livré — 4 étapes orchestrées `run_pipeline.sh` |
| O2 | Normalisation des valeurs critiques | Genre, dates standardisés (gender → male/female) | Livré (gender) — CIM-10 partiel, dettes mapping MMT_DB |
| O3 | Détection des doublons patients | Flag `is_duplicate` (nom + date naissance + genre) | Livré — 24 872 doublons détectés, sans fusion |
| O4 | RBAC fonctionnel | 2 rôles min. (ADMIN, MEDECIN), protection pages + API | Livré (NextAuth + Prisma + `checkRole`) |
| O5 | Gestion du consentement patient | Chaque accès vérifié contre le consentement | **À terme (Post-MVP)** — non démarré |
| O6 | Dashboard de gouvernance | KPI : doublons, qualité données, consentements, accès | Partiel — dashboard KPI livré, page governance à créer |

---

## 3. Périmètre Fonctionnel

### 3.1 Module 1 — Pipeline de Données (ELT Big Data)

**Entrée** : Données brutes depuis les bases sources (PostgreSQL via SSH/JDBC)
**Sortie** : Données structurées dans la zone GOLD, prêtes pour la visualisation

| Composant | Description | Technologies | Statut |
|-----------|-------------|--------------|--------|
| **Extraction (RAW)** | Connexion aux bases sources via SSH tunnel + JDBC, extraction Parquet vers HDFS | PySpark, sshtunnel, paramiko | Livré |
| **Découverte** | Métadonnées automatiques (tables, colonnes, types, FK via information_schema) | PySpark | Livré |
| **Mapping FHIR** | Correspondance tables/colonnes → entités FHIR (synonymes + RapidFuzz) | Python, RapidFuzz, `fhir_synonyms.py` | Livré (sans NLP) |
| **Nettoyage (SILVER)** | Normalisation des valeurs (gender → male/female), cast typé, union multi-sources | PySpark | Livré |
| **Déduplication** | Identification des doublons par fenêtrage Spark (nom + DOB + genre), flag `is_duplicate` | PySpark Window functions | Livré |
| **Traçabilité** | `_source_table`, `patient_uuid` (SHA-256), `sync_metadata.json` | PySpark | Livré |
| **Stockage SILVER** | 4 tables Hive harmonisées FHIR | Hive, HDFS | Livré |
| **Stockage GOLD** | Table Hive agrégée pour la visualisation (17 colonnes) | Hive, HDFS | Livré |
| **Orchestration** | Enchaînement séquentiel des 4 étapes, arrêt sur erreur | `run_pipeline.sh` | Livré |

**Architecture Medallion :**
```
Sources (PostgreSQL) ──→ Zone RAW (Bronze) ──→ Zone SILVER (Argent) ──→ Zone GOLD (Or)
     [JDBC/SSH]            [HDFS Parquet]      [Hive Tables FHIR]       [Hive Analytics]
                           Découverte           Nettoyage               Table patient_events_gold
                           Extraction           Normalisation gender     Prêt pour API
                                                Détection doublons
                                                Mapping FHIR
```

**Étapes du pipeline (4/4) :**

| Étape | Script | Rôle |
|-------|--------|------|
| 1/4 | `provision/scripts/ELT/gen_extract_raw.py` | Extraction RAW + découverte + tables Hive externes |
| 2/4 | `provision/scripts/ELT/gen_fhir_mapping.py` | Génération du mapping colonnes → FHIR (`fhir_mapping.json`) |
| 3/4 | `provision/scripts/ELT/create_silver.py` | Transformation SILVER (4 tables `datalake_silver.*_fhir`) |
| 4/4 | `provision/scripts/ELT/create_gold.py` | Table GOLD `datalake_gold.patient_events_gold` |

**Tables SILVER générées :**

| Table | Contenu |
|-------|---------|
| `datalake_silver.patient_fhir` | Patients unifiés multi-sources, genre normalisé, `is_duplicate` |
| `datalake_silver.encounter_fhir` | Consultations / hospitalisations |
| `datalake_silver.condition_fhir` | Diagnostics CIM-10 |
| `datalake_silver.observation_fhir` | Indicateurs (mortalité, parité, gravida, live_births) |

### 3.2 Module 2 — Gouvernance et Sécurité

| Composant | Description | Technologies | Statut |
|-----------|-------------|--------------|--------|
| **RBAC** | Contrôle d'accès basé sur les rôles (ADMIN, MEDECIN) | NextAuth.js, JWT, Prisma, `src/lib/rbac.ts`, `middleware.ts` | Livré |
| **Authentification** | Système de login/sessions sécurisé | NextAuth.js, JWT, bcryptjs, Prisma | Livré |
| **Rôles étendus** | INFIRMIER, CHERCHEUR | — | Reporté (besoin métier à préciser) |
| **Consentement patient** | Chaque patient définit qui peut accéder à quelles données et pour quel usage | Prisma, API REST | **Post-MVP** (non démarré) |
| **Audit log** | Journalisation de chaque accès (qui, quoi, quand, autorisé/refusé) | Prisma, API REST | **Post-MVP** (non démarré) |

**Rôles définis (MVP livré) :**

| Rôle | Accès Données Patient | Accès Gouvernance | Accès Admin |
|------|----------------------|-------------------|-------------|
| ADMIN | Complet | Complet | Complet |
| MEDECIN | Données métier RMA | Non | Non |

**Rôles futurs (Post-MVP, définis dans le cahier initial) :**

| Rôle | Accès Données Patient | Accès Gouvernance | Accès Admin |
|------|----------------------|-------------------|-------------|
| INFIRMIER | Données de soins | Lecture seule | Non |
| CHERCHEUR | Données anonymisées | Statistiques agrégées | Non |

### 3.3 Module 3 — Application Web (Visualisation)

| Composant | Description | Technologies | Statut |
|-----------|-------------|--------------|--------|
| **Dashboard** | Vue d'ensemble : KPI admissions, genre, top diagnostics | Next.js, Tailwind CSS, D3.js | Livré |
| **Visualisations métier** | Graphiques dynamiques (barres, heatmap, line charts, donut, KPI cards) | D3.js | Livré |
| **Rapports RMA** | 5 pages standards (diagnostics, morbidité, maternité, labo, paludisme) | Next.js, API Flask | Livré (mock si GOLD sparse) |
| **Recherche/Filtres** | Filtres par date/sexe/tranche d'âge (8 tranches RMA) | React context | Livré |
| **Gestion utilisateurs** | CRUD utilisateurs, attribution des rôles (ADMIN) | NextAuth.js, Prisma, PostgreSQL | Livré |
| **Page Settings** | Profil + changement de mot de passe | Next.js | Livré |
| **Page Consentements** | Gestion des consentements patients | Next.js | **À créer (Post-MVP)** |
| **Page Governance** | Indicateurs de gouvernance (admin) | Next.js | **À créer** |

**Routes principales (implémentées) :**

| Route | Fonctionnalité |
|-------|---------------|
| `/login` | Authentification NextAuth |
| `/dashboard` | KPIs généraux |
| `/rma` | Diagnostics consultations externes (heatmap CIM-10) |
| `/rma/morbidite` | Morbidité & mortalité hospitalière |
| `/rma/maternite` | CPN & maternité (line chart mensuel) |
| `/rma/laboratoire` | Activité laboratoires |
| `/rma/paludisme` | Prise en charge paludisme |
| `/users` | Gestion des utilisateurs (ADMIN seul) |
| `/settings` | Profil + mot de passe |

---

## 4. Architecture Technique

### 4.1 Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js 15)                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │Dashboard │  │ 5 pages  │  │ Users    │  │ Settings       │  │
│  │  KPI     │  │  RMA     │  │  (CRUD)  │  │                │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
│                NextAuth.js + JWT + RBAC (checkRole)            │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP (CORS)
┌─────────────────────────┼───────────────────────────────────────┐
│                    BACKEND API (Flask / Python)                 │
│  provision/api/hive_api.py (PySpark → Hive)                     │
│  Endpoints /rma/* et /api/rma/*  +  mocks backend               │
└─────────────────────────┼───────────────────────────────────────┘
                          │ JDBC/SSH
┌─────────────────────────┼───────────────────────────────────────┐
│          PIPELINE BIG DATA (Vagrant / VMware)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │ PySpark  │  │ Hadoop   │  │  Hive    │                       │
│  │ Pipeline │  │ HDFS     │  │ Metasta. │                       │
│  └──────────┘  └──────────┘  └──────────┘                       │
│  RAW → SILVER → GOLD (Medallion)                                │
│  Extraction → Mapping FHIR → Nettoyage → Agrégation            │
└─────────────────────────────────────────────────────────────────┘
                          │ SSH/JDBC
┌─────────────────────────┼───────────────────────────────────────┐
│              SOURCES DE DONNÉES                                 │
│  ┌──────────┐  ┌──────────┐                                     │
│  │  MAVIS   │  │  MMT_DB  │                                     │
│  │PostgreSQL│  │PostgreSQL│  (MMT_DB reconstruite - synthétique)│
│  └──────────┘  └──────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Stack Technologique

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| **Frontend** | Next.js 15 + React + TypeScript | SSR/SSG, middleware, typage fort |
| **UI** | Tailwind CSS + shadcn/ui + D3.js | Design system, graphiques dynamiques |
| **Auth / RBAC** | NextAuth.js + JWT + bcryptjs | Sessions sécurisées, rôle dans JWT, `checkRole()` |
| **ORM** | Prisma 6 | Migration DB, type safety, seed |
| **Base de données** | PostgreSQL | Utilisateurs, sessions (données app) |
| **Backend API** | Flask (Python) + PySpark | Exposition des données Spark/Hive via REST (port 5000) |
| **Pipeline** | Apache Spark (PySpark) | Traitement, normalisation, détection doublons |
| **Stockage** | Hadoop HDFS | Data Lake (RAW Parquet + warehouse SILVER/GOLD) |
| **Métastore** | Apache Hive 3.1.3 | Tables externes, requêtes SQL sur HDFS |
| **Mapping FHIR** | RapidFuzz + dictionnaire de synonymes | Mappage automatique colonnes → FHIR (légèreté, sans ML) |
| **Infra** | Vagrant + VMware | VM de développement reproductible (`bootstrap.sh`) |
| **CI/CD** | GitHub Actions | Prévu (Module 5) — non configuré |
| **Conteneurs** | Docker | Prévu (Module 5) — non livré |

> **Choix d'implémentation** : le cahier initial prévoyait Express.js (Node.js) + FastAPI. Le backend a été réalisé en **Flask + PySpark** (homogénéité avec la pile PySpark du pipeline, un seul langage de données). Le RBAC a été implémenté directement dans Next.js (`middleware.ts`, `src/lib/rbac.ts`) au lieu d'un middleware Express séparé. Le mapping FHIR utilise RapidFuzz + synonymes au lieu de Sentence-Transformers (dépendance ML supprimée pour stabilité Python 3.8).

### 4.3 Modèle de Données PostgreSQL (Prisma, implémenté)

```prisma
enum Role {
  ADMIN
  MEDECIN
}

model User {
  id            String    @id @default(cuid())
  firstName     String?
  lastName      String?
  email         String    @unique
  password      String
  role          Role      @default(MEDECIN)
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
}

// --- Post-MVP (prévu, non implémenté) ---
// enum Role étendu : INFIRMIER, CHERCHEUR
//
// model Consentement {
//   id            String   @id @default(cuid())
//   patientUuid   String
//   userId        String
//   user          User     @relation(fields: [userId], references: [id])
//   typeDonnee    String   // "medical", "labo", "pharmacie"
//   usage         String   // "consultation", "recherche", "statistique"
//   accorde       Boolean  @default(false)
//   dateDonation  DateTime @default(now())
//   dateExpiration DateTime?
//   createdAt     DateTime @default(now())
// }
//
// model AuditLog {
//   id          String   @id @default(cuid())
//   userId      String
//   user        User     @relation(fields: [userId], references: [id])
//   action      String   // "read", "write", "export"
//   ressource   String
//   patientUuid String?
//   autorise    Boolean
//   timestamp   DateTime @default(now())
//   details     String?
// }
```

### 4.4 Schéma Pivot FHIR (Zones SILVER / GOLD)

**Zone SILVER** (défini dans `provision/scripts/utils/fhir_schema.py`) :

| Entité | Champs | Exemple |
|--------|--------|---------|
| Patient | patient_uuid, source_patient_id, name, birth_date, gender, address, phone, email | + `is_duplicate`, `_source_table` |
| Encounter | patient_uuid, encounter_id, admission_date, discharge_date, create_date, visit_type | |
| Condition | patient_uuid, diagnosis, diagnosis_code, category, code, info, name | diagnostics CIM-10 |
| Observation | patient_uuid, mortality, parity, gravida, live_births | |

**Zone GOLD** — table `datalake_gold.patient_events_gold` (17 colonnes) :

| Champ | Type | Description |
|-------|------|-------------|
| patient_uuid | string | Identifiant unique (SHA-256) |
| source_patient_id | string | ID source préfixé (ex: `MAVIS_1`) |
| name | string | Nom du patient |
| gender | string | Genre normalisé (male/female) |
| birth_date | date | Date de naissance |
| age | double | Âge en années |
| age_tranche | string | Tranche d'âge RMA (8 tranches) |
| encounter_id | string | ID encounter |
| admission_date | date | Date d'admission |
| discharge_date | date | Date de sortie |
| visit_type | string | Type de visite |
| diagnosis_code | string | Code CIM-10 |
| category | string | Catégorie |
| diagnosis | string | Libellé diagnostic |
| mortality | int | 0/1 décès |
| parity | int | Parité |
| gravida | int | Gravida |
| live_births | int | Naissances vivantes |

---

## 5. État d'Avancement au 28/08/2026

Résumé global : **~85%** du périmètre MVP livré.

| Module | Avancement | Détaillants |
|--------|-----------|-------------|
| Pipeline ELT (Big Data) | ~90% | 4 étapes validées bout-en-bout (RAW → SILVER → GOLD), idempotence |
| Gouvernance (RBAC) | ~70% | RBAC NextAuth + `checkRole` + middleware, 2 rôles |
| Frontend (Next.js) | ~90% | Toutes les pages RMA alimentées par l'API (mocks backend si GOLD sparse) |
| Backend API (Flask) | ~60% | API opérationnelle, 12/12 tests PASS, JWT à implémenter côté API |
| Tests & Déploiement | ~5% | Tests manuels RBAC + tests API ; Docker/CI-CD et tests auto à faire |
| Authentification | ~95% | NextAuth + JWT + Prisma complet |
| Consentement patient | 0% | Post-MVP |
| Audit log | 0% | Post-MVP |
| Docker / CI-CD | ~20% | GitHub Actions non configuré |

**Dettes techniques connues (à traiter en priorité) :**
- Mapping FHIR enrichi : lier encounters/conditions/observations aux patients (jointures GOLD limitées : 16 lignes)
- Compléter gender/date de naissance côté MMT_DB (actuellement NULL)
- Connexion du filtre âge frontend aux endpoints API réels
- Authentification JWT côté API Flask (uniquement NextAuth côté frontend actuellement)

---

## 6. Planning Révisé

**Réalisé (Sprints 1 à 2.6) :**
- Sprint 1 — Finalisation pipeline ELT (23/08) : normalisation gender, détection doublons, portage GOLD, orchestration
- Sprint 2 — Auth + RBAC (24/08) : JWT, middleware, `checkRole`, rôles ADMIN/MEDECIN
- Sprint 2.5 — Frontend fonctionnel (26/08) : pages RMA, settings, filtres, données fictives backend
- Sprint 2.6 — Documentation (26/08) : MODULE_1 à MODULE_5, SUIVI_AVANCEMENT
- 27/08 — API Flask réécrite, tests backend 12/12, frontend branché sur l'API

**Restant (à planifier) :**

| Sprint | Contenu | Durée estimée |
|--------|---------|---------------|
| Sprint 3 | Gouvernance : tables Consentement + Audit Log (Prisma), API, pages frontend | 1-2 semaines |
| Sprint 4 | Docker Compose + GitHub Actions CI/CD (Vagrantfile dans `old/` à réintégrer) | 1 semaine |
| Sprint 5 | Tests unitaires et d'intégration, enrichissement mapping FHIR (dettes qualité) | 1-2 semaines |
| Finalisation | Export VM `.box`, documentation utilisateur, préparation soutenance | 1 semaine |

---

## 7. Données Sources

### 7.1 Sources Identifiées (réel)

| Source | Type | Connexion | Tables extraites |
|--------|------|-----------|------------------|
| **MAVIS** (mavis_notheme) | PostgreSQL distant | SSH tunnel (102.16.7.154:8090) + JDBC | 11 tables (hms_patient, res_partner, hms_diseases, hr_employee, res_users, ir_attachment, product_product, patient_death_register, hms_physician, acs_ethnicity, account_move) |
| **MMT_DB** (mmt_db) | PostgreSQL local (hôte Windows) | TCP direct (192.168.56.1:5432) | 3 tables (gnuhealth_patient, party_party, gnuhealth_family) |
| **Fichiers Excel** | CIM-10, templates | Import local (`docs/`, `provision/config/`) | Références (cim10_liste.csv) |

> **MMT_DB** : base d'origine GNU Health non récupérable → **reconstruite avec données synthétiques réalistes** via `provision/db/rebuild_mmt_db.py` (60 271 lignes, 9 tables, CIM-10 réelle, FK respectées).

### 7.2 Volumes réels observés (run du 24/08/2026)

| Critère | Valeur |
|---------|--------|
| `datalake_silver.patient_fhir` | ~65 680 patients (fusion MAVIS + MMT_DB) |
| dont MMT_DB `gnuhealth_patient` | 9 791 |
| dont MAVIS `hms_patient` | 2 155 |
| Genre normalisé | male 2 014 / female 1 144 / other 1 (le reste NULL) |
| Doublons détectés (`is_duplicate=1`) | 24 872 |
| `datalake_gold.patient_events_gold` | 16 lignes (encounters non reliées aux patients — dette connue) |
| Temps de traitement | Pipeline complet < 30 min |

---

## 8. Contraintes et Risques

### 8.1 Contraintes Techniques

| Contrainte | Impact | Mitigation |
|------------|--------|------------|
| VM Vagrant 8 Go (ressources limitées) | Performance pipeline Spark | Mémoire Spark réduite (executor 4g / driver 2g), `shuffle.partitions=8` |
| Connexion SSH distante (MAVIS) | Instabilité réseau | Retry automatique (sshtunnel, 3 tentatives) |
| Hétérogénéité des sources | Mapping FHIR | Synonymes + RapidFuzz (sans dépendance ML) |
| Données médicales sensibles | Confidentialité | RBAC + chiffrement des mots de passe (bcrypt) |
| Postgres local non-service (Laragon) | Indisponibilité MMT_DB après reboot | Démarrage manuel `pg_ctl start`, base synthétique recréable |

### 8.2 Risques Identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Indisponibilité des sources | Moyenne | Élevé | Données de test fictives en backup (mocks backend) |
| Mauvais mapping FHIR (dettes qualité) | Élevée | Moyen | Enrichir `fhir_synonyms` + liens FK, priorité Sprint 5 |
| Dérapage planning | Élevée | Moyen | MVP dissocié du Post-MVP (consentement, audit log) |
| Problèmes SSH/VPN | Élevée | Élevé | Documentation des erreurs, fallback direct |
| Volume de données > capacité VM | Faible | Moyen | Échantillonnage, pagination des endpoints |

---

## 9. Livrables Attendus

| # | Livrable | Format | Statut (28/08/2026) |
|---|----------|--------|---------------------|
| 1 | Code source complet | Git | Livré |
| 2 | Pipeline ELT fonctionnel | Scripts PySpark (`provision/scripts/ELT/`) | Livré |
| 3 | Application web | Next.js (visualisation_app/) | Livré (fonctionnel) |
| 4 | API backend | Flask (`provision/api/hive_api.py`) | Livré |
| 5 | Documentation technique | README, MODULE_1..5, PIPELINE.md, SUIVI_AVANCEMENT.md | Livré |
| 6 | Rapport de stage | Document Word/PDF | À faire |
| 7 | Slides de soutenance | PowerPoint/PDF | À faire |
| 8 | VM Vagrant exportée | `.box` | À faire |
| 9 | Docker + CI/CD | `docker-compose.yml`, `.github/workflows/` | À faire (Sprint 4) |

---

## 10. Métriques de Succès

| Métrique | Cible | Constat (28/08/2026) |
|----------|-------|----------------------|
| Taux de normalisation des données | ≥ 95% | Partiel : gender normalisé, NULL côté MMT_DB |
| Doublons détectés correctement | ≥ 90% (recall) | 24 872 marqués sur (name, birth_date, gender) |
| Temps de traitement pipeline | < 30 min | Atteint |
| Taux de disponibilité application | ≥ 99% | Non mesuré |
| Couverture des tests | ≥ 80% | Non atteint (~5%, tests API 12/12 PASS) |
| Zéro accès non autorisé | 0 violation | RBAC testé (ancien 401, MEDECIN 403, ADMIN 200) |

---

## 11. Références

- [FHIR Standard](https://www.hl7.org/fhir/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
- [OWASP Security Practices](https://owasp.org/www-project-top-ten/)
- CIM-10 : Classification Internationale des Maladies (OMS)

---

## Annexes

### A. Correspondance cahier initial → réalisation (écarts notables)

| Sujet | Cahier initial | Réalisation | Type |
|-------|----------------|-------------|------|
| Backend API | Express.js + FastAPI | Flask + PySpark | Choix technique |
| RBAC | Middleware Express.js | NextAuth + Prisma + `checkRole` (Next.js) | Choix technique |
| Mapping FHIR | Sentence-Transformers (NLP) | RapidFuzz + synonymes | Simplification |
| Rôles | 4 (ADMIN, MEDECIN, INFIRMIER, CHERCHEUR) | 2 (ADMIN, MEDECIN) | Périmètre réduit (MVP) |
| Consentement patient | Objectif du thème | Post-MVP | Reporté |
| Audit log | Périmètre initial | Post-MVP | Reporté |
| Docker / CI-CD | Stack comprise | Non livré (Module 5) | Reporté |
| GOLD storage | Hive/PostgreSQL | Hive uniquement | Inhibition |
| MMT_DB | Base GNU Health réelle | Base synthétique recréée | Contrainte |
| Table cible | `datalake_gold.patient_events_gold` (schéma différent) | 17 colonnes réelles alignées API | Évolution |

### B. Fichiers de référence du projet

| Fichier | Contenu |
|---------|---------|
| `README.md` | Présentation projet + démarrage |
| `CONCEPTION_GLOBALE.md` | Architecture Medallion, découpage modules |
| `PIPELINE.md` | Fonctionnement complet du pipeline ELT |
| `MODULE_1_PIPELINE_RAW_SILVER.md` | Détails Module 1 |
| `MODULE_2_GOUVERNANCE_SIMPLIFIEE.md` | Détails Module 2 |
| `MODULE_3_FRONTEND_VISUALISATION.md` | Détails Module 3 |
| `MODULE_4_BACKEND_API.md` | Détails Module 4 |
| `MODULE_5_TESTS_DEPLOIEMENT.md` | Détails Module 5 |
| `SUIVI_AVANCEMENT.md` | Journal de traçabilité + état d'avancement |
| `provision/api/README.md` | Guide API Flask |
# Suivi d'avancement — DataLake Mavis

Dernière mise à jour : 01/09/2026

## Objectif

Plateforme **Big Data de gestion et de gouvernance des données patients** pour Madagascar Medical Technology : centraliser des données médicales hétérogènes dans un Data Lake, les nettoyer selon un schéma pivot **FHIR**, identifier les doublons, sécuriser l'accès (RBAC) et visualiser les indicateurs RMA via une application web.

Détails : `CAHIER_DE_CHARGE.md` | Architecture : `CONCEPTION_GLOBALE.md` | Pipeline : `PIPELINE.md`

## Vue globale — ~85%

```
Pipeline ELT [███████████████████░] 90%
Backend API  [████████████████░░░░] 60%
Frontend     [████████████████████░] 90%
Gouvernance  [███████████████░░░░░] 70%
Auth         [███████████████████░░] 95%
Tests/Deploy [█░░░░░░░░░░░░░░░░░░░]  5%
```

| Module | % | Statut |
|--------|---|--------|
| Pipeline ELT (PySpark + Hive) | 90% | Fonctionnel bout-en-bout |
| Backend API (Flask) | 60% | Opérationnel, 12/12 tests, JWT à ajouter |
| Frontend (Next.js) | 90% | Toutes pages RMA alimentées par l'API |
| Gouvernance (RBAC) | 70% | ADMIN/MEDECIN, pages + API protégées |
| Authentification | 95% | NextAuth + JWT + Prisma |
| Tests & Déploiement | 5% | RBAC manuel + tests API ; Docker/CI à faire |
| Consentement + Audit log | 0% | Post-MVP |

---

## Modules — fait / reste

### 1. Pipeline ELT (~90%)

**Fait :**
- 4 étapes orchestrées (`run_pipeline.sh`) : extraction RAW → mapping FHIR → silver → gold, arrêt sur erreur
- Extraction PostgreSQL via SSH tunnel + JDBC, Parquet HDFS, tables Hive externes (11 tables MAVIS, 3 tables MMT_DB)
- **Sources locales de développement (01/09)** : réplique `mavis_notheme` sur PostgreSQL Laragon (`rebuild_mavis_db.py`, 73 090 lignes) en remplacement du MAVIS distant instable ; MMT_DB déjà local ; config `data_sources.json` sans SSH. Nouvelle source **SQLite `CLINIQUE`** (`clinique.db`, 54 582 lignes, 4 tables FHIR) intégrée au pipeline (extraction `discover_sqlite`, mapping FHIR, Silver, Gold)
- Silver : 4 tables FHIR, genre normalisé (male/female), `is_duplicate`, `patient_uuid` SHA-256, traçabilité `sync_metadata.json`
- Gold : `datalake_gold.patient_events_gold` (17 colonnes, 8 tranches d'âge RMA), idempotent

**Reste :**
- Enrichir le mapping FHIR : lier encounters/conditions/observations aux patients (jointures GOLD limitées)
- Fusion des doublons patients (golden record) — Post-MVP
- Intégration du vrai MAVIS distant quand stable (les sources locales restent disponibles en parallèle)

### 2. Backend API (Flask, ~60%)

**Fait :**
- API Flask + PySpark (`provision/api/hive_api.py`, port 5000), CORS
- 9 endpoints (`/rma/*` et `/api/rma/*`), mocks backend (flag `mocked`) quand GOLD est sparse
- 12/12 tests PASS

**Reste :**
- Authentification JWT côté API (seulement NextAuth actuellement)
- Endpoints laboratoire et paludisme : données réelles (sources hors GOLD)
- Brancher le filtre âge frontend aux endpoints réels

### 3. Frontend (Next.js, ~90%)

**Fait :**
- Auth : page login, NextAuth Credentials + JWT, seed utilisateurs
- Gestion utilisateurs : CRUD complet, protégé ADMIN, hash masqué
- Dashboard : KPIs (admissions, mortalité), top 5 pathologies
- Filtres globaux : date, sexe, 8 tranches d'âge RMA
- 5 pages RMA (diagnostics, morbidité, maternité, laboratoire, paludisme) avec graphiques D3.js (heatmap, bar, line, donut), alimentées par l'API (mocks si nécessaires)
- Page Settings (profil + mot de passe), Sidebar adaptative, dernière synchro Data Lake

**Reste :**
- Intégration des **données réelles** (GOLD enrichi) — actuellement mocks backend
- Page Consentements + page Governance (Post-MVP / Sprint 3)
- Exports PDF/Excel, responsive mobile, dark mode, notifications (priorité basse)

### 4. Gouvernance RBAC (~70%)

**Fait :**
- 2 rôles (ADMIN, MEDECIN), rôle dans le JWT
- Middleware pages + helper `checkRole()` API (401/403), sidebar adaptative
- Tests : anonyme 401, MEDECIN 403 sur /users, ADMIN 200

**Reste :**
- Rôles INFIRMIER / CHERCHEUR (reportés, besoin métier à préciser)
- Consentement patient + audit log : tables Prisma, API, pages — **Post-MVP**

### 5. Authentification (~95%)

**Fait :** NextAuth + Prisma Adapter, JWT avec rôle, bcrypt, routes `/api/auth/[...nextauth]`, types étendus. Seed ADMIN + MEDECIN.

**Reste :** rien de bloquant (rôles étendus dépendent du §4).

### 6. Tests & Déploiement (~5%)

**Fait :** tests manuels RBAC, 12/12 tests API Flask.

**Reste :**
- Tests unitaires + intégration (cible ≥80% de couverture)
- Docker Compose + GitHub Actions CI/CD (Sprint 4)
- Export VM `.box` + documentation utilisateur
- Rapport de stage + slides de soutenance

---

## Prochaines étapes (priorisées)

| Priorité | Tâche | Effort | Module |
|----------|-------|--------|--------|
| Haute | Enrichir mapping FHIR + liens FK (GOLD réellement alimenté) | 3-5 j | Pipeline |
| Haute | Propager Docker/CI + dépendances + démarrage API (infra Laragon en place) | 1 j | Déploiement |
| Moyenne | JWT côté API Flask | 1 j | Backend |
| Moyenne | Filtre âge branché aux endpoints réels | 0.5 j | Backend/Frontend |
| Moyenne | Tests automatiques (pipeline + API + frontend) | 3-5 j | Tests |
| Moyenne | Docker Compose + GitHub Actions | 2-3 j | Déploiement |
| Basse | Consentements + audit log (tables, API, pages) | 1-2 sem | Gouvernance |
| Basse | Export PDF/Excel, responsive, dark mode | 2-3 j | Frontend |
| Final | Export VM `.box`, rapport de stage, slides | 1 sem | — |

---

## Jalons clés

| Date | Jalon |
|------|-------|
| 23/08 | Module 1 : normalisation gender + doublons + portage GOLD |
| 23/08 | VM reconstruite (bootstrap.sh automatisé, Hadoop/Hive/Spark opérationnels) |
| 24/08 | MMT_DB recréée (synthétique, 60 271 lignes) ; pipeline 4/4 vert ; Module 1 validé (65 680 patients Silver) |
| 24/08 | Sprint 2 : Auth + RBAC (JWT, checkRole, middleware, seed) |
| 26/08 | Frontend fonctionnel : 5 pages RMA, settings, filtres, données fictives |
| 26/08 | API Flask réécrite ; modules de documentation créés |
| 27/08 | API + mocks backend ; frontend branché sur l'API ; 12/12 tests PASS |
| 28/08 | Documentation consolidée (PIPELINE.md, CAHIER actualisé, LOG.md) |
| 01/09 | Sources 100% locales + nouvelle source SQLite : réplique `mavis_notheme` (Laragon), source `CLINIQUE` (sqlite) intégrée bout-en-bout (RAW→Silver→Gold) |

---

## Liens utiles

| Fichier | Contenu |
|---------|---------|
| `CAHIER_DE_CHARGE.md` | Objectifs, périmètre, architecture, planning, métriques |
| `CONCEPTION_GLOBALE.md` | Architecture Medallion et découpage modules |
| `PIPELINE.md` | Fonctionnement complet du pipeline ELT |
| `MODULE_1..5_*.md` | Détails par module (pipeline, gouvernance, frontend, backend, tests) |
| `LOG.md` | Historique détaillé (incidents, fixes, runs, traçabilité) |
# 🎯 Projet : DataLake Mavis

## 📌 Titre complet
**Réalisation d’un Data Lake interopérable pour analyse et visualisation des données médicales via une application web.**

---

## 🧭 Contexte du projet

Les établissements médicaux génèrent une grande quantité de données hétérogènes (formats, systèmes, technologies). Ce projet propose la conception d'un **Data Lake interopérable** qui collecte, nettoie, structure et rend accessibles les données médicales provenant de plusieurs sources, via une application web.

## 🎯 Objectif principal

Créer une plateforme complète permettant :
- la **centralisation de données médicales** (MAVIS + MMT_DB) dans un Data Lake
- la **normalisation des données** selon un schéma pivot FHIR
- le **traitement distribué** et automatisé via **Spark** (médaillons RAW → SILVER → GOLD)
- la **visualisation dynamique** via une application web Next.js
- le **contrôle d'accès** par rôles (ADMIN / MEDECIN)

---

## 🏗️ Architecture

Architecture **Medallion** sur cluster Hadoop/Hive :

```
MAVIS (PostgreSQL, SSH tunnel) ─┐
                                ├─> RAW ──> SILVER (FHIR, 4 entités) ──> GOLD ──> API Flask ──> Web Next.js
MMT_DB (PostgreSQL local) ──────┘          (patient/encounter/condition/observation)       (D3.js)
```

- **RAW** : extraction PostgreSQL → Parquet HDFS + tables Hive externes, rapport `extract_raw_report.json`
- **SILVER** : 4 tables harmonisées FHIR (`datalake_silver.*_fhir`), genre normalisé, flag `is_duplicate`
- **GOLD** : table agrégée `datalake_gold.patient_events_gold` (18 colonnes) servant à l'API et à la visualisation

Détails : [`PIPELINE.md`](./PIPELINE.md), [`CAHIER_DE_CHARGE.md`](./CAHIER_DE_CHARGE.md), [`SUIVI_AVANCEMENT.md`](./SUIVI_AVANCEMENT.md).

---

## 🧱 Technologies utilisées

| Catégorie     | Technologies / Outils                                      |
|---------------|------------------------------------------------------------|
| 🖥️ Frontend    | Next.js 15 (App Router), React 19, TypeScript, Tailwind 4, shadcn/ui, **D3.js 7** |
| 🔐 Auth        | NextAuth.js 4 (JWT) + Prisma 6, rôles ADMIN / MEDECIN       |
| 🔄 API         | **Flask** (Python) + PySpark, port 5000, CORS frontend       |
| 🏗️ Big Data   | Apache Spark 3.4.2, Apache Hive 3.1.3, Hadoop 3.3.6 (Java 8) |
| 🗄️ BDD         | PostgreSQL (application Prisma `datalake_user_db` + sources) |
| 🖥️ VM / Provision | Vagrant, **VirtualBox** (ubuntu/focal64, 8 Go)            |
| 🌐 Réseau      | SSH tunnel (MAVIS 102.16.7.154:8090), connexions JDBC       |

---

## 📦 Installation rapide

```bash
# 1. Copier la config des sources et renseigner les identifiants
cp provision/config/data_sources.example.json provision/config/data_sources.json

# 2. Démarrer la VM et les services Big Data (HDFS → YARN → metastore 9083 → HiveServer2 10000)
vagrant up && vagrant ssh
start-dfs.sh && start-yarn.sh

# 3. Lancer le pipeline ELT (4 étapes, arrêt sur erreur)
bash provision/scripts/run_pipeline.sh

# 4. API Flask (dans la VM)
python -m provision.api.hive_api

# 5. Application web (hôte Windows)
cd visualisation_app && npm install && npx prisma migrate deploy && npx prisma db seed && npm run dev
```

> `provision/config/data_sources.json`, `provision/metadata/` et `.ai_context/` ne sont **pas** commités (secrets et artefacts générés — voir `.gitignore`).

---

## 📆 Suivi et planification

📄 **Timesheet** : [Google Sheets](https://docs.google.com/spreadsheets/d/1JWz_dfxnkArTi9TRiZZPBILCvF8YHNExeXLZ4VoAGos/edit?gid=484971601#gid=484971601)
📅 **Diagramme de Gantt** : [Google Sheets](https://docs.google.com/spreadsheets/d/1z16lRxS4UNZ_0dSJzX2hVAvIBH-Qd9ygO6pLdOZd554/edit?gid=1330547112#gid=1330547112)
📊 **Slide d'informations** : [Google Slides](https://docs.google.com/presentation/d/1pQC7ZwHdDugI1H4Ev_qz6J3Q7Yy6Jy-yy4y1MbC2p_g/edit?slide=id.gc6f9e470d_0_37#slide=id.gc6f9e470d_0_37)
💾 **Export VM `.box`** : à venir

---

## 📋 État d'avancement

**~85 % du MVP réalisé** (détails : [`SUIVI_AVANCEMENT.md`](./SUIVI_AVANCEMENT.md), incidents : [`LOG.md`](./LOG.md)).

| Module | État |
|--------|------|
| 1. Pipeline RAW → SILVER (extraction, mapping FHIR, normalisation) | ✅ Fait |
| 2. Zone GOLD (table agrégée, tranches d'âge) | ✅ Fait (à enrichir) |
| 3. API Flask (9 endpoints RMA) | ✅ Fait |
| 4. Frontend (auth, RBAC, CRUD users, visualisations D3) | ✅ Fait |
| 5. Gouvernance (consentement, audit log) | ⏳ Sprint 3 (à créer) |
| 6. Docker + CI/CD | ⏳ Sprint 4 |
| 7. Tests & finalisation (export `.box`, rapport) | ⏳ Sprint 5 |

---

*Document de référence : [`CAHIER_DE_CHARGE.md`](./CAHIER_DE_CHARGE.md).*
# Module 4 : Backend API — Exposition des Données Spark

## Objectif

Exposer les données du Data Lake (GOLD) au frontend Next.js via une API REST Flask.

**Technologie :** Flask (Python) + PySpark  
**Répertoire :** `provision/api/`  
**Fichier principal :** `provision/api/hive_api.py`

---

## Architecture

```
Frontend (Next.js:3000)
    ↓
Backend API (Flask:5000)   ← hive_api.py
    ↓
Hive (HiveServer2:10000) → HDFS GOLD table
    ↓
datalake_gold.patient_events_gold
```

---

## Table GOLD cible

| Colonne | Type | Description |
|---------|------|-------------|
| patient_uuid | string | UUID patient |
| name | string | Nom |
| gender | string | male/female |
| birth_date | date | Date de naissance |
| age | int | Âge en années |
| age_tranche | string | Tranche d'âge |
| encounter_id | string | ID encounter |
| admission_date | date | Date admission |
| discharge_date | date | Date sortie |
| visit_type | string | Type de visite |
| diagnosis_code | string | Code CIM-10 |
| category | string | Catégorie |
| diagnosis | string | Libellé diagnostic |
| mortality | int | 0/1 décès |
| parity | int | Parité |
| gravida | int | Gravida |
| live_births | int | Naissances vivantes |

---

## Endpoints implémentés

### RMA — Endpoints principaux

| Endpoint | Méthode | Description | Source |
|----------|---------|-------------|--------|
| `/rma/last_sync` | GET | Dernière synchro pipeline | metadata JSON |
| `/rma/admissions_summary` | GET | KPIs (total, mortalité infantile, maternelle) | GOLD |
| `/rma/top_diagnostics` | GET | Top N diagnostics | GOLD |
| `/rma/diagnostics_heatmap` | GET | Heatmap par tranches d'âge | GOLD |
| `/rma/diagnostics_list` | GET | Liste paginée diagnostics | GOLD |

### RMA — Endpoints spécifiques

| Endpoint | Méthode | Description | Source |
|----------|---------|-------------|--------|
| `/api/rma/mortality` | GET | Morbidité/mortalité par service | GOLD |
| `/api/rma/maternity` | GET | Accouchements mensuels | GOLD |
| `/api/rma/laboratory` | GET | Activité laboratoire | ⚠️ Non dispo |
| `/api/rma/malaria` | GET | Prise en charge paludisme | ⚠️ Non dispo |

> **Note :** `/api/rma/laboratory` et `/api/rma/malaria` retournent des données vides car ces sources ne sont pas encore dans la table GOLD.

### Paramètres communs

| Param | Défaut | Description |
|-------|--------|-------------|
| `start` | -365j | Date début |
| `end` | aujourd'hui | Date fin |
| `sex` | tous | Filtrage par sexe |
| `limit` | 5 ou 15 | Nombre de résultats |
| `page` | 1 | Pagination |

---

## Statut : ~50% ✅

| Étape | Statut |
|-------|--------|
| Serveur Flask opérationnel | ✅ |
| Connexion PySpark → Hive | ✅ |
| Table GOLD `patient_events_gold` | ✅ |
| Endpoints RMA principaux (5) | ✅ |
| Endpoints RMA spécifiques (2/4) | ✅ |
| CORS configuré | ✅ |
| Authentification JWT | ⏳ À implémenter |
| Laboratory & Malaria endpoints | ⏳ Source externe requise |

---

## Fichiers

- `provision/api/hive_api.py` — API Flask complète
- `provision/metadata/sync_metadata.json` — Métadonnées synchro

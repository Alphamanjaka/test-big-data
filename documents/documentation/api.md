# API

Deux couches d'API complémentaires :

1. **API données** (Flask + PySpark + Hive) — expose la zone **GOLD** du Data Lake.
2. **API gouvernance** (plateforme) — expose maître patients, consentement et audit (lecture).

## 1. API données — Flask (`provision/api/hive_api.py`, port 5000)

```
Frontend (Next.js:3000)
    ↓ HTTP (CORS localhost:3000, 192.168.56.1:3000)
API Flask (5000)  ← PySpark → Hive (HiveServer2:10000) → datalake_gold.patient_events_gold
```

Lancement (VM) : `python -m provision.api.hive_api`. Fallback sur données **mock** si GOLD est vide
(`provision/api/mock_data.py`, flag `"mocked": true`).

### Endpoints

| Endpoint | Donnée | Source |
|---|---|---|
| `GET /rma/last_sync` | Timestamps de synchro pipeline | `sync_metadata.json` (réel) |
| `GET /rma/admissions_summary` | KPIs : total admissions, mortalité infantile/maternelle | GOLD (+mock) |
| `GET /rma/top_diagnostics` | Top N diagnostics CIM-10 | GOLD (+mock) |
| `GET /rma/diagnostics_heatmap` | Heatmap tranches d'âge × diagnostics | GOLD (+mock) |
| `GET /rma/diagnostics_list` | Liste diagnostics paginée | GOLD (+mock) |
| `GET /api/rma/mortality` | Morbidité/mortalité par catégorie | GOLD (+mock) |
| `GET /api/rma/maternity` | Accouchements mensuels (agrégé) | GOLD (+mock) |
| `GET /api/rma/laboratory` | Activité laboratoire | ⚠️ mock uniquement |
| `GET /api/rma/malaria` | Prise en charge paludisme | ⚠️ mock uniquement |
| `GET /api/governance/duplicates` | KPIs déduplication (patients/masters/doublons/méthode) | SILVER patient (+mock) |
| `GET /api/governance/consent` | Consentements purpose-by-purpose | GOLD `patient_consent_gold` (+mock) |

### Paramètres communs

| Param | Défaut | Description |
|---|---|---|
| `start` | -365 j | Date début (YYYY-MM-DD) |
| `end` | aujourd'hui | Date fin |
| `sex` | tous | `male` / `female` |
| `limit` | 5 ou 15 | Nombre max de résultats |
| `page` | 1 | Pagination (`diagnostics_list`) |

Exemple de réponse :

```json
{
  "success": true,
  "filters": { "start": "2025-09-06", "end": "2026-09-06", "sex": null },
  "data": { "total_admissions": 1234, "mortalite_infantile": 3.2, "mortalite_maternelle": 0.85 }
}
```

### Tests

`python -m provision.api.test_api` → **14/14 PASS** attendu.

## 2. API gouvernance — plateforme

API **lecture seule** exposant le PostgreSQL central (master patient, consentement, audit) :

| Endpoint | Rôle |
|---|---|
| `GET /health` | État du service |
| `GET /metrics` | Indicateurs de gouvernance |
| `GET /patients` | Patientes maîtres (les payloads RAW ne sont jamais exposés) |
| `GET /patients/{master_patient_id}` | Détail d'un patient |
| `GET /audit` | Journal des accès (rôle admin requis) |
| `GET /consent` | Consentements d'un patient (selon rôle) |

Sécurité : clés API hachées SHA-256, rôles `admin`/`analyst`/`viewer`, audit systématique de chaque
accès (autorisé ou refusé).

Depuis la fusion (dépôt unique), deux endpoints de gouvernance sont implémentés **dans
`provision/api/hive_api.py`** (un seul service Flask) :
`GET /api/governance/duplicates` (KPIs de déduplication depuis `datalake_silver.patient_fhir`) et
`GET /api/governance/consent` (consentements depuis `datalake_gold.patient_consent_gold`). Les deux
basculent en **fallback mock** (`mock_data.py`) si la donnée est absente ou si le moteur/services Hive
sont indisponibles. Les endpoints FastAPI (`engine/governance`) restent la référence de la plateforme
(PostgreSQL central + clés API).

## 3. Références d'implémentation

| Composant | Fichier |
|---|---|
| API données Flask | `provision/api/hive_api.py`, `mock_data.py`, `test_api.py` |
| Guide API données | provenance `provision/api/README.md` (fusionné ici) |
| Moteur gouvernance (FastAPI/psycopg) | `engine/governance/database.py`, `auth.py`, `consent.py`, `audit.py` |
| Paramètres & exemples RMA | ce document (§1) |

## 4. Limites connues

- Auth JWT côté API Flask : à ajouter (le RBAC web NextAuth n'enchaîne pas l'API).
- `/api/rma/laboratory` et `/api/rma/malaria` : 100 % mock (sources hors GOLD).
- Pas de cache : chaque requête interroge Hive.
- Pas de validation des paramètres (entrées invalides → 500).
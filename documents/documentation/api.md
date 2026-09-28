# API

Deux couches d'API complémentaires :

1. **API indicateurs du warehouse** (Flask + PySpark + Hive) — expose les indicateurs de
   **gouvernance** du Data Lake (déduplication SILVER, consentement GOLD).
2. **API gouvernance** (plateforme) — expose maître patients, consentement et audit (lecture).

## 1. API indicateurs — Flask (`provision/api/hive_api.py`, port 5000)

```
Frontend (Next.js:3000)
    ↓ HTTP (CORS localhost:3000, 192.168.56.1:3000)
API Flask (5000)  ← PySpark → Hive (HiveServer2:10000) → datalake_silver.patient_fhir
                                                       → datalake_gold.patient_consent_gold
```

Lancement (VM) : `python -m provision.api.hive_api`. Fallback sur données **mock** si Spark/Hive
est indisponible ou la table est vide (`provision/api/mock_data.py`, flag `"mocked": true`).

### Endpoints

| Endpoint | Donnée | Source |
|---|---|---|
| `GET /api/governance/duplicates` | KPIs déduplication (patients/masters/doublons/méthode) | SILVER patient (+mock) |
| `GET /api/governance/consent` | Consentements purpose-by-purpose | GOLD `patient_consent_gold` (+mock) |

### Paramètres

| Param | Défaut | Description |
|---|---|---|
| `limit` | 200 | Nombre max de consentements renvoyés (`/api/governance/consent`) |

Exemple de réponse :

```json
{
  "success": true,
  "filters": {},
  "data": {
    "total_patients": 65214,
    "total_masters": 62180,
    "duplicates": 3034,
    "duplicate_rate": 4.65,
    "by_method": {"exact": 1876, "probabilistic": 1158}
  },
  "mocked": true
}
```

Chaque réponse transporte un drapeau `mocked` : `true` quand l'API a basculé sur le jeu de
démonstration, `false` sinon. Le front lit ce drapeau et affiche un bandeau « données de
démonstration » — il ne l'infère jamais lui-même.

### Tests

`python -m provision.api.test_api` → **3/3 PASS** attendu.

## 2. API gouvernance — FastAPI (`engine/governance/app.py`, port 8000)

```
Frontend (Next.js:3000)  ou  curl / client
    ↓ HTTP (Authorization: Bearer <api_key>)
FastAPI Gouvernance (8000)  ← psycopg → PostgreSQL central (master_patient, consent, access_audit)
```

Lancement (hôte Windows) : `uvicorn engine.governance.app:app --port 8000`.
Auth : clés API (Bearer token, SHA-256 côté serveur).

### Endpoints

| Endpoint | Description | Rôle requis |
|---|---|---|
| `GET /health` | Liveness probe | — |
| `GET /metrics` | KPIs déduplication (total, doublons, taux) | admin, analyst |
| `GET /patients` | Liste master patients | admin, analyst |
| `GET /patients/{master_patient_id}` | Détail d'un master patient | admin, analyst |
| `GET /audit` | Journal d'accès (200 dernières lignes) | admin |
| `GET /consent` | Liste consentements | admin, analyst |
| `GET /consent/{master_patient_id}` | Consentements d'un patient | admin, analyst |
| `POST /consent` | Créer un consentement | admin |

API **lecture seule** exposant le PostgreSQL central (master patient, consentement, audit) :
les payloads RAW ne sont jamais exposés.

Sécurité : clés API hachées SHA-256, rôles `admin`/`analyst`/`viewer`, audit systématique de chaque
accès (autorisé ou refusé).

Depuis la fusion (dépôt unique), les endpoints de gouvernance lisibles en lecture sont implémentés
**dans `provision/api/hive_api.py`** (un seul service Flask) :
`GET /api/governance/duplicates` (KPIs de déduplication depuis `datalake_silver.patient_fhir`) et
`GET /api/governance/consent` (consentements depuis `datalake_gold.patient_consent_gold`). Les deux
basculent en **fallback mock** (`mock_data.py`) si la donnée est absente ou si les services Hive
sont indisponibles. Les endpoints FastAPI (`engine/governance`) restent la référence de la plateforme
(PostgreSQL central + clés API).

## 3. Références d'implémentation

| Composant | Fichier |
|---|---|
| API indicateurs Flask | `provision/api/hive_api.py`, `mock_data.py`, `test_api.py` |
| Guide API indicateurs | provenance `provision/api/README.md` (fusionné ici) |
| Moteur gouvernance (FastAPI/psycopg) | `engine/governance/database.py`, `auth.py`, `consent.py`, `audit.py` |
| Paramètres & exemples | ce document (§1) |

## 4. Limites connues

- Auth JWT côté API Flask : à ajouter (le RBAC web NextAuth n'enchaîne pas l'API).
- Pas de cache : chaque requête interroge Hive.
- Pas de validation des paramètres (entrées invalides → 500).
# API Flask — Gouvernance et exposition des données GOLD

## Présentation

L'API Flask expose les indicateurs de **gouvernance** du Data Lake (déduplication,
consentement purpose-by-purpose) au frontend Next.js via des endpoints REST.

```
Frontend (Next.js:3000)
    ↓
Backend API (Flask:5000)       ← ce service
    ↓
PySpark → Hive (HiveServer2:10000)
    ↓
HDFS SILVER / GOLD (patient_fhir, patient_consent_gold)
```

**Technologies :** Flask + PySpark + Hive  
**Port :** 5000

---

## Prérequis

1. **Pipeline ELT exécuté** — les tables `datalake_silver.patient_fhir` et
   `datalake_gold.patient_consent_gold` doivent exister
2. **HiveServer2 + Metastore actifs** dans la VM
3. **Virtualenv** `~/api-venv` avec les packages installés (automatique via `vagrant provision`)

Vérifier une table :

```bash
vagrant ssh
beeline -u jdbc:hive2://localhost:10000 -n vagrant \
  -e "SELECT count(*) FROM datalake_silver.patient_fhir;"
```

Vérifier le venv :

```bash
vagrant ssh
source ~/api-venv/bin/activate
python -c "import flask; print(flask.__version__)"
```

---

## Lancement

### Dans la VM

```bash
vagrant ssh
cd ~/datalake-final
python -m provision.api.hive_api
```

Le venv `~/api-venv` est automatiquement activé au login.

L'API démarre sur `http://0.0.0.0:5000`.

### Vérification rapide

```bash
curl http://localhost:5000/api/governance/duplicates
curl http://localhost:5000/api/governance/consent
```

---

## Endpoints

### Gouvernance

| Méthode | Endpoint                    | Description                                    | Params  |
| ------- | --------------------------- | ---------------------------------------------- | ------- |
| GET     | `/api/governance/duplicates` | KPIs déduplication (patients/masters/doublons) | —       |
| GET     | `/api/governance/consent`    | Consentements purpose-by-purpose               | `limit` |

> L'API gouvernance **plateforme** (FastAPI, port 8000, hôte Windows) est documentée dans
> [`documents/documentation/api.md`](../../documents/documentation/api.md).

### Exemple de réponse

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

Chaque réponse transporte un drapeau `mocked` : `true` quand l'API a basculé sur
le jeu de démonstration (`mock_data.py`) car Hive/Spark est indisponible ou la
table est vide, `false` sinon.

---

## Tests

Lancer la suite de tests (endpoints gouvernance) :

```bash
# Depuis la VM
cd ~/datalake-final
python -m provision.api.test_api

# Ou depuis Windows (port 5000 forwardé)
python provision/api/test_api.py
```

Sortie :

```
✅ PASS /api/governance/duplicates
✅ PASS /api/governance/consent
...
RÉSULTAT : 3/3 PASS — 0 FAIL — 0 SKIP
```

---

## Structure du code

```
provision/api/
├── hive_api.py      ← API Flask principale (endpoints + requêtes PySpark)
├── mock_data.py     ← Jeu de démonstration (fallback gouvernance)
├── test_api.py      ← Tests automatisés des endpoints
└── README.md        ← Ce fichier
```

---

## Fichiers associés

| Fichier                                 | Rôle                                         |
| --------------------------------------- | -------------------------------------------- |
| `provision/scripts/run_pipeline.sh`     | Pipeline ELT (création des tables SILVER/GOLD) |
| `provision/metadata/sync_metadata.json` | Métadonnées de synchronisation               |
| `documents/documentation/api.md`        | Documentation de l'API plateforme (FastAPI)  |

---

## Limites connues

| Problème                         | Détail                                | Priorité |
| -------------------------------- | ------------------------------------- | -------- |
| Auth JWT non implémentée         | Tous les endpoints sont ouverts       | Haute    |
| Pas de cache                     | Chaque requête interroge Hive         | Basse    |
| Pas de validation des paramètres | Paramètres invalides → erreurs 500    | Basse    |
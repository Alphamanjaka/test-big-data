# API Flask — DataLake Mavis

## Présentation

L'API Flask expose les données de la couche **GOLD** du Data Lake au frontend Next.js via des endpoints REST.

```
Frontend (Next.js:3000)
    ↓
Backend API (Flask:5000)       ← ce service
    ↓
PySpark → Hive (HiveServer2:10000)
    ↓
HDFS GOLD (datalake_gold.patient_events_gold)
```

**Technologies :** Flask + PySpark + Hive  
**Port :** 5000

---

## Prérequis

1. **Pipeline ELT exécuté** — la table `datalake_gold.patient_events_gold` doit exister
2. **HiveServer2 + Metastore actifs** dans la VM
3. **Virtualenv** `~/api-venv` avec les packages installés (automatique via `vagrant provision`)

Vérifier la table GOLD :

```bash
vagrant ssh
beeline -u jdbc:hive2://localhost:10000 -n vagrant \
  -e "SELECT count(*) FROM datalake_gold.patient_events_gold;"
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
curl http://localhost:5000/rma/last_sync
curl http://localhost:5000/rma/admissions_summary
```

---

## Quick Startup Health Check

Avant de lancer un pipeline ou un test complet, vérifiez rapidement que MAVIS est démarré et accessible.

### Usage

```bash
# Depuis le répertoire racine du projet
bash provision/test_startup.sh                    # Mode silencieux (rapide)
bash provision/test_startup.sh --verbose          # Mode détaillé + logs
bash provision/test_startup.sh --report           # Sauvegarde rapport JSON
bash provision/test_startup.sh --verbose --report # Tous les détails + rapport
```

### Checks effectués

| Check                          | Objectif                                      | Timeout | Priorité  |
| ------------------------------ | --------------------------------------------- | ------- | --------- |
| **Vagrant VM Status**          | Vérifie que la VM est en cours d'exécution    | N/A     | CRITIQUE  |
| **HiveServer2 (Beeline)**      | Teste la connexion HiveServer2 via port 10000 | 5s      | CRITIQUE  |
| **Flask API (/rma/last_sync)** | Vérifie que l'API Flask répond (port 5000)    | 5s      | CRITIQUE  |
| **Metadata Freshness**         | Vérifie que `sync_metadata.json` est à jour   | N/A     | IMPORTANT |
| **GOLD Table Access**          | Requête GOLD pour vérifier l'accessibilité    | 5s      | OPTIONNEL |

### Exemple de sortie

```
══════════════════════════════════════════════════════════════════
  MAVIS Database Startup Health Check
══════════════════════════════════════════════════════════════════

  Vagrant VM Status                          ✓ PASS
  HiveServer2 (Beeline)                      ✓ PASS
  Flask API (/rma/last_sync)                 ✓ PASS
  Metadata Freshness                         ✓ PASS
  GOLD Table Data Access                     ✓ PASS

──────────────────────────────────────────────────────────────────
✓ SUCCESS: All checks passed!
  MAVIS database is running and accessible.
  Results: 5/5 checks passed
──────────────────────────────────────────────────────────────────
```

### Codes de sortie

- **0** → Tous les checks passent (MAVIS prêt pour une utilisation)
- **1** → Au moins un check échoue (MAVIS pas prêt)

Utilisez-le dans des scripts d'orchestration :

```bash
bash provision/test_startup.sh || { echo "MAVIS not ready"; exit 1; }
bash provision/scripts/run_pipeline.sh  # Exécuter seulement si MAVIS est sain
```

### Reports (mode --report)

Les rapports JSON sont sauvegardés dans `provision/reports/startup_test_*.json` :

```json
{
  "timestamp": "2026-08-31T10:05:18Z",
  "hostname": "my-laptop",
  "checks_run": 5,
  "checks_passed": 5,
  "checks_failed": 0,
  "status": "HEALTHY"
}
```

---

## Endpoints

### RMA — Endpoints principaux

| Méthode | Endpoint                   | Description                                                        | Params                                 |
| ------- | -------------------------- | ------------------------------------------------------------------ | -------------------------------------- |
| GET     | `/rma/last_sync`           | Dernière synchro pipeline                                          | —                                      |
| GET     | `/rma/admissions_summary`  | KPIs : total admissions, mortalité infantile, mortalité maternelle | `start`, `end`, `sex`                  |
| GET     | `/rma/top_diagnostics`     | Top N diagnostics par fréquence                                    | `limit`, `start`, `end`, `sex`         |
| GET     | `/rma/diagnostics_heatmap` | Diagnostics avec répartition par tranches d'âge                    | `limit`, `start`, `end`, `sex`         |
| GET     | `/rma/diagnostics_list`    | Liste paginée des diagnostics                                      | `page`, `limit`, `start`, `end`, `sex` |

### RMA — Endpoints spécifiques

| Méthode | Endpoint              | Description                       | Params                |
| ------- | --------------------- | --------------------------------- | --------------------- |
| GET     | `/api/rma/mortality`  | Morbidité/mortalité par catégorie | `start`, `end`, `sex` |
| GET     | `/api/rma/maternity`  | Accouchements mensuels (agrégé)   | `start`, `end`, `sex` |
| GET     | `/api/rma/laboratory` | Activité laboratoire              | —                     |
| GET     | `/api/rma/malaria`    | Prise en charge paludisme         | —                     |

> `/api/rma/laboratory` et `/api/rma/malaria` retournent des données vides pour l'instant (sources hors GOLD).

### Paramètres communs

| Param   | Défaut      | Description                       |
| ------- | ----------- | --------------------------------- |
| `start` | -365j       | Date début (format YYYY-MM-DD)    |
| `end`   | aujourd'hui | Date fin                          |
| `sex`   | tous        | `male` ou `female`                |
| `limit` | 5 ou 15     | Nombre max de résultats           |
| `page`  | 1           | Numéro de page (diagnostics_list) |

### Exemple de réponse

```json
{
  "success": true,
  "filters": {
    "start": "2025-08-26",
    "end": "2026-08-26",
    "sex": null
  },
  "data": {
    "total_admissions": 1234,
    "mortalite_infantile": 3.2,
    "mortalite_maternelle": 0.85
  }
}
```

---

## Tests

Lancer la suite de tests (14 tests, tous les endpoints, dont gouvernance) :

```bash
# Depuis la VM
cd ~/datalake-final
python -m provision.api.test_api

# Ou depuis Windows (port 5000 forwardé)
python provision/api/test_api.py
```

Sortie :

```
✅ PASS /rma/last_sync
✅ PASS /rma/admissions_summary
✅ PASS /rma/top_diagnostics
...
RÉSULTAT : 14/14 PASS — 0 FAIL — 0 SKIP
```

---

## Structure du code

```
provision/api/
├── hive_api.py      ← API Flask principale (endpoints + requêtes PySpark)
├── test_api.py      ← Tests automatisés des endpoints
└── README.md        ← Ce fichier
```

---

## Fichiers associés

| Fichier                                 | Rôle                                         |
| --------------------------------------- | -------------------------------------------- |
| `provision/scripts/run_pipeline.sh`     | Pipeline ELT (création de la table GOLD)     |
| `provision/metadata/sync_metadata.json` | Métadonnées de synchronisation               |
| `MODULE_4_BACKEND_API.md`               | Documentation technique du module            |
| `visualisation_app/src/lib/mockData.ts` | Données fictives (attente connexion backend) |

---

## Limites connues

| Problème                         | Détail                                 | Priorité |
| -------------------------------- | -------------------------------------- | -------- |
| Auth JWT non implémentée         | Tous les endpoints sont ouverts        | Haute    |
| `/api/rma/laboratory`            | Données vides — source externe requise | Moyenne  |
| `/api/rma/malaria`               | Données vides — source externe requise | Moyenne  |
| Pas de cache                     | Chaque requête interroge Hive          | Basse    |
| Pas de validation des paramètres | Paramètres invalides → erreurs 500     | Basse    |

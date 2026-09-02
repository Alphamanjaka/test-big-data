# Patient Data Platform

MVP de centralisation de donnees patients synthetiques.

## Demarrage

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -e ".[test]"
.venv\Scripts\python -m pytest -q
```

Le pipeline local lit les trois sources CSV de `data/raw`, standardise les patients et produit une identity map explicable. PostgreSQL est prepare par `sql/schema.sql`; aucun secret ni aucune vraie donnee patient ne doit etre ajoute au depot.

Les événements d'exécution sont ajoutés en temps réel dans `logs/runtime.log` et recopiés dans `LOGS.md` pour l'audit du projet.

Quand la base `patient_plateform` existe, le chargement se lance avec :

```powershell
.venv\Scripts\python load_to_postgres.py
```

La connexion utilise `DATABASE_URL` depuis `.env`; cette valeur ne doit jamais être commitée.

## Dashboard

Le dashboard de gouvernance se lance avec :

```powershell
.venv\Scripts\python dashboard_server.py
```

Il est ensuite disponible sur `http://localhost:8501`.

## API

L'API en lecture seule se lance avec :

```powershell
.venv\Scripts\python api_server.py
```

Endpoints disponibles : `/health`, `/metrics`, `/patients` et `/patients/{master_patient_id}`. Les payloads RAW ne sont pas exposés par l'API. Les lignes RAW sont conservées comme historique de chaque extraction.

## Structure

- `src/patient_platform/extract/`: lecture des sources
- `src/patient_platform/transform/`: modele canonique et standardisation
- `src/patient_platform/deduplication/`: matching exact et probabiliste
- `src/patient_platform/load/`: chargement RAW, master et identity map vers PostgreSQL
- `src/patient_platform/api/`: API FastAPI en lecture seule
- `src/patient_platform/dashboard/`: dashboard Streamlit en lecture seule
- `tests/`: cas critiques du MVP

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

## Structure

- `src/patient_platform/extract/`: lecture des sources
- `src/patient_platform/transform/`: modele canonique et standardisation
- `src/patient_platform/deduplication/`: matching exact et probabiliste
- `src/patient_platform/load/`: futur chargement PostgreSQL
- `src/patient_platform/api/`: futurs endpoints
- `src/patient_platform/dashboard/`: futur dashboard
- `tests/`: cas critiques du MVP

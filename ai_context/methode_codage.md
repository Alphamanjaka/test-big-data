# Méthode de codage

Code clair, maintenable, démontrable en soutenance.

## Règles
- Simplicité > complexité inutile.
- Couches séparées : extraction, transformation, déduplication, chargement, dashboard, gouvernance.
- Noms explicites (fichiers, fonctions, variables).
- Pas de variables magiques → constantes nommées.
- Fonctions courtes, cohérentes, testables.
- Transformations traçables (chaque étape expliquable).
- Documenter les hypothèses métier.

## Architecture
`extract/` · `transform/` (mapping, standardisation, nettoyage) · `deduplication/` (exact + probabiliste) · `load/` (PostgreSQL) · `api/` · `dashboard/` · `tests/`

## Bonnes pratiques
- Python modulaire. Pandas / SQLAlchemy / FastAPI / Streamlit selon besoin.
- Erreurs gérées proprement sans masquer la cause.
- Logs utiles, sans données sensibles.
- Séparer UI / logique métier / extraction.

## Contrôle qualité
- Tests : doublons, valeurs nulles, formats hétérogènes.
- Score de matching toujours explicite.
- Traçabilité conservée : source → canonique → master patient.

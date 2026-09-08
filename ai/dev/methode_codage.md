# Méthode de codage

Source : `ai_context/methode_codage.md` (test_bigdata), appliquée à tout `projet/code-source/`.

Code clair, maintenable, **démontrable en soutenance**.

## Règles

- Simplicité > complexité inutile.
- Couches séparées : extraction, transformation/règles canoniques, déduplication, chargement, gouvernance, API, dashboard, évaluation.
- Noms explicites (fichiers, fonctions, variables).
- Pas de variables magiques → constantes nommées.
- Fonctions courtes, cohérentes, testables.
- Transformations traçables (chaque étape expliquable).
- Documenter les hypothèses métier.

## Architecture du code

```
engine/identity/    canonical (mapping/standardisation) → matcher (exact+probabiliste) → spark_dedup
engine/governance/  database · auth (clés SHA-256) · consent · audit
provision/          VM + ELT Big Data + API Flask (schéma FHIR, GOLD)
evaluation/         générateur + ground truth + évaluateur
tests/              cas critiques (matcher, consentement)
sql/schema.sql      PostgreSQL central
```

## Bonnes pratiques

- Python modulaire. Pandas / PySpark / SQLAlchemy/psycopg / Flask / FastAPI / Streamlit selon besoin.
- Erreurs gérées proprement **sans masquer la cause**.
- Logs utiles, **sans données sensibles**.
- Séparer UI / logique métier / extraction.
- Compatibilité Python 3.8 (VM) : `from __future__ import annotations`, éviter les f-strings avancées
  non supportées, RapidFuzz au lieu de libs ML.

## Contrôle qualité

- Tests : doublons, valeurs nulles, formats hétérogènes, parité Pandas/Spark.
- Score de matching **toujours explicite** (méthode + score + seuil).
- Traçabilité conservée : `source → canonique → master patient`.
- Validation : `pytest` (tests moteur + consentement), évaluateur ground-truth, API données 12/12.
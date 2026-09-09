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
- Validation : `pytest` moteur + consentement + canonique (23/23 documenté), évaluateur ground-truth, API données
  (14/14 documenté).

## Pyramide de tests et critères de validation

- **Unitaires** : canonique, normalisation, matching exact/probabiliste, consentement et contrôles de
  rôles ; inclure valeurs manquantes, formats hétérogènes et erreurs attendues.
- **Intégration** : flux RAW → SILVER → GOLD, schémas Hive/PostgreSQL, idempotence, audit après accès
  autorisé ou refusé et contrôle des réponses API.
- **Système** : démarrage des composants disponibles, pipeline complet, parité Pandas/Spark et
  évaluation ground-truth.
- **Sécurité et non-régression** : aucun secret dans les logs/réponses, refus sans consentement,
  refus pour rôle insuffisant, et absence de régression des schémas ou des valeurs métier.

Pour chaque validation, indiquer la commande, le périmètre, le résultat observé et la date. Distinguer
les tests réellement exécutés des tests prévus, impossibles ou non applicables. Ne jamais déclarer une
fonctionnalité testée sur la seule base d'une lecture de code.

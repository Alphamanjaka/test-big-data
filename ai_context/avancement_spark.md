# Avancement Niveau 2 — Apache Spark

Dernière mise à jour : 2026-09-02

## Prérequis (MVP validé)

| # | Critère | État |
|---|---|---|
| P1 | Pipeline Pandas bout en bout | Terminé |
| P2 | Déduplication Jean Rakoto validée | Terminé |
| P3 | PostgreSQL central alimenté | Terminé |
| P4 | Dashboard opérationnel | Terminé |
| P5 | Tests MVP passés (14/14) | Terminé |

> Prérequis validés — le Niveau 2 peut démarrer.

## Phase 1 — Environnement

| # | Tâche | État |
|---|---|---|
| S1.1 | Installer PySpark / vérifier environnement | En cours |
| S1.2 | Session Spark de test | À faire |
| S1.3 | Lecture CSV en Spark | À faire |
| S1.4 | Benchmark Pandas vs Spark | À faire |

> Note : `pyspark==4.2.0` est dans `requirements.txt` mais absent de `pyproject.toml` et jamais importé. Il faut l'ajouter aux dépendances officielles et valider une session Spark.

## Phase 2 — Extraction

| # | Tâche | État |
|---|---|---|
| S2.1 | Adapter CSVExtractor → Spark DataFrame | À faire |
| S2.2 | SparkExtractor (abstrait) | À faire |
| S2.3 | Valider extraction des 3 sources | À faire |

## Phase 3 — Transformation

| # | Tâche | État |
|---|---|---|
| S3.1 | Mapping canonique en Spark | À faire |
| S3.2 | Standardisation en Spark | À faire |
| S3.3 | Nettoyage en Spark | À faire |
| S3.4 | Validation en Spark | À faire |

## Phase 4 — Déduplication

| # | Tâche | État |
|---|---|---|
| S4.1 | Blocking en Spark | À faire |
| S4.2 | Exact matching en Spark | À faire |
| S4.3 | Fuzzy matching en Spark | À faire |
| S4.4 | Valider cas Jean Rakoto en Spark | À faire |

## Phase 5 — Chargement

| # | Tâche | État |
|---|---|---|
| S5.1 | Chargement PostgreSQL (Spark) | À faire |
| S5.2 | Valider intégrité données | À faire |
| S5.3 | Comparer résultats Pandas vs Spark | À faire |

## État global

```
Prérequis ████████ 100%   S1 ░░░░ 5%   S2 ░░░░0%   S3 ░░░░0%   S4 ░░░░0%   S5 ░░░░0%   TOTAL ░░░░ 17%
```

## Critères de succès

| Critère | Cible |
|---|---|
| Compatibilité résultats | 100% identique au MVP |
| Performance | Amélioration mesurable |
| Scalabilité | Volumes > RAM locale acceptés |
| Traçabilité | Même niveau de logs que le MVP |

## Décisions techniques

| Décision | Choix | Justification |
|---|---|---|
| Framework | PySpark | Interface Python |
| Session | Local (pas de cluster) | MVP Spark |
| Chargement | JDBC → PostgreSQL | Compatible MVP |

## Hypothèses / Blocages / Journal

- **Hypothèses** :
  - HS1 : PySpark en mode local suffisant pour le Niveau 2
  - HS2 : Résultats Pandas comme baseline de référence
  - HS3 : Même schéma PostgreSQL que le MVP
- **Blocages** : pyspark installé mais pas intégré au projet (`pyproject.toml` ne le liste pas)
- **Journal** :
  - 2026-09-02 | Prérequis | MVP validé | P1-P5 terminés, Niveau 2 débloqué
  - 2026-09-02 | S1.1 | pyspark==4.2.0 dans requirements.txt | Présent mais absent de pyproject.toml, jamais importé — à intégrer officiellement

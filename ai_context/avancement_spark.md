# Avancement Niveau 2 — Apache Spark

## Prérequis (MVP validé)

| # | Critère | État |
|---|---|---|
| P1 | Pipeline Pandas bout en bout | À faire |
| P2 | Déduplication Jean Rakoto validée | À faire |
| P3 | PostgreSQL central alimenté | À faire |
| P4 | Dashboard opérationnel | À faire |
| P5 | Tests MVP passés | À faire |

> Ne pas commencer le Niveau 2 tant que P1-P5 ne sont pas validés.

## Phase 1 — Environnement

| # | Tâche | État |
|---|---|---|
| S1.1 | Installer PySpark / vérifier environnement | À faire |
| S1.2 | Session Spark de test | À faire |
| S1.3 | Lecture CSV en Spark | À faire |
| S1.4 | Benchmark Pandas vs Spark | À faire |

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
P1 ░░░░0%   P2 ░░░░0%   P3 ░░░░0%   P4 ░░░░0%   P5 ░░░░0%   TOTAL ░░░░0%
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
- Hypothèses : HS1-HS3
- Blocages : BS1 (vide)
- Journal : (date | phase | action | résultat)

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
| S1.1 | Installer PySpark / vérifier environnement | Terminé |
| S1.2 | Session Spark de test | Terminé |
| S1.3 | Lecture CSV en Spark | Terminé |
| S1.4 | Benchmark Pandas vs Spark | Terminé |

> Phase 1 complète. `src/patient_platform/spark/session.py` normalise JAVA_HOME
> (correction du `\bin` en trop) et fournit une session locale partagée ;
> `SparkCSVExtractor` lit les CSV avec `source_system`/`source_file`.

## Phase 2 — Extraction

| # | Tâche | État |
|---|---|---|
| S2.1 | Adapter CSVExtractor → Spark DataFrame | Terminé |
| S2.2 | SparkExtractor (abstrait) | Terminé |
| S2.3 | Valider extraction des 3 sources | Terminé |

> `SparkExtractor` (ABC) + `SparkCSVExtractor`. Validation : colonnes et comptes
> identiques à Pandas (36 lignes), `source_system` correct.

## Phase 3 — Transformation

| # | Tâche | État |
|---|---|---|
| S3.1 | Mapping canonique en Spark | Terminé |
| S3.2 | Standardisation en Spark | Terminé |
| S3.3 | Nettoyage en Spark | Terminé |
| S3.4 | Validation en Spark | Terminé |

> `spark/transform.py` réutilise les fonctions N1 (`_text`, `_phone`, `_birth_date`)
> via UDFs : transformation strictement identique. 18 patients canoniques validés
> champ par champ contre le MVP.

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
Prérequis ████████ 100%   S1 ████████ 100%   S2 ████████ 100%   S3 ████████ 100%   S4 ░░░░0%   S5 ░░░░0%   TOTAL ░░░░░ 60%
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
- **Blocages** : levés — `JAVA_HOME` contenait `\bin` en trop et bloquait tout lancement Spark ; corrigé au niveau utilisateur et normalisé dans `spark/session.py`. Avertissements winutils/native-hadoop non bloquants en mode local.
- **Journal** :
  - 2026-09-02 | Prérequis | MVP validé | P1-P5 terminés, Niveau 2 débloqué
  - 2026-09-02 | S1.1 | pyspark>=4.0 ajouté à pyproject.toml | Dépendance officielle intégrée
  - 2026-09-02 | S1.2 | Session Spark validée | Spark 4.2.0, master local[2], range count OK
  - 2026-09-02 | S1.3 | Lecture CSV en Spark | 18 patients + 18 métier = MVP, via SparkCSVExtractor
  - 2026-09-02 | S1.4 | Benchmark Pandas vs Spark | Pandas ~1-2ms vs Spark ~0.4-4s à 6 lignes : overhead JVM domine sur petit volume, Spark se justifie sur gros volume
  - 2026-09-02 | S2.1-S2.3 | Extraction Spark | SparkExtractor abstrait + SparkCSVExtractor, 36 lignes cohérentes avec Pandas
  - 2026-09-02 | S3.1-S3.4 | Transformation Spark | UDFs des fonctions N1, 18 patients exactement identiques au MVP. Bloqueurs levés : PYSPARK_PYTHON (stub MS Store) + inferSchema convertissant les dates

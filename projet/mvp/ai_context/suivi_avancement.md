# Instruction de suivi d'avancement

Projet sur 3 niveaux, strictement progressifs : MVP → Spark → Big Data.

## Fichiers de sortie

| Niveau | Fichier |
|---|---|
| 1 MVP | `SUIVI-AVANCEMENT.md` + `ai_context/avancement_mvp.md` |
| 2 Spark | `ai_context/avancement_spark.md` |
| 3 Big Data | `ai_context/avancement_bigdata.md` |

Ne pas créer d'autres fichiers de suivi.

## Règles

- Un niveau n'est démarrable que si le précédent est validé.
- Chaque fichier de niveau suit le même squelette : Prérequis, Tâches (tableau # / tâche / état), État global (barres), Critères de succès, Décisions, Hypothèses / Blocages / Journal.
- Ne pas mélanger les étapes de niveaux différents.
- Pas d'avancement dans une étape sans validation de la précédente.
- Documenter hypothèses et blocages.

## États

À faire / En cours / Terminé / Bloqué

## Checklist MVP (Niveau 1)

Sources connectées · Extraction · Mapping/standardisation · Nettoyage · Déduplication expl. · Identity mapping · PostgreSQL · Dashboard · Cas démo

## Checklist Spark (Niveau 2)

PySpark + session · Extraction DataFrame · Transformation = MVP · Déduplication Jean Rakoto · Chargement PG · Résultats = Pandas · Performance

## Checklist Big Data (Niveau 3)

Hadoop (HDFS+Hive+Spark) · Data Lake /raw/staging/processed/curated · Tables Hive · Pipeline distribué bout en bout · Résultats cohérents 1-2 · Démo 3 niveaux

## Bonnes pratiques

- Progression lisible pour la soutenance.
- Vérifier avant de déclarer une étape terminée.
- Justifier chaque finalisation (test/résultat/trace).
- Mettre à jour le fichier du niveau concerné dès qu'une action est terminée.

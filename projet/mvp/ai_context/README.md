# Contexte IA

Ce dossier contient les consignes techniques et opérationnelles que les IA doivent suivre pour ce projet.

## Fichiers

- methode_codage.md : règles de conception, architecture et qualité du code
- security.md : protection des données, consentement et gouvernance
- suivi_avancement.md : méthode de suivi de progression et validation des tâches
- logs.md : politique de journalisation, audit et traçabilité
- avancement_mvp.md : suivi détaillé du Niveau 1 (MVP)
- avancement_spark.md : suivi détaillé du Niveau 2 (Apache Spark)
- avancement_bigdata.md : suivi détaillé du Niveau 3 (Architecture Big Data)

## Règle principale

Les IA doivent respecter la logique du projet :

- MVP de centralisation de données patients ;
- sources hétérogènes ;
- données synthétiques uniquement ;
- traçabilité et consentement obligatoires ;
- logique de déduplication explicable ;
- démonstration prioritaire sur robustesse et clarté.

## Niveaux de développement

Le projet évolue en 3 niveaux, chacun suivi dans un fichier dédié :

| Niveau | Description | Techno | Suivi |
|---|---|---|---|
| 1 | MVP fonctionnel | CSV + Pandas + PostgreSQL | avancement_mvp.md |
| 2 | Scalabilité | PySpark distribué | avancement_spark.md |
| 3 | Big Data complète | Data Lake + HDFS + Hive + Spark | avancement_bigdata.md

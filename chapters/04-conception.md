# Chapitre 4 — Conception

> **Statut** : à rédiger

## Objectif

Décrire l'architecture de la plateforme : modèle canonique (CanonicalPatient), pipeline
ETL (extraction, mapping, standardisation, nettoyage, validation), déduplication
explicable (blocking, exact, fuzzy, seuils), schéma PostgreSQL (RAW, master, identity
mapping, relations métier, gouvernance) et montée en charge vers Spark.

## Notes / TODO

- [ ] Architecture globale (MVP Pandas puis Spark)
- [ ] Modèle canonique et mappings des sources
- [ ] Entity Resolution : blocking, similarité, seuils (≥90 auto / 70-90 revue / <70 non)
- [ ] Modèle de données PostgreSQL et idempotence
- [ ] Gouvernance : rôles, clés API, audit, consentement
- [ ] Niveau 2 : PySpark (session, DataFrame, UDF) ; Niveau 3 : Data Lake/HDFS/Hive
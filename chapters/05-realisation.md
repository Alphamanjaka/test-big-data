# Chapitre 5 — Réalisation

> **Statut** : à rédiger

## Objectif

Restituer l'implémentation effective : générateur de données, pipeline de traitement,
entity resolution, interface de chargement PostgreSQL, API et dashboard Streamlit,
puis transposition en Spark et architecture big data.

## Notes / TODO

- [ ] Générateur : master patients, variation par source, vocabularies hétérogènes
- [ ] Pipeline ETL : extraction, standardisation, déduplication, identity mapping
- [ ] Chargement PostgreSQL (ON CONFLICT, idempotence) et schéma
- [ ] Gouvernance : init_governance, API FastAPI, Streamlit
- [ ] Niveau 2 : Spark (extraction, UDF de transformation, déduplication, chargement)
- [ ] Niveau 3 : Data Lake, Hive (si réalisé)
- [ ] Difficultés rencontrées et solutions
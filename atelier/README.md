# Data Lake Final — Plateforme de centralisation et gouvernance des données patients

Projet fusionné : **Big Data maîtrisé** (Medallion HDFS/Hive/Spark) + **consentement/gouvernance demontrable**
+ **de-duplication explicable** (exact + probabiliste), à visée pédagogique pour le stage M2 Big Data.

## Objectif

Maîtriser un sujet : centraliser, standardiser, de-dupliquer et gouverner des données patients
synthétiques multi-sources dans une architecture Big Data. L'essentiel :

1. **Concept Big Data** : pipeline Medallion RAW → SILVER → GOLD sur Hive/HDFS/Spark (VM).
2. **Consentement / gouvernance** : consent purpose-by-purpose, audit d'accès, rôles, clés API.
3. **De-duplication explicable** : matching exact + probabiliste, master patient, identity map, evaluation ground-truth.

Le frontend Next.js est **optionnel** (`projet/code-source/front-optional/`), conservé sans effort.

## Structure

```
documents/            docs du stage (fusion des 2 projets) - manuel conceptuel
ai/                   instructions agents IA : memoire/ (redaction) + dev/ (developpement)
references/           bibliographie (reserve)
projet/code-source/   code fusionne (provision VM, engine, evaluation, tests)
```

## Sources de la fusion

- `datalake_mavis/` : architecture Big Data pro (VM, Medallion, FHIR, Hive, Spark, Next.js).
- `Mon_Memoire/projet/code-source/` (ex `test_bigdata`) : de-duplication, consentement, audit, evaluation.

## Points d'entrée

- [documents/cahier_des_charges.md](documents/cahier_des_charges.md) — objectifs et perimetre
- [documents/documentation/bigdata_concepts.md](documents/documentation/bigdata_concepts.md) — concepts Big Data a maitriser
- [documents/documentation/deduplication.md](documents/documentation/deduplication.md) — methode de de-duplication
- [documents/documentation/consentement_gouvernance.md](documents/documentation/consentement_gouvernance.md) — consentement & gouvernance
- [projet/code-source/README.md](projet/code-source/README.md) — guide technique du code
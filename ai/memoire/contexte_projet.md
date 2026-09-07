# Contexte du projet (pour rédaction du mémoire)

Faits clés, vérifiables dans le dépôt, utiles pour rédiger les chapitres.

## Contexte

Thème : **conception d'une plateforme Big Data de gestion et de gouvernance des données patients** —
nettoyage, **déduplication** (Master Patient Index) et **contrôle d'accès basé sur le consentement**.
Stage M2 Big Data chez Madagascar Medical Technology (MMT), données **synthétiques** uniquement.

Problématique : données patients dispersées dans des systèmes hétérogènes (identifiants, formats,
schémas différents) ; un même patient apparaît sous des formes variées. Il faut déterminer s'il s'agit
du même patient, centraliser en **conservant la traçabilité d'origine**, et **gouverner les accès**.

## Démarche (3 niveaux) — argument structurant du mémoire

1. **Niveau 1 — MVP** : CSV + Pandas + PostgreSQL. Résoudre d'abord le problème métier.
2. **Niveau 2 — Spark** : PySpark local, résultats **strictement identiques** au MVP (parité).
3. **Niveau 3 — Big Data** : Data Lake + HDFS + Hive + Spark, pipeline ELT Medallion.

Chaque technologie est introduite **par besoin**, pas par effet de mode (documenté dans
`documents/documentation/bigdata_concepts.md`).

## Projet fusionné `data_lake_final`

Fusion de deux PoC complémentaires :
- `datalake_mavis` → architecture Big Data complète (VM Hadoop/Hive/Spark, ELT 4 étapes, FHIR, API Flask, Next.js).
- `test_bigdata` (devenu `Mon_Memoire/projet/code-source/`) → dédup explicable, consentement/audit, évaluation ground-truth.

Choix de fusion validés : nouveau repo autonome ; docs = un seul set logique
(`documents/cahier_des_charges.md` + `documents/documentation/*` ; SUIVI/LOGS consolidés — pas de doublons) ;
`ai/` = `memoire/` + `dev/` ; frontend Next.js conservé **optionnel** ; consentement porté **Hive GOLD + API**.

## Chiffres clés réels (à réutiliser avec mentions)

| Domaine | Donnée vérifiable |
|---|---|
| Pipeline | 4 étapes orchestrées ; ~65 680 patients Silver (run 24/08) ; 24 872 doublons détectés (flag) |
| Sources ELT | MAVIS (11 tables), MMT_DB (3 tables, base synthétique 60 271 lignes), CLINIQUE SQLite (54 582 lignes) |
| GOLD | `datalake_gold.patient_events_gold` (17 colonnes, 8 tranches RMA) ; dette : jointures GOLD limitées |
| Plateforme | 3 sources CSV ; 60 RAW → 36 masters ; 24 fusions exactes ; 60 identity links ; 108 consentements |
| Dédup | Score nom 0.5 / naissance 0.3 / tél 0.2 ; seuil 0.80 ; blocking ; exact + probabiliste |
| Évaluation | hard : Precision **1.000**, Recall 0.253, **F1 0.403** ; exact F1 0.855 ; probabilistic F1 0.851 ; 0 FP |
| Spark | Spark 3.4.2 (VM) / 4.2 local ; dédup Spark **identique** au MVP (18 liens / 11 masters, Jean Rakoto + Nirina) |
| Tests | moteur 9/9 PASS (matcher 6, consent 3) ; API données 12/12 ; MVP 20 tests + 44 tests générateur |
| API | Flask 9 endpoints `/rma/*` (+ mocks backend) ; FastAPI lecture seule `/health /metrics /patients /audit /consent` |

## Pièges / anti-régression à évoquer (preuves de robustesse)

- `sentence_transformers` interdit (crash Python 3.8) → RapidFuzz + synonymes.
- Warehouse Spark jamais sur vboxsf (corruption `part-*.snappy.parquet`) → toujours HDFS.
- Pas d'`overwrite` dans la boucle par source (incident log n°11) → 1re `overwrite`, suivantes `append`.
- Mocks **côté backend** uniquement (flag `mocked`), jamais côté frontend.
- `JAVA_HOME` avec `\bin` en trop → Spark bloqué ; corrigé et normalisé dans `spark/session.py`.

## Reste à faire (à ne pas présenter comme fait)

Export VM `.box`, tests unitaires EI-déployés, Docker/CI, pages governance frontend, enrichissement
mapping FHIR (liens FK), rapport slides soutenance.
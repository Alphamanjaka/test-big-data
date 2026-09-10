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

## Projet fusionné (dépôt unique)

Fusion de deux PoC complémentaires :
- `datalake_mavis` → architecture Big Data complète (VM Hadoop/Hive/Spark, ELT 4 étapes, FHIR, API Flask, Next.js).
- `test_bigdata` (repris dans `projet/mvp/`, moteur porté dans `projet/code-source/engine/`) → dédup explicable, consentement/audit, évaluation ground-truth.

Choix de fusion validés : nouveau repo autonome ; docs = un seul set logique
(`documents/cahier_des_charges.md` + `documents/documentation/*` ; SUIVI/LOGS consolidés — pas de doublons) ;
`ai/` = `memoire/` + `dev/` ; frontend Next.js conservé **optionnel** ; consentement porté **Hive GOLD + API**.

## Chiffres clés réels (à réutiliser avec mentions)

### Run final fusion (07/09/2026, VM, sources CSV synthétiques)

| Domaine | Donnée vérifiable |
|---|---|
| Pipeline | `run_pipeline.sh` **4/4 vert** : RAW → SILVER → GOLD OK (`provision/logs/elt.log`) |
| SILVER | `datalake_silver.patient_fhir` **214** lignes (76 pharmacy + 76 consultation + 62 imaging) |
| Masters | **145** masters distincts ; **69** doublons liés (`is_duplicate`) ; `match_method` exact 69 / new_master 145 ; `match_score` 1.0 |
| Gouvernance API | `duplicate_rate` **32.24 %**, `mocked: false` (données réelles Hive) |
| GOLD | `patient_events_gold` **0** ligne (interim patients-only, attendu) ; `patient_consent_gold` **145** |
| API | `test_api.py` **14/14 PASS** avec `RMA_USE_MOCK=false` ; health `GET /rma/last_sync` 200 |
| Incident corrigé | explosion 11 614 lignes → cause racine : `patient_uuid` capturé par le mapping FHIR dynamique (colonne id détournée → `source_patient_id` NULL → jointure moteur 76×76) |

### Historique PoC `datalake_mavis` / `test_bigdata` (à dater dans le texte)

| Domaine | Donnée vérifiable |
|---|---|
| Pipeline | 4 étapes orchestrées ; ~65 680 patients Silver (run 24/08, PoC datalake_mavis d'origine) ; 24 872 doublons détectés (flag) |
| Sources ELT | MAVIS (11 tables), MMT_DB (3 tables, base synthétique 60 271 lignes), CLINIQUE SQLite (54 582 lignes) |
| GOLD | `datalake_gold.patient_events_gold` (18 colonnes, 8 tranches RMA) ; dette : jointures GOLD limitées |
| Plateforme | 3 sources CSV ; 60 RAW → 36 masters ; 24 fusions exactes ; 60 identity links ; 108 consentements |
| Dédup | Score nom 0.5 / naissance 0.3 / CIN 0.1 / ville de naissance 0.1 ; seuil 0.80 ; blocking ; exact + probabiliste |
| Évaluation | hard (2026-09-08, `evaluation_truth.md`) : **Precision 1.000, Recall 0.422, F1 0.594** ; exact P/R/F1 1.000/0.854/0.921 ; probabilistic 1.000/0.533/0.696 ; 0 FP ; rappel par source pharmacy 0.422 / consultation 0.422 / imaging 0.423 |
| Spark | Spark 3.4.2 (VM) / 4.2 local ; dédup Spark **identique** au MVP (JSON `evaluation_truth.md` : modes MVP+Spark, TP=307 FP=0 FN=420, 804 masters prédits, 500 groupes vérité, 1 057 enregistrements) |
| Tests | moteur 23/23 PASS (matcher 12, consent 3, canonique 8) ; API données **14/14 PASS** ; MVP 20 tests + 44 tests générateur |
| API | Flask 11 endpoints (9 `/rma/*` + 2 `/api/governance/*`) + mocks backend ; FastAPI lecture seule `/health /metrics /patients /audit /consent` |

## Pièges / anti-régression à évoquer (preuves de robustesse)

- `sentence_transformers` interdit (crash Python 3.8) → RapidFuzz + synonymes.
- Warehouse Spark jamais sur vboxsf (corruption `part-*.snappy.parquet`) → toujours HDFS.
- Pas d'`overwrite` dans la boucle par source (incident log n°11) → 1re `overwrite`, suivantes `append`.
- Mocks **côté backend** uniquement (flag `mocked`), jamais côté frontend.
- `JAVA_HOME` avec `\bin` en trop → Spark bloqué ; corrigé et normalisé dans `spark/session.py`.

## Reste à faire (à ne pas présenter comme fait)

Export VM `.box`, tests unitaires EI-déployés, Docker/CI, pages governance frontend, enrichissement
mapping FHIR (liens FK → `patient_events_gold` vide en interim), alimentation PostgreSQL central
(`granted`/`purpose` NULL dans `patient_consent_gold`), rapport slides soutenance.
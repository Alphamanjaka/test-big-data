# ai/memoire — Consignes de rédaction du mémoire

> **Lire ce dossier au début de toute session de rédaction du mémoire.** Il centralise le contexte et la
> méthode de rédaction. Le mémoire vit dans `F:\MBDS\STAGE\PROJECT\Mon_Memoire\` (repo séparé de
> `data_lake_final` — la mémoire reste dans Mon_Memoire, le code fusionné est dans data_lake_final).

## Fichiers

| Fichier | Contenu | À consulter quand |
|---|---|---|
| `contexte_projet.md` | Contexte, problématique, objectifs, périmètre fusionné, faits clés chiffrés | Début de session, pour cadrer un chapitre |
| `methode.md` | Méthode de rédaction, structure des chapitres, traçabilité des affirmations | Avant d'écrire un chapitre |

## Structure de la mémoire (Mon_Memoire/chapters/)

| Chapitre | Contenu cible |
|---|---|
| `01-introduction.md` | Contexte organisme, problématique, objectifs, périmètre, plan |
| `02-etat-de-l-art.md` | État de l'art : FHIR, Medallion, MPI/Entity Resolution, consentement (RGPD), Big Data Hadoop/Hive/Spark |
| `03-analyse.md` | Analyse du besoin, sources, contraintes, choix de conception |
| `04-conception.md` | Architecture (3 niveaux : MVP → Spark → Big Data), modèle canonique, schéma SQL |
| `05-realisation.md` | Réalisation : générateur, pipeline, dédup, PostgreSQL, gouvernance, Spark, Data Lake |
| `06-tests.md` | Tests & évaluation ground-truth (P/R/F1), difficultés rencontrées |

Chaque chapitre commence par un bloc « Objectif » + « Notes / TODO » (squelette existant, à rédiger).

## Sources de référence (à citer / aligner)

- `F:\MBDS\STAGE\PROJECT\data_lake_final\documents\` — cahier des charges + manuel conceptuel (fusionnés).
- `F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\` — code (ex test_bigdata) + `ai_context/` consignes.
- `F:\MBDS\STAGE\PROJECT\datalake_mavis\` — docs d'architecture Big Data d'origine.
- `references/` (Mon_Memoire) — bibliographie.

## Règles de rédaction

1. Le mémoire raconte une **démarche progressive** : problème métier → MVP → validation → Big Data.
2. Chaque affirmation doit s'appuyer sur un **fait vérifiable** du dépôt (fichier, run, résultat de test).
3. Utiliser le vocabulaire des concepts (Medallion, MPH, blocking, purpose-by-purpose…).
4. Illustrer avec les **chiffres réels** disponibles dans `contexte_projet.md`.
5. Ne pas prétendre avoir réalisé ce qui est « à rendre » (export VM, soutenance, Docker) — l'honnêteté
   du PoC est une valeur affichée du projet.
6. Mise à jour du suivi : voir `ai/dev/suivi_avancement.md` (les jalons mémoire sont loggés comme jalons projet).
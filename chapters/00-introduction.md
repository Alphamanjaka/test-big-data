# Introduction générale

## Contexte général

Comme la plupart des organisations de santé, un établissement fait coexister **plusieurs
systèmes d'information indépendants** : consultations, pharmacies, laboratoires, imagerie,
dossiers médicaux. Chacun possède sa propre base, son propre format et ses propres
identifiants [cahier_des_charges.md §1]. Le même patient y est donc enregistré plusieurs fois,
sous des formes différentes, sans qu'aucun système ne sache qu'il s'agit de la même personne.

Deux évolutions rendent ce problème pressant. D'une part, la quantité de données produites par
ces systèmes augmente, et leur exploitation relève désormais des architectures **Big Data** :
des données trop nombreuses ou trop variées pour un seul poste de travail, qu'il faut stocker
et traiter de façon répartie. D'autre part, les données de santé sont des données sensibles :
leur usage doit être **gouverné**, c'est-à-dire contrôlé selon qui les demande, pour quelle
finalité, et avec l'accord du patient.

## Motivation personnelle

Ce sujet m'a attiré pour deux raisons. La première est qu'il réunit, dans un seul projet, les
trois volets de la formation MBDS : les bases de données, l'intégration de systèmes
hétérogènes et le traitement de données à grande échelle. C'est un sujet complet, qui oblige à
aller de la donnée brute jusqu'à son exposition contrôlée.

La seconde est mon intérêt pour le Big Data et pour les volumes de données à grande échelle.
Mon expérience dans ce domaine reste encore limitée, et ce stage a été l'occasion de passer de
la théorie à la pratique : installer un Data Lake, écrire des traitements Spark, et comprendre
pourquoi chaque technologie est introduite, plutôt que de l'employer par effet de mode.

## Mission confiée

Le stage, d'une durée de **quatre mois**, s'est déroulé du **6 juillet à fin octobre 2026** au sein de **Madagascar Medical
Technology (MMT)**, dans son département Recherche et Développement (chapitre 1). La mission
confiée était de **concevoir une plateforme de centralisation et de gouvernance des données
patients** : intégrer des sources hétérogènes, nettoyer et standardiser les données, reconnaître
les patients présents dans plusieurs systèmes (déduplication), et contrôler l'accès aux données
selon le consentement du patient [cahier_des_charges.md §3].

Deux contraintes du commanditaire encadrent cette mission : les données doivent rester sur les
machines de l'établissement (**hébergement interne**, aucun service cloud externe), et seules
des **données synthétiques** peuvent être utilisées — aucune donnée réelle de patient n'est
manipulée dans ce travail. La plateforme est livrée sous forme de prototype reproductible ; elle
n'a **pas été déployée** en production chez le commanditaire (§ 3.4).

## Problématique

> **Problématique** : comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer
> et centraliser des données patients issues de sources hétérogènes, tout en assurant la
> traçabilité des identités et la gouvernance des accès basée sur le consentement du patient ?
> [cahier_des_charges.md §1]

## Annonce du plan

Le mémoire suit le plan de référence du master MBDS.

**Tableau 1 — Le plan du mémoire : huit chapitres numérotés entre l'introduction et la conclusion générales, puis bibliographie et annexes.**

| Partie | Contenu |
|---|---|
| **1 — Présentation du stage** | l'entreprise d'accueil, le sujet, ses objectifs, ses enjeux et ses risques |
| **2 — État de l'art** | notions de référence (Entity Resolution, MPI, FHIR, consentement, Big Data, Medallion), critères de comparaison, étude des solutions existantes, tableau comparatif, pertinence du projet |
| **3 — Étude de l'existant et solution envisagée** | les systèmes de MMT vus par l'utilisateur et par le développeur, leur critique, la solution retenue en trois niveaux, objectifs et livrables |
| **4 — Démarche projet** | principes (méthode, rôles, outils, gestion de configuration), contraintes et risques, planning, budget |
| **5 — Exigences réalisées** | exigences fonctionnelles organisées par étapes du pipeline, exigences non fonctionnelles, interfaces (IHM et API) |
| **6 — Architecture du système** | architecture logicielle et architecture technique |
| **7 — Conception du logiciel** | plate-forme technique, structure du code, modèle de données, composants, déploiement, réalisation des étapes |
| **8 — Tests du système** | stratégie de test, tests unitaires, d'intégration et fonctionnels, évaluation sur vérité terrain |
| **Conclusion générale** | bilan, difficultés, limites, apports personnels, perspectives |

Les pièces liminaires comprennent un **glossaire** des termes clés. La bibliographie et les
**annexes** (A à G) suivent la conclusion.

# Introduction générale

Un patient se présente à la pharmacie, puis en consultation, puis au service d'imagerie. À
chaque étape, il est enregistré de nouveau, dans une base différente et sous une forme
différente. Aucun de ces services ne sait qu'il s'agit de la même personne, et aucun ne peut lui
demander ce qu'il accepte que l'on fasse de ses données.

C'est la situation de nombreux établissements de santé : des **systèmes d'information
indépendants**, chacun avec sa base, son format et ses identifiants, et des sources appelées à
évoluer (cahier des charges, § 1). Or les données de santé sont sensibles : leur usage doit être
**gouverné**, c'est-à-dire contrôlé selon qui les demande, pour quelle finalité et avec l'accord
du patient.

Le stage s'est déroulé du **6 juillet à fin octobre 2026** au département Recherche et
Développement de **Madagascar Medical Technology (MMT)**. La mission était de **concevoir une
plateforme de centralisation et de gouvernance des données patients** : intégrer des sources
hétérogènes, reconnaître un même patient d'une base à l'autre et n'ouvrir l'accès à ses données
que selon son consentement, aujourd'hui **par finalité**, et **par type de dossier** en cours de
développement (cahier des charges, § 3). Deux contraintes encadrent ce travail : l'**hébergement
interne** et l'usage exclusif de **données synthétiques**. La plateforme est livrée comme
prototype reproductible ; elle n'a pas été déployée en production.

> **Problématique** : comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer
> et centraliser des données patients issues de sources hétérogènes, tout en assurant la
> traçabilité des identités et la gouvernance des accès basée sur le consentement du patient ?

Le mémoire suit le plan de référence du master MBDS.

**Tableau 1 — Le plan du mémoire.**

| Partie | Contenu |
|---|---|
| **1 — Présentation du stage** | l'entreprise, le sujet, ses objectifs et ses enjeux |
| **2 — État de l'art** | notions de référence, solutions existantes et comparaison |
| **3 — Existant et solution envisagée** | les systèmes de MMT, leur critique, la solution en trois niveaux |
| **4 — Démarche projet** | méthode, outils, contraintes et risques, planning, budget |
| **5 — Exigences réalisées** | exigences fonctionnelles et non fonctionnelles, interfaces |
| **6 — Architecture du système** | architecture logicielle et technique |
| **7 — Conception du logiciel** | modèle de données, composants, réalisation des étapes |
| **8 — Tests du système** | tests et évaluation sur vérité terrain |
| **Conclusion générale** | bilan, limites et perspectives |

# ai/memoire — Consignes de rédaction du mémoire

> **Lire ce dossier au début de toute session de rédaction du mémoire.** Il centralise le contexte et la
> méthode de rédaction. Le mémoire vit dans `chapters/` du dépôt unique (`Mon_Memoire`), qui contient
> aussi le code (`projet/code-source/`) et le PoC `test_bigdata` (`projet/mvp/`). Le PoC Big Data
> d'origine a été retiré du dépôt (28/09/2026) ; son journal reste dans
> `documents/journal_poc_datalake_mavis.md`.

## Fichiers

| Fichier              | Contenu                                                                     | À consulter quand                         |
| -------------------- | --------------------------------------------------------------------------- | ----------------------------------------- |
| `contexte_projet.md` | Contexte, problématique, objectifs, périmètre fusionné, faits clés chiffrés | Début de session, pour cadrer un chapitre |
| `methode.md`         | Méthode de rédaction, structure des chapitres, traçabilité des affirmations | Avant d'écrire un chapitre                |

## Structure de la mémoire (Mon_Memoire/chapters/)

Le mémoire suit le **plan imposé par le master MBDS** (modèle des rapports de référence
`documents/RAPPORT_HASINA_1613.docx` et `documents/Rapport de stage ETU 1156 … .docx`), adopté le
28/09/2026.

| Fichier                     | Contenu cible                                                                                          |
| --------------------------- | ------------------------------------------------------------------------------------------------------ |
| `remerciements.md`          | Pièce liminaire (insérée après la page de garde par l'exporteur)                                       |
| `00-introduction.md`        | Introduction générale : contexte du domaine, motivation personnelle, mission confiée, problématique, plan |
| `01-presentation-stage.md`  | 1.1 Entreprise (MMT) ; 1.2 Sujet : contexte métier, objectifs, enjeux et risques                       |
| `02-etat-de-l-art.md`       | 2.1 Notions de référence + critères ; 2.2 Étude des solutions ; 2.3 Tableau comparatif ; 2.4 Pertinence |
| `03-existant-solution.md`   | 3.1 Existant (vision utilisateur / développeur) ; 3.2 Critique ; 3.3 Solutions envisagées (3 niveaux) ; 3.4 Objectifs et livrables |
| `04-demarche-projet.md`     | 4.1 Principes (activités, méthode, rôles, outils, gestion de configuration) ; 4.2 Contraintes et risques ; 4.3 Planning (jalons + Gantt) ; 4.4 Budget (humain, matériel/logiciel, total) |
| `05-exigences.md`           | 5.1 Exigences fonctionnelles par étapes (CU1–CU8, générateur) ; 5.2 Non fonctionnelles ; 5.3 Interfaces (IHM, API) |
| `06-architecture.md`        | 6.1 Architecture logicielle (3 niveaux, bout-en-bout) ; 6.2 Architecture technique (composants, ports) |
| `07-conception.md`          | 7.1 Plate-forme technique ; 7.2 Code (structure, données, composants, déploiement) ; 7.3 Réalisation des étapes et difficultés |
| `08-tests.md`               | 8.1 Stratégie ; 8.2 Unitaires ; 8.3 Intégration ; 8.4 Fonctionnels ; 8.5 Évaluation ground-truth ; 8.6 Limites |
| `09-conclusion.md`          | Conclusion générale : bilan, difficultés, limites, apports personnels, perspectives                   |
| `glossaire.md`              | Pièce liminaire (insérée après les acronymes) : chaque terme en français courant + où il est détaillé  |

Les annexes (A à G, dont G = questions anticipées du jury) sont dans `references/annexes.md`.
L'exporteur `projet/code-source/scripts/dev/export_memoire_docx.py` assemble le corps à partir de
`chapters/0*.md` : un nouveau fichier de corps doit respecter ce motif, une pièce liminaire ne
doit pas le respecter.

Chaque chapitre commence par un bloc « Objectif ». Le statut de rédaction ne figure pas dans les
chapitres (il s'imprimerait dans le DOCX) : il est tenu dans `ai/dev/logs.md`.

## Sources de référence (à citer / aligner)

- `documents/` — cahier des charges + manuel conceptuel (fusionnés).
- `projet/code-source/` — code consolidé (ex `test_bigdata`) + consignes.
- `projet/mvp/` — PoC `test_bigdata` (niveaux 1 et 2).
- `documents/journal_poc_datalake_mavis.md` — journal du PoC Big Data d'origine (captures de schémas,
  incidents, dates du 23/08 au 01/09/2026) ; le code du PoC reste consultable dans l'historique Git.
- `references/` — bibliographie.

## Règles de rédaction

1. Le mémoire raconte une **démarche progressive** : problème métier → MVP → validation → Big Data.
2. Chaque affirmation doit s'appuyer sur un **fait vérifiable** du dépôt (fichier, run, résultat de test).
3. Utiliser le vocabulaire des concepts (Medallion, MPI, blocking, purpose-by-purpose…) **et le
   définir en français courant à sa première apparition en prose** ; le glossaire (chapitre 9) en
   tient la liste. Un terme seul, non défini, est un défaut de rédaction.
4. Illustrer avec les **chiffres réels** disponibles dans `contexte_projet.md`.
5. Ne pas prétendre avoir réalisé ce qui est « à rendre » (export VM, soutenance, Docker) — l'honnêteté
   du PoC est une valeur affichée du projet.
6. Mise à jour du suivi : voir `ai/dev/suivi_avancement.md` (les jalons mémoire sont loggés comme jalons projet).

## Communication et démonstration

- Présenter séparément le message métier (réduire les doublons et contrôler les usages) et le message
  technique (pipeline Medallion, MPI explicable, consentement et audit).
- Préparer une démonstration reproductible : prérequis, commande, jeu synthétique, résultat attendu,
  preuve obtenue et limite observée.
- Identifier chaque élément comme réalisé, simulé, prévu, optionnel ou limité au PoC ; ne jamais
  transformer une hypothèse ou une cible en résultat expérimental.
- Les tableaux, graphiques et captures doivent préciser la source, la date, le périmètre et l'unité ;
  aucune donnée sensible ou réelle ne doit apparaître.

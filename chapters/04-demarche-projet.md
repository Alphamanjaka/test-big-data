# Chapitre 4 — Démarche projet

## 4.1 Principes

### 4.1.1 Activités d'ingénierie logicielle

Le projet a mobilisé les cinq activités classiques de l'ingénierie logicielle. Chacune a laissé
une production vérifiable dans le dépôt.

**Tableau 16 — Les activités d'ingénierie logicielle et leurs productions.**

| Activité | Ce qu'elle a produit | Où le trouver |
|---|---|---|
| **Analyse** | cahier des charges consolidé, capture des schémas sources, exigences F1–F6 | `documents/cahier_des_charges.md`, `documents/journal_poc_datalake_mavis.md`, chapitre 5 |
| **Conception** | architecture en trois niveaux, modèle canonique, schéma de la base centrale, règles de gouvernance | chapitres 6 et 7, `sql/schema.sql`, `documents/documentation/` |
| **Développement** | générateur synthétique, moteur de déduplication (Pandas et Spark), pipeline ELT, API, frontend optionnel | `projet/code-source/` |
| **Tests et évaluation** | suites `pytest`, évaluation sur vérité terrain, runs du pipeline | `projet/code-source/tests/`, `evaluation/evaluation_truth.md`, chapitre 8 |
| **Documentation et suivi** | journal daté, suivi d'avancement, manuel conceptuel, ce mémoire | `ai/dev/logs.md`, `ai/dev/suivi_avancement.md`, `documents/`, `chapters/` |

### 4.1.2 Méthode de gestion de projet

Le stage a suivi une **démarche itérative et incrémentale par jalons**. Elle emprunte aux
méthodes agiles l'idée d'**incréments démontrables** — chaque jalon livre quelque chose qui
fonctionne et se vérifie — et celle d'un **critère de sortie** explicite, qui joue le rôle de
la « définition de terminé ». Elle n'en reprend pas les cérémonies (sprints, revues d'équipe),
l'équipe de développement se limitant à une personne.

**Règles de pilotage appliquées** : ne pas engager une évolution avant que les tests du niveau
précédent réussissent ; tracer chaque décision d'architecture avec sa raison ; écrire chaque
limite constatée plutôt que la passer sous silence ; ne jamais remplacer les données de test par
des données réelles.

### 4.1.3 Rôles et responsabilités

Les **rôles du projet**, décrits ici, sont distincts des **rôles applicatifs** (`admin`,
`analyst`, `viewer`), qui régissent ce qu'un utilisateur de l'API peut lire (§ 7.2.3). Les
parties prenantes sont au nombre de quatre :

- **Le commanditaire**, Madagascar Medical Technology (MMT), représenté par l'encadrant
  professionnel. Il porte les deux contraintes structurantes du stage : l'**hébergement
  interne** — les données ne doivent pas quitter les machines de l'établissement, donc aucun
  service cloud externe — et l'usage exclusif de **données synthétiques**. Il valide les trois
  finalités d'accès déclarées à l'API.
- **L'encadrant professionnel**, M. Harena Ny Aina RABEMANOELA, fait le lien entre le besoin
  métier et sa formulation technique, et arbitre entre les options proposées.
- **L'encadrant pédagogique**, M. Rojo RABENANAHARY, suit le stage du point de vue de la
  formation.
- **Le stagiaire**, RANOMENJANAHARY Manjaka Alpha, auteur du projet, conçoit, développe, teste
  et documente la plateforme.

> **Conséquence d'une équipe réduite.** Avec un seul développeur, la revue de code croisée n'a
> pas eu lieu : la seule relecture est celle de l'auteur, ce qui limite la valeur des tests
> comme preuve externe.

### 4.1.4 Outils

**Tableau 17 — Les outils du projet, regroupés par usage.**

| Usage | Outils | Rôle dans le projet |
|---|---|---|
| Développement | Visual Studio Code, Python 3.8 (environnement virtuel de la VM), Node.js | écriture du code, du pipeline et du frontend optionnel |
| Environnement | Vagrant, VirtualBox (`ubuntu/focal64`), Laragon | VM Big Data reproductible ; bases locales de développement (PostgreSQL, SQLite) |
| Big Data | Hadoop 3.3.6 (HDFS, YARN), Hive 3.1.3, Spark 3.4.2 | Data Lake et traitements répartis |
| Données et API | PostgreSQL, Pandas, PySpark, RapidFuzz, FastAPI, Flask, Next.js | base centrale, moteur, exposition |
| Qualité | `pytest`, évaluateur ground-truth (`evaluation/`) | tests et mesure de la déduplication |
| Configuration | Git (branches `main` et `develop_spark`), hook `githooks/pre-commit` | versionnement, blocage des secrets avant commit |
| Documentation | Markdown, Mermaid (`mermaid-cli`), `python-docx` | chapitres, figures, export Word du mémoire |

### 4.1.5 Gestion de configuration

Trois principes rendent le projet rejouable à partir du seul dépôt, sans dépendre d'une
machine encore allumée : ce qui est versionné, ce qui est déclaré, et ce qui est vérifié.

**Ce qui est versionné.** Le dépôt Git est la source de vérité du projet : code, scripts du
pipeline, configuration de référence, tests, et ce mémoire. Chaque jalon correspond à des
commits identifiables, et les documents de suivi (`ai/dev/logs.md`,
`ai/dev/suivi_avancement.md`) enregistrent ce qui a été décidé et pourquoi. Les données
patients ne sont pas versionnées : elles sont régénérées par le générateur synthétique, avec
une graine fixe (`RANDOM_SEED = 42`) qui rend la génération reproductible. Les secrets et les
fichiers de configuration contenant des identifiants sont exclus du dépôt et fournis par
variables d'environnement ; un hook de pré-commit bloque les identifiants connus avant qu'ils
n'atteignent l'historique.

**Ce qui est déclaré, et non codé en dur.** Les sources de données, les chemins et les
identifiants sont décrits dans des fichiers de configuration lus au démarrage, jamais
écrits dans le code. Les paramètres qui gouvernent le comportement — le nombre de partitions,
le seuil de rapprochement à 0,80, les poids par champ, les finalités autorisées — sont
explicites et regroupés : les modifier ne demande pas de toucher à la logique.

**Ce qui est vérifié.** La suite de tests est exécutée à chaque jalon, et son résultat vert
constitue le critère de sortie du jalon suivant : on n'engage pas une évolution sur un niveau
de test cassé. Les journaux du pipeline (`elt.log`) conservent la trace des volumes traités à
chaque étape, ce qui permet de comparer une exécution à une autre sans la rejouer. La
rejouabilité est également une propriété du code : le pipeline est idempotent, et un
traitement peut être relancé depuis la zone SILVER sans dupliquer ni corrompre les zones
en aval.

> **Limite.** Cette gestion démontre la reproductibilité depuis le dépôt, pas la mise en
> production : aucun déploiement automatisé sur un serveur du commanditaire n'a été réalisé.

## 4.2 Contraintes et risques

**Tableau 18 — Les contraintes du stage et leur traitement.**

| Contrainte | Nature | Traitement adopté |
|---|---|---|
| **VM de 8 Go et 4 cœurs** | mémoire limitée pour Spark | 4 Go pour l'exécuteur, 2 Go pour le driver, 8 partitions |
| **Nœud distant MAVIS instable** | source PostgreSQL distante (`mavis_notheme`, 11 tables, tunnel SSH) | répliques locales de dev (`rebuild_mavis_db.py`, 73 090 lignes) ; données finales synthétiques |
| **Python 3.8 imposé** | `sentence_transformers` plante sous Python 3.8 | RapidFuzz pour la similarité des noms ; dictionnaire de synonymes pour le mapping des colonnes |
| **Dossier partagé de la VM** | fichiers Parquet corrompus quand Spark y écrit | entrepôt Spark toujours sur HDFS |
| **Reproductibilité** | évaluation et déduplication déterministes | graine 42 ; seuil et poids fixés en configuration |
| **Données sensibles** | loi n° 2014-038, art. 18 ; RGPD, art. 9 | données **synthétiques** uniquement ; gouvernance intégrée au système |

**Contexte local.** Quatre réalités du terrain conditionnent l'applicabilité du projet ; la
dernière n'est que **partiellement** traitée dans le périmètre du stage.

**Tableau 19 — Le contexte local et ce qu'il change à la solution.**

| Plan de réalité | Observation de terrain | Conséquence sur la solution | État |
|---|---|---|---|
| **Données de santé dispersées** | chaque service tient son propre registre (pharmacie, consultation, imagerie), sans identifiant commun | justifie l'Entity Resolution et le MPI : l'identifiant partagé doit être **reconstruit**, pas supposé | traité |
| **Organisation et rôles** | le service concerné n'a pas de référentiel d'identité ; la clé d'accès est un couple (identifiant fonctionnel, mot de passe) | l'API d'accès a été conçue sur un modèle **clé API + rôle** plutôt que sur des comptes nominatifs, plus simple à configurer sans annuaire | traité |
| **Infrastructure et connectivité** | réseau intermittent, alimentation non garantie, pas de cluster | conception **mono-nœud** et **rejouable** : un run complet repart de zéro et produit le même résultat (seed fixe) | traité |
| **Données sensibles, contexte juridique** | la loi n° 2014-038 classe les données de santé parmi les données sensibles ; son autorité de contrôle, la CMIL, n'est pas encore opérationnelle (§ 2.1.6) | conception alignée sur la loi malgache et sur le RGPD (finalité, consentement, sécurité, hébergement interne) ; les **formalités** (déclaration, autorisation préalable) restent à accomplir avant tout déploiement | **partiel** |

Deux points restent ouverts :

1. **La conformité est un cadre de conception, pas une certification.** Le droit
   applicable est la loi malgache n° 2014-038 [B24] ; le RGPD [B10] et les
   recommandations CNIL [B11], [B12] ont servi de référence de conception, parce
   que leur doctrine est détaillée et que leurs principes sont les mêmes (§ 2.1.6).
   Aucune formalité n'a été accomplie auprès de la CMIL, puisque le prototype n'est
   pas déployé ; une plateforme réelle relèverait probablement de l'autorisation
   préalable prévue pour les traitements à risques particuliers (art. 46). Cette
   démarche reste à mener avant toute mise en production, même si l'autorité n'est
   pas encore opérationnelle [B25].
2. **La volumétrie réelle n'a pas été utilisée.** Toutes les données sont
   synthétiques, générées à l'échelle du prototype (214 fiches au run de référence,
   1 057 dans le jeu d'évaluation, § 5.1.5). Le dimensionnement réel de l'établissement — volumétrie,
   cardinalité, taux de doublons observé — est **inconnu** et conditionne le choix
   du seuil de similarité (§ 7.2.3) comme le partitionnement du blocking.

> **Conséquence concrète.** Sans annuaire d'identité, la gestion des accès par clé d'API et
> trois rôles est un compromis pragmatique. Avec un annuaire, elle passerait à des comptes
> nominatifs ; le contrôle du consentement (§ 7.2.3) resterait inchangé, car il ne dépend pas du
> mode d'authentification.

**Risques du projet.** Le cahier des charges (§ 11) identifie les risques qui pouvaient bloquer
le projet ; le tableau les reprend avec la parade prévue et le constat à la fin du stage.

**Tableau 20 — Les risques du projet et leur traitement.**

| Risque | Impact | Parade | Constat à la fin du stage |
|---|---|---|---|
| Mémoire limitée de la VM (8 Go) | performance de Spark | paramétrage de la mémoire et des partitions | maîtrisé au volume du prototype : pipeline complet au run de référence |
| Nœud distant MAVIS instable | blocage du pipeline | sources locales de développement (Laragon, SQLite) puis synthétiques | contourné : le run de référence n'utilise que les sources CSV |
| Hétérogénéité des sources | mapping FHIR incomplet | synonymes et similarité pour le mapping des colonnes | partiellement maîtrisé : table GOLD des événements vide (§ 8.6) |
| Données sensibles | confidentialité | données **synthétiques** uniquement ; rôles, audit et consentement | maîtrisé : aucune donnée réelle manipulée |
| Indisponibilité de la VM en fin de stage | re-validation impossible | tests hors VM avant toute exécution réelle | en partie : planification et incrémental testés hors VM (§ 7.3.2) |

## 4.3 Démarche mise en œuvre

Le travail s'est organisé en **cinq jalons**, chacun stabilisé (tests, évaluation) par un
critère de sortie vérifiable. Les deux PoC d'origine ont avancé en parallèle — `test_bigdata`
pour le moteur métier, `datalake_mavis` pour l'architecture Big Data — avant d'être fusionnés
dans le dépôt unique ; la règle du critère de sortie s'applique à l'intérieur de chaque chaîne.

**Tableau 21 — Les cinq jalons du stage.**

| Jalon | Contenu | Critère de sortie | Preuve | Traces datées |
|---|---|---|---|---|
| **J1 — Socle** | générateur de données synthétiques et vérité terrain | 44 tests réussis, 500 patients maîtres, 3 niveaux de difficulté | `evaluation/synthetic-patient-generator/` | MVP : 01/09/2026 |
| **J2 — Moteur** | modèle canonique, blocking, passes exacte et probabiliste | précision de 1,000 ; parité Pandas et Spark | `engine/identity/`, `evaluation_truth.md` | 07–08/09/2026 |
| **J3 — Big Data** | pipeline ELT Medallion RAW → SILVER → GOLD | 4 étapes sur 4, 214 lignes SILVER, 145 patients maîtres, 69 doublons | `run_pipeline.sh`, `elt.log` | PoC : 23/08–01/09 ; fusion : 07/09/2026 |
| **J4 — Gouvernance** | rôles, clés d'API, consentement par finalité, audit, refus 403 journalisé ; planification et reprise du pipeline | suite de tests complète réussie, dont 401 et 403 vérifiés | `engine/governance/`, `tests/` | 01/09, 27–28/09/2026 |
| **J5 — Mémoire** | structuration selon le plan MBDS, état de l'art sourcé, mise en cohérence des résultats | 31 références citées ; chaque chiffre rattaché à un résultat du dépôt | ce dépôt | 08/09–28/09/2026 |

Le planning ci-dessous répartit ces jalons sur la durée du stage (6 juillet – fin octobre
2026, soit quatre mois). Il distingue ce qui est **daté** par les journaux du dépôt (bleu foncé),
ce qui est **déclaré** sans trace datée (bleu clair) et ce qui est **prévu** (gris).

**Les premières semaines : une analyse itérative.** Avant toute ligne de code, le stage a
commencé par une phase d'analyse qui ne laisse pas de trace dans le dépôt : discussions avec
l'encadrant professionnel, compréhension du sujet, analyse de l'existant, documentation et
état de l'art — ce dernier à lui seul sur au moins trois semaines —, puis confrontation aux
problèmes et contraintes réels (nœud MAVIS instable, VM de 8 Go, Python 3.8). Ces activités
ne se sont pas enchaînées une fois pour toutes : elles **revenaient en boucle**, chaque
contrainte découverte relançant une discussion, une relecture de l'existant ou une recherche
documentaire. C'est ce qui justifie une démarche itérative plutôt qu'un cycle en cascade
(§ 4.1.2).

**Tableau 22 — Diagramme de Gantt du stage, par quinzaine. {gantt}**

| Phase | 06/07–19/07 | 20/07–02/08 | 03/08–16/08 | 17/08–30/08 | 31/08–13/09 | 14/09–27/09 | 28/09–11/10 | 12/10–31/10 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Cadrage du sujet | □ | □ | □ | | | | | |
| Existant et contraintes | □ | □ | □ | ■ | ■ | | | |
| Documentation et état de l'art | | □ | □ | □ | ■ | ■ | | |
| Développement | | | | ■ | ■ | ■ | ■ | |
| Tests et évaluation | | | | ■ | ■ | ■ | ■ | |
| Rédaction du mémoire | | | | | ■ | ■ | ■ | ○ |
| Finalisation et soutenance | | | | | | | ○ | ○ |

> **Lecture du planning.** Les journaux du dépôt commencent le 23/08/2026 ; les semaines
> antérieures sont **déclarées** et figurées comme telles, sans dates reconstituées. Les
> dernières quinzaines (finalisation, soutenance) sont **prévues**.

> **Ce que ce découpage a permis, et ce qu'il a coûté.** Chaque jalon est démontrable
> indépendamment. En revanche, la parité stricte entre Pandas et Spark a exigé d'écrire
> l'algorithme deux fois, ce qui aurait pu être évité si l'échelle cible avait été arrêtée plus
> tôt. C'est la principale leçon de conduite de projet tirée du stage.

## 4.4 Budget

Le budget couvre la **durée du stage, soit quatre mois** (6 juillet – fin octobre 2026), et le
**périmètre réalisé** : un prototype reproductible sur la VM de développement. La plateforme
n'ayant pas été déployée chez le commanditaire (§ 3.4), aucun coût de serveur de production,
d'hébergement ou d'exploitation n'est compté. Les **coûts humains sont une estimation** : ils
valorisent le temps consacré au projet sur la base d'un coût mensuel de référence, et non des
montants facturés. Les coûts matériels et logiciels, eux, sont réels.

**Tableau 23 — Budget du projet sur quatre mois.**

| Poste | Base de calcul | Coût (Ar) |
|---|---|---:|
| Développeur (stagiaire) | 1 ETP à 1 000 000 Ar par mois (estimation) | 4 000 000 |
| Encadrement professionnel et pédagogique | 2 × 0,1 ETP, 150 000 Ar par mois (estimation) | 600 000 |
| Poste de travail et connexion | matériel et abonnement existants | 0 |
| Machine virtuelle | créée par Vagrant sur le poste de développement | 0 |
| Logiciels | Hadoop, Hive, Spark, PostgreSQL, FastAPI, Flask, Next.js, Pandas, RapidFuzz, `pytest`, Vagrant, VirtualBox, Git (open source) | 0 |
| Serveur de production | non applicable : plateforme non déployée | 0 |
| Solutions commerciales comparées (§ 2.2) | étudiées sur documentation, non acquises | 0 |
| **Total** | | **4 600 000** |

Le coût total, **4 600 000 Ar**, est entièrement humain : aucune licence n'a été achetée, ce
que confirment les fichiers de dépendances du dépôt. C'est un avantage de l'open source dans un
contexte aux moyens limités. Un déploiement en production ajouterait des postes non chiffrés ici
(serveur, sauvegarde, exploitation).

## Conclusion et transition

La démarche est posée : une méthode incrémentale à critères de sortie vérifiables, des rôles
clairs, des outils libres, une configuration rejouable, des contraintes traitées une à une et
un budget dont la part matérielle et logicielle est nulle. Le chapitre 5 décrit les **exigences réalisées**, vues
par l'utilisateur : ce que la plateforme fait, avec quelle qualité, et par quelles interfaces.

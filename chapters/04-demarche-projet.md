# Chapitre 4 — Démarche projet

## Objectif

Décrire comment le projet a été conduit : les principes retenus (activités d'ingénierie,
méthode de gestion de projet, rôles, outils, gestion de configuration), les contraintes et les
risques, la démarche effectivement mise en œuvre avec son planning, et le budget.

---

## 4.1 Principes

### 4.1.1 Activités d'ingénierie logicielle

Le projet a mobilisé les cinq activités classiques de l'ingénierie logicielle. Chacune a laissé
une production vérifiable dans le dépôt, ce qui permet de la relire sans dépendre de la mémoire
du stagiaire.

**Tableau 16 — Les activités d'ingénierie logicielle du projet, ce que chacune a produit, et où le trouver.**

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
la « définition de terminé ». Elle n'en reprend pas les cérémonies (sprints, revues d'équipe) :
l'équipe de développement tient en une seule personne (§ 4.1.3).

**Règles de pilotage appliquées** : ne pas engager une évolution avant que le
contrôle ciblé du niveau précédent soit vert ; toute décision d'architecture est
tracée avec sa raison (ce mémoire) ; chaque limite constatée est écrite dans le
chapitre des limites plutôt que passée sous silence ; les données de test ne sont
jamais remplacées par des données réelles, y compris quand elles seraient
plus commodes à obtenir.

### 4.1.3 Rôles et responsabilités

Avant toute notion de rôle applicatif, il faut distinguer deux plans qui se ressemblent et
que les rapports de référence traitent séparément : **les rôles du projet**, qui décident de
quoi pendant le stage, et **les rôles d'exécution** (`admin`, `analyst`, `viewer`), qui
régissent ce qu'un utilisateur de l'API a le droit de lire une fois le logiciel livré. Les
premiers sont décrits ici, les seconds au § 2.1.6 et au § 7.2.3.

Les parties prenantes du projet sont au nombre de quatre, et l'équipe de développement
tient en une seule personne :

- **Le commanditaire**, Madagascar Medical Technology (MMT), représenté par l'encadrant
  professionnel. Il porte les deux contraintes structurantes du stage : l'**hébergement
  interne** — les données ne doivent pas quitter les machines de l'établissement, donc aucun
  service cloud externe — et l'usage de **données synthétiques** uniquement, aucune donnée
  réelle de patient ne devant être mobilisée, y compris quand elle serait plus facile à
  obtenir. Il valide par ailleurs les trois finalités déclarées à l'API.
- **L'encadrant professionnel**, M. Harena Ny Aina Rabemanoela, fait le lien entre le besoin
  métier et sa formulation technique : c'est lui qui arbitre, entre les options présentées en
  conclusion générale, celle que le commanditaire valide.
- **L'encadrant pédagogique**, M. RABENANAHARY Rojo, encadre le stage du point de vue de la
  formation et évalue ce mémoire au regard du plan imposé.
- **Le stagiaire**, RANOMENJANAHARY Manjaka Alpha, auteur du projet, conçoit, développe, teste
  et documente. Il n'a pas d'équipe de développement : toute décision technique qu'il n'a pas pu
  trancher avec ses encadrants est écrite comme une question ouverte, pas comme un choix assumé.

> **Point d'honnêteté sur la taille de l'équipe.** Le stage a été mené à effectif constant
> et réduit : un développeur, deux encadrants, un commanditaire. Cela a des effets
> mesurables. D'abord, la revue de code et les tests de revue mutuelle, qui supposent au moins
> deux personnes, n'ont pas eu lieu : la seule relecture est celle que j'ai faite moi-même, ce
> qui limite la valeur de mes tests comme preuve externe. Ensuite, la séparation des rôles
> décrite plus haut n'a pas de contrepartie technique : il n'existe pas, dans le dépôt,
> d'outil de revue de code ni de piste d'audit permettant de distinguer une modification faite sous une
> consigne de celle prise en autonomie.

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

Trois objets rendent le projet rejouable : ce qui est versionné, ce qui est déclaré, et ce
qui est vérifié. Les séparer est ce qui permet à un tiers de reconstruire un résultat à
partir du dépôt seul, sans dépendre d'une machine encore allumée.

**Ce qui est versionné.** Le dépôt Git est la source de vérité du projet : code, scripts du
pipeline, configuration de référence, tests, et ce mémoire. Chaque jalon correspond à des
commits identifiables, et les documents de suivi (`ai/dev/logs.md`,
`ai/dev/suivi_avancement.md`) enregistrent ce qui a été décidé et pourquoi. Les données
patients ne sont pas versionnées : elles sont régénérées par le générateur synthétique, avec
une graine fixe (`RANDOM_SEED = 42`) qui rend la génération reproductible. Les secrets et les
fichiers de configuration contenant des identifiants sont exclus du dépôt et fournis par
variables d'environnement ; un hook de pré-commit bloque les identifiants connus avant qu'ils
n'atteignent l'historique. C'est une contrainte de sécurité, pas une commodité.

**Ce qui est déclaré, et non codé en dur.** Les sources de données, les chemins et les
identifiants sont décrits dans des fichiers de configuration lus au démarrage, jamais
écrits dans le code. Les paramètres qui gouvernent le comportement — le nombre de partitions,
le seuil de rapprochement à 0,80, les poids par champ, les finalités autorisées — sont
explicites et regroupés : les modifier ne demande pas de toucher à la logique, et le chapitre 8
peut ainsi annoncer des résultats reproductibles. Le manifeste des figures
(`documents/figures/manifest.json`) joue le même rôle pour la documentation : il associe chaque
diagramme à son chapitre et à sa ligne, et il est revérifié à chaque export.

**Ce qui est vérifié.** La suite de tests est exécutée à chaque jalon, et son résultat vert
constitue le critère de sortie du jalon suivant : on n'engage pas une évolution sur un niveau
de test cassé. Les journaux du pipeline (`elt.log`) conservent la trace des volumes traités à
chaque étape, ce qui permet de comparer une exécution à une autre sans la rejouer. La
rejouabilité est également une propriété du code : le pipeline est idempotent, et un
traitement peut être relancé depuis la zone SILVER sans dupliquer ni corrompre les zones
en aval.

> **Ce que cette gestion de la configuration ne fait pas.** Elle ne garantit pas
> l'exploitabilité en conditions de production : les fichiers de configuration contenant les
> identifiants sont locaux au poste de développement, et le déploiement automatisé sur un
> serveur du commanditaire n'a pas été réalisé. Ce qui est démontré ici, c'est la
> reproductibilité depuis le dépôt, pas la mise en production.

## 4.2 Contraintes et risques

**Contraintes techniques et environnementales.**

**Tableau 18 — Les six contraintes du stage et le traitement adopté pour chacune.**

| Contrainte | Nature | Traitement adopté |
|---|---|---|
| **VM 8 Go / 4 cœurs** | mémoire limitée (Spark gourmand) | `executor 4g / driver 2g`, `shuffle.partitions=8` [cahier_des_charges.md §11] |
| **Nœud distant MAVIS instable** | source PostgreSQL distante (`mavis_notheme`, 11 tables, tunnel SSH) | répliques locales de dev (`rebuild_mavis_db.py`, 73 090 lignes) ; données finales synthétiques |
| **Interdiction NLP lourd** | `sentence_transformers` crash sous **Python 3.8** | RapidFuzz + dictionnaire de synonymes (`fhir_synonyms.py`) |
| **Stockage Spark sur partage vboxsf interdit** | corruption `part-*.snappy.parquet` | warehouse toujours `hdfs://localhost:9000` |
| **Reproductibilité** | évaluation et dédup déterministes | seed 42, seuil 0.80, pondérations 0.5/0.3/0.1/0.1 fixes |
| **Données sensibles** | RGPD art. 9 | **synthétiques uniquement** + gouvernance implémentée dans le système |

Environnement de référence : VM `ubuntu/focal64` (Vagrant) — Hadoop 3.3.6, Hive
3.1.3, Spark 3.4.2, venv Python, ports redirigés (9870 HDFS, 10000 Hive, 5000 API)
[provision/Vagrantfile].

**Contexte local et conditions d'applicabilité.** Un prototype reproductible sur sa VM ne
devient un outil utilisable que si les contraintes du terrain ont été regardées. Quatre plans
de la réalité malgache conditionnent l'applicabilité du projet — et l'un d'entre eux n'a
**pas** pu être résolu dans le périmètre du stage, ce qui doit être dit.

**Tableau 19 — Les quatre plans de réalité du contexte local, et ce que chacun change à la solution ; le dernier reste non traité.**

| Plan de réalité | Observation de terrain | Conséquence sur la solution | État |
|---|---|---|---|
| **Données de santé dispersées** | chaque service tient son propre registre (pharmacie, consultation, imagerie), sans identifiant commun | justifie l'Entity Resolution et le MPI : l'identifiant partagé doit être **reconstruit**, pas supposé | traité |
| **Organisation et rôles** | le service concerné n'a pas de référentiel d'identité ; la clé d'accès est un couple (identifiant fonctionnel, mot de passe) | l'API d'accès a été conçue sur un modèle **clé API + rôle** plutôt que sur des comptes nominatifs, plus simple à configurer sans annuaire | traité |
| **Infrastructure et connectivité** | réseau intermittent, alimentation non garantie, pas de cluster | conception **mono-nœud** et **rejouable** : un run complet repart de zéro et produit le même résultat (seed fixe) | traité |
| **Données sensibles, contexte juridique** | cadre juridique national des données de santé **non vérifié** dans ce stage : seul le RGPD et la loi française ont été étudiés (§ 2.1.6) | la conformité présentée est **européenne**, à transposer au droit malgache (loi sur les données à caractère personnel, autorité de protection) | **non traité** |

Deux points doivent rester explicites, car ils sont les plus souvent omis dans un
projet de ce type :

1. **Le droit applicable n'est pas celui du pays de l'établissement.** Le stage
   s'est appuyé sur le RGPD [B10] et les recommandations CNIL [B11], [B12] parce
   que ce sont les références accessibles depuis le stage. Elles constituent un
   **cadre de conception exigeant** (finalité déterminée, minimisation,
   traçabilité, consentement explicite) et non une certification de conformité
   locale. La vérification du droit malgache — et de l'existence d'une autorité
   de contrôle — reste à faire avant toute mise en production.
2. **La volumétrie réelle n'a pas été utilisée.** Toutes les données sont
   synthétiques, générées à l'échelle du prototype (quelques centaines de lignes
   en SILVER, § 5.1.5). Le dimensionnement réel de l'établissement — volumétrie,
   cardinalité, taux de doublons observé — est **inconnu** et conditionne le choix
   du seuil de similarité (§ 2.1.3) comme le partitionnement du blocking.

> **Ce que le contexte local change concrètement.** Sans annuaire d'identité, la
> gestion des accès par clé API avec trois rôles est un compromis pragmatique et
> non un choix esthétique. Avec un annuaire, elle serait remplacée par du vrai
> RBAC nominatif ; le travail sur le consentement (§ 2.1.6, § 7.2.3) resterait
> inchangé, car il est indépendant du mode d'authentification.

**Risques du projet.** Le cahier des charges identifie les risques qui pouvaient bloquer le
projet ; le tableau ci-dessous les reprend avec la parade prévue et ce qu'il en est à la fin
du stage.

**Tableau 20 — Les risques du projet, leur impact, la parade prévue et le constat à la fin du stage.**

| Risque | Impact | Parade [cahier_des_charges.md §11] | Constat à la fin du stage |
|---|---|---|---|
| Mémoire limitée de la VM (8 Go) | performance Spark | `executor 4g / driver 2g`, `shuffle.partitions=8` | maîtrisé : pipeline 4/4 au run de référence |
| Nœud distant MAVIS instable | blocage du pipeline | sources locales de développement (Laragon, SQLite) puis synthétiques | contourné : le run de référence n'utilise que les sources CSV |
| Hétérogénéité des sources | mapping FHIR incomplet | synonymes + RapidFuzz, liens de clés étrangères à enrichir | partiellement maîtrisé : `patient_events_gold` reste vide (§ 8.6) |
| Données sensibles | confidentialité | données **synthétiques** uniquement, RBAC + audit + consentement | maîtrisé : aucune donnée réelle manipulée |
| Indisponibilité de la VM en fin de stage | re-validation impossible | tests hors VM (`pytest`) avant toute exécution réelle | réalisé en partie : planification et incrémental testés, **non rejoués** sur la VM (§ 7.3.2) |

## 4.3 Démarche mise en œuvre

Le travail s'est organisé en **cinq jalons**, chacun stabilisé (tests, évaluation) par un
critère de sortie vérifiable. Les deux PoC d'origine ont avancé en parallèle — `test_bigdata`
pour le moteur métier, `datalake_mavis` pour l'architecture Big Data — avant d'être fusionnés
dans le dépôt unique ; la règle du critère de sortie s'applique à l'intérieur de chaque chaîne.

**Tableau 21 — Les cinq jalons du stage : contenu, critère de sortie atteint, preuve correspondante et traces datées dans les journaux.**

| Jalon | Contenu | Critère de sortie | Preuve | Traces datées |
|---|---|---|---|---|
| **J1 — Socle** | générateur de données synthétiques + vérité terrain | 44 tests verts, 500 masters, 3 niveaux de difficulté | `evaluation/synthetic-patient-generator/` | MVP : 01/09/2026 |
| **J2 — Moteur** | canonique + blocking + exact/probabiliste (Pandas) | précision 1.000, parité Pandas = Spark | `engine/identity/`, `evaluation_truth.md` | 07–08/09/2026 |
| **J3 — Big Data** | pipeline ELT Medallion RAW → SILVER → GOLD | 4/4 étapes vertes, 214 lignes SILVER, 145 masters, 69 doublons | `run_pipeline.sh`, `elt.log` | PoC : 23/08–01/09 ; fusion : 07/09/2026 |
| **J4 — Gouvernance** | RBAC, clés API, consentement *purpose-by-purpose*, audit, refus 403 journalisé ; planification et reprise du pipeline | suite de tests complète verte, dont 403 et 401 vérifiés | `engine/governance/`, `tests/` | 01/09, 27–28/09/2026 |
| **J5 — Mémoire** | structuration selon le plan MBDS (introduction, huit chapitres, conclusion, glossaire en liminaire), état de l'art sourcé, mise en cohérence de la preuve | 20 références citées, aucun chiffre non vérifiable | ce dépôt | 08/09–28/09/2026 |

Le planning ci-dessous répartit ces jalons sur la durée du stage (6 juillet – fin octobre
2026, soit quatre mois). Il distingue ce qui est **daté** par les journaux du dépôt de ce qui
est **déclaré** sans trace datée, et de ce qui est **prévu**.

**Les premières semaines : une analyse itérative.** Avant toute ligne de code, le stage a
commencé par une phase d'analyse qui ne laisse pas de trace dans le dépôt : discussions avec
l'encadrant professionnel, compréhension du sujet, analyse de l'existant, documentation et
état de l'art — ce dernier à lui seul sur au moins trois semaines —, puis confrontation aux
problèmes et contraintes réels (nœud MAVIS instable, VM de 8 Go, Python 3.8). Ces activités
ne se sont pas enchaînées une fois pour toutes : elles **revenaient en boucle**, chaque
contrainte découverte relançant une discussion, une relecture de l'existant ou une recherche
documentaire. C'est ce qui justifie une démarche itérative plutôt qu'un cycle en cascade
(§ 4.1.2).

**Tableau 22 — Diagramme de Gantt du stage, par quinzaine : ■ période datée dans les journaux du dépôt, □ période déclarée, sans trace datée dans le dépôt, ○ prévu.**

| Phase | 06/07–19/07 | 20/07–02/08 | 03/08–16/08 | 17/08–30/08 | 31/08–13/09 | 14/09–27/09 | 28/09–11/10 | 12/10–31/10 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Cadrage** — discussions avec l'encadrant, compréhension du sujet | □ | □ | □ | | | | | |
| **Existant et contraintes réelles** — analyse des systèmes, capture des schémas, contraintes | □ | □ | □ | ■ | ■ | | | |
| **Documentation et état de l'art** (au moins 3 semaines) | | □ | □ | □ | ■ | ■ | | |
| **Développement** — PoC Big Data, MVP, fusion, moteur, gouvernance | | | | ■ | ■ | ■ | ■ | |
| **Tests** — évaluation ground-truth, suites `pytest`, runs VM | | | | ■ | ■ | ■ | ■ | |
| **Rédaction du mémoire** | | | | | ■ | ■ | ■ | ○ |
| **Finalisation et soutenance** | | | | | | | ○ | ○ |

> **Lecture honnête du planning.** Les journaux du dépôt commencent le 23/08/2026
> (`documents/journal_poc_datalake_mavis.md`) ; les semaines antérieures sont **déclarées** par le
> stagiaire et figurées comme telles, sans dates reconstituées. Le dépôt consolidé
> (`ai/dev/logs.md`) couvre ensuite la période du 07/09 au 28/09/2026. Les dernières
> quinzaines (finalisation, soutenance) sont **prévues**, non réalisées à la date de rédaction.

> **Ce que ce découpage a permis, et ce qu'il a coûté.** Il a rendu chaque jalon
> démontrable indépendamment, donc présentable en soutenance sans dépendre de la
> disponibilité de la VM. Il a en revanche consommé du temps de réintégration
> entre Pandas et Spark : la parité stricte exigeait de porter l'algorithme deux
> fois, ce qui n'aurait pas été nécessaire si le choix de l'échelle avait été
> arrêté plus tôt. C'est la principale leçon de conduite de projet tirée du stage
> (conclusion générale).

## 4.4 Budget

**Avertissement méthodologique.** Les montants ci-dessous sont des **hypothèses de travail
étiquetées**, construites sur l'ordre de grandeur des rapports de référence, et non des
comptes réels. Aucun de ces chiffres ne provient d'une facture ou d'un document comptable du
commanditaire. Ils sont présentés dans cette forme parce que les deux rapports de référence
comportent un budget, et qu'un mémoire sans cette rubrique laisserait cette question ouverte
au jury ; ils doivent être remplacés par les chiffres réels du commanditaire avant toute
diffusion. Ce qui est réel, en revanche, est indiqué séparément : les licences sont
réellement nulles, et le matériel est réellement déjà acquis.

Le budget couvre la **durée du stage, soit 4 mois** (6 juillet – fin octobre 2026), et le
**périmètre réalisé** : un prototype reproductible sur la VM de développement. La plateforme
n'ayant **pas été déployée** chez le commanditaire (§ 3.4), aucun coût de serveur de
production, d'hébergement ou d'exploitation n'est compté.

### 4.4.1 Coûts humains

**Tableau 23 — Coûts humains sur la durée du stage (hypothèses de travail, à remplacer par les chiffres réels du commanditaire).**

| Poste | Base de calcul | Coût mensuel (Ar) | Coût sur 4 mois (Ar) |
|---|---|---:|---:|
| Développeur (stagiaire) | 1 ETP sur la durée du stage | 1 000 000 | 4 000 000 |
| Encadrement professionnel et pédagogique | 2 × 0,1 ETP | 150 000 | 600 000 |
| **Sous-total coûts humains** | | **1 150 000** | **4 600 000** |

### 4.4.2 Coûts matériels et logiciels

**Tableau 24 — Coûts matériels et logiciels : le matériel est déjà acquis et les logiciels sont libres ; aucun achat n'a été nécessaire.**

| Poste | Détail | Coût (Ar) |
|---|---|---:|
| Poste de travail du développeur | matériel déjà acquis, aucun achat | 0 |
| Machine virtuelle du projet | fournie par le commanditaire, hébergée sur le poste existant | 0 |
| Serveur de production | non applicable : plateforme non déployée | 0 |
| Connexion Internet | déjà acquise | 0 |
| Big Data | Hadoop, Hive, Spark — open source | 0 |
| Bases et API | PostgreSQL, FastAPI, Flask, Next.js — open source | 0 |
| Bibliothèques et outils | Pandas, PySpark, RapidFuzz, `pytest`, Vagrant, VirtualBox, Git — open source | 0 |
| Solutions commerciales comparées (§ 2.2) | InterSystems EMPI, Talend MDM, Azure Health Data Services — étudiées sur documentation, non acquises | 0 |
| **Sous-total matériel et logiciel** | | **0** |

### 4.4.3 Coût total

**Tableau 25 — Coût total du projet sur la durée du stage.**

| Catégorie | Coût sur 4 mois (Ar) |
|---|---:|
| Coûts humains (hypothèses) | 4 600 000 |
| Coûts matériels et logiciels (réels) | 0 |
| **Total** | **4 600 000** |

> **Ce qui est vérifiable, et ce qui ne l'est pas.** Le **budget logiciel et matériel réel
> est zéro** : Hadoop, Spark, Hive, PostgreSQL, Next.js et l'ensemble des dépendances sont
> libres, aucune licence n'a été achetée, et le développement s'est fait sur un poste de
> travail et une machine virtuelle déjà existants, dont le commanditaire est le fournisseur.
> C'est un avantage décisif de l'open source dans un contexte où les moyens sont limités, et
> il est attesté par les fichiers de dépendances du dépôt. Le **coût humain ne l'est pas** :
> les montants du tableau sont des hypothèses, et le stage n'a pas été rémunéré, donc sa
> valorisation n'a de sens que par rapport à un coût de recrutement équivalent. Un déploiement
> en production ajouterait des postes non chiffrés ici (serveur, sauvegarde, exploitation). La
> ligne la plus sous-estimée de tout projet de ce type n'est d'ailleurs pas l'infrastructure,
> mais le temps passé à réconcilier deux implémentations d'un même algorithme, dont la parité
> stricte (§ 7.2.3) a fait un choix d'architecture et non un simple contrôle.

## Conclusion et transition

La démarche est posée : une méthode incrémentale à critères de sortie vérifiables, des rôles
clairs, des outils libres, une configuration rejouable, des contraintes traitées une à une et
un budget dont la part réelle est nulle. Le chapitre 5 décrit les **exigences réalisées**, vues
par l'utilisateur : ce que la plateforme fait, avec quelle qualité, et par quelles interfaces.

### Références

- `documents/cahier_des_charges.md` §9, §10, §11.
- `provision/Vagrantfile`, `bootstrap.sh`.
- `ai/dev/logs.md`, `ai/dev/suivi_avancement.md`, `documents/journal_poc_datalake_mavis.md`
  (dates des jalons J1 à J5).
- `documents/budget.md` (budget détaillé).

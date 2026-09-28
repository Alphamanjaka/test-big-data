<!--
Source du rapport de stage (format Word du master MBDS).
Générer : python projet/code-source/scripts/dev/build_rapport_stage_docx.py
Syntaxe : voir l'en-tête du script. Les chiffres proviennent des chapitres du mémoire
(chapters/) et de ai/memoire/contexte_projet.md ; toutes les données sont synthétiques.
-->

#= Remerciements

Je tiens à remercier toutes les personnes qui ont contribué au bon déroulement de ce stage et à la rédaction de ce rapport.

Je remercie la société **Madagascar Medical Technology (MMT)** de m'avoir accueilli au sein de son département Recherche et Développement, et de m'avoir confié un sujet à la hauteur des ambitions de la formation.

Je remercie tout particulièrement **M. Harena Ny Aina RABEMANOELA**, mon encadrant professionnel, pour sa disponibilité, ses conseils et la confiance qu'il m'a accordée tout au long du stage.

J'adresse mes sincères remerciements à **M. Rojo RABENANAHARY**, mon encadrant pédagogique, pour son suivi et ses orientations dans la conduite de ce travail.

Je remercie également l'ensemble de l'équipe pédagogique du **Master MBDS** pour la qualité des enseignements reçus, qui m'ont permis d'aborder ce projet.

Enfin, je remercie ma famille et mes proches pour leur soutien constant.

#= Résumé

Dans un établissement de santé, les données des patients sont réparties entre plusieurs systèmes d'information indépendants — consultations, pharmacie, imagerie, gestion hospitalière — qui ne partagent aucun identifiant commun. Une même personne y apparaît plusieurs fois, sous des formes différentes, et aucun système ne contrôle qui accède à ses données ni pour quelle finalité.

Ce stage, réalisé chez Madagascar Medical Technology (MMT), a porté sur la conception d'une plateforme de centralisation et de gouvernance de ces données. L'architecture retenue est un lac de données organisé en trois zones de qualité croissante (RAW, SILVER, GOLD) sur HDFS, Hive et Spark, alimenté par un pipeline ELT rejouable, incrémental et planifiable. Elle est complétée par un moteur de déduplication explicable, qui combine une passe exacte sur clés normalisées et une passe probabiliste par score pondéré, et par une gouvernance des accès associant rôles, consentement du patient par finalité et journal d'audit.

Sur le jeu de démonstration, la plateforme ramène 214 enregistrements à 145 patients, soit un taux de doublons de 32,24 %. Évaluée sur trois jeux synthétiques dont la vérité est connue, la déduplication atteint une précision de 1,000 sur tous les niveaux — aucune fusion à tort — et un rappel de 0,422 sur le jeu le plus difficile. Les implémentations Pandas et Spark produisent des résultats strictement identiques. Toutes les données manipulées sont fictives.

**Mots-clés** : données de santé, lac de données, architecture Medallion, Spark, Hive, FHIR, déduplication, Master Patient Index, consentement, RGPD.

#= Abstract

In a healthcare institution, patient data is spread across several independent information systems — consultations, pharmacy, imaging, hospital management — that share no common identifier. The same person appears several times in different forms, and no system controls who accesses their data or for what purpose.

This internship, carried out at Madagascar Medical Technology (MMT), focused on designing a platform to centralise and govern this data. The chosen architecture is a data lake organised in three zones of increasing quality (RAW, SILVER, GOLD) on HDFS, Hive and Spark, fed by a replayable, incremental and schedulable ELT pipeline. It is complemented by an explainable deduplication engine, combining an exact pass on normalised keys with a probabilistic pass based on a weighted score, and by access governance that associates roles, purpose-based patient consent and an audit log.

On the demonstration dataset, the platform reduces 214 records to 145 patients, a duplicate rate of 32.24 %. Evaluated on three synthetic datasets with known ground truth, deduplication reaches a precision of 1.000 at every level — no false merge — and a recall of 0.422 on the hardest dataset. The Pandas and Spark implementations produce strictly identical results. All data used is fictitious.

**Keywords**: healthcare data, data lake, Medallion architecture, Spark, Hive, FHIR, deduplication, Master Patient Index, consent, GDPR.

#= Table des matières

[[TOC]]

#! Liste des tableaux

[[LOT]]

#! Liste des figures

[[LOF]]

#! Liste des extraits de code

[[LOC]]

#! Glossaire

**Blocking** : technique qui ne compare que les fiches ayant une chance de correspondre (même début de nom, même date de naissance ou même CIN), au lieu de comparer toutes les paires.

**CIN (Carte d'Identité Nationale)** : numéro d'identité malgache, l'identifiant le plus stable d'un patient.

**CNIL (Commission Nationale de l'Informatique et des Libertés)** : autorité française de protection des données personnelles.

**CU** : cas d'utilisation.

**DMP (Data Management Platform)** : plateforme qui pilote la qualité des données d'un établissement.

**ELT (Extract, Load, Transform)** : extraction, chargement, puis transformation ; la donnée est d'abord déposée telle quelle, la transformation vient ensuite.

**EM (Expectation-Maximisation)** : algorithme qui estime automatiquement des paramètres, par exemple les poids d'un rapprochement.

**EMPI (Enterprise Master Patient Index)** : référentiel d'identité patient à l'échelle d'une organisation.

**ER (Entity Resolution)** : rapprochement des enregistrements qui désignent la même entité ; nom savant de la déduplication.

**ETP** : équivalent temps plein, unité de charge de travail.

**FHIR (Fast Healthcare Interoperability Resources)** : standard d'échange de données de santé, utilisé ici comme format commun entre les sources.

**FN, FP** : faux négatif (deux fiches d'une même personne non rapprochées) et faux positif (deux personnes différentes fusionnées à tort).

**Identity map** : table qui relie chaque fiche d'origine à son patient maître, avec la méthode et le score de la décision.

**MAVIS** : système de gestion hospitalière (Odoo) rencontré pendant le stage, répliqué localement pour le prototype.

**MPI (Master Patient Index)** : annuaire qui attribue à chaque personne un identifiant unique, le *master patient*, quel que soit le système d'origine de ses fiches.

**MVP (Minimum Viable Product)** : première version minimale ; ici, le prototype Pandas et PostgreSQL.

**NLP (Natural Language Processing)** : traitement automatique du langage.

**PoC (Proof of Concept)** : prototype de démonstration.

**Précision, rappel, F1** : la précision mesure la part des fusions correctes, le rappel la part des doublons retrouvés, le F1 le compromis des deux.

**RBAC (Role-Based Access Control)** : droits attachés à un rôle (`admin`, `analyst`, `viewer`) plutôt qu'à une personne.

**RGPD (Règlement Général sur la Protection des Données)** : règlement européen ; son article 9 encadre le traitement des données de santé.

**VM** : machine virtuelle ; ici, la machine Vagrant qui héberge la plateforme Big Data.

[[FIN_LIMINAIRES]]

#! Introduction

Comme la plupart des organisations de santé, un établissement fait coexister plusieurs systèmes d'information indépendants : consultations, pharmacie, laboratoire, imagerie, dossiers médicaux. Chacun possède sa propre base, son propre format et ses propres identifiants. Le même patient y est donc enregistré plusieurs fois, sous des formes différentes, sans qu'aucun système ne sache qu'il s'agit de la même personne.

Deux évolutions rendent ce problème pressant. D'une part, la quantité de données produites augmente, et leur exploitation relève désormais des architectures **Big Data** : des données trop nombreuses ou trop variées pour un seul poste de travail, qu'il faut stocker et traiter de façon répartie. D'autre part, les données de santé sont des données sensibles : leur usage doit être **gouverné**, c'est-à-dire contrôlé selon qui les demande, pour quelle finalité et avec l'accord du patient.

Ce sujet m'a attiré parce qu'il réunit, dans un seul projet, les trois volets de la formation MBDS — les bases de données, l'intégration de systèmes hétérogènes et le traitement de données à grande échelle — et parce qu'il m'a permis de passer de la théorie à la pratique du Big Data : installer un lac de données, écrire des traitements Spark, et comprendre pourquoi chaque technologie est introduite plutôt que de l'employer par effet de mode.

Le stage, d'une durée de quatre mois, s'est déroulé du 6 juillet à fin octobre 2026 au sein du département Recherche et Développement de **Madagascar Medical Technology (MMT)**. La mission confiée était de concevoir une plateforme de centralisation et de gouvernance des données patients : intégrer des sources hétérogènes, nettoyer et standardiser les données, reconnaître les patients présents dans plusieurs systèmes, et contrôler l'accès aux données selon le consentement du patient. Deux contraintes du commanditaire encadrent ce travail : les données doivent rester sur les machines de l'établissement (**hébergement interne**), et seules des **données synthétiques** peuvent être utilisées. La plateforme est livrée sous forme de prototype reproductible ; elle n'a pas été déployée en production.

La problématique peut se formuler ainsi : **comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités et la gouvernance des accès basée sur le consentement du patient ?**

Pour y répondre, ce rapport présente d'abord le cadre du stage (chapitre 1) et l'état de l'art du domaine (chapitre 2). Il étudie ensuite l'existant et la solution envisagée (chapitre 3), puis la démarche de projet suivie (chapitre 4). Les exigences réalisées (chapitre 5), l'architecture (chapitre 6) et la conception du logiciel (chapitre 7) décrivent la solution construite ; les tests et l'évaluation (chapitre 8) en mesurent la qualité. La conclusion dresse le bilan, les limites et les perspectives.

# Présentation du stage

## Présentation de l'entreprise

La société **Madagascar Medical Technology (MMT)** a été créée en 2009 afin de répondre aux besoins des professionnels de la santé à Madagascar. Son activité englobe la distribution et la maintenance de matériels biomédicaux, la fourniture de consommables, ainsi que la gestion de stock des établissements partenaires.

L'entreprise réunit une équipe spécialisée dans l'ingénierie biomédicale, qui accompagne l'évolution technologique du secteur. Dans le cadre de son développement, MMT a conclu une convention avec Siemens Healthineers, qui lui confère le statut de *Business Partner* à Madagascar, avec un rattachement direct à la branche sud-africaine du groupe.

Depuis 2024, l'entreprise dispose d'un **département Recherche et Développement**, chargé de la gestion des systèmes d'information médicale ainsi que des infrastructures et réseaux informatiques. C'est dans ce département que s'est déroulé le stage. Les systèmes rencontrés illustrent ce périmètre : une base de gestion hospitalière fondée sur GNU Health, une plateforme de gestion hospitalière distante fondée sur Odoo (MAVIS) et la base d'une clinique ; ils sont décrits au chapitre 3.

## Présentation du sujet et objectifs du projet

### Contexte métier

Le même patient est enregistré dans plusieurs systèmes, sous des formes différentes. Dans le cas de référence de la plateforme, trois fiches désignent une seule et même personne :

Tableau: Trois enregistrements d'un même patient fictif dans trois systèmes différents.
| Système | Nom | CIN | Date de naissance |
|---|---|---|---|
| Pharmacie | Jean Rakoto | 101 02404 5 | 1990-01-10 |
| Consultation | Rakoto Jean | 101024045 | 10/01/1990 |
| Imagerie | J. RAKOTO | 101024045 | 1990/01/10 |

Cette situation pose trois problèmes concrets :

1. **La dispersion** : les données d'un patient sont réparties entre plusieurs bases, sans vue globale.
2. **L'hétérogénéité** : identifiants, libellés et formats diffèrent ; le genre, par exemple, s'écrit `H/F`, `male/female` ou `Homme/femme` selon la source.
3. **L'absence de gouvernance** : rien ne garantit qui peut accéder à quelle donnée, pour quelle finalité et dans quelles conditions.

### Objectifs

Les objectifs s'appuient sur quatre notions qui reviennent tout au long du rapport : l'ELT, le modèle Medallion, le Master Patient Index et le consentement par finalité. La figure ci-dessous les résume, chacune illustrée sur le cas de référence.

Figure: Les quatre notions clés du rapport : ELT, modèle Medallion, Master Patient Index et consentement par finalité. | documents/figures/notions_cles.png | 16

Le cahier des charges fixe six objectifs, qui structurent l'ensemble du projet.

Tableau: Les six objectifs du cahier des charges et leur traduction concrète.
| N° | Objectif | Traduction concrète |
|:---:|---|---|
| 1 | **Centraliser** les données dans une architecture Big Data | pipeline ELT Medallion RAW → SILVER → GOLD |
| 2 | **Nettoyer et standardiser** selon un modèle commun | modèle canonique du patient et schéma pivot FHIR |
| 3 | **Dédupliquer** avec une logique toujours explicable | patient maître, identity map, score, méthode et seuil |
| 4 | **Gouverner les accès** | rôles, consentement par finalité, audit d'accès, clés API hachées |
| 5 | **Visualiser** les indicateurs | vues de déduplication et de consentement (frontend optionnel) |
| 6 | **Évaluer** la déduplication | vérité terrain, précision, rappel et F1 |

### Enjeux et risques

La dispersion des données entraîne des risques d'erreurs médicales (dossier éclaté), des analyses faussées (agrégats comptant des fiches plutôt que des patients) et des failles de confidentialité. Chaque enjeu porte un risque que la solution doit maîtriser.

Tableau: Les enjeux du sujet, le risque associé et la manière dont il est maîtrisé.
| Enjeu | Risque à maîtriser | Maîtrise démontrée |
|---|---|---|
| Un dossier patient complet | fusionner à tort deux personnes distinctes, l'erreur la plus grave en santé | précision de 1,000, aucun faux positif sur les trois jeux évalués (section 8.4) |
| Des indicateurs justes | des agrégats faussés par les doublons, ou une fusion impossible à justifier | chaque fusion porte sa méthode, son score et son explication (section 7.2.3) |
| Des accès maîtrisés | exposer une donnée sans consentement, ou refuser sans trace | refus 403 journalisé avec son motif (section 8.3) |
| Une démarche reproductible | dépendre d'une machine, d'un réseau instable ou de données réelles | données synthétiques à graine fixe, pipeline rejouable (section 4.1.5) |

# État de l'art sur le sujet traité

Cet état de l'art répond à des questions formulées à l'avance à partir du cahier des charges : quelle théorie fonde le rapprochement d'identités, quelles mesures de similarité sont utilisables sous Python 3.8, comment éviter la comparaison de toutes les paires, quel standard de santé retenir, quelle base légale pour des données de santé, quelles briques Big Data mobiliser, et que propose déjà le marché. Les sources privilégiées sont primaires (publications, spécifications, documentations officielles). Les produits comparés n'ont **pas été installés** : leur comparaison porte sur les capacités annoncées par leur documentation.

## Notions de référence

### Le rapprochement d'identités (Entity Resolution)

Déterminer si des enregistrements issus de sources différentes désignent la même personne est un problème générique appelé **Entity Resolution**, ou *record linkage* [1], [3]. Ses fondements théoriques datent de 1969 : Fellegi et Sunter formalisent la décision d'appariement de deux enregistrements en comparant leurs champs et en concluant à un match, un non-match ou un match indéterminé [2]. Ce modèle probabiliste reste la référence des systèmes modernes [1].

Le processus générique se décompose en cinq étapes [1], [3], toutes appliquées dans le projet : le **prétraitement** normalise les champs (casse, accents, CIN, dates) ; l'**indexation** (*blocking*) réduit les comparaisons à des groupes de candidats ; la **comparaison** mesure la similarité champ par champ ; la **classification** décide match ou non-match ; l'**évaluation** mesure la qualité sur une vérité terrain. Le résultat attendu est une réconciliation d'identités : chaque personne est reconnue comme une seule entité, sans fusion erronée de personnes distinctes. Tout l'enjeu est l'équilibre entre **précision** (ne pas fusionner à tort) et **rappel** (retrouver tous les doublons).

### Mesures de similarité et blocking

Les variantes *Jean Rakoto*, *Rakoto Jean* et *J. RAKOTO* imposent de comparer des chaînes de caractères et non de simples égalités. Les mesures classiques du domaine sont présentées dans le tableau ci-dessous.

Tableau: Les mesures de similarité classiques et leur usage dans le rapprochement d'identités.
| Mesure | Principe | Usage typique |
|---|---|---|
| Levenshtein | nombre minimal d'insertions, suppressions et substitutions | nom, prénom |
| Damerau (OSA) | Levenshtein avec transposition de deux caractères adjacents | fautes de frappe |
| Jaro-Winkler | similarité qui favorise un début de chaîne commun | initiales, noms tronqués |
| Mesures par mots | comparaison des mots indépendamment de leur ordre | *Rakoto Jean* et *Jean Rakoto* |

Le projet utilise **RapidFuzz** [4], bibliothèque libre qui implémente ces mesures de façon performante. Son intérêt est opérationnel : légère et compatible avec Python 3.8, elle évite les dépendances de traitement du langage lourdes, dont la bibliothèque `sentence_transformers`, qui plantait sous Python 3.8 dans l'environnement du stage.

Comparer chaque enregistrement à tous les autres est quadratique : pour *n* patients, de l'ordre de *n²* comparaisons, soit 10¹² pour un million de patients. La pratique standard, le **blocking**, regroupe les enregistrements en blocs de candidats partageant une clé grossière — préfixe du nom, date de naissance, CIN — et ne compare qu'à l'intérieur de ces blocs [1], [3].

### Master Patient Index et interopérabilité FHIR

En santé, le rapprochement aboutit à un **Master Patient Index** : chaque fiche des bases sources est rattachée à un identifiant unique, le *master patient*, par une **identity map** traçable.

Tableau: Exemple d'identity map : trois fiches rattachées au même patient maître.
| Source | Identifiant source | Patient maître | Score | Méthode |
|---|---|---|---:|---|
| pharmacy | 15 | 102 | 1,000 | exacte |
| consultation | 88 | 102 | 0,950 | probabiliste |
| imaging | IMG-20 | 102 | 0,920 | probabiliste |

Cette démarche rejoint le standard **FHIR** (HL7 *Fast Healthcare Interoperability Resources*), qui prévoit une opération dédiée, `$match` : à partir des champs d'un patient, elle retourne les correspondances candidates avec un score explicite [5]. Le projet en reprend la philosophie — rechercher puis apparier par score — sans serveur FHIR. FHIR sert aussi de **schéma pivot** : quatre ressources (`Patient`, `Encounter`, `Condition`, `Observation`) harmonisent des sources structurées différemment.

### Consentement et RGPD

Les données de santé sont une catégorie particulière de données personnelles : leur traitement est **en principe interdit** par l'article 9 du RGPD, sauf exceptions, dont le **consentement explicite** de la personne [10]. La CNIL précise que la base légale (article 6) et l'exception propre aux données sensibles (article 9) se cumulent, et que le consentement au traitement des données diffère du consentement aux soins [11], [12]. Le projet traduit ces principes en mécanismes vérifiables.

Tableau: Traduction des exigences du RGPD en mécanismes implémentés.
| Exigence | Mécanisme implémenté dans la plateforme |
|---|---|
| Finalité déterminée (art. 5.1.b) | la finalité est déclarée et obligatoire à chaque requête, dans une liste fermée : `api_access`, `research`, `analytics` |
| Consentement explicite (art. 9.2.a) | table des consentements par patient et par finalité ; refus par défaut en l'absence d'avis ; le dernier avis enregistré prévaut |
| Refus effectif | un utilisateur autorisé dont la finalité n'est pas consentie reçoit un refus (code 403) |
| Traçabilité (art. 30) | chaque appel est journalisé, y compris la finalité demandée et le motif d'un refus |
| Minimisation (art. 5.1.c) | les clés d'API sont stockées sous forme d'empreinte SHA-256, jamais en clair |

### Architecture Big Data : HDFS, Spark, Hive et Medallion

**HDFS** (*Hadoop Distributed File System*) est le socle de stockage réparti : un NameNode gère les métadonnées, des DataNodes stockent les blocs de données [6]. **Apache Spark** a remplacé en pratique le modèle MapReduce en conservant les données en mémoire entre les étapes de calcul ; il est utilisé ici par son interface Python, PySpark [7]. **Hive** apporte une couche SQL au-dessus du lac : un catalogue (*metastore*) décrit les tables et un service (HiveServer2) exécute les requêtes [8].

Le modèle **Medallion** organise le lac en zones de qualité croissante — RAW, SILVER, GOLD [9]. Chaque zone est un état distinct de la donnée, ce qui apporte la traçabilité (on sait d'où vient chaque valeur), le rejeu (relancer un traitement depuis une zone propre) et la séparation exigée par la gouvernance. Le pipeline suit la logique **ELT** : l'ingestion charge la donnée brute dans RAW, la transformation s'applique ensuite — c'est le principe du *schema-on-read*, où le format est décidé au moment de la lecture.

Un constat mesuré pendant le stage nuance l'intérêt de Spark : sur de petits volumes (6 à 36 lignes), Pandas répond en 1 à 2 millisecondes contre 0,4 à 4 secondes pour Spark, dont le démarrage domine. Spark se justifie donc par le **volume** visé ; le projet le conserve aussi pour démontrer que la logique métier reste identique lorsqu'on change d'échelle.

## Critères de comparaison

Six critères découlent de ces notions, du problème posé et des contraintes du stage :

1. **Déduplication explicable** : chaque fusion porte un score, une méthode et une justification.
2. **Interopérabilité FHIR** : la solution sait lire ou produire le format pivot de santé.
3. **Gouvernance rôle, consentement et audit** : l'accès est contrôlé par le rôle, la finalité consentie et une trace.
4. **Montée en charge Big Data** : la solution s'appuie sur un stockage et un calcul répartis.
5. **Hébergement interne** : les données restent sur les machines de l'établissement.
6. **Faisabilité dans l'environnement du stage** : une VM de 8 Go et Python 3.8.

## Étude de chaque solution au vu des critères

Quatre familles de produits couvrent partiellement le besoin : les référentiels d'identité patient (MPI), les plateformes de gestion des données de référence (MDM), les services cloud de santé et les briques open source.

**InterSystems EMPI** [13] est un référentiel d'identité patient de référence. Il combine rapprochement déterministe et probabiliste, construit un enregistrement composite par personne et expose les services d'identification standard du secteur (IHE PIX et PDQ). C'est toutefois un produit propriétaire sous licence, dont l'atout principal repose sur un référentiel externe de population, incompatible avec l'hébergement interne ; il ne couvre ni le lac de données ni la gouvernance par consentement.

**Talend MDM** [14] propose un rapprochement intégré avec règles de fusion, construction d'une fiche de référence (*golden record*) et validation par des gestionnaires de données. La suite est lourde et commerciale, sans interopérabilité FHIR native, et ne traite pas le contrôle d'accès aux données patients.

**Azure Health Data Services** [17] fournit des services FHIR et DICOM managés, un export massif vers un lac de données et un service de dé-identification. Il s'agit d'un service cloud, incompatible avec la contrainte d'hébergement interne, qui ne fournit par ailleurs ni MPI ni déduplication.

**HAPI FHIR** [16] est l'implémentation open source de référence d'un serveur FHIR (validation, stockage, recherche, opération `$match`). Il apporte l'interopérabilité, mais ni rapprochement d'identités, ni gouvernance, ni zones de qualité.

**Splink** [15] est une bibliothèque open source de rapprochement probabiliste à grande échelle, fondée sur le modèle de Fellegi-Sunter, avec estimation automatique des poids par l'algorithme EM et exécution sur Spark (environ un million d'enregistrements en une minute selon ses auteurs). Il excelle sur le cœur algorithmique, mais ses poids estimés sont difficilement lisibles par un gestionnaire de données, et il n'offre ni gouvernance ni audit.

**Apache Atlas** [18] est un catalogue de métadonnées pour l'écosystème Hadoop : lignage des données de bout en bout et classification des données sensibles. Il gouverne les métadonnées mais n'exerce aucun contrôle d'accès au moment de la requête, ni consentement par finalité, ni journal d'accès.

## Tableau comparatif des solutions

Le tableau suivant applique les six critères à chaque solution. Pour les produits, il s'agit de capacités annoncées par la documentation ; pour la solution du stage, la mention « testé » signale une mesure dans le dépôt et « conçu » un mécanisme vérifié par les tests mais sans données réelles en base au moment du run.

Tableau: Comparaison des solutions existantes et de la solution du stage (✔ oui, ◐ partiel, ✖ non).
| Critère | EMPI | Talend | Azure | HAPI | Splink | Atlas | Stage |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Déduplication explicable | ✔ | ✔ | ✖ | ✖ | ◐ | ✖ | ✔ testé |
| Interopérabilité FHIR | ◐ | ✖ | ✔ | ✔ | ✖ | ✖ | ✔ testé |
| Rôle, consentement et audit | ◐ | ◐ | ✔ | ✖ | ✖ | ◐ | ✔ conçu |
| Montée en charge Big Data | ◐ | ✔ | ✔ | ✖ | ✔ | ✔ | ✔ testé |
| Hébergement interne | ✔ | ✔ | ✖ | ✔ | ✔ | ✔ | ✔ testé |
| VM 8 Go et Python 3.8 | ✖ | ✖ | ✖ | ✖ | ◐ | ✖ | ✔ testé |

Aucun produit ne satisfait les six critères. Les solutions les plus complètes sur l'identité (EMPI, Talend) sont les plus lourdes et les plus coûteuses ; les solutions compatibles avec l'hébergement interne ne résolvent ni le rapprochement, ni la gouvernance, ni l'explicabilité. Le délai de quatre mois et l'environnement entièrement interne achèvent d'écarter l'adoption d'un produit.

## Pertinence entre le projet et l'état de l'art

Le projet ne réinvente pas les concepts : il **réutilise les standards et les algorithmes existants** et ne développe que la chaîne d'exécution et de gouvernance qu'aucune solution ne fournit dans le contexte imposé.

Tableau: Ce que le projet reprend de l'état de l'art et comment il l'implémente.
| Élément repris | Provenance | Implémentation retenue |
|---|---|---|
| Décision match / non-match | Fellegi-Sunter [2] | score pondéré explicable (0,5 / 0,3 / 0,1 / 0,1), seuil 0,80 |
| Appariement par score | FHIR `$match` [5] | même principe dans le moteur, sans serveur FHIR |
| Schéma pivot | FHIR [5] | quatre entités : patient, rencontre, pathologie, observation |
| Zones de qualité croissante | Medallion [9] | RAW, SILVER, GOLD sur HDFS et Hive |
| Référentiel d'identité | MPI [13] | patient maître et identity map dans PostgreSQL |
| Gouvernance | catalogue de métadonnées [18] | contrôle appliqué à chaque requête : rôle, consentement, audit |

Trois écarts à l'existant sont assumés. Le projet n'utilise pas d'estimation automatique des poids comme Splink, afin que les poids restent lisibles et modifiables par un gestionnaire de données. Il n'utilise pas de référentiel externe comme EMPI, afin qu'aucune donnée tierce n'entre dans la plateforme. Il n'utilise pas de service managé comme Azure, le lac restant interne à la VM. Le risque propre à une chaîne sur mesure est la maintenabilité ; il est réduit en déclarant les poids, le seuil et la stratégie de blocking dans un fichier de configuration unique, lu à la fois par le moteur, sa version Spark et l'évaluation.

# Étude de l'existant et solution envisagée

## Étude de l'existant

### Description externe du système existant (vision utilisateur)

Du point de vue d'un utilisateur, chaque service travaille dans son propre logiciel : la gestion hospitalière s'appuie sur MAVIS, une application Odoo étendue par un module hospitalier ; les dossiers médicaux relèvent de GNU Health ; une clinique tient ses patients, visites, diagnostics et observations dans une base à part. Chaque logiciel est complet dans son périmètre : on y crée un patient, on y consulte son historique, on y saisit ses actes.

L'utilisateur ne peut pas, en revanche, passer d'un système à l'autre. Une recherche de patient ne renvoie que les fiches du logiciel ouvert. La même personne apparaît sous des formes différentes selon le service, sans que rien ne le signale. Enfin, aucun écran n'indique qui a consulté un dossier, pour quelle finalité, ni si le patient y a consenti. Cette vision est reconstituée à partir des schémas capturés et du cahier des charges ; aucune enquête auprès des utilisateurs n'a été conduite.

### Description interne du système existant (vision développeur)

Les schémas et volumes des systèmes rencontrés ont été capturés et consignés au cours du stage.

Tableau: Les sources étudiées : socle technique, volume vérifié et particularités.
| Source | Socle | Volume vérifié | Tables retenues | Particularités |
|---|---|---|---|---|
| MAVIS | Odoo et module hospitalier, PostgreSQL distant | 73 090 lignes en réplique locale ; 1 260 tables sur le nœud distant | 11, dont `hms_patient` et `res_partner` | nœud distant instable ; jointure patient–partenaire vérifiée sur 9 791 lignes sur 9 791 |
| MMT_DB | GNU Health, PostgreSQL local | 60 271 lignes, 9 tables | 3 : patients, personnes, familles | 5 clés étrangères découvertes automatiquement |
| CLINIQUE | SQLite | 54 582 lignes, aucune violation de clé | 4 : patients, visites, diagnostics, observations | seule source déjà alignée sur les entités FHIR |
| Démonstration | fichiers CSV synthétiques | 76 / 76 / 62 au run de référence | patients et transactions | pharmacie, consultation, imagerie (graine 42) |

Capture: C01 | Structure de la base MAVIS vue dans un client SQL (schéma uniquement). | C01_schema_mavis.png | Optionnel. Liste des tables ou diagramme du schéma MAVIS (DBeaver, pgAdmin) ; aucune ligne de données patient ne doit être visible.

Chaque base est cohérente avec elle-même : l'intégrité référentielle existe à l'intérieur d'une source. C'est l'absence d'équivalent **entre** sources qui pose problème. Les données réelles ne pouvant pas être utilisées, trois sources synthétiques reproduisent l'hétérogénéité observée, sur un triple plan :

- **Structure** : le nom tient en une colonne ou en deux (prénom et nom) ; l'identifiant change de nom et de format selon la source (`PH000001`, `MED000001`, `IMG000001`).
- **Vocabulaire** : le genre s'écrit `H/F` en pharmacie, `male/female` en consultation, `Homme/femme` en imagerie.
- **Formats** : les dates s'écrivent `01/02/1934`, `08-06-1943` ou `1934-02-01` ; le CIN est espacé, compact ou absent (environ 25 % des patients).

## Critique de l'existant

L'analyse fait ressortir cinq manques :

1. **Aucun identifiant patient transversal.** Chaque base possède son propre espace d'identifiants. Le CIN, seul identifiant métier stable, est absent pour environ un quart des patients.
2. **Aucune normalisation commune.** Il n'existe pas de schéma pivot : libellés, dates et numéros obéissent à des conventions différentes.
3. **Aucun rapprochement d'identités.** Le prototype Big Data initial avait compté 24 872 marqueurs de doublon dans ses tables nettoyées (run du 24/08/2026), mais sans référentiel patient ni justification traçable des fusions.
4. **Aucune gouvernance des accès.** Ni rôles, ni consentement par finalité, ni journal d'accès, alors que le cahier des charges exige un hébergement interne et un contrôle par le couple rôle et consentement.
5. **Aucun espace de rejeu.** Sans zone brute de référence, une erreur de traitement ne peut pas être rejouée proprement ; un incident du prototype initial a ainsi laissé la table des patients avec les 9 791 patients d'une seule source au lieu de l'union de toutes les sources.

Figure: L'existant à MMT : trois systèmes isolés, cinq manques et la réponse apportée par le projet. | documents/figures/fig-1.png | 15

## Solutions envisagées

### Adopter un produit ou construire une chaîne adossée aux standards

Deux voies étaient ouvertes. La première, adopter un produit, est écartée par l'état de l'art : aucune solution ne couvre les six critères dans les contraintes du stage. La seconde, une **chaîne sur mesure adossée aux standards**, a été retenue et construite progressivement.

### Une progression en trois niveaux

Le projet ne part pas d'un besoin de « Big Data pour le Big Data ». Chaque technologie est introduite **par un besoin** :

- **Niveau 1 — MVP** : fichiers CSV, Pandas et PostgreSQL pour l'extraction, le nettoyage, la déduplication et le patient maître. L'objectif est de résoudre d'abord le problème métier, au plus simple.
- **Niveau 2 — Spark** : le même moteur porté en PySpark, avec des résultats strictement identiques au MVP. L'objectif est de changer d'échelle sans changer la logique.
- **Niveau 3 — Big Data** : lac de données HDFS, Hive et Spark, pipeline ELT Medallion planifiable et rejouable, API d'exposition. L'objectif est une architecture adaptée à des volumes réels.

Deux étapes transverses complètent cette progression : la **validation des algorithmes** sur une vérité terrain, qui conditionne le passage à l'échelle, puis la **gouvernance** (consentement, audit, API), qui s'appuie sur la zone GOLD. On ne passe pas à l'échelle et on n'ouvre pas les accès avant que la preuve soit établie.

Les deux premiers niveaux proviennent d'un premier prototype consacré à la déduplication et à la gouvernance ; le troisième provient d'un second prototype consacré à l'architecture Big Data. Le dépôt final en est la **fusion consolidée** : un seul code, une seule documentation, un moteur de déduplication intégré au lac de données.

### Un contrat de normalisation

L'hétérogénéité relevée a été convertie en un **contrat de normalisation explicite**, appliqué à chaque champ avant toute comparaison.

Tableau: Le contrat de normalisation : règle appliquée à chaque champ et comportement en cas d'échec.
| Champ | Règle de normalisation | En cas d'échec |
|---|---|---|
| Genre | liste fermée de libellés masculins et féminins ramenés à `M` ou `F` | valeur vide, jamais devinée |
| CIN | seuls les chiffres sont conservés | valeur vide si la longueur sort de 6 à 12 chiffres |
| Date de naissance | format ISO, sinon lecture jour-mois-année | date inconnue |
| Nom | accents, casse et ponctuation supprimés | chaîne vide si le nom est absent |

Une règle gouverne les quatre champs : **aucune valeur n'est devinée**. Un champ douteux produit une valeur vide, qui exclut l'enregistrement du rapprochement exact et le renvoie vers la voie probabiliste ; il ne peut donc pas provoquer une fusion exacte erronée.

## Objectifs principaux et livrables

Les objectifs principaux sont les six objectifs du cahier des charges, traduits en exigences vérifiables au chapitre 5. Le périmètre couvert comprend : le pipeline ELT en cinq étapes avec reprise, ingestion incrémentale et planification ; le moteur de déduplication exact et probabiliste, en Pandas et en PySpark ; la gouvernance (rôles, consentement par finalité, audit, clés hachées) ; deux API REST ; et l'évaluation de la déduplication sur trois niveaux de difficulté. Les tableaux de bord d'analyse et le déploiement chez le commanditaire sont hors périmètre.

Tableau: Les livrables prévus au cahier des charges et leur état à la fin du stage.
| N° | Livrable | État à la fin du stage |
|:---:|---|---|
| 1 | Code source complet dans un dépôt unique | réalisé |
| 2 | Pipeline ELT Big Data | réalisé ; 4 étapes sur 4 réussies au run de référence du 07/09/2026, orchestration portée depuis à 5 étapes |
| 3 | Moteur de déduplication et évaluation sur vérité terrain | réalisé |
| 4 | Base centrale PostgreSQL (patients maîtres, consentements, audit) | schéma réalisé et testé ; base non peuplée pendant le stage |
| 5 | API des indicateurs et API de gouvernance | réalisé |
| 6 | Documentation technique et manuel conceptuel | réalisé |
| 7 | Frontend (optionnel) | réalisé partiellement : pilotage du pipeline et consultation des patients |
| 8 | Rapport de stage et support de soutenance | ce document ; support de soutenance |

# Démarche projet

## Principes de la démarche projet

### Activités d'ingénierie logicielle

Le projet a mobilisé les cinq activités classiques de l'ingénierie logicielle, chacune ayant laissé une production vérifiable dans le dépôt.

Tableau: Les activités d'ingénierie logicielle et leurs productions.
| Activité | Production |
|---|---|
| Analyse | cahier des charges consolidé, capture des schémas sources, exigences fonctionnelles |
| Conception | architecture en trois niveaux, modèle canonique, schéma de la base centrale, règles de gouvernance |
| Développement | générateur de données synthétiques, moteur de déduplication (Pandas et Spark), pipeline ELT, API, frontend optionnel |
| Tests et évaluation | suites de tests automatisés, évaluation sur vérité terrain, exécutions du pipeline |
| Documentation et suivi | journal daté, suivi d'avancement, manuel conceptuel, rapport |

### Méthode de gestion de projet utilisée

Le stage a suivi une **démarche itérative et incrémentale par jalons**. Elle emprunte aux méthodes agiles l'idée d'incréments démontrables — chaque jalon livre un résultat qui fonctionne et se vérifie — et celle d'un critère de sortie explicite, qui joue le rôle de « définition de terminé ». Elle n'en reprend pas les cérémonies (sprints, revues d'équipe), l'équipe de développement se limitant à une personne.

Quatre règles de pilotage ont été appliquées : ne pas engager une évolution avant que les tests du niveau précédent soient verts ; tracer chaque décision d'architecture avec sa raison ; écrire chaque limite constatée plutôt que la passer sous silence ; ne jamais remplacer les données de test par des données réelles.

### Rôles et responsabilités

Les parties prenantes sont au nombre de quatre :

- **Le commanditaire**, MMT, représenté par l'encadrant professionnel. Il porte les deux contraintes structurantes du stage : l'hébergement interne et l'usage exclusif de données synthétiques. Il valide les trois finalités d'accès.
- **L'encadrant professionnel**, M. Harena Ny Aina RABEMANOELA, fait le lien entre le besoin métier et sa formulation technique, et arbitre entre les options proposées.
- **L'encadrant pédagogique**, M. Rojo RABENANAHARY, suit le stage du point de vue de la formation.
- **Le stagiaire**, auteur du projet, conçoit, développe, teste et documente la plateforme.

L'effectif réduit a une conséquence qu'il convient de mentionner : la revue de code croisée n'a pas eu lieu, ce qui limite la valeur des tests comme preuve externe. Ces rôles de projet sont distincts des rôles applicatifs (`admin`, `analyst`, `viewer`) qui régissent l'accès aux données une fois le logiciel livré (section 7.2.3).

### Outils

Les outils retenus sont tous libres ou gratuits. Ils sont présentés par usage, avec la version effectivement employée.

Tableau: Les outils du projet, regroupés par usage. {logos}
| Usage | Outil | Version | Description |
|---|---|---|---|
| Développement | logo:vscode Visual Studio Code | 1.139 | éditeur du code, des scripts du pipeline et de la documentation |
| ^ | logo:python Python | 3.8 | langage du moteur de déduplication, du pipeline et des API ; version imposée par la VM |
| ^ | logo:nodejs Node.js | 22.21 | exécution de l'interface web et du rendu des diagrammes |
| ^ | logo:git Git | 2.45 | versionnement ; un hook de pré-commit bloque les secrets |
| Environnement | logo:vagrant Vagrant | 2.4.9 | description et provisionnement reproductibles de la VM |
| ^ | logo:virtualbox VirtualBox | 7.2.8 | hyperviseur de la VM (8 Go, 4 cœurs) |
| ^ | logo:ubuntu Ubuntu | 20.04 | système de la VM (image `ubuntu/focal64`) |
| ^ | logo:laragon Laragon | — | bases locales de développement sur le poste Windows |
| Big Data | logo:hadoop Hadoop | 3.3.6 | HDFS stocke les zones du lac ; YARN exécute les traitements |
| ^ | logo:hive Hive | 3.1.3 | catalogue des tables du lac et accès SQL |
| ^ | logo:spark Spark / PySpark | 3.4.2 | traitements répartis : mapping FHIR, déduplication, zone GOLD |
| ^ | logo:openjdk OpenJDK | 8 | machine Java requise par Hadoop, Hive et Spark |
| Données et moteur | logo:postgresql PostgreSQL | 18.2 | base centrale : patients maîtres, consentements, audit |
| ^ | logo:pandas pandas | ≥ 2.0 | MVP et implémentation Pandas du moteur |
| ^ | logo:rapidfuzz RapidFuzz | ≥ 3.0 | similarité des noms dans le score de rapprochement |
| ^ | logo:fhir HL7 FHIR | R5 (5.0.0) | standard de référence du schéma pivot |
| Exposition | logo:fastapi FastAPI | ≥ 0.115 | API de gouvernance : rôles, finalité, consentement, audit |
| ^ | logo:flask Flask | non épinglée | API des indicateurs des zones SILVER et GOLD |
| ^ | logo:nextjs Next.js | 15.4.6 | interface web optionnelle (React 19.1) |
| ^ | logo:typescript TypeScript | 5.9 | langage de l'interface web |
| ^ | logo:tailwind Tailwind CSS | 4 | mise en forme de l'interface web |
| ^ | logo:d3 D3.js | 7.9 | graphiques de l'interface (carte de chaleur) |
| Qualité et documentation | logo:pytest pytest | ≥ 7.0 | 102 tests du moteur, de la gouvernance et de la planification |
| ^ | logo:mermaid Mermaid | CLI (npx) | diagrammes de conception de ce rapport |

Les versions ont trois origines : celles de Hadoop, Hive, Spark, Java et Ubuntu sont fixées par le provisionnement de la VM ; celles de l'interface web par son fichier de dépendances ; pour les bibliothèques Python, le signe « ≥ » indique la version minimale déclarée par le projet. Les autres sont celles installées sur le poste de développement.

### Gestion de la configuration

Trois principes rendent le projet rejouable à partir du seul dépôt.

**Ce qui est versionné.** Le dépôt Git est la source de vérité : code, scripts du pipeline, configuration de référence, tests et documentation. Chaque jalon correspond à des commits identifiables, et un journal daté enregistre les décisions et leurs raisons. Les données patients ne sont pas versionnées : elles sont régénérées par le générateur synthétique avec une graine fixe, qui rend la génération reproductible. Les secrets sont exclus du dépôt et fournis par variables d'environnement ; un hook de pré-commit bloque les identifiants avant qu'ils n'atteignent l'historique.

**Ce qui est déclaré.** Les sources, les chemins et les paramètres qui gouvernent le comportement — partitions Spark, seuil de 0,80, poids par champ, finalités autorisées — sont décrits dans des fichiers de configuration, jamais dans le code. Les modifier ne demande pas de toucher à la logique.

**Ce qui est vérifié.** La suite de tests est exécutée à chaque jalon, et son succès conditionne le jalon suivant. Le journal du pipeline conserve les volumes traités à chaque étape, ce qui permet de comparer deux exécutions sans les rejouer. Le pipeline est idempotent : un traitement relancé ne duplique ni ne corrompt les zones en aval.

## Contraintes et risques sur le projet

Tableau: Les contraintes du stage et le traitement adopté pour chacune.
| Contrainte | Nature | Traitement adopté |
|---|---|---|
| VM de 8 Go et 4 cœurs | mémoire limitée pour Spark | 4 Go pour l'exécuteur, 2 Go pour le driver, 8 partitions |
| Nœud MAVIS distant instable | source inaccessible par moments | répliques locales, puis sources synthétiques pour le run final |
| Python 3.8 imposé | bibliothèques NLP lourdes inutilisables | RapidFuzz et dictionnaire de synonymes |
| Partage de fichiers de la VM | corruption des fichiers Parquet écrits par Spark | entrepôt Spark toujours écrit sur HDFS |
| Reproductibilité | évaluation et déduplication déterministes | graine 42, seuil et pondérations fixés en configuration |
| Données sensibles | RGPD, article 9 | données synthétiques uniquement et gouvernance intégrée au système |

Le contexte local conditionne aussi l'applicabilité de la solution. En l'absence d'annuaire d'identité dans le service, l'accès à l'API repose sur des **clés d'API associées à un rôle** plutôt que sur des comptes nominatifs. Le réseau intermittent et l'absence de cluster ont conduit à une conception **mono-nœud et rejouable**. Enfin, le cadre juridique malgache des données de santé n'a pas été étudié : la conformité présentée s'appuie sur le RGPD, qui constitue un cadre de conception exigeant mais doit être transposé au droit local avant toute mise en production.

Tableau: Les risques du projet, la parade prévue et le constat à la fin du stage.
| Risque | Impact | Parade | Constat |
|---|---|---|---|
| Mémoire limitée de la VM | performance de Spark | paramétrage mémoire et partitions | maîtrisé : pipeline complet au run de référence |
| Nœud MAVIS instable | blocage du pipeline | sources locales puis synthétiques | contourné |
| Hétérogénéité des sources | mapping FHIR incomplet | synonymes et similarité | partiellement maîtrisé : table des événements GOLD vide |
| Données sensibles | confidentialité | données synthétiques, rôles, audit, consentement | maîtrisé |
| VM indisponible en fin de stage | re-validation impossible | tests hors VM avant toute exécution réelle | partiel : planification testée mais non rejouée sur la VM |

## Démarche projet mise en œuvre

Le travail s'est organisé en cinq jalons, chacun validé par un critère de sortie vérifiable. Les deux prototypes d'origine ont avancé en parallèle avant d'être fusionnés dans le dépôt unique.

Tableau: Les cinq jalons du stage et leur critère de sortie.
| Jalon | Contenu | Critère de sortie atteint | Dates |
|---|---|---|---|
| J1 — Socle | générateur de données synthétiques et vérité terrain | 44 tests verts, 500 patients maîtres, 3 niveaux de difficulté | 01/09/2026 |
| J2 — Moteur | normalisation, blocking, rapprochement exact et probabiliste | précision de 1,000 ; parité Pandas et Spark | 07–08/09/2026 |
| J3 — Big Data | pipeline ELT Medallion RAW → SILVER → GOLD | 4 étapes sur 4, 214 lignes SILVER, 145 patients maîtres | 23/08–07/09/2026 |
| J4 — Gouvernance | rôles, clés, consentement, audit ; planification et reprise | suite de tests complète verte, refus 401 et 403 vérifiés | 01/09 et 27–28/09/2026 |
| J5 — Rapport | structuration selon le plan MBDS, état de l'art sourcé | 20 références, aucun chiffre non vérifiable | 08–28/09/2026 |

Les premières semaines ont été consacrées à une analyse itérative : discussions avec l'encadrant, compréhension du sujet, analyse de l'existant, documentation et état de l'art, puis confrontation aux contraintes réelles (nœud MAVIS instable, VM de 8 Go, Python 3.8). Ces activités se sont répétées en boucle, chaque contrainte découverte relançant une discussion ou une recherche, ce qui justifie une démarche itérative plutôt qu'un cycle en cascade.

## Planification

Le diagramme de Gantt ci-dessous répartit les activités sur les quatre mois du stage, par quinzaine. Il distingue les périodes datées par le journal du dépôt, les périodes déclarées sans trace datée (les journaux commencent le 23/08/2026) et les périodes prévues.

Tableau: Diagramme de Gantt du stage par quinzaine (bleu foncé : daté dans le journal ; bleu clair : déclaré ; gris : prévu). {gantt}
| Phase | 06/07 | 20/07 | 03/08 | 17/08 | 31/08 | 14/09 | 28/09 | 12/10 |
|---|---|---|---|---|---|---|---|---|
| Cadrage du sujet | □ | □ | □ | | | | | |
| Existant et contraintes | □ | □ | □ | ■ | ■ | | | |
| Documentation et état de l'art | | □ | □ | □ | ■ | ■ | | |
| Développement | | | | ■ | ■ | ■ | ■ | |
| Tests et évaluation | | | | ■ | ■ | ■ | ■ | |
| Rédaction du rapport | | | | | ■ | ■ | ■ | ○ |
| Finalisation et soutenance | | | | | | | ○ | ○ |

Capture: C02 | Suivi du projet dans le diagramme de Gantt détaillé. | C02_gantt.png | Optionnel. Capture de la feuille Gantt de documents/Gantt_suivi_projet.xlsx, zoom lisible, du 06/07 à fin octobre.

Ce découpage a rendu chaque jalon démontrable indépendamment. Il a en revanche coûté du temps : la parité stricte entre Pandas et Spark a exigé d'écrire l'algorithme deux fois, ce qui aurait pu être évité si l'échelle cible avait été arrêtée plus tôt. C'est la principale leçon de conduite de projet tirée du stage.

## Budget du projet

Le budget couvre la durée du stage (quatre mois) et le périmètre réalisé, un prototype reproductible sur la VM de développement ; aucun coût de production n'est compté. Les **coûts humains sont des hypothèses de travail**, établies sur l'ordre de grandeur des rapports de référence et non sur des comptes du commanditaire ; ils sont à remplacer par les chiffres réels avant toute diffusion. Les coûts matériels et logiciels, eux, sont réels.

### Coûts humains

Tableau: Coûts humains sur la durée du stage (hypothèses de travail).
| Poste | Base de calcul | Coût mensuel (Ar) | Coût sur 4 mois (Ar) |
|---|---|---:|---:|
| Développeur (stagiaire) | 1 ETP | 1 000 000 | 4 000 000 |
| Encadrement professionnel et pédagogique | 2 × 0,1 ETP | 150 000 | 600 000 |
| **Sous-total** | | **1 150 000** | **4 600 000** |

### Coûts matériels et logiciels

Tableau: Coûts matériels et logiciels : matériel déjà acquis et logiciels libres.
| Poste | Détail | Coût (Ar) |
|---|---|---:|
| Poste de travail et VM | matériel existant, VM hébergée sur le poste | 0 |
| Serveur de production | non applicable : plateforme non déployée | 0 |
| Big Data | Hadoop, Hive, Spark (open source) | 0 |
| Bases, API et interface | PostgreSQL, FastAPI, Flask, Next.js (open source) | 0 |
| Bibliothèques et outils | Pandas, PySpark, RapidFuzz, pytest, Vagrant, Git (open source) | 0 |
| Solutions commerciales comparées | étudiées sur documentation, non acquises | 0 |
| **Sous-total** | | **0** |

### Coût total

Tableau: Coût total du projet sur la durée du stage.
| Catégorie | Coût sur 4 mois (Ar) |
|---|---:|
| Coûts humains (hypothèses) | 4 600 000 |
| Coûts matériels et logiciels (réels) | 0 |
| **Total** | **4 600 000** |

Le coût logiciel et matériel nul est un avantage décisif de l'open source dans un contexte aux moyens limités. Un déploiement en production ajouterait des postes non chiffrés ici : serveur, sauvegarde et exploitation.

# Exigences réalisées dans le projet (vision externe/utilisateur)

## Exigences fonctionnelles

Les six objectifs du cahier des charges sont traduits en exigences fonctionnelles vérifiables, organisées en quatre étapes qui suivent le chemin de la donnée, puis une activité transverse d'évaluation.

Tableau: Les exigences fonctionnelles, leur critère de succès et les cas d'utilisation associés.
| N° | Exigence | Critère de succès | Cas d'utilisation |
|---|---|---|---|
| F1 | Centraliser les données dans un lac | pipeline Medallion RAW → SILVER → GOLD | CU1 |
| F2 | Nettoyer et standardiser | modèle canonique et pivot FHIR | CU2 |
| F3 | Dédupliquer de façon explicable | patient maître et identity map (score, méthode, seuil) | CU3 |
| F4 | Gouverner les accès | rôles, consentement par finalité, audit, clés hachées | CU4, CU5 |
| F5 | Visualiser les indicateurs | vues de déduplication et de consentement | CU6, CU7, CU8 |
| F6 | Évaluer la déduplication | précision, rappel et F1 sur vérité terrain | section 5.1.5 |

### Étape 1 : Intégration des sources

**CU1 — Ingérer un lot de sources.** Le processus automatique lit chaque source et écrit ses fiches dans la zone RAW du lac, sans transformation ; le nombre de lignes écrites doit égaler la somme des lignes lues. Un fichier absent ou tronqué interrompt le lot et l'erreur est journalisée : un lot n'est jamais écrit à moitié.

**CU2 — Ramener des formats différents à un modèle unique.** L'étape de mapping associe chaque champ FHIR attendu à la colonne source la plus proche, puis la normalisation produit le modèle canonique dans la zone SILVER. Toute fiche en sort au même format, quelle que soit sa source. Un champ sans équivalent reste vide et n'est jamais deviné ; les règles de mapping sont décrites dans un fichier, et non dans le code.

### Étape 2 : Déduplication et MPI

**CU3 — Décider qui est le même patient.** Le blocking réduit les comparaisons, le rapprochement exact s'applique d'abord, puis le rapprochement probabiliste pondéré au-dessus du seuil de 0,80. Le résultat est un patient maître par personne retenue, et une identity map qui relie chaque fiche d'origine à son patient maître avec le score et la méthode de décision. Aucune fusion n'est appliquée sans y être inscrite : aucune fusion n'est invisible.

### Étape 3 : Gouvernance des accès

**CU4 — Appliquer le consentement avant d'exposer la donnée.** La construction de la zone GOLD ne conserve, pour chaque patient maître, que les finalités effectivement accordées ; en l'absence d'avis, le refus s'applique par défaut.

**CU5 — Interroger l'API pour un patient.** Un utilisateur présente une clé d'API. La clé est résolue en utilisateur et en rôle, la finalité demandée est comparée aux consentements, la réponse est renvoyée, et l'appel est journalisé. Une finalité non consentie produit un refus explicite (code 403), et non une réponse vide, et ce refus est journalisé au même titre qu'un accès accordé : un refus doit être visible pour que le dispositif soit crédible.

### Étape 4 : Exploitation et pilotage

**CU6 — Consulter les vues de gouvernance.** L'interface web affiche les indicateurs de déduplication (patients maîtres, doublons, méthodes) et de consentement (accords et refus par finalité), calculés sur des données dédupliquées. Si le lac ne répond pas, l'API se replie sur un jeu de démonstration, signalé comme tel à l'écran.

**CU7 — Planifier et piloter le pipeline.** L'administrateur fixe la fréquence d'exécution (quotidienne, hebdomadaire ou mensuelle) par l'API ou un fichier de configuration. Le planificateur de la VM vérifie l'échéance chaque minute et lance le pipeline, sans jamais lancer deux exécutions simultanées. Un run échoué reprend à la première étape non terminée, et une source dont l'empreinte n'a pas changé n'est pas retraitée.

**CU8 — Consulter un dossier patient.** Un médecin authentifié recherche un patient en déclarant sa finalité. Les patients sans consentement pour cette finalité sont retirés de la liste ; la fiche affiche l'identité, l'identity map et les consentements par finalité.

### Évaluation : générateur et vérité terrain

Évaluer objectivement une déduplication exige de connaître la vérité, ce qui est impossible avec des données réelles. Un **générateur de données synthétiques** produit donc des données fictives et leur vérité terrain, de façon déterministe (graine 42) :

- **500 patients maîtres** aux identités propres, dont environ 75 % portent un CIN ;
- une **distribution** entre les trois sources selon des probabilités de présence de 0,8, 0,7 et 0,6, soit **1 057 enregistrements** répartis en 404, 353 et 300 ;
- un **moteur de variations** à trois niveaux de difficulté — facile (10 %), moyen (30 %) et difficile (50 %) — qui injecte des erreurs de casse, d'espaces, de format, des inversions, des fautes de frappe, des abréviations et des valeurs manquantes ;
- une **table de vérité** reliant chaque enregistrement à son patient réel, **jamais fournie à l'algorithme** et réservée à l'évaluation.

## Exigences non fonctionnelles transverses

Tableau: Les exigences non fonctionnelles : réalisation et preuve ou limite.
| Qualité | Exigence | Réalisation | Preuve ou limite |
|---|---|---|---|
| Utilisabilité | un refus doit être compréhensible | finalité inconnue : code 422 avec la liste des valeurs autorisées ; refus : 403 avec motif journalisé | vérifié (section 8.3) |
| Performance | pipeline complet en moins de 30 minutes | cible atteinte au run de référence | volume réel non mesuré |
| Scalabilité | changer d'échelle sans changer la logique | moteur porté en PySpark avec parité stricte, comparaisons bornées | résultats identiques Pandas et Spark (section 8.4) |
| Sécurité | aucun accès sans rôle, finalité et consentement | rôles, clés hachées, consentement, audit, secrets hors dépôt | codes 401, 403 et 422 vérifiés ; hachage non salé |
| Maintenabilité | faire évoluer le comportement sans toucher la logique | poids, seuil et blocking en configuration ; schéma idempotent | 102 tests sur 102 réussis |
| Fiabilité | ne pas retraiter en boucle, reprendre après échec | empreinte des sources, reprise, verrou anti-double exécution | 45 tests dédiés ; non rejoué sur la VM |
| Confidentialité | aucune donnée réelle | générateur synthétique à graine fixe | aucune donnée réelle dans le dépôt |

## Interfaces détaillées

### Interface homme-machine

L'interface web (Next.js) est **optionnelle** au sens du cahier des charges. Elle se limite au pilotage du pipeline, aux vues de gouvernance et à la consultation des patients. L'accès est contrôlé par jeton avec deux profils, administrateur et médecin, et la finalité reste un paramètre obligatoire des pages patients.

Tableau: Les pages de l'interface web et la source de leurs données.
| Page | Contenu affiché | Source des données |
|---|---|---|
| Connexion | authentification (administrateur, médecin) | interface |
| Synthèse | qualité d'identité et consentement côte à côte | API des indicateurs |
| Doublons | patients, maîtres, doublons résolus, répartition par méthode | API des indicateurs |
| Gouvernance | consentements par patient et par finalité, taux d'accord | API des indicateurs |
| Pipeline et tableau de bord | zones Medallion, étapes du dernier run, fraîcheur des sources, planification | API de gouvernance |
| Patients | recherche, pagination, fiche d'identité, identity map, consentements | API de gouvernance |

Chaque vue signale par un bandeau les données de démonstration : un indicateur de démonstration n'est jamais présenté comme une mesure réelle.

Les figures suivantes présentent les principaux écrans, dans l'ordre d'un parcours type : connexion, synthèse, doublons, consentements, pilotage du pipeline, puis consultation des patients.

Capture: C03 | Écran de connexion de l'interface web. | C03_connexion.png | Page /login, formulaire vide ou identifiants de démonstration masqués.

Capture: C04 | Page de synthèse : qualité d'identité et consentement côte à côte. | C04_synthese.png | Page /synthese avec les indicateurs (patients maîtres, doublons, taux, accords et refus).

Capture: C05 | Page des doublons : patients maîtres, doublons résolus et répartition par méthode. | C05_doublons.png | Page /doublons ; laisser visible le bandeau « données de démonstration » s'il apparaît.

Capture: C06 | Page de gouvernance : consentements par patient et par finalité. | C06_gouvernance.png | Page /gouvernance, idéalement filtrée sur une finalité.

Capture: C07 | Tableau de bord du pipeline : zones Medallion, étapes du dernier run et planification. | C07_pipeline.png | Page /dashboard (ou /pipeline) montrant les zones RAW, SILVER, GOLD, le dernier run et la prochaine échéance.

Capture: C08 | Liste des patients filtrée par finalité déclarée. | C08_patients.png | Page /patients avec une recherche et la finalité choisie (ex. research).

Capture: C09 | Fiche d'un patient : identité, identity map et consentements par finalité. | C09_fiche_patient.png | Page /patients/{id} d'un patient ayant plusieurs fiches sources (idéalement le cas « Jean Rakoto »).

### Interfaces avec d'autres systèmes

**L'API de gouvernance (FastAPI)** est le seul point d'application de la règle d'accès. Chaque appel présente une clé d'API, résolue en utilisateur et en rôle, et chaque appel est journalisé.

Tableau: Les points d'entrée de l'API de gouvernance, les rôles autorisés et les contrôles.
| Point d'entrée | Méthode | Rôles | Contrôle et réponse |
|---|---|---|---|
| `/health` | GET | — | état du service |
| `/metrics` | GET | admin, analyst | indicateurs de la plateforme |
| `/patients` | GET | admin, analyst | finalité obligatoire (422 sinon) ; recherche et pagination ; patients non consentis retirés |
| `/patients/{id}` | GET | admin, analyst | finalité non consentie : 403 et motif journalisé |
| `/consent` | GET, POST | lecture admin, analyst ; écriture admin | lecture et enregistrement des consentements |
| `/pipeline/schedule` | GET, PUT | écriture admin | planification, validation stricte |
| `/pipeline/status` | GET | admin, analyst | plan, prochain run, zones, dernier run |
| `/audit` | GET | admin | journal des accès |

Capture: C10 | Documentation interactive de l'API de gouvernance (FastAPI). | C10_swagger.png | Page /docs de l'API FastAPI (port 8000), liste des points d'entrée dépliée.

Une clé absente ou inconnue produit un code 401, un rôle insuffisant un code 403. **L'API des indicateurs (Flask)** expose deux points d'entrée de reporting, sur la table SILVER des patients et sur la table GOLD des consentements ; elle ne contrôle pas l'accès, ce contrôle étant réservé à l'API de gouvernance. La plateforme échange enfin avec les sources (CSV, PostgreSQL, SQLite), avec le lac (HDFS et Hive), avec la base centrale PostgreSQL et avec le planificateur de la VM.

# Architecture du système

## Architecture logicielle

L'architecture suit la progression en trois niveaux : chaque niveau réutilise la **même logique métier**, seule l'infrastructure d'exécution change.

Figure: L'architecture en trois niveaux : MVP Pandas, parité PySpark, puis lac de données Medallion portant le moteur et la gouvernance. | documents/figures/fig-4.png | 15

La chaîne retenue (niveau 3) va de la source hétérogène à l'API gouvernée. Les sources sont extraites vers la zone RAW en fichiers Parquet sur HDFS, décrites par des tables Hive externes. Le mapping FHIR produit les quatre tables de la zone SILVER, où le moteur de déduplication rattache chaque ligne à son patient maître. La zone GOLD porte les agrégats prêts à l'analyse et les consentements. La base centrale PostgreSQL conserve l'état de référence : patients maîtres, identity map, consentements, utilisateurs et journal d'audit. Les deux magasins ont des rôles distincts : le lac est **rejouable**, la base centrale est **de référence**.

Tableau: Les briques de la chaîne et la conception adoptée pour chacune.
| Brique | Conception |
|---|---|
| Extraction | couche d'extraction abstraite (CSV, PostgreSQL, SQLite) vers la zone RAW |
| Normalisation | modèle canonique du patient |
| Interopérabilité | schéma pivot FHIR à quatre entités |
| Déduplication | blocking, passe exacte, passe probabiliste, seuil de 0,80 |
| Consolidation | patient maître et identity map traçable |
| Chargement | base PostgreSQL centrale à écriture idempotente |
| Exposition | API REST et espace de gouvernance |

La traçabilité est assurée de bout en bout : chaque ligne SILVER conserve son système et sa table d'origine, son identifiant source et une empreinte unique ; chaque fusion porte l'identifiant du patient maître, la méthode, le score et l'explication.

## Architecture technique

L'ensemble est installé sur une **VM unique** (Ubuntu 20.04, 8 Go, 4 cœurs) décrite par Vagrant. L'ordre de démarrage des services est strict : HDFS, puis YARN, puis le catalogue Hive, puis HiveServer2, puis les traitements Spark et enfin les API. Toute inversion produit des erreurs d'écriture ou de métadonnées.

Tableau: Les composants installés sur la VM et leur port.
| Composant | Rôle | Port |
|---|---|---:|
| HDFS NameNode | stockage du lac (Parquet RAW, SILVER, GOLD) | 9000 |
| YARN | exécution des traitements Spark | 8088 |
| Hive Metastore | catalogue des bases du lac | 9083 |
| HiveServer2 | accès SQL | 10000 |
| API des indicateurs (Flask) | exposition des zones SILVER et GOLD | 5000 |
| API de gouvernance (FastAPI) | patients, consentements, audit, planification | 8000 |
| Planificateur | déclenchement du pipeline selon la fréquence définie | cron |
| Interface web (Next.js) | pilotage et consultation, sur l'hôte Windows | 3000 |

Capture: C11 | Les trois zones du lac de données dans l'interface web de HDFS. | C11_hdfs_datalake.png | Interface HDFS (port 9870), menu Utilities > Browse the file system, dossier /datalake montrant raw, silver et gold.

Les versions installées sont Hadoop 3.3.6, Hive 3.1.3, Spark 3.4.2 et Java 8. Spark est configuré avec 4 Go pour l'exécuteur, 2 Go pour le driver et 8 partitions, afin de tenir dans la mémoire de la VM.

# Conception du système logiciel réalisée dans le projet (vision interne/développeur)

## Plate-forme technique

Chaque concept de l'état de l'art est porté par une brique technique précise, comme le montre la figure suivante.

Figure: Des concepts de l'état de l'art aux briques techniques livrées. | documents/figures/fig-6.png | 10

Les choix technologiques ont été arbitrés sur cinq critères pondérés, issus des contraintes du stage : la compatibilité avec l'environnement (0,30, critère éliminatoire), l'explicabilité de la décision (0,25), le coût mémoire et la performance (0,20), la maturité et la documentation (0,15), et le coût de licence (0,10). Chaque option est notée de 1 à 5.

Tableau: Notation pondérée des options pour les trois arbitrages structurants.
| Arbitrage | Option | Score | Verdict |
|---|---|---:|---|
| Moteur de similarité | **RapidFuzz** | **5,00** | retenu |
| | `sentence_transformers` | 2,10 | écarté : incompatible avec Python 3.8 |
| | Levenshtein en Python pur | 3,60 | repli possible, trop lent |
| Base centrale | **PostgreSQL** | **4,80** | retenu : JSONB, contraintes, horodatage |
| | SQLite | 4,35 | écarté : écritures concurrentes |
| | MySQL | 4,25 | écarté : JSONB moins intégré |
| API de gouvernance | **FastAPI** | **4,65** | retenu : finalité validée dans le schéma de l'API |
| | Flask | 4,50 | écarté de peu |

L'écart entre FastAPI et Flask est faible : le choix tient à ce que FastAPI permet d'exprimer le contrôle de finalité dans le schéma de l'API plutôt que dans le code de chaque route.

## Conception du logiciel développé

### Le code source : vue statique

Le code est découpé selon la séparation entre ingestion, normalisation, déduplication, gouvernance et exposition :

- **Moteur d'identité** : le modèle canonique et les deux implémentations du moteur de déduplication, Pandas et Spark.
- **Gouvernance** : authentification par clé, consentement, audit et API FastAPI.
- **Provisionnement et pipeline** : description de la VM, orchestrateur du pipeline, étapes ELT, gestion de l'état et planificateur.
- **Exposition** : API des indicateurs et interface web optionnelle.
- **Paramètres** : fichier de configuration de la déduplication (poids, seuil, blocking) et schéma SQL de la base centrale.
- **Évaluation et tests** : générateur synthétique, évaluateur sur vérité terrain et suites de tests automatisés.

### Modélisation des données

**Le modèle canonique.** Chaque source possède son vocabulaire ; la conception introduit une représentation unique du patient (source, identifiant source, prénom, nom, nom complet, date de naissance, CIN, ville de naissance, adresse, genre). Le mapping des colonnes source vers ce modèle est explicite et déterministe.

Tableau: Le mapping des colonnes source vers le modèle canonique.
| Champ | pharmacy | consultation | imaging | Standardisation |
|---|---|---|---|---|
| Identifiant | `client_id` | `patient_code` | `id_personne` | — |
| Nom | `nom_complet` | `prenom` + `nom` | `patient_name` | minuscules, sans accents ni ponctuation |
| Naissance | `naissance` | `date_naiss` | `dob` | format ISO |
| CIN | `cin` | `no_cin` | `cin_number` | chiffres uniquement |
| Ville de naissance | `ville_naissance` | `ville_nai` | `birth_place` | texte normalisé |
| Genre | `sexe` (H/F) | `genre` (male/female) | `sex` (Homme/femme) | `M` ou `F` |

Après normalisation, les trois formes du cas « Jean Rakoto » produisent des valeurs canoniques identiques.

Les deux fonctions ci-dessous appliquent le contrat de normalisation au CIN et au genre ; toute valeur hors règle devient vide au lieu d'être devinée.

Code: X01 | Normalisation du CIN et du genre | engine/identity/canonical.py::_cin,_gender | X01_normalisation.png

**La base centrale.** Tout converge vers le patient maître : chaque fiche d'origine, chaque consentement et chaque événement métier s'y rattache par clé étrangère.

Figure: Le modèle de la base centrale : neuf tables organisées autour du patient maître. | documents/figures/fig-7.png | 24 | paysage

Tableau: Les tables de la base centrale et leurs règles de conception.
| Table | Rôle | Règles de conception |
|---|---|---|
| `raw_patient_record` | historique brut, jamais exposé | contenu JSONB, unicité par source et identifiant |
| `master_patient` | identité unique | genre contraint à `M`, `F` ou vide |
| `patient_identity_map` | lien fiche source → patient maître | méthode contrainte, score, explication |
| `consent` | consentement par finalité | finalité en liste fermée, accord, date d'enregistrement |
| `api_user` | utilisateurs de l'API | empreinte SHA-256 de la clé, rôle contraint |
| `access_audit` | journal de toutes les tentatives | point d'entrée, statut, finalité, motif de refus, date |
| Tables de transactions | achats, consultations, examens | rattachés au patient maître |

Les contraintes de l'identity map et de la table des consentements portent les règles de gouvernance dans la base elle-même : méthode de rapprochement et finalité en listes fermées, score borné entre 0 et 1.

Code: X02 | Tables de l'identity map et des consentements | sql/schema.sql:30-65 | X02_schema.png

Le schéma est **idempotent** : tables et colonnes sont créées seulement si elles n'existent pas, et les insertions ignorent les doublons ; relancer le même traitement ne duplique rien.

**Les zones du lac.** La zone RAW reçoit la donnée brute en Parquet sur HDFS, décrite par des tables Hive externes. La zone SILVER contient les quatre tables FHIR normalisées, avec les doublons marqués et expliqués. La zone GOLD contient la table des événements patients (18 colonnes, 8 tranches d'âge) et la table des consentements.

### Composants

**Le moteur de déduplication.** Pour éviter la comparaison de toutes les paires, le moteur indexe les patients maîtres selon trois clés de blocking : les quatre premières lettres du nom normalisé, la date de naissance et le CIN. Seuls les candidats partageant l'une de ces clés sont comparés. La déduplication procède en deux passes :

1. **Rapprochement exact** : le patient partage la clé de rapprochement d'un patient maître (nom normalisé, date de naissance, CIN), ou bien la même date de naissance et le même CIN non vide, ce qui absorbe les inversions de prénom et de nom. Décision « exacte », score 1,0.
2. **Rapprochement probabiliste** : parmi les candidats, un score pondéré est calculé. Au-dessus de 0,80, la fiche est rattachée au patient maître ; en dessous, un nouveau patient maître est créé.

Tableau: Le calcul du score de similarité probabiliste.
| Critère | Similarité | Poids |
|---|---|---:|
| Nom | similarité de chaînes, indépendante de l'ordre des mots | 0,50 |
| Date de naissance | égalité | 0,30 |
| CIN | égalité (si présent) | 0,10 |
| Ville de naissance | égalité après normalisation | 0,10 |

Les poids et le seuil ne sont pas écrits dans le code : ils sont déclarés dans un fichier de configuration unique, lu par le moteur Pandas, sa version Spark et l'évaluation.

Code: X03 | Paramètres de la déduplication | config/deduplication.yaml | X03_config.png

Code: X04 | Calcul du score de similarité pondéré | engine/identity/matcher.py::_similarity | X04_score.png

Chaque décision porte l'identifiant du patient maître, la méthode, le score et une explication en clair. La règle « jamais de fusion sans logique explicable » est ainsi **structurelle** : elle est inscrite dans le modèle de données, pas seulement dans une convention.

**La gouvernance.** Trois mécanismes s'appliquent dans cet ordre : on vérifie **qui** demande, **pourquoi** il demande, puis on **trace** ce qui s'est passé.

- **Rôles** : `admin`, `analyst` et `viewer`, résolus à partir de la clé d'API présentée.
- **Clés d'API** : seule leur empreinte SHA-256 est stockée ; la clé en clair n'est jamais conservée.
- **Finalité déclarée** : paramètre obligatoire des requêtes sur les patients, validé contre une liste fermée ; une finalité inconnue produit un code 422.
- **Consentement par finalité** : la décision ne dépend pas du rôle seul ; un utilisateur autorisé mais sans finalité consentie est refusé (403). Dans une liste, les patients non consentis sont retirés et le nombre d'exclusions est journalisé.
- **Audit** : chaque requête est journalisée avec l'utilisateur, le point d'entrée, le statut, l'adresse, la finalité et le motif de refus, y compris pour les appels anonymes.

La règle de consentement tient en deux fonctions : la première lit le dernier avis enregistré et vaut refus en son absence ; la seconde valide la finalité, prépare les informations d'audit et oppose le refus.

Code: X05 | Vérification du consentement et refus explicite | engine/governance/consent.py::check_consent,enforce_consent | X05_consentement.png

**La parité Spark.** L'algorithme est porté en PySpark sans changer sa sémantique : les groupes exacts sont construits par regroupement sur la clé, puis la résolution probabiliste ne compare que les représentants de ces groupes. Les deux implémentations partagent la normalisation et lisent les mêmes poids et le même seuil ; seule la stratégie de regroupement diffère.

### Déploiement

La plateforme s'installe sur la VM de développement par Vagrant, qui décrit la machine et installe Hadoop, Hive, Spark et l'environnement Python. Les services démarrent dans l'ordre imposé, puis le pipeline se lance à la main ou par le planificateur. L'interface optionnelle tourne sur l'hôte Windows. Aucun déploiement n'a été réalisé sur un serveur du commanditaire : la plateforme est **reproductible depuis le dépôt**, pas mise en production.

## Réalisation des étapes

### Pipeline ELT Medallion

Le pipeline est orchestré par un script unique qui s'arrête à la première erreur et journalise chaque étape. Chaque étape est un programme distinct : une étape qui échoue ne laisse pas la zone suivante dans un état intermédiaire, condition pour que le pipeline reste relançable.

Tableau: Les cinq étapes du pipeline ELT et leur production.
| Étape | Traitement | Production |
|---|---|---|
| 1 — Préparation | régénère les sources de démonstration si elles sont absentes | fichiers CSV synthétiques (sans effet s'ils existent) |
| 2 — Extraction RAW | copie brute des sources dans le lac | fichiers Parquet sur HDFS, tables Hive externes, rapport d'extraction |
| 3 — Mapping FHIR | association des colonnes source aux champs FHIR | fichier de correspondance |
| 4 — SILVER | normalisation FHIR et déduplication par le moteur | quatre tables FHIR enrichies du patient maître |
| 5 — GOLD | agrégation et application du consentement | table des événements patients, table des consentements |

Deux mécanismes évitent de retraiter en boucle. La **reprise** : l'état de chaque exécution et de chaque étape est persisté ; un run échoué repart de la première étape non terminée, et un run en cours verrouille tout lancement concurrent. L'**ingestion incrémentale** : chaque source conserve une empreinte (hachage, taille, date de modification) ; une source inchangée n'est pas ré-extraite. La **planification** confie le lancement régulier au planificateur de la VM, qui vérifie l'échéance chaque minute et lance le pipeline en arrière-plan. Cette mécanique est écrite et testée hors VM ; **elle n'a pas encore été rejouée sur la VM**, indisponible en fin de stage.

Capture: C12 | Exécution du pipeline : enchaînement des étapes jusqu'à la zone GOLD. | C12_run_pipeline.png | Terminal de la VM : sortie de run_pipeline.sh (ou fin de elt.log) montrant chaque étape terminée avec succès.

Tableau: Résultats du run de référence du 07/09/2026 (sources CSV synthétiques).
| Indicateur | Valeur |
|---|---:|
| Étapes réussies (orchestration de l'époque) | 4 sur 4 |
| Lignes dans la table SILVER des patients (76 + 76 + 62) | 214 |
| Patients maîtres distincts | 145 |
| Doublons rattachés (tous par rapprochement exact) | 69 |
| Taux de doublons | 32,24 % |
| Lignes de la table GOLD des consentements | 145 |
| Lignes de la table GOLD des événements | 0 |

Capture: C13 | Contrôle des volumes dans le lac : 214 enregistrements et 145 patients maîtres. | C13_comptages.png | Résultat d'une requête Spark ou Hive (COUNT sur la table SILVER des patients, nombre de patients maîtres distincts).

Le passage de 214 à 145 se vérifie par un simple comptage : 214 − 69 = 145. La table des consentements aligne 145 lignes sur 145 patients maîtres, mais la finalité et l'accord y sont vides, la base centrale n'ayant pas été peuplée au moment du run. La table des événements est vide : les consultations et pathologies ne sont pas encore rattachées au patient. La zone GOLD certifie donc aujourd'hui l'identité, pas encore les événements de soin.

### Moteur de déduplication : Pandas et Spark

Tableau: Les deux implémentations du moteur : même sémantique, mécanique différente.
| Aspect | Pandas | PySpark |
|---|---|---|
| Normalisation | modèle canonique | même modèle canonique |
| Passe exacte | clé de rapprochement, ou naissance et CIN | regroupement par clé |
| Passe probabiliste | index à trois clés de blocking | index borné sur les représentants de groupes |
| Score et seuil | 0,5 / 0,3 / 0,1 / 0,1 ; 0,80 | identiques |
| Décision | exacte, probabiliste ou nouveau maître | identique |

La parité est vérifiée sur la démonstration (18 fiches ramenées à 11 patients maîtres dans les deux implémentations) et sur l'évaluation complète, où les deux produisent exactement les mêmes décisions (chapitre 8). Le protocole rejoue les deux chemins sur le même jeu et compare les décisions : c'est le seul moyen de détecter une dérive qu'aucune implémentation ne peut détecter seule.

### Gouvernance et API

La gouvernance est implémentée dans le moteur par quatre composants : l'authentification par clé hachée et rôle, la décision de consentement par finalité, le journal d'audit sous forme de *middleware* qui enregistre chaque requête, et l'API FastAPI qui expose les points d'entrée décrits au chapitre 5. Les données brutes de la zone RAW ne sont jamais exposées : seuls les patients maîtres consolidés le sont.

Deux API portent le mot « gouvernance » sans jouer le même rôle. L'API Flask est une surface de consultation : elle lit les zones SILVER et GOLD et en rend des agrégats, sans authentification. L'API FastAPI est le seul point d'**application** de la règle : c'est là que se produisent les codes 401 (clé inconnue), 403 (rôle insuffisant ou finalité non consentie) et 422 (finalité absente ou inconnue), chacun journalisé.

Capture: C14 | Refus d'accès pour finalité non consentie et trace correspondante dans le journal d'audit. | C14_refus_403.png | Optionnel, uniquement si la base centrale a été peuplée (seed de gouvernance) : réponse 403 dans /docs ou curl, puis la ligne de access_audit avec purpose et refusal_reason. Sinon, supprimer cet emplacement.

### Difficultés rencontrées et résolutions

Tableau: Les difficultés réellement rencontrées, leur cause et le correctif apporté.
| Problème | Cause | Correctif |
|---|---|---|
| Table SILVER passée à 11 614 lignes | une colonne d'identifiant capturée par le mapping FHIR automatique rendait l'identifiant source vide, d'où une jointure 76 × 76 | colonne exclue du mapping automatique ; chaque colonne source utilisée une seule fois |
| Écritures qui s'écrasaient d'une source à l'autre | écriture en mode remplacement dans la boucle par source | accumulation par entité, puis une seule écriture par table |
| Fichiers Parquet corrompus | entrepôt Spark écrit sur le partage de fichiers de la VM | entrepôt toujours écrit sur HDFS |
| Spark ne démarrait pas | variable `JAVA_HOME` mal formée | normalisation automatique du chemin Java |
| HiveServer2 instable | service fragile sur la VM | contrôle des volumes par scripts Spark |
| NLP lourd inutilisable | plantage de `sentence_transformers` sous Python 3.8 | RapidFuzz et dictionnaire de synonymes |
| Script d'extraction non compilable | caractère invisible dans un commentaire | caractère supprimé, script recompilé |

Ces incidents relèvent de trois familles. Les incidents de **données** ont donné lieu à des correctifs documentés comme pièges à ne pas reproduire. Les incidents d'**infrastructure** ont été contournés par des règles de configuration. L'incident d'**outillage** est le seul qui ait changé la méthode : l'approche par vecteurs a été abandonnée au profit d'un score pondéré, plus léger et plus explicable.

# Tests du système logiciel

## Stratégie de test

La validation suit une pyramide : des tests unitaires rapides (générateur, moteur, gouvernance), des tests d'intégration (MVP, pipeline) et des tests système (API, évaluation sur vérité terrain). L'ordre des niveaux suit le coût d'un échec : un test unitaire échoue en quelques secondes et désigne une ligne de code ; un test système n'échoue qu'après un pipeline complet et nécessite la VM. En l'absence d'intégration continue, hors périmètre du stage, chaque niveau est rejouable manuellement.

Figure: La stratégie de test : tests unitaires, intégration, puis preuve système. | documents/figures/fig-9.png | 11

Tableau: Les niveaux de test, leur périmètre et le résultat obtenu.
| Niveau | Périmètre | Résultat |
|---|---|---|
| Générateur | variations, distribution, identity mapping, construction des jeux | 44 tests réussis |
| Moteur et gouvernance | rapprochement (12), consentement (21), normalisation (8), API de gouvernance (16) | 57 sur 57 |
| Planification et reprise | échéances (22), empreintes (10), état du pipeline (5), API de planification (8) | 45 sur 45 |
| MVP | pipeline, chargement PostgreSQL, authentification, audit, API | 20 tests réussis |
| API des indicateurs | trois vérifications sur données réelles | 3 sur 3 |
| Pipeline | exécution complète RAW → SILVER → GOLD sur la VM | 4 étapes sur 4 (07/09/2026) |

Capture: C15 | Exécution de la suite de tests automatisés. | C15_pytest.png | Terminal : fin de la sortie de pytest projet/code-source/tests avec « 102 passed ».

La suite principale réunit les tests du moteur, de la gouvernance et de la planification : **102 tests sur 102 réussis** (exécution du 28/09/2026), sans aucun échec.

## Tests unitaires et d'intégration

Les tests du moteur couvrent la sémantique de la déduplication : rapprochement exact avec des CIN de formats différents, inversion du nom compensée par la date de naissance et le CIN, fusion au seuil de 0,80, faute de frappe compensée par la date de naissance, contribution de la ville de naissance au score, **non-fusion de patients distincts** et parité entre Pandas et Spark. Les tests de planification vérifient le calcul des échéances, la décision de saut d'une source inchangée, la reprise d'un run échoué et l'API de planification.

Au niveau intégration, les 20 tests du MVP enchaînent pipeline, chargement en base, authentification, audit et API. Le run de référence du pipeline sur la VM a exécuté la chaîne complète RAW → SILVER → GOLD avec succès.

## Tests fonctionnels du contrôle d'accès

Les tests de l'API de gouvernance empruntent le **chemin réel** d'authentification : clé présentée, résolution de l'utilisateur, contrôle du rôle, contrôle du consentement. Seul l'accès à la base de données est simulé ; le contrôle d'accès n'est jamais court-circuité.

Tableau: Les cas de contrôle d'accès vérifiés et le comportement attendu.
| Cas vérifié | Résultat attendu |
|---|---|
| Aucune clé présentée | 401, appel journalisé comme anonyme |
| Clé inconnue | 401 |
| Rôle `viewer` sur un point d'entrée réservé à l'administrateur | 403 |
| Finalité absente | 422 |
| Finalité hors liste (`marketing`) | 422, valeurs autorisées indiquées |
| Finalité non consentie pour un patient | 403 et motif du refus journalisé |
| Finalité consentie pour un patient | 200, aucun motif de refus |
| Liste avec consentements partiels | seuls les patients consentis sont renvoyés, exclusions comptées |
| Recherche par nom, CIN ou identifiant, pagination | patients attendus, tranche bornée avec le total |
| Absence de ligne de consentement | refus par défaut |

La sensibilité du test de refus a été vérifiée par mutation : neutraliser le contrôle de consentement dans le code fait échouer le test. Un test qui réussirait quelle que soit l'implémentation ne prouverait rien.

## Évaluation sur vérité terrain

Trois jeux sont générés à partir **des mêmes 500 patients maîtres** ; seul le taux de variation change (10 %, 30 %, 50 %), de sorte que la dégradation de la qualité est attribuable à un seul facteur. Les métriques sont calculées par paires d'enregistrements : la **précision** mesure l'exactitude des fusions, le **rappel** la part des vrais doublons retrouvés, et le **F1** le compromis entre les deux.

Tableau: Résultats de l'évaluation sur vérité terrain (run du 08/09/2026).
| Niveau | Maîtres prédits | VP | FP | FN | Précision | Rappel | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Facile (10 %) | 500 | 727 | 0 | 0 | **1,000** | 1,000 | 1,000 |
| Moyen (30 %) | 554 | 643 | 0 | 84 | **1,000** | 0,884 | 0,939 |
| Difficile (50 %) | 804 | 307 | 0 | 420 | **1,000** | 0,422 | 0,594 |

Capture: C16 | Sortie de l'évaluation sur vérité terrain (jeu difficile). | C16_evaluation.png | Terminal : sortie de evaluate_engine.py sur le jeu hard (précision, rappel, F1, VP/FP/FN).

L'algorithme **ne fusionne jamais à tort** : aucun faux positif sur les trois niveaux, propriété essentielle en santé, où fusionner deux personnes est plus grave que de les laisser séparées. Sur le jeu difficile, il ne reconnaît pas toutes les variantes (rappel de 0,422). L'introduction du CIN dans la clé exacte a relevé ce rappel de 0,287 à 0,422 sans créer de faux positif.

La décomposition par méthode localise la faiblesse : sur le jeu difficile, le rapprochement exact atteint un rappel de 0,854 et le rapprochement probabiliste de 0,533, avec une précision de 1,000 dans les deux cas. Le rappel est homogène entre les sources (0,422 ; 0,422 ; 0,423) : la dégradation vient du taux de variation, et non d'une source particulière. Enfin, les implémentations Pandas et Spark produisent exactement les mêmes résultats : 307 vrais positifs, 0 faux positif, 420 faux négatifs et 804 patients maîtres prédits pour 500 groupes réels.

Une précision mérite d'être faite sur l'absence de faux positif : le générateur dégrade des enregistrements existants mais ne construit jamais deux personnes distinctes presque identiques. La précision de 1,000 est donc un **plancher observé**, et non une garantie ; la confirmer demanderait un jeu d'homonymes proches.

## Limites identifiées

Le prototype présente des limites identifiées et documentées :

- **Rappel de 0,422 sur le jeu difficile** : 420 paires manquées, en raison d'un seuil volontairement conservateur ; l'abaisser ou enrichir la clé suppose une validation métier.
- **Table GOLD des événements vide** : les rencontres et pathologies ne sont pas encore rattachées au patient ; le mapping FHIR est à enrichir.
- **Consentement non alimenté en base centrale** : la mécanique est démontrée par les tests, mais la base n'a pas été peuplée pendant le stage.
- **Absence de cas adversarial** : pas de jeu d'homonymes proches pour éprouver la précision.
- **API des indicateurs non sécurisée** : elle ne sert que du reporting ; le contrôle d'accès est appliqué et testé sur l'API de gouvernance.
- **Clés d'API hachées sans sel** : l'empreinte protège la lecture directe de la table, mais un hachage salé ou lent (bcrypt) serait préférable.
- **Pas d'intégration continue ni de tests en environnement déployé**, et planification incrémentale non rejouée sur la VM.

#! Conclusion générale

Ce stage avait pour objet de concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités et la gouvernance des accès par le consentement du patient. Le tableau suivant reprend chaque volet de cette problématique avec la réponse apportée et sa preuve.

Tableau: Réponse à la problématique, volet par volet.
| Volet | Réponse réalisée | Preuve |
|---|---|---|
| Intégrer | extraction abstraite vers la zone RAW (Parquet sur HDFS, tables Hive) | 3 sources de démonstration et 3 sources réelles capturées |
| Nettoyer et normaliser | modèle canonique et schéma pivot FHIR | 214 lignes SILVER cohérentes |
| Dédupliquer de façon explicable | blocking, passe exacte, passe probabiliste ; méthode, score et explication pour chaque décision | 145 patients maîtres, 69 doublons, taux de 32,24 % |
| Centraliser avec traçabilité | zones RAW, SILVER, GOLD ; origine conservée ; reprise et incrémental | 214 − 69 = 145 vérifié sur le lac |
| Gouverner par consentement | rôles, clés hachées, finalité obligatoire, refus 403 journalisé | 102 tests sur 102, dont 401, 403 et 422 |
| Ne jamais fusionner sans logique | méthode obligatoire pour tout patient maître | précision de 1,000 sur les trois niveaux |

Le projet démontre quatre résultats. **La démarche progressive tient** : le même moteur, écrit en Pandas puis porté en PySpark et intégré au lac, conserve exactement la même sémantique. **L'explicabilité a un coût maîtrisé** : le seuil est positionné pour ne jamais fusionner à tort, et le rappel limité sur le jeu difficile est expliqué plutôt que masqué. **La gouvernance est dans le système** : un refus pour finalité non consentie est décidé, opposé et journalisé, et cela est vérifié par des tests qui empruntent le vrai chemin d'authentification. **Le contexte dicte les choix** : VM de 8 Go, Python 3.8 et nœud distant instable ont chacun conduit à une décision documentée.

Les difficultés rencontrées ont été techniques (sept incidents corrigés), d'environnement (nœud distant instable, VM indisponible en fin de stage), d'organisation (développement mené seul, algorithme écrit deux fois) et de méthode. La plus instructive a été de définir ce que l'on accepte de perdre — des doublons non retrouvés — au regard de ce que l'on refuse de risquer — la fusion de deux patients — et de pouvoir le démontrer par des chiffres reproductibles.

Sur le plan personnel, ce stage m'a permis de pratiquer le Big Data, domaine dans lequel mon expérience était limitée : installer et faire fonctionner une chaîne HDFS, Hive et Spark, et découvrir ce que la documentation ne dit pas, comme l'ordre de démarrage des services ou le coût de Spark sur de petits volumes. Il m'a appris à relier le modèle statistique du rapprochement d'identités, l'architecture qui le rend exploitable et la règle de gouvernance qui décide qui peut le lire. Il m'a enfin appris une discipline : ne rien affirmer sans preuve reproductible, et écrire une limite plutôt que de la taire.

Plusieurs perspectives prolongent ce travail. À court terme : enrichir le mapping FHIR pour alimenter la table des événements, peupler la base centrale de consentements pour démontrer le refus sur données, calibrer le seuil et les poids sur la vérité terrain, et rejouer la planification sur la VM. À moyen terme : ajouter une intégration continue, passer à l'échelle par un blocking partitionné et une consolidation transitive des groupes, et reprendre la source MAVIS réelle lorsque le nœud sera stable. À plus long terme : brancher la gouvernance sur un catalogue de métadonnées pour le lignage des données, et généraliser le moteur à d'autres entités, comme les médecins ou les médicaments.

#! Références et bibliographie

**Rapprochement d'identités**

[1] ELMAGARMID, A. K. ; IPEIROTIS, P. G. ; VERYKIOS, V. S. *Duplicate Record Detection: A Survey*. IEEE Transactions on Knowledge and Data Engineering, vol. 19, n° 1, 2007, p. 1-16.

[2] FELLEGI, I. P. ; SUNTER, A. B. *A Theory for Record Linkage*. Journal of the American Statistical Association, vol. 64, n° 328, 1969, p. 1183-1210.

[3] CHRISTEN, P. *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*. Springer, 2012.

[4] RapidFuzz, documentation (version 3.14.5). https://rapidfuzz.github.io/RapidFuzz/

**Standards de santé**

[5] HL7 FHIR, *Resource Patient* (v5.0.0), dont l'opération `$match` (§ 8.1.11). https://www.hl7.org/fhir/patient.html

**Architecture Big Data**

[6] Apache Hadoop, *HDFS Architecture*. https://hadoop.apache.org

[7] Apache Spark. https://spark.apache.org

[8] Apache Hive. https://hive.apache.org

[9] Databricks, *Medallion Architecture*. https://docs.databricks.com/aws/en/lakehouse/medallion

**Réglementation**

[10] Règlement (UE) 2016/679 (RGPD), article 9.

[11] CNIL, *Quelles formalités pour les traitements de données de santé ?* https://www.cnil.fr

[12] CNIL, *RGPD et professionnels de santé libéraux : ce que vous devez savoir*. https://www.cnil.fr

**Solutions existantes** (étude documentaire, consultée le 27/09/2026)

[13] InterSystems, *InterSystems EMPI* et documentation *IRIS for Health*. https://www.intersystems.com

[14] Qlik, *Talend MDM — Integrated Matching*. https://help.qlik.com

[15] LINACRE, R. et al. *Splink: Free software for probabilistic record linkage at scale*. International Journal of Population Data Science, vol. 7, n° 3, 2022.

[16] HAPI FHIR. https://hapifhir.io

[17] Microsoft, *Azure Health Data Services*. https://learn.microsoft.com/azure/healthcare-apis/

[18] Apache Atlas. https://atlas.apache.org

[19] GNU Health. https://www.gnuhealth.org

[20] Odoo et applications hospitalières. https://www.odoo.com

#! Annexes

##! Annexe A — Exécution du pipeline

Le pipeline est lancé par un script unique, qui enchaîne les cinq étapes et produit un journal d'exécution conservant, pour chaque étape, les volumes lus, écrits et écartés ainsi que la durée. Les options suivantes pilotent son comportement :

Tableau: Les options d'exécution du pipeline.
| Option | Effet |
|---|---|
| `--resume` | reprend un run échoué à la première étape non terminée |
| `--full` | purge l'état et rejoue toutes les étapes |
| `--since AAAA-MM-JJ` | force la ré-extraction des données à partir d'une date |
| `--from <étape>` | repart d'une étape nommée |
| `--dry-run` | affiche le plan d'exécution sans rien écrire |

Le planificateur ne lance le pipeline que si la planification est active, si l'échéance vient d'être atteinte sans avoir déjà été déclenchée, et si aucun run n'est en cours.

##! Annexe B — Le générateur de données synthétiques

Tableau: Les modules du générateur synthétique.
| Module | Rôle |
|---|---|
| Générateur de patients | 500 patients maîtres, référence absolue de l'évaluation |
| Moteur de distribution | répartition entre les trois sources (0,8 / 0,7 / 0,6) |
| Moteur de variations | injection d'erreurs à 10 %, 30 % ou 50 % |
| Générateurs de sources | fichiers patients et transactions de chaque source |
| Table de vérité | correspondance enregistrement source → patient réel |
| Constructeur d'expériences | jeux facile, moyen et difficile |

Sur le jeu difficile, les transactions associées comptent 792 achats en pharmacie, 519 consultations et 450 examens d'imagerie. Le jeu complet se régénère en une commande, avec la même graine, ce qui rend l'évaluation reproductible.

##! Annexe C — Exemple de décision de déduplication

Pour le cas de référence de démonstration (18 fiches), le moteur produit 11 patients maîtres et 18 liens d'identité, à l'identique en Pandas et en Spark. Jean Rakoto est rattaché par **rapprochement exact** grâce à son CIN, présent sous deux formats différents mais identique après normalisation. Une autre patiente, Nirina, est rattachée par **rapprochement probabiliste** avec un score supérieur à 0,80, son nom présentant une variation. Chaque lien conserve sa méthode, son score et une explication lisible par un gestionnaire de données.

##! Annexe D — Extraits de code complémentaires

La fonction de déduplication enchaîne les deux passes décrites à la section 7.2.3 : rapprochement exact, puis meilleur candidat probabiliste au-dessus du seuil, sinon création d'un nouveau patient maître. Chaque branche produit une décision avec sa méthode, son score et son explication.

Code: X06 | Boucle de déduplication en deux passes | engine/identity/matcher.py::deduplicate | X06_deduplicate.png

Le journal d'audit est un *middleware* : il s'exécute après chaque requête, quelle qu'en soit l'issue, et enregistre la finalité et le motif d'un éventuel refus.

Code: X07 | Journalisation de chaque accès | engine/governance/audit.py::AuditMiddleware | X07_audit.png

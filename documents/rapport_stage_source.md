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

Rejouée sur la VM avec un jeu synthétique difficile, la plateforme ramène 1 057 fiches à 803 patients. Évaluée sur trois jeux synthétiques dont la vérité est connue, la déduplication atteint une précision de 1,000 sur tous les niveaux — aucune fusion à tort — et un rappel de 0,422 sur le jeu le plus difficile ; le pipeline complet, mesuré de la même façon, obtient le même résultat. Sur 100 000 patients, traités en 7 minutes, deux homonymes parfaits sont fusionnés à tort, limite analysée dans le rapport. Les implémentations Pandas et Spark produisent des résultats strictement identiques. Toutes les données manipulées sont fictives.

#= Abstract

In a healthcare institution, patient data is spread across several independent information systems — consultations, pharmacy, imaging, hospital management — that share no common identifier. The same person appears several times in different forms, and no system controls who accesses their data or for what purpose.

This internship, carried out at Madagascar Medical Technology (MMT), focused on designing a platform to centralise and govern this data. The chosen architecture is a data lake organised in three zones of increasing quality (RAW, SILVER, GOLD) on HDFS, Hive and Spark, fed by a replayable, incremental and schedulable ELT pipeline. It is complemented by an explainable deduplication engine, combining an exact pass on normalised keys with a probabilistic pass based on a weighted score, and by access governance that associates roles, purpose-based patient consent and an audit log.

Run on the virtual machine with a hard synthetic dataset, the platform reduces 1,057 records to 803 patients. Evaluated on three synthetic datasets with known ground truth, deduplication reaches a precision of 1.000 at every level — no false merge — and a recall of 0.422 on the hardest dataset; the full pipeline, measured the same way, achieves the same result. On 100,000 patients, processed in 7 minutes, two perfect homonyms are wrongly merged, a limit analysed in the report. The Pandas and Spark implementations produce strictly identical results. All data used is fictitious.

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

Un patient se présente à la pharmacie, puis en consultation, puis au service d'imagerie. À chaque étape, il est enregistré de nouveau, dans une base différente et sous une forme différente. Aucun de ces services ne sait qu'il s'agit de la même personne, et aucun ne peut lui demander ce qu'il accepte que l'on fasse de ses données.

C'est la situation de nombreux établissements de santé : des systèmes indépendants, chacun avec sa base, son format et ses identifiants. Or les données de santé sont sensibles : leur usage doit être **gouverné**, c'est-à-dire contrôlé selon qui les demande, pour quelle finalité et avec l'accord du patient.

Le stage s'est déroulé du 6 juillet à fin octobre 2026 au département Recherche et Développement de **Madagascar Medical Technology (MMT)**. La mission était de concevoir une plateforme de centralisation et de gouvernance des données patients : intégrer des sources hétérogènes, reconnaître un même patient d'une base à l'autre et n'ouvrir l'accès à ses données que selon son consentement, aujourd'hui **par finalité**, et **par type de dossier** en cours de développement. Deux contraintes encadrent ce travail : l'**hébergement interne** et l'usage exclusif de **données synthétiques**. La plateforme est livrée comme prototype reproductible, non déployé.

D'où la problématique : **comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités et la gouvernance des accès basée sur le consentement du patient ?**

Pour y répondre, ce rapport s'organise comme suit :

- **Chapitres 1 et 2** : le cadre du stage, puis l'état de l'art du domaine ;
- **Chapitres 3 et 4** : l'étude de l'existant, la solution envisagée et la démarche de projet ;
- **Chapitres 5 à 7** : les exigences réalisées, l'architecture et la conception du logiciel ;
- **Chapitre 8 et conclusion** : les tests et l'évaluation, puis le bilan, les limites et les perspectives.

# Présentation du stage

## Présentation de l'entreprise

La société **Madagascar Medical Technology (MMT)** a été créée en 2009 afin de répondre aux besoins des professionnels de la santé à Madagascar. Son activité englobe la distribution et la maintenance de matériels biomédicaux, la fourniture de consommables, ainsi que la gestion de stock des établissements partenaires.

L'entreprise réunit une équipe spécialisée dans l'ingénierie biomédicale, qui accompagne l'évolution technologique du secteur. Dans le cadre de son développement, MMT a conclu une convention avec Siemens Healthineers, qui lui confère le statut de *Business Partner* à Madagascar, avec un rattachement direct à la branche sud-africaine du groupe.

Depuis 2024, l'entreprise dispose d'un **département Recherche et Développement**, chargé de la gestion des systèmes d'information médicale ainsi que des infrastructures et réseaux informatiques. C'est dans ce département que s'est déroulé le stage. Les systèmes rencontrés illustrent ce périmètre : une base de gestion hospitalière fondée sur GNU Health, une plateforme de gestion hospitalière distante fondée sur Odoo (MAVIS) et la base d'une clinique ; ils sont décrits au chapitre 3.

## Présentation du sujet et objectifs du projet

### Contexte métier

Le cas de référence de la plateforme en donne un exemple concret : trois fiches désignent une seule et même personne :

Tableau: Trois fiches d'un même patient fictif.
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

Figure: Les quatre notions clés du rapport. | documents/figures/notions_cles.png | 16

Le cahier des charges fixe six objectifs, qui structurent l'ensemble du projet : **centraliser** les données dans une architecture Big Data, les **nettoyer et standardiser** selon un modèle commun, les **dédupliquer** avec une logique toujours explicable, **gouverner les accès**, **visualiser** les indicateurs et **évaluer** la déduplication. Leur traduction en exigences vérifiables figure au chapitre 5.

### Enjeux et risques

La dispersion des données entraîne des risques d'erreurs médicales (dossier éclaté), des analyses faussées (agrégats comptant des fiches plutôt que des patients) et des failles de confidentialité. Chaque enjeu porte un risque que la solution doit maîtriser.

Tableau: Enjeux, risques et maîtrise.
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

Tableau: Mesures de similarité classiques.
| Mesure | Principe | Usage typique |
|---|---|---|
| Levenshtein | nombre minimal d'insertions, suppressions et substitutions | nom, prénom |
| Damerau (OSA) | Levenshtein avec transposition de deux caractères adjacents | fautes de frappe |
| Jaro-Winkler | similarité qui favorise un début de chaîne commun | initiales, noms tronqués |
| Mesures par mots | comparaison des mots indépendamment de leur ordre | *Rakoto Jean* et *Jean Rakoto* |

Le projet utilise **RapidFuzz** [4], bibliothèque libre qui implémente ces mesures de façon performante. Son intérêt est opérationnel : légère et compatible avec Python 3.8, elle évite les dépendances lourdes de traitement du langage.

Comparer chaque enregistrement à tous les autres est quadratique : pour *n* patients, de l'ordre de *n²* comparaisons, soit 10¹² pour un million de patients. La pratique standard, le **blocking**, regroupe les enregistrements en blocs de candidats partageant une clé grossière — préfixe du nom, date de naissance, CIN — et ne compare qu'à l'intérieur de ces blocs [1], [3].

### Master Patient Index et interopérabilité FHIR

En santé, le rapprochement aboutit à un **Master Patient Index** : chaque fiche des bases sources est rattachée à un identifiant unique, le *master patient*, par une **identity map** traçable.

Tableau: Exemple d'identity map.
| Source | Identifiant source | Patient maître | Score | Méthode |
|---|---|---|---:|---|
| pharmacy | 15 | 102 | 1,000 | exacte |
| consultation | 88 | 102 | 0,950 | probabiliste |
| imaging | IMG-20 | 102 | 0,920 | probabiliste |

Cette démarche rejoint le standard **FHIR** (HL7 *Fast Healthcare Interoperability Resources*), qui prévoit une opération dédiée, `$match` : à partir des champs d'un patient, elle retourne les correspondances candidates avec un score explicite [5]. Le projet en reprend la philosophie — rechercher puis apparier par score — sans serveur FHIR. FHIR sert aussi de **schéma pivot** : quatre ressources (`Patient`, `Encounter`, `Condition`, `Observation`) harmonisent des sources structurées différemment.

### Consentement et RGPD

Les données de santé sont une catégorie particulière de données personnelles : leur traitement est **en principe interdit** par l'article 9 du RGPD, sauf exceptions, dont le **consentement explicite** de la personne [10]. La CNIL précise que la base légale (article 6) et l'exception propre aux données sensibles (article 9) se cumulent, et que le consentement au traitement des données diffère du consentement aux soins [11], [12]. Le projet traduit ces principes en mécanismes vérifiables.

Tableau: Du RGPD aux mécanismes implémentés.
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

Tableau: Comparaison des solutions.
| Critère | EMPI | Talend | Azure | HAPI | Splink | Atlas | Stage |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Déduplication explicable | oui | oui | non | non | partiel | non | oui, testé |
| Interopérabilité FHIR | partiel | non | oui | oui | non | non | oui, testé |
| Rôle, consentement et audit | partiel | partiel | oui | non | non | partiel | oui, conçu |
| Montée en charge Big Data | partiel | oui | oui | non | oui | oui | oui, testé |
| Hébergement interne | oui | oui | non | oui | oui | oui | oui, testé |
| VM 8 Go et Python 3.8 | non | non | non | non | partiel | non | oui, testé |

Aucun produit ne satisfait les six critères. Les solutions les plus complètes sur l'identité (EMPI, Talend) sont les plus lourdes et les plus coûteuses ; les solutions compatibles avec l'hébergement interne ne résolvent ni le rapprochement, ni la gouvernance, ni l'explicabilité. Le délai de quatre mois et l'environnement entièrement interne achèvent d'écarter l'adoption d'un produit.

## Pertinence entre le projet et l'état de l'art

Le projet ne réinvente pas les concepts : il **réutilise les standards et les algorithmes existants** et ne développe que la chaîne d'exécution et de gouvernance qu'aucune solution ne fournit dans le contexte imposé.

Tableau: Ce que le projet reprend de l'état de l'art.
| Élément repris | Provenance | Implémentation retenue |
|---|---|---|
| Décision match / non-match | Fellegi-Sunter [2] | score pondéré explicable (0,5 / 0,3 / 0,1 / 0,1), seuil 0,80 |
| Appariement par score | FHIR `$match` [5] | même principe dans le moteur, sans serveur FHIR |
| Schéma pivot | FHIR [5] | quatre entités : patient, rencontre, pathologie, observation |
| Zones de qualité croissante | Medallion [9] | RAW, SILVER, GOLD sur HDFS et Hive |
| Référentiel d'identité | MPI [13] | patient maître et identity map dans PostgreSQL |
| Gouvernance | catalogue de métadonnées [18] | contrôle appliqué à chaque requête : rôle, consentement, audit |

Trois écarts à l'existant sont assumés. Le projet n'utilise pas d'estimation automatique des poids comme Splink, afin que les poids restent lisibles et modifiables par un gestionnaire de données. Il n'utilise pas de référentiel externe comme EMPI, afin qu'aucune donnée tierce n'entre dans la plateforme. Il n'utilise pas de service managé comme Azure, le lac restant interne à la VM. Le risque propre à une chaîne sur mesure est la maintenabilité ; il est réduit en déclarant poids, seuil et blocking dans un fichier de configuration unique (chapitre 7).

# Étude de l'existant et solution envisagée

## Étude de l'existant

### Description externe du système existant (vision utilisateur)

Du point de vue d'un utilisateur, chaque service travaille dans son propre logiciel : la gestion hospitalière s'appuie sur MAVIS, une application Odoo étendue par un module hospitalier ; les dossiers médicaux relèvent de GNU Health ; une clinique tient ses patients, visites, diagnostics et observations dans une base à part. Chaque logiciel est complet dans son périmètre : on y crée un patient, on y consulte son historique, on y saisit ses actes.

L'utilisateur ne peut pas, en revanche, passer d'un système à l'autre. Une recherche de patient ne renvoie que les fiches du logiciel ouvert. La même personne apparaît sous des formes différentes selon le service, sans que rien ne le signale. Enfin, aucun écran n'indique qui a consulté un dossier, pour quelle finalité, ni si le patient y a consenti. Cette vision est reconstituée à partir des schémas capturés et du cahier des charges ; aucune enquête auprès des utilisateurs n'a été conduite.

### Description interne du système existant (vision développeur)

Les schémas et volumes des systèmes rencontrés ont été capturés et consignés au cours du stage.

Tableau: Les sources étudiées.
| Source | Socle | Volume vérifié | Tables retenues | Particularités |
|---|---|---|---|---|
| MAVIS | Odoo et module hospitalier, PostgreSQL distant | 73 090 lignes en réplique locale ; 1 260 tables sur le nœud distant | 11, dont `hms_patient` et `res_partner` | nœud distant instable ; jointure patient–partenaire vérifiée sur 9 791 lignes sur 9 791 |
| MMT_DB | GNU Health, PostgreSQL local | 60 271 lignes, 9 tables | 3 : patients, personnes, familles | 5 clés étrangères découvertes automatiquement |
| CLINIQUE | SQLite | 54 582 lignes, aucune violation de clé | 4 : patients, visites, diagnostics, observations | seule source déjà alignée sur les entités FHIR |
| Démonstration | fichiers CSV synthétiques | 76 / 76 / 62 au run de référence | patients et transactions | pharmacie, consultation, imagerie (graine 42) |

Capture: C01 | Schéma de la base MAVIS. | C01_schema_mavis.png | Optionnel. Liste des tables ou diagramme du schéma MAVIS (DBeaver, pgAdmin) ; aucune ligne de données patient ne doit être visible.

Chaque base est cohérente avec elle-même : l'intégrité référentielle existe à l'intérieur d'une source. C'est l'absence d'équivalent **entre** sources qui pose problème. Les données réelles ne pouvant pas être utilisées, trois sources synthétiques reproduisent l'hétérogénéité observée. Ces fichiers CSV sont des **sources de test** : ils servent uniquement à exercer et à évaluer la plateforme sur des données fictives, générées avec une graine fixe. Ils ne représentent pas les sources de production : en établissement, la plateforme lirait directement les bases des services (PostgreSQL, SQLite ou autre), par la même couche d'extraction. L'hétérogénéité est reproduite sur un triple plan :

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

Figure: L'existant à MMT et la réponse du projet. | documents/figures/fig-1.png | 15

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

Tableau: Le contrat de normalisation.
| Champ | Règle de normalisation | En cas d'échec |
|---|---|---|
| Genre | liste fermée de libellés masculins et féminins ramenés à `M` ou `F` | valeur vide, jamais devinée |
| CIN | seuls les chiffres sont conservés | valeur vide si la longueur sort de 6 à 12 chiffres |
| Date de naissance | format ISO, sinon lecture jour-mois-année | date inconnue |
| Nom | accents, casse et ponctuation supprimés | chaîne vide si le nom est absent |

Une règle gouverne les quatre champs : **aucune valeur n'est devinée**. Un champ douteux produit une valeur vide, qui exclut l'enregistrement du rapprochement exact et le renvoie vers la voie probabiliste ; il ne peut donc pas provoquer une fusion exacte erronée.

## Objectifs principaux et livrables

Les objectifs principaux sont les six objectifs du cahier des charges, traduits en exigences vérifiables au chapitre 5. Le périmètre couvert comprend : le pipeline ELT en cinq étapes avec reprise, ingestion incrémentale et planification ; le moteur de déduplication exact et probabiliste, en Pandas et en PySpark ; la gouvernance (rôles, consentement par finalité, audit, clés hachées) ; deux API REST ; et l'évaluation de la déduplication sur trois niveaux de difficulté. Les tableaux de bord d'analyse et le déploiement chez le commanditaire sont hors périmètre.

Tableau: Livrables et état en fin de stage.
| N° | Livrable | État à la fin du stage |
|:---:|---|---|
| 1 | Code source complet dans un dépôt unique | réalisé |
| 2 | Pipeline ELT Big Data | réalisé ; 4 étapes sur 4 réussies au run de référence du 07/09/2026, orchestration portée depuis à 5 étapes |
| 3 | Moteur de déduplication et évaluation sur vérité terrain | réalisé |
| 4 | Base centrale PostgreSQL (patients maîtres, consentements, audit) | réalisé ; alimentée par le pipeline sur une base de test (30/09/2026) |
| 5 | API des indicateurs et API de gouvernance | réalisé |
| 6 | Documentation technique et manuel conceptuel | réalisé |
| 7 | Frontend (optionnel) | réalisé partiellement : pilotage du pipeline et consultation des patients |
| 8 | Rapport de stage et support de soutenance | ce document ; support de soutenance |

# Démarche projet

## Principes de la démarche projet

### Activités d'ingénierie logicielle

Le projet a mobilisé les cinq activités classiques de l'ingénierie logicielle, chacune ayant laissé une production vérifiable dans le dépôt.

Tableau: Activités d'ingénierie et productions.
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

L'effectif réduit a une conséquence qu'il convient de mentionner : la revue de code croisée n'a pas eu lieu, ce qui limite la valeur des tests comme preuve externe. Ces rôles de projet sont distincts des rôles applicatifs (`admin`, `analyst`, `viewer`) qui régissent l'accès aux données une fois le logiciel livré (section 7.3.3).

### Outils

Les outils retenus sont tous libres ou gratuits. Ils sont présentés par usage, avec la version effectivement employée.

Tableau: Les outils du projet. {logos}
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
| Big Data | logo:hadoop Hadoop | 3.3.6 | HDFS stocke les zones du lac ; YARN, démarré, n'est pas encore utilisé (Spark en mode local) |
| ^ | logo:hive Hive | 3.1.3 | catalogue des tables du lac et accès SQL |
| ^ | logo:spark Spark / PySpark | 3.4.2 | traitements répartis : mapping FHIR, déduplication, zone GOLD |
| ^ | logo:openjdk OpenJDK | 8 | machine Java requise par Hadoop, Hive et Spark |
| Données et moteur | logo:postgresql PostgreSQL | 18.2 | base centrale : patients maîtres, consentements, audit |
| ^ | logo:pandas pandas | ≥ 2.0 | MVP et implémentation Pandas du moteur |
| ^ | logo:rapidfuzz RapidFuzz | ≥ 3.0 | similarité des noms dans le score de rapprochement |
| ^ | logo:fhir HL7 FHIR | R5 (5.0.0) | standard de référence du schéma pivot |
| Exposition | logo:fastapi FastAPI | ≥ 0.115 | API de gouvernance : rôles, finalité, consentement, audit |
| ^ | logo:flask Flask | non épinglée | API des indicateurs des zones SILVER et GOLD |
| ^ | logo:nextjs Next.js | 15.4.6 | interface web optionnelle (React, TypeScript, Tailwind CSS, D3.js) |
| Qualité et documentation | logo:pytest pytest | ≥ 7.0 | 123 tests du moteur, de la gouvernance et du pipeline |
| ^ | logo:mermaid Mermaid | CLI (npx) | diagrammes de conception de ce rapport |

Les versions sont celles du provisionnement de la VM et des fichiers de dépendances ; « ≥ » indique une version minimale.

### Gestion de la configuration

Le projet est rejouable à partir du seul dépôt. Le dépôt Git est la source de vérité : code, pipeline, configuration, tests et documentation, avec un journal daté des décisions. Les données patients ne sont pas versionnées mais régénérées par le générateur synthétique à graine fixe ; les secrets sont fournis par variables d'environnement. Les paramètres qui gouvernent le comportement (seuil, poids, finalités, partitions Spark) sont déclarés en configuration, jamais dans le code. Enfin, la suite de tests est exécutée à chaque jalon, et son succès conditionne le jalon suivant.

## Contraintes et risques sur le projet

Tableau: Contraintes et risques du projet.
| Contrainte ou risque | Traitement adopté | Constat |
|---|---|---|
| VM de 8 Go et 4 cœurs | Spark en mode local : un processus de 2 Go, 8 partitions | maîtrisé au volume du prototype ; gels de la VM observés à 25 587 fiches |
| Nœud MAVIS distant instable | répliques locales, puis sources synthétiques pour le run final | contourné |
| Hétérogénéité des sources | synonymes et similarité pour le mapping FHIR | maîtrisé au 30/09/2026 : dates et noms corrigés, 1 761 événements en GOLD |
| Reproductibilité | graine 42, seuil et pondérations fixés en configuration | appliqué |
| Données sensibles (RGPD, article 9) | données synthétiques uniquement ; rôles, audit et consentement | maîtrisé |
| VM indisponible en fin de stage | tests hors VM avant toute exécution réelle | VM relancée le 30/09/2026 : runs complets et en reprise réussis ; cron non activé |

Les contraintes techniques découvertes en cours de développement (Python 3.8, partage de fichiers de la VM) sont traitées avec les difficultés rencontrées, au chapitre 7.

Le contexte local conditionne aussi l'applicabilité de la solution. En l'absence d'annuaire d'identité dans le service, l'accès à l'API repose sur des **clés d'API associées à un rôle** plutôt que sur des comptes nominatifs. Le réseau intermittent et l'absence de cluster ont conduit à une conception **mono-nœud et rejouable**. Enfin, le cadre juridique malgache des données de santé n'a pas été étudié : la conformité présentée s'appuie sur le RGPD, qui constitue un cadre de conception exigeant mais doit être transposé au droit local avant toute mise en production.

## Démarche projet mise en œuvre

Le travail s'est organisé en cinq jalons, chacun validé par un critère de sortie vérifiable. Les deux prototypes d'origine ont avancé en parallèle avant d'être fusionnés dans le dépôt unique.

Tableau: Les cinq jalons du stage.
| Jalon | Contenu | Critère de sortie atteint | Dates |
|---|---|---|---|
| J1 — Socle | générateur de données synthétiques et vérité terrain | 44 tests verts, 500 patients maîtres, 3 niveaux de difficulté | 01/09/2026 |
| J2 — Moteur | normalisation, blocking, rapprochement exact et probabiliste | précision de 1,000 ; parité Pandas et Spark | 07–08/09/2026 |
| J3 — Big Data | pipeline ELT Medallion RAW → SILVER → GOLD | 4 étapes sur 4, 214 lignes SILVER, 145 patients maîtres | 23/08–07/09/2026 |
| J4 — Gouvernance | rôles, clés, consentement, audit ; planification et reprise | suite de tests complète verte, refus 401 et 403 vérifiés | 01/09 et 27–28/09/2026 |
| J5 — Rapport | structuration selon le plan MBDS, état de l'art sourcé | 20 références, aucun chiffre non vérifiable | 08–28/09/2026 |

Les premières semaines ont été consacrées à une analyse itérative : discussions avec l'encadrant, compréhension du sujet, analyse de l'existant, documentation et état de l'art, puis confrontation aux contraintes réelles (nœud MAVIS instable, VM de 8 Go, Python 3.8). Ces activités se sont répétées en boucle, chaque contrainte découverte relançant une discussion ou une recherche, ce qui justifie une démarche itérative plutôt qu'un cycle en cascade.

## Planification

Le diagramme de Gantt ci-dessous répartit les activités sur les quatre mois du stage, par quinzaine. Il distingue les périodes datées par le journal du dépôt (bleu foncé), les périodes déclarées sans trace datée (bleu clair ; les journaux commencent le 23/08/2026) et les périodes prévues (gris).

Tableau: Diagramme de Gantt du stage. {gantt}
| Phase | 06/07 | 20/07 | 03/08 | 17/08 | 31/08 | 14/09 | 28/09 | 12/10 |
|---|---|---|---|---|---|---|---|---|
| Cadrage du sujet | □ | □ | □ | | | | | |
| Existant et contraintes | □ | □ | □ | ■ | ■ | | | |
| Documentation et état de l'art | | □ | □ | □ | ■ | ■ | | |
| Développement | | | | ■ | ■ | ■ | ■ | |
| Tests et évaluation | | | | ■ | ■ | ■ | ■ | |
| Rédaction du rapport | | | | | ■ | ■ | ■ | ○ |
| Finalisation et soutenance | | | | | | | ○ | ○ |

Ce découpage a rendu chaque jalon démontrable indépendamment. Il a en revanche coûté du temps : la parité stricte entre Pandas et Spark a exigé d'écrire l'algorithme deux fois, ce qui aurait pu être évité si l'échelle cible avait été arrêtée plus tôt. C'est la principale leçon de conduite de projet tirée du stage.

## Budget du projet

Le budget couvre la durée du stage (quatre mois) et le périmètre réalisé, un prototype reproductible sur la VM de développement ; aucun coût de production n'est compté. Les **coûts humains sont des hypothèses de travail**, établies sur l'ordre de grandeur des rapports de référence et non sur des comptes du commanditaire ; ils sont à remplacer par les chiffres réels avant toute diffusion. Les coûts matériels et logiciels, eux, sont réels.

Tableau: Budget du projet sur quatre mois.
| Poste | Base de calcul | Coût (Ar) |
|---|---|---:|
| Développeur (stagiaire) | 1 ETP à 1 000 000 Ar par mois (hypothèse) | 4 000 000 |
| Encadrement professionnel et pédagogique | 2 × 0,1 ETP, 150 000 Ar par mois (hypothèse) | 600 000 |
| Poste de travail et VM | matériel existant, VM hébergée sur le poste | 0 |
| Logiciels | Hadoop, Hive, Spark, PostgreSQL, FastAPI, Flask, Next.js, Pandas, RapidFuzz, pytest, Vagrant, Git (open source) | 0 |
| Serveur de production | non applicable : plateforme non déployée | 0 |
| Solutions commerciales comparées | étudiées sur documentation, non acquises | 0 |
| **Total** | | **4 600 000** |

Le coût total, **4 600 000 Ar**, est entièrement humain. Ce coût logiciel et matériel nul est un avantage décisif de l'open source dans un contexte aux moyens limités. Un déploiement en production ajouterait des postes non chiffrés ici : serveur, sauvegarde et exploitation.

# Exigences réalisées dans le projet (vision externe/utilisateur)

## Exigences fonctionnelles

Les six objectifs du cahier des charges sont traduits en exigences fonctionnelles vérifiables, organisées en quatre étapes qui suivent le chemin de la donnée, puis une activité transverse d'évaluation.

Tableau: Exigences fonctionnelles.
| N° | Exigence | Critère de succès | Cas d'utilisation |
|---|---|---|---|
| F1 | Centraliser les données dans un lac | pipeline Medallion RAW → SILVER → GOLD | CU1 |
| F2 | Nettoyer et standardiser | modèle canonique et pivot FHIR | CU2 |
| F3 | Dédupliquer de façon explicable | patient maître et identity map (score, méthode, seuil) | CU3 |
| F4 | Gouverner les accès | rôles, consentement par finalité, audit, clés hachées | CU4, CU5 |
| F5 | Visualiser les indicateurs | vues de déduplication et de consentement | CU6, CU7, CU8 |
| F6 | Évaluer la déduplication | précision, rappel et F1 sur vérité terrain | section 5.1.5 |

### Étape 1 : Intégration des sources

**CU1 — Ingérer un lot de sources.** Le processus automatique lit chaque source et l'écrit telle quelle dans la zone RAW du lac ; le nombre de lignes écrites par table figure dans le rapport d'extraction et dans l'historique du run. Une table absente ou illisible est consignée comme échec sans bloquer les autres, et une source inchangée depuis le run précédent n'est pas relue.

**CU2 — Ramener des formats différents à un modèle unique.** L'étape de mapping associe chaque champ FHIR attendu à la colonne source la plus proche, puis la normalisation produit le modèle canonique dans la zone SILVER. Toute fiche en sort au même format, quelle que soit sa source. Un champ sans équivalent reste vide et n'est jamais deviné ; les règles de mapping sont décrites dans un fichier, et non dans le code.

### Étape 2 : Déduplication et MPI

**CU3 — Décider qui est le même patient.** Le blocking réduit les comparaisons, le rapprochement exact s'applique d'abord, puis le rapprochement probabiliste pondéré au-dessus du seuil de 0,80. Le résultat est un patient maître par personne retenue, et une identity map qui relie chaque fiche d'origine à son patient maître avec le score et la méthode de décision. Aucune fusion n'est appliquée sans y être inscrite.

### Étape 3 : Gouvernance des accès

**CU4 — Préparer le consentement dans la zone GOLD.** L'étape GOLD associe à chaque patient maître ses avis par finalité, lus dans la base centrale ; sans avis, la finalité est considérée comme refusée. Le contrôle lui-même s'applique au moment de l'accès, par l'API (CU5).

**CU5 — Interroger l'API pour un patient.** Un utilisateur présente une clé d'API. La clé est résolue en utilisateur et en rôle, la finalité demandée est comparée aux consentements, la réponse est renvoyée, et l'appel est journalisé. Pour la fiche d'un patient, une finalité non consentie produit un refus explicite (code 403), et non une réponse vide, journalisé au même titre qu'un accès accordé ; dans une liste, les patients non consentis sont retirés et leur nombre est journalisé. Un refus doit être visible pour que le dispositif soit crédible.

### Étape 4 : Exploitation et pilotage

**CU6 — Consulter les vues de gouvernance.** L'interface web affiche les indicateurs de déduplication (patients maîtres, doublons, méthodes) et de consentement (accords et refus par finalité), calculés sur des données dédupliquées. Si le lac ne répond pas, l'API se replie sur un jeu de démonstration, signalé comme tel à l'écran.

**CU7 — Planifier et piloter le pipeline.** L'administrateur fixe la fréquence d'exécution (quotidienne, hebdomadaire ou mensuelle) par l'API ou un fichier de configuration ; le pipeline se lance alors seul, sans exécution simultanée, et reprend après un échec (chapitre 7).

**CU8 — Consulter un dossier patient.** Un médecin authentifié recherche un patient en déclarant sa finalité. Les patients sans consentement pour cette finalité sont retirés de la liste ; la fiche affiche l'identité, l'identity map et les consentements par finalité.

### Évaluation : générateur et vérité terrain

Évaluer objectivement une déduplication exige de connaître la vérité, ce qui est impossible avec des données réelles. Un **générateur de données synthétiques** produit donc des données fictives et leur vérité terrain, de façon déterministe (graine 42) :

- **500 patients maîtres** aux identités propres, dont environ 75 % portent un CIN ;
- une **distribution** entre les trois sources selon des probabilités de présence de 0,8, 0,7 et 0,6, soit **1 057 enregistrements** répartis en 404, 353 et 300 ;
- un **moteur de variations** à trois niveaux de difficulté — facile (10 %), moyen (30 %) et difficile (50 %) — qui injecte des erreurs de casse, d'espaces, de format, des inversions, des fautes de frappe, des abréviations et des valeurs manquantes ;
- une **table de vérité** reliant chaque enregistrement à son patient réel, **jamais fournie à l'algorithme** et réservée à l'évaluation.

## Exigences non fonctionnelles transverses

Tableau: Exigences non fonctionnelles.
| Qualité | Exigence | Réalisation | Preuve ou limite |
|---|---|---|---|
| Utilisabilité | un refus doit être compréhensible | finalité inconnue : code 422 avec la liste des valeurs autorisées ; refus : 403 avec motif journalisé | vérifié (section 8.3) |
| Performance | pipeline complet en moins de 30 minutes | cible atteinte au run de référence | volume réel non mesuré |
| Scalabilité | changer d'échelle sans changer la logique | moteur porté en PySpark avec parité stricte, comparaisons bornées | résultats identiques Pandas et Spark (section 8.4) ; déduplication exécutée sur une seule machine |
| Sécurité | aucun accès sans rôle, finalité et consentement | rôles, clés hachées, consentement, audit, secrets hors dépôt | codes 401, 403 et 422 vérifiés ; hachage non salé |
| Maintenabilité | faire évoluer le comportement sans toucher la logique | poids, seuil et blocking en configuration ; schéma idempotent | 123 tests sur 123 réussis |
| Fiabilité | ne pas retraiter en boucle, reprendre après échec | empreinte des sources, reprise, verrou anti-double exécution, historique des runs | 66 tests ; reprise validée sur la VM (6 tables sur 6 sautées) ; cron non exécuté |
| Confidentialité | aucune donnée réelle | générateur synthétique à graine fixe | aucune donnée réelle dans le dépôt |

## Interfaces détaillées

### Interface homme-machine

L'interface web (Next.js) est **optionnelle** au sens du cahier des charges. Elle se limite au pilotage du pipeline, aux vues de gouvernance et à la consultation des patients. L'accès est contrôlé par jeton avec deux profils, administrateur et médecin, et la finalité reste un paramètre obligatoire des pages patients.

Tableau: Pages de l'interface web.
| Page | Contenu affiché | Source des données |
|---|---|---|
| Connexion | authentification (administrateur, médecin) | interface |
| Synthèse | qualité d'identité et consentement côte à côte | API des indicateurs |
| Doublons | patients, maîtres, doublons résolus, répartition par méthode | API des indicateurs |
| Gouvernance | consentements par patient et par finalité, taux d'accord | API des indicateurs |
| Pipeline et tableau de bord | zones Medallion, étapes du dernier run, fraîcheur des sources, planification | API de gouvernance |
| Patients | recherche, pagination, fiche d'identité, identity map, consentements | API de gouvernance |

Chaque vue signale par un bandeau les données de démonstration ; les figures suivantes en présentent trois écrans.

Capture: C04 | Page de synthèse. | C04_synthese.png | Page /synthese avec les indicateurs (patients maîtres, doublons, taux, accords et refus).

Capture: C07 | Tableau de bord du pipeline. | C07_pipeline.png | Page /dashboard (ou /pipeline) montrant les zones RAW, SILVER, GOLD, le dernier run et la prochaine échéance.

Capture: C09 | Fiche d'un patient. | C09_fiche_patient.png | Page /patients/{id} d'un patient ayant plusieurs fiches sources (idéalement le cas « Jean Rakoto »).

### Interfaces avec d'autres systèmes

**L'API de gouvernance (FastAPI)** est le seul point d'application de la règle d'accès. Chaque appel présente une clé d'API, résolue en utilisateur et en rôle, et chaque appel est journalisé.

Tableau: Points d'entrée de l'API de gouvernance.
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

Capture: C10 | Documentation interactive de l'API. | C10_swagger.png | Page /docs de l'API FastAPI (port 8000), liste des points d'entrée dépliée.

Une clé absente ou inconnue produit un code 401, un rôle insuffisant un code 403. **L'API des indicateurs (Flask)** expose deux points d'entrée de reporting, sur la table SILVER des patients et sur la table GOLD des consentements ; elle ne contrôle pas l'accès, ce contrôle étant réservé à l'API de gouvernance. La plateforme échange enfin avec les sources (CSV, PostgreSQL, SQLite), avec le lac (HDFS et Hive), avec la base centrale PostgreSQL et avec le planificateur de la VM.

# Architecture du système

## Architecture logicielle

L'architecture suit la progression en trois niveaux : chaque niveau réutilise la **même logique métier**, seule l'infrastructure d'exécution change.

Figure: L'architecture en trois niveaux. | documents/figures/fig-4.png | 15

La chaîne retenue (niveau 3) va de la source hétérogène à l'API gouvernée. Les sources sont extraites vers la zone RAW en fichiers Parquet sur HDFS, décrites par des tables Hive externes. Le mapping FHIR produit les quatre tables de la zone SILVER, où le moteur de déduplication rattache chaque ligne à son patient maître. La zone GOLD porte les agrégats prêts à l'analyse et les consentements. La base centrale PostgreSQL conserve l'état de référence : patients maîtres, identity map, consentements, utilisateurs et journal d'audit. Les deux magasins ont des rôles distincts : le lac est **rejouable**, la base centrale est **de référence**.

Tableau: Briques de la chaîne et conception.
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

Tableau: Composants de la VM et ports.
| Composant | Rôle | Port |
|---|---|---:|
| HDFS NameNode | stockage du lac (Parquet RAW, SILVER, GOLD) | 9000 |
| YARN | gestionnaire de ressources d'un futur cluster, non utilisé par le pipeline | 8088 |
| Hive Metastore | catalogue des bases du lac | 9083 |
| HiveServer2 | accès SQL | 10000 |
| API des indicateurs (Flask) | exposition des zones SILVER et GOLD | 5000 |
| API de gouvernance (FastAPI) | patients, consentements, audit, planification | 8000 |
| Planificateur | déclenchement du pipeline selon la fréquence définie | cron |
| Interface web (Next.js) | pilotage et consultation, sur l'hôte Windows | 3000 |

Capture: C11 | Les zones du lac dans HDFS. | C11_hdfs_datalake.png | Interface HDFS (port 9870), menu Utilities > Browse the file system, dossier /datalake montrant raw, silver et gold.

Les versions installées sont Hadoop 3.3.6, Hive 3.1.3, Spark 3.4.2 et Java 8. Spark s'exécute en mode local : un seul processus Java de 2 Go exécute toutes les tâches, avec 8 partitions, afin de tenir dans la mémoire de la VM ; le réglage prévu pour l'exécuteur ne s'applique qu'en cluster.

# Conception du système logiciel réalisée dans le projet (vision interne/développeur)

## Plate-forme technique

Chaque concept de l'état de l'art est porté par une brique technique précise (section 2.5).

Les choix technologiques ont été arbitrés sur cinq critères pondérés, issus des contraintes du stage : la compatibilité avec l'environnement (0,30, critère éliminatoire), l'explicabilité de la décision (0,25), le coût mémoire et la performance (0,20), la maturité et la documentation (0,15), et le coût de licence (0,10). Chaque option est notée de 1 à 5.

Tableau: Notation pondérée des options.
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

## Conception du logiciel développé

### Le code source : vue statique

Le code suit la séparation entre ingestion, normalisation, déduplication, gouvernance et exposition. Il se répartit en six blocs : le moteur d'identité (modèle canonique, déduplication Pandas et Spark), la gouvernance (clés, consentement, audit, API FastAPI), le provisionnement et le pipeline, l'exposition des indicateurs, les paramètres (configuration de la déduplication, schéma SQL) et l'évaluation avec les tests.

### Modélisation des données

**Le modèle canonique.** Chaque source possède son vocabulaire ; la conception introduit une représentation unique du patient (source, identifiant source, prénom, nom, nom complet, date de naissance, CIN, ville de naissance, adresse, genre). Le mapping des colonnes source vers ce modèle est explicite et déterministe.

Tableau: Mapping vers le modèle canonique.
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

Figure: Modèle de la base centrale. | documents/figures/fig-7.png | 24 | paysage

Les règles de gouvernance sont portées par la base elle-même : méthode de rapprochement et finalité en listes fermées, score borné entre 0 et 1, clés d'API conservées sous forme d'empreinte SHA-256, données brutes jamais exposées.

Code: X02 | Identity map et consentements | sql/schema.sql:30-65 | X02_schema.png

Le schéma est **idempotent** : tables et colonnes sont créées seulement si elles n'existent pas, et les insertions ignorent les doublons ; relancer le même traitement ne duplique rien.

**Les zones du lac.** La zone RAW reçoit la donnée brute en Parquet sur HDFS, décrite par des tables Hive externes. La zone SILVER contient les quatre tables FHIR normalisées, avec les doublons marqués et expliqués. La zone GOLD contient la table des événements patients (18 colonnes, 8 tranches d'âge) et la table des consentements.

### Composants

**Le moteur de déduplication.** Pour éviter la comparaison de toutes les paires, le moteur indexe les patients maîtres selon trois clés de blocking : les quatre premières lettres du nom normalisé, la date de naissance et le CIN. Seuls les candidats partageant l'une de ces clés sont comparés. La déduplication procède en deux passes :

1. **Rapprochement exact** : le patient partage la clé de rapprochement d'un patient maître (nom normalisé, date de naissance, CIN), ou bien la même date de naissance et le même CIN non vide, ce qui absorbe les inversions de prénom et de nom. Décision « exacte », score 1,0.
2. **Rapprochement probabiliste** : parmi les candidats, un score pondéré est calculé. Au-dessus de 0,80, la fiche est rattachée au patient maître ; en dessous, un nouveau patient maître est créé.

Tableau: Calcul du score de similarité.
| Critère | Similarité | Poids |
|---|---|---:|
| Nom | similarité de chaînes, sensible à l'ordre des mots (l'inversion est rattrapée par la règle exacte) | 0,50 |
| Date de naissance | égalité | 0,30 |
| CIN | égalité (si présent) | 0,10 |
| Ville de naissance | égalité après normalisation | 0,10 |

Les poids et le seuil ne sont pas écrits dans le code : ils sont déclarés dans un fichier de configuration unique (`config/deduplication.yaml`), lu par le moteur Pandas, sa version Spark et l'évaluation.

Code: X04 | Calcul du score pondéré | engine/identity/matcher.py::_similarity | X04_score.png

Chaque décision porte l'identifiant du patient maître, la méthode, le score et une explication en clair. La règle « jamais de fusion sans logique explicable » est ainsi **structurelle** : elle est inscrite dans le modèle de données, pas seulement dans une convention.

### Déploiement

L'installation sur la VM et l'ordre de démarrage des services sont décrits au chapitre 6. La plateforme est **reproductible depuis le dépôt** ; elle n'a pas été déployée sur un serveur du commanditaire.

## Réalisation des étapes

### Pipeline ELT Medallion

Le pipeline est orchestré par un script unique qui s'arrête à la première erreur et journalise chaque étape. Chaque étape est un programme distinct : une étape qui échoue ne laisse pas la zone suivante dans un état intermédiaire, condition pour que le pipeline reste relançable.

Tableau: Les étapes du pipeline ELT.
| Étape | Traitement | Production |
|---|---|---|
| 1 — Préparation | régénère les sources de démonstration si elles sont absentes | fichiers CSV synthétiques (sans effet s'ils existent) |
| 2 — Extraction RAW | copie brute des sources dans le lac | fichiers Parquet sur HDFS, tables Hive externes, rapport d'extraction |
| 3 — Mapping FHIR | association des colonnes source aux champs FHIR | fichier de correspondance |
| 4 — SILVER | normalisation FHIR et déduplication par le moteur | quatre tables FHIR enrichies du patient maître |
| 5 — GOLD | agrégation et application du consentement | table des événements patients, table des consentements |

Deux mécanismes évitent de retraiter en boucle. La **reprise** : l'état de chaque exécution et de chaque étape est persisté ; un run échoué repart de la première étape non terminée, et un run en cours verrouille tout lancement concurrent. L'**ingestion incrémentale** : chaque source conserve une empreinte (hachage, taille, date de modification) ; une source inchangée n'est pas ré-extraite. La **planification** confie le lancement régulier au planificateur de la VM, qui vérifie l'échéance chaque minute et lance le pipeline en arrière-plan. Chaque run laisse aussi son **historique chiffré** dans la base centrale (lignes par source, patients maîtres, doublons, volumes GOLD), restitué par l'API et le tableau de bord. Cette mécanique a été rejouée sur la VM le 30/09/2026 : un run en mode reprise a sauté les six tables inchangées ; seule la planification par cron n'a pas été activée.

Capture: C12 | Exécution du pipeline. | C12_run_pipeline.png | Terminal de la VM : sortie de run_pipeline.sh (ou fin de elt.log) montrant chaque étape terminée avec succès.

Tableau: Run de référence du 07/09/2026.
| Indicateur | Valeur |
|---|---:|
| Étapes réussies (orchestration de l'époque) | 4 sur 4 |
| Lignes dans la table SILVER des patients (76 + 76 + 62) | 214 |
| Patients maîtres distincts | 145 |
| Doublons rattachés (tous par rapprochement exact) | 69 |
| Taux de doublons | 32,24 % |
| Lignes de la table GOLD des consentements | 145 |
| Lignes de la table GOLD des événements | 0 |

Le passage de 214 à 145 se vérifie par un simple comptage : 214 − 69 = 145. À cette date, la table des événements était vide et la base centrale n'était pas alimentée.

Le pipeline a été rejoué sur la VM les 29 et 30/09/2026, avec en source le jeu d'évaluation difficile, dont la vérité terrain est connue. Ces runs ont révélé deux défauts de données, corrigés depuis : des dates de naissance perdues à l'extraction et des noms tronqués pour la source consultation.

Tableau: Runs réels du pipeline sur la VM (jeu difficile, 29–30/09/2026).
| Indicateur | Valeur |
|---|---:|
| Fiches SILVER (404 + 353 + 300) | 1 057 |
| Patients maîtres distincts | 803 |
| Doublons rattachés (exacts / probabilistes) | 254 (245 / 9) |
| Taux de doublons | 24,03 % |
| Table GOLD des événements | 1 761 lignes |
| Table GOLD des consentements (803 patients × 3 finalités) | 2 409 lignes |
| Durée d'un run complet | 2 min 56 s |
| Run en mode reprise : tables sources sautées | 6 sur 6 |

Mesuré sur la vérité terrain, le run complet obtient une précision de 1,000, un rappel de 0,424 et un F1 de 0,595 (0,422 et 0,594 pour le moteur seul) : la chaîne Big Data ne dégrade pas la déduplication.

Pour éprouver le volume, le pipeline a ensuite traité un jeu facile de 12 000 patients synthétiques (25 587 fiches, sans variation de saisie). Il retrouve les 12 000 patients maîtres, avec une précision et un rappel de 1,000, et produit 43 141 événements en GOLD. Ce run a révélé un défaut de passage à l'échelle, décrit plus loin : une fois corrigé, le run complet passe de 15 min 15 s à 4 min 57 s. Sur 100 000 patients (212 523 fiches, 359 299 transactions), le run complet dure 7 min 03 s, dont environ 5 minutes de déduplication, et retrouve 99 998 patients maîtres : deux homonymes parfaits ont été fusionnés à tort (voir l'évaluation). Ce run a traversé trois gels de la VM ; sur 12 000 patients, un premier run avait échoué pour cette raison.

### Moteur de déduplication : Pandas et Spark

Tableau: Implémentations Pandas et Spark.
| Aspect | Pandas | PySpark |
|---|---|---|
| Normalisation | modèle canonique | même modèle canonique |
| Passe exacte | clé de rapprochement, ou naissance et CIN | regroupement par clé |
| Passe probabiliste | index à trois clés de blocking | index borné sur les représentants de groupes |
| Score et seuil | 0,5 / 0,3 / 0,1 / 0,1 ; 0,80 | identiques |
| Décision | exacte, probabiliste ou nouveau maître | identique |

La parité est vérifiée sur la démonstration (18 fiches ramenées à 11 patients maîtres dans les deux implémentations) et sur l'évaluation complète, où les deux produisent exactement les mêmes décisions (chapitre 8).

### Gouvernance et API

La gouvernance applique trois mécanismes dans cet ordre : on vérifie **qui** demande, **pourquoi** il demande, puis on **trace** ce qui s'est passé.

- **Rôles** : `admin`, `analyst` et `viewer`, résolus à partir de la clé d'API présentée.
- **Clés d'API** : seule leur empreinte SHA-256 est stockée ; la clé en clair n'est jamais conservée.
- **Finalité déclarée** : paramètre obligatoire des requêtes sur les patients, validé contre une liste fermée ; une finalité inconnue produit un code 422.
- **Consentement par finalité** : la décision ne dépend pas du rôle seul ; un utilisateur autorisé mais sans finalité consentie est refusé (403). Dans une liste, les patients non consentis sont retirés et le nombre d'exclusions est journalisé.
- **Audit** : un *middleware* journalise chaque requête avec l'utilisateur, le point d'entrée, le statut, l'adresse, la finalité et le motif de refus, y compris pour les appels anonymes.

La règle de consentement tient en deux fonctions : la première lit le dernier avis enregistré et vaut refus en son absence ; la seconde valide la finalité, prépare les informations d'audit et oppose le refus.

Code: X05 | Vérification du consentement | engine/governance/consent.py::check_consent,enforce_consent | X05_consentement.png

Seuls les patients maîtres consolidés sont exposés, jamais les données brutes de la zone RAW. La distinction avec l'API des indicateurs, qui ne contrôle pas l'accès, est présentée au chapitre 5.

Capture: C14 | Contrôle d'accès sur la base peuplée et trace dans le journal d'audit. | C14_refus_403.png | Sortie réelle des requêtes (clés masquées) et des dernières lignes de access_audit.

### Difficultés rencontrées et résolutions

Tableau: Difficultés et correctifs.
| Problème | Cause | Correctif |
|---|---|---|
| Table SILVER passée à 11 614 lignes | une colonne d'identifiant capturée par le mapping FHIR automatique rendait l'identifiant source vide, d'où une jointure 76 × 76 | colonne exclue du mapping automatique ; chaque colonne source utilisée une seule fois |
| Écritures qui s'écrasaient d'une source à l'autre | écriture en mode remplacement dans la boucle par source | accumulation par entité, puis une seule écriture par table |
| Fichiers Parquet corrompus | entrepôt Spark écrit sur le partage de fichiers de la VM | entrepôt toujours écrit sur HDFS |
| Spark ne démarrait pas | variable `JAVA_HOME` mal formée | normalisation automatique du chemin Java |
| HiveServer2 instable | service fragile sur la VM | contrôle des volumes par scripts Spark |
| NLP lourd inutilisable | plantage de `sentence_transformers` sous Python 3.8 | RapidFuzz et dictionnaire de synonymes |
| Script d'extraction non compilable | caractère invisible dans un commentaire | caractère supprimé, script recompilé |
| NameNode qui ne redémarrait plus (30/09) | métadonnées HDFS dans `/tmp`, vidé au redémarrage de la VM | données HDFS déplacées hors de `/tmp` |
| Environ 20 % des dates de naissance perdues (30/09) | quatre formats mêlés dans une colonne ; seul le dominant était lu | lecture valeur par valeur, format par format |
| Noms tronqués pour la source consultation (30/09) | nom en deux colonnes, dont une seule était retenue | nom complet reconstitué avant le mapping |
| Déduplication de 25 587 fiches en près de 15 minutes (30/09) | la passe exacte comparait chaque fiche à tous les patients maîtres déjà créés | recherche directe par dictionnaire : moteur seul de 887 s à 13 s, décisions identiques |

Ces incidents relèvent de quatre familles. Les incidents de **données** ont donné lieu à des correctifs documentés comme pièges à ne pas reproduire. Les incidents d'**infrastructure** ont été contournés par des règles de configuration. L'incident d'**outillage** est le seul qui ait changé la méthode : l'approche par vecteurs a été abandonnée au profit d'un score pondéré, plus léger et plus explicable. Le dernier relève du **passage à l'échelle** : invisible sur un millier de fiches, il n'est apparu qu'avec 25 587.

# Tests du système logiciel

## Stratégie de test

La validation suit une pyramide : des tests unitaires rapides (générateur, moteur, gouvernance), des tests d'intégration (MVP, pipeline) et des tests système (API, évaluation sur vérité terrain). L'ordre des niveaux suit le coût d'un échec : un test unitaire échoue en quelques secondes et désigne une ligne de code ; un test système n'échoue qu'après un pipeline complet et nécessite la VM. En l'absence d'intégration continue, hors périmètre du stage, chaque niveau est rejouable manuellement.

Tableau: Niveaux de test et résultats.
| Niveau | Périmètre | Résultat |
|---|---|---|
| Générateur | variations, distribution, identity mapping, construction des jeux | 44 tests réussis |
| Moteur et gouvernance | rapprochement (12), consentement (21), normalisation (8), API de gouvernance (16) | 57 sur 57 |
| Planification et reprise | échéances (22), empreintes (10), état du pipeline (5), API de planification (8) | 45 sur 45 |
| MVP | pipeline, chargement PostgreSQL, authentification, audit, API | 20 tests réussis |
| API des indicateurs | trois vérifications sur les données du lac | 3 sur 3 |
| Pipeline | exécution complète RAW → SILVER → GOLD sur la VM | 4 étapes sur 4 (07/09/2026) |

Capture: C15 | Exécution des tests automatisés. | C15_pytest.png | Terminal : sortie de pytest projet/code-source/tests avec « 123 passed ».

La suite principale réunit les tests du moteur, de la gouvernance et du pipeline : **123 tests sur 123 réussis** (exécution du 30/09/2026), sans aucun échec.

## Tests unitaires et d'intégration

Les tests du moteur couvrent la sémantique de la déduplication : rapprochement exact avec des CIN de formats différents, inversion du nom compensée par la date de naissance et le CIN, fusion au seuil de 0,80, faute de frappe compensée par la date de naissance, contribution de la ville de naissance au score, **non-fusion de patients distincts** et parité entre Pandas et Spark. Les tests de planification vérifient le calcul des échéances, la décision de saut d'une source inchangée, la reprise d'un run échoué et l'API de planification.

Au niveau intégration, les 20 tests du MVP enchaînent pipeline, chargement en base, authentification, audit et API. Le run de référence du pipeline sur la VM a exécuté la chaîne complète RAW → SILVER → GOLD avec succès.

## Tests fonctionnels du contrôle d'accès

Les tests de l'API de gouvernance empruntent le **chemin réel** d'authentification : clé présentée, résolution de l'utilisateur, contrôle du rôle, contrôle du consentement. Seul l'accès à la base de données est simulé ; le contrôle d'accès n'est jamais court-circuité.

Tableau: Cas de contrôle d'accès vérifiés.
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

Tableau: Évaluation sur vérité terrain (08/09/2026).
| Niveau | Maîtres prédits | VP | FP | FN | Précision | Rappel | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Facile (10 %) | 500 | 727 | 0 | 0 | **1,000** | 1,000 | 1,000 |
| Moyen (30 %) | 554 | 643 | 0 | 84 | **1,000** | 0,884 | 0,939 |
| Difficile (50 %) | 804 | 307 | 0 | 420 | **1,000** | 0,422 | 0,594 |

Capture: C16 | Évaluation sur le jeu difficile. | C16_evaluation.png | Terminal : sortie de evaluate_engine.py sur le jeu hard (précision, rappel, F1, VP/FP/FN).

L'algorithme **ne fusionne aucune paire à tort** sur les trois niveaux, propriété essentielle en santé, où fusionner deux personnes est plus grave que de les laisser séparées. Sur le jeu difficile, il ne reconnaît pas toutes les variantes (rappel de 0,422). L'introduction du CIN dans la clé exacte a relevé ce rappel de 0,287 à 0,422 sans créer de faux positif. Le pipeline complet, mesuré sur la même vérité terrain, obtient les mêmes résultats : précision de 1,000, rappel de 0,424.

La décomposition par méthode localise la faiblesse : sur le jeu difficile, le rapprochement exact atteint un rappel de 0,854 et le rapprochement probabiliste de 0,533, avec une précision de 1,000 dans les deux cas. Le rappel est homogène entre les sources (0,422 ; 0,422 ; 0,423) : la dégradation vient du taux de variation, et non d'une source particulière. Enfin, les implémentations Pandas et Spark produisent exactement les mêmes résultats : 307 vrais positifs, 0 faux positif, 420 faux négatifs et 804 patients maîtres prédits pour 500 groupes réels.

Une précision mérite d'être faite sur l'absence de faux positif : le générateur dégrade des enregistrements existants mais ne construit jamais deux personnes distinctes presque identiques. La précision de 1,000 vaut donc pour les erreurs simulées : face à des homonymes réels, c'est une estimation **optimiste**, et non une garantie ; la confirmer demanderait un jeu d'homonymes proches.

## Limites identifiées

Le prototype présente des limites identifiées et documentées :

- **Rappel de 0,422 sur le jeu difficile** : 420 paires manquées, en raison d'un seuil volontairement conservateur ; l'abaisser ou enrichir la clé suppose une validation métier.
- **Consentement par type de dossier** : en cours de développement ; le contrôle actuel porte sur la finalité.
- **Base centrale de test** : alimentée par le pipeline et par des consentements de démonstration, pas par des avis réellement recueillis.
- **Environnement de démonstration** : une VM de 8 Go et 4 cœurs sur un poste de 16 Go, Spark en mode local (un seul processus de 2 Go) ; 212 523 fiches traitées au plus, en 7 min 03 s, avec des gels de la VM quand l'hôte manque de mémoire.
- **Déduplication centralisée** : toutes les fiches sont rapatriées sur une machine et comparées en Python, sur toutes les fiches à chaque run (332 s pour 212 523 fiches, contre 13 s pour 25 587). Des millions de lignes demanderaient une déduplication incrémentale et un blocage réparti, pas seulement plus de puissance.
- **Identifiants de patients maîtres non permanents** : ils sont numérotés dans l'ordre de traitement à chaque run ; une fiche nouvelle ou d'autres données décalent les numéros, et un consentement enregistré pour un numéro peut alors désigner une autre personne.
- **Homonymes parfaits** : à 100 000 patients, deux personnes de même nom et de même date de naissance sont fusionnées à tort (précision de 0,9999), car le nom et la date atteignent seuls le seuil. Un veto sur deux CIN différents en évite une, sans perte de rappel en simulation ; l'autre demande une validation humaine.
- **API des indicateurs non sécurisée** : elle ne sert que du reporting ; le contrôle d'accès est appliqué et testé sur l'API de gouvernance.
- **Clés d'API hachées sans sel** : l'empreinte protège la lecture directe de la table, mais un hachage salé ou lent (bcrypt) serait préférable.
- **Pas d'intégration continue ni de tests en environnement déployé**, et planification par cron non activée sur la VM.

#! Conclusion générale

Ce stage avait pour objet de concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités et la gouvernance des accès par le consentement du patient. Le tableau suivant reprend chaque volet de cette problématique avec la réponse apportée et sa preuve.

Tableau: Réponse à la problématique.
| Volet | Réponse réalisée | Preuve |
|---|---|---|
| Intégrer | extraction abstraite vers la zone RAW (Parquet sur HDFS, tables Hive) | 3 sources de test (CSV synthétiques) ; extraction PostgreSQL et SQLite implémentée |
| Nettoyer et normaliser | modèle canonique et schéma pivot FHIR | 1 057 lignes SILVER, dates et noms complets |
| Dédupliquer de façon explicable | blocking, passe exacte, passe probabiliste ; méthode, score et explication pour chaque décision | 803 patients maîtres, 254 doublons ; précision de 1,000 pour le moteur et pour le pipeline |
| Centraliser avec traçabilité | zones RAW, SILVER, GOLD ; origine conservée ; reprise, incrémental et historique des runs | 1 057 − 254 = 803 vérifié sur le lac |
| Gouverner par consentement | rôles, clés hachées, finalité obligatoire, refus 403 journalisé | 123 tests ; 401, 403 et 422 vérifiés aussi sur base peuplée |
| Ne jamais fusionner sans logique | méthode obligatoire pour tout patient maître | précision de 1,000 sur les trois niveaux |

Le projet démontre quatre résultats. **La démarche progressive tient** : le même moteur, écrit en Pandas puis porté en PySpark et intégré au lac, conserve exactement la même sémantique, jusque dans le pipeline complet mesuré sur la vérité terrain. **La prudence a un coût, mesuré** : le seuil est positionné pour ne jamais fusionner à tort, et le rappel limité sur le jeu difficile est expliqué plutôt que masqué. **La gouvernance est dans le système** : un refus pour finalité non consentie est décidé, opposé et journalisé, et cela est vérifié par des tests qui empruntent le vrai chemin d'authentification. **Le contexte dicte les choix** : VM de 8 Go, Python 3.8 et nœud distant instable ont chacun conduit à une décision documentée.

Les difficultés rencontrées ont été techniques (onze incidents corrigés, dont quatre découverts en rejouant le pipeline sur la VM le 30/09), d'environnement (nœud distant instable, VM longtemps indisponible en fin de stage), d'organisation (développement mené seul, algorithme écrit deux fois) et de méthode. La plus instructive a été de définir ce que l'on accepte de perdre — des doublons non retrouvés — au regard de ce que l'on refuse de risquer — la fusion de deux patients — et de pouvoir le démontrer par des chiffres reproductibles.

Sur le plan personnel, ce stage m'a permis de pratiquer le Big Data, domaine dans lequel mon expérience était limitée : installer et faire fonctionner une chaîne HDFS, Hive et Spark, et découvrir ce que la documentation ne dit pas, comme l'ordre de démarrage des services ou le coût de Spark sur de petits volumes. Il m'a appris à relier le modèle statistique du rapprochement d'identités, l'architecture qui le rend exploitable et la règle de gouvernance qui décide qui peut le lire. Il m'a enfin appris une discipline : ne rien affirmer sans preuve reproductible, et écrire une limite plutôt que de la taire.

Plusieurs perspectives prolongent ce travail. À court terme : terminer le consentement par type de dossier, rendre permanents les identifiants de patients maîtres, déployer la base centrale et y enregistrer des consentements réellement recueillis, calibrer le seuil et les poids sur la vérité terrain, ajouter un veto sur deux CIN différents, et activer la planification sur la VM. À moyen terme : ajouter une intégration continue, passer à l'échelle par une déduplication incrémentale (seules les fiches nouvelles comparées aux patients maîtres en base), l'extraction des seules lignes nouvelles et un blocage réparti entre plusieurs nœuds Spark, et reprendre la source MAVIS réelle lorsque le nœud sera stable. À plus long terme : brancher la gouvernance sur un catalogue de métadonnées pour le lignage des données, et généraliser le moteur à d'autres entités, comme les médecins ou les médicaments.

#! Références et bibliographie

Les ressources en ligne sont citées avec leur date de consultation : leur contenu a pu évoluer depuis. Les documentations logicielles sont rapportées à la version employée dans le projet lorsqu'elle est connue. Les articles et ouvrages publiés sont identifiés par leur DOI, qui reste stable.

**Rapprochement d'identités**

[1] ELMAGARMID, A. K. ; IPEIROTIS, P. G. ; VERYKIOS, V. S. *Duplicate Record Detection: A Survey*. IEEE Transactions on Knowledge and Data Engineering, vol. 19, n° 1, 2007, p. 1-16. En ligne : https://www.cs.purdue.edu/homes/ake/pub/survey2.pdf (consulté le 8 septembre 2026).

[2] FELLEGI, I. P. ; SUNTER, A. B. *A Theory for Record Linkage*. Journal of the American Statistical Association, vol. 64, n° 328, 1969, p. 1183-1210. DOI : 10.2307/2286061.

[3] CHRISTEN, P. *Data Matching: Concepts and Techniques for Record Linkage, Entity Resolution, and Duplicate Detection*. Springer, coll. Data-Centric Systems and Applications, 2012. DOI : 10.1007/978-3-642-31164-2.

[4] RapidFuzz, documentation et code source, version 3.14.5. En ligne : https://rapidfuzz.github.io/RapidFuzz/ (consulté le 8 septembre 2026).

**Standards de santé**

[5] HL7. *FHIR — Resource Patient*, version 5.0.0 (R5), dont l'opération `$match` (§ 8.1.11). En ligne : https://www.hl7.org/fhir/patient.html (consulté le 8 septembre 2026).

**Architecture Big Data**

[6] Apache Software Foundation. *HDFS Architecture* (documentation Hadoop). En ligne : https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-hdfs/HdfsDesign.html (consulté le 8 septembre 2026).

[7] Apache Software Foundation. *Apache Spark — Unified engine for large-scale data analytics*. En ligne : https://spark.apache.org (consulté le 8 septembre 2026).

[8] Apache Software Foundation. *Apache Hive*. En ligne : https://hive.apache.org (consulté le 8 septembre 2026).

[9] Databricks. *What is the medallion lakehouse architecture?* En ligne : https://docs.databricks.com/aws/en/lakehouse/medallion (consulté le 8 septembre 2026).

**Réglementation**

[10] Règlement (UE) 2016/679 du Parlement européen et du Conseil du 27 avril 2016 (règlement général sur la protection des données), article 9. Journal officiel de l'Union européenne, L 119, 4 mai 2016.

[11] CNIL. *Quelles formalités pour les traitements de données de santé ?* En ligne : https://www.cnil.fr/fr/quelles-formalites-pour-les-traitements-de-donnees-de-sante (consulté le 8 septembre 2026).

[12] CNIL. *RGPD et professionnels de santé libéraux : ce que vous devez savoir*. En ligne : https://www.cnil.fr/fr/rgpd-et-professionnels-de-sante-liberaux-ce-que-vous-devez-savoir (consulté le 8 septembre 2026).

**Solutions existantes** (étude documentaire : aucun produit n'a été installé)

[13] InterSystems. *InterSystems EMPI* et documentation *InterSystems IRIS for Health*. En ligne : https://www.intersystems.com/products/intersystems-empi/ et https://docs.intersystems.com/irisforhealthlatest/ (consulté le 27 septembre 2026).

[14] Qlik. *Integrated matching in Talend MDM* (version 8.0). En ligne : https://help.qlik.com/talend/en-US/mdm-examples/8.0/integrated-matching-in-talend-mdm (consulté le 27 septembre 2026).

[15] LINACRE, R. ; LINDSAY, S. ; MANASSIS, T. ; SLADE, Z. ; HEPWORTH, T. ; KENNEDY, R. ; BOND, A. *Splink: Free software for probabilistic record linkage at scale*. International Journal of Population Data Science, vol. 7, n° 3, 2022. DOI : 10.23889/ijpds.v7i3.1794. Documentation : https://moj-analytical-services.github.io/splink (consulté le 27 septembre 2026).

[16] HAPI FHIR, implémentation open source de la spécification FHIR. En ligne : https://hapifhir.io (consulté le 27 septembre 2026).

[17] Microsoft. *Azure Health Data Services* : export de données FHIR et service de dé-identification. En ligne : https://learn.microsoft.com/en-us/azure/healthcare-apis/fhir/export-data et https://learn.microsoft.com/en-us/azure/healthcare-apis/deidentification/overview (consulté le 27 septembre 2026).

[18] Apache Software Foundation. *Apache Atlas — Data Governance and Metadata framework for Hadoop*. En ligne : https://atlas.apache.org (consulté le 27 septembre 2026).

[19] GNU Health, système libre d'information de santé. En ligne : https://www.gnuhealth.org et https://docs.gnuhealth.org (consulté le 27 septembre 2026).

[20] Odoo, progiciel de gestion intégré, et module de gestion hospitalière. En ligne : https://www.odoo.com et https://apps.odoo.com/apps/modules/19.0/base_hospital_management (consulté le 27 septembre 2026).

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

Le générateur est décrit à la section 5.1.5 : 500 patients maîtres, répartition entre les trois sources, variations à trois niveaux et table de vérité. Sur le jeu difficile, les transactions associées comptent 792 achats en pharmacie, 519 consultations et 450 examens d'imagerie. Le jeu complet se régénère en une commande, avec la même graine, ce qui rend l'évaluation reproductible.

##! Annexe C — Exemple de décision de déduplication

Pour le cas de référence de démonstration (18 fiches), le moteur produit 11 patients maîtres et 18 liens d'identité, à l'identique en Pandas et en Spark. Jean Rakoto est rattaché par **rapprochement exact** grâce à son CIN, présent sous deux formats différents mais identique après normalisation. Une autre patiente, Nirina, est rattachée par **rapprochement probabiliste** avec un score supérieur à 0,80, son nom présentant une variation. Chaque lien conserve sa méthode, son score et une explication lisible par un gestionnaire de données.

##! Annexe D — Extraits de code complémentaires

La fonction de déduplication enchaîne les deux passes décrites à la section 7.2.3 : rapprochement exact, puis meilleur candidat probabiliste au-dessus du seuil, sinon création d'un nouveau patient maître. Chaque branche produit une décision avec sa méthode, son score et son explication.

Code: X06 | Boucle de déduplication en deux passes | engine/identity/matcher.py::deduplicate | X06_deduplicate.png

Le journal d'audit est un *middleware* : il s'exécute après chaque requête, quelle qu'en soit l'issue, et enregistre la finalité et le motif d'un éventuel refus.

Code: X07 | Journalisation de chaque accès | engine/governance/audit.py::AuditMiddleware | X07_audit.png

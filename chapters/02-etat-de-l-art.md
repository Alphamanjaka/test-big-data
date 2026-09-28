# Chapitre 2 — État de l'art

## Objectif

Établir les notions de référence du sujet — Entity Resolution et Record Linkage, mesures de
similarité, blocking, Master Patient Index (MPI) et interopérabilité FHIR, cadre juridique du
consentement, architectures Big Data et Data Lake Medallion — puis en déduire des **critères de
comparaison**, étudier les **solutions existantes** au regard de ces critères, les comparer dans
un tableau de synthèse et situer la **pertinence** du projet. Chaque concept est relié au rôle
qu'il joue dans le projet, conformément au document conceptuel
[`bigdata_concepts.md`](../documents/documentation/bigdata_concepts.md).

> **Portée de l'étude.** Aucun des produits comparés n'a été déployé sur la VM ni mesuré : la
> comparaison s'appuie sur leur **documentation**. Les capacités citées sont donc des
> **capacités annoncées**, jamais des résultats obtenus [AGENTS.md — règle d'honnêteté des
> livrables].

---

## 2.1 Notions de référence et critères de comparaison

Les critères de comparaison ne se choisissent pas au hasard : ils découlent des notions du
domaine. Cette section présente la méthode de veille, puis les sept notions de référence, et
en déduit les six critères appliqués aux solutions existantes.

### 2.1.1 Méthode de la veille

**Protocole de recherche.** L'état de l'art n'est pas constitué par juxtaposition de
liens : les sous-sections 2.1.2 à 2.1.8 correspondent à des **questions formulées à l'avance**,
dérivées du cahier des charges, auxquelles on a cherché une réponse sourcée.

**Tableau 4 — Les sept questions de veille formulées à l'avance, le paragraphe qui y répond et les sources retenues.**

| Question de veille | Où c'est traité | Sources retenues |
|---|---|---|
| Quelle théorie fonde l'appariement d'enregistrements ? | §2.1.2 | [B1], [B2], [B3] |
| quelles similarités, et lesquelles sont utilisables sous Python 3.8 ? | §2.1.3 | [B3], [B4] |
| Comment éviter la comparaison quadratique ? | §2.1.4 | [B1], [B3] |
| Quel standard de santé pour l'identité et l'échange ? | §2.1.5 | [B5] |
| Quelle base légale pour des données de santé ? | §2.1.6 | [B10], [B11], [B12] |
| Quelles briques Big Data, et pour quel usage ? | §2.1.7, §2.1.8 | [B6] à [B9] |
| Que fait déjà le marché et l'open source ? | §2.2 à §2.4 | [B13] à [B20] |

**Règles de sélection retenues** : (1) une source **technique normative ou
documentaire primaire** (publication, spécification, documentation officielle)
privilégiée sur toute source secondaire ; (2) une source **récente** ou
**fondatrice** selon l'axe — les fondations datent de 1969 [B2] et restent la
référence, la documentation technique est suivie à la version utilisée (FHIR
v5.0.0 [B5], RapidFuzz 3.14.5 [B4]) ; (3) une source **exploitable** : chaque
référence doit pouvoir être rattachée à une décision de conception ou à un
risque identifié ; (4) les solutions propriétaires sont citées pour leurs
**capacités annoncées** et signalées comme non expérimentées [B13] à [B17].

**Période couverte** : les travaux fondateurs (1969) à la version de la
documentation consultée en septembre 2026. Il ne s'agit pas d'une revue
systématique exhaustive, mais d'une revue **ciblée sur les décisions du projet** :
aucune source n'a été retenue « parce qu'elle est récente », mais « parce qu'elle
permet de justifier un choix ».

**Couverture du plan d'État de l'art.** Le plan comporte 20 axes répartis en cinq
blocs (existant, concepts, choix, soutenance, méthodologie) ; le mémoire en
traite directement 11, en traite partiellement 7, laisse 1 axe hors périmètre
(les personas : le commanditaire est le public cible, pas l'utilisateur final) et
1 axe optionnel non traité (sobriété).

**Tableau 5 — Couverture du plan imposé : traitement de chacun des cinq blocs d'axes, et mention explicite de ce qui reste hors périmètre.**

| Bloc | Axes | Traitement dans le mémoire |
|---|---|---|
| **1 — Existant** (0-4) | veille · règlementaire · solutions du marché · internes · personas | **0 traité** (§2.1.1) · **1-3 traités** (chapitres 2, 3) · **4 absent** (hors périmètre : le commanditaire est le public cible, pas l'utilisateur final) |
| **2 — Concepts** (5-9) | architecture · technologies · matrice de choix · données & flux · algorithmes | **5 traité** (§6.1) · **6 traité** (§7.1) · **7-8 partiels** (volumétrie et/providers non traités) · **9 traité** (FHIR, §2.1.5) |
| **3 — Choix** (10-15) | sécurité · performance · déploiement · coûts · contexte local · pilotage | **10 traité** (§2.1.6, §7.2.3) · **11-13 partiels** · **14 traité** (§4.2) · **15 traité** (§4.3) |
| **4 — Soutenance** (16-19) | coût-bénéfice · protection des données · sobriété · synthèse des décisions | **16-17 partiels** (RGPD traité, coût total estimé sur hypothèses, § 4.4) · **18 optionnel absent** (hors périmètre) · **19 traité** (conclusion générale) |
| **5 — Méthodologie** | — | ce §2.1.1 |

### 2.1.2 Entity Resolution et Record Linkage

Le problème central du projet — déterminer si des enregistrements issus de sources
différentes désignent la même personne — porte un nom générique : **Entity Resolution**
(ER), également appelé *record linkage*, *data matching*, *duplicate detection* ou
*fusion de doublons* selon les communautés [B1], [B3].

Les fondements théoriques datent de 1969 : **Fellegi et Sunter** formalisent la
décision d'appariement de deux enregistrements en comparant leurs champs et en
concluant à un match, un non-match ou un match indéterminé
(« possible match ») [B2]. Ce modèle probabiliste est encore la référence des
systèmes d'ER modernes [B1].

Le processus générique, décrit par Elmagarmid et al. [B1] et détaillé par Christen
[B3], se décompose en cinq étapes, chacune appliquée dans le projet : le
**prétraitement** nettoie et standardise les champs (`CanonicalPatient` : casse, accents,
CIN, villes, dates) ; l'**indexation** (*blocking*) réduit les comparaisons en groupes de
candidats (préfixe du nom, date de naissance, CIN) ; la **comparaison** mesure la
similarité champ à champ (RapidFuzz, score pondéré) ; la **classification** décide match
ou non-match (seuil 0.80, passe exacte puis passe probabiliste) ; l'**évaluation** mesure
la qualité sur une vérité terrain (ground truth P/R/F1) [deduplication.md §3-§5].

Le résultat attendu de l'ER est une **réconciliation d'identités** : un patient
présent sous plusieurs formes dans plusieurs systèmes doit être reconnu comme une
seule entité physique, sans fusion erronée de personnes distinctes — c'est
l'équilibre **précision vs rappel** propre au domaine.

> **Point de vocabulaire.** Entity Resolution = déterminer si deux enregistrements
> désignent la même entité [B1] ; le résultat produit un **golden record** (fiche
> consolidée) et une **identity map** (table de correspondance traçable).

### 2.1.3 Mesures de similarité

Deux chaînes qui désignent la même personne diffèrent rarement d'un seul caractère :
les variantes *Jean Rakoto* / *Rakoto Jean* / *J. RAKOTO* imposent de comparer des
chaînes de caractères, pas seulement des égalités.

Les mesures classiques du domaine [B1], [B3] :

**Tableau 6 — Les mesures de similarité classiques du domaine et leur usage dans le rapprochement d'identités.**

| Mesure | Principe | Usage typique |
|---|---|---|
| **Levenshtein** | distance d'édition : nombre minimal d'insertions / suppressions / substitutions | nom, prénom |
| **OSA (optimal string alignment)** | Levenshtein + transposition de deux caractères adjacents (souvent qualifié de « Damerau » en pratique) | fautes de frappe |
| **Jaro–Winkler** | similarité orientée début de chaînes (préfixe commun pondéré) | initiales, noms tronqués |
| **Token-based** (`fuzz.ratio`, `token_sort_ratio`) | comparaison des séquences de mots, indépendante de l'ordre | *Rakoto Jean* vs *Jean Rakoto* |

Le projet utilise **RapidFuzz**, bibliothèque Python/C++ MIT qui implémente ces
mesures avec un processeur rapide et un fallback pur Python [B4]. Son intérêt
décisif est **opérationnel** : léger, compatible Python 3.8 (indispensable sur la
VM), sans dépendance NLP lourde — le recours à `sentence_transformers` a été
explicitement **interdit** (crash sous Python 3.8) [bigdata_concepts.md §8].

Le score combine quatre champs **pondérés** et **configurables** : le nom pèse 0.50, la
date de naissance 0.30, le CIN 0.10 et la ville de naissance 0.10. Le détail de ces
pondérations et leur justification figurent au § 7.1 [deduplication.md §5].

Décision : **score ≥ 0.80 → fusion automatique**, sinon pas de fusion (aucune
logique arbitraire). Les deux valeurs — pondérations et seuil — sont calibrées sur
le cas de référence « Jean Rakoto » et vérifiées par évaluation ; sur le jeu de
difficulté « hard », la similarité seule plafonne le rappel autour de **0.422**
(F1 0.594, précision 1.000) — voir chapitre 8 [evaluation_truth.md].

### 2.1.4 Blocking et complexité

Comparer chaque enregistrement à tous les autres est **quadratique** : pour n
patients, n² comparaisons. La pratique standard du domaine, le **blocking** (ou
indexation), regroupe les enregistrements en blocs de candidats partageant une clé
grossière (préfixe de nom, date de naissance, CIN) ; le matching
n'est exécuté que **dans chaque bloc** [B1], [B3].

Dans le projet, la clé de matching est `(nom normalisé, birth_date, cin)`
[deduplication.md §2] et le moteur exploite deux index bornés :
`_MasterIndex` (version Pandas) et `_BoundedMasterIndex` (version Spark)
[deduplication.md §8]. Cette limite de comparaison est un point clé de passage à
l'échelle : sans elle, un volume de l'ordre du million de patients imposerait
10¹² comparaisons.

### 2.1.5 Master Patient Index et interopérabilité FHIR

En santé, l'ER aboutit à un référentiel d'identités : le **Master Patient Index
(MPI)** — chaque patient des bases sources est rattaché à un identifiant synthétique
unique, le *master patient*, via une **identity map** traçable
[deduplication.md §6] :

**Tableau 7 — Exemple d'identity map : trois enregistrements de sources différentes rattachés à un même master patient, chacun avec sa méthode et son score.**

| Source | ID source | Master ID | Score | Méthode |
|---|---|---|---|---|
| pharmacy | 15 | 102 | 1.000 | exact |
| consultation | 88 | 102 | 0.950 | probabilistic |
| imaging | IMG-20 | 102 | 0.920 | probabilistic |

La démarche rejoint la norme d'interopérabilité **FHIR** (HL7 Fast Healthcare
Interoperability Resources), qui prescrit au §8.1.11 un service dédié : le
`$match` retourne, à partir d'une liste de champs patients, la liste des
correspondances candidates selon un score de similarité explicite [B5]. Le projet
s'aligne sur cette philosophie — *search + match par score* — tout en l'implémentant
localement.

Côté format, FHIR sert de **schéma pivot** : 4 entités (`Patient`, `Encounter`,
`Condition`, `Observation`) harmonisent des sources structurées différemment
[bigdata_concepts.md §8]. Le mapping automatique des colonnes vers FHIR combine
correspondance exacte, dictionnaire de synonymes et *fuzzy matching* (seuil 60 %) —
toujours sans modèle NLP lourd.

### 2.1.6 Consentement et RGPD sur les données de santé

Les données de santé sont une **catégorie particulière** de données à caractère
personnel : leur traitement est **en principe interdit** par l'article 9 du RGPD,
sauf dérogation dont le **consentement explicite** (art. 9.2.a) [B10]. En droit
français, la loi Informatique et Libertés reprend ce principe (art. 6) et ses
exceptions (art. 44) [B11]. La CNIL rappelle en outre deux distinctions :
article 6 (base légale) et article 9 (dérogation données sensibles) se cumulent ;
le consentement au **traitement** diffère du consentement aux soins [B11], [B12].

Le projet incarne ces principes dans le système, et non à côté
[`consentement_gouvernance.md` §2–§5] :

**Tableau 8 — Traduction des exigences du RGPD en mécanismes implémentés, avec le fichier qui en constitue la preuve.**

| Exigence RGPD | Mécanisme implémenté | Preuve |
|---|---|---|
| **Traçabilité des accès** (art. 30) | RBAC : rôles `admin` / `analyst` / `viewer`, contrôlés par clé API résolue en `api_user` | `engine/governance/auth.py` |
| **Finalité déterminée** (art. 5.1.b) | la finalité est **déclarée par l'appelant** et **obligatoire** : `purpose` en paramètre de requête de `/patients` et `/patients/{id}` ; alphabet fermé `api_access`, `research`, `analytics` | `engine/governance/consent.py::PURPOSES`, `validate_purpose` |
| **Consentement explicite** (art. 9.2.a) | table `consent(master_patient_id, purpose, granted, recorded_at)` ; **refus par défaut** (absence de ligne = refus) et « le dernier avis gagne » | `sql/schema.sql`, `check_consent()` |
| **Refus effectif** | un utilisateur **autorisé** dont la finalité n'est pas consentie reçoit **403**, y compris sur la liste (les patients non consentis en sont retirés) | `enforce_consent()`, `consented_master_ids()` |
| **Journalisation** (art. 30/33) | chaque appel est journalisé dans `access_audit`, **finalité et motif de refus compris** : un refus est consultable, pas seulement déduit du code HTTP | `engine/governance/audit.py`, colonnes `purpose` / `refusal_reason` |
| **Minimisation** (art. 5.1.c) | clés API **hachées SHA-256** en base, jamais en clair | `_hash_api_key()` |

Deux limites sont assumées et non masquées : le modèle ne gère **ni périmètre de
données** (`data_scope`) **ni durée de validité** du consentement — la validité est
portée par `recorded_at` et par la possibilité d'enregistrer un nouvel avis ; et
les accès sont journalisés mais **non chiffrés** au repos dans `access_audit`.

Toutes les données manipulées sont **synthétiques** : la conformité est un actif de
conception (exigence du cahier des charges), pas un obstacle de démonstration.

### 2.1.7 Big Data : HDFS, MapReduce, Spark, Hive

**HDFS** (Hadoop Distributed File System) est le socle de stockage distribué : une
architecture NameNode (métadonnées) + DataNodes (blocs), avec **réplication**
défaut et **data locality** au profit des traitements [B6]. Dans le projet, le Data
Lake repose sur HDFS : parquet RAW/SILVER/GOLD sous `/datalake/*`, tables Hive
externes par-dessus [bigdata_concepts.md §4].

Le premier modèle de calcul distribué, **MapReduce**, a été supplanté en pratique
par **Apache Spark**, qui garde les données **en mémoire** entre les étapes et
généralise le modèle (RDD/DataFrame) — largement utilisé via son API Python
**PySpark** [B7]. **Hive** apporte la couche SQL sur le Data Lake : son
**metastore**, le catalogue qui décrit les tables et leurs colonnes
(thrift://localhost:9083), et HiveServer2/beeline, le service qui reçoit et exécute
les requêtes SQL (port 10000) [B8].

Chaque brique a un rôle et un fait vérifiable : **HDFS** est l'entrepôt du Data Lake en
parquet (`spark.sql.warehouse.dir = hdfs://localhost:9000`) ; **Spark (PySpark)** assure
le mapping FHIR, la normalisation, la déduplication et la production GOLD, avec une
configuration VM 8 Go à 4g/2g et 8 partitions ; **Hive** porte les tables externes
SILVER/GOLD et les analyses SQL, par exemple `datalake_gold.patient_events_gold`
[bigdata_concepts.md §4-§6].

Constat mesuré du projet : sur petits volumes (~6 à 36 lignes), Pandas est ~1–2 ms
contre ~0.4–4 s pour Spark — l'overhead JVM domine. Spark se justifie sur le
**volume** ; le projet le conserve aussi pour la **démonstration de parité**
(résultats strictement identiques au pipeline Pandas) [bigdata_concepts.md §2].

### 2.1.8 Data Lake Medallion et ELT

Le **modèle Medallion** (Databricks) organise le lac en **zones de qualité
croissante** : RAW (brut, inchangé) → SILVER (nettoyé, standardisé, doublons
identifiés) → GOLD (agrégé, prêt à l'analyse) [B9].

Concrètement, la zone **RAW** reçoit la donnée brute en parquet sous
`/datalake/raw/{source}/{table}` et sous forme de tables externes ; la zone **SILVER**
porte la donnée nettoyée, **normalisée FHIR**, avec les doublons marqués
(`datalake_silver.*_fhir`, 4 tables) ; la zone **GOLD** contient les agrégats prêts à
l'analyse (`datalake_gold.patient_events_gold`, 18 colonnes, 8 tranches d'âge).

Chaque zone est un **état distinct de la donnée**, ce qui apporte trois choses : la
**traçabilité** (on sait d'où vient chaque valeur), le **rejeu** (relancer un
traitement depuis une zone propre, sans tout recommencer) et la séparation exigée
par la gouvernance [bigdata_concepts.md §3].

Le pipeline suit la logique **ELT** (extract → load → transform) : l'ingestion
charge la donnée **telle quelle** dans RAW, la transformation s'applique *a
posteriori* dans les zones suivantes — c'est le **schéma-on-read** (« on décide
du format au moment de lire »), caractéristique du Data Lake
[bigdata_concepts.md §7].

### 2.1.9 Critères de comparaison retenus

Six critères sont déduits de ces notions, du problème posé au § 1.2.1 (disperser,
dédupliquer, gouverner) et des contraintes du stage (§ 4.2). Ils sont appliqués à chaque
solution au § 2.2, puis réunis dans le tableau comparatif du § 2.3 :

1. **Déduplication explicable** — chaque fusion porte un score, une méthode et une
   justification (§ 2.1.2 à 2.1.4).
2. **Interopérabilité FHIR** — la solution sait lire ou produire le format pivot de santé
   (§ 2.1.5).
3. **Gouvernance rôle + consentement + audit** — l'accès est contrôlé par le rôle, la
   finalité consentie et une trace (§ 2.1.6).
4. **Montée en charge Big Data** — la solution s'appuie sur un stockage et un calcul
   répartis (§ 2.1.7, 2.1.8).
5. **Hébergement interne** (*on-premise*) — les données restent sur les machines de
   l'établissement, contrainte du commanditaire.
6. **Faisabilité VM 8 Go / Python 3.8** — la solution fonctionne dans l'environnement réel
   du stage (§ 4.2).

## 2.2 Étude des solutions existantes

Quatre familles de produits couvrent, partiellement, le besoin. Trois sigles reviennent
souvent : le **MPI** (Master Patient Index, un annuaire de patients qui attribue un identifiant
unique à chaque personne), le **DMP** (Data Management Platform, une plateforme qui pilote la
qualité des données d'un établissement) et le **MDM** (Master Data Management, la même
approche appliquée aux données de référence, patients ou non). Pour chacune, ce qu'elle apporte
et ce qui bloque son adoption dans le contexte du stage :

**Tableau 9 — Les six solutions du domaine : ce qu'elles apportent au besoin et ce qui bloque leur adoption ici.**

| Solution | Famille | Apport pour le besoin | Ce qui bloque l'adoption ici |
|---|---|---|---|
| **InterSystems EMPI** [B13] | MPI / DMP santé | Moteur d'identité déterministe **et** probabiliste, rapprochement de référence (LexisNexis LexID), création d'un enregistrement composite par personne, services IHE **PIX** (MRN → MPI ID) et **PDQ** (démographiques partiels → MPI IDs) | Produit **propriétaire et sous licence**, conçu pour des systèmes de santé nord-américains ; son atout est un **référentiel externe** de population, incompatible avec l'exigence d'hébergement interne ; ne couvre ni le Data Lake Medallion ni la gouvernance par consentement |
| **Talend MDM** [B14] | MDM / ETL commercial | *Integrated Matching* : *match and survivorship*, **golden record**, tâches de fusion revues par des gestionnaires de données (« data stewards »), seuils de confiance paramétrables | Suite commerciale lourde ; la **survivorship** suppose une autorité de gestion des données et un poste de travail à valider ; pas d'interopérabilité **FHIR** native ; ne résout pas la gouvernance d'accès aux données patients |
| **Azure Health Data Services** [B17] | Plateforme Data / cloud santé | Service **FHIR** et **DICOM** managés, export massif `$export` vers Data Lake Storage Gen2, service de **dé-identification** (27 entités, opérations `TAG` / `REDACT` / `SURROGATE`) | Service **cloud managé** : incompatible avec la contrainte d'**hébergement interne** et avec le réseau de l'établissement ; ne fournit **ni MPI ni déduplication** |
| **HAPI FHIR** [B16] | Open source (Java, Apache 2.0) | Implémentation de référence du serveur FHIR : validation, stockage, opérations REST, recherche, `$match` | Fournit l'**interopérabilité** mais **ni rapprochement d'identité, ni gouvernance, ni zones de qualité** : à lui seul il ne résout aucun des trois problèmes du § 1.2.1 |
| **Splink** [B15] | Open source (Python, MoJ) | Lien probabiliste d'enregistrements à l'échelle : modèle **Fellegi-Sunter**, estimation par **EM**, backends Spark/SQL, ~1 million d'enregistrements en une minute | Excellent sur le **cœur** algorithmique, mais la calibration EM produit des poids **non lisibles** par un data steward ; ni gouvernance, ni Medallion, ni audit d'accès. Le projet a préféré un **score pondéré explicable** (§ 7.2.3) |
| **Apache Atlas** [B18] | Open source (gouvernance Hadoop) | Catalogue, **lineage** de bout en bout, classifications type `PII` / `SENSITIVE` propagées le long des traitements | Gouvernance de **métadonnées**, pas contrôle d'accès : n'exerce aucun filtrage au runtime, n'implémente ni consentement par finalité ni journal d'accès |

## 2.3 Tableau comparatif et synthèse

Les six critères du § 2.1.9 sont appliqués à chaque solution. `✔` = capacité annoncée par la
documentation, `◐` = partielle, `✖` = absente. **Aucune mesure : lecture documentaire.**

**Tableau 10 — Grille de comparaison des six solutions et de la solution du stage sur les six critères retenus (lecture documentaire, aucune mesure).**

| Critère | InterSystems EMPI | Talend MDM | Azure HDS | HAPI FHIR | Splink | Apache Atlas | Solution du stage |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Déduplication **explicable** (score + méthode + justification) | ✔ | ✔ | ✖ | ✖ | ◐ | ✖ | **✔ testé** |
| Interopérabilité **FHIR** | ◐ | ✖ | ✔ | ✔ | ✖ | ✖ | **✔ testé** |
| Gouvernance **rôle + consentement + audit** | ◐ | ◐ | ✔ | ✖ | ✖ | ◐ | **✔ conçu** |
| Montée en charge **Big Data** (HDFS/Spark) | ◐ | ✔ | ✔ | ✖ | ✔ | ✔ | **✔ testé** |
| **Hébergement interne** (on-premise) | ✔ | ✔ | ✖ | ✔ | ✔ | ✔ | **✔ testé** |
| Faisabilité **VM 8 Go / Python 3.8** | ✖ | ✖ | ✖ | ✖ | ◐ | ✖ | **✔ testé** |

Lecture : **aucun produit ne coche les six cases**. Les solutions les plus complètes sur l'identité
(EMPI, Talend) sont les plus lourdes et les plus coûteuses ; les solutions conformes à
l'hébergement interne ne résolvent ni le rapprochement, ni la gouvernance, ni l'explicabilité. Le
cahier des charges fixe en outre un délai de **4 mois** et un environnement **entièrement
interne** [cahier_des_charges_stage_M2_MBDS.docx §1 et §3].

Deux précautions de lecture. D'abord, la colonne du projet n'est **pas soumise au même régime de
preuve** que les six autres : les produits sont jugés sur des capacités *annoncées*, alors que la
solution du stage est notée `✔ testé` lorsqu'une mesure existe et `✔ conçu` lorsqu'elle n'existe
pas encore — c'est le cas de la ligne gouvernance, mécaniquement vérifiée par la suite de tests
(§ 8.4) mais dont les données PostgreSQL n'étaient pas peuplées au run (chapitre 8). Ensuite, un
`◐` signifie « partiel selon la documentation » : il signale une capacité réelle mais non
complète dans le contexte du stage, et non un doute sur l'existence de la fonction — la nuance
est celle de Splink sur l'explicabilité, excellent sur le cœur algorithmique mais dont les poids
estimés par EM ne sont pas lisibles par un data steward.

## 2.4 Pertinence entre le projet et l'état de l'art

**Décision.** Le projet ne réinvente pas les concepts : il **réutilise les standards et les
algorithmes de l'existant** et n'écrit que la chaîne d'exécution et de gouvernance, qu'aucune
solution ne peut fournir dans le contexte imposé.

**Tableau 11 — Ce que le projet reprend de l'état de l'art, d'où cela vient et comment cela a été implémenté.**

| Élément repris de l'existant | Provenance | Implémentation retenue |
|---|---|---|
| Décision *match / non-match* probabiliste | Fellegi-Sunter [B2] | score pondéré explicable 0.5 / 0.3 / 0.1 / 0.1, seuil 0.80 (§ 7.2.3) |
| Service de correspondance par score | FHIR `$match` [B5] | `engine/identity/matcher.py` — même philosophie, sans serveur FHIR |
| Interopérabilité par schéma pivot | FHIR [B5] | 4 entités `patient / encounter / condition / observation` |
| Stockage en zones de qualité croissante | Medallion [B9] | RAW / SILVER / GOLD sur HDFS + Hive |
| Rapprochement multi-sources | MPI / identity map [B13] | `master_patient` + `patient_identity_map` en PostgreSQL |
| Gouvernance et traçabilité | catalogue de métadonnées [B18] | **l'inverse** : le contrôle est exercé *au runtime* (RBAC, consentement, audit) et non seulement sur les métadonnées |

Face à cet état de l'art, les choix du projet sont assumés et explicables. Cinq
arbitrages structurent le positionnement : **RapidFuzz** avec un dictionnaire de
synonymes plutôt qu'un NLP lourd (`sentence_transformers`, qui crash sous Python 3.8
et n'aurait apporté qu'un mapping illustratif) ; un **MPI local avec pivot FHIR**
plutôt qu'un DMP/MPI réglementaire dédié, hors périmètre d'un stage sur données
synthétiques ; un **seuil pondéré 0.80** (0.5/0.3/0.1/0.1) plutôt qu'un seuil unique
à trois niveaux (90/70), validé par la parité ground-truth et par la lisibilité de la
décision ; une montée en complexité **par paliers (MVP → Spark → Big Data)** plutôt
qu'un Big Data direct, pour introduire chaque technologie par un besoin ; et enfin la
**parité Pandas = Spark vérifiée** plutôt que deux logiques divergentes, pour montrer
que le scale ne change pas la sémantique. L'inventaire complet des onze arbitrages,
avec pour chacun la preuve et le risque résiduel assumé, est donné dans la conclusion
générale.

Trois écarts à l'existant sont assumés, justifiés par le besoin et non par la commodité :

- **Pas d'estimation EM** (à la différence de Splink) : les poids restent **lisibles et
  modifiables** par un gestionnaire de données, condition posée par l'exigence « jamais fusionner
  sans logique explicable » [deduplication.md — règle métier].
- **Pas de référentiel externe** (à la différence d'EMPI) : aucune donnée de tiers n'entre dans
  la plateforme, conformément à l'hébergement interne.
- **Pas de service managé** (à la différence d'Azure HDS) : le Data Lake est interne à la VM
  (Hadoop 3.3.6, Hive 3.1.3, Spark 3.4.2) [Vagrantfile, bootstrap.sh].

Le risque propre à une chaîne sur mesure est la **maintenabilité** : il porte sur le code écrit,
pas sur le choix des standards. Il a été réduit en rendant les décisions paramétrables plutôt
qu'encodées dans la logique : poids, seuil et stratégie de blocage sont déclarés dans
`config/deduplication.yaml` et lus par le matcher, l'implantation Spark, l'évaluation et l'étape
SILVER. Une évolution du comportement se fait donc par **une** édition de YAML. Cette
centralisation a un contrepoids assumé : le même fichier alimente l'évaluation, si bien que
modifier un poids **invalide les métriques publiées** tant que l'évaluation n'a pas été rejouée
(chapitre 8).

> **Limite honnête de l'étude.** Les produits cités sont décrits **d'après leur documentation** et
> n'ont **pas été installés ni exécutés** : la grille compare des capacités annoncées, non des
> performances mesurées. Une évaluation comparative réelle demanderait un banc d'essai hors
> périmètre du stage.

## Conclusion et transition

L'état de l'art établit le vocabulaire et les références du mémoire : Entity
Resolution fondée sur Fellegi–Sunter [B2], similarités RapidFuzz [B4], MPI et FHIR,
consentement RGPD art. 9 [B10], architecture Big Data Medallion [B9] portée par
HDFS/Hive/Spark. Le marché, comparé sur six critères, ne les couvre jamais tous à la fois
dans les contraintes du stage : la décision qui en découle est une **chaîne sur mesure,
adossée aux standards** plutôt qu'un produit. Le chapitre 3 examine maintenant **l'existant
propre à MMT** — les systèmes de l'établissement, vus par l'utilisateur et par le
développeur — puis la solution envisagée.

### Références citées

[B1] Elmagarmid et al., *Duplicate Record Detection: A Survey*, IEEE TKDE 2007.
[B2] Fellegi & Sunter, *A Theory for Record Linkage*, JASA 1969.
[B3] Christen, *Data Matching*, Springer 2012.
[B4] RapidFuzz documentation, rapidfuzz.github.io/RapidFuzz.
[B5] HL7 FHIR §8.1.11, Resource Patient (v5.0.0), hl7.org/fhir/patient.html.
[B6] Apache Hadoop, HDFS Design.
[B7] Apache Spark, spark.apache.org.
[B8] Apache Hive, hive.apache.org.
[B9] Databricks, Lakehouse Medallion Architecture.
[B10] RGPD, article 9.
[B11] CNIL, *Quelles formalités pour les traitements de données de santé ?*
[B12] CNIL, *RGPD et professionnels de santé libéraux*.
[B13] InterSystems EMPI / IRIS for Health (PIX, PDQ).
[B14] Talend MDM, *Integrated Matching*. [B15] Splink (Fellegi-Sunter, EM).
[B16] HAPI FHIR. [B17] Azure Health Data Services. [B18] Apache Atlas.

Voir `references/bibliographie.md` (numérotation complète, URLs et
protocole de veille).

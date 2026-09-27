# Chapitre 2 — État de l'art

> **Statut** : rédigé (08/09/2026, actualisé 27/09/2026)

## Objectif

Situer la plateforme par rapport aux concepts et standards existants : Entity
Resolution et Record Linkage (historique, définitions, mesures de similarité,
blocking), Master Patient Index (MPI) et interopérabilité FHIR, architectures Big
Data (HDFS, MapReduce, Spark, Hive, Data Lake Medallion) et cadre juridique du
consentement sur les données de santé. Chaque concept est relié au rôle qu'il joue
dans le projet, conformément au document conceptuel
[`bigdata_concepts.md`](../documents/documentation/bigdata_concepts.md).

---

## 2.1 Entity Resolution et Record Linkage

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
[B3], se décompose en étapes :

| Étape | Rôle | Application dans le projet |
|---|---|---|
| **Prétraitement** | nettoyer, standardiser les champs | `CanonicalPatient` : casse, accents, CIN, villes, dates [deduplication.md §3] |
| **Indexation (blocking)** | réduire les comparaisons en groupes de candidats | préfixe nom, date de naissance, CIN [deduplication.md §4] |
| **Comparaison** | mesurer la similarité champ à champ | RapidFuzz, score pondéré [deduplication.md §5] |
| **Classification** | décider match / non-match | seuil 0.80, exact puis probabiliste [deduplication.md §5] |
| **Évaluation** | mesurer la qualité sur une vérité terrain | ground truth P/R/F1 [evaluation.md] |

Le résultat attendu de l'ER est une **réconciliation d'identités** : un patient
présent sous plusieurs formes dans plusieurs systèmes doit être reconnu comme une
seule entité physique, sans fusion erronée de personnes distinctes — c'est
l'équilibre **précision vs rappel** propre au domaine.

> **Point de vocabulaire.** Entity Resolution = déterminer si deux enregistrements
> désignent la même entité [B1] ; le résultat produit un **golden record** (fiche
> consolidée) et une **identity map** (table de correspondance traçable).

## 2.2 Mesures de similarité

Deux chaînes qui désignent la même personne diffèrent rarement d'un seul caractère :
les variantes *Jean Rakoto* / *Rakoto Jean* / *J. RAKOTO* imposent de comparer des
chaînes de caractères, pas seulement des égalités.

Les mesures classiques du domaine [B1], [B3] :

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

Le score combine quatre champs **pondérés** et **configurables** [deduplication.md §5] :

| Critère | Poids |
|---|---:|
| Nom | 0.50 |
| Date de naissance | 0.30 |
| CIN | 0.10 |
| Ville de naissance | 0.10 |

Décision : **score ≥ 0.80 → fusion automatique**, sinon pas de fusion (aucune
logique arbitraire). Les deux valeurs — pondérations et seuil — sont calibrées sur
le cas de référence « Jean Rakoto » et vérifiées par évaluation ; sur le jeu de
difficulté « hard », la similarité seule plafonne le rappel autour de **0.422**
(F1 0.594, précision 1.000) — voir chapitre 7 [evaluation_truth.md].

## 2.3 Blocking et complexité

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

## 2.4 Master Patient Index et interopérabilité FHIR

En santé, l'ER aboutit à un référentiel d'identités : le **Master Patient Index
(MPI)** — chaque patient des bases sources est rattaché à un identifiant synthétique
unique, le *master patient*, via une **identity map** traçable
[deduplication.md §6] :

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

## 2.5 Consentement et RGPD sur les données de santé

Les données de santé sont une **catégorie particulière** de données à caractère
personnel : leur traitement est **en principe interdit** par l'article 9 du RGPD,
sauf dérogation dont le **consentement explicite** (art. 9.2.a) [B10]. En droit
français, la loi Informatique et Libertés reprend ce principe (art. 6) et ses
exceptions (art. 44) [B11]. La CNIL rappelle en outre deux distinctions :
article 6 (base légale) et article 9 (dérogation données sensibles) se cumulent ;
le consentement au **traitement** diffère du consentement aux soins [B11], [B12].

Le projet incarne ces principes dans le système, et non à côté
[`consentement_gouvernance.md` §2–§5] :

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

## 2.6 Big Data : HDFS, MapReduce, Spark, Hive

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

| Brique | Rôle dans le projet | Fait vérifiable |
|---|---|---|
| HDFS | entrepôt du Data Lake (parquet) | `spark.sql.warehouse.dir = hdfs://localhost:9000` [bigdata_concepts.md §4] |
| Spark (PySpark) | mapping FHIR, normalisation, dédup, GOLD | config VM 8 Go : 4g/2g, 8 partitions [bigdata_concepts.md §6] |
| Hive | tables externes SILVER/GOLD, analyses SQL | `datalake_gold.patient_events_gold` [bigdata_concepts.md §5] |

Constat mesuré du projet : sur petits volumes (~6 à 36 lignes), Pandas est ~1–2 ms
contre ~0.4–4 s pour Spark — l'overhead JVM domine. Spark se justifie sur le
**volume** ; le projet le conserve aussi pour la **démonstration de parité**
(résultats strictement identiques au pipeline Pandas) [bigdata_concepts.md §2].

## 2.7 Data Lake Medallion et ELT

Le **modèle Medallion** (Databricks) organise le lac en **zones de qualité
croissante** : RAW (brut, inchangé) → SILVER (nettoyé, standardisé, doublons
identifiés) → GOLD (agrégé, prêt à l'analyse) [B9].

| Couche | Rôle | Dans le projet |
|---|---|---|
| **RAW** | brute, sans transformation | parquet `/datalake/raw/{source}/{table}` + tables externes |
| **SILVER** | nettoyée, **normalisée FHIR**, doublons marqués | `datalake_silver.*_fhir` (4 tables) |
| **GOLD** | agrégats prêts à l'analyse | `datalake_gold.patient_events_gold` (18 colonnes, 8 tranches RMA) |

Chaque zone est un **état distinct de la donnée**, ce qui apporte trois choses : la
**traçabilité** (on sait d'où vient chaque valeur), le **rejeu** (relancer un
traitement depuis une zone propre, sans tout recommencer) et la séparation exigée
par la gouvernance [bigdata_concepts.md §3].

Le pipeline suit la logique **ELT** (extract → load → transform) : l'ingestion
charge la donnée **telle quelle** dans RAW, la transformation s'applique *a
posteriori* dans les zones suivantes — c'est le **schéma-on-read** (« on décide
du format au moment de lire »), caractéristique du Data Lake
[bigdata_concepts.md §7].

## 2.8 Positionnement de la solution retenue

Face à cet état de l'art, les choix du projet sont assumés et explicables :

| Choix | Alternative écartée | Justification |
|---|---|---|
| **RapidFuzz** + synonymes | NLP lourd (`sentence_transformers`) | crash Python 3.8 ; mapping fake illustratif |
| **MPI local + FHIR pivot** | DMP/MPI réglementaire dédié | périmètre stage, données synthétiques |
| **Seuil 0.80 pondéré 0.5/0.3/0.1/0.1** | seuil à 3 niveaux (90/70) | parité ground-truth, logique explicable |
| **3 niveaux MVP → Spark → Big Data** | Big Data direct | chaque technologie introduite par besoin |
| **Parité Pandas = Spark vérifiée** | logiques divergentes | démontrer que scale ≠ changement de sémantique |

Cette grille est confrontée aux **produits existants** (MPI/DMP, MDM, plateformes Data Lake
santé, open source) au chapitre 3.

## 2.9 Cartographie concept → technologie

```mermaid
flowchart RL
    subgraph Concepts
        ER[Entity Resolution / Record Linking]
        SIM[Similarités Levenshtein / Jaro-Winkler]
        BLK[Blocking : clé nom + naissance + CIN]
        MPI[Master Patient Index + Identity Map]
        RGDP[RGPD art. 9 : consentement purpose-by-purpose]
        FH[Interopérabilité FHIR : Patient / $match]
        MED[Medallion RAW → SILVER → GOLD]
        ELT[ELT : Extract → Load → Transform]
    end
    subgraph Technologies
        RF[RapidFuzz]
        EN[engine/identity : canonical + matcher]
        PG[PostgreSQL central : master, consent, audit]
        SP[Spark / HDFS / Hive]
        API[API FastAPI RBAC + clés SHA-256<br/>refus 403 + audit]
    end
    ER --> EN
    SIM --> RF
    BLK --> EN
    MPI --> PG
    RGDP --> API
    RGDP --> PG
    FH --> SP
    MED --> SP
    ELT --> SP
```

## 2.10 Méthodologie de la veille et couverture des axes

**Protocole de recherche.** L'état de l'art n'est pas constitué par juxtaposition de
liens : les sections 2.1 à 2.9 correspondent à des **questions formulées à l'avance**,
dérivées du cahier des charges, auxquelles on a cherché une réponse sourcée.

| Question de veille | Où c'est traité | Sources retenues |
|---|---|---|
| Quelle théorie fonde l'appariement d'enregistrements ? | §2.1 | [B1], [B2], [B3] |
| quelles similarités, et lesquelles sont utilisables sous Python 3.8 ? | §2.2 | [B3], [B4] |
| Comment éviter la comparaison quadratique ? | §2.3 | [B1], [B3] |
| Quel standard de santé pour l'identité et l'échange ? | §2.4 | [B5] |
| Quelle base légale pour des données de santé ? | §2.5 | [B10], [B11], [B12] |
| Quelles briques Big Data, et pour quel usage ? | §2.6, §2.7 | [B6] à [B9] |
| Que fait déjà le marché et l'open source ? | chapitre 3 | [B13] à [B20] |

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

| Bloc | Axes | Traitement dans le mémoire |
|---|---|---|
| **1 — Existant** (0-4) | veille · règlementaire · solutions du marché · internes · personas | **0 traité** (§2.10) · **1-3 traités** (chapitres 2, 3) · **4 absent** (hors périmètre : le commanditaire est le public cible, pas l'utilisateur final) |
| **2 — Concepts** (5-9) | architecture · technologies · matrice de choix · données & flux · algorithmes | **5 traité** (§5.1) · **6 traité** (§2.11) · **7-8 partiels** (volumétrie et/providers non traités) · **9 traité** (FHIR, §2.4) |
| **3 — Choix** (10-15) | sécurité · performance · déploiement · coûts · contexte local · pilotage | **10 traité** (§2.5, §5.5) · **11-13 partiels** · **14 traité** (§4.5) · **15 traité** (§4.6) |
| **4 — Soutenance** (16-19) | coût-bénéfice · protection des données · sobriété · synthèse des décisions | **16-17 partiels** (RGPD traité, coût total non chiffré) · **18 optionnel absent** (hors périmètre) · **19 traité** (§8.1) |
| **5 — Méthodologie** | — | ce §2.10 |

## 2.11 Matrice de sélection technologique

Les choix du projet ne sont pas des preferences : ils sont arbitrés sur des
critères **explicités et pondérés**. La grille ci-dessous est appliquée aux trois
arbitrages structurants ; les critères sont issus des contraintes du chapitre 4
(Python 3.8, VM 8 Go, interdiction de NLP lourd, exigence d'explicabilité).

| Critère | Poids | Justification du poids |
|---|---:|---|
| C1 · Compatibilité environnement (Python 3.8, 8 Go) | 0.30 | contrainte **éliminatoire** : une option incompatible est écartée quelles que soient ses qualités |
| C2 · Explicabilité de la décision | 0.25 | exigence F3 : toute fusion doit être justifiable, toute finalité contrôlable |
| C3 · Coût mémoire / performance | 0.20 | la VM limite les ressources |
| C4 · Maturité et documentation | 0.15 | autonomie du stage, sans expert dédié |
| C5 · Coût de licence | 0.10 | budget nul |

**Arbitrage 1 — moteur de similarité** (note 1 à 5, 5 = le meilleur) :

| Option | C1 | C2 | C3 | C4 | C5 | **Score** | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| **RapidFuzz** [B4] | 5 | 5 | 5 | 5 | 5 | **5.00** | **retenu** |
| `sentence_transformers` | 1 | 2 | 1 | 4 | 5 | 2.10 | écarté (crash Python 3.8) |
| Levenshtein pur Python (`difflib`) | 4 | 3 | 2 | 5 | 5 | 3.60 | repli possible, trop lent |

**Arbitrage 2 — base centrale** :

| Option | C1 | C2 | C3 | C4 | C5 | **Score** | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| **PostgreSQL** | 5 | 5 | 4 | 5 | 5 | **4.80** | **retenu** (JSONB, contraintes CHECK, `TIMESTAMPTZ`) |
| SQLite | 5 | 3 | 5 | 4 | 5 | 4.35 | écarté (écriture concurrente des 3 sources) |
| MySQL | 4 | 4 | 4 | 5 | 5 | 4.25 | écarté (JSONB moins intégré) |

**Arbitrage 3 — framework d'API de gouvernance** :

| Option | C1 | C2 | C3 | C4 | C5 | **Score** | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| **FastAPI** | 5 | 5 | 4 | 4 | 5 | **4.65** | **retenu** |
| Flask | 5 | 3 | 5 | 5 | 5 | 4.50 | écarté de peu — validation manuelle de la finalité |

> **Lecture honnête du score.** Flask et FastAPI ne se séparent que de 0.15 : le
> choix n'est pas « le meilleur », mais « celui qui rend le contrôle de finalité
> **exprimable dans le schéma de l'API** plutôt que dans le code de la route »
> (C2 = 5 contre 3). De même, `SQLite` (4.35) et MySQL (4.25) ne sont écartés que
> par un critère de cohérence (écriture concurrente, support JSONB), pas par une
> incapacité. Le pondérage est **sensible** : C1 étant éliminatoire, aucune
> pondération ne réintroduirait `sentence_transformers`. Le même raisonnement
> appliqué à la déduplication (§2.2, poids 0.5/0.3/0.1/0.1) impose de garder le
> **score de similarité explicite**, jamais une décision opaque — c'est le principe
> commun aux deux exercices.

## Conclusion et transition

L'état de l'art établit le vocabulaire et les références du mémoire : Entity
Resolution fondée sur Fellegi–Sunter [B2], similarités RapidFuzz [B4], MPI et FHIR,
consentement RGPD art. 9 [B10], architecture Big Data Medallion [B9] portée par
HDFS/Hive/Spark. Chaque concept est **réincarné dans un choix de conception**,
arbitré sur une grille explicite (§2.11), et le périmètre de la revue est déclaré
 (§2.10). Le détail de la conception est donné au chapitre 5. Avant la conception,
le chapitre 3 examine **ce qui existe déjà** — les systèmes de l'établissement et
les solutions du marché, comparés sur six critères — puis le chapitre 4 analyse le
besoin : sources hétérogènes, générateur avec vérité terrain, contexte local,
conduite de projet et contraintes réelles (VM 8 Go, nœud distant).

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

Voir `references/bibliographie.md` (numérotation complète, URLs et
protocole de veille).
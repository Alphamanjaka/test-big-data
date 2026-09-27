# Chapitre 9 — Glossaire

> **Statut** : rédigé (27/09/2026)

## Objectif

Réunir en un seul endroit les mots techniques employés dans ce mémoire, et les expliquer en
français courant. Chaque entrée dit **ce que le mot signifie**, puis **où le sujet est détaillé**.
Aucun mot n'est inventé : tous ceux listés ici apparaissent dans les chapitres 1 à 8.

---

## 9.1 Comment lire ce glossaire

- **Le mot** est écrit comme il apparaît dans le texte, souvent en anglais : c'est l'usage
  courant du métier, on ne l'invente pas.
- **En clair** donne l'explication, sans jargon, en une ou deux phrases.
- **Où c'est détaillé** renvoie au chapitre, ou à la section, qui développe le sujet.

Un mot est expliqué **sur place** à sa première apparition ; le glossaire sert à retrouver
l'explication, pas à la remplacer. Les six mots-clés sont déjà donnés en langage courant dans
la section 1.3.

## 9.2 Données, identité et qualité

| Mot | En clair | Où c'est détaillé |
|---|---|---|
| **Doublon** | La même personne enregistrée plusieurs fois, donc comptée plusieurs fois dans les statistiques. | ch. 1, 2 |
| **Déduplication** | Reconnaître que deux fiches qui se ressemblent désignent la même personne, et n'en garder qu'une seule. | ch. 1 à 8 |
| **Entity Resolution** (ER) | Le nom savant de cette reconnaissance de doublons, quand elle porte sur plusieurs systèmes. | § 2.1 |
| **Record linkage** | Synonyme d'Entity Resolution, plus employé en statistique. | § 2.1 |
| **Blocking** | Réduire le travail avant de comparer : on ne confronte que des fiches qui ont une chance de correspondre (même début de nom, même date de naissance). Sans cela, il faut comparer chaque fiche à toutes les autres. | § 2.3, 5.3 |
| **Mesure de similarité** | Un chiffre qui dit à quel point deux valeurs se ressemblent, par exemple deux noms écrits différemment. | § 2.2 |
| **Score pondéré** | Un score de similarité où chaque champ compte pour une part choisie : ici le nom compte davantage que la ville de naissance. | § 2.2, 5.3 |
| **Seuil** | La valeur au-dessus de laquelle on décide que deux fiches sont la même personne. Au-dessus : fusion ; en dessous : pas de fusion. | § 2.2, 5.3 |
| **Faux positif** | Deux fiches fusionnées à tort : deux personnes différentes ont été confondues. C'est l'erreur la plus grave en santé. | § 7.2, 8.1 |
| **Faux négatif** | L'erreur inverse : deux fiches de la même personne n'ont pas été rapprochées. C'est ce que mesure le **rappel**. | § 7.2 |
| **master patient** | L'identifiant unique attribué à une personne, le même quels que soient les systèmes d'origine. | § 2.4 |
| **identity map** | La table qui relie chaque fiche d'origine à son `master_patient` : c'est elle qui rend chaque fusion explicable. | § 2.4 |
| **golden record** | La fiche consolidée d'une personne, obtenue après fusion. | § 2.1, 3.2 |
| **Modèle canonique** (`CanonicalPatient`) | Le format unique dans lequel le projet range tous les patients, quelle que soit leur source. | § 5.2 |
| **CIN** | Le numéro d'identité nationale malgache, qui identifie une personne de façon fiable. | § 1.2, 2.2 |
| **Pivot FHIR** | Utiliser le format FHIR comme format d'échange commun entre des sources qui n'ont pas le même format. | § 2.4, 3.1, 4.1 |
| **Vérité terrain** (*ground truth*) | La liste de référence qui dit, dossier par dossier, quelles fiches sont vraiment la même personne. C'est la seule façon de mesurer si la déduplication est bonne. | § 2.1, 4.7, 7.2 |
| **Précision, rappel, F1** | Les trois mesures de qualité : la précision compte les bonnes fusions, le rappel compte les fusions manquées, le F1 fait la moyenne des deux. | § 2.2, 7.2 |

## 9.3 Architecture Big Data

| Mot | En clair | Où c'est détaillé |
|---|---|---|
| **Big Data** | Des données trop nombreuses ou trop variées pour un poste de travail : il faut les répartir sur plusieurs machines. | § 2.6 |
| **Data Lake** | Un grand magasin de fichiers bruts, où l'on dépose tout sans décider à l'avance de la forme finale. | § 2.6, 2.7 |
| **Medallion** | Ranger la donnée dans trois zones de qualité croissante : **RAW** (brut) → **SILVER** (nettoyé) → **GOLD** (prêt à analyser). | § 2.7 |
| **RAW** | La zone du Data Lake qui contient la donnée telle qu'elle arrive, sans aucune transformation. | § 2.7 |
| **SILVER** | La zone nettoyée et standardisée, où les doublons sont signalés. | § 2.7 |
| **GOLD** | La zone finale, enrichie et directement exploitable par les analyses et l'API. | § 2.7 |
| **ELT** | On **charge** d'abord les données telles quelles, on **transforme** ensuite. C'est l'inverse de l'ETL, où l'on transforme avant d'écrire. | § 2.7 |
| **ETL** | On **extrait** la donnée, on la **transforme**, puis on la **charge** : le traitement précède l'écriture. | § 3.2 |
| **Schéma-on-read** | Le format des données est décidé au moment de les lire, pas au moment de les écrire. | § 2.7, 5.6 |
| **HDFS** | Le système de fichiers réparti qui stocke réellement les fichiers du Data Lake, sur plusieurs machines. | § 2.6 |
| **Hive** | La couche qui permet d'écrire des requêtes SQL sur les fichiers du Data Lake, comme dans une base de données. | § 2.6 |
| **metastore** | Le catalogue de Hive : la liste des tables, de leurs colonnes et de leur emplacement. | § 2.6, 5.1 |
| **HiveServer2** | Le service qui reçoit les requêtes SQL et les exécute sur le Data Lake. | § 2.6, 5.1 |
| **Spark** | Le moteur de calcul qui traite les données en mémoire et répartit le travail sur plusieurs machines. | ch. 1 à 8 |
| **PySpark** | Spark écrit en Python, c'est-à-dire l'interface utilisée dans ce projet. | § 2.6, 6.3 |
| **MapReduce** | Le premier modèle de calcul réparti de Hadoop, aujourd'hui remplacé par Spark en pratique. | § 2.6 |
| **Partition** (de données) | Un morceau d'un fichier, découpé pour être traité en parallèle. Sur la VM du projet, le traitement se fait en 8 partitions. | § 2.6, 4.4 |
| **Pipeline** | L'enchaînement des étapes : extraction, transformation, puis chargement. | ch. 1 à 8 |
| **Rejeu** | Relancer un traitement depuis une zone propre du Data Lake, sans tout recommencer depuis le début. | § 2.7, 3.1, 5.6 |
| **Idempotence** | Relancer le même traitement ne duplique rien et ne casse rien : on obtient le même état qu'au premier passage. | § 5.4 |
| **Entrepôt de données** (*warehouse*) | Un stockage organisé pour l'analyse, où les données sont nettoyées et rapprochées. | § 2.6, 4.4 |
| **Volumétrie** | La quantité de données à traiter, exprimée en nombre de lignes ou en taille. | § 2.10, 4.5 |
| **Parité** | Le fait que deux implémentations différentes, ici Pandas et Spark, rendent exactement les mêmes résultats. | § 2.6, 6.3, 7.2 |
| **Parquet** | Le format de fichier compressé utilisé dans le Data Lake, plus compact qu'un CSV. | § 2.7 |

## 9.4 Gouvernance, sécurité et droit

| Mot | En clair | Où c'est détaillé |
|---|---|---|
| **Consentement** | L'accord du patient pour que ses données soient utilisées, donné ou retiré selon des règles précises. | ch. 1 à 8 |
| **Finalité** (*purpose*) | Ce que l'on veut faire des données : consulter, chercher, ou analyser. Le projet n'accepte que trois finalités : `api_access`, `research`, `analytics`. | § 2.5, 5.5 |
| **Consentement par finalité** (*purpose-by-purpose*) | Un accord donné finalité par finalité, plutôt qu'un oui global. C'est ce qu'exige l'article 9 du RGPD. | § 2.5, 5.5 |
| **Refus par défaut** | Sans réponse explicite du patient, l'accès est refusé : l'absence d'avis vaut refus. | § 2.5, 5.5 |
| **RBAC** | Les droits d'accès sont attachés à un rôle (`admin`, `analyst`, `viewer`) et non à une personne : on donne un rôle, pas un nom. | § 2.5, 5.5 |
| **Rôle** | Le niveau d'autorisation d'un utilisateur : lecture large, lecture restreinte, ou administration. | § 2.5, 5.5 |
| **Clé d'API** | Un long texte secret présenté par l'application pour prouver qui elle est, à la place d'un mot de passe. | § 2.5, 6.5 |
| **SHA-256** | L'algorithme de hachage utilisé pour stocker les clés d'API : la base n'en garde que l'empreinte, illisible. Il protège la lecture directe de la table, mais n'est **ni salé ni lent**, donc insuffisant face à une attaque par dictionnaire — dette déclarée en § 8.3. | § 2.5, 5.4 |
| **Audit d'accès** | Le journal de qui a demandé quoi, quand et avec quelle finalité, y compris les refus. | ch. 1 à 8 |
| **403** | Le code HTTP renvoyé quand l'accès est refusé : l'utilisateur est connu et autorisé en général, mais la finalité demandée n'est pas consentie. | § 2.5, 5.5 |
| **API** (*endpoint*) | Un point d'entrée du programme : l'URL appelée, avec sa méthode, qui renvoie une réponse. | § 5.5, 6.5 |
| **Données synthétiques** | Des données fabriquées pour la démonstration, qui imitent la réalité sans contenir aucun patient réel. | § 1.5, 4.3, 5.5 |
| **Hébergement interne** (*on-premise*) | Les données restent sur les machines de l'établissement, sans passer par un service cloud externe. C'est une contrainte du commanditaire. | § 3.2, 3.3 |
| **Dé-identification** | Retirer de la donnée tout ce qui permet de reconnaître une personne. | § 3.2, 8.4 |
| **RGPD** | Le règlement européen de protection des données. L'article 9 interdit en principe de traiter des données de santé, sauf dérogation, dont le consentement explicite. | § 2.5 |
| **CNIL** | L'autorité française de contrôle du RGPD ; ses publications ont servi de source ici. | § 2.5 |
| **MPI** (Master Patient Index) | Un annuaire de patients qui attribue un identifiant unique à chaque personne. | § 2.4, 3.2 |
| **DMP** (Data Management Platform) | Une plateforme qui pilote la qualité des données d'un établissement. | § 3.2 |
| **MDM** (Master Data Management) | La même approche appliquée aux données de référence, patients ou non ; exemple : Talend MDM. | § 3.2 |
| **EMPI** | Le « master patient index » d'InterSystems, produit commercial cité en § 3.2. | § 3.2 |
| **Lineage** | Savoir d'où vient une donnée et par quelles transformations elle est passée. | § 3.2 |

## 9.5 Les objets du dépôt

Le glossaire ci-dessus explique les mots. Celui-ci explique les noms : où se trouve le code cité
dans les chapitres, et à quoi il sert.

### 9.5.1 Les tables de la base centrale (PostgreSQL)

| Table | Ce qu'elle contient | Où c'est détaillé |
|---|---|---|
| `raw_patient_record` | Les fiches telles qu'elles arrivent des trois sources, sans transformation. | § 5.4 |
| `master_patient` | Un enregistrement par patient retenu, avec son `master_patient_id`. | § 3.4, 5.1, 5.4 |
| `patient_identity_map` | Le lien entre une fiche d'origine et son `master_patient_id`, avec le score et la méthode de rapprochement. | § 3.4, 5.4, 8.1 |
| `consent` | Les avis de consentement : un patient, une finalité, un oui ou un non, une date. | § 2.5, 5.4 |
| `api_user` | Les utilisateurs de l'API : rôle, clé d'API hachée, état du compte. | § 2.5, 5.1, 5.4 |
| `access_audit` | Le journal des accès : qui, quoi, quand, quelle finalité, et le motif d'un éventuel refus. | § 2.5, 5.1, 5.4 |
| `medicine_purchase`, `patient_consultation`, `imaging_exam` | Les événements métier des trois sources, conservés séparément pour rester vérifiables. | § 5.4 |

### 9.5.2 Les scripts et les couches

| Chemin | Rôle | Où c'est détaillé |
|---|---|---|
| `run_pipeline.sh` | Le chef d'orchestre du pipeline ELT : il enchaîne les étapes et produit les journaux. | § 1.5, 6.2 |
| `gen_extract_raw.py` | Extraction : lit les bases sources et écrit la zone RAW. | § 6.2 |
| `gen_fhir_mapping.py` | Associe chaque champ FHIR attendu à la colonne source la plus proche. | § 6.2 |
| `create_silver.py` | Construit la zone SILVER : nettoyage, standardisation, doublons marqués. | § 6.2 |
| `create_gold.py` | Construit la zone GOLD, en tenant compte du consentement. | § 6.2 |
| `engine/identity/canonical.py` | Le modèle canonique `CanonicalPatient` et la normalisation des champs. | § 5.2, 6.3 |
| `engine/identity/matcher.py` | Le moteur de rapprochement exact puis probabiliste, avec le seuil à 0.80. | § 5.3, 6.3, 7.3 |
| `engine/identity/spark_dedup.py` | Le même moteur écrit pour Spark, qui doit rendre le même résultat. | § 5.6, 6.3 |
| `engine/governance/consent.py` | Les finalités autorisées et la décision d'accorder ou de refuser un accès. | § 2.5, 6.5 |
| `engine/governance/auth.py` | La clé d'API, résolue en utilisateur et en rôle. | § 2.5, 6.5 |
| `engine/governance/audit.py` | La journalisation de chaque appel dans `access_audit`. | § 2.5, 6.5 |
| `engine/governance/app.py` | L'API de gouvernance : la liste des patients, le détail d'un patient, l'audit. | § 5.5, 6.5 |
| `hive_api.py` | L'API REST des données GOLD, exposée sur les routes `/rma/*`. | § 6.5, 6.6 |
| `seed_governance.py` | Prépare un jeu de démonstration : utilisateurs de démonstration et consentements. | § 8.3, 8.4 |
| `sql/schema.sql` | La structure de la base centrale, relisible et rejouable. | § 2.5, 5.4 |

## Conclusion et transition

Ce glossaire ne remplace rien : il rassemble. Les définitions détaillées restent dans les
chapitres, où elles sont argumentées et sourcées. Il permet de lire le mémoire dans l'ordre
inverse — partir d'un mot, puis ouvrir le chapitre correspondant.

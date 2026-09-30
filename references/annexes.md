# Annexes

## Annexe A — Le pipeline ELT : exécution, étapes et journaux

Le pipeline est piloté par un seul script, `provision/scripts/run_pipeline.sh`, qui enchaîne
les étapes dans l'ordre et produit le journal `elt.log`. Le principe Medallion — RAW, puis
SILVER, puis GOLD — est implémenté par cinq programmes distincts : `ensure_generator_data.sh`
(étape préparatoire et idempotente : régénère les CSV synthétiques seulement s'ils sont
absents), `gen_extract_raw.py` (extraction vers la zone RAW), `gen_fhir_mapping.py` (association
des champs FHIR aux colonnes sources), `create_silver.py` (nettoyage, standardisation et
marquage des doublons) et `create_gold.py` (zone finale, application du consentement). Chaque
étape est un programme distinct plutôt qu'une fonction d'un programme unique : une étape qui
échoue ne laisse pas la zone suivante dans un état intermédiaire, ce qui est la condition pour
que le pipeline soit relançable. La reprise d'un run (`--resume`), l'ingestion incrémentale
(`watermark.json`) et la planification par cron (scheduler) sont décrites au § 7.3.2 du mémoire.

Le journal `elt.log` conserve le déroulé de chaque exécution : étapes, volumes écrits
(patients maîtres, tables GOLD) et erreurs. Les compteurs chiffrés de chaque run (lignes par
source, patients maîtres, doublons, volumes GOLD) sont en outre enregistrés dans la base
centrale, ce qui permet de comparer deux exécutions sans les rejouer. Le journal n'est pas
versionné, puisqu'il est produit à chaque passage.

## Annexe B — La structure de la base centrale

Le schéma complet de la base PostgreSQL de gouvernance est dans `sql/schema.sql`, écrit pour
être relu et rejoué. Il crée **onze tables** : `raw_patient_record` (les fiches brutes des trois
sources), `master_patient` (un enregistrement par patient retenu), `patient_identity_map` (le
lien de chaque fiche d'origine vers son patient maître, avec score et méthode), `consent` (les
avis de consentement par finalité), `medicine_purchase`, `patient_consultation` et
`imaging_exam` (les événements métier des trois sources), `api_user` (les utilisateurs, leur rôle
et leur clé d'API hachée), `access_audit` (le journal des accès), et `pipeline_run` et
`pipeline_run_source` (l'historique des runs). Les patients maîtres et leurs correspondances sont
écrits par le pipeline (étape SILVER) ; les comptes et consentements de démonstration, par
`provision/db/seed_governance.py`.

Deux choix de ce schéma sont discutés ailleurs et ne sont pas repris ici : le refus par défaut,
matérialisé par l'absence de ligne dans `consent`, et le fait que `patient_identity_map` porte
le score et la méthode, sans quoi une fusion serait inexplicable.

## Annexe C — Le moteur de rapprochement

Le moteur tient dans trois fichiers de `engine/identity/`. `canonical.py` définit le modèle
canonique et la normalisation des champs, notamment la fonction `matching_key`, qui produit la
clé de rapprochement. `matcher.py` porte l'algorithme : la similarité entre deux valeurs, la
comparaison par préfixe de nom, et la fonction `deduplicate`, qui enchaîne rapprochement exact
puis rapprochement probabiliste pondéré par champ, au-dessus du seuil de 0,80.
`spark_dedup.py` est le même algorithme réécrit pour Spark, dont la parité stricte avec la
version Pandas est l'un des résultats vérifiés du projet.

Cette duplication de l'algorithme est le prix d'un choix fait tard : comparer deux
implémentations plutôt que décider plus tôt de l'échelle. Cette décision et
son coût sont discutés au § 7.2.3 et retenus comme leçon de conduite de projet au § 4.3 et
dans la conclusion générale.

## Annexe D — L'API de gouvernance

Quatre fichiers de `engine/governance/` portent la gouvernance. `auth.py` résout une clé
d'API en utilisateur et en rôle, la base ne conservant que l'empreinte SHA-256 de la clé.
`consent.py` définit les finalités autorisées et la décision d'accorder ou de refuser un
accès, avec le refus par défaut. `audit.py` journalise chaque appel, y compris les refus.
`app.py` expose l'API FastAPI : la liste des patients (avec recherche texte et CIN, pagination,
et **filtrage silencieux** — un patient sans consentement pour la finalité demandée disparaît
plutôt que de provoquer une erreur), le détail d'un patient, la consultation de l'audit, la
planification du pipeline (`/pipeline/schedule`, GET/PUT, écriture réservée à l'admin), son
statut (`/pipeline/status`) et l'historique des runs (`/pipeline/runs`).

Pour la fiche d'un patient, un refus renvoie un **403** plutôt qu'une réponse muette, et ce refus
est journalisé comme un accès accordé. C'est cette propriété qui rend la gouvernance vérifiable
par un tiers.

## Annexe E — L'API des indicateurs du warehouse et les vues de gouvernance

`provision/api/hive_api.py` expose les indicateurs de **gouvernance** du Data Lake sur les
routes `/api/governance/*` (`duplicates` sur la table SILVER `patient_fhir`, `consent` sur la
table GOLD `patient_consent_gold`), avec un repli explicite sur un jeu de démonstration
(`mock_data.py`) lorsque la source n'est pas disponible. Les données de démonstration sont
signalées comme telles à l'écran, ce qui évite qu'un indicateur de démonstration soit lu comme
une mesure réelle. L'interface web se trouve dans `front-optional/`, et son contrat d'interface
dans `front-optional/src/lib/api.ts`.

Cette partie du projet est **optionnelle** dans le cahier des charges. Elle est donc présentée
comme une démonstration de ce que la zone SILVER/GOLD sait exposer, et non comme un résultat de
production.

## Annexe F — La génération des données synthétiques et la vérité terrain

Le générateur se trouve dans `evaluation/synthetic-patient-generator/`. Il produit les
données patients des trois sources, avec une graine fixe (`--seed 42`) qui rend la génération
reproductible, et environ 75 % des patients maîtres portent un CIN. La vérité terrain, qui dit
pour chaque fiche à quel patient réel elle appartient, est le fichier
`data/experiments/<niveau>/ground_truth/identity_mapping.csv` ; les résultats de l'évaluation
sont consignés dans `evaluation/evaluation_truth.md`. Sans cette vérité terrain, on ne pourrait
pas mesurer si la déduplication est bonne.

Aucune donnée réelle de patient n'est utilisée dans ce projet, y compris lorsqu'elle serait
plus simple à obtenir. C'est une contrainte du commanditaire, mais c'est aussi ce qui rend
le travail reproductible et partageable : le jeu complet se régénère en une
commande.

## Annexe G — Couverture de la grille d'analyse de l'état de l'art

La grille d'état de l'art du master comporte 20 axes répartis en cinq blocs (A à E). Pour chacun, le tableau indique la section du mémoire qui le traite, ou ce qui reste partiel ou hors périmètre.

| Bloc de la grille | Axes et traitement dans le mémoire |
|---|---|
| **A — Cadrage du besoin** (0-2) | **0** veille : traité (§ 2.1.1) · **1** entreprise et existant interne : traité (§ 1.1, § 3.1) · **2** besoin métier et cadre réglementaire : traité (§ 1.2, § 2.1.6) |
| **B — Existant et utilisateurs** (3-4) | **3** solutions existantes : traité (§ 2.2, § 2.3) · **4** utilisateurs et personas : **hors périmètre** (le commanditaire est le public cible du prototype, pas un utilisateur final observé) |
| **C — Analyse technique** (5-13) | **5** architecture : traité (§ 6.1) · **6** écosystème technologique : traité (§ 2.2.2, § 7.1) · **7** données et flux : **partiel** (volumétrie cible inconnue, § 4.2) · **8** briques algorithmiques : traité (§ 2.1.2 à 2.1.4, § 2.2.2) · **9** interopérabilité : **partiel** (FHIR traité, reprise des sources réelles hors du run de référence) · **10** sécurité : **partiel** (rôles, consentement et audit conçus ; hachage non salé, journal non chiffré) · **11** performance : **partiel** (petits volumes mesurés, pas de test de charge) · **12** qualité et tests : traité (chapitre 8) · **13** déploiement : **partiel** (VM reproductible, ni conteneur ni intégration continue) |
| **D — Contraintes et valeur** (14-18) | **14** contexte local : traité (§ 4.2) · **15** conduite de projet : traité (§ 4.1, § 4.3) · **16** coûts et dépendances : **partiel** (coût du stage et dépendance aux éditeurs traités, § 2.2.1, § 4.4 ; coût de possession sur trois ans non chiffré) · **17** protection des données : traité (§ 2.1.6) · **18** sobriété : **optionnel, non traité** |
| **E — Synthèse et décision** (19) | **19** justification des choix : traité (§ 2.3, § 2.4, § 7.1, conclusion générale) |

## Annexe H — Captures de la plateforme en fonctionnement

Captures réalisées le 30/09/2026 sur la plateforme en fonctionnement (VM, API, interface
web), avec les données synthétiques du jeu difficile. Les captures de terminal reproduisent
des sorties réelles, sans modification ; les clés d'API y sont masquées.

![](documents/captures/C04_synthese.png)

> **Figure 10 — Page de synthèse : qualité d'identité et consentement, sur les données du lac.**

![](documents/captures/C07_pipeline.png)

> **Figure 11 — Tableau de bord du pipeline et historique des runs.**

![](documents/captures/C09_fiche_patient.png)

> **Figure 12 — Fiche d'un patient : identité, correspondances et consentements.**

![](documents/captures/C10_swagger.png)

> **Figure 13 — Documentation interactive de l'API de gouvernance, générée par FastAPI.**

![](documents/captures/C11_hdfs_datalake.png)

> **Figure 14 — Les trois zones du lac dans l'interface de HDFS.**

![](documents/captures/C12_run_pipeline.png)

> **Figure 15 — Run du pipeline en mode reprise (extraits du journal).**

![](documents/captures/C14_refus_403.png)

> **Figure 16 — Contrôle d'accès de l'API de gouvernance sur la base peuplée.**

![](documents/captures/C15_pytest.png)

> **Figure 17 — Suite de tests automatisés : 123 tests réussis.**

![](documents/captures/C16_evaluation.png)

> **Figure 18 — Évaluation du run du pipeline sur la vérité terrain (jeu difficile).**

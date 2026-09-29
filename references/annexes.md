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

Le journal `elt.log` est l'artefact le plus utile en cas de doute : il conserve, pour chaque
exécution, le nombre de lignes lues, écrites et écartées, et la durée de chaque étape. C'est
lui qui permet de comparer deux exécutions sans les rejouer. Il n'est pas versionné, puisqu'il
est produit à chaque passage.

## Annexe B — La structure de la base centrale

Le schéma complet de la base PostgreSQL de gouvernance est dans `sql/schema.sql`, écrit pour
être relu et rejoué. Il crée **neuf tables** : `raw_patient_record` (les fiches brutes des trois
sources), `master_patient` (un enregistrement par patient retenu), `patient_identity_map` (le
lien de chaque fiche d'origine vers son master, avec score et méthode), `consent` (les avis de
consentement par finalité), `medicine_purchase`, `patient_consultation` et `imaging_exam` (les
événements métier des trois sources, conservés séparément pour rester vérifiables), `api_user`
(les utilisateurs, leur rôle et leur clé d'API hachée) et `access_audit` (le journal des
accès). Le jeu de démonstration qui alimente ces tables est produit par
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

Cette duplication volontaire de l'algorithme n'est pas un défaut de conception mais le prix d'un choix fait tard, celui de devoir
comparer deux implémentations plutôt que de décider plus tôt de l'échelle. Cette décision et
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
planification du pipeline (`/pipeline/schedule`, GET/PUT, écriture réservée à l'admin) et son
statut (`/pipeline/status` : plan, prochain run, sources suivies, zones et dernier run).

Un refus renvoie un **403** et
non une réponse muette ou une liste réduite, et que ce refus est journalisé comme un accès
accordé. C'est cette propriété qui rend la gouvernance vérifiable par un tiers.

## Annexe E — L'API des indicateurs du warehouse et les vues de gouvernance

`provision/api/hive_api.py` expose les indicateurs de **gouvernance** du Data Lake sur les
routes `/api/governance/*` (`duplicates` sur la table SILVER `patient_fhir`, `consent` sur la
table GOLD `patient_consent_gold`), avec un repli explicite sur un jeu de démonstration
(`mock_data.py`) lorsque la source n'est pas disponible. Les données de démonstration sont
signalées comme telles à l'écran, ce qui évite qu'un indicateur de démonstration soit lu comme
une mesure réelle. Le front se trouve dans `front-optional/`, et son contrat d'interface dans
`front-optional/src/lib/api.ts`.

Cette partie du projet est **optionnelle** dans le cahier des charges. Elle est donc présentée
comme une démonstration de ce que la zone SILVER/GOLD sait exposer, et non comme un résultat de
production.

## Annexe F — La génération des données synthétiques et la vérité terrain

Le générateur se trouve dans `evaluation/synthetic-patient-generator/`. Il produit les
données patients des trois sources, avec une graine fixe (`--seed 42`) qui rend la génération
reproductible, et environ 75 % des fiches portent un CIN. La liste de référence qui dit, dossier
par dossier, quelles fiches désignent la même personne est `evaluation/evaluation_truth.md`.
Sans elle, on ne pourrait pas mesurer si la déduplication est bonne : on ne saurait que des
chiffres, pas une qualité.

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

## Annexe H — Questions anticipées du jury

Cette annexe recense les objections les plus probables du jury, avec la réponse **vérifiée** et
l'endroit du mémoire où elle s'appuie.

**1. « Votre précision vaut 1,000 : le moteur ne fusionne-t-il jamais deux patients différents ? »**
Non sur les trois jeux évalués, et ce n'est pas une garantie. Le générateur dégrade des
enregistrements existants — casse, espaces, fautes de frappe, changements de format — mais ne crée
jamais deux personnes distinctes qui se ressemblent : le cas adversariaire des faux positifs n'est
donc pas sollicité par la vérité terrain. C'est un plancher, pas une borne. § 8.6.

**2. « Un rappel de 0,422 est-il acceptable en santé ? »**
Sur le jeu « hard » (variations à 50 %), il reste 420 faux négatifs sur 1 057 enregistrements. Le
seuil 0,80 est conservateur et n'a pas été abaissé sans validation métier : l'abaisser remonte le
rappel mais réintroduit le risque de fusion de deux patients, que la priorité donnée à la précision
interdit. Levier identifié : enrichir la clé exacte (adresse), puis calibrer sur la vérité terrain.
§ 8.5, conclusion générale (perspectives).

**3. « Pourquoi ne pas estimer les poids et le seuil par EM, comme Splink ? »**
Pour qu'un EM ait un sens, il lui faut des données d'appariement identifiantes ; celles du stage
sont synthétiques et n'ont pas été appariées par un tiers. Les paramètres seraient donc estimés sur
des paires que le modèle n'a pas lui-même produites. Le choix retenu — un score pondéré **lisible**
(0,5 / 0,3 / 0,1 / 0,1, seuil 0,80, déclarés dans un fichier de configuration) — se justifie ligne à
ligne devant un gestionnaire de données. L'EM reste une perspective, « en complément », avec double
comptage explicable. § 2.4, § 7.2.3, conclusion générale (perspectives).

**4. « Une VM de 8 Go suffit-elle pour passer à l'échelle ? »**
Non. Le run de référence porte quelques centaines de lignes en SILVER : le parcours Big Data est
**architecturé et reproductible** (HDFS, RAW → SILVER → GOLD), pas passé à l'échelle. Le passage à
l'échelle suppose le partitionnement du blocking et la consolidation transitive des clusters.
Conclusion générale (limites, perspectives).

**5. « Le consentement est-il réellement appliqué ? »**
La règle l'est : `purpose` est obligatoire (422), une finalité non consentie produit un refus (403),
et chaque accès comme chaque refus est journalisé — 16 cas de test dédiés à l'API de gouvernance.
La donnée ne l'était pas au moment du run : `patient_consent_gold` compte 145 lignes mais `purpose`
et `granted` sont à `NULL`, le PostgreSQL central n'ayant pas été peuplé faute d'environnement. La
distinction entre **mécanique prouvée** et **donnée absente** est maintenue partout. § 7.3.5, § 8.6.

**6. « Pourquoi une API Flask et une API FastAPI ? »**
L'API de données (Flask) est une surface de *reporting* sur la zone GOLD, héritée du PoC : elle ne
filtre rien. Le contrôle par rôle et par consentement est appliqué sur l'API de gouvernance
(FastAPI), seule à renvoyer 401, 403 et 422. Cette frontière est assumée, bornée et documentée.
§ 7.3.5, conclusion générale (limites).

**7. « Les clés d'API sont-elles vraiment protégées ? »**
La clé en clair n'est ni stockée ni exposée : la base n'en conserve qu'une empreinte SHA-256. En
revanche cette empreinte n'est **ni salée ni lente**, si bien qu'une table de correspondance
suffirait à retrouver une clé. La dette, sa cause et sa correction (sel par clé, ou fonction lente
comme `bcrypt` déjà utilisée côté frontend) sont déclarées dans les limites de la conclusion
générale.

**8. « Les 3 tests de l'API Flask prouvent-ils le contrôle d'accès ? »**
Non : ils prouvent la joignabilité et les statuts de réponse. Le contrôle d'accès est vérifié
séparément par les 16 cas de l'API de gouvernance. § 8.4, § 8.6.

**9. « Comment garantissez-vous qu'aucun profil n'a été inventé ? »**
Le générateur est à racine fixe (`RANDOM_SEED = 42`) et toutes les données sont synthétiques. Aucune
valeur n'est estimée côté patients : un genre hors liste fermée, un CIN de longueur incohérente ou
une date illisible laissent le champ vide, et l'enregistrement bascule alors vers la voie
probabiliste. Un champ douteux ne peut donc pas corrompre une clé de rapprochement exact.
§ 5.1.5, § 7.3.1.

**10. « Pourquoi ne pas tout mettre dans PostgreSQL ? »**
Parce que les deux magasins n'ont pas le même rôle : HDFS, Hive et Spark portent le lac rejouable et
les trois zones de qualité, PostgreSQL porte l'état de référence — patients maîtres, consentements,
journal d'audit, comptes. C'est une séparation de rôles, pas une redondance. § 6.1.2, § 7.2.2.

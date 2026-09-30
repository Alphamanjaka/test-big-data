# Conclusion générale

## Bilan : réponse à la problématique

La problématique posée en introduction était la suivante :

> *Comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des
> données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités
> et la gouvernance des accès basée sur le consentement du patient ?*

**Tableau 45 — Réponse à la problématique, volet par volet.**

| Volet de la problématique | Réponse conçue et réalisée | Preuve vérifiable |
|---|---|---|
| **Intégrer** des sources hétérogènes | couche d'extraction abstraite (CSV, PostgreSQL, SQLite) → zone **RAW** en parquet HDFS, tables Hive externes, typage `STRING` assumé | 3 sources actives + 3 sources avancées (MAVIS 11 tables, MMT_DB 9 tables, CLINIQUE 4 tables) capturées [§ 3.1.2] |
| **Nettoyer / normaliser** | modèle canonique `CanonicalPatient` + schéma pivot **FHIR** (4 entités) + normalisation de genre, dates, CIN | `datalake_silver.patient_fhir` : **1 057 lignes** (404 + 353 + 300), dates et noms complets (run du 29/09/2026) |
| **Dédupliquer** de façon explicable | blocking sur trois clés, passe **exacte** puis passe **probabiliste** (RapidFuzz, poids 0,5 / 0,3 / 0,1 / 0,1, seuil 0,80) ; chaque décision porte méthode, score et explication | **803 patients maîtres**, 254 doublons ; précision de 1,000 sur vérité terrain, pour le moteur seul comme pour le pipeline complet |
| **Centraliser en conservant la traçabilité** | Medallion **RAW → SILVER → GOLD**, `patient_uuid` (empreinte SHA-2 de la source et de l'identifiant d'origine), colonnes `_source_system` / `_source_table`, `patient_identity_map` ; orchestration reprise (`pipeline_state.json`) et incrémentale (watermark) | runs complets et en reprise réussis sur la VM (29–30/09/2026), historique de chaque run en base ; **1 057 − 254 = 803** vérifié par comptage sur le lac |
| **Gouverner par consentement** | **RBAC** (admin / analyst / viewer), clés API **SHA-256**, consentement *purpose-by-purpose* lié au `master_patient_id`, **finalité déclarée obligatoire**, refus **403** journalisé avec son motif | `access_audit` : `purpose` et `refusal_reason` ; **123 tests** réussis ; 401, 403 (rôle, consentement) et 422 vérifiés aussi sur une base peuplée (803 patients, 2 409 avis) |
| **Ne jamais fusionner sans logique explicable** | règle **structurelle** : aucun `master_patient_id` sans `match_method` (`new_master` / `exact` / `probabilistic`) | précision de **1,000**, **aucun faux positif** sur les trois jeux |

### Synthèse des arbitrages

Les choix du projet se lisent comme une suite d'arbitrages, chacun posé sur des
critères explicites (§ 7.1) et chacun assorti d'un risque résiduel assumé. Cette
table est la réponse à la question « *qu'avez-vous choisi, et à la place de quoi ?* ».

**Tableau 46 — Les arbitrages du projet.**

| Décision | Alternative écartée | Critère décisif | Preuve | Risque résiduel |
|---|---|---|---|---|
| **RapidFuzz** | `sentence_transformers` | compatibilité Python 3.8 (C1) | 2,10 contre 5,00 en arbitrage pondéré | rappel limité sur les variations fortes (0,422) |
| **Seuil 0,80**, poids 0,5 / 0,3 / 0,1 / 0,1 | seuil plus bas, davantage de fusions | en santé, une fusion à tort est plus grave qu'une fusion manquée | précision de 1,000 sur les 3 jeux, aucun faux positif | 420 paires manquées sur le jeu difficile |
| **CIN dans la clé exacte** (et le blocking) | rapprochement sur le nom et la date seuls | CIN porté par environ 75 % des patients | rappel du jeu difficile 0,287 → **0,422** | patients sans CIN : rappel plus faible |
| **Medallion RAW → SILVER → GOLD** | base unique « à plat » | traçabilité et rejeu exigés (F1) | runs complets et en reprise réussis ; 1 761 événements en GOLD | agrégats GOLD encore simples |
| **PostgreSQL central** | SQLite / MySQL | JSONB, contraintes CHECK, écritures concurrentes | schéma versionné, contraintes `purpose` et `role` | base unique : point de défaillance unique, non traité |
| **Clé API + 3 rôles** | comptes nominatifs / annuaire | pas d'annuaire d'identité sur place (§ 4.2) | `api_user`, SHA-256, 401/403 vérifiés | pas de traçabilité nominative individuelle |
| **Finalité en paramètre de requête** | finalité déduite du rôle | finalité déterminée (loi 2014-038, art. 14 ; RGPD, art. 5.1.b) | 422 hors liste fermée, 403 si non consentie | la finalité reste déclarative : elle repose sur la bonne foi de l'appelant |
| **FastAPI** | Flask | contrôle de finalité exprimé dans le schéma d'API | 4,65 contre 4,50 | écart faible : choix révisable |
| **MPI local + pivot FHIR** | MPI commercial ou registre complet (OpenCR) | périmètre du stage, données synthétiques | `engine/identity/`, 4 entités `_fhir` | MPI non certifié, à valider avant tout usage réel |
| **3 niveaux : MVP → Spark → Big Data** | Big Data direct | chaque technologie introduite par un besoin | `run_pipeline.sh`, 4/4 étapes vertes | chaque niveau ajoute un palier à maintenir |
| **Parité Pandas = Spark vérifiée** | deux logiques divergentes | montrer que le passage à l'échelle ne change pas la sémantique | VP = 307, FP = 0, FN = 420 identiques | parité vérifiée sur 3 jeux, pas sur le volume réel |

> **Lecture.** Chaque arbitrage a une raison, une preuve et un risque. Deux sont plus
> discutables que les autres : la finalité déclarée par l'appelant n'est vérifiable qu'*a
> posteriori*, par l'audit ; et l'écart entre FastAPI et Flask est trop faible pour être une
> conviction forte.

### Ce que le projet démontre

1. **La démarche progressive tient.** Le même moteur métier a été écrit une première fois en
   Pandas (niveau 1), puis porté en PySpark (niveau 2) avec une **parité stricte** vérifiée par
   test et par évaluation (VP = 307, FP = 0, FN = 420 pour les deux implantations), puis intégré
   à un Data Lake Medallion (niveau 3). Mesuré sur la même vérité terrain, le pipeline complet
   obtient les mêmes résultats (précision 1,000, rappel 0,424) : changer d'infrastructure **n'a
   pas changé la sémantique**.
2. **La prudence a un coût, et il est mesuré.** En santé, une fusion à tort est plus grave qu'une
   fusion manquée : le seuil a été positionné en conséquence. Le rappel atteint 1,000 et 0,884
   sur les jeux facile et moyen, sans faux positif ; sur le jeu difficile, il reste à 0,422, et
   la cause en est expliquée.
3. **La gouvernance est dans le système, pas à côté.** Le refus d'accès pour finalité non
   consentie est **décidé, opposé et journalisé** : un utilisateur autorisé qui demande une
   finalité non consentie reçoit un **403**, et l'audit conserve la finalité demandée et le motif
   du refus. La conformité se démontre par l'audit, pas par une intention. Le comportement est
   vérifié par des tests qui empruntent le **vrai** chemin d'authentification (clé API → rôle →
   consentement), puis sur une base peuplée de 803 patients et 2 409 avis.
4. **Le contexte dicte les choix.** VM 8 Go, Python 3.8, nœud distant instable : chaque
   contrainte a été traitée (RapidFuzz au lieu d'un modèle NLP, réplique locale de MAVIS, entrepôt
   Spark toujours sur HDFS) et consignée dans les pièges anti-régression.

> **Toutes les données manipulées sont synthétiques** (`RANDOM_SEED = 42`). Aucun identifiant réel,
> aucun dump de production n'a été exploité : la confidentialité est une exigence de conception, pas
> une contrainte contournée.

## Difficultés rencontrées

Les difficultés ont été de quatre ordres.

- **Techniques.** Onze incidents ont été rencontrés et corrigés (§ 7.3.6) : explosion de la zone
  SILVER à 11 614 lignes, écritures qui s'écrasaient d'une source à l'autre, fichiers Parquet
  corrompus sur le dossier partagé de la VM, démarrage de Spark bloqué, HiveServer2 instable,
  bibliothèque de NLP inutilisable sous Python 3.8, caractère invisible qui empêchait un script de
  compiler ; puis, en rejouant le pipeline le 30/09, un NameNode qui ne redémarrait plus, des
  dates de naissance perdues à l'extraction, des noms tronqués et, sur 12 000 patients, une passe
  exacte au coût quadratique.
- **D'environnement.** Le nœud distant MAVIS était instable, ce qui a imposé des répliques locales
  puis des sources synthétiques ; la VM, indisponible une partie de la fin du stage, n'a été
  relancée que le 30/09.
- **D'organisation.** L'équipe de développement tenait en une personne : pas de revue de code
  croisée (§ 4.1.3), et un algorithme porté deux fois, en Pandas puis en Spark, faute d'avoir
  arrêté l'échelle plus tôt (§ 4.3).
- **De méthode.** La difficulté la plus instructive n'a pas été technique : elle a été de
  **définir ce qu'on accepte de perdre** (420 paires manquées) pour ce qu'on refuse de risquer
  (une fusion de deux patients), et de pouvoir le démontrer par des chiffres reproductibles.

## Limites assumées

**Tableau 47 — Les limites du prototype.**

| Limite | État observé | Cause |
|---|---|---|
| **Rappel de 0,422 sur le jeu difficile** (0,424 pour le pipeline complet) | 420 paires manquées sur 1 057 fiches | variations à 50 % ; seuil de 0,80 prudent ; le métier n'a pas validé un seuil plus bas |
| **Consentement par type de dossier** | en cours de développement | le contrôle actuel porte sur la finalité (consultation par l'API, recherche, statistiques) |
| **Base centrale de test** | alimentée par le pipeline et par un jeu de consentements de démonstration (2 409 avis) | pas d'avis réellement recueillis ni de base de production |
| **Identifiants de patients maîtres non permanents** | `PAT-0001`, `PAT-0002`… numérotés dans l'ordre de traitement, à chaque run | une fiche nouvelle ou d'autres données décalent les numéros : un consentement enregistré pour un numéro peut alors désigner une autre personne (constaté sur la base de test le 30/09) |
| **Planification par cron non exécutée** | logique couverte par 22 tests | planification désactivée pendant les runs du 29–30/09 |
| **Formalités légales non accomplies** | conception alignée sur la loi n° 2014-038 et sur le RGPD (§ 2.1.6), sans déclaration ni autorisation auprès de la CMIL | prototype non déployé ; autorité de contrôle pas encore opérationnelle (§ 4.2) |
| **API Flask de démonstration non sécurisée** | `/api/governance/consent` sans authentification, `debug=True` | dette connue du PoC ; le contrôle de consentement est implémenté sur l'API **FastAPI** de gouvernance, qui est celle du dépôt consolidé |
| **Clés d'API hachées sans sel** | empreinte SHA-256 simple, sans sel ni itération | une même clé donne toujours la même empreinte. Les clés générées étant aléatoires et longues (64 caractères hexadécimaux), une attaque par dictionnaire reste peu réaliste ; la pratique recommandée reste un sel ou une fonction lente (`bcrypt`, déjà employé par l'interface pour les mots de passe) |
| **Précision de 1,000 : estimation optimiste** | aucun quasi-homonyme dans la vérité terrain | le générateur dégrade des fiches existantes mais ne crée jamais deux personnes presque identiques ; un module de quasi-homonymes renforcerait la preuve (§ 8.6) |
| **Volume démontré** | 25 587 fiches (12 000 patients) au plus, sur un jeu sans variation de saisie | les volumes réels de l'établissement n'étaient pas disponibles, et la VM de 8 Go limite les essais ; le parcours Big Data est **architecturé et reproductible**, pas éprouvé sur les volumes d'un établissement |
| **Comparaison de l'existant = documentaire** | aucun produit tiers installé | banc d'essai hors périmètre du stage (§ 2.4) |
| **Absents du périmètre** | déploiement en production, Docker/CI, export VM `.box` | écartés explicitement (hors stage) ; le frontend, optionnel, n'est réalisé que partiellement |

## Apports personnels

Ce stage a d'abord répondu à ce que j'en attendais : **pratiquer le Big Data**, domaine dans
lequel mon expérience était limitée. J'ai installé et fait fonctionner une chaîne complète —
HDFS, Hive, Spark — sur une machine virtuelle, et j'ai appris à mes dépens ce que la
documentation ne dit pas : l'ordre de démarrage des services, l'entrepôt Spark qu'on n'écrit
jamais sur un partage, le coût de démarrage de Spark sur de petits volumes.

Il m'a ensuite permis de relier trois niveaux souvent étudiés séparément : le **modèle
statistique** du rapprochement d'identités, l'**architecture Big Data** qui le rend exploitable à
l'échelle, et la **règle de gouvernance** qui décide qui peut lire les données. Enfin, il m'a appris une
discipline : ne rien affirmer sans preuve reproductible, et écrire une limite plutôt que de la
taire.

## Perspectives

**Court terme — compléter la chaîne existante**

1. Terminer le **consentement par type de dossier** (consultations, imagerie…), annoncé en
   introduction.
2. Rendre **permanents les identifiants de patients maîtres** : réutiliser le numéro déjà
   attribué à une fiche connue (table de correspondance) avant d'en créer un, pour que
   consentements et audit restent attachés à la même personne.
3. **Déployer la base centrale** sur un serveur de l'établissement et y enregistrer des
   consentements réellement recueillis.
4. **Calibrer le seuil et les poids** sur la vérité terrain (rappel contre précision) et
   documenter la courbe de compromis au lieu d'un point unique.
5. **Activer et observer la planification** par cron sur la VM ; l'ingestion incrémentale a été
   validée le 30/09.

**Moyen terme — fiabiliser et généraliser**

6. Ajouter les **tests d'intégration déployés** et une **CI** (GitHub Actions) exécutant générateur,
   moteur et évaluation à chaque commit.
7. Passer à l'échelle : partitionnement du blocking, consolidation *transitive* des groupes dans
   `spark_dedup.py`, calibration EM (dans l'esprit de Splink) **en complément** du score pondéré.
8. Reprendre le vrai MAVIS distant quand le nœud sera stable et rejouer le pipeline sur les
   volumes réels, en conservant les répliques synthétiques pour la démonstration.

**Long terme — ouverture**

9. Brancher la gouvernance sur un **catalogue de métadonnées** (Apache Atlas) pour la lignée
   RAW → GOLD, et sur la dé-identification pour toute sortie de données hors plateforme.
10. Généraliser le moteur à d'autres entités qu'aux patients (médecins, médicaments) : la
   traçabilité des identités se transpose telle quelle.

*Toutes les données de ce mémoire sont fictives et vérifiables dans le dépôt unique
`Mon_Memoire`.*

# Conclusion générale

## Bilan : réponse à la problématique

La problématique posée en introduction était la suivante :

> *Comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des
> données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités
> et la gouvernance des accès basée sur le consentement du patient ?*

**Tableau 47 — Les six volets de la problématique : la réponse conçue et réalisée, et la preuve vérifiable dans le dépôt.**

| Volet de la problématique | Réponse conçue et réalisée | Preuve vérifiable |
|---|---|---|
| **Intégrer** des sources hétérogènes | couche d'extraction abstraite (CSV, PostgreSQL, SQLite) → zone **RAW** en parquet HDFS, tables Hive externes, typage `STRING` assumé | 3 sources actives + 3 sources avancées (MAVIS 11 tables, MMT_DB 9 tables, CLINIQUE 4 tables) capturées [§ 3.1.2] |
| **Nettoyer / normaliser** | modèle canonique `CanonicalPatient` + schéma pivot **FHIR** (4 entités) + normalisation de genre, dates, CIN | `datalake_silver.patient_fhir` : **214 lignes** cohérentes (76 + 76 + 62) [run 07/09/2026] |
| **Dédupliquer** de façon explicable | blocking (3 buckets) + passe **exact** + passe **probabiliste** (RapidFuzz, poids 0.5 / 0.3 / 0.1 / 0.1, seuil 0.80) ; chaque décision porte méthode, score et explication | **145 masters**, **69 doublons** liés, `duplicate_rate` 32.24 % avec `mocked: false` |
| **Centraliser en conservant la traçabilité** | Medallion **RAW → SILVER → GOLD**, `patient_uuid` (empreinte SHA-2 de la source et de l'identifiant d'origine), colonnes `_source_system` / `_source_table`, `patient_identity_map` ; orchestration reprise (`pipeline_state.json`) et incrémentale (watermark) | 4/4 au run de référence (07/09), 5 étapes d'orchestration ; **214 − 69 = 145** vérifié par comptage sur le lac |
| **Gouverner par consentement** | **RBAC** (admin / analyst / viewer), clés API **SHA-256**, consentement *purpose-by-purpose* lié au `master_patient_id`, **finalité déclarée obligatoire**, refus **403** journalisé avec son motif | `access_audit` : `purpose` + `refusal_reason` ; suite de tests **102/102** (57 moteur, 45 planification et reprise), dont 401, 403 rôle, 403 consentement et 422 finalité inconnue |
| **Ne jamais fusionner sans logique explicable** | règle **structurelle** : aucun `master_patient_id` sans `match_method` (`new_master` / `exact` / `probabilistic`) | précision **1.000** et **zéro faux positif** sur easy, medium **et** hard |

### Synthèse des arbitrages

Les choix du projet se lisent comme une suite d'arbitrages, chacun posé sur des
critères explicites (§ 7.1) et chacun assorti d'un risque résiduel assumé. Cette
table est la réponse à la question « *qu'avez-vous choisi, et à la place de quoi ?* ».

**Tableau 48 — Les onze arbitrages du projet : la décision, l'alternative écartée, le critère décisif, la preuve et le risque résiduel assumé.**

| Décision | Alternative écartée | Critère décisif | Preuve | Risque résiduel |
|---|---|---|---|---|
| **RapidFuzz** + dictionnaire de synonymes | `sentence_transformers` | compatibilité Python 3.8 (C1 éliminatoire) | 2.10 vs 5.00 en arbitrage pondéré ; parité Pandas = Spark | rappel limité sur variations fortes (0.422) |
| **Seuil 0.80**, poids 0.5/0.3/0.1/0.1 | seuil unique 0.90 | en santé, une fusion à tort est plus grave qu'une fusion manquée | précision 1.000 sur les 3 niveaux, 0 FP | 420 paires manquées (faux négatifs) sur le jeu dur |
| **CIN dans la clé de blocking** | blocage sur le seul nom | couverture ~75 % des maîtres | rappel hard 0.287 → **0.422** | patients sans CIN : rappel plus faible |
| **Medallion RAW → SILVER → GOLD** | base unique « wide » | traçabilité et rejeu exigés (F1) | 4/4 étapes vertes, rejeu reproductible | tables GOLD à enrichir (`patient_events_gold` vide) |
| **PostgreSQL central** | SQLite / MySQL | JSONB, contraintes CHECK, écritures concurrentes | schéma versionné, contraintes `purpose` et `role` | base unique : point de défaillance unique, non traité |
| **Clé API + 3 rôles** | comptes nominatifs / annuaire | pas d'annuaire d'identité sur place (§ 4.2) | `api_user`, SHA-256, 401/403 vérifiés | pas de traçabilité nominative individuelle |
| **Finalité en paramètre de requête** | finalité déduite du rôle | finalité déterminée (art. 5.1.b) | 422 hors liste fermée, 403 sinon | une finalité reste déclarative : elle repose sur l'honnêteté de l'appelant |
| **FastAPI** | Flask | contrôle de finalité exprimé dans le schéma d'API | 4.65 vs 4.50 | écart faible : choix revisable |
| **MPI local + pivot FHIR** | DMP / MPI réglementaire dédié | périmètre du stage, données synthétiques | `engine/identity/`, 4 entités `_fhir` | MPI non certifié, à valider avant tout usage réel |
| **3 niveaux : MVP → Spark → Big Data** | Big Data direct | chaque technologie introduite par un besoin | `run_pipeline.sh`, 4/4 étapes vertes | chaque niveau ajoute un palier à maintenir |
| **Parité Pandas = Spark vérifiée** | deux logiques divergentes | démontrer que le scale ne change pas la sémantique | `test_spark_parity` : TP=307, FP=0, FN=420 identiques | parité vérifiée sur 3 jeux, pas sur le volume réel |

> **Ce que cette synthèse dit du projet.** Aucun arbitrage n'a été fait « par
> défaut » : chacun a une raison, une preuve et un risque associé. Les deux
> derniers points sont les plus discutables — la finalité déclarée par l'appelant
> n'est vérifiable qu'*a posteriori* par l'audit, et l'écart FastAPI/Flask est trop
> faible pour être une conviction forte. Les assumer explicitement vaut mieux
> qu'un tableau de décisions toutes présentées comme optimales.

### Ce que le projet démontre

1. **La démarche progressive tient.** Le même moteur métier a été écrit une première fois en
   Pandas (niveau 1), puis porté en PySpark (niveau 2) avec une **parité stricte** vérifiée par
   test et par évaluation (TP = 307, FP = 0, FN = 420 pour les deux implantations), puis intégré
   à un Data Lake Medallion (niveau 3). Changer d'infrastructure **n'a pas changé la sémantique**.
2. **L'explicabilité a un coût, et ce coût est maîtrisé.** En santé, une fusion à tort est plus
   grave qu'une fusion manquée : le seuil a été positionné en conséquence, et le rappel
   « easy / medium » atteint 1.000 / 0.884 sans aucun faux positif. Le rappel dur (0.422) est
   **assumé et expliqué**, pas masqué.
3. **La gouvernance est dans le système, pas à côté.** Le refus d'accès pour finalité non
   consentie est **décidé, opposé et journalisé** : un utilisateur autorisé qui demande une
   finalité non consentie reçoit un **403**, et l'audit conserve la finalité demandée et le motif
   du refus. La conformité se démontre par l'audit, pas par une intention. Le comportement est
   vérifié par des tests qui empruntent le **vrai** chemin d'authentification (clé API → rôle →
   consentement), et non en court-circuitant la sécurité.
4. **Le contexte dicte les choix.** VM 8 Go, Python 3.8, nœud distant instable : chaque
   contrainte a été traitée (RapidFuzz au lieu d'un modèle NLP, réplique locale de MAVIS, entrepôt
   Spark toujours sur HDFS) et consignée dans les pièges anti-régression [pipeline_elt.md].

> **Toutes les données manipulées sont synthétiques** (`RANDOM_SEED = 42`). Aucun identifiant réel,
> aucun dump de production n'a été exploité : la confidentialité est une exigence de conception, pas
> une contrainte contournée.

## Difficultés rencontrées

Les difficultés ont été de quatre ordres.

- **Techniques.** Sept incidents ont été rencontrés et corrigés (§ 7.3.6) : explosion de la zone
  SILVER à 11 614 lignes, écritures qui s'écrasaient d'une source à l'autre, fichiers parquet
  corrompus sur le partage de la VM, démarrage de Spark bloqué, HiveServer2 instable, modèle NLP
  inutilisable sous Python 3.8, caractère invisible qui empêchait un script de compiler.
- **D'environnement.** Le nœud distant MAVIS était instable, ce qui a imposé des répliques locales
  puis des sources synthétiques ; en fin de stage, la VM indisponible sur le poste de préparation
  n'a pas permis de rejouer la planification et l'ingestion incrémentale (§ 8.6).
- **D'organisation.** L'équipe de développement tenait en une personne : pas de revue de code
  croisée (§ 4.1.3), et un algorithme porté deux fois, en Pandas puis en Spark, faute d'avoir
  arrêté l'échelle plus tôt (§ 4.3).
- **De méthode.** La difficulté la plus instructive n'a pas été technique : elle a été de
  **définir ce qu'on accepte de perdre** (420 paires manquées) pour ce qu'on refuse de risquer
  (une fusion de deux patients), et de pouvoir le démontrer par des chiffres reproductibles.

## Limites assumées

**Tableau 49 — Les limites assumées du prototype : état observé et cause, sans dissimulation.**

| Limite | État observé | Cause |
|---|---|---|
| **Rappel 0.422 sur le jeu « hard »** | 420 faux négatifs sur 1 057 enregistrements | variations à 50 % ; seuil 0.80 conservateur ; le métier n'a pas validé un seuil plus bas |
| **`patient_events_gold` vide** | 0 ligne en intermédiaire | Encounter / Condition / Observation non rattachées à `patient_uuid` : enrichissement du mapping FHIR restant |
| **Consentement non alimenté en base centrale** | `patient_consent_gold` : 145 lignes mais `purpose` / `granted` à `NULL` | PostgreSQL central non peuplé pendant le stage. La **mécanique** est démontrée et testée (seed `provision/db/seed_governance.py` fourni, non exécuté faute d'environnement) ; la **donnée** ne l'est pas |
| **Formalités légales non accomplies** | conception alignée sur la loi n° 2014-038 et sur le RGPD (§ 2.1.6), sans déclaration ni autorisation auprès de la CMIL | prototype non déployé ; autorité de contrôle pas encore opérationnelle (§ 4.2) |
| **API Flask de démonstration non sécurisée** | `/api/governance/consent` sans authentification, `debug=True` | dette connue du PoC ; le contrôle de consentement est implémenté sur l'API **FastAPI** de gouvernance, qui est celle du dépôt consolidé |
| **Clés d'API hachées sans sel** | `engine/governance/auth.py:26` et `provision/db/seed_governance.py:57` : `hashlib.sha256(...).hexdigest()`, sans sel ni itération | l'empreinte protège la lecture directe de `api_user`, mais une même clé produit toujours la même empreinte : une table de correspondance suffit à la retrouver. Voie de correction : un sel par clé, ou une fonction lente par défaut (`bcrypt`, déjà employée côté frontend pour les mots de passe). Sans effet sur le moteur de déduplication, qui n'utilise pas ces clés |
| **Précision 1.000 = un plancher, pas une borne** | aucun cas adversariaire dans la vérité terrain | le générateur ne dégrade que des enregistrements existants et ne crée jamais deux personnes presque identiques ; un module « faux jumeaux » renforcerait la preuve (§ 8.6) |
| **Volume démontré** | quelques centaines de lignes en Silver | la VM 8 Go ne permet pas de charger les volumes réels de l'établissement ; le parcours Big Data est **architecturé et reproductible**, pas passé à l'échelle |
| **Comparaison de l'existant = documentaire** | aucun produit tiers installé | banc d'essai hors périmètre du stage (§ 2.4) |
| **Absents du périmètre** | déploiement en production, Docker/CI, export VM `.box` | écartés explicitement (hors stage) ; le frontend, optionnel, n'est réalisé que partiellement |

## Apports personnels

Ce stage a d'abord répondu à ce que j'en attendais : **pratiquer le Big Data**, domaine dans
lequel mon expérience était limitée. J'ai installé et fait fonctionner une chaîne complète —
HDFS, Hive, Spark — sur une machine virtuelle, et j'ai appris à mes dépens ce que la
documentation ne dit pas : l'ordre de démarrage des services, l'entrepôt Spark qu'on n'écrit
jamais sur un partage, le coût de démarrage de Spark sur de petits volumes.

Il m'a ensuite permis de mettre en relation trois niveaux rarement réconciliés — le **modèle
statistique** du rapprochement d'identités, l'**architecture Big Data** qui le rend exploitable à
l'échelle, et la **règle de gouvernance** qui décide qui peut le lire. Enfin, il m'a appris une
discipline : ne rien affirmer sans preuve reproductible, et écrire une limite plutôt que de la
taire.

## Perspectives

**Court terme — compléter la chaîne existante**

1. Enrichir le **mapping FHIR** (liens `Encounter` / `Condition` / `Observation` sur
   `patient_uuid`) pour alimenter `patient_events_gold` et valider un `COUNT(*) > 0`.
2. **Peupler le PostgreSQL central** en exécutant `provision/db/seed_governance.py`
   (utilisateurs, consentements mixtes accords/refus) et rejouer l'étape GOLD pour
   démontrer le refus par finalité non consentie sur données réelles du dépôt.
3. **Calibrer le seuil et les poids** sur la vérité terrain existante (rappel contre précision) et
   documenter la courbe de compromis au lieu d'un point unique.
4. **Rejouer sur la VM** la planification et l'ingestion incrémentale, écrites et testées hors
   VM.

**Moyen terme — fiabiliser et généraliser**

5. Ajouter les **tests d'intégration déployés** et une **CI** (GitHub Actions) exécutant générateur,
   moteur et évaluation à chaque commit.
6. Passer à l'échelle : partitionnement du blocking, consolidation *transitive* des clusters dans
   `spark_dedup.py`, calibration EM (dans l'esprit de Splink) **en complément** du score pondéré,
   avec double comptage explicable.
7. Reprendre le vrai MAVIS distant quand le nœud sera stable et rejouer le pipeline sur les
   volumes réels, en conservant les répliques synthétiques pour la démonstration.

**Long terme — ouverture**

8. Brancher la gouvernance sur un **catalogue de métadonnées** (Apache Atlas) pour la lignée
   RAW → GOLD, et sur la dé-identification pour toute sortie de données hors plateforme.
9. Généraliser le moteur à d'autres entités qu'aux patients (médecins, médicaments) : la
   traçabilité des identités se transpose telle quelle.

---

## Références

- `ai/memoire/contexte_projet.md` (chiffres du run 07/09/2026) ; `evaluation/evaluation_truth.md`.
- `documents/documentation/deduplication.md` (règles de fusion) ;
  `documents/documentation/pipeline_elt.md` (pièges et run) ;
  `documents/documentation/consentement_gouvernance.md` (RBAC, consentement, audit).
- `documents/rapport_stage.md` §6 (synthèse de stage, même contenu condensé).
- `documents/slides_soutenance.md` (support de démonstration).
- Annexe G : questions anticipées du jury, avec la réponse vérifiée et le paragraphe d'appui.

*Toutes les données de ce mémoire sont fictives et vérifiables dans le dépôt unique
`Mon_Memoire`.*

# Chapitre 8 — Conclusion générale

> **Statut** : rédigé (27/09/2026)

## Objectif

Conclure le mémoire : rappeler ce qui a été **conçu et réalisé**, vérifier la **réponse à la
problématique** posée au chapitre 1, exposer sans complaisance les **limites** du prototype et
formuler les **perspectives**. Ce chapitre est autonome : il peut être lu seul.

---

## 8.1 Réponse à la problématique

La problématique du chapitre 1 était la suivante :

> *Comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des
> données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités
> et la gouvernance des accès basée sur le consentement du patient ?*

**Tableau 34 — Les six volets de la problématique : la réponse conçue et réalisée, et la preuve vérifiable dans le dépôt.**

| Volet de la problématique | Réponse conçue et réalisée | Preuve vérifiable |
|---|---|---|
| **Intégrer** des sources hétérogènes | couche d'extraction abstraite (CSV, PostgreSQL, SQLite) → zone **RAW** en parquet HDFS, tables Hive externes, typage `STRING` assumé | 3 sources actives + 3 sources avancées (MAVIS 11 tables, MMT_DB 9 tables, CLINIQUE 4 tables) capturées [ch. 3 §3.1] |
| **Nettoyer / normaliser** | modèle canonique `CanonicalPatient` + schéma pivot **FHIR** (4 entités) + normalisation de genre, dates, CIN | `datalake_silver.patient_fhir` : **214 lignes** cohérentes (76 + 76 + 62) [run 07/09/2026] |
| **Dédupliquer** de façon explicable | blocking (3 buckets) + passe **exact** + passe **probabiliste** (RapidFuzz, poids 0.5 / 0.3 / 0.1 / 0.1, seuil 0.80) ; chaque décision porte méthode, score et explication | **145 masters**, **69 doublons** liés, `duplicate_rate` 32.24 % avec `mocked: false` |
| **Centraliser en conservant la traçabilité** | Medallion **RAW → SILVER → GOLD**, `patient_uuid = sha2(source|source_patient_id)`, colonnes `_source_system` / `_source_table`, `patient_identity_map` | 4/4 étapes vertes ; **214 − 69 = 145** vérifié par comptage sur le lac |
| **Gouverner par consentement** | **RBAC** (admin / analyst / viewer), clés API **SHA-256**, consentement *purpose-by-purpose* lié au `master_patient_id`, **finalité déclarée obligatoire**, refus **403** journalisé avec son motif | `access_audit` : `purpose` + `refusal_reason` ; suite de tests **54/54** dont 401, 403 rôle, 403 consentement et 422 finalité inconnue |
| **Ne jamais fusionner sans logique explicable** | règle **structurelle** : aucun `master_patient_id` sans `match_method` (`new_master` / `exact` / `probabilistic`) | précision **1.000** et **zéro faux positif** sur easy, medium **et** hard |

### Synthèse des arbitrages

Les choix du projet se lisent comme une suite d'arbitrages, chacun posé sur des
critères explicites (§2.11) et chacun assorti d'un risque résiduel assumé. Cette
table est la réponse à la question « *qu'avez-vous choisi, et à la place de quoi ?*
».

**Tableau 35 — Les onze arbitrages du projet : la décision, l'alternative écartée, le critère décisif, la preuve et le risque résiduel assumé.**

| Décision | Alternative écartée | Critère décisif | Preuve | Risque résiduel |
|---|---|---|---|---|
| **RapidFuzz** + dictionnaire de synonymes | `sentence_transformers` | compatibilité Python 3.8 (C1 éliminatoire) | 2.10 vs 5.00 en arbitrage pondéré ; parité Pandas = Spark | rappel limited sur variations fortes (0.422) |
| **Seuil 0.80**, poids 0.5/0.3/0.1/0.1 | seuil unique 0.90 | en santé, une fusion à tort est plus grave qu'une fusion manquée | précision 1.000 sur les 3 niveaux, 0 FP | 420 faux positifs manqués sur le jeu dur |
| **CIN dans la clé de blocking** | blocage sur le seul nom | couverture ~75 % des maîtres | rappel hard 0.287 → **0.422** | patients sans CIN : rappel plus faible |
| **Medallion RAW → SILVER → GOLD** | base unique « wide » | traçabilité et rejeu exigés (F1) | 4/4 étapes vertes, rejeu reproductible | tables GOLD à enrichir (`patient_events_gold` vide) |
| **PostgreSQL central** | SQLite / MySQL | JSONB, contraintes CHECK, écritures concurrentes | schéma versionné, contraintes `purpose` et `role` | base unique : point de défaillance unique, non traité |
| **Clé API + 3 rôles** | comptes nominatifs / annuaire | pas d'annuaire d'identité sur place (§4.5) | `api_user`, SHA-256, 401/403 vérifiés | pas de traçabilité nominative individuelle |
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
> qu'un tableau de décisions toutes presentations comme optimales.

## 8.2 Ce que le projet démontre

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

## 8.3 Limites assumées

**Tableau 36 — Les limites assumées du prototype : état observé et cause, sans dissimulation.**

| Limite | État observé | Cause |
|---|---|---|
| **Rappel 0.422 sur le jeu « hard »** | 420 faux négatifs sur 1 057 enregistrements | variations à 50 % ; seuil 0.80 conservateur ; le métier n'a pas validé un seuil plus bas |
| **`patient_events_gold` vide** | 0 ligne en intermédiaire | Encounter / Condition / Observation non rattachées à `patient_uuid` : enrichissement du mapping FHIR restant |
| **Consentement non alimenté en base centrale** | `patient_consent_gold` : 145 lignes mais `purpose` / `granted` à `NULL` | PostgreSQL central non peuplé pendant le stage. La **mécanique** est démontrée et testée (seed `provision/db/seed_governance.py` fourni, non exécuté faute d'environnement) ; la **donnée** ne l'est pas |
| **Droit applicable non vérifié localement** | conformité démontrée au RGPD seul | cadre juridique malgache des données de santé non étudié dans le stage (§4.5) |
| **API Flask de démonstration non sécurisée** | `/governance/consent` sans authentification, `debug=True` | dette connue du PoC ; le contrôle de consentement est implémenté sur l'API **FastAPI** de gouvernance, qui est celle du dépôt consolidé |
| **Clés d'API hachées sans sel** | `engine/governance/auth.py:26` et `provision/db/seed_governance.py:57` : `hashlib.sha256(...).hexdigest()`, sans sel ni itération | l'empreinte protège la lecture directe de `api_user`, mais une même clé produit toujours la même empreinte : une table de correspondance suffit à la retrouver. Voie de correction : un sel par clé, ou une fonction lente par défaut (`bcrypt`, déjà employée côté frontend pour les mots de passe). Sans effet sur le moteur de déduplication, qui n'utilise pas ces clés |
| **Précision 1.000 = un plancher, pas une borne** | aucun cas adversariaire dans la vérité terrain | le générateur ne dégrade que des enregistrements existants et ne crée jamais deux personnes presque identiques ; un module « faux jumeaux » renforcerait la preuve (§ 7.5) |
| **Endpoints sur données de secours** | `laboratory`, `malaria` | sources métier absentes du run de référence ; indicateur `mocked` exposé dans chaque réponse |
| **Volume démontré** | quelques centaines de lignes en Silver | la VM 8 Go ne permet pas de charger les volumes réels de l'établissement ; le parcours Big Data est **architecturé et reproductible**, pas passé à l'échelle |
| **Comparaison de l'existant = documentaire** | aucun produit tiers installé | banc d'essai hors périmètre du stage (ch. 3) |
| **Absents du périmètre** | frontend Next.js, Docker/CI, export VM `.box` | écartés explicitement (optionnel / hors stage) |

## 8.4 Perspectives

**Court terme — compléter la chaîne existante**

1. Enrichir le **mapping FHIR** (liens `Encounter` / `Condition` / `Observation` sur
   `patient_uuid`) pour alimenter `patient_events_gold` et valider un `COUNT(*) > 0`.
2. **Peupler le PostgreSQL central** en exécutant `provision/db/seed_governance.py`
   (utilisateurs, consentements mixtes accords/refus) et rejouer l'étape GOLD pour
   démontrer le refus par finalité non consentie sur données réelles du dépôt.
3. **Calibrer le seuil et les poids** sur la vérité terrain existante (rappel contre précision) et
   documenter la courbe de compromis au lieu d'un point unique.

**Moyen terme — fiabiliser et généraliser**

4. Ajouter les **tests d'intégration déployés** et une **CI** (GitHub Actions) exécutant générateur,
   moteur et évaluation à chaque commit.
5. Passer à l'échelle : partitionnement du blocking, consolidation *transitive* des clusters dans
   `spark_dedup.py`, calibration EM (dans l'esprit de Splink) **en complément** du score pondéré,
   avec double comptage explicable.
6. Reprendre le vrai MAVIS distant quand le nœud sera stable et rejouer le pipeline sur les
   volumes réels, en conservant les répliques synthétiques pour la démonstration.

**Long terme — ouverture**

7. Brancher la gouvernance sur un **catalogue de métadonnées** (Apache Atlas) pour la lignée
   RAW → GOLD, et sur la dé-identification pour toute sortie de données hors plateforme.
8. Généraliser le moteur à d'autres entités qu'aux patients (médecins, médicaments) : la
   traçabilité des identités se transpose telle quelle.

## 8.5 Bilan pour la formation

Ce stage a permis de mettre en relation trois niveaux rarement réconciliés — le **modèle
statistique** du rapprochement d'identités, l'**architecture Big Data** qui le rend exploitable à
l'échelle, et la **règle de gouvernance** qui décide qui peut le lire. La difficulté la plus
instructive n'a pas été technique : elle a été **méthodologique** — définir ce qu'on accepte de
perdre (420 paires manquées) pour ce qu'on refuse de risquer (une fusion de deux patients), et
pouvoir le démontrer par des chiffres reproductibles.

---

## 8.6 Questions anticipées

Cette section recense les objections les plus probables du jury, avec la réponse **vérifiée** et
l'endroit du mémoire où elle s'appuie. Elle ne remplace pas le développement : elle indique où le
chercher.

**1. « Votre précision vaut 1,000 : le moteur ne fusionne-t-il jamais deux patients différents ? »**
Non sur les trois jeux évalués, et ce n'est pas une garantie. Le générateur dégrade des
enregistrements existants — casse, espaces, fautes de frappe, changements de format — mais ne crée
jamais deux personnes distinctes qui se ressemblent : le cas adversariaire des faux positifs n'est
donc pas sollicité par la vérité terrain. C'est un plancher, pas une borne. § 7.5.

**2. « Un rappel de 0,422 est-il acceptable en santé ? »**
Sur le jeu « hard » (variations à 50 %), il reste 420 faux négatifs sur 1 057 enregistrements. Le
seuil 0,80 est conservateur et n'a pas été abaissé sans validation métier : l'abaisser remonte le
rappel mais réintroduit le risque de fusion de deux patients, que la priorité donnée à la précision
interdit. Levier identifié : enrichir la clé exacte (adresse), puis calibrer sur la vérité terrain.
§ 7.2, § 8.4.

**3. « Pourquoi ne pas estimer les poids et le seuil par EM, comme Splink ? »**
Pour qu'un EM ait un sens, il lui faut des données d'appariement identifiantes ; celles du stage
sont synthétiques et n'ont pas été appariées par un tiers. Les paramètres seraient donc estimés sur
des paires que le modèle n'a pas lui-même produites. Le choix retenu — un score pondéré **lisible**
(0,5 / 0,3 / 0,1 / 0,1, seuil 0,80, déclarés dans un fichier de configuration) — se justifie ligne à
ligne devant un gestionnaire de données. L'EM reste une perspective, « en complément », avec double
comptage explicable. § 3.4, § 5.3, § 8.4.

**4. « Une VM de 8 Go suffit-elle pour passer à l'échelle ? »**
Non. Le run de référence porte quelques centaines de lignes en SILVER : le parcours Big Data est
**architecturé et reproductible** (HDFS, RAW → SILVER → GOLD), pas passé à l'échelle. Le passage à
l'échelle suppose le partitionnement du blocking et la consolidation transitive des clusters.
§ 8.3, § 8.4.

**5. « Le consentement est-il réellement appliqué ? »**
La règle l'est : `purpose` est obligatoire (422), une finalité non consentie produit un refus (403),
et chaque accès comme chaque refus est journalisé — 13 cas de test dédiés à l'API de gouvernance.
La donnée ne l'était pas au moment du run : `patient_consent_gold` compte 145 lignes mais `purpose`
et `granted` sont à `NULL`, le PostgreSQL central n'ayant pas été peuplé faute d'environnement. La
distinction entre **mécanique prouvée** et **donnée absente** est maintenue partout. § 6.5, § 7.5.

**6. « Pourquoi une API Flask et une API FastAPI ? »**
L'API de données (Flask) est une surface de *reporting* sur la zone GOLD, héritée du PoC : elle ne
filtre rien. Le contrôle par rôle et par consentement est appliqué sur l'API de gouvernance
(FastAPI), seule à renvoyer 401, 403 et 422. Cette frontière est assumée, bornée et documentée.
§ 6.5, § 8.3.

**7. « Les clés d'API sont-elles vraiment protégées ? »**
La clé en clair n'est ni stockée ni exposée : la base n'en conserve qu'une empreinte SHA-256. En
revanche cette empreinte n'est **ni salée ni lente**, si bien qu'une table de correspondance
suffirait à retrouver une clé. La dette, sa cause et sa correction (sel par clé, ou fonction lente
comme `bcrypt` déjà utilisée côté frontend) sont déclarées en § 8.3.

**8. « Les 14 tests de l'API prouvent-ils le contrôle d'accès ? »**
Non : ils prouvent la joignabilité et les statuts de réponse. Le contrôle d'accès est vérifié
séparément par les 13 cas de l'API de gouvernance. § 7.4, § 7.5.

**9. « Comment garantissez-vous qu'aucun profil n'a été inventé ? »**
Le générateur est à racine fixe (`RANDOM_SEED = 42`) et toutes les données sont synthétiques. Aucune
valeur n'est estimée côté patients : un genre hors liste fermée, un CIN de longueur incohérente ou
une date illisible laissent le champ vide, et l'enregistrement bascule alors vers la voie
probabiliste. Un champ douteux ne peut donc pas corrompre une clé de rapprochement exact.
§ 4.3, § 6.1.

**10. « Pourquoi ne pas tout mettre dans PostgreSQL ? »**
Parce que les deux magasins n'ont pas le même rôle : HDFS, Hive et Spark portent le lac rejouable et
les trois zones de qualité, PostgreSQL porte l'état de référence — patients maîtres, consentements,
journal d'audit, comptes. C'est une séparation de rôles, pas une redondance. § 5.1, § 5.4.

---

## Références

- `ai/memoire/contexte_projet.md` (chiffres du run 07/09/2026) ; `evaluation/evaluation_truth.md`.
- `documents/documentation/deduplication.md` (règles de fusion) ;
  `documents/documentation/pipeline_elt.md` (pièges et run) ;
  `documents/documentation/consentement_gouvernance.md` (RBAC, consentement, audit).
- `documents/rapport_stage.md` §6 (synthèse de stage, même contenu condensé).
- `documents/slides_soutenance.md` (support de démonstration).

*Toutes les données de ce mémoire sont fictives et vérifiables dans le dépôt unique
`Mon_Memoire`.*

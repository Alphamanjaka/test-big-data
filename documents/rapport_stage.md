# Rapport de Stage — Plateforme Big Data de gestion et de gouvernance des données patients

> **Master MBDS** (spécialité Big Data) · Session Septembre 2026
> **Société d'accueil** : Madagascar Medical Technology (MMT)
> **Thème** : conception d'une plateforme Big Data de gestion et de gouvernance des données patients —
> nettoyage, déduplication et contrôle d'accès basé sur le consentement du patient.
> **Statut** : rédigé — synthèse du mémoire (chapitres 01→06), tous les chiffres vérifiables dans le dépôt.

---

## 1. Introduction

### 1.1 Contexte

MMT exploite des systèmes d'information de santé à Madagascar issus de GNU Health
(`gnuhealth_patient`, `party_party`, `gnuhealth_family`) et une plateforme hospitalière
distante (`mavis_notheme`, 11 tables dont `hms_patient`, `res_partner`, `hms_diseases`).
Comme la plupart des établissements, les systèmes successifs sont **indépendants** :
consultations, pharmacies, laboratoires, imagerie. Chacun a sa base, son format et ses
identifiants — un même patient peut ainsi être enregistré plusieurs fois sous des formes
différentes (ex. *Jean Rakoto* / *Rakoto Jean* / *J. RAKOTO*).

### 1.2 Problématique

> Comment concevoir une plateforme capable d'intégrer, nettoyer, dédupliquer et centraliser des
> données patients issues de sources hétérogènes, tout en assurant la traçabilité des identités et
> la gouvernance des accès basée sur le consentement du patient ?

Trois conséquences concrètes : **dispersion** (pas de vue globale), **hétérogénéité**
(identifiants, libellés, formats) et **absence de gouvernance** (qui accède à quoi, pour quelle
finalité).

### 1.3 Démarche

Approche progressive, chaque technologie introduite **par besoin** :

```
PROBLÈME MÉTIER → MVP PANDAS+PG → VALIDATION GROUND-TRUTH → SPARK (parité) → BIG DATA MEDALLION
```

Le projet est la **fusion consolidée** de deux PoC complémentaires — `datalake_mavis`
(architecture Big Data : VM Hadoop/Hive/Spark, ELT 4 étapes, FHIR, API Flask) et `test_bigdata`
(déduplication explicable, consentement/audit, évaluation ground-truth) — réunis dans un **dépôt
unique** autonome.

---

## 2. Conception retenue

### 2.1 Architecture en trois niveaux

| Niveau | Contenu | Justification |
|---|---|---|
| **1 — MVP** | CSV + Pandas + PostgreSQL : extraction, nettoyage, déduplication, master patient | résoudre le problème métier au plus simple |
| **2 — Spark** | PySpark local, résultats **strictement identiques** au MVP (parité vérifiée) | passer à l'échelle sans changer la sémantique |
| **3 — Big Data** | Data Lake HDFS + Hive + Spark, pipeline ELT Medallion (RAW→SILVER→GOLD), API | traiter des volumes réels en architecture médicale |

### 2.2 Déduplication explicable (Master Patient Index)

- **Modèle canonique** `CanonicalPatient` (source, id source, nom, naissance, CIN, ville de
  naissance, adresse, genre) normalisant casse, accents, formats de dates, CIN et genre.
- **Blocking** : 3 index de candidats (préfixe nom, date de naissance ISO, CIN) pour éviter la
  comparaison quadratique.
- **Deux passes** : *exact* (clé partagée, ou naissance+CIN identiques) puis *probabiliste*
  (score pondéré — nom 0.5 · naissance 0.3 · CIN 0.1 · ville de naissance 0.1, seuil **0.80**).
- Chaque décision porte `master_patient_id`, `method` (`exact`/`probabilistic`/`new_master`),
  `score` et `explanation` — **jamais de fusion sans logique justifiable**.
- Implémentation **Pandas et PySpark**, résultats strictement identiques (parité vérifiée).

### 2.3 Gouvernance et consentement

- **RBAC** : rôles `admin` / `analyst` / `viewer`, clés API hachées SHA-256 en base.
- **Consentement *purpose-by-purpose*** : table `consent` liée au `master_patient_id` ; un accès
  est refusé **même à un utilisateur autorisé** si la finalité n'est pas consentie.
- **Audit** : chaque tentative (autorisée ou refusée) journalisée dans `access_audit`.
- **Schéma pivot FHIR** (Patient, Encounter, Condition, Observation) côté pipeline ELT.

---

## 3. Réalisation

### 3.1 Pipeline ELT Medallion (4 étapes)

`run_pipeline.sh` orchestre extraction RAW → mapping FHIR → SILVER → GOLD, avec arrêt sur erreur
et logs `elt.log`.

### 3.2 Résultats du run de référence (VM, 07/09/2026)

| Étape | Résultat vérifié |
|---|---|
| Pipeline | **4/4 vert** (RAW → SILVER → GOLD) |
| SILVER `patient_fhir` | **214** lignes (76 pharmacy + 76 consultation + 62 imaging) |
| Masters | **145** distincts ; **69** doublons liés (`is_duplicate`), `match_method=exact` |
| Gouvernance API | `duplicate_rate` **32.24 %** (`mocked: false`) |
| GOLD | `patient_consent_gold` **145** lignes ; `patient_events_gold` 0 ligne (interim attendu) |
| API données | `test_api.py` **14/14 PASS** sur données réelles (`RMA_USE_MOCK=false`) |

### 3.3 Difficultés réelles et résolutions

| Problème | Cause | Correctif |
|---|---|---|
| SILVER explosait à 11 614 lignes | `patient_uuid` capturé par le mapping FHIR dynamique → `source_patient_id` NULL → jointure 76×76 | `patient_uuid` exclu du mapping dynamique, écriture `overwrite` unique par table |
| Parquet corrompu sur vboxsf | warehouse Spark sur le partage | warehouse **toujours sur HDFS** |
| Spark bloqué | `JAVA_HOME` avec `\bin` en trop | normalisation `_resolve_java_home()` |
| NLP lourd | `sentence_transformers` crash Python 3.8 | RapidFuzz + dictionnaire de synonymes |

---

## 4. Évaluation ground-truth

Trois jeux synthétiques (500 patients maîtres, ~1 057 enregistrements, seed 42) issus des mêmes
masters, seul le **taux de variation** change (10 % / 30 % / 50 %). La vérité terrain
(`identity_mapping.csv`) est **réservée à l'évaluation** — jamais fournie à l'algorithme.
Métriques **par paires** (précision / rappel / F1).

| Niveau | Précision | Rappel | F1 | Lecture |
|---|---|---|---|---|
| easy (10 %) | **1.000** | **1.000** | **1.000** | tous les doublons reconnus, zéro fausse fusion |
| medium (30 %) | **1.000** | 0.884 | 0.939 | 84 paires manquées, aucune fusion à tort |
| hard (50 %) | **1.000** | 0.422 | 0.594 | jeu volontairement dur ; 420 paires manquées |

**Résultat-clé** : **zéro faux positif sur les trois niveaux** — l'algorithme ne fusionne jamais à
tort, propriété essentielle en santé. L'introduction de la **clé CIN** (~75 % des maîtres) a relevé
le rappel hard de 0.287 (07/09) à **0.422** sans le moindre faux positif. La **parité
Pandas = Spark** est parfaite à chaque niveau (TP=307, FP=0, FN=420 pour les deux).

**Tests** : moteur **23/23 PASS** (matcher 12 · consent 3 · canonique 8) ; générateur **44/44** ;
MVP 20 ; API données **14/14 PASS** — soit une pyramide unitaire → intégration → système complète.

---

## 5. Limites identifiées (honnêteté du PoC)

| Limite | Observation | Cause / piste |
|---|---|---|
| Rappel hard 0.422 | 420 faux négatifs / 1 057 | variations 50 % ; seuil 0.80 conservateur → abaisser le seuil ou enrichir la clé si le métier l'accepte |
| `patient_events_gold` vide en intermédiaire | 0 ligne | jointures FHIR non rattachées (Encounter/Condition sans `patient_uuid`) → enrichir le mapping |
| Consentement non alimenté | `granted`/`purpose` NULL | PostgreSQL central non peuplé en interim (mécanique démontrée, données à venir) |
| Endpoints mock | `laboratory`, `malaria` | sources métier absentes du run final ; flag `mocked` tracé |
| Frontend, Docker/CI, export VM | — | hors périmètre stage (assumés) |

---

## 6. Conclusion et perspectives

La plateforme répond à la problématique : **centraliser** (Data Lake Medallion RAW→SILVER→GOLD),
**nettoyer et standardiser** (canonique + FHIR), **dédupliquer de façon explicable** (exact +
probabiliste, zéro fusion à tort, parité Pandas/Spark) et **gouverner les accès par
consentement** (purpose-by-purpose, RBAC, audit). Le tout sur **données exclusivement
synthétiques**.

Perspectives : enrichir le mapping FHIR (rattacher encounters/conditions/observations) pour
alimenter `patient_events_gold`, calibrer seuil/poids sur la base du ground-truth, peupler le
consentement central, et engager un passage à l'échelle réel (volume + tests CI).

---

*Tous les chiffres se rapportent à des données fictives et sont vérifiables dans le dépôt unique
`Mon_Memoire` — voir `ai/memoire/contexte_projet.md` et `evaluation/evaluation_truth.md`.*
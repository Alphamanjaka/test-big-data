# Chapitre 1 — Présentation du stage

## 1.1 Présentation de l'entreprise

La société **Madagascar Medical Technology (MMT)** a été créée en 2009 afin de répondre aux
besoins des professionnels de la santé à Madagascar. Son secteur d'activité englobe la
distribution et la maintenance de matériels biomédicaux, la fourniture de consommables, ainsi
que la gestion de stock des établissements partenaires.

L'entreprise est composée d'une équipe dynamique et passionnée par le domaine de l'ingénierie
biomédicale, prête à accompagner l'évolution technologique du secteur. Dans le cadre de son
développement, MMT a conclu une convention avec Siemens Healthineers, qui lui confère le statut
de *Business Partner* à Madagascar, avec un rattachement direct à la branche sud-africaine de
Siemens Healthineers.

Depuis 2024, l'entreprise a ouvert un **département Recherche et Développement**, chargé de la
gestion des systèmes d'information médicale ainsi que des infrastructures et réseaux
informatiques. C'est dans ce département que s'est déroulé le stage.

Les systèmes d'information médicale rencontrés au cours du stage illustrent ce périmètre : des
bases de gestion hospitalière fondées sur GNU Health (tables `gnuhealth_patient`,
`party_party`, `gnuhealth_family` de la base MMT_DB) et une plateforme de gestion hospitalière
distante (`mavis_notheme`, 11 tables retenues dont `hms_patient`, `res_partner`,
`hms_diseases`) [cahier_des_charges.md §1 et §6]. Ils sont décrits au chapitre 3.

## 1.2 Présentation du sujet et objectifs

### 1.2.1 Contexte métier

Le cas de référence de la plateforme en donne un exemple concret : trois fiches, **sous des formes
différentes**, désignent une seule et même personne [deduplication.md §7].

```text
Pharmacie     → Jean Rakoto · CIN 101 02404 5 · 1990-01-10
Consultation  → Rakoto Jean · 101024045 · 10/01/1990
Imagerie      → J. RAKOTO · 101024045 · 1990/01/10
```

Cette situation pose trois problèmes concrets :

1. **Dispersion** : les données d'un patient sont réparties entre plusieurs fichiers et bases,
   sans vue globale.
2. **Hétérogénéité** : identifiants, libellés et formats diffèrent (le genre apparaît tour à tour
   sous les formes `H/F`, `male/female`, `Homme/femme` selon la source) — voir chapitre 3.
3. **Absence de gouvernance** : rien ne garantit qui peut accéder à quelle donnée, pour quelle
   finalité, et dans quelles conditions.

### 1.2.2 Objectifs

Six mots reviennent dans tous les chapitres :

- **ELT** : on **charge** d'abord les fichiers tels quels, on **transforme** ensuite — l'inverse
  d'un ETL classique, où l'on transforme avant d'écrire.
- **Medallion** : ranger la donnée dans trois zones de qualité croissante — **RAW** (brut,
  inchangé) → **SILVER** (nettoyé, standardisé) → **GOLD** (prêt à analyser).
- **MPI** : l'annuaire qui reconnaît qu'un patient est le même d'un système à l'autre, et lui
  attribue un identifiant unique.
- **Déduplication** : rapprocher les fiches identiques dispersées dans plusieurs systèmes, en
  pouvant **expliquer** chaque fusion.
- **RBAC** : les droits d'accès sont portés par un **rôle** (`admin`, `analyst`, `viewer`), pas
  par une personne.
- **Consentement par finalité** : le patient autorise **un usage précis** (`api_access`,
  `research`, `analytics`) — c'est le *purpose-by-purpose*.

**Tableau 2 — Les six objectifs du cahier des charges et l'illustration concrète retenue pour chacun d'eux.**

| # | Objectif | Illustration concrète |
|---|---|---|
| 1 | **Centraliser** les données dans une architecture Big Data | pipeline ELT Medallion RAW → SILVER → GOLD [cahier_des_charges.md §4.1] |
| 2 | **Nettoyer et standardiser** selon un modèle commun | modèle canonique `CanonicalPatient` côté déduplication, schéma pivot FHIR côté ELT [cahier_des_charges.md §7] |
| 3 | **Dédupliquer** avec une logique toujours explicable | master patient, identity map, score + méthode + seuil [cahier_des_charges.md §4.2] |
| 4 | **Gouverner les accès** | rôles (RBAC), consentement *purpose-by-purpose*, audit d'accès, clés API hachées [cahier_des_charges.md §4.3] |
| 5 | **Visualiser** les indicateurs | vues de gouvernance : déduplication et consentement (frontend optionnel) [cahier_des_charges.md §4.5] |
| 6 | **Évaluer** la déduplication | vérité terrain (ground truth), précision / rappel / F1 [cahier_des_charges.md §4.4 / §8] |

Les données manipulées sont **exclusivement synthétiques** : la confidentialité est un actif du
projet, pas un obstacle de démonstration.

### 1.2.3 Enjeux et risques

Les conséquences de la dispersion sont des risques d'erreurs médicales (dossier éclaté), des
difficultés d'analyse (agrégats faux en présence de doublons) et des failles de
confidentialité. Le sujet porte donc trois enjeux, et chacun a son risque propre, que la
solution doit maîtriser plutôt qu'ignorer.

**Tableau 3 — Les enjeux métier du sujet, le risque associé à chacun, et le chapitre où la maîtrise de ce risque est démontrée.**

| Enjeu | Risque à maîtriser | Où la maîtrise est démontrée |
|---|---|---|
| **Un dossier patient complet** : retrouver toutes les fiches d'une même personne | **fusionner à tort** deux personnes distinctes — l'erreur la plus grave en santé, plus grave qu'une fusion manquée | précision 1.000, zéro faux positif sur les trois jeux évalués (§ 8.5) |
| **Des indicateurs justes** : compter des patients, pas des fiches | des agrégats faussés par les doublons, ou une fusion impossible à justifier après coup | chaque fusion porte méthode, score et explication (§ 7.2.3) |
| **Des accès maîtrisés** : chaque lecture a un demandeur, une finalité et un consentement | exposer une donnée sans consentement, ou refuser sans trace | refus 403 journalisé avec son motif (§ 8.4) |
| **Une démarche reproductible** : pouvoir rejouer et vérifier chaque résultat | dépendre d'une machine ou d'un réseau instable, ou de données réelles non partageables | données synthétiques à graine fixe, pipeline rejouable (§ 4.1.5) |

## Conclusion et transition

Le cadre est posé : une entreprise qui a ouvert un département dédié aux systèmes d'information
médicale, un sujet qui répond à un problème concret de dispersion des données, et des enjeux
dont les risques sont identifiés. Avant d'examiner les systèmes de MMT, le chapitre 2 établit
l'**état de l'art** : les notions de référence, les critères de comparaison et les solutions
existantes.

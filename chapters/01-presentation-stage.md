# Chapitre 1 — Présentation du stage

## 1.1 Présentation de l'entreprise

La société **Madagascar Medical Technology (MMT)** a été créée en 2009 afin de répondre aux
besoins des professionnels de la santé à Madagascar. Son secteur d'activité englobe la
distribution et la maintenance de matériels biomédicaux, la fourniture de consommables, ainsi
que la gestion de stock des établissements partenaires.

L'entreprise réunit une équipe spécialisée en ingénierie biomédicale. Dans le cadre de son
développement, MMT a conclu une convention avec Siemens Healthineers, qui lui confère le statut
de *Business Partner* à Madagascar, avec un rattachement direct à la branche sud-africaine du
groupe.

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

Le cas de référence de la plateforme illustre le problème : trois fiches, **sous des formes
différentes**, désignent une seule et même personne.

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

Six notions reviennent dans tout le mémoire :

- **ELT** : on **charge** d'abord les données telles quelles, on les **transforme** ensuite ; un
  ETL classique transforme avant d'écrire.
- **Medallion** : ranger la donnée dans trois zones de qualité croissante — **RAW** (brut,
  inchangé) → **SILVER** (nettoyé, standardisé) → **GOLD** (prêt à analyser).
- **MPI** : l'annuaire qui reconnaît qu'un patient est le même d'un système à l'autre, et lui
  attribue un identifiant unique.
- **Déduplication** : rapprocher les fiches d'une même personne dispersées dans plusieurs
  systèmes, en pouvant **expliquer** chaque fusion.
- **RBAC** : les droits d'accès sont portés par un **rôle** (`admin`, `analyst`, `viewer`), pas
  par une personne.
- **Consentement par finalité** : le patient autorise **un usage précis** (consultation par
  l'API, recherche, statistiques), jamais un accès global.

Le cahier des charges (§ 3) fixe six objectifs :

**Tableau 2 — Les six objectifs du cahier des charges.**

| # | Objectif | Illustration concrète |
|---|---|---|
| 1 | **Centraliser** les données dans une architecture Big Data | pipeline ELT Medallion RAW → SILVER → GOLD |
| 2 | **Nettoyer et standardiser** selon un modèle commun | modèle canonique du patient pour la déduplication, schéma pivot FHIR pour le pipeline |
| 3 | **Dédupliquer** avec une logique toujours explicable | patient maître, table de correspondance, score, méthode et seuil |
| 4 | **Gouverner les accès** | rôles (RBAC), consentement par finalité, journal d'accès, clés d'API hachées |
| 5 | **Visualiser** les indicateurs | vues de déduplication et de consentement (interface web optionnelle) |
| 6 | **Évaluer** la déduplication | vérité terrain, précision, rappel et F1 |

Toutes les données manipulées sont **synthétiques**.

### 1.2.3 Enjeux et risques

La dispersion des données entraîne des risques d'erreurs médicales (dossier éclaté), des
analyses faussées (un patient compté plusieurs fois) et des failles de confidentialité. Le sujet
porte ainsi quatre enjeux, chacun avec un risque que la solution doit maîtriser.

**Tableau 3 — Les enjeux, leur risque et la section où sa maîtrise est démontrée.**

| Enjeu | Risque à maîtriser | Où la maîtrise est démontrée |
|---|---|---|
| **Un dossier patient complet** : retrouver toutes les fiches d'une même personne | **fusionner à tort** deux personnes distinctes, l'erreur la plus grave en santé | précision de 1,000, aucun faux positif sur les trois jeux évalués (§ 8.5) |
| **Des indicateurs justes** : compter des patients, pas des fiches | des agrégats faussés par les doublons, ou une fusion impossible à justifier après coup | chaque fusion porte sa méthode, son score et son explication (§ 7.2.3) |
| **Des accès maîtrisés** : chaque lecture a un demandeur, une finalité et un consentement | exposer une donnée sans consentement, ou refuser sans trace | refus 403 journalisé avec son motif (§ 8.4) |
| **Une démarche reproductible** : pouvoir rejouer et vérifier chaque résultat | dépendre d'une machine, d'un réseau instable ou de données réelles non partageables | données synthétiques à graine fixe, pipeline rejouable (§ 4.1.5) |

## Conclusion et transition

Le cadre est posé : une entreprise dotée d'un département consacré aux systèmes d'information
médicale, un problème concret de dispersion des données, et des enjeux dont les risques sont
identifiés. Le chapitre 2 établit l'**état de l'art** : les notions de référence, les critères de
comparaison et les solutions existantes.

# Slides de Soutenance — Plateforme Big Data de gestion et de gouvernance des données patients

> **Format : 13 slides · 20 min d'exposé, démonstration comprise** (le jury dispose d'un créneau de
> questions séparé). Budget **planifié 16 min + 4 min de marge** (transitions, développement à
> l'oral, aléas) : le texte des slides n'est qu'un squelette, 4 min restent à dire.
> Message **métier** et message **technique** séparés (règle `ai/memoire/README.md`). Chaque slide
> porte sa durée, l'**image à projeter** et sa **preuve** (fichier vérifiable).
> Images dans `figures/` (rendues par `scripts/dev/render_mermaid_figures.py`, versionnées).
> À convertir dans l'outil de présentation au choix (PowerPoint / Google Slides / reveal.js).

| Partie | Slides | Durée |
|---|---|---|
| A — Message métier | S1 → S4 | 4:00 |
| B — Message technique | S5 → S9 | 6:00 |
| C — Démonstration (vidéo) | S10 | 4:00 |
| D — Conclusion | S11 → S13 | 2:00 |
| **Planifié** | | **16:00** |
| **Marge** | transitions, développement, aléas | **4:00** |
| **Total** | | **20:00** |

---

## Partie A — Message métier (4:00)

### S1. Titre (0:30)
**Concevoir une plateforme Big Data de gestion et de gouvernance des données patients**
Nettoyage · Déduplication · Contrôle d'accès par consentement
Stage M2 MBDS — Madagascar Medical Technology — Octobre 2026
*Support : page de garde du rapport ; le message d'ouverture pointe la double finalité (qualité + confidentialité).*

### S2. Le problème : un même patient, plusieurs systèmes (1:15)
```
Pharmacie     → Jean Rakoto · CIN 101 02404 5
Consultation  → Rakoto Jean · 101024045
Imagerie      → J. RAKOTO
```
- Trois systèmes indépendants, trois formats, trois identifiants — et **trois colonnes pour le même
  champ** (`sexe` / `genre` / `sex`).
- Chaque base est **intègre avec elle-même** (jointure MAVIS vérifiée 9 791 / 9 791) : le problème
  n'est pas la qualité, c'est l'absence d'équivalent **entre** les bases.
- Conséquences : dossier éclaté, agrégats faux, accès non maîtrisés.
- **Image à projeter : `figures/fig-1.png`** — trois systèmes isolés, cinq manques, quatre réponses.
- *Support : `chapters/01-presentation-stage.md` §1.2.1, `chapters/03-existant-solution.md` §3.1 ; preuve = enregistrements du générateur synthétique.*

### S3. La promesse de la plateforme (1:00)
1. **Centraliser** dans un Data Lake (zones RAW → SILVER → GOLD).
2. **Dédupliquer** de façon **explicable** (chaque fusion justifiée par un score).
3. **Gouverner les accès** par **consentement purpose-by-purpose** + audit.
- Données **exclusivement synthétiques** — la confidentialité est un actif de démonstration.
- *Support : objectifs `documents/cahier_des_charges.md` §3.*

### S4. Démarche : chaque technologie par besoin (1:15)
```
PROBLÈME MÉTIER → MVP (Pandas+PG) → VALIDATION (ground-truth) → SPARK (parité) → BIG DATA MEDALLION → GOUVERNANCE (consentement + audit)
```
- Pas de « Big Data pour le Big Data » : le besoin précède l'outil.
- Deux PoC fusionnés en un seul dépôt autonome.
- **Image à projeter : `figures/fig-2.png`** — la démarche en six étapes.
- *Support : `chapters/03-existant-solution.md` §3.3.*

---

## Partie B — Message technique (6:00)

### S5. Architecture cible (1:30)
- Pipeline Medallion RAW → SILVER → GOLD sur HDFS/Hive/Spark.
- Moteur de dédup `engine/` (Pandas + Spark) branché en SILVER, master patient + identity map.
- PostgreSQL central (master, consent, audit, clés API) ; API données + gouvernance.
- **Image à projeter : `figures/fig-4.png`** — l'architecture en trois niveaux.
- *Support : `chapters/06-architecture.md` §6.1 ; `diagramme_flux_donnees.md` ; `figures/fig-5.png` en réserve pour les questions.*

### S6. Déduplication explicable (MPI) (1:30)
- **Blocage** (blocking) : 3 index bornés (préfixe de nom, naissance, CIN).
- **Exact** (clé partagée / naissance+CIN) puis **probabiliste** (RapidFuzz).
- Pondérations 0.5/0.3/0.1/0.1 · seuil **0.80** — déclarés en YAML, pas dans le code.
- **Aucune valeur n'est devinée** : un genre hors liste ou un CIN mal formé reste vide et renvoie
  l'enregistrement vers la branche probabiliste — un champ douteux ne peut pas corrompre une clé exacte.
- Décision = `master_patient_id` + `method` + `score` + `explanation` → **jamais de fusion arbitraire**.
- *Support : `chapters/07-conception.md` §7.2.3 ; `config/deduplication.yaml` ; `engine/identity/canonical.py`.*
- *Image de réserve pour les questions : `figures/fig-6.png`.*

### S7. Résultats du run de référence (VM) (1:00)
| Élément | Valeur vérifiée |
|---|---|
| Pipeline | 4/4 au run de référence · orchestration en 5 étapes (reprise + incrémentale) |
| SILVER `patient_fhir` | 214 lignes (76+76+62) |
| Masters / doublons | 145 / 69 (exact) · duplicate_rate 32.24 % |
| API données | 3/3 PASS |
- **Image à projeter : `figures/fig-8.png`** — le pipeline ELT en cinq étapes (la 1re, préparatoire, est idempotente).
- *Support : `ai/memoire/contexte_projet.md` ; logs `elt.log` ; `test_api.py` ; `chapters/07-conception.md` §7.3.2.*

### S8. Évaluation ground-truth (1:15)
- 3 jeux easy/medium/hard (500 maîtres, ~1 057 enregistrements, seed 42) ; vérité terrain réservée.
- **Zéro faux positif sur les trois jeux évalués** → jamais fusionner à tort dans cette campagne.
- Ce zéro est un **plancher, pas une borne** : le générateur ne crée pas d'homophones quasi
  identiques, le cas adversariaire n'est pas sollicité.
- Clé CIN : rappel hard **0.287 → 0.422**, toujours sans faux positif. Rappeler = 0.884 (medium).
- Parité : **décisions identiques** Pandas = Spark sur les jeux testés (TP=307, FP=0, FN=420).
- *Support : `evaluation/evaluation_truth.md` ; `chapters/08-tests.md` §8.5.*
- *Image de réserve : `figures/fig-9.png` — la stratégie de test.*

### S9. Difficultés réelles et honnêteté (0:45)
- Incident : SILVER 11 614 lignes (mapping FHIR capturant `patient_uuid`) → corrigé et documenté
  comme piège anti-régression.
- Dettes assumées, non masquées : `patient_events_gold` **0 ligne** (jointures à enrichir) ;
  consentement GOLD non alimenté en base (la mécanique est prouvée, pas la donnée) ; l'API Flask
  reste une surface de **reporting**, le contrôle par rôle et consentement s'applique à l'API de
  gouvernance.
- Les 16 tests de l'API de gouvernance sont un **test d'intégration** (statuts : 401, 403, 422) :
  la joignabilité est prouvée, et le contrôle d'accès y est vérifié par des cas dédiés (rôle,
  consentement, finalité).
- *Support : `chapters/07-conception.md` §7.3.5-7.3.6 ; `chapters/08-tests.md` §8.1 et §8.6.*

---

## Partie C — Démonstration (4:00)

### S10. Démonstration en vidéo (4:00)
> **Pas de démonstration en direct** : une vidéo de **3:30** enregistrée à l'avance, commenting
> 0:30. Le public n'a donc **rien à installer** et la VM n'est pas un point de failure le jour J.
> Les commandes ci-dessous sont celles **à filmer**, avec les chemins réels du dépôt unifié.

| Plan | Contenu à filmer | Commande | Durée |
|---|---|---|---|
| 1 | Les 102 tests passent (moteur + gouvernance + planification/reprise) | `.venv\Scripts\python -m pytest projet/code-source/tests -q` | 0:45 |
| 2 | L'évaluation hard sort ses métriques | `.venv\Scripts\python projet\code-source\evaluation\evaluate_engine.py --level hard` | 0:45 |
| 3 | Le pipeline Medallion tourne bout en bout (5 étapes) | `bash projet/code-source/provision/scripts/run_pipeline.sh` | 1:00 |
| 4 | **Tableau de bord `/dashboard`** : zones Medallion, étapes, planification cron, fraîcheur des sources | lancer `front-optional/`, API FastAPI sur le port 8000 | 0:30 |
| 5 | **Repli** si la vidéo ne se lance pas : compteurs figés | slide de captures datées (voir ci-dessous) | 0:30 |

- **À enregistrer à la maison, VM allumée** : les plans 3 et 4 exigent la VM Vagrant et `front-optional`,
  indisponibles sur le poste de préparation.
- Le plan 1 doit être **rejoué juste avant l'enregistrement** pour que l'écran montre 102/102.
- *Slide de repli obligatoire* (à construire dans le même deck) : capture du run de référence,
  `patient_fhir` **214 lignes** / **145 masters** / **69 doublons** / **32.24 %**, extrait de
  `evaluation_truth.md`, sortie de l'API.
- Préalables pour le public : dépôt `Mon_Memoire`, venv Python 3.8+ (`pyproject.toml`).
- *Support : `projet/code-source/README.md` (démarrage rapide).*

---

## Partie D — Conclusion (2:00)

### S11. Réponse à la problématique (1:00)
Centraliser, nettoyer/standardiser, **dédupliquer de façon explicable**, **gouverner par
consentement** — sur données synthétiques, architecture Big Data, dépôt unique.

### S12. Perspectives (0:45)
- Enrichir le mapping FHIR (encounters/conditions/observations → `patient_events_gold`).
- Calibrer seuil/poids via le ground-truth ; peupler le consentement central.
- Ajouter un générateur d'homophones pour solliciter enfin le cas adversariaire des faux positifs.
- Passage à l'échelle (volume, CI), export VM.

### S13. Merci / questions (0:15)
- Recontact + référence du dépôt unique et du rapport de stage.

---

## Images : ce qui est projeté, ce qui ne l'est pas

| Figure | Slide | Contenu | Décision |
|---|---|---|---|
| `figures/fig-1.png` | S2 | trois systèmes isolés, cinq manques | **projeté** — le meilleur visuel « problème » |
| `figures/fig-2.png` | S4 | la démarche en six étapes | **projeté** |
| `figures/fig-4.png` | S5 | l'architecture en trois niveaux | **projeté** |
| `figures/fig-8.png` | S7 | le pipeline ELT en cinq étapes | **projeté** |
| `figures/fig-5.png` | — | le chemin d'une donnée | **exclu** : à 5,7 pt même en page paysage, illisible sur un vidéoprojecteur. Reste dans le mémoire, et ne passe qu'en pause zoomée dans la vidéo. |
| `figures/fig-6.png`, `figures/fig-3.png`, `figures/fig-9.png` | — | état de l'art, générateur, stratégie de test | **réserves** pour les questions du jury |

## Note de préparation

- [ ] **Enregistrer la vidéo (3:30)** dans l'ordre des 5 plans, VM allumée, depuis la racine du dépôt
      `Mon_Memoire`. Chronométrer le film : au-delà de 4 min, couper les plans 3 et 4.
- [ ] Vérifier la **lecture du `.mp4` sur le poste de la salle** (codec, plein écran, chemin) et
      garder le fichier dans le même dossier que les slides.
- [ ] Construire la **slide de repli** (captures d'écran datées du run VM et de la sortie API) :
      c'est le filet de sécurité si la vidéo ne se lance pas.
- [ ] **Ne pas projeter la figure 6** (5,7 pt) ; la réserver à une pause zoomée dans la vidéo.
- [ ] Chaque chiffre affiché doit reposer sur une **preuve** (règle AGENTS : ne jamais annoncer un
      résultat sans preuve) — les supports de chaque slide donnent le fichier vérifiable.
- [ ] Les chiffres de S7, S8 et S9 sont alignés sur `chapters/07-conception.md` et
      `chapters/08-tests.md` : toute modification du mémoire avant la soutenance doit être
      répercutée ici.

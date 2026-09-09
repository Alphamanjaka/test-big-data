# Slides de Soutenance — Plateforme Big Data de gestion et de gouvernance des données patients

> **Esquisse (~15 slides, 15 min conseillées + 10 min questions).** Message **métier** et message
> **technique** séparés (règle `ai/memoire/README.md`). Chaque slide précise son support / preuve.
> Durées indicatives. À convertir dans l'outil de présentation au choix (PowerPoint / Google Slides / reveal.js).

---

## Partie A — Message métier (4 min)

### S1. Titre (30 s)
**Concevoir une plateforme Big Data de gestion et de gouvernance des données patients**
Nettoyage · Déduplication · Contrôle d'accès par consentement
Stage M2 MBDS — Madagascar Medical Technology — Septembre 2026
*Support : page de garde du rapport ; le message d'ouverture pointe la double finalité (qualité + confidentialité).*

### S2. Le problème : un même patient, plusieurs systèmes (1 min)
```
Pharmacie     → Jean Rakoto · CIN 101 02404 5
Consultation  → Rakoto Jean · 101024045
Imagerie      → J. RAKOTO
```
- Trois systèmes indépendants, trois formats, trois identifiants.
- Conséquences : dossier éclaté, agrégats faux, accès non maîtrisés.
- *Support : `chapters/01-introduction.md` §1.2 ; preuve = enregistrements du générateur synthétique.*

### S3. La promesse de la plateforme (1 min)
1. **Centraliser** dans un Data Lake (zones RAW → SILVER → GOLD).
2. **Dédupliquer** de façon **explicable** (chaque fusion justifiée par un score).
3. **Gouverner les accès** par **consentement purpose-by-purpose** + audit.
- Données **exclusivement synthétiques** — la confidentialité est un actif de démonstration.
- *Support : objectifs `documents/cahier_des_charges.md` §3.*

### S4. Démarche : chaque technologie par besoin (1.5 min)
```
PROBLÈME MÉTIER → MVP (Pandas+PG) → VALIDATION (ground-truth) → SPARK (parité) → BIG DATA MEDALLION
```
- Pas de « Big Data pour le Big Data » : le besoin précède l'outil.
- Deux PoC fusionnés en un seul dépôt autonome.
- *Support : `chapters/01-introduction.md` §1.4 + schéma mermaid.*

---

## Partie B — Message technique (7 min)

### S5. Architecture cible (2 min)
- Pipeline Medallion RAW → SILVER → GOLD sur HDFS/Hive/Spark.
- Moteur de dédup `engine/` (Pandas + Spark) branché en SILVER, master patient + identity map.
- PostgreSQL central (master, consent, audit, clés API) ; API données + gouvernance.
- *Support : `diagramme_flux_donnees.md` (schéma Mermaid) ; `chapters/04-conception.md` §4.1.*

### S6. Déduplication explicable (MPI) (2 min)
- **Blocage** (blocking) : 3 index bornés (nom, naissance, CIN).
- **Exact** (clé partagée / naissance+CIN) puis **probabiliste** (RapidFuzz).
- Pondérations 0.5/0.3/0.1/0.1 · seuil **0.80**.
- Décision = `master_patient_id` + `method` + `score` + `explanation` → **jamais de fusion arbitraire**.
- *Support : `chapters/04-conception.md` §4.3 ; `config/deduplication.yaml`.*

### S7. Résultats run de référence (VM) (1 min)
| Élément | Valeur vérifiée |
|---|---|
| Pipeline | 4/4 vert |
| SILVER `patient_fhir` | 214 lignes (76+76+62) |
| Masters / doublons | 145 / 69 (exact) · duplicate_rate 32.24 % |
| API données | 14/14 PASS (`RMA_USE_MOCK=false`) |
- *Support : `ai/memoire/contexte_projet.md` ; logs `elt.log` ; `test_api.py`.*

### S8. Évaluation ground-truth (2 min)
- 3 jeux easy/medium/hard (500 maîtres, ~1 057 enregistrements, seed 42) ; vérité terrain réservée.
- **Zéro faux positif** sur tous les niveaux → jamais fusionner à tort (essentiel en santé).
- Clé CIN : rappel hard **0.287 → 0.422** sans FP. Parité Pandas = Spark parfaite.
- *Support : `evaluation/evaluation_truth.md` ; tableau `chapters/06-tests.md` §6.2.*

### S9. Difficultés réelles et honnêteté (partie du message technique)
- Incident : SILVER 11 614 lignes (mapping FHIR capturant `patient_uuid`) → corrigé.
- Dettes assumées : `patient_events_gold` 0 ligne (jointures à enrichir), consentement GOLD à alimenter.
- *Support : `chapters/05-realisation.md` §5.6 ; `chapters/06-tests.md` §6.5.*

---

## Partie C — Démonstration reproductible (2 min)

### S10. Démo (script type)
```
# 1. Tests moteur (23/23)
.venv\Scripts\python -m pytest -q

# 2. Évaluation hard
.venv\Scripts\python evaluation\evaluate_engine.py --level hard

# 3. Pipeline VM (si disponible)
bash provision/scripts/run_pipeline.sh
```
- Prérequis : dépôt `Mon_Memoire`, venv Python 3.8+ (`pyproject.toml`), VM Vagrant pour la partie Big Data.
- Résultat attendu → preuve : compteurs `patient_fhir` 214 / 145 masters, rapport `evaluation_truth.md`,
  API 14/14.
- *Support : `projet/code-source/README.md` (démarrage rapide) — à répéter avant la soutenance pour
  capturer des captures d'écran datées.*

---

## Partie D — Conclusion (2 min)

### S11. Réponse à la problématique
Centraliser, nettoyer/standardiser, **dédupliquer de façon explicable**, **gouverner par
consentement** — sur données synthétiques, architecture Big Data, dépôt unique.

### S12. Perspectives
- Enrichir le mapping FHIR (encounters/conditions/observations → `patient_events_gold`).
- Calibrer seuil/poids via le ground-truth ; peupler le consentement central.
- Passage à l'échelle (volume, CI), export VM.

### S13. Merci / questions
- Recontact + référence du dépôt unique et du rapport de stage.

---

## Note de préparation
- **Vérifier avant la soutenance** : re-run `pytest` (23/23), `evaluate_engine.py --level hard`,
  captures d'écran datées du run VM et de la sortie API — pour que chaque chiffre affiché repose sur
  une preuve (règle AGENTS : ne jamais annoncer un résultat sans preuve).
- Les schémas Mermaid (`diagramme_flux_donnees.md`, chapitres) peuvent être exportés en PNG/SVG pour
  intégration dans les slides.
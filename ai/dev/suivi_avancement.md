# Suivi d'avancement — feuille de route

Sources : `ai_context/suivi_avancement.md` (test_bigdata) + `.ai_context/04_priorities.md` (Mavis) + plan de fusion.

## État global de la fusion (dépôt unique `Mon_Memoire`)

```
Phase 0 repo+root [██████████] 100%   Phase 1 docs [██████████] 100%
Phase 2 ai/       [██████████] 100%   Phase 3 copies [██████████] 100%
Phase 4 moteur    [██████████] 100%   Phase 5 GOLD+API [██████████] 100%
Phase 6 éval+tests [██████████] 100%   Commit initial git [██████████] 100%
```

### Phases

| Phase | Description                                                                                  | Statut |
| ----- | -------------------------------------------------------------------------------------------- | ------ |
| 0     | Repo `data_lake_final` (git init, README, AGENTS.md, .gitignore, arborescence)               | ✅     |
| 1     | Docs consolidées : cahier des charges + manuel conceptuel (7 fichiers thématiques)           | ✅     |
| 2     | `ai/memoire/` + `ai/dev/` (instructions agents fusionnées)                                   | ✅     |
| 3     | Copies : `provision/`, `front-optional/`, `sql/schema.sql`, dossiers engine/evaluation/tests | ✅     |
| 4     | Moteur porté `engine/` (identity + governance) + évaluateur adapté + tests 15/15             | ✅     |
| 5     | Intégration SILVER/GOLD + API : `master_patient_id`, consent GOLD, endpoints gouvernance     | ✅     |
| 6     | Évaluation finale (easy/medium/hard), tests API/parité, commit git initial                   | ✅     |

## Règles de progression

- Une phase n'est **démarrable** que si la précédente est validée.
- Vérifier **avant** de déclarer une étape terminée (test / run / trace de validation).
- Documenter hypothèses et blocages dans `ai/dev/logs.md`.
- Ne pas créer d'autres fichiers de suivi.
- États : À faire / En cours / Terminé / Bloqué.

## Priorités actuelles

1. **[Phase 6]** Évaluation easy/medium/hard + `pytest` 9/9 **fait** ; re-run pipeline VM **fait**
   (4/4 vert, 214 lignes / 145 masters / 69 doublons) ; `test_api.sh` **fait (14/14)** ; **commit git
   initial fait** (`2004865`, 07/09).
2. **[Code]** Validation VM OK : `run_pipeline.sh` bout en bout (moteur intégré dans
   `create_silver.py`, consent GOLD 145 lignes) ; API réelle `RMA_USE_MOCK=false` 14/14 PASS ;
   beeline HS2 instable → validation par scripts Spark (`provision/metadata/check_data.py`).
3. **[Mémoire]** Rédaction `Mon_Memoire/chapters/` (01→06) **faite** (08/09) + `references/bibliographie.md`
   (12 réf. vérifiées) ; reste : relecture/conversion docx par l'utilisateur.
4. **[Dépôt unique]** Consolidation **faite** (09/09) — `data_lake_final` + `datalake_mavis` rapatriés
   dans `Mon_Memoire` (subtree → `projet/code-source/`, `projet/mvp/`, `archives/datalake_mavis/`) ;
   pytest 9/9 + générateur 44/44 re-vérifiés.
5. **[Rework CIN + ville]** Rework déduplication **fait** (08/09) — clé CIN (couverture ~75 %) +
   ville de naissance (poids 0.1) remplacent téléphone dans `projet/code-source/` ; weights 0.5/0.3/0.1/0.1 ;
   **pytest moteur 15/15** (matcher 12 incl. config) ; évaluation régénérée (hard : R 0.422, F1 0.594) ;
   docs/mémoire harmonisées. Commits en attente de push (branche `develop_spark`).
6. **[Sécurité]** Purge secrets en dur **faite** (08/09) — `mavis_diag.py` supprimé (identifiants SSH),
   mot de passe PG externalisé via `.env` (template `provision/.env.example`), docs trouées
   (placeholders), hook `githooks/pre-commit` actif (bloque secrets/DSN, `core.hooksPath` activé) ;
   dépôt **exempt de secrets** (live + archive). **Reste :** rotation des identifiants côté serveur
   `102.16.7.154` + recréer `projet/code-source/.env`.
7. **[Config YAML]** Calibration déduplication **déclarative** (08/09) — `config/deduplication.yaml`
   (weights, threshold, blocking) lu par matcher/spark/éval/SILVER via `engine/identity/config.py`
   (fallback défauts) ; une future modification = 1 édit YAML (+ tableau de référence) sans toucher au code.

## Dettes techniques connues

- Mapping FHIR : relier encounters/conditions/observations aux patients (GOLD ~16 lignes en test).
- Gender/birth_date NULL côté MMT_DB (âge « unknown »).
- JWT côté API Flask (RBAC web ≠ API données).
- Docker/CI, export VM `.box`, tests unitaires ≥80 % (hors moteur).
- Pages governance/consentements frontend (optionnel).

## Critères de succès

| Critère            | Cible                                                        |
| ------------------ | ------------------------------------------------------------ |
| Pipeline Medallion | RAW→SILVER→GOLD bout en bout                                 |
| Déduplication      | Explicable, precision ≥0.95, parité Pandas/Spark             |
| Consentement       | Purpose-by-purpose fonctionnel (GOLD + API + PostgreSQL)     |
| Évaluation         | Ground-truth P/R/F1 documenté (easy/medium/hard)             |
| Tests              | Moteur + consentement + API PASS                             |
| Fusion             | Un seul repo autonome, docs sans doublon, commit git initial |
| Mémoire            | Chapitres 01→06 rédigés                                      |

## Journal

- 07/09 : démarrage fusion ; Phases 0, 3, 4 terminées (moteur porté + 9/9 tests).
- 07/09 : Phase 1 docs consolidées rédigées (cahier + 7 thématiques) ; Phase 2 ai/memoire + ai/dev rédigées.
- 07/09 : guide technique `projet/code-source/README.md` + `pyproject.toml` créés ; journal `ai/dev/logs.md` initialisé.
- 07/09 : Phase 5 terminée — `create_silver.py` relié au moteur (master_patient_id/match_method/match_score) ;
  `create_gold.py` produit `patient_consent_gold` ; endpoints `/api/governance/duplicates` + `/api/governance/consent`
  ajoutés à `hive_api.py` (fallback mock) ; chemins VM passés à `datalake-final`.
- 07/09 : Phase 6 (partiel) — `pytest` 9/9 PASS ; évaluation easy/medium/hard exécutée (parité MVP=Spark,
  zero FP, hard Recall 0.287 documenté) ; `evaluation.md` mis à jour. Reste : re-run pipeline VM + tests API + commit initial.
- 07/09 : **Phase 6 VM validée** — cause racine de l'explosion 11 614 lignes corrigée dans `create_silver.py`
  (`patient_uuid` exclu du mapping dynamique, écritures fiabilisées via tmp+rename) ; `run_pipeline.sh` 4/4 vert
  (SILVER 214 = 76+76+62, 145 masters, 69 doublons) ; GOLD patients-only (events 0, consent 145) ; API réelle
  (`RMA_USE_MOCK=false`) **14/14 PASS** ; KPIs gouvernance réels servis hors mock. Reste : **commit git initial**.
- 07/09 : **commit git initial fait** (`2004865`) — `git init` (repo préexistait), `.gitignore` corrigé
  (`**/provision/metadata/`, `**/provision/config/data_sources.json`), `git rm --cached` des métadonnées
  runtime ; message « fix: ELT silver/gold 76×76 dedup explosion + untrack runtime metadata » ; tree propre.
- 08/09 : **Mémoire rédigé** — chapitres 01→06 (`Mon_Memoire/chapters/`, statut « rédigé » daté) +
  `references/bibliographie.md` (B1–B12 vérifiées) ; `ai/dev/logs.md` entrée « Mémoire : chapitres 01→06 ».
  Reste : relecture/conversion docx par l'utilisateur.
- 09/09 : **Dépôt unique `Mon_Memoire` consolidé** — `data_lake_final` importé via `git subtree` (historique
  préservé), PoC `test_bigdata` → `projet/mvp/`, PoC `datalake_mavis` → `archives/datalake_mavis/` (source
  seule) ; artefacts dérivés hors suivi (data_sources.json, cim_embeddings.pkl, docx externe) ; liens
  chapitres + README + AGENTS + cahier des charges alignés ; pytest 9/9 + générateur 44/44 re-vérifiés ;
  anciens répertoires supprimés (coquille `data_lake_final` vide verrouillée — suppression manuelle restante).
- 08/09 : **Rework CIN + ville de naissance** — remplacement téléphone par CIN (~75 %, clé forte) + ville
  (poids 0.1) dans toute la chaîne live (`projet/code-source/`) ; `_phone` → `_cin` (canonical, matcher,
  spark, **init**) ; `MasterPatient.cin/birth_city` ; `make_missing` naissance/ville ; tests matcher 6→9
  (formats CIN, ville, CIN différents) → **pytest moteur 12/12** ; évaluation régénérée (hard TP 307 / FP 0 /
  FN 420 → **R 0.422, F1 0.594**, medium R 0.884, F1 0.939) ; `evaluation_truth.md` mis à jour (hard) ;
  chapitres 01→06, cahier des charges, deduplication.md, evaluation.md, contexte*projet.md, architecture.md,
  deduplication dev harmonisés ; logs.md entrée ajoutée. Outils legacy `rebuild*\*.py`et`ELT.before/` non
  modifiés (hors périmètre actif).
- 08/09 : **Config YAML (source de vérité)** — poids/seuil/préfixe de blocage extraits dans
  `config/deduplication.yaml`, lus par `engine/identity/config.py` (fallback défauts) ; `matcher.py`,
  `spark_dedup.py`, `evaluate_engine.py`, `create_silver.py` paramétrés ; `pyproject.toml` + PyYAML ;
  tests matcher 9→12 (lecture YAML, fallback, override poids) → **pytest 15/15** + générateur 44/44 ;
  éval hard inchangée (parité)

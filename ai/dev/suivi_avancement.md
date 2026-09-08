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

| Phase | Description | Statut |
|---|---|---|
| 0 | Repo `data_lake_final` (git init, README, AGENTS.md, .gitignore, arborescence) | ✅ |
| 1 | Docs consolidées : cahier des charges + manuel conceptuel (7 fichiers thématiques) | ✅ |
| 2 | `ai/memoire/` + `ai/dev/` (instructions agents fusionnées) | ✅ |
| 3 | Copies : `provision/`, `front-optional/`, `sql/schema.sql`, dossiers engine/evaluation/tests | ✅ |
| 4 | Moteur porté `engine/` (identity + governance) + évaluateur adapté + tests 9/9 | ✅ |
| 5 | Intégration SILVER/GOLD + API : `master_patient_id`, consent GOLD, endpoints gouvernance | ✅ |
| 6 | Évaluation finale (easy/medium/hard), tests API/parité, commit git initial | ✅ |

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

## Dettes techniques connues

- Mapping FHIR : relier encounters/conditions/observations aux patients (GOLD ~16 lignes en test).
- Gender/birth_date NULL côté MMT_DB (âge « unknown »).
- JWT côté API Flask (RBAC web ≠ API données).
- Docker/CI, export VM `.box`, tests unitaires ≥80 % (hors moteur).
- Pages governance/consentements frontend (optionnel).

## Critères de succès

| Critère | Cible |
|---|---|
| Pipeline Medallion | RAW→SILVER→GOLD bout en bout |
| Déduplication | Explicable, precision ≥0.95, parité Pandas/Spark |
| Consentement | Purpose-by-purpose fonctionnel (GOLD + API + PostgreSQL) |
| Évaluation | Ground-truth P/R/F1 documenté (easy/medium/hard) |
| Tests | Moteur + consentement + API PASS |
| Fusion | Un seul repo autonome, docs sans doublon, commit git initial |
| Mémoire | Chapitres 01→06 rédigés |

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
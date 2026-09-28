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

1. **[Phase 6]** Évaluation easy/medium/hard + `pytest` moteur **23/23** **fait** ; re-run pipeline VM **fait**
   (4/4 vert, 214 lignes / 145 masters / 69 doublons) ; `test_api.sh` **fait (14/14)** ; **commit git
   initial fait** (`2004865`, 07/09).
2. **[Code]** Validation VM OK : `run_pipeline.sh` bout en bout (moteur intégré dans
   `create_silver.py`, consent GOLD 145 lignes) ; API réelle `RMA_USE_MOCK=false` 14/14 PASS ;
   beeline HS2 instable → validation par scripts Spark (`provision/metadata/check_data.py`).
3. **[Mémoire]** Rédaction `Mon_Memoire/chapters/` (01→06) **faite** (08/09) + `references/bibliographie.md`
   (12 réf. vérifiées) ; **rapport de stage** `documents/rapport_stage.md` + **slides**
   `documents/slides_soutenance.md` + **docx** `documents/memoire_M2_MBDS.docx` **faits** (09/09) ;
   comptes tests harmonisés (moteur **23/23**). Reste : relecture par l'utilisateur, ajustement slides,
   mise en page finale du docx.
4. **[Dépôt unique]** Consolidation **faite** (09/09) — `data_lake_final` + `datalake_mavis` rapatriés
dans `Mon_Memoire` (subtree → `projet/code-source/`, `projet/mvp/`, `archives/datalake_mavis/`) ;
    pytest moteur **23/23** + générateur 44/44 re-vérifiés.
5. **[Rework CIN + ville]** Rework déduplication **fait** (08/09) — clé CIN (couverture ~75 %) +
    ville de naissance (poids 0.1) remplacent téléphone dans `projet/code-source/` ; weights 0.5/0.3/0.1/0.1 ;
    **pytest moteur 23/23** (matcher 12 · consent 3 · canonique 8) ; évaluation régénérée (hard : R 0.422, F1 0.594) ;
    docs/mémoire harmonisées. Commits en attente de push (branche `develop_spark`).
6. **[Sécurité]** Purge secrets en dur **faite** (08/09) — `mavis_diag.py` supprimé (identifiants SSH),
   mot de passe PG externalisé via `.env` (template `provision/.env.example`), docs trouées
   (placeholders), hook `githooks/pre-commit` actif (bloque secrets/DSN, `core.hooksPath` activé) ;
   dépôt **exempt de secrets** (live + archive). **Reste :** rotation des identifiants côté serveur
   `102.16.7.154` + recréer `projet/code-source/.env`.
7. **[Config YAML]** Calibration déduplication **déclarative** (08/09) — `config/deduplication.yaml`
   (weights, threshold, blocking) lu par matcher/spark/éval/SILVER via `engine/identity/config.py`
   (fallback défauts) ; une future modification = 1 édit YAML (+ tableau de référence) sans toucher au code.
8. **[Gouvernance]** Consentement **câblé sur l'API FastAPI** (27/09) — `purpose` obligatoire,
   refus 403 + `refusal_reason` journalisé, finalités en liste fermée (contrainte SQL), `pytest`
   **54/54** (tests sans contournement de l'authentification). Reste : **exécuter** `schema.sql` et
   `seed_governance.py` sur une base réelle (`.env` absent, VM indisponible) pour valider la preuve
   en base — la mécanique est prouvée, la donnée ne l'est pas.
9. **[Mémoire — lisibilité]** Glossaire **créé** (27/09) : `chapters/09-glossaire.md`, ~60 entrées en
   français courant + table des objets du dépôt, inclus automatiquement dans le DOCX (9 chapitres,
   51 tableaux). Six mots-clés données en langage courant dans la section 1.3 ; définitions ajoutées
   à la première occurrence en prose (`metastore`, `rejeu`, MPI/DMP/MDM, `idempotence`,
   `purpose-by-purpose`, `schéma-on-read`). Règle actée dans `ai/memoire/methode.md` et
   `ai/memoire/README.md`. **Aucune perte** de chiffre, identifiant, chemin ou référence vérifiée
   par comparaison avant/après. Reste : relecture humaine de la nouvelle prose.
10. **[Mémoire — présentation]** Lot 2 **fait** (27/09) : les **8 diagrammes Mermaid sont rendus en
    images** (`documents/figures/fig-1..8.png` + `manifest.json`, versionnés, 1,3 Mo) par
    `scripts/dev/render_mermaid_figures.py` (mermaid-cli local via `npx`, navigateur du poste, rien
    dans le dépôt). Le DOCX est désormais **A4** avec page de garde (auteur + 2 encadrants), sommaire
    (champ Word), pagination `Page X / Y` et **bibliographie consolidée** (24 URL). Une figure sur
    deux est placée sur une page paysage dédiée pour que ses libellés restent au moins à 9 pt ;
    seule la figure 6 reste à 5.7 pt (schéma à 12 rangs de nœuds, signalé). **0 perte** de nombre,
    identifiant, chemin ou référence ; `pytest` **54/54**. Lot 3 traité au point 11.
11. **[Mémoire — analyse]** Lot 3 **fait** (27/09) : les trois chapitres les plus courts en prose
    (3 : 664 mots, 6 : 496, 7 : 607) étaient **tableaux denses, analyse absente**. **1 475 mots de
    prose** ajoutés (corpus 6 372 → **7 847**), tous les faits étant vérifiés dans le code :
    ch. 3 (méthode de la capture d'existant, **contrat de normalisation** issu des 3 encodages du
    genre constatés, lecture de la grille de comparaison, réversibilité par
    `config/deduplication.yaml` et son contrepoids) ; ch. 6 (le déterminisme comme condition d'une
    évaluation comparable, lecture de l'entonnoir 214 → 145 vérifiable par comptage, **parité
    Pandas/Spark structurelle**, distinction **API Flask = reporting / API FastAPI = application de
    la règle**, 6 incidents regroupés en 3 familles) ; ch. 7 (pyramide = substitut à une CI, les
    **14/14 de l'API sont un test de fumée** — joignabilité, pas contrôle d'accès —, comptage
    analytique des paires, et le **zéro faux positif présenté comme un plancher** faute de cas
    adversariaire dans la vérité terrain). **0 perte** de token de preuve, structure 9 × 1 H1,
    52 tableaux, 20/20 références, `pytest` **54/54**, DOCX régénéré. Reste : **relecture humaine**
    et ouverture dans Word (champs du sommaire et de la pagination).
12. **[Soutenance]** Plan de temps refait pour un **exposé de 20 min, démonstration comprise**
    (27/09) : `documents/slides_soutenance.md` annonçait « 15 min + 10 min questions » (25 min) et
    n'accordait **aucun budget à S9** (la partie B annonçait 7 min déjà consommées par S5→S8).
    Nouveau budget **16:00 + 4:00 de marge = 20:00**, vérifié par sommation des 13 slides, S9
    enfin chiffré (0:45). **Démonstration non live** mais vidéo de 4:00 enregistrée en amont
    (storyboard en 4 plans + slide de repli obligatoire) : la VM n'est plus un point de failure le
    jour J. Corrigé au passage : les 2 premières commandes de la démo **n'existaient pas** (préfixe
    `projet/code-source/` manquant — elles cassaient devant le jury), 4 figures PNG désormais
    projetées (**`fig-6` exclue** : 5,7 pt illisible au vidéoprojecteur), note obsolète sur
    l'export des PNG supprimée, S8/S9 **alignés sur le ch. 7** (précision = plancher, parité =
    décisions identiques sur les jeux testés, 14/14 = test de fumée).
12b. **[Soutenance]** **Script de passage oral** écrit et **débit mesuré** (27/09) :
    `documents/soutenance_script_oral.md` donne le texte à dire slide par slide (1 548 mots
    mesurés, transitions et « à montrer » inclus), avec chrono, règle de sacrifice en cas de
    dépassement, et une liste de **trois interdictions de parole**. Deux slides étaient
    réellement illisibles à l'oral (S1 à 164 et S9 à 189 mots/min) : texte ramené à un
    maximum de 150 mots/min, le détail restant porté par les figures et les tableaux projetés.
    Total = **15:25 sur 16:00** à 140 mots/min, vidéo comprise.
    Reste : répéter à voix haute avec chronomètre, filmer la vidéo, construire la slide de
    repli, convertir le Markdown dans l'outil de présentation.

## Dettes techniques connues

- Mapping FHIR : relier encounters/conditions/observations aux patients (GOLD ~16 lignes en test).
- Gender/birth_date NULL côté MMT_DB (âge « unknown »).
- JWT côté API Flask (RBAC web ≠ API données).
- API Flask du PoC (`provision/api/hive_api.py`) : `/governance/consent` sans authentification,
  nom du patient exposé, `debug=True`, pas de TLS ni de rate limiting. **Hors périmètre** : le
  contrôle de consentement est appliqué à l'API FastAPI de gouvernance.
- Clés API hachées en SHA-256 **non salées** (`engine/governance/auth.py:26`,
  `provision/db/seed_governance.py:57`) — **désormais déclarée dans le mémoire** (§ 8.3, glossaire,
  § 5.5) avec sa cause et sa voie de correction (sel par clé ou `bcrypt`) ; `access_audit` non
  chiffré au repos ; ni `data_scope` ni `expires_at` sur le consentement.
- `schema.sql` et `provision/db/seed_governance.py` non exécutés depuis leur dernière modification.
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
| Mémoire            | Chapitres 01→08 rédigés                                      |

## Journal

- 09/09 : **Guides techniques** — regroupés dans `GUIDE/` (index + `guide-vagrant.md`,
  `guide-generateur-donnees.md`, `guide-frontend.md`, `guide-backend.md`), basés sur l'état consolidé
  du dépôt ; README API (14/14) et README générateur (sans `main.py`/`pytest.ini` inexistants,
  point d'entrée `evaluate_engine.py`) corrigés ; 44 tests générateur re-comptés.

- 09/09 : **Volet académique** — comptes tests moteur harmonisés **23/23** (matcher 12 · consent 3 ·
  canonique 8, fichiers de test comptés) dans chapitres/contexte/READMEs ; `documents/rapport_stage.md`
  (synthèse MBDS) + `documents/slides_soutenance.md` (esquisse 13 slides) + convertisseur
  `scripts/dev/export_memoire_docx.py` → `documents/memoire_M2_MBDS.docx` (6 chapitres, 27 tables,
  accents UTF-8 validés).
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
- 10/09 : **Cohérence code/docs + docstrings + FastAPI governance** — corrections incohérences (GOLD 17→18, matching_key, test counts, source_file, match_method, bigdata_concepts) ; docstrings des fonctions complexes (moteur identity, governance, ELT, hive_api) ; retrait sentence-transformers (bootstrap.sh) ; bandeaux DÉPRÉCIÉ (evaluation_truth, test.py, ELT.before) ; FastAPI governance câblée (engine/governance/app.py : /health, /metrics, /patients, /patients/{id}, /audit + consent router, port 8000) ; tests test_governance_api.py (4 tests, pattern FakeCursor) ; docs FastAPI (api.md, architecture.md, cahier §4.4, api/README).
- 27/09 : **Mémoire restructurée en 8 chapitres** — les 2 critères non couverts comblés : `chapters/03-etude-existant.md`
  (systèmes MMT : MAVIS 73 090 l./11 tables, MMT_DB 60 271 l./9 tables, CLINIQUE 54 582 l./4 tables ; grille de
  comparaison 6 critères ; verdict — étude **documentaire**, aucun produit installé) et `chapters/08-conclusion.md`
  (réponse à la problématique, limites assumées, perspectives, bilan). Renumérotation 03→07 via `git mv` + renvois ;
  §1.7 du plan étendu à 8 lignes ; architecture §5.1 renforcée (chaîne bout-en-bout + composants/ports) ;
  bibliographie `[B13..B20]` ; README / `ai/memoire/*` / rapport / slides synchronisés. Correctif **BOM UTF-8**
  (PS 5.1 `Set-Content`) qui cassait la détection des titres : DOCX régénéré = **8 H1**, 34 tables, 50 605 caractères.
  Reste : relecture utilisateur + commit.
- 27/09 : **Consentement réellement appliqué + axes d'état de l'art** — commit `fb5582c` (restructuration
  8 chapitres) validé, puis câblage du contrôle d'accès sur l'API FastAPI : `purpose` obligatoire sur
  `/patients` et `/patients/{id}`, liste fermée `api_access|research|analytics` (contrainte SQL), refus
  **403** avec `refusal_reason` persisté dans `access_audit`, **401/403/422** vérifiés. Bug corrigé :
  `/audit` interrogeait `recorded_at` (colonne inexistante) → `accessed_at`. Seed gouvernance créé
  (`provision/db/seed_governance.py`, consentements mixtes déterministes, clés générées à l'exécution).
  Tests réécrits **sans `dependency_overrides`** → **54/54** (12 matcher · 21 consentement · 8 dédup ·
  13 API) ; sensibilité vérifiée par mutation (retirer `enforce_consent` fait échouer le test de refus).
  Mémoire : axes **0** (§2.10 veille + couverture des 20 axes), **6** (§2.11 matrice de sélection
  pondérée), **14** (§4.5 contexte local), **15** (§4.6 jalons J1→J5), **19** (§8.1 synthèse des
  arbitrages) ; §2.5 et §5.5 corrigés (les colonnes `data_scope` / `expires_at` annoncées n'existent pas) ;
  comptes de tests harmonisés 23/23 → 54/54. Reste : exécuter `schema.sql` + le seed sur une base réelle.
- 27/09 : **Correctif BOM** (commit `4d3c417`) puis **glossaire et passe de lisibilité** —
  `chapters/09-glossaire.md` créé (~60 entrées : données et qualité / architecture Big Data /
  gouvernance et droit / objets du dépôt), importé automatiquement dans le DOCX (glob `0*.md` de
  `export_memoire_docx.py`). Le lecteur rencontre désormais le jargon expliqué : six mots-clés
  en langage courant insérés en §1.3 avant le tableau des objectifs, définitions ajoutées à la
  première occurrence en prose (`metastore`, `rejeu`, MPI / DMP / MDM, `idempotence`,
  `purpose-by-purpose`, `schéma-on-read`, `partition`, `volumétrie`). **22 renvois de section du
  glossaire vérifiés un par un** contre l'inventaire réel (56 sections) : 0 renvoi cassé. Règle
  actée : tout terme technique doit être défini en français courant à sa première apparition
  (`ai/memoire/methode.md`, `ai/memoire/README.md`). **Non-régression prouvée** : comparaison
  avant/après de tous les chiffres, identifiants de code, chemins et références `[B#]` → **0 perte**.
  Structure : **9 chapitres** à 1 H1, 51 tableaux, fences équilibrées, **20/20** références ;
  DOCX régénéré = **9 H1**, 51 tableaux, **61 908 caractères** ; `pytest` **54/54**.
- 27/09 : **Lot 1 — corrections de fond du mémoire** (9 corrections, sans réécriture) — audit des
  9 chapitres, du DOCX et des documents de soutenance. La plus grave : la synthèse de couverture de
  §2.10 annonçait « 6 traités / 8 partiels / 5 hors périmètre / 1 optionnel » alors que son propre
  tableau donne **11 / 7 / 1 / 1** (= 20 axes) ; les noms de blocs divergeaient aussi du tableau.
  Corrigé en plus : « trois niveaux » suivi de cinq jalons J1–J5 (§4.6), J5 « 8 chapitres » → 9,
  **plan du mémoire complété de 1 à 9** (§1.7), schéma à 5 étapes vs tableau à 3 niveaux (§1.4,
  ligne « Transverse » ajoutée), dashboard du PoC vs hors périmètre (§1.4/§1.5), API de
  gouvernance nommée **FastAPI** (§1.5), docstring de l'exporteur en `01..09`, et chaîne de
  démarche des slides complétée par la gouvernance. Preuves : **0 perte** de nombre, identifiant,
  chemin ou référence sur 12 fichiers ; structure 9 × 1 H1, 51 tableaux, **20/20** références ;
  `pytest` **54/54** ; DOCX **9 H1**, 51 tableaux, **62 445 caractères**.
  **Reste (lots 2 et 3, non engagés, à arbitrer)** : rendu des 8 diagrammes Mermaid en images,
  page de garde / TDM / pagination, bibliographie consolidée dans le DOCX, élargissement des
  chapitres 6 (675 mots), 7 (821) et 3 (949).
- 27/09 : **Lot 2 — figures Mermaid rendues et DOCX A4 complet** — les 8 diagrammes des chapitres
  sont maintenant des **images** dans le DOCX au lieu de 66 lignes de code brut, produites localement
  par `scripts/dev/render_mermaid_figures.py` (mermaid-cli via `npx`, Chrome du poste, aucun
  Chromium téléchargé, aucun `node_modules` dans le dépôt). Chaque figure porte une légende
  numérotée lue depuis le Markdown. Deux défauts réels corrigés au passage : le libellé
  `extract_raw_report.json` cassait le parseur Mermaid (points en collision avec la syntaxe
  `-. texte .->`), et **3 figures étaient tronquées** par une fenêtre de rendu trop étroite
  (largeurs naturelles 1812 / 1606 / 2904 px pour 1600 px disponibles) — le moteur mesure désormais
  la taille naturelle avant de rendre. Lisibilité mesurée et outillée : 2 figures dans le texte,
  6 sur page paysage dédiée (libellés ≥ 8.7 pt sauf la figure 6 à 5.7 pt, signalée). Le DOCX passe
  en **A4** avec page de garde complète (auteur, encadrant professionnel, encadrant pédagogique),
  sommaire, pagination `Page X / Y` et la bibliographie complète (24 URL, 0 avant).
  Preuves : 8 images insérées, 0 résidu de code Mermaid, 10 H1, 51 tableaux, 13 sections,
  **0 perte** de nombre / identifiant / chemin / référence sur 12 fichiers, structure 20/20
  références, `pytest` **54/54**, encodage sans BOM ni caractère de contrôle, aucun secret.
- 27/09 : **Lot 3 — élargissement de la prose des chapitres 3, 6 et 7** — le constat était net :
  les trois chapitres les plus courts (**6 : 496**, **7 : 607**, **3 : 664** mots de prose)
  concentraient l'argument dans leurs tableaux. **1 475 mots de prose** ajoutés, tous les faits
  étant vérifiés dans le code ou dans une sortie de commande (corpus **6 372 → 7 847** mots).
  Ch. 3 : méthode de la capture d'existant (ce que l'introspection prouve et ne prouve pas),
  **contrat de normalisation** déduit des 3 encodages du genre réellement émis par les générateurs
  (listes fermées, CIN rejeté hors 6-12 chiffres, « aucune valeur n'est devinée »), lecture de la
  grille de comparaison (la colonne du projet n'est pas soumise au même régime de preuve :
  `testé` vs `conçu`), réversibilité via `config/deduplication.yaml` — avec son contrepoids écrit :
  le même fichier alimente l'évaluation, donc un changement de poids **invalide les métriques
  publiées**. Ch. 6 : le déterminisme comme condition d'une évaluation comparable, lecture de
  l'entonnoir **214 → 145** vérifiable par comptage sur le lac, **parité Pandas/Spark structurelle**
  (mêmes poids, même seuil, seule la stratégie de regroupement diffère), distinction explicite
  **API Flask = reporting / API FastAPI = application de la règle** (dette désormais écrite dans le
  mémoire), 6 incidents regroupés en 3 familles. Ch. 7 : la pyramide comme substitut à une CI,
  **les 14/14 de l'API sont un test de fumée** (statuts seuls, sans en-tête d'authentification :
  joignabilité, pas contrôle d'accès), comptage analytique des paires, et **le zéro faux positif
  présenté comme un plancher** — le générateur ne crée jamais d'homophones quasi identiques, donc
  le cas adversariaire n'est pas sollicité ; 2 lignes ajoutées au tableau des limites (§7.5).
  Preuves : **0 perte** de token de preuve (nombres, identifiants, chemins, `[B#]`) sur les
  3 chapitres, structure 9 × 1 H1, **52 tableaux**, 8 diagrammes, légendes 1..8, **20/20**
  références, `pytest` **54/54** (code de sortie 0), DOCX régénéré (1 178 paragraphes, 8 images,
  13 sections A4, 0 résidu Mermaid). Les 8 diagrammes et leurs légendes étant **inchangés**, les PNG
  n'ont pas été re-rendus ; seuls 2 numéros de ligne du manifeste ont été recorrectés.
  **Reste : relecture humaine, et ouverture dans Word** (les champs du sommaire et de la pagination
  se remplissent à la première ouverture).
- 27/09 : **Soutenance — plan de temps refait pour 20 min, démonstration en vidéo** — l'exposé
  dure 20 min démo comprise et la démonstration n'est **pas** en direct. Constat : les 13 slides
  étaient bien calibrées en nombre mais le fichier annonçait 25 min (15 + 10 questions), la partie B
  consommait ses 7 min sans budget pour S9, et surtout les **2 premières commandes de la démo
  n'existaient pas** (préfixe `projet/code-source/` manquant) — elles se seraient arrêtées net
  pendant la soutenance. Nouveau budget **16:00 + 4:00 de marge**, S9 chiffré à 0:45, démo
  transformée en **storyboard vidéo de 4:00** (pytest, évaluation hard, pipeline Medallion,
  repli) avec slide de repli obligatoire. 4 figures PNG projetées ; **`fig-6` exclue** car
  illisible à 5,7 pt. S8 et S9 **recorrigés pour coller au chapitre 7** : le zéro faux positif y
  est présenté comme un plancher (pas de cas adversariaire dans la vérité terrain) et la parité
  comme l'identité des décisions sur les jeux testés. Reste : filmer la vidéo à la maison (VM
  allumée), construire la slide de repli, convertir le Markdown dans l'outil de présentation.
- 28/09 : **Mémoire — étape 2 : 52 → 40 tableaux, 35 légendes, liste des tableaux active** —
  réduction au critère jury, sans perte de preuve. Convertis en prose : le vocabulaire d'introduction
  (§1.3) et les trois niveaux (§1.4) en puces, les 5 étapes de l'ER (§2.1), les poids du score (§2.2,
  doublon du §2.11), les briques Big Data (§2.6) et les zones Medallion (§2.7), les 3 grilles de
  notation fusionnées en **une seule** avec colonne « Arbitrage » (§2.11), les définitions de
  métriques et le breakdown par méthode (§7.2, §7.3). Doublons supprimés : les arbitrages du §2.8
  existaient en double au §8.2 (les 3 choix absents de la conclusion y ont été ajoutés, tableau
  consolidé à **11 arbitrages**) et les limites du §7.5 existaient en double au §8.3 (la limite des
  homophones, absente de la conclusion, y a été ajoutée). Colonne redondante retirée du tableau
  des sources (§4.2), le mapping champ par champ restant au §5.2. Les **40 tableaux conservés**
  (5 du glossaire volontairement non légendés, c'est du matériel de référence) portent **35
  légendes** numérotées 1..35 en continu, ce qui active la **liste des tableaux** du liminaire
  (absente tant qu'aucune légende n'existait). Preuves : numérotation continue 1..35 sans doublon,
  aucun tableau cassé (contrôle en-tête + séparateur + lignes sur les 9 chapitres), scan des lignes
  modifiées **sans accent manquant**, `pytest` **54/54**, DOCX régénéré (**41** tableaux = 40 + 1
  acronymes, 14 sections, liminaire : 8 figures et **35 tableaux** listés, archive zip et XML
  valides). **6 numéros de ligne** de `documents/figures/manifest.json` recorrectés (décalages dus
  aux légendes et aux conversions).
  **Reste : relecture humaine dans Word**, et l'étape 3 (3 pages de front en plus des RMA, bandeau
  `mocked`, KPI `CPN4` à corriger, puis les 3 passages du mémoire qui en dépendent).
# Captures du rapport de stage

Dépose ici les images, avec **exactement** le nom de fichier indiqué, puis régénère le rapport :

```
python projet/code-source/scripts/dev/build_rapport_stage_docx.py
```

Chaque image remplace son cadre « EMPLACEMENT RÉSERVÉ » ; la numérotation, la légende et la liste
des figures se mettent à jour seules. Le terminal affiche à chaque génération l'état de chaque
emplacement (`inséré` / `EN ATTENTE`).

## Règles

- **Aucune donnée réelle** : uniquement les données synthétiques (seed 42). Pour MAVIS, le schéma
  seulement, jamais de lignes de patients.
- **Pas de secret visible** : clé d'API, mot de passe, jeton JWT, adresse IP interne → à masquer.
- PNG de préférence, recadré sur l'utile (pas de barre des tâches ni d'onglets inutiles).
- Largeur conseillée : 1 400 à 2 000 px. Le texte de la capture doit rester lisible une fois l'image
  réduite à 16 cm (police du terminal ≥ 14 px, zoom navigateur 100–125 %).
- Terminal : fond clair de préférence (rendu imprimé), ou thème sombre si tu préfères, mais le même
  pour toutes les captures de terminal.
- Pour retirer un emplacement que tu ne veux pas remplir, supprime sa ligne `Capture:` dans
  `documents/rapport_stage_source.md`.

## Captures à préparer

| Id | Fichier | Section | Contenu attendu | Priorité |
|---|---|---|---|---|
| C01 | `C01_schema_mavis.png` | 3.1.2 Existant | liste des tables ou diagramme du schéma MAVIS (DBeaver, pgAdmin), sans données | optionnel |
| C02 | `C02_gantt.png` | 4.4 Planification | feuille Gantt de `documents/Gantt_suivi_projet.xlsx`, du 06/07 à fin octobre | retiré du rapport (29/09/2026) |
| C03 | `C03_connexion.png` | 5.3.1 IHM | page `/login` | retiré du rapport (29/09/2026) |
| C04 | `C04_synthese.png` | 5.3.1 IHM | page `/synthese` : maîtres, doublons, taux, accords/refus | réalisée le 30/09/2026 |
| C05 | `C05_doublons.png` | 5.3.1 IHM | page `/doublons` : répartition par méthode | retiré du rapport (29/09/2026) |
| C06 | `C06_gouvernance.png` | 5.3.1 IHM | page `/gouvernance`, filtrée sur une finalité | retiré du rapport (29/09/2026) |
| C07 | `C07_pipeline.png` | 5.3.1 IHM | page `/dashboard` ou `/pipeline` : zones, dernier run, planification | réalisée le 30/09/2026 |
| C08 | `C08_patients.png` | 5.3.1 IHM | page `/patients` avec recherche et finalité | retiré du rapport (29/09/2026) |
| C09 | `C09_fiche_patient.png` | 5.3.1 IHM | page `/patients/{id}` d'un patient à trois fiches (une par source), réunies par la règle d'identité stricte | réalisée le 30/09/2026 |
| C10 | `C10_swagger.png` | 5.3.2 API | `/docs` de l'API FastAPI (port 8000), points d'entrée listés | réalisée le 30/09/2026 |
| C11 | `C11_hdfs_datalake.png` | 6.2 Architecture technique | interface HDFS (port 9870) > Browse, dossier `/datalake` (raw, silver, gold) | réalisée le 30/09/2026 |
| C12 | `C12_run_pipeline.png` | 7.3.1 Pipeline | terminal VM : sortie de `run_pipeline.sh` ou fin de `elt.log`, étapes OK | réalisée le 30/09/2026 |
| C13 | `C13_comptages.png` | 7.3.1 Pipeline | requête Spark/Hive : 214 lignes SILVER, 145 maîtres | retiré du rapport (29/09/2026) |
| C14 | `C14_refus_403.png` | 7.3.3 Gouvernance | réponse 403 + ligne `access_audit` (purpose, refusal_reason) | réalisée le 30/09/2026 |
| C15 | `C15_pytest.png` | 8.1 Tests | `pytest projet/code-source/tests` avec la base de test PostgreSQL : « 160 passed, 2 skipped » | réalisée le 30/09/2026 (refaite après l'ajout des tests PostgreSQL et des tranches d'âge) |
| C16 | `C16_evaluation.png` | 8.4 Évaluation | sortie de `evaluate_pipeline_run.py --level hard --parity` (P/R/F1 et parité Spark) | réalisée le 30/09/2026 |

## Extraits de code (déjà remplis)

Ces emplacements affichent déjà le **code réel du dépôt**, avec ses numéros de ligne, repéré par nom de
fonction (il reste juste si le code bouge). Une capture est **facultative** : si tu préfères une image
(VS Code, Carbon…), dépose-la sous le nom indiqué et elle remplacera le texte.

| Id | Fichier facultatif | Section | Code extrait |
|---|---|---|---|
| X01 | `X01_normalisation.png` | 7.2.2 | `canonical.py` : `_cin`, `_gender` |
| X02 | `X02_schema.png` | 7.2.2 | `sql/schema.sql` : tables `patient_identity_map` et `consent` |
| X03 | `X03_config.png` | 7.2.3 | retiré du rapport (29/09/2026) |
| X04 | `X04_score.png` | 7.2.3 | `rules.py` : `identity_key`, `master_id` |
| X05 | `X05_consentement.png` | 7.2.3 | `consent.py` : `check_consent`, `enforce_consent` |
| X06 | `X06_deduplicate.png` | Annexe D | `matcher.py` : `deduplicate` |
| X07 | `X07_audit.png` | Annexe D | `audit.py` : `AuditMiddleware` |

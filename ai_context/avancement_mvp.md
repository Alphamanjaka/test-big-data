# Avancement Niveau 1 — MVP (CSV + Pandas + PostgreSQL)

Dernière mise à jour : 2026-09-01

## Semaine 1 — Fondations et sources

| # | Tâche | État |
|---|---|---|
| 1.1 | Créer l'arborescence du projet | Terminé |
| 1.2 | Créer les CSV sources (pharmacie, consultation, imagerie) | Terminé |
| 1.3 | Générer données fictives avec doublons volontaires | Terminé |
| 1.4 | Configurer PostgreSQL / créer la base | Terminé |
| 1.5 | Définir le modèle canonique (CanonicalPatient) | Terminé |
| 1.6 | Créer config/sources.json + config/mappings.json | Terminé |
| 1.7 | Initialiser le repo Git | Terminé |

## Semaine 2 — Pipeline ETL

| # | Tâche | État |
|---|---|---|
| 2.1 | BaseExtractor (abstrait) | Terminé |
| 2.2 | CSVExtractor | Terminé |
| 2.3 | Mapping source → canonique | Terminé |
| 2.4 | Standardisation (noms, dates, téléphones) | Terminé |
| 2.5 | Nettoyage | Terminé |
| 2.6 | Validation | Terminé |
| 2.7 | Zone RAW | Terminé |
| 2.8 | Orchestrateur | Terminé |

## Semaine 3 — Entity Resolution

| # | Tâche | État |
|---|---|---|
| 3.1 | Blocking | Terminé |
| 3.2 | Exact matching | Terminé |
| 3.3 | Fuzzy matching (RapidFuzz) | Terminé |
| 3.4 | Score de similarité global | Terminé |
| 3.5 | Seuils (≥90 auto / 70-90 review / <70 no match) | Terminé |
| 3.6 | Master Patient Index | Terminé |
| 3.7 | Identity Mapping | Terminé |
| 3.8 | Valider cas Jean Rakoto | Terminé |

## Semaine 4 — Centralisation et démonstration

| # | Tâche | État |
|---|---|---|
| 4.1 | Chargement PostgreSQL | Terminé |
| 4.2 | Migrer relations métier (achats, consultations, examens) | Terminé |
| 4.3 | Consentement basique | Terminé |
| 4.4 | Dashboard Streamlit | Terminé |
| 4.5 | Tests | Terminé |
| 4.6 | Documentation | Terminé |
| 4.7 | Préparer démonstration soutenance | Terminé |

## État global

```
S1 ████████ 100%   S2 ████████ 100%   S3 ████████ 100%   S4 ████████ 100%   TOTAL ████████ 100%
```

## Décisions techniques

| Décision | Choix | Justification |
|---|---|---|
| Langage | Python | Standard data engineering |
| Manipulation | Pandas | MVP, volume faible |
| Matching | RapidFuzz | Similarité floue |
| BDD | PostgreSQL | Robuste, standard |
| Dashboard | Streamlit | rapide à implémenter |
| ORM | SQLAlchemy | abstraction BDD |

## Validations

- `pytest -q` : 14 tests réussis (pipeline, API, auth, audit, consent)
- `python run_pipeline.py` : 3 sources, 60 lignes RAW, 36 masters, 24 fusions exactes, 60 identity links
- `python load_to_postgres.py` : schéma idempotent, 60 RAW, 36 masters, 60 identity links, 60 enregistrements métier, 108 consentements
- API : `/health`, `/metrics`, `/patients`, `/audit`, `/consent` validés
- Dashboard : Streamlit sur `localhost:8501`, auth par clé API, données mises en cache 30s
- `logs/runtime.log` : journalisation temps réel active
- Gouvernance : 3 rôles (admin/analyst/viewer), clés API hachées SHA-256, audit d'accès

## Hypothèses / Blocages / Journal

- **Hypothèses** :
  - H1 : Données exclusivement synthétiques
  - H2 : Fichiers CSV comme sources d'entrée, PostgreSQL comme cible centrale
  - H3 : Clés API de démo régénérées à chaque exécution de `init_governance.py`
  - H4 : Lignes RAW append-only (historique des extractions conservé)
- **Blocages** : Aucun blocage technique actuel
- **Journal** :
  - 2026-09-01 | S1-S4 | Pipeline complet | 3 sources → 36 masters → PostgreSQL → Dashboard → API → Tests → Gouvernance

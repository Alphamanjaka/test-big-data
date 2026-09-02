# Suivi d'avancement global

Dernière mise à jour : 2026-09-02

## Vue d'ensemble des 3 niveaux

| Niveau | Description | État | Détail |
|---|---|---|---|
| 1 | MVP — CSV + Pandas + PostgreSQL | Terminé | [ai_context/avancement_mvp.md](ai_context/avancement_mvp.md) |
| 2 | Scalabilité — PySpark distribué | À faire | [ai_context/avancement_spark.md](ai_context/avancement_spark.md) |
| 3 | Big Data — Data Lake + HDFS + Hive + Spark | À faire | [ai_context/avancement_bigdata.md](ai_context/avancement_bigdata.md) |

**Règle** : Les Niveaux 2 et 3 ne peuvent commencer que si le Niveau 1 est validé.

---

# Niveau 1 — MVP (suivi détaillé)

Le Niveau 1 (MVP) est le plus avancé. Les étapes du Niveau 2 et 3 sont détaillées dans les fichiers de suivi dédiés
(`ai_context/avancement_spark.md` et `ai_context/avancement_bigdata.md`).

## Prérequis du Niveau 2 (Spark) — à valider avant de commencer

| # | Critère | État |
|---|---|---|
| P1 | PySpark installé et session fonctionnelle | À faire |
| P2 | Extraction en Spark DataFrame | À faire |
| P3 | Transformation identique au MVP | À faire |
| P4 | Déduplication validée en Spark | À faire |
| P5 | Résultats identiques à Pandas | À faire |

## État des étapes

| Étape                      | État    | Justificatif                                                   |
| -------------------------- | ------- | -------------------------------------------------------------- |
| Architecture               | Terminé | Structure Python modulaire créée                               |
| Sources CSV synthétiques   | Terminé | 3 sources × 6 lignes dans `data/raw`                          |
| Extraction                 | Terminé | 6 lignes par source (18 lignes) validées par le pipeline      |
| Mapping et standardisation | Terminé | Modèle canonique, dates et téléphones testés                   |
| Nettoyage                  | Terminé | Normalisation des espaces, accents et formats                  |
| Déduplication explicable   | Terminé | Matching exact puis probabiliste, 24 fusions exactes           |
| Traçabilité RAW            | Terminé | 18 lignes originales chargées dans `raw_patient_record`        |
| Données métier             | Terminé | 18 enregistrements métier (6 par domaine) reliés aux masters   |
| Identity mapping           | Terminé | 18 enregistrements source reliés à 11 masters                  |
| PostgreSQL central         | Terminé | Schéma idempotent et données chargées dans `patient_plateform` |
| API                        | Terminé | Endpoints lecture seule validés sur PostgreSQL                 |
| Dashboard                  | Terminé | Vue Streamlit validée sur PostgreSQL                           |
| Cas de démonstration       | Terminé | Deux tests passent et le script produit les liens attendus     |
| Journalisation temps réel  | Terminé | `logs/runtime.log` alimenté à chaque exécution du pipeline     |
| Configuration Git          | Terminé | `.gitignore` et `.gitattributes` ajoutés, dépôt sur `main`     |
| Contrôle d'accès API       | Terminé | Authentification par clé API + 3 rôles (admin, analyst, viewer) |
| Audit des accès            | Terminé | Table `access_audit` alimentée à chaque requête API            |
| Gestion du consentement    | Terminé | Endpoints CRUD `consent` + consentements de démo               |
| Journal d'audit consultable| Terminé | Endpoint `/audit` réservé admin                                |
| Authentification Dashboard | Terminé | Sidebar à clé API + affichage selon le rôle                    |

## Validations réalisées

- `pytest -q` : 14 tests réussis (pipeline, API, auth, audit, consent).
- `python run_pipeline.py` : 3 sources traitées (6 lignes chacune), 11 patients master créés.
- `python load_to_postgres.py` : schéma appliqué et données chargées dans `patient_plateform`.
- Vérification PostgreSQL : `18` RAW, `11` masters et `18` identity links présents.
- Vérification données métier : `6` achats, `6` consultations et `6` examens présents.
- Relance de `python load_to_postgres.py` : réussie sans doublonner les lignes.
- `logs/runtime.log` : événements pipeline, extraction et déduplication écrits immédiatement.
- API : `/health`, `/metrics`, `/patients`, `/audit`, `/consent` validés sur `patient_plateform`.
- Dashboard : serveur démarré sur `http://localhost:8501`, réponse HTTP `200`, requêtes mises en cache 30 secondes.
- `scripts/init_governance.py` : crée les 3 utilisateurs de démo et les consentements.
- Données : 6 lignes par source (18 RAW), 11 masters, 6 fusions exactes, 18 identity links, 18 enregistrements métier.
- Correction du loader : les masters sont insérés avant les données métier pour respecter les clés étrangères.
- BDD vérifiée : 18 RAW, 11 masters, 18 identity links, 6 achats / 6 consultations / 6 examens, 27 consentements.

## Hypothèses et blocages

- Les données utilisées sont exclusivement synthétiques.
- Les fichiers CSV restent les sources d'entrée du MVP et PostgreSQL est la cible centrale.
- Aucun blocage technique actuel pour le pipeline local.
- La connexion au serveur PostgreSQL est configurée pour `patient_plateform`.
- Les clés API sont stockées hachées (SHA-256) dans la table `api_user`.
- Les clés API de démo sont régénérées à chaque exécution de `scripts/init_governance.py`.
- Les lignes RAW sont append-only : les relances conservent l'historique des extractions.
- La gouvernance avancée (audit, rôles, consentement) est en place ; l'exposition réelle des payloads RAW reste désactivée par conception.
- `pyspark==4.2.0` est présent dans `requirements.txt` mais absent de `pyproject.toml` et jamais importé.

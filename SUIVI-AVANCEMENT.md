# Suivi d’avancement du MVP

Dernière mise à jour : 2026-09-01

## État des étapes

| Étape                      | État    | Justificatif                                                   |
| -------------------------- | ------- | -------------------------------------------------------------- |
| Architecture               | Terminé | Structure Python modulaire créée                               |
| Sources CSV synthétiques   | Terminé | Trois sources présentes dans `data/raw`                        |
| Extraction                 | Terminé | Extracteur CSV validé par le pipeline                          |
| Mapping et standardisation | Terminé | Modèle canonique, dates et téléphones testés                   |
| Nettoyage                  | Terminé | Normalisation des espaces, accents et formats                  |
| Déduplication explicable   | Terminé | Matching exact puis probabiliste avec score et explication     |
| Traçabilité RAW            | Terminé | Six lignes originales chargées dans `raw_patient_record`       |
| Données métier             | Terminé | Achats, consultations et examens reliés aux patients master    |
| Identity mapping           | Terminé | Six enregistrements source reliés à deux masters               |
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
| Autentification Dashboard  | Terminé | Sidebar à clé API + affichage selon le rôle                    |

## Validations réalisées

- `pytest -q` : 4 tests réussis.
- `python -m compileall -q src` : compilation réussie.
- `python run_pipeline.py` : trois sources traitées, deux patients master créés.
- `python load_to_postgres.py` : schéma appliqué et données chargées dans `patient_plateform`.
- Vérification PostgreSQL : `6` RAW, `2` masters et `6` identity links présents.
- Vérification données métier : `2` achats, `2` consultations et `2` examens présents.
- Relance de `python load_to_postgres.py` : réussie sans doublonner les lignes (`2` masters, `6` identity links).
- `logs/runtime.log` : événements pipeline, extraction et déduplication écrits immédiatement.
- API : `/health`, `/metrics` et `/patients` validés sur `patient_plateform`.
- Dashboard : serveur démarré sur `http://localhost:8501`, réponse HTTP `200`, requêtes mises en cache 30 secondes.
- Configuration Git vérifiée : identité locale configurée, aucun commit encore créé.
- `pytest -q` : 14 tests réussis (pipeline, API, auth, audit, consent).
- Contrôle d'accès : token API requis sur les endpoints, roles appliqués (admin/analyst/viewer).
- Endpoint `/audit` : journal d'accès réservé admin.
- Endpoint `/consent` : lecture admin/analyst, écriture admin.
- `scripts/init_governance.py` : crée les 3 utilisateurs de démo et les consentements.

## Hypothèses et blocages

- Les données utilisées sont exclusivement synthétiques.
- Les fichiers CSV restent les sources d'entrée du MVP et PostgreSQL est maintenant la cible centrale.
- Aucun blocage technique actuel pour le pipeline local.
- La connexion au serveur PostgreSQL est configurée pour `patient_plateform`.
- Les clés API sont stockées hachées (SHA-256) dans la table `api_user`.
- Les clés API de démo sont régénérées à chaque exécution de `scripts/init_governance.py`.
- Les lignes RAW sont append-only : les relances conservent l'historique des extractions.
- La gouvernance avancée (audit, rôles, consentement) est en place ; l'exposition réelle des payloads RAW reste désactivée par conception.

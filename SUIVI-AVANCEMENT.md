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
| API                        | À faire | Module réservé, endpoints non implémentés                      |
| Dashboard                  | À faire | Module réservé, visualisation non implémentée                  |
| Cas de démonstration       | Terminé | Deux tests passent et le script produit les liens attendus     |
| Journalisation temps réel  | Terminé | `logs/runtime.log` alimenté à chaque exécution du pipeline     |
| Configuration Git          | Terminé | `.gitignore` et `.gitattributes` ajoutés, dépôt sur `main`     |

## Validations réalisées

- `pytest -q` : 3 tests réussis.
- `python -m compileall -q src` : compilation réussie.
- `python run_pipeline.py` : trois sources traitées, deux patients master créés.
- `python load_to_postgres.py` : schéma appliqué et données chargées dans `patient_plateform`.
- Vérification PostgreSQL : `6` RAW, `2` masters et `6` identity links présents.
- Vérification données métier : `2` achats, `2` consultations et `2` examens présents.
- Relance de `python load_to_postgres.py` : réussie sans doublonner les lignes (`2` masters, `6` identity links).
- `logs/runtime.log` : événements pipeline, extraction et déduplication écrits immédiatement.
- Configuration Git vérifiée : identité locale configurée, aucun commit encore créé.

## Hypothèses et blocages

- Les données utilisées sont exclusivement synthétiques.
- Les fichiers CSV restent les sources d'entrée du MVP et PostgreSQL est maintenant la cible centrale.
- Aucun blocage technique actuel pour le pipeline local.
- La connexion au serveur PostgreSQL est configurée pour `patient_plateform`.
- La gouvernance opérationnelle et le dashboard restent à développer.

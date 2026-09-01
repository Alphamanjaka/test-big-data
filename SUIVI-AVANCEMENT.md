# Suivi d’avancement du MVP

Dernière mise à jour : 2026-09-01

## État des étapes

| Étape                      | État    | Justificatif                                               |
| -------------------------- | ------- | ---------------------------------------------------------- |
| Architecture               | Terminé | Structure Python modulaire créée                           |
| Sources CSV synthétiques   | Terminé | Trois sources présentes dans `data/raw`                    |
| Extraction                 | Terminé | Extracteur CSV validé par le pipeline                      |
| Mapping et standardisation | Terminé | Modèle canonique, dates et téléphones testés               |
| Nettoyage                  | Terminé | Normalisation des espaces, accents et formats              |
| Déduplication explicable   | Terminé | Matching exact puis probabiliste avec score et explication |
| Identity mapping           | Terminé | Six enregistrements source reliés à deux masters           |
| PostgreSQL central         | À faire | Schéma SQL préparé, chargement non implémenté              |
| API                        | À faire | Module réservé, endpoints non implémentés                  |
| Dashboard                  | À faire | Module réservé, visualisation non implémentée              |
| Cas de démonstration       | Terminé | Deux tests passent et le script produit les liens attendus |
| Journalisation temps réel  | Terminé | `logs/runtime.log` alimenté à chaque exécution du pipeline |
| Configuration Git          | Terminé | `.gitignore` et `.gitattributes` ajoutés, dépôt sur `main` |

## Validations réalisées

- `pytest -q` : 2 tests réussis.
- `python -m compileall -q src` : compilation réussie.
- `python run_pipeline.py` : trois sources traitées, deux patients master créés.
- `logs/runtime.log` : événements pipeline, extraction et déduplication écrits immédiatement.
- Configuration Git vérifiée : identité locale configurée, aucun commit encore créé.

## Hypothèses et blocages

- Les données utilisées sont exclusivement synthétiques.
- Le MVP utilise des fichiers CSV avant le branchement PostgreSQL.
- Aucun blocage technique actuel pour le pipeline local.
- Le chargement PostgreSQL, la gouvernance opérationnelle et le dashboard restent à développer.

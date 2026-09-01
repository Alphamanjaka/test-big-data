# Logs et traçabilité

## Objectif

Assurer une trace claire des transformations et des décisions tout en protégeant les données sensibles.

## Fichier de sortie obligatoire

Toutes les entrées de journalisation du projet doivent être écrites dans le fichier racine `LOGS.md`.
Ne pas créer un autre fichier de logs et ne pas conserver uniquement les informations dans la conversation, le terminal ou un fichier temporaire.

## Règles

- Les logs doivent être lisibles, concis et structurés.
- Chaque étape importante doit être journalisée : connexion, extraction, mapping, nettoyage, matching, chargement.
- Les logs ne doivent jamais afficher de données patients réelles.
- Les erreurs doivent contenir le contexte technique sans divulguer d’informations sensibles.

## Types de logs à conserver

- logs de connexion aux sources
- logs d’extraction et de chargement
- logs de mapping et de transformation
- logs de matching / score de similarité
- logs d’audit et de consentement
- logs de validation de l’intégrité des données

## Format conseillé

- niveau (INFO, WARNING, ERROR)
- étape
- source
- identifiant interne si nécessaire
- message court et explicite

## Exemple

```text
INFO | extraction | source=pharmacy | rows_read=250 | status=success
WARN | deduplication | source=imaging | low_confidence_match | score=72
ERROR | load | target=postgres | table=master_patient | reason=constraint_violation
```

## Règles métier

- Les décisions de matching doivent garder la trace de la méthode utilisée.
- Les accès aux données doivent être audités si possible.
- Les logs doivent aider à expliquer la démonstration finale du projet.

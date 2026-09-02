# Logs et traçabilité

Toute journalisation → fichier racine `LOGS.md`. Aucune autre destination.

## Règles
- Lisibles, concis, structurés.
- Chaque étape importante journalisée : connexion, extraction, mapping, nettoyage, matching, chargement.
- Jamais de données patients réelles/sensibles.
- Les erreurs : contexte technique sans info sensible.

## Format
`niveau | étape | source | identifiant interne | message`

niveau = INFO / WARNING / ERROR

```
INFO | extraction | source=pharmacy | rows_read=250 | status=success
WARN | deduplication | source=imaging | low_confidence_match | score=72
ERROR| load | target=postgres | table=master_patient | reason=constraint_violation
```

## Règles métier
- Garder la trace de la méthode de matching.
- Auditer les accès si possible.
- Les logs aident à expliquer la démonstration.

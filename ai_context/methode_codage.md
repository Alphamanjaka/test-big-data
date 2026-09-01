# Méthode de codage

## Objectif

Produire un code clair, maintenable et démontrable en soutenance.

## Règles

- Favoriser la simplicité sur la complexité inutile.
- Séparer les responsabilités par couche : extraction, transformation, déduplication, chargement, dashboard, gouvernance.
- Utiliser des noms de fichiers, fonctions et variables explicites.
- Éviter les variables magiques : les constantes doivent être nommées et documentées.
- Écrire des fonctions courtes, cohérentes et testables.
- Garder les transformations traçables : chaque étape doit pouvoir être expliquée.
- Documenter les hypothèses métier dans le code ou dans la documentation.

## Architecture attendue

- extract/ : connexion et lecture des sources
- transform/ : mapping, standardisation et nettoyage
- deduplication/ : matching exact et probabiliste
- load/ : écriture vers PostgreSQL
- api/ : exposition des données ou endpoints utiles
- dashboard/ : métriques et visualisation
- tests/ : validation des cas critiques

## Bonnes pratiques

- Utiliser Python avec des modules bien isolés.
- Préférer Pandas / SQLAlchemy / FastAPI / Streamlit selon le besoin projet.
- Gérer proprement les erreurs sans masquer la cause.
- Ajouter des logs utiles mais sans exposer de données sensibles.
- Ne pas mélanger interface utilisateur, logique métier et extraction dans un même fichier.

## Contrôle qualité

- Écrire des tests pour les cas de doublon, valeurs nulles et formats hétérogènes.
- Vérifier qu’un score de matching est toujours explicite.
- Valider que chaque transformation conserve la traçabilité source → modèle canonique → master patient.

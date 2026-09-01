# AGENTS.md

## Références

- [ai_context/README.md](ai_context/README.md)
- [ai_context/methode_codage.md](ai_context/methode_codage.md)
- [ai_context/security.md](ai_context/security.md)
- [ai_context/suivi_avancement.md](ai_context/suivi_avancement.md)
- [ai_context/logs.md](ai_context/logs.md)

## Règle unique

MVP de centralisation de données patients : 3 sources hétérogènes, nettoyage, standardisation, mapping, déduplication explicable, PostgreSQL central, traçabilité, consentement, sécurité, démonstration claire.

## Priorité

1. Données fictives uniquement.
2. Respecter le périmètre MVP.
3. Garder la traçabilité source → transformation → master patient.
4. Ne pas fusionner sans logique explicable.
5. Préférer simplicité, lisibilité et démonstration.

## Travail attendu

1. Connecter les 3 sources.
2. Extraire et stocker RAW.
3. Mapper vers un modèle canonique.
4. Nettoyer et standardiser.
5. Dédupliquer exact puis probabiliste.
6. Créer master patient + identity map.
7. Charger PostgreSQL.
8. Produire le dashboard.
9. Valider le cas patient dupliqué.

## À éviter

- vraies données patients ;
- suppression des traces ;
- fusion arbitraire ;
- fonctionnalités hors MVP ;
- solution présentée comme “complète” alors qu’elle est un PoC.

# Sécurité et gouvernance

## Règles fondamentales

- Ne jamais utiliser de vraies données patients.
- Ne jamais exposer des informations sensibles dans les logs, le terminal ou les captures.
- Travailler uniquement avec des données fictives ou synthétiques.
- Considérer la donnée de santé comme sensible.

## Consentement

- Le consentement doit être traité comme un élément fonctionnel du système.
- Un accès ou un partage de données ne doit pas être effectué sans validation explicite du consentement.
- Les règles d’accès doivent être distinguées entre données brutes, nettoyées et consolidées.

## Traçabilité

- Conserver l’historique des transformations et du matching.
- Garder les liens source_system → source_patient_id → master_patient_id.
- Les décisions de matching doivent être explicables et auditables.

## Séparation des données

- Stocker séparément les données brutes, validées et consolidées.
- Ne pas fusionner directement des enregistrements sans score de confiance.
- Ne pas supprimer les éléments nécessaires à l’audit.

## Recommandations

- Masquer les valeurs sensibles dans les messages d’erreur et les sorties utilisateur.
- Utiliser des variables d’environnement pour les secrets et les paramètres sensibles.
- Vérifier les permissions d’accès avant toute exposition d’API ou de dashboard.

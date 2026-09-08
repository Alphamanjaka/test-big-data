# Sécurité et gouvernance

## Règles fondamentales
- Jamais de vraies données patients.
- Jamais d'infos sensibles dans logs / terminal / captures.
- Données fictives ou synthétiques uniquement.
- Donnée de santé = sensible.

## Consentement
- Élément fonctionnel du système.
- Pas d'accès/partage sans validation explicite.
- Distinguer données brutes / nettoyées / consolidées.

## Traçabilité
- Historique des transformations et du matching.
- Liens source_system → source_patient_id → master_patient_id.
- Décisions de matching explicables et auditables.

## Séparation des données
- Stocker séparément données brutes, validées, consolidées.
- Ne pas fusionner sans score de confiance.
- Ne pas supprimer les éléments d'audit.

## Recommandations
- Masquer les valeurs sensibles (erreurs, sorties).
- Variables d'environnement pour secrets.
- Vérifier les permissions avant toute exposition API/dashboard.

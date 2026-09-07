# AGENTS.md — Consignes projet DataLake Final

## Références (lire en début de session)

- `ai/dev/README.md` : index des consignes de developpement (fusion des `.ai_context`).
- `ai/memoire/README.md` : index des consignes de redaction du memoire.
- `documents/cahier_des_charges.md` : perimetre.
- `documents/documentation/` : manuel conceptuel (Big Data, de-duplication, consentement).

## Règle unique

Plateforme de centralisation et de gouvernance de **donnees patients synthetiques** : pipeline Big Data
Medallion (RAW→SILVER→GOLD) sur Hive/HDFS/Spark, de-duplication explicable exact+probabiliste
(master patient + identity map), consentement purpose-by-purpose, audit d'acces, rôles + cles API.

Priorites : **maitriser le sujet** (concepts Big Data et consentement) plutot que perfectionner un frontend.
Les donnees sont toujours fictives.

## Méthode de travail (traçabilité)

1. Toute session, fix, incident ou run ajoute une entree datée dans `ai/dev/logs.md` (**Logs**).
2. Etape MAJEURE (jalon cahier des charges) : en plus des logs, mettre a jour `ai/dev/suivi_avancement.md`
   et le(s) document(s) `documents/documentation/*` concerne(s).
3. Seuil : simple run / reboot / fix robustesse → logs uniquement.

## A ne JAMAIS faire

- Introduire de vraies donnees patients.
- Commiter `provision/config/data_sources.json`, `.env`, `provision/metadata/` ou le dossier `data/`.
- Fusionner sans logique explicable (chaque master patient doit etre justifie par un match).
- Rajouter des fonctionnalites hors perimetre (pas de frontend perfectionne).
- Reintroduire `sentence_transformers` (crash Python 3.8) → RapidFuzz + synonymes.
- Ecrire le warehouse Spark sur vboxsf → toujours `hdfs://localhost:9000/...`.
- Supprimer des traces / logs d'audit.
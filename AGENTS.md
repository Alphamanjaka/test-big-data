# AGENTS.md — Consignes projet (dépôt unique `Mon_Memoire`)

## Références (lire en début de session)

- `ai/dev/README.md` : index des consignes de developpement (fusion des `.ai_context`).
- `ai/memoire/README.md` : index des consignes de redaction du memoire (chapters/01..06).
- `documents/cahier_des_charges.md` : perimetre.
- `documents/documentation/` : manuel conceptuel (Big Data, de-duplication, consentement).
- `projet/code-source/` : code consolide (Big Data + moteur de de-duplication).
- `projet/mvp/` : PoC `test_bigdata` (niveaux 1 et 2) ; `archives/datalake_mavis/` : PoC Big Data d'origine.

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

## Hiérarchie des consignes

- Ce fichier définit les règles globales du dépôt.
- `ai/dev/` définit les règles opérationnelles du code consolidé.
- `ai/memoire/` définit les règles de rédaction et de démonstration.
- `projet/mvp/` et `archives/datalake_mavis/` sont des périmètres historiques ou locaux : leurs
  consignes ne s'appliquent pas au code consolidé sauf mention explicite.
- En cas de conflit, appliquer la règle la plus spécifique si elle reste compatible avec les règles
  globales ; sinon conserver la règle globale et documenter l'écart.

## Validation et communication

- Avant toute modification : identifier le chemin contrôlant le comportement, vérifier l'état Git et
  formuler une hypothèse vérifiable.
- Après une modification : exécuter le contrôle le plus ciblé disponible, puis vérifier les régressions
  pertinentes.
- Ne jamais annoncer un test, un résultat, une performance ou une fonctionnalité comme réalisé sans
  preuve dans la sortie d'une commande, un rapport ou un fichier versionné.
- Distinguer explicitement ce qui est réalisé, simulé, prévu, optionnel ou limité au PoC.
- Toute modification importante doit préserver la séparation ingestion, validation, nettoyage,
  normalisation, déduplication, MPI, gouvernance, audit et exposition.

## Git et dépendances

- Vérifier `git status` avant toute modification et ne jamais écraser les changements existants.
- Ne pas exécuter `git push`, `git reset --hard`, suppression distante ou commande destructive sans
  demande explicite.
- Avant commit, contrôler les tests ciblés, le scan des secrets et les fichiers générés/non commitables.
- Ajouter une dépendance seulement après avoir vérifié qu'une solution existante ne suffit pas et que la
  compatibilité Python 3.8 est préservée.

## A ne JAMAIS faire

- Introduire de vraies donnees patients.
- Commiter `provision/config/data_sources.json`, `.env`, `provision/metadata/` ou le dossier `data/`.
- Commiter de secrets en dur (mots de passe, cles, tokens) : hook `githooks/pre-commit` (active via
  `git config core.hooksPath githooks`) bloque les identifiants connus, les affectations de mots de passe,
  les valeurs PGPASSWORD entre guillemets et les DSN contenant un mot de passe. Externaliser via variables
  d'environnement / `.env` gitignore
  (template : `projet/code-source/provision/.env.example`).
- Fusionner sans logique explicable (chaque master patient doit etre justifie par un match).
- Rajouter des fonctionnalites hors perimetre (pas de frontend perfectionne).
- Reintroduire `sentence_transformers` (crash Python 3.8) → RapidFuzz + synonymes.
- Ecrire le warehouse Spark sur vboxsf → toujours `hdfs://localhost:9000/...`.
- Supprimer des traces / logs d'audit.

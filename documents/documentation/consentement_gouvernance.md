# Consentement et gouvernance

La donnée de santé est **sensible**. Le projet intègre la gouvernance comme **élément fonctionnel** du
système, et non comme un supplément : rôles (RBAC), **consentement purpose-by-purpose**, **audit des
accès** et **clés API** sécurisées. Toutes les données manipulées sont **synthétiques**.

## 1. Principes fondamentaux

- **Jamais de vraies données patients** — données fictives ou synthétiques uniquement.
- **Pas d'accès/partage sans validation explicite** du patient.
- Distinguer données **brutes / nettoyées / consolidées** (stockées séparément — zones RAW/SILVER/GOLD).
- **Ne pas fusionner sans score de confiance**.
- **Ne pas supprimer les éléments d'audit**.
- Ne jamais exposer d'identifiant brute-source ni de secret côté API : payloads RAW non exposés, clés
  API **hachées SHA-256**.

## 2. RBAC (rôles)

Deux systèmes coopéraient dans les projets sources, fusionnés ici sous une logique unique :

| Rôle | Accès données patient | Accès gouvernance | Accès admin |
|---|---|---|---|
| ADMIN (plateforme) / ADMIN (web) | Complet | Complet | Complet |
| MEDECIN (web) | Données métier RMA uniquement | Non | Non |
| analyst (plateforme) | Lecture agrégée | Lecture | Non |
| viewer (plateforme) | Lecture | Non | Non |

Règles web (NextAuth + JWT + `checkRole`) : `/users/*` réservé ADMIN (sinon 403/redirect) ; pages
métier authentifiées (sinon redirect `/login`). La plateforme expose 3 rôles (`admin`/`analyst`/`viewer`)
validés par clé API. Ne pas utiliser l'alias obsolète `DOCTOR`.

## 3. Consentement patient (purpose-by-purpose)

Modèle retenu pour la fusion : **table `consent` liée au `master_patient_id`**, portée par le
PostgreSQL central, et reflétée en **GOLD + API** sur le Data Lake.

| Colonne (réf. schéma) | Rôle |
|---|---|
| `consent_id` | Identifiant du consentement |
| `master_patient_id` | Patient concerné (via identity map) |
| `authorized_user_id` / rôle | Qui peut accéder |
| `purpose` | Finalité : consultation, recherche, statistique… |
| `data_scope` | Type de données couvertes (medical, labo, pharmacie) |
| `granted` | Booléen accordé / refusé |
| `granted_at`, `expires_at` | Durée de validité |

Flux :

```text
Demande d'accès → vérification du consentement (valide + granted + périmètre couvert)
                → AUTORISÉ (accès)   ou   REFUSÉ (access denied, auditée)
```

Le projet veille à démontrer le **consentement selon la finalité** : un accès est refusé si la finalité
n'est pas consentie, même pour un utilisateur autorisé. Implémentation de référence :
[`engine/governance/consent.py`](../../projet/code-source/engine/governance/consent.py).

## 4. Audit d'accès

Table `access_audit` — un enregistrement par tentative d'accès :

```text
qui (user/api key) · quoi (ressource) · quand (timestamp) · autorisé/refusé · détails
```

Toute consultation, extraction ou export est journalisée, y compris les **refus** (traçabilité des
violations potentielles). Les logs ne doivent **jamais** contenir de données sensibles.
Implémentation : [`engine/governance/audit.py`](../../projet/code-source/engine/governance/audit.py).

## 5. Clés API

Les utilisateurs machine (dashboard, intégrations) s'authentifient par clé API **hachée SHA-256** en
base. La clé en clair n'est jamais stockée ni exposée ; les clés de démo sont régénérées à chaque
exécution d'initialisation. Implémentation : [`engine/governance/auth.py`](../../projet/code-source/engine/governance/auth.py).

## 6. Schéma PostgreSQL central

```sql
-- ref : projet/code-source/sql/schema.sql
raw_patient_record      -- historique append-only de chaque extraction (RAW jamais exposé)
master_patient          -- identité unique (+ gender)
patient_identity_map    -- source_system → source_patient_id → master_patient_id (score + méthode)
consent                 -- consentement purpose-by-purpose
api_user                -- utilisateurs machine (clé SHA-256)
access_audit            -- journal d'accès
```

Idempotence : `ON CONFLICT` + `ADD COLUMN IF NOT EXISTS` (rejouable).

## 7. Endpoints de gouvernance

| Endpoint | Rôle |
|---|---|
| `GET /health` | État du service |
| `GET /metrics` | Indicateurs de gouvernance (source : doublons, qualité données) |
| `GET /patients` | Données maîtres (jamais les payloads RAW) |
| `GET /patients/{master_patient_id}` | Détail d'un patient |
| `GET /audit` | Journal des accès (ADMIN) |
| `GET /consent` / mutation | Consentements (lecture / mise à jour selon rôle) |

## 8. Gouvernance vs consentement (Démo)

Démo de référence à présenter :

1. 3 sources, 60 lignes RAW, 36 masters, 24 fusions exactes, 60 identity links, 108 consentements ;
2. un utilisateur sans rôle requis → **403** ;
3. un utilisateur autorisé mais **finalité non consentie** → refus audité ;
4. dashboard : KPIs doublons / qualité / consentements / accès.

## 9. Différence avec le projet Mavis

Le projet `datalake_mavis` avait le RBAC **web** (NextAuth/Prisma) mais le consentement/audit **Post-MVP**
(commenté dans le schéma Prisma). Le projet `test_bigdata` avait le consentement/audit **fonctionnel**
côté plateforme (SQLAlchemy/PG). La fusion (**dépôt unique**) porte le consentement/audit dans le
**moteur + PostgreSQL central + table GOLD du Data Lake** (décision : « Hive GOLD + API »), en plus du
RBAC web conservé en optionnel.
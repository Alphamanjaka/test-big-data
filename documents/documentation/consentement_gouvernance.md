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
| `purpose` | Finalité, **liste fermée** : `api_access`, `research`, `analytics` (contrainte `consent_purpose_check`) |
| `granted` | Booléen accordé / refusé |
| `recorded_at` | Horodatage de l'avis ; le **dernier avis** fait foi |

Flux :

```text
Demande d'accès → finalité déclarée (paramètre `purpose`, obligatoire)
                → vérification du consentement (dernier avis pour cette finalité)
                → AUTORISÉ (accès)   ou   REFUSÉ (403 + motif journalisé)
```

Le projet veille à démontrer le **consentement selon la finalité** : un accès est refusé si la finalité
n'est pas consentie, même pour un utilisateur autorisé. L'absence de ligne vaut **refus**
(*fail closed*). Implémentation de référence :
[`engine/governance/consent.py`](../../projet/code-source/engine/governance/consent.py)
(`PURPOSES`, `validate_purpose`, `check_consent`, `enforce_consent`, `consented_master_ids`).

**Écarts assumés** : ni `data_scope` (périmètre de données), ni `expires_at` (durée de validité), ni
`authorized_user_id` — le consentement est lié au **patient et à la finalité**, pas à une personne.
Ces colonnes figurent dans les versions antérieures de ce document ; elles ne sont pas dans le schéma
livré et ne doivent pas être réintroduites sans conception associée.

## 4. Audit d'accès

Table `access_audit` — un enregistrement par tentative d'accès :

```text
qui (user/api key) · quoi (ressource) · quand (accessed_at) · autorisé/refusé (response_status)
· finalité déclarée (purpose) · motif du refus (refusal_reason)
```

Toute consultation, extraction ou export est journalisée, y compris les **refus** (traçabilité des
violations potentielles) : le refus doit être **consultable**, pas seulement déduit du code HTTP. Les
logs ne doivent **jamais** contenir de données sensibles. Implémentation :
[`engine/governance/audit.py`](../../projet/code-source/engine/governance/audit.py).

Limites : le journal n'est **pas chiffré au repos** et la durée de traitement n'est pas persistée
(aucune colonne dédiée).

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

Idempotence : `ON CONFLICT` + `ADD COLUMN IF NOT EXISTS` + `DROP CONSTRAINT IF EXISTS` (rejouable).

## 7. Endpoints de gouvernance

API FastAPI `engine/governance/app.py` (rôles vérifiés par clé API) :

| Endpoint | Rôle | Particularité |
|---|---|---|
| `GET /health` | État du service | pas d'auth |
| `GET /metrics` | Indicateurs de gouvernance (source : doublons, qualité données) | admin / analyst |
| `GET /patients` | Données maîtres (jamais les payloads RAW) | `purpose` **obligatoire** ; patients non consentis **retirés** de la réponse |
| `GET /patients/{master_patient_id}` | Détail d'un patient | `purpose` **obligatoire** ; **403** si finalité non consentie |
| `GET /audit` | Journal des accès (admin) | inclut `purpose` et `refusal_reason` |
| `GET /consent` / mutation | Consentements (lecture admin/analyst, écriture admin) | `purpose` validée contre la liste fermée |

Codes de sortie : **401** (token manquant / clé inconnue), **403** (rôle insuffisant ou finalité non
consentie), **422** (`purpose` absente ou inconnue).

## 8. Gouvernance vs consentement (Démo)

Démo de référence à présenter :

1. 3 sources, 60 lignes RAW, 36 masters, 24 fusions exactes, 60 identity links, 108 consentements ;
2. un utilisateur sans rôle requis → **403** ;
3. un utilisateur autorisé mais **finalité non consentie** → **403** + motif journalisé ;
4. `GET /patients?purpose=research` → seuls les patients consentis sont listés ;
5. `GET /audit` → la trace du refus, avec `purpose` et `refusal_reason` ;
6. dashboard : KPIs doublons / qualité / consentements / accès.

Peut être rejouée sans base grâce à la suite de tests `projet/code-source/tests/test_governance_api.py`
(13 cas, chemin d'authentification réel, PostgreSQL simulé). Jeu de données :
`provision/db/seed_governance.py` (consentements mixtes : `api_access` accordé partout,
`research` à 70 %, `analytics` à 40 %).

## 9. Différence avec le projet Mavis

Le projet `datalake_mavis` avait le RBAC **web** (NextAuth/Prisma) mais le consentement/audit **Post-MVP**
(commenté dans le schéma Prisma). Le projet `test_bigdata` avait le consentement/audit **fonctionnel**
côté plateforme (SQLAlchemy/PG). La fusion (**dépôt unique**) porte le consentement/audit dans le
**moteur + PostgreSQL central + table GOLD du Data Lake** (décision : « Hive GOLD + API »), en plus du
RBAC web conservé en optionnel.
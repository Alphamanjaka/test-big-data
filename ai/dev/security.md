# Sécurité et gouvernance (consignes)

Sources : `ai_context/security.md` (test_bigdata) + `.ai_context/03_security_web.md` (Mavis).

## 1. Règles fondamentales

- **Jamais de vraies données patients** — données fictives ou synthétiques uniquement.
- **Jamais d'infos sensibles** dans les logs / terminal / captures.
- Donnée de santé = sensible, même synthétique en démo.

## 2. Consentement

- Élément fonctionnel du système, pas un supplément.
- **Pas d'accès/partage sans validation explicite** (purpose + périmètre + validité).
- Distinguer données brutes / nettoyées / consolidées (zones séparées).
- Consentement lié au `master_patient_id` (PostgreSQL central + table GOLD côté Data Lake).

## 3. Traçabilité & séparation

- Historique des transformations et du matching (`source_system → source_patient_id → master_patient_id`).
- Décisions de matching explicables et auditables (score + méthode).
- Ne pas fusionner sans score de confiance.
- **Ne jamais supprimer les éléments d'audit** — ne pas supprimer les traces.

## 4. Clés et secrets

- Secrets via variables d'environnement (`DATABASE_URL`, `POSTGRES_PASSWORD_*`), jamais commités.
- Clés API **hachées SHA-256** en base (`engine/governance/auth.py`) ; jamais en clair.

## 5. Règles web / API (front-optional + API Flask)

- NextAuth.js 4 (Credentials + JWT), adaptateur Prisma ; rôle **dans le JWT**.
- Rôles : `ADMIN` / `MEDECIN` (web) ; `admin` / `analyst` / `viewer` (plateforme). **Pas de `DOCTOR`**.
- Protection : `middleware.ts` → `/users/*` ADMIN seul ; pages métier authentifiées. `checkRole()` API
  → 401/403.
- **Ne jamais exposer** `password` ni clés dans les réponses API (`select` + destructuring).
- Mocks **côté backend** uniquement (`mock_data.py`, flag `mocked`), jamais côté frontend.
- API données : JWT côté Python à ajouter (dette sécurité).
- Vérifier les permissions avant toute exposition API/dashboard.

## 6. Recommandations

- Masquer les valeurs sensibles dans les erreurs et sorties.
- `.env` (front-optional) : valeurs réelles sans commentaires dans l'URL (casse NextAuth).
- Vérifier le consentement avant tout accès à une donnée patient (ne pas se fier au rôle seul).
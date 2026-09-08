# Module 2 : Implémentation de la Gouvernance Simplifiée (RBAC)

## Objectif

Mettre en place un mécanisme de **Contrôle d'Accès Basé sur les Rôles (RBAC)** simple pour sécuriser l'accès aux données via l'API. Cela constitue la première brique de la fonctionnalité de gouvernance requise par le thème de stage.

**Fichiers concernés :** Principalement le **backend Node.js/Express.js**.

---

## Portée du MVP (Priorité Absolue)

L'objectif est de prouver que l'accès aux données peut être contrôlé en fonction du profil de l'utilisateur.

### MVP - Étape 1 : Modélisation Statique des Rôles

- **Problème :** Il n'existe pas de système pour différencier les utilisateurs.
- **Action à réaliser :**
  1.  Définir deux rôles simples :
      - `ADMIN` : Peut accéder à toutes les données, y compris les indicateurs de gouvernance.
      - `MEDECIN` : Peut accéder aux données des patients (données métier), mais pas aux informations sensibles de gouvernance (ex: logs d'accès détaillés).
  2.  Créer une structure de données (par exemple, une simple table ou un fichier JSON de configuration) pour associer un utilisateur à un rôle.
      ```json
      // Exemple dans un fichier users.json
      [
        { "userId": "user1", "email": "admin@example.com", "role": "ADMIN" },
        { "userId": "user2", "email": "doctor@example.com", "role": "MEDECIN" }
      ]
      ```

### MVP - Étape 2 : Création d'un Middleware de Contrôle d'Accès

- **Problème :** Les routes de l'API sont ouvertes à tous les utilisateurs authentifiés.
- **Action à réaliser :**
  1.  Dans l'application Express.js, créer un _middleware_ (une fonction intermédiaire) nommé `checkRole`.
  2.  Ce middleware prendra en paramètre le rôle requis pour accéder à une route.
  3.  Il vérifiera le rôle de l'utilisateur connecté (information qui devrait être dans le token JWT après l'authentification) et le comparera au rôle requis.
  4.  Si l'utilisateur n'a pas le bon rôle, le middleware renverra une erreur `403 Forbidden`. Sinon, il passera à la fonction suivante.

### MVP - Étape 3 : Sécurisation des Routes de l'API

- **Problème :** Les routes ne sont pas protégées.
- **Action à réaliser :**
  1.  Appliquer le middleware `checkRole` aux routes existantes.

      ```javascript
      // Exemple de route sécurisée
      const { checkRole } = require("./middlewares/auth");

      // Seuls les ADMINS peuvent accéder à cette route
      router.get("/api/governance/stats", checkRole(["ADMIN"]), (req, res) => {
        // ... logique pour retourner les stats
      });

      // Les ADMINS et les MEDECINS peuvent voir les données patient
      router.get(
        "/api/patients",
        checkRole(["ADMIN", "MEDECIN"]),
        (req, res) => {
          // ... logique pour retourner les données patient
        },
      );
      ```

---

## Améliorations (Post-MVP / Tâches difficiles)

Ces tâches constituent le cœur de la gouvernance avancée et correspondent à la vision complète du projet.

- **Gestion du Consentement Patient :**
  - **Problème :** Le contrôle d'accès ne dépend pas du consentement du patient.
  - **Action :** Concevoir et implémenter un système complet où chaque accès à une donnée patient vérifie en temps réel si un consentement valide a été donné par ce dernier pour ce type d'usage et pour cet utilisateur.

- **Journalisation des Accès (Audit Log) :**
  - **Problème :** Les accès aux données ne sont pas tracés.
  - **Action :** Créer une table ou une collection pour enregistrer chaque tentative d'accès (qui, quoi, quand, autorisé/refusé).

## Validation

À la fin de ce module, un utilisateur authentifié avec le rôle `MEDECIN` ne devrait pas pouvoir accéder à une route réservée aux `ADMIN`s et devrait recevoir une erreur 403.

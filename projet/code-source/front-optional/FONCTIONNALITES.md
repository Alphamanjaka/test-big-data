# Fonctionnalites - DataViz Gouvernance

## Table des matieres

1. [Authentification et autorisation](#1-authentification-et-autorisation)
2. [Page de synthese](#2-page-de-synthese)
3. [Doublons](#3-doublons)
4. [Gouvernance et consentement](#4-gouvernance-et-consentement)
5. [Indicateur de donnees de demonstration](#5-indicateur-de-donnees-de-demonstration)
6. [Gestion des utilisateurs](#6-gestion-des-utilisateurs)
7. [Navigation et interface](#7-navigation-et-interface)
8. [Fichiers de stockage](#8-fichiers-de-stockage)

---

## 1. Authentification et autorisation

### Page de connexion (`/login`)

- Formulaire de connexion avec email et mot de passe
- Authentification via **NextAuth v4** avec strategy **JWT**
- Messages d'erreur en cas de identifiants incorrects
- Redirection automatique vers `/synthese` apres connexion

### Roles et permissions

| Role | Acces |
|------|-------|
| **ADMIN** | Toutes les routes + gestion des utilisateurs (`/users`) |
| **MEDECIN** | Parametres, Synthese, Doublons, Gouvernance |

### Protection des routes

Le middleware (`src/middleware.ts`) verifie le token JWT pour chaque requete :
- Routes admin (`/users/*`) : requis role `ADMIN`
- Routes protegees (`/settings`, `/doublons`, `/gouvernance`, `/synthese`, `/users`) : requis authentification
- Non connecte : redirection vers `/login?callbackUrl=<route>`
- Non autorise (MEDECIN sur route admin) : redirection vers `/synthese?denied=1`

### Comptes par defaut

| Email | Mot de passe | Role |
|-------|-------------|------|
| `dataviz@mmt.mg` | `dataviz` | ADMIN |
| `medecin@mmt.mg` | `dataviz` | MEDECIN |

---

## 2. Page de synthese

**Route :** `/synthese`
**Composant :** `src/app/synthese/page.tsx`

### Contenu

Reunit en une vue les deux volets metier alimentes par la zone GOLD :
- **Qualite d'identite** : patients maîtresses, doublons resolus et taux via
  `/api/governance/duplicates`
- **Consentement** : patients concernes, accords / refus via
  `/api/governance/consent`
- **Chaine de traitement** : rappel RAW → SILVER → GOLD, seules les couches
  pretes a l'usage sont exposees

### Comportement

- Les deux endpoints sont interroges en parallele (`Promise.all`)
- Le bandeau de demonstration apparait si au moins l'un des deux repond en
  mode mock
- Aucune valeur n'est recalculee : l'interface affiche les reponses telles
  quelles ; une valeur absente s'affiche `n/d`, jamais `0`

---

## 3. Doublons

**Route :** `/doublons`
**Composant :** `src/app/doublons/page.tsx`

### Contenu

- Cartes KPI issues de `/api/governance/duplicates` :
  - Patients en base et patients maîtresses (table des identites)
  - Doublons resolus et taux de doublon
- Tableau de repartition des correspondances par methode :
  - Exacte (identifiants identiques)
  - Probabiliste (similarite de noms / dates de naissance / genre)
  - Chaque ligne precise la justification d'une fusion

### Choix d'affichage

- Aucune valeur n'est recalculee cote interface : les KPIs reprennent tels quels
  la reponse du moteur
- Un taux affiche n'est donc jamais une moyenne front : il provient du backend
- Bandeau de demonstration des que `/api/governance/duplicates` repond en
  mode mock

---

## 4. Gouvernance et consentement

**Route :** `/gouvernance`
**Composant :** `src/app/gouvernance/page.tsx`

### Contenu

- Cartes KPI issues de `/api/governance/consent` (metadonnees de l'enveloppe) :
  - Patients concernes
  - Consentements accordes / total
  - Taux d'accord
- Tableau des consentements (une ligne par couple patient × finalite) :
  - Patient maître, identifiant patient, nom
  - Finalite : `api_access` (Acces API), `research` (Recherche), `analytics`
    (Analyse) — alphabets de `engine/governance/consent.py`
  - Decision (accorde / refuse) et date d'enregistrement
- Filtre par finalite pour verifier le principe purpose-by-purpose (un patient
  peut etre accorde en recherche et refuse en analyse)

### Choix d'affichage

- `patient_uuid` s'affiche `n/d` quand le jeu de demonstration ne le fournit pas
- Les noms viennent du jeu de demonstration : identifiants synthetiques, sans
  lien avec une personne reelle (mention affichee sous le tableau)
- Bandeau de demonstration des que l'endpoint repond en mode mock

---

## 5. Indicateur de donnees de demonstration

**Composant :** `src/components/MockedBanner.tsx`

Le backend signale dans l'enveloppe de reponse une execution en mode mock
(`mocked: true`) quand la zone GOLD/SILVER (Hive/warehouse) n'est pas joignable. Le
front n'inferre jamais ce statut : il le lit dans l'enveloppe, via
`resultOf()` dans `src/lib/api.ts`, et propage le drapeau jusqu'aux pages.

Comportement :
- Un bandeau ambre "Donnees de demonstration" s'affiche sur toute vue dont les
  chiffres ne proviennent pas de la zone GOLD
- Applique aux pages Synthese / Doublons / Gouvernance
- Le bandeau est masque des que la source reelle repond (`mocked: false`) :
  aucune bascule manuelle cote interface

---

## 6. Gestion des utilisateurs

**Route :** `/users` (admin uniquement)
**Composant :** `UserClient.tsx`

### Fonctionnalites CRUD

| Operation | Description | Methode API |
|-----------|-------------|-------------|
| **Lister** | Affiche tous les utilisateurs dans un tableau | `GET /api/users` |
| **Creer** | Formulaire modal pour ajouter un utilisateur | `POST /api/users` |
| **Editer** | Modifier les informations d'un utilisateur | `PUT /api/users/[id]` |
| **Supprimer** | Confirmation puis suppression | `DELETE /api/users/[id]` |

### Champs du formulaire

| Champ | Type | Obligatoire | Notes |
|-------|------|-------------|-------|
| Nom | text | Oui | `firstName` |
| Prenom | text | Oui | `lastName` |
| Email | email | Oui | Unique |
| Role | select | Oui | `MEDECIN` ou `ADMIN` |
| Mot de passe | password | Oui (creation uniquement) | Hashage via bcrypt |

### Securite

- Route protegee par middleware (role `ADMIN` requis)
- Les API routes utilisent `checkRole(["ADMIN"])` comme garde
- Le mot de passe n'est jamais affiche dans le tableau

---

## 7. Navigation et interface

### Sidebar (`src/components/Sidebar.tsx`)

- **Branding** : Logo + titre "DataViz Gouvernance"
- **Menu principal** :
  - Synthese (`/synthese`) - tous les roles
  - Doublons (`/doublons`) - tous les roles
  - Gouvernance (`/gouvernance`) - tous les roles
  - Gestion des utilisateurs (`/users`) - admin uniquement
  - Parametres (`/settings`) - tous les roles

### Header (`src/components/Header.tsx`)

- **Rappel** : Plateforme de gouvernance — donnees synthetiques et de demonstration
- **Info utilisateur** : Email de l'utilisateur connecte
- **Parametres** : Lien vers `/settings`
- **Deconnexion** : Bouton de deconnexion (redirige vers `/login`)

### AppWrapper (`src/app/AppWrapper.tsx`)

Layout wrapper combinant Sidebar + Header pour toutes les pages authentifiees.

---

## 8. Fichiers de stockage

### Base de donnees PostgreSQL

Schema Prisma (`prisma/schema.prisma`) avec les migrations :
- `20250817080916_init` : Creation initiale de la table User
- `20250817082705_init` : Ajout de `firstName` et `lastName`
- `20260824100000_rename_doctor_to_medecin` : Renommage du role `DOCTOR` en `MEDECIN`

### API Backend externe

L'application communique avec un serveur backend sur `localhost:5000` exposant les endpoints de gouvernance :

| Endpoint | Description |
|----------|-------------|
| `/api/governance/duplicates` | Statistiques de deduplication (doublons, methodes) |
| `/api/governance/consent` | Consentements purpose-by-purpose (liste + metadonnees) |
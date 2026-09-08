# Fonctionnalites - RMA DataViz

## Table des matieres

1. [Authentification et autorisation](#1-authentification-et-autorisation)
2. [Tableau de bord (Dashboard)](#2-tableau-de-bord-dashboard)
3. [Filtres globaux](#3-filtres-globaux)
4. [Visualisations RMA](#4-visualisations-rma)
5. [Gestion des utilisateurs](#5-gestion-des-utilisateurs)
6. [Navigation et interface](#6-navigation-et-interface)
7. [Fichiers de stockage](#7-fichiers-de-stockage)

---

## 1. Authentification et autorisation

### Page de connexion (`/login`)

- Formulaire de connexion avec email et mot de passe
- Authentification via **NextAuth v4** avec strategy **JWT**
- Messages d'erreur en cas de identifiants incorrects
- Redirection automatique vers la page demande apres connexion

### Roles et permissions

| Role | Acces |
|------|-------|
| **ADMIN** | Toutes les routes + gestion des utilisateurs (`/users`) |
| **MEDECIN** | Dashboard, parametres, visualisations RMA |

### Protection des routes

Le middleware (`src/middleware.ts`) verifie le token JWT pour chaque requete :
- Routes admin (`/users/*`) : requis role `ADMIN`
- Routes protegees (`/dashboard`, `/settings`, `/rma/*`) : requis authentification
- Non connecte : redirection vers `/login?callbackUrl=<route>`
- Non autorise (MEDECIN sur route admin) : redirection vers `/dashboard?denied=1`

### Comptes par defaut

| Email | Mot de passe | Role |
|-------|-------------|------|
| `dataviz@mmt.mg` | `dataviz` | ADMIN |
| `medecin@mmt.mg` | `dataviz` | MEDECIN |

---

## 2. Tableau de bord (Dashboard)

**Route :** `/dashboard`

### KPI Cards

Trois cartes d'indicateurs cles affichees en haut de page :

| KPI | Description | Source API |
|-----|-------------|------------|
| Total Admissions | Nombre total d'admissions hospitalieres | `/rma/admissions_summary` |
| Taux de Mortalite infantile | Taux de mortalite des nourrissons | `/rma/admissions_summary` |
| Taux de Mortalite maternelle | Taux de mortalite maternelle | `/rma/admissions_summary` |

Chaque carte affiche une valeur numerique, une icone coloree et une bordure laterale coloree.

### Top 5 des pathologies

Tableau affichant les 5 diagnostics les plus frequents :
- Code CIM-10
- Nom de la pathologie
- Nombre de cas
- Source API : `/rma/top_diagnostics`

### Comportement

- Les donnees sont fetch automatiquement au montage du composant
- Re-fetch automatique lors du changement de filtres (bouton "Voir")
- Indicateur de chargement (spinner) pendant le fetch
- Affichage de la periode selectionnee dans le titre du tableau

---

## 3. Filtres globaux

**Composant :** `src/components/Header.tsx`
**Contexte :** `src/context/FiltersContext.tsx`

### Filtres disponibles

| Filtre | Type | Options | Valeur par defaut |
|--------|------|---------|-------------------|
| Periode | DateRangePicker | Date debut / date fin | null (pas de filtre) |
| Sexe | Select | Tous / Homme / Femme | `all` |

### Fonctionnement

1. **Selection** : L'utilisateur modifie les filtres dans le Header
2. **Application** : Clic sur le bouton "Voir" pour appliquer les filtres
3. **Reset** : Clic sur "Reset" pour revenir aux valeurs par defaut
4. **Transmission** : Les filtres sont passes en parametres de query (`start_date`, `end_date`, `gender`) aux appels API

### Etat partage

Le contexte `FiltersContext` partage l'etat des filtres entre :
- Le Header (controles)
- Le Dashboard (fetch des KPIs)
- Les pages RMA (fetch des donnees de visualisation)

---

## 4. Visualisations RMA

### 4.1 Diagnostics consultations externes (Tableau 5)

**Route :** `/rma`
**Composant :** `DiagnosticsHeatmap.tsx`
**Statut :** Actif

#### Description

Visualisation des diagnostics CIM-10 des consultations externes, ventiles par tranches d'age.

#### Composants d'interface

- **Heatmap D3.js** : Matrice diagnostics (lignes) x tranches d'age (colonnes)
  - Tranches d'age : 0-28j, 29-59j, 2-11m, 1-4a, 5-14a, 15-24a, 25-59a, 60+
  - Degradation de couleurs pour representeer l'intensite des cas
  - Tooltips au survol avec les valeurs exactes
- **Tableau pagine** : Liste detaillee des diagnostics avec tri et pagination

#### Source API

- Heatmap : `/rma/diagnostics_heatmap?start_date=...&end_date=...&gender=...`
- Liste : `/rma/diagnostics_list?start_date=...&end_date=...&gender=...`

---

### 4.2 Morbidite et mortalite hospitaliere (Tableau 9)

**Route :** `/rma/morbidite`
**Composant :** `MortalityChart.tsx`
**Statut :** En developpement

#### Description

Visualisation du taux de mortalite hospitaliere par diagnostic principal.

#### Composants d'interface

- **Bar chart horizontal D3.js** :
  - Axe Y : Diagnostics CIM-10
  - Axe X : Taux de mortalite (%)
  - Couleurs par service (medecine, chirurgie, maternite)
  - Tooltips avec details par tranche d'age

#### Source API

- `/api/rma/mortality`

---

### 4.3 Consultations prenatales et Maternite (Tableaux 11 & 12)

**Route :** `/rma/maternite`
**Composant :** `MalariaKPI.tsx` (composant reutilise)
**Statut :** En developpement (donnees fictives)

#### Description

Suivi des activites de maternite : consultations prenatales (CPN) et accouchements.

#### Composants d'interface

- **KPI Cards** :
  - Taux de CPN >= 4 consultations
  - Nombre de deces maternels
  - Nombre d'avortements
- **Line chart D3.js** :
  - Evolution mensuelle des CPN1 vs Accouchements
  - Comparaison mois par mois

#### Source API

- Donnees actuellement **hardcodees** (echantillon Jan-Mar 2025)
- Pas encore connecte au backend API

---

### 4.4 Activite de laboratoire (Tableau 16)

**Route :** `/rma/laboratoire`
**Composant :** `LaboratoryChart.tsx`
**Statut :** En developpement

#### Description

Volume et taux de positivite des examens de laboratoire.

#### Composants d'interface

- **Donut chart D3.js** : Repartition du volume d'examens par type
- **Bar chart D3.js** : Taux de positivite par type d'examen
  - Types d'examens : BK, BH, palu, NFS, VIH, syphilis, hepatitis, etc.

#### Source API

- `/api/rma/laboratory`

---

### 4.5 Prise en charge Paludisme (Tableau 25)

**Route :** `/rma/paludisme`
**Composant :** `MalariaKPI.tsx`
**Statut :** En developpement

#### Description

Suivi des cas de paludisme : cas detectes, TDR effectues, traites, et prevention.

#### Composants d'interface

- **KPI Cards** :
  - Taux de positivite TDR
  - Taux de traitement
  - Statistiques de prevention (moustiquaires)
- **Line chart D3.js** :
  - Evolution mensuelle des cas vs cas traites
  - Visualisation des pics saisonniers

#### Source API

- `/api/rma/malaria`

---

## 5. Gestion des utilisateurs

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
| Role | select | Oui | `DOCTOR` ou `ADMIN` |
| Mot de passe | password | Oui (creation uniquement) | Hashage via bcrypt |

### Securite

- Route protegee par middleware (role `ADMIN` requis)
- Les API routes utilisent `checkRole(["ADMIN"])` comme garde
- Le mot de passe n'est jamais affiche dans le tableau

---

## 6. Navigation et interface

### Sidebar (`src/components/Sidebar.tsx`)

- **Branding** : Logo + titre "RMA DataViz"
- **Derniere synchro** : Affiche la date de derniere synchronisation du Data Lake (fetch depuis `/rma/last_sync`)
- **Menu principal** :
  - Accueil (`/dashboard`) - tous les roles
  - Gestion des utilisateurs (`/users`) - admin uniquement
- **Section RMA** (collapsible) :
  - Tableau 5 - Diagnostics consultations externes (`/rma`) - actif
  - Tableau 9 - Morbidite & Mortalite (`/rma/morbidite`) - en developpement
  - Tableaux 11 & 12 - CPN & Maternite (`/rma/maternite`) - en developpement
  - Tableau 16 - Activite de laboratoires (`/rma/laboratoire`) - en developpement
  - Tableau 25 - Paludisme (`/rma/paludisme`) - en developpement

### Header (`src/components/Header.tsx`)

- **Filtres** : DateRangePicker + Select sexe + boutons Voir/Reset
- **Info utilisateur** : Email de l'utilisateur connecte
- **Parametres** : Lien vers `/settings`
- **Deconnexion** : Bouton de deconnexion (redirige vers `/login`)

### AppWrapper (`src/app/AppWrapper.tsx`)

Layout wrapper combinant Sidebar + Header + FiltersProvider pour toutes les pages authentifiees.

---

## 7. Fichiers de stockage

### Base de donnees PostgreSQL

Schema Prisma (`prisma/schema.prisma`) avec les migrations :
- `20250817080916_init` : Creation initiale de la table User
- `20250817082705_init` : Ajout de `firstName` et `lastName`
- `20260824100000_rename_doctor_to_medecin` : Renommage du role `DOCTOR` en `MEDECIN`

### API Backend externe

L'application communique avec un serveur backend sur `localhost:5000` exposant les endpoints :

| Endpoint | Description |
|----------|-------------|
| `/rma/last_sync` | Date de derniere synchro du Data Lake |
| `/rma/diagnostics_heatmap` | Donnees pour la heatmap des diagnostics |
| `/rma/diagnostics_list` | Liste detaillee des diagnostics |
| `/rma/admissions_summary` | Resume des admissions (KPIs) |
| `/rma/top_diagnostics` | Top N des diagnostics les plus frequents |
| `/api/rma/mortality` | Donnees de mortalite |
| `/api/rma/laboratory` | Donnees de laboratoire |
| `/api/rma/malaria` | Donnees de paludisme |

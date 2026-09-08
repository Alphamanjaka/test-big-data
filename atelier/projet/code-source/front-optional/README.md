# RMA DataViz - Application Web de Visualisation

## Presentation du projet

**Nom du projet :** Data Lake MAVIS - Application Web de Visualisation
**Objectif :** Centralisation, traitement et visualisation de donnees de sante issues du **Rapport Mensuel d'Activite (RMA)** du CHRD2 Madagascar (Centre Hospitalier Regional de Diagnostic et de Demonstration).

Cette application web est le **frontend de visualisation** d'un pipeline Data Lake compose de :
- **Backend Data Lake :** Apache Spark, Hive, MongoDB, HBase (ETL, stockage, API REST)
- **Frontend :** Next.js 15 + D3.js + Tailwind CSS (interface de visualisation interactive)

Le projet vise a construire une architecture capable de gerer jusqu'a 100 sources de donnees differentes (PostgreSQL, Excel, CSV, etc.) dans le cadre de la digitalisation du systeme de sante a Madagascar.

### Stack technique

| Domaine       | Technologies                                              |
|---------------|-----------------------------------------------------------|
| Framework     | Next.js 15.4.6 (App Router + Turbopack)                  |
| Langage       | TypeScript 5.9                                            |
| Styling       | Tailwind CSS v4 + shadcn/ui (New York style, Zinc base)  |
| Visualisation | D3.js v7 (graphiques SVG customisés)                     |
| Authentification | NextAuth v4 (JWT + Prisma adapter)                     |
| Base de donnees | PostgreSQL via Prisma ORM 6.17                          |
| Composants UI | Radix UI primitives (~40 composants shadcn/ui)           |
| Icons         | Lucide React                                              |
| Notifications | React Toastify                                            |
| Dates         | date-fns + react-day-picker                               |

---

## Guide de demarrage

### Pre-requis

- **Node.js** (v18+ recommande, compatible Next.js 15)
- **PostgreSQL** en cours d'execution sur `localhost:5432`
- **Backend API** sur `localhost:5000` (le serveur Spark/Hive qui expose les endpoints `/rma/*`)

### Installation

```bash
# 1. Installer les dependances
npm install

# 2. Configurer les variables d'environnement
# Creer un fichier .env a la racine du projet :
NEXT_PUBLIC_SERVER_URL=http://localhost:5000
DATABASE_URL="postgresql://postgres:jonah@localhost:5432/datalake_user_db?schema=public"
NEXTAUTH_SECRET=48f565bf218679c77a57feb02969e6b059d24f1d0e9082e6d686d7c6ecbff195
NEXTAUTH_URL=http://localhost:3000

# 3. Initialiser la base de donnees
npx prisma migrate dev --name init

# 4. Peupler la base avec les utilisateurs par defaut
npx prisma db seed

# 5. Lancer le serveur de developpement
npm run dev
```

L'application est accessible sur **http://localhost:3000**.

### Comptes par defaut

| Role      | Email               | Mot de passe |
|-----------|---------------------|--------------|
| ADMIN     | dataviz@mmt.mg      | dataviz      |
| MEDECIN   | medecin@mmt.mg      | dataviz      |

### Commandes utiles

```bash
npm run dev      # Serveur de developpement (Turbopack)
npm run build    # Build de production
npm run start    # Demarrer le build de production
npm run lint     # Linter le code
```

---

## Structure du projet

```
visualisation_app/
├── prisma/
│   ├── schema.prisma          # Schema de la base de donnees
│   ├── seed.js                # Script de seed (utilisateurs par defaut)
│   └── migrations/            # Migrations Prisma
│
├── src/
│   ├── app/
│   │   ├── layout.tsx         # Layout racine
│   │   ├── page.tsx           # Page racine -> redirection vers /login
│   │   ├── globals.css        # Styles globaux (Tailwind v4)
│   │   │
│   │   ├── login/             # Page de connexion
│   │   ├── dashboard/         # Tableau de bord (KPIs + top diagnostics)
│   │   ├── rma/               # Visualisations RMA
│   │   │   ├── page.tsx                    # Tableau 5 - Diagnostics consultations externes
│   │   │   ├── morbidite/page.tsx          # Tableau 9 - Morbidite et mortalite
│   │   │   ├── maternite/page.tsx          # Tableaux 11 & 12 - Maternite / CPN
│   │   │   ├── laboratoire/page.tsx        # Tableau 16 - Activite de laboratoire
│   │   │   └── paludisme/page.tsx          # Tableau 25 - Paludisme
│   │   ├── settings/          # Parametres
│   │   ├── users/             # Gestion des utilisateurs (admin)
│   │   │
│   │   └── api/
│   │       ├── auth/          # Route NextAuth
│   │       └── users/         # API CRUD utilisateurs
│   │
│   ├── components/
│   │   ├── Header.tsx         # Barre superieure (filtres, user info, logout)
│   │   ├── Sidebar.tsx        # Barre laterale de navigation
│   │   ├── Heatmap.tsx        # Composant D3 heatmap generique
│   │   ├── Providers.tsx      # Wrapper NextAuth SessionProvider
│   │   │
│   │   ├── rma/
│   │   │   ├── DiagnosticsHeatmap.tsx    # Heatmap diagnostics x tranches d'age
│   │   │   ├── LaboratoryChart.tsx       # Donut + bar chart laboratoire
│   │   │   ├── MalariaKPI.tsx            # KPI cards + line chart paludisme
│   │   │   └── MortalityChart.tsx        # Bar chart horizontal mortalite
│   │   │
│   │   └── ui/                # ~40 composants shadcn/ui
│   │
│   ├── context/
│   │   └── FiltersContext.tsx # Filtres globaux (periode, sexe)
│   │
│   ├── lib/
│   │   ├── auth.ts            # Configuration NextAuth
│   │   ├── prisma.ts          # Client Prisma singleton
│   │   ├── rbac.ts            # Controle d'acces par role
│   │   └── utils.ts           # Utilitaires (cn pour Tailwind)
│   │
│   └── middleware.ts          # Protection des routes
│
├── pages/
│   └── api/rma/diagnostics.ts # Route API legacy (Pages Router)
│
├── public/                    # Assets statiques
├── .env                       # Variables d'environnement
├── components.json            # Config shadcn/ui
├── next.config.ts             # Config Next.js
├── tsconfig.json              # Config TypeScript
└── package.json               # Dependances et scripts
```

---

## Architecture

L'application suit une architecture **hybride client-serveur** :

1. **Server Components** (`page.tsx`) : Verification de l'authentification via `getServerSession()`, redirection des utilisateurs non connectes.
2. **Client Components** (`*Client.tsx`) : Toute l'interactivite, le fetch de donnees et les visualisations D3.
3. **Backend externe** (`localhost:5000`) : L'application proxy les requetes vers le serveur backend qui expose les endpoints RMA.

### Flux de donnees

```
Utilisateur -> Next.js Frontend -> API Backend (localhost:5000) -> Spark/Hive Data Lake
                                    |
                                    +-> PostgreSQL (auth, utilisateurs)
```

### Securite

- **Authentification** : NextAuth v4 avec strategy JWT + Prisma adapter
- **Autorisation** : RBAC (Role-Based Access Control) avec deux roles : `ADMIN` et `MEDECIN`
- **Middleware** : Protection des routes avec verification du token JWT
- **Routes admin** : `/users/*` restreintes au role `ADMIN`
- **Routes protegees** : `/dashboard`, `/settings`, `/rma/*` necessitent une authentification

---

## Visualisations RMA

L'application implmente 4 graphiques D3.js correspondant aux tableaux du RMA :

| Route | Tableau RMA | Type de graphique | Statut |
|-------|-------------|-------------------|--------|
| `/rma` | Tableau 5 - Diagnostics consultations externes (CIM-10) | Heatmap (diagnostics x tranches d'age) + tableau pagine | Actif |
| `/rma/morbidite` | Tableau 9 - Morbidite et mortalite hospitaliere | Bar chart horizontal (taux de mortalite par diagnostic) | En developpement |
| `/rma/maternite` | Tableaux 11 & 12 - CPN et Maternite | Line chart + KPI cards | En developpement (donnees fictives) |
| `/rma/laboratoire` | Tableau 16 - Activite de laboratoire | Donut chart + bar chart | En developpement |
| `/rma/paludisme` | Tableau 25 - Prise en charge Paludisme | Line chart + KPI cards | En developpement |

---

## Environnement

Le fichier `.env` doit contenir :

```env
# URL du backend API (Spark/Hive)
NEXT_PUBLIC_SERVER_URL=http://localhost:5000

# Connexion PostgreSQL (authentification)
DATABASE_URL="postgresql://postgres:jonah@localhost:5432/datalake_user_db?schema=public"

# Secrets NextAuth
NEXTAUTH_SECRET=48f565bf218679c77a57feb02969e6b059d24f1d0e9082e6d686d7c6ecbff195
NEXTAUTH_URL=http://localhost:3000
```

# DataViz Gouvernance - Application Web de Visualisation

## Presentation du projet

**Nom du projet :** Plateforme de gouvernance des donnees patients
**Objectif :** Centralisation et gouvernance de donnees patients synthetiques :
pipeline Big Data Medallion (RAW→SILVER→GOLD) sur Hive/HDFS/Spark,
de-duplication explicable (exact + probabiliste, master patient + identity map),
consentement purpose-by-purpose, audit et roles + cles API.

Cette application web est le **frontend de presentation** des deux volets metier
exposes depuis le warehouse :
- **Qualite d'identite** : resultats de la de-duplication (masters, doublons, methodes)
- **Consentement** : decisions purpose-by-purpose enregistrees en GOLD

Le backend de donnees expose les indicateurs via `hive_api.py` (Flask + PySpark).

### Stack technique

| Domaine       | Technologies                                              |
|---------------|-----------------------------------------------------------|
| Framework     | Next.js 15.4.6 (App Router + Turbopack)                  |
| Langage       | TypeScript 5.9                                            |
| Styling       | Tailwind CSS v4 + shadcn/ui (New York style, Zinc base)  |
| Authentification | NextAuth v4 (JWT + Prisma adapter)                     |
| Base de donnees | PostgreSQL via Prisma ORM 6.17                          |
| Composants UI | Radix UI primitives (~40 composants shadcn/ui)           |
| Icons         | Lucide React                                              |
| Notifications | React Toastify                                            |

---

## Guide de demarrage

### Pre-requis

- **Node.js** (v18+ recommande, compatible Next.js 15)
- **PostgreSQL** en cours d'execution sur `localhost:5432`
- **Backend API** sur `localhost:5000` (le serveur Spark/Hive qui expose les endpoints `/api/governance/*`)

### Installation

```bash
# 1. Installer les dependances
npm install

# 2. Configurer les variables d'environnement
# Creer un fichier .env a la racine du projet :
NEXT_PUBLIC_SERVER_URL=http://localhost:5000
DATABASE_URL="postgresql://postgres:<PASSWORD>@localhost:5432/datalake_user_db?schema=public"
NEXTAUTH_SECRET=<GENERATE_A_RANDOM_64_HEX_VALUE>
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
front-optional/
├── prisma/
│   ├── schema.prisma          # Schema de la base de donnees
│   ├── seed.js                # Script de seed (utilisateurs par defaut)
│   └── migrations/            # Migrations Prisma
│
├── src/
│   ├── app/
│   │   ├── layout.tsx         # Layout racine
│   │   ├── page.tsx           # Page racine -> redirection vers /synthese
│   │   ├── globals.css        # Styles globaux (Tailwind v4)
│   │   │
│   │   ├── login/             # Page de connexion
│   │   ├── synthese/          # Synthese (qualite d'identite + consentement)
│   │   ├── doublons/          # KPIs de de-duplication
│   │   ├── gouvernance/       # Consentements purpose-by-purpose
│   │   ├── settings/          # Parametres
│   │   └── users/             # Gestion des utilisateurs (admin)
│   │
│   ├── components/
│   │   ├── Header.tsx         # Barre superieure (info utilisateur, logout)
│   │   ├── Sidebar.tsx        # Barre laterale de navigation
│   │   ├── MockedBanner.tsx   # Bandeau "donnees de demonstration"
│   │   │
│   │   └── ui/                # Composants shadcn/ui
│   │
│   ├── lib/
│   │   ├── api.ts             # Client API gouvernance (getDuplicates, getConsent)
│   │   ├── auth.ts            # Configuration NextAuth
│   │   ├── prisma.ts          # Client Prisma singleton
│   │   ├── rbac.ts            # Controle d'acces par role
│   │   └── utils.ts           # Utilitaires (cn pour Tailwind)
│   │
│   └── middleware.ts          # Protection des routes
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
2. **Client Components** (`*Client.tsx`) : Toute l'interactivite, le fetch de donnees et l'affichage des KPIs.
3. **Backend externe** (`localhost:5000`) : L'application lit les indicateurs de gouvernance exposes par `hive_api.py`.

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
- **Routes protegees** : `/settings`, `/synthese`, `/doublons`, `/gouvernance` necessitent une authentification

---

## Pages

| Route | Contenu | Source API |
|-------|---------|------------|
| `/` | Redirection vers `/synthese` | — |
| `/synthese` | Synthese : qualite d'identite + consentement + chaine RAW/SILVER/GOLD | `/api/governance/duplicates`, `/api/governance/consent` |
| `/doublons` | KPIs de de-duplication (masters, doublons, taux, methodes) | `/api/governance/duplicates` |
| `/gouvernance` | Consentements purpose-by-purpose + filtre par finalite | `/api/governance/consent` |
| `/settings` | Parametres du compte | — |
| `/users` | Gestion des utilisateurs (admin) | `/api/users` |

> Chaque page affiche un bandeau "Donnees de demonstration" quand le backend
> repond en mode mock (`mocked: true` dans l'enveloppe) : aucune valeur n'est
> jamais presentee comme issue de donnees reelles.

---

## Environnement

Le fichier `.env` doit contenir :

```env
# URL du backend API (Spark/Hive)
NEXT_PUBLIC_SERVER_URL=http://localhost:5000

# Connexion PostgreSQL (authentification)
DATABASE_URL="postgresql://postgres:<PASSWORD>@localhost:5432/datalake_user_db?schema=public"

# Secrets NextAuth
NEXTAUTH_SECRET=<GENERATE_A_RANDOM_64_HEX_VALUE>
NEXTAUTH_URL=http://localhost:3000
```
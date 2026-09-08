# Module 3 : Frontend — Application Web de Visualisation

## Objectif

Concevoir et implémenter une application web de visualisation des données médicales du Data Lake, permettant aux utilisateurs (ADMIN, MEDECIN) de consulter les indicateurs RMA, gérer les utilisateurs et suivre l'activité hospitalière via des graphiques interactifs D3.js.

**Technologies :** Next.js 15 (App Router), TypeScript, Tailwind CSS, shadcn/ui, D3.js v7, NextAuth v4, Prisma ORM

**Répertoire :** `visualisation_app/`

---

## Portée du MVP (Priorité Absolue)

### MVP - Étape 1 : Authentification et Layout

| Tâche | Fichier | Statut |
|-------|---------|--------|
| Page de connexion (email/password) | `src/components/login.tsx` | ✅ |
| NextAuth Credentials + JWT | `src/lib/auth.ts` | ✅ |
| Rôle dans le JWT (ADMIN/MEDECIN) | `src/lib/auth.ts` | ✅ |
| Middleware protection routes | `src/middleware.ts` | ✅ |
| Layout Sidebar + Header | `src/app/AppWrapper.tsx` | ✅ |
| Sidebar navigation adaptative | `src/components/Sidebar.tsx` | ✅ |
| Header avec filtres | `src/components/Header.tsx` | ✅ |

### MVP - Étape 2 : Dashboard et KPIs

| Tâche | Fichier | Statut |
|-------|---------|--------|
| KPI Total Admissions | `src/app/dashboard/DashboardClient.tsx` | ✅ |
| KPI Taux mortalité infantile | `src/app/dashboard/DashboardClient.tsx` | ✅ |
| KPI Taux mortalité maternelle | `src/app/dashboard/DashboardClient.tsx` | ✅ |
| Tableau Top 5 pathologies (CIM-10) | `src/app/dashboard/DashboardClient.tsx` | ✅ |
| Intégration filtres globaux | `src/context/FiltersContext.tsx` | ✅ |

### MVP - Étape 3 : Visualisations RMA

| Tâche | Tableau RMA | Fichier | Statut |
|-------|-------------|---------|--------|
| Heatmap D3.js (diagnostics × tranches d'âge) | T5 - Diagnostics | `src/components/rma/DiagnosticsHeatmap.tsx` | ✅ |
| Vue tableau paginée | T5 - Diagnostics | `src/app/rma/page.tsx` | ✅ |
| Bar chart horizontal (taux mortalité) | T9 - Morbidité | `src/components/rma/MortalityChart.tsx` | ✅ |
| Line chart (CPN1 vs Accouchements) + KPI cards | T11/12 - Maternité | `src/app/rma/maternite/page.tsx` | ✅ |
| Donut chart + bar chart (examens) | T16 - Laboratoire | `src/components/rma/LaboratoryChart.tsx` | ✅ |
| Line chart (cas vs traités) + KPI cards | T25 - Paludisme | `src/components/rma/MalariaKPI.tsx` | ✅ |

### MVP - Étape 4 : Gestion des Utilisateurs

| Tâche | Fichier | Statut |
|-------|---------|--------|
| Liste des utilisateurs | `src/app/users/UserClient.tsx` | ✅ |
| Formulaire création (modal) | `src/app/users/UserClient.tsx` | ✅ |
| Formulaire édition (modal) | `src/app/users/UserClient.tsx` | ✅ |
| Suppression avec confirmation | `src/app/users/UserClient.tsx` | ✅ |
| API CRUD protégée (ADMIN) | `src/app/api/users/` | ✅ |

### MVP - Étape 5 : Filtres et Paramètres

| Tâche | Fichier | Statut |
|-------|---------|--------|
| Filtre date range | `src/components/Header.tsx` | ✅ |
| Filtre sexe (Tous/Homme/Femme) | `src/components/Header.tsx` | ✅ |
| Filtre tranche d'âge (8 tranches RMA) | `src/components/Header.tsx` | ✅ |
| Bouton Voir (appliquer) / Reset | `src/components/Header.tsx` | ✅ |
| Page Settings (profil + mot de passe) | `src/app/settings/SettingsClient.tsx` | ✅ |
| Dernière synchro Data Lake | `src/components/Sidebar.tsx` | ✅ |

---

## Améliorations (Post-MVP)

| Tâche | Description | Priorité |
|-------|-------------|----------|
| Intégration backend réel | Connecter les pages RMA aux vrais endpoints `/rma/*` | Haute |
| Filtre âge sur données réelles | Brancher `age_range` aux endpoints backend | Moyenne |
| Export PDF/Excel | Exportation des graphiques et tableaux | Moyenne |
| Notifications | Alertes email/SMS pour seuils critiques | Basse |
| Mode sombre | Dark mode dans les paramètres | Basse |
| Responsive mobile | Adaptation tablettes/téléphones | Basse |

---

## Bugs corrigés (26/08/2026)

| Bug | Fichier | Correction |
|-----|---------|------------|
| Double `?` dans URL top_diagnostics | `FiltersContext.tsx:76` | `?...?limit=5` → `?...&limit=5` |
| Role `DOCTOR` envoyé au lieu de `MEDECIN` | `UserClient.tsx:181` | `<option value="DOCTOR">` → `<option value="MEDECIN">` |
| Hash mot de passe exposé en API | `api/users/route.ts`, `[id]/route.ts` | `select: { password: false }` |
| Redirect `/auth/login` inexistant | `dashboard/page.tsx`, `settings/page.tsx` | → `/login` |
| Credentials admin pré-remplis | `login.tsx` | `useState("")` au lieu de valeurs |

---

## Validation

1. `npm run build` ✅ — Compile sans erreur
2. `npx next lint` ✅ — 0 erreurs
3. Toutes les pages RMA accessibles depuis la Sidebar
4. Filtres fonctionnels (date, sexe, âge)
5. CRUD utilisateurs opérationnel (ADMIN seulement)
6. Login/Logout fonctionnel avec redirection

---

## Avancement : ~90% ✅

**Statut :** Fonctionnel avec données fictives. Prochaine étape : intégration des données réelles du backend Spark.

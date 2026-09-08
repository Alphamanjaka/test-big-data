# Structure de l'interface - RMA DataViz

## Architecture generale de l'interface

L'application suit un layout compose de trois elements principaux :

```
+------------------------------------------------------------------+
|                           HEADER                                  |
|  [DateRangePicker] [Sexe: Tous v] [Voir] [Reset]  [User] [⚙] [⏻]|
+------------------------------------------------------------------+
|            |                                                       |
|  SIDEBAR   |                    CONTENU PRINCIPAL                  |
|  (240px)   |                                                       |
|            |  +---------------------------------------------------+|
|  [Logo]    |  |                                                   ||
|  RMA DataV |  |              Pages / Visualisations                ||
|            |  |                                                   ||
|  Derniere  |  |                                                   ||
|  synchro   |  |                                                   ||
|            |  +---------------------------------------------------+|
|  Accueil   |                                                       |
|  Utilisat. |                                                       |
|            |                                                       |
|  Rapports  |                                                       |
|  > T.5     |                                                       |
|  > T.9     |                                                       |
|  > T.11/12 |                                                       |
|  > T.16    |                                                       |
|  > T.25    |                                                       |
|            |                                                       |
+------------------------------------------------------------------+
```

### Layout de l'application

| Element | Position | Taille | Composant |
|---------|----------|--------|-----------|
| Sidebar | Gauche, fixe | 240px de large, pleine hauteur | `src/components/Sidebar.tsx` |
| Header | Haut, dans la zone principale | Pleine largeur | `src/components/Header.tsx` |
| Contenu | Centre, sous le Header | Reste de l'espace | Pages individuelles |

### Providers

L'interface est enveloppee par deux providers :
1. **`Providers`** (`src/components/Providers.tsx`) : Fournit le `SessionProvider` de NextAuth
2. **`FiltersProvider`** (`src/context/FiltersContext.tsx`) : Fournit l'etat des filtres globaux (periode, sexe)

---

## Pages et routes

### Pages publiques

| Route | Page | Description |
|-------|------|-------------|
| `/login` | `src/app/login/page.tsx` | Page de connexion (pas de Sidebar/Header) |
| `/` | `src/app/page.tsx` | Redirige automatiquement vers `/login` |

### Pages authentifiees

| Route | Page | Composant client | Description |
|-------|------|------------------|-------------|
| `/dashboard` | `src/app/dashboard/page.tsx` | `DashboardClient.tsx` | Tableau de bord avec KPIs |
| `/rma` | `src/app/rma/page.tsx` | `DiagnosticsHeatmap.tsx` | Heatmap des diagnostics (Tableau 5) |
| `/rma/morbidite` | `src/app/rma/morbidite/page.tsx` | `MortalityChart.tsx` | Taux de mortalite (Tableau 9) |
| `/rma/maternite` | `src/app/rma/maternite/page.tsx` | `MalariaKPI.tsx` | Maternite et CPN (Tableaux 11 & 12) |
| `/rma/laboratoire` | `src/app/rma/laboratoire/page.tsx` | `LaboratoryChart.tsx` | Activite laboratoire (Tableau 16) |
| `/rma/paludisme` | `src/app/rma/paludisme/page.tsx` | `MalariaKPI.tsx` | Paludisme (Tableau 25) |
| `/settings` | `src/app/settings/page.tsx` | `SettingsClient.tsx` | Parametres (en cours de developpement) |

### Pages admin uniquement

| Route | Page | Composant client | Description |
|-------|------|------------------|-------------|
| `/users` | `src/app/users/page.tsx` | `UserClient.tsx` | Gestion des utilisateurs |

---

## Structure du Sidebar

```
Sidebar (240px, fond gris fonce #1a1a2e)
|
+-- Header Sidebar
|   +-- Logo (icone Activity + "RMA DataViz")
|   +-- "Derniere synchro : <date>"
|
+-- Menu principal
|   +-- Accueil (icone Home)          -> /dashboard
|   +-- Gestion des utilisateurs*     -> /users
|       (icone Users, admin seulement)
|
+-- Section "Rapports RMA" (collapsible)
    +-- Tableau 5 - Diagnostics...    -> /rma
    +-- Tableau 9 - Morbidite*        -> /rma/morbidite
    +-- Tableaux 11 & 12 - Maternite* -> /rma/maternite
    +-- Tableau 16 - Laboratoire*     -> /rma/laboratoire
    +-- Tableau 25 - Paludisme*       -> /rma/paludisme

* = en developpement (commente dans le code)
```

---

## Structure du Header

```
Header (pleine largeur, bordure inferieure, fond blanc)
|
+-- Gauche (filtres)
|   +-- DatePickerWithRange (280px)
|   +-- Select Sexe (120px) : Tous / Homme / Femme
|   +-- Bouton "Voir" (applique les filtres)
|   +-- Bouton "Reset" (reinitialise les filtres)
|
+-- Droite (infos utilisateur)
    +-- Icone User + email de l'utilisateur
    +-- Bouton Parametres (icone Settings) -> /settings
    +-- Bouton Deconnexion (icone LogOut) -> /login
```

---

## Structure du Dashboard

```
Dashboard (/dashboard)
|
+-- KPI Cards (grille responsive 1-2-4 colonnes)
|   +-- Total Admissions (icone BarChart3, bordure rouge)
|   +-- Taux Mortalite infantile (icone HeartPulse, bordure verte)
|   +-- Taux Mortalite maternelle (icone Venus, bordure orange)
|
+-- Top 5 des pathologies
    +-- Titre : "Top 5 des pathologies du <date_debut> au <date_fin>"
    +-- Tableau
        +-- En-tete : Code CIM-10 | Pathologie | Nombre de cas
        +-- Lignes : donnees fetch depuis /rma/top_diagnostics
```

---

## Structure des pages RMA

### Page Diagnostics (Tableau 5)

```
/rma
|
+-- Heatmap D3.js
|   +-- Axe Y : Diagnostics CIM-10
|   +-- Axe X : Tranches d'age (0-28j, 29-59j, 2-11m, 1-4a, 5-14a, 15-24a, 25-59a, 60+)
|   +-- Couleurs : Degradation representant l'intensite
|   +-- Tooltips : Valeurs exactes au survol
|
+-- Tableau pagine
    +-- Colonnes : Code CIM-10 | Diagnostic | Total | Detail par age
    +-- Pagination et tri
```

### Page Morbidite (Tableau 9)

```
/rma/morbidite
|
+-- Bar chart horizontal D3.js
    +-- Axe Y : Diagnostics CIM-10
    +-- Axe X : Taux de mortalite (%)
    +-- Couleurs : Par service (medecine, chirurgie, maternite)
    +-- Tooltips : Details par tranche d'age
```

### Page Maternite (Tableaux 11 & 12)

```
/rma/maternite
|
+-- KPI Cards
|   +-- Taux CPN >= 4
|   +-- Deces maternels
|   +-- Avortements
|
+-- Line chart D3.js
    +-- Axe X : Mois
    +-- Axe Y : Nombre
    +-- Lignes : CPN1 vs Accouchements
```

### Page Laboratoire (Tableau 16)

```
/rma/laboratoire
|
+-- Donut chart D3.js (volume d'examens par type)
|
+-- Bar chart D3.js (taux de positivite par type)
    +-- Types : BK, BH, palu, NFS, VIH, syphilis, hepatitis...
```

### Page Paludisme (Tableau 25)

```
/rma/paludisme
|
+-- KPI Cards
|   +-- Taux positivite TDR
|   +-- Taux de traitement
|   +-- Prevention (moustiquaires)
|
+-- Line chart D3.js
    +-- Evolution mensuelle : cas vs cas traites
    +-- Visualisation des pics saisonniers
```

---

## Page de gestion des utilisateurs

```
/users (admin uniquement)
|
+-- En-tete
|   +-- Titre : "Gestion des utilisateurs"
|   +-- Bouton "Ajouter utilisateur"
|
+-- Tableau des utilisateurs
|   +-- Colonnes : Nom | Email | Role | Actions
|   +-- Actions : Editer (jaune) | Supprimer (rouge)
|
+-- Modal (creation/edition)
    +-- Champs : Nom, Prenom, Email, Role (select), Mot de passe
    +-- Bouton : Creer / Sauvegarder
```

---

## Composants UI utilises

L'application utilise **shadcn/ui** (New York style, Zinc base) avec les composants suivants :

### Composants de mise en page
- `Card` (CardHeader, CardTitle, CardDescription, CardContent)
- `Separator`
- `ScrollArea`
- `Resizable`

### Composants de formulaire
- `Button`
- `Input`
- `Select` (SelectTrigger, SelectValue, SelectContent, SelectItem)
- `Label`
- `Checkbox`
- `Switch`
- `Textarea`
- `RadioGroup`
- `Slider`

### Composants de navigation
- `NavigationMenu`
- `Menubar`
- `Tabs`
- `Accordion`
- `Breadcrumb`

### Composants de presentation
- `Badge`
- `Avatar`
- `Alert`
- `Progress`
- `Tooltip`
- `HoverCard`

### Composants de dialogue
- `Dialog`
- `AlertDialog`
- `Sheet`
- `Drawer`
- `Popover`
- `Toast` / `Toaster`

### Composants de donnees
- `Table`
- `Pagination`
- `Carousel`
- `Calendar`
- `DatePicker` (via react-day-picker)

### Composants utilitaires
- `Collapsible`
- `Command`
- `ContextMenu`
- `DropdownMenu`
- `Toggle` / `ToggleGroup`
- `Skeleton`
- `AspectRatio`
- `InputOTP`

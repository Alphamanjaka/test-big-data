# Structure de l'interface - DataViz Gouvernance

## Architecture generale de l'interface

L'application suit un layout compose de trois elements principaux :

```
+------------------------------------------------------------------+
|                           HEADER                                  |
|  [Rappel plateforme gouvernance]                [User] [⚙] [⏻]   |
+------------------------------------------------------------------+
|            |                                                       |
|  SIDEBAR   |                    CONTENU PRINCIPAL                  |
|  (240px)   |                                                       |
|            |  +---------------------------------------------------+|
|  [Logo]    |  |                                                   ||
|  DataViz   |  |              Pages Gouvernance                    ||
|            |  |                                                   ||
|  Synthese  |  |                                                   ||
|  Doublons  |  |                                                   ||
|  Gouv.     |  |                                                   ||
|  Utilisat. |  |                                                   ||
|  Param.    |  |                                                   ||
|            |  +---------------------------------------------------+|
+------------------------------------------------------------------+
```

### Layout de l'application

| Element | Position | Taille | Composant |
|---------|----------|--------|-----------|
| Sidebar | Gauche, fixe | 240px de large, pleine hauteur | `src/components/Sidebar.tsx` |
| Header | Haut, dans la zone principale | Pleine largeur | `src/components/Header.tsx` |
| Contenu | Centre, sous le Header | Reste de l'espace | Pages individuelles |

### Providers

L'interface est enveloppee par le provider :
1. **`Providers`** (`src/components/Providers.tsx`) : Fournit le `SessionProvider` de NextAuth

---

## Pages et routes

### Pages publiques

| Route | Page | Description |
|-------|------|-------------|
| `/login` | `src/app/login/page.tsx` | Page de connexion (pas de Sidebar/Header) |
| `/` | `src/app/page.tsx` | Redirige automatiquement vers `/synthese` |

### Pages authentifiees

| Route | Page | Composant client | Description |
|-------|------|------------------|-------------|
| `/synthese` | `src/app/synthese/page.tsx` | — | Synthese : qualite d'identite + consentement + chaine |
| `/doublons` | `src/app/doublons/page.tsx` | — | KPIs de de-duplication (masters, doublons, taux, methodes) |
| `/gouvernance` | `src/app/gouvernance/page.tsx` | — | Consentements purpose-by-purpose + filtre par finalite |
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
|   +-- Logo (icone Activity + "DataViz Gouvernance")
|
+-- Menu principal
|   +-- Synthese (icone Layers)            -> /synthese
|   +-- Doublons (icone CopyCheck)         -> /doublons
|   +-- Gouvernance (icone ShieldCheck)    -> /gouvernance
|   +-- Gestion des utilisateurs* (icone Users) -> /users
|       (admin seulement)
|   +-- Parametres (icone Settings)        -> /settings
```

---

## Structure du Header

```
Header (pleine largeur, bordure inferieure, fond blanc)
|
+-- Gauche
|   +-- Rappel : "Plateforme de gouvernance des donnees patients
|       — donnees synthetiques et de demonstration."
|
+-- Droite (infos utilisateur)
    +-- Icone User + email de l'utilisateur
    +-- Bouton Parametres (icone Settings) -> /settings
    +-- Bouton Deconnexion (icone LogOut) -> /login
```

---

## Structure de la page Synthese

```
Synthese (/synthese)
|
+-- MockedBanner (si au moins une source repond en mode mock)
|
+-- Cartes KPI (grille 1-2 colonnes)
|   +-- Qualite d'identite (icone CopyCheck)
|   |   +-- Patients maîtresses | Doublons resolus | Taux de doublon
|   +-- Consentement (icone ShieldCheck)
|       +-- Patients concernes | Accords (granted/total) | Refus
|
+-- Chaine de traitement
    +-- RAW : donnees sources conservees telles quelles
    +-- SILVER : donnees normalisees, nettoyees, validees
    +-- GOLD : donnees de reference, dedupliquees, pretes a l'usage
```

---

## Structure de la page Doublons

```
Doublons (/doublons)
|
+-- MockedBanner (si mock)
|
+-- Cartes KPI
|   +-- Patients en base | Patients maîtresses | Doublons | Taux
|
+-- Tableau de repartition par methode
    +-- Colonnes : Methode (exacte / probabiliste) | Nb de correspondances | Justification
```

---

## Structure de la page Gouvernance

```
Gouvernance (/gouvernance)
|
+-- MockedBanner (si mock)
|
+-- Cartes KPI (consentement)
|   +-- Patients concernes | Accords | Taux d'accord
|
+-- Filtre par finalite (select : Toutes / api_access / research / analytics)
|
+-- Tableau des consentements
    +-- Colonnes : Patient maître | UUID | Nom | Finalite | Decision | Date
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

### Composants utilitaires
- `Collapsible`
- `Command`
- `ContextMenu`
- `DropdownMenu`
- `Toggle` / `ToggleGroup`
- `Skeleton`
- `AspectRatio`
- `InputOTP`
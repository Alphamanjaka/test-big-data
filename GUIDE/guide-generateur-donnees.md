# Guide Générateur de données — Patients synthétiques + Ground Truth

Générateur de données patients **synthétiques** réparties dans trois sources hétérogènes
(Pharmacie, Consultation, Imagerie), avec une **vérité de référence (Ground Truth)** pour évaluer
objectivement le moteur de déduplication.

## 1. Vue d'ensemble

| Élément | Valeur |
|---|---|
| Emplacement | `projet/code-source/evaluation/synthetic-patient-generator/` |
| Langage | Python 3.8+ |
| Dépendances | `faker`, `pandas`, `pytest` (`requirements.txt`) |
| Locale | `fr_FR` |
| Seed par défaut | `42` (reproductibilité) |
| Niveaux | `easy` (10 % var.), `medium` (30 %), `hard` (50 %) |
| Sources hétérogènes | `pharmacy`, `consultation`, `imaging` |

### Flux de génération

```
patient_generator (master patients) → distribution_engine → variation_engine (par niveau)
       → pharmacy/consultation/imaging generators → identity_mapping (ground truth)
       → experiment_builder (datasets easy/medium/hard complets)
```

### Règles de confidentialité

- **Données 100 % fictives** (Faker `fr_FR`, seed fixe).
- `identity_mapping.csv` et ses copies dans chaque `experiments/<niveau>/ground_truth/` sont
  **réservés à l'évaluation** : ne **jamais** les fournir à l'algorithme (interdiction stricte).

## 2. Installation

```bash
cd F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\evaluation\synthetic-patient-generator
python -m pip install -r requirements.txt
```

Toutes les commandes s'exécutent depuis ce répertoire (les modules utilisent des imports relatifs
`config.settings` / `generator.*`). Les tests (44) :

```bash
python -m pytest tests/ -v        # tous les tests
python -m pytest tests/test_setup.py -v      # installation OK
python -m pytest tests/test_end_to_end.py -v # bout-en-bout
```

## 3. Commandes disponibles

Tous les scripts acceptent `--patients` (défaut 10 000) et `--seed` (défaut 42) pour la
reproductibilité : **même seed = mêmes données**. Les générateurs de sources acceptent `--difficulty`
(`easy`/`medium`/`hard`).

### 3.1 Modules individuels (étape par étape)

| Commande | Fait quoi | Sortie |
|---|---|---|
| `python -m generator.patient_generator --patients 10000 --seed 42` | Patients maîtres (Ground Truth) | `data/ground_truth/master_patients.csv` |
| `python -m generator.distribution_engine --patients 10000 --seed 42` | Distribution dans les 3 sources | `data/ground_truth/distribution_plan.csv` |
| `python -m generator.pharmacy_generator --patients 10000 --difficulty medium --seed 42` | Source Pharmacie | `data/raw/pharmacy/{patients,achats}.csv` |
| `python -m generator.consultation_generator --patients 10000 --difficulty medium --seed 42` | Source Consultation | `data/raw/consultation/{patients,consultations}.csv` |
| `python -m generator.imaging_generator --patients 10000 --difficulty medium --seed 42` | Source Imagerie | `data/raw/imaging/{patients,examens}.csv` |
| `python -m generator.identity_mapping --patients 10000 --seed 42` | Vérité de référence | `data/ground_truth/identity_mapping.csv` |
| `python -m generator.experiment_builder --patients 10000 --seed 42` | **3 datasets complets** easy/medium/hard | `data/experiments/{easy,medium,hard}/` |

### 3.2 Chemin « officiel » : les 3 datasets via l'évaluateur

Le point d'entrée recommandé pour la démonstration est l'**évaluateur** (il régénère automatiquement
le dataset du niveau s'il manque) :

```bash
cd F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source
.venv\Scripts\python evaluation\evaluate_engine.py --level hard --patients 500 --seed 42
# options : --level easy|medium|hard (défaut medium) ; --only mvp|spark (défaut les deux)
```

`evaluate_engine.py` génère ~500 patients maîtres (défaut) et produit : Precision / Recall / F1
**par paires**, breakdown par méthode (`exact`/`probabilistic`/`new_master`), contribution par
source, et vérifie la **parité MVP (Pandas) vs Spark**. Le rapport est écrit dans
`evaluation/evaluation_truth.md` et affiché en sortie.

## 4. Paramètres centraux

`config/settings.py` :

| Paramètre | Valeur par défaut | Rôle |
|---|---|---|
| `DEFAULT_NUM_PATIENTS` | 10 000 | taille par défaut des datasets bruts |
| `FAKER_LOCALE` | `fr_FR` | noms, adresses, … |
| `CIN_COVERAGE` | 0.75 | ~75 % des maîtres ont un CIN (format malgache `101 02404 2`) |
| `DIFFICULTY_LEVELS` | easy 0.10 / medium 0.30 / hard 0.50 | taux de variation |
| `DIFFICULTY_VARIATION_TYPES` | par niveau | types de variations actifs |
| `SOURCE_PRESENCE_PROBABILITY` | ph 0.8 / cons 0.7 / img 0.6 | probabilité de présence par source |
| `SOURCE_ID_PREFIXES` | PH / MED / IMG | identifiants locaux |

Niveaux de variation :

| Niveau | Types actifs |
|---|---|
| easy | `case`, `spacing`, `date_format`, `cin_format` |
| medium | easy + `name_inversion`, `typo_light` |
| hard | medium + `typo`, `abbreviation`, `missing_value` |

## 5. Résultats de référence (reproductibles, seed 42)

Évaluation du moteur `engine/` sur ~500 maîtres / ~1 057 enregistrements (P/R/F1 par paires) :

| Niveau | Precision | Recall | F1 | Lecture |
|---|---|---|---|---|
| easy (10 %) | 1.000 | 1.000 | 1.000 | parfait |
| medium (30 %) | 1.000 | 0.884 | 0.939 | quasi-parfait |
| hard (50 %) | 1.000 | 0.422 | 0.594 | difficile (TFNE assumés) |

**Point-clé** : Precision = **1.000 sur les trois niveaux** (zéro faux positif → jamais de fusion à
tort, propriété essentielle en santé). La **parité Pandas = Spark** est stricte à chaque niveau.

## 6. Structure des données générées

```
synthetic-patient-generator/data/
├── ground_truth/
│   ├── master_patients.csv        # patients maîtres (ID GT + attributs stables)
│   ├── distribution_plan.csv      # dans quelle source chaque maître apparaît
│   └── identity_mapping.csv       # vérité de référence (RÉSERVÉ ÉVALUATION)
├── raw/                           # sorties des générateurs unitaires
│   ├── pharmacy/        {patients,achats}.csv
│   ├── consultation/    {patients,consultations}.csv
│   └── imaging/         {patients,examens}.csv
└── experiments/
    ├── easy/    → pharmacy/ + consultation/ + imaging/ + ground_truth/
    ├── medium/  → idem
    └── hard/    → idem   (utilisé par evaluate_engine)
```

## 7. Personnalisation

- **Changer la proportion de CIN** : ajuster `CIN_COVERAGE` (cohérence avec les masters → sources).
- **Ajouter un type de variation** : déclarer le type dans `DIFFICULTY_VARIATION_TYPES` et son
  implémentation dans `variation_engine`.
- **Changer le seed nominal** : `RANDOM_SEED` (toute la chaîne reste reproductible).

## 8. Dépannage rapide

| Symptôme | Cause probable | Correctif |
|---|---|---|
| `ModuleNotFoundError: config` | exécution hors répertoire du générateur | lancer depuis `synthetic-patient-generator/` |
| Dataset absent → erreur d'évaluation | `data/experiments/<niveau>` effacé | re-run `evaluate_engine.py --level X` (auto-génère) |
| Résultats non reproductibles | seed différent | tout lancer avec le même `--seed` |
| CIN absent sur certains patients | `CIN_COVERAGE=0.75` (volontaire) | cohérent : sans CIN, absent de toutes les sources |

## 9. Suite logique

- Évaluer la dédup : moteur `engine/` (Pandas + Spark) — voir aussi `GUIDE/guide-backend.md`,
  `documents/documentation/evaluation.md` et `evaluation/EVALUATION_GUIDE.md`.
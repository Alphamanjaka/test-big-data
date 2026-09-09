# Synthetic Patient Data Generator & Ground Truth

Générateur de données patients synthétiques réparties dans plusieurs
sources hétérogènes (Pharmacie, Consultation, Imagerie), avec une
vérité de référence (Ground Truth) permettant d'évaluer objectivement
un algorithme de déduplication / Entity Resolution.

## Structure du projet

```
synthetic-patient-generator/
├── generator/
│   ├── patient_generator.py       # Étape 2 — Patients maîtres / Ground Truth
│   ├── distribution_engine.py     # Étape 3 — Distribution dans les sources
│   ├── variation_engine.py        # Étape 4 — Injection d'erreurs/variations
│   ├── pharmacy_generator.py      # Étape 5 — Source Pharmacie
│   ├── consultation_generator.py  # Étape 5 — Source Consultation
│   ├── imaging_generator.py       # Étape 5 — Source Imagerie
│   ├── identity_mapping.py        # Étape 6 — Fichier de vérité (évaluation)
│   ├── experiment_builder.py      # Étape 7 — Datasets easy/medium/hard
│   └── common.py                  # Utilitaires partagés
├── config/
│   └── settings.py                # Paramètres centraux (chemins, seuils, sources)
├── data/
│   ├── ground_truth/              # master_patients.csv, distribution_plan.csv, identity_mapping.csv
│   ├── raw/                       # Sorties par source (pharmacy/consultation/imaging)
│   └── experiments/               # Datasets complets easy/medium/hard
├── tests/                         # Étape 8 — Tests unitaires + bout-en-bout
└── requirements.txt
```

> Guide complet d'utilisation : `GUIDE/guide-generateur-donnees.md`.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
```

## Commandes disponibles

Tous les scripts acceptent `--seed` pour la reproductibilité (même seed =
mêmes données). `--difficulty` / `--variation` accepte : `easy`, `medium`, `hard`.

### Modules individuels (étape par étape)

| Commande | Fait quoi |
|---|---|
| `python -m generator.patient_generator --patients 10000 --seed 42` | Génère les patients maîtres (Ground Truth) → `data/ground_truth/master_patients.csv` |
| `python -m generator.distribution_engine --patients 10000 --seed 42` | Génère les patients + les distribue dans les 3 sources → `data/ground_truth/distribution_plan.csv` |
| `python -m generator.pharmacy_generator --patients 10000 --difficulty medium --seed 42` | Génère la source Pharmacie → `data/raw/pharmacy/{patients,achats}.csv` |
| `python -m generator.consultation_generator --patients 10000 --difficulty medium --seed 42` | Génère la source Consultation → `data/raw/consultation/{patients,consultations}.csv` |
| `python -m generator.imaging_generator --patients 10000 --difficulty medium --seed 42` | Génère la source Imagerie → `data/raw/imaging/{patients,examens}.csv` |
| `python -m generator.identity_mapping --patients 10000 --seed 42` | Génère le fichier de vérité → `data/ground_truth/identity_mapping.csv` |
| `python -m generator.experiment_builder --patients 10000 --seed 42` | Génère **les 3 datasets complets** (easy/medium/hard) → `data/experiments/{easy,medium,hard}/` |

### Chemin officiel : datasets easy/medium/hard via l'évaluateur

L'**évaluateur** (recommandé) génère automatiquement le dataset du niveau s'il est absent, puis calcule
les métriques vs le Ground Truth. Il sert de point d'entrée « tout-en-un » :

```bash
# Depuis projet/code-source (venv actif)
python evaluation/evaluate_engine.py --level hard --patients 500 --seed 42
```

> Détails (modules, paramètres, sorties) : `GUIDE/guide-generateur-donnees.md`.

### Tests

```bash
pytest tests/ -v                    # tous les tests du générateur (44)
pytest tests/test_setup.py -v       # juste vérifier l'installation
pytest tests/test_end_to_end.py -v  # juste le test bout-en-bout global
```

## Avertissement

`data/ground_truth/identity_mapping.csv` (et son équivalent dans chaque
`data/experiments/<niveau>/ground_truth/`) ne doit **jamais** être fourni à
un algorithme de déduplication : il est réservé à l'évaluation de ses
performances (précision / rappel du matching).

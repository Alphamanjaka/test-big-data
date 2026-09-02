# Synthetic Patient Data Generator & Ground Truth

Générateur de données patients synthétiques réparties dans plusieurs
sources hétérogènes (Pharmacie, Consultation, Imagerie), avec une
vérité de référence (Ground Truth) permettant d'évaluer objectivement
un algorithme de déduplication / Entity Resolution.

## Structure du projet

```
synthetic-patient-generator/
├── main.py                        # Point d'entrée unique (pipeline complet)
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
├── pytest.ini
└── requirements.txt
```

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
| `python -m generator.pharmacy_generator --patients 10000 --difficulty medium --seed 42` | Génère la source Pharmacie → `data/raw/pharmacy/{patients,purchases}.csv` |
| `python -m generator.consultation_generator --patients 10000 --difficulty medium --seed 42` | Génère la source Consultation → `data/raw/consultation/{patients,consultations}.csv` |
| `python -m generator.imaging_generator --patients 10000 --difficulty medium --seed 42` | Génère la source Imagerie → `data/raw/imaging/{patients,exams}.csv` |
| `python -m generator.identity_mapping --patients 10000 --seed 42` | Génère le fichier de vérité → `data/ground_truth/identity_mapping.csv` |
| `python -m generator.experiment_builder --patients 10000 --seed 42` | Génère **les 3 datasets complets** (easy/medium/hard) → `data/experiments/{easy,medium,hard}/` |

### Commande unique (pipeline complet en un coup)

```bash
python main.py --patients 10000 --sources 3 --variation medium --output data/experiments/medium
```

Fait tout d'un coup (patients → distribution → 3 sources → identity mapping)
vers le dossier `--output` de ton choix, avec un résumé affiché à la fin.

### Tests

```bash
pytest tests/ -v                    # tous les tests + couverture (pytest.ini)
pytest tests/test_setup.py -v       # juste vérifier l'installation
pytest tests/test_end_to_end.py -v  # juste le test bout-en-bout global
```

## Avertissement

`data/ground_truth/identity_mapping.csv` (et son équivalent dans chaque
`data/experiments/<niveau>/ground_truth/`) ne doit **jamais** être fourni à
un algorithme de déduplication : il est réservé à l'évaluation de ses
performances (précision / rappel du matching).

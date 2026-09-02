# Synthetic Patient Data Generator & Ground Truth

Générateur de données patients synthétiques réparties dans plusieurs
sources hétérogènes (Pharmacie, Consultation, Imagerie), avec une
vérité de référence (Ground Truth) permettant d'évaluer objectivement
un algorithme de déduplication / Entity Resolution.

## Structure du projet

```
synthetic-patient-generator/
├── generator/              # Code du générateur (patient_generator, distribution_engine, ...)
├── config/
│   └── settings.py         # Paramètres centraux (chemins, seuils, sources)
├── data/
│   ├── ground_truth/       # master_patients.csv, identity_mapping.csv
│   ├── raw/                # Sorties par source (pharmacy/consultation/imaging)
│   └── experiments/        # Datasets easy/medium/hard
├── tests/
└── requirements.txt
```

## Installation (Étape 1 — Initialisation)

```bash
python -m venv .venv
source .venv/bin/activate   # ou .venv\Scripts\activate sous Windows
pip install -r requirements.txt
pytest tests/test_setup.py -v
```

## Prochaine étape

Étape 2 — `generator/patient_generator.py` : génération des patients
maîtres (`master_id`, identité via Faker) et construction du Ground
Truth (`data/ground_truth/master_patients.csv`).

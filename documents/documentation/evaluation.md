# Évaluation de la déduplication (ground truth)

L'évaluation compare la déduplication (version Pandas **et** version Spark) au regroupement de
**référence** (`identity_mapping.csv`) et produit **précision / rappel / F1**. Elle sert à
*démontrer* que la logique est correcte et à *diagnostiquer* où l'algorithme se trompe.

## 1. Principe

- On génère 3 jeux de données **synthétiques** (niveaux easy / medium / hard) : mêmes master patients,
  mêmes sources, seul le **taux de variation** change (hard = 50 % de variations volontaires).
- `--seed 42` rend la génération **reproductible**.
- Pour chaque niveau, un **ground truth** encode quels enregistrements sont en réalité le même patient.
- L'algorithme **ne reçoit jamais** le ground truth (règle d'explicabilité).

## 2. Métriques (niveau paire)

| Métrique | Définition | Interprétation |
|---|---|---|
| TP | Paires de patients correctement regroupées | — |
| FP | Paires fusionnées à tort | FP > 0 → l'algo fusionne des patients différents |
| FN | Paires non fusionnées qui devraient l'être | FN > 0 → l'algo rate des vrais doublons |
| Precision (Pair Quality) | TP / (TP + FP) | Exactitude des fusions |
| Recall (Pair Completeness) | TP / (TP + FN) | Complétude des fusions |
| **F1** | 2·P·R / (P+R) | Compromis global |

- **F1 = 1.000** : chaque groupe prédit = groupe vérité (perfect).
- Pour `hard`, une baisse de F1 est **attendue** : c'est là que l'outil diagnostique les erreurs.

## 3. Résultats de référence (moteur porté `engine/`)

Run 2026-09-08 — `evaluate_engine.py --level {easy|medium|hard}` (500 masters par niveau,
~1 000 enregistrements, seed 42), parité **MVP (Pandas) = Spark** vérifiée à chaque niveau :

| Niveau | Masters prédits | TP | FP | FN | Precision | Recall | F1 |
|---|---|---|---|---|---|---|---|
| easy | 500 | 727 | 0 | 0 | 1.000 | 1.000 | 1.000 |
| medium | 554 | 643 | 0 | 84 | 1.000 | 0.884 | 0.939 |
| hard | 804 | 307 | 0 | 420 | 1.000 | 0.422 | 0.594 |

Breakdown `hard` par méthode de match (identique MVP/Spark) :

| Méthode | Precision / Recall / F1 |
|---|---|
| exact | 1.000 / 0.854 / 0.921 |
| probabilistic | 1.000 / 0.533 / 0.696 |

Contribution par source (rappel, hard) : pharmacy 0.422 · consultation 0.422 · imaging 0.423.

Rapport complet : `evaluation/evaluation_truth.md` (regénéré à chaque run).

**Lecture :** l'algorithme **ne fusionne jamais à tort** (Precision 1.000, zéro FP) — propriété
essentielle pour la donnée de santé ; sur le dataset volontairement dur (50 % de variations), il ne
reconnaît pas toutes les variantes (Recall 0.422). L'introduction de la **clé CIN** (couverture ~75 %)
a relevé le rappel hard de 0.287 (07/09) à 0.422 sans faux positif. Les seuils/pondérations sont
ajustables pour trader précision ↔ rappel selon le besoin métier.

### Référence historique (test_bigdata, 10 669 patients)

Run 2026-09-04 — 10 669 patients sources, 5 000 masters, multithreads MVP + Spark :

| Métrique | MVP (Pandas) | Spark |
|---|---|---|
| Masters prédits | 9 023 | 9 023 |
| Vrais positifs (paires) | 1 868 | 1 868 |
| Faux positifs (fusion à tort) | **0** | **0** |
| Faux négatifs (non-fusion) | 5 523 | 5 523 |
| Precision | **1.000** | **1.000** |
| Recall | 0.253 | 0.253 |
| **F1** | **0.403** | **0.403** |

Breakdown par méthode de match (identique MVP/Spark) : exact 1.000/0.746/0.855 ·
probabilistic 1.000/0.741/0.851. Contribution source : pharmacy 0.255 · consultation 0.251 ·
imaging 0.252.

## 4. Exécution

```powershell
# 1. (si besoin) générer les datasets
cd evaluation/synthetic-patient-generator
..\.venv\Scripts\python -m generator.experiment_builder --patients 5000 --seed 42
cd ..

# 2. pointer config/sources.json → data_root (easy | medium | hard)

# 3. lancer l'évaluation du moteur
..\.venv\Scripts\python evaluation\evaluate_engine.py --level hard
# arguments : --level easy|medium|hard (défaut medium) · --only mvp|spark · --patients/--seed

# 4. lire le rapport dans evaluation/evaluation_truth.md
```

(Ancienne torche de référence : `evaluation/evaluation_truth.py` + `EVALUATION_GUIDE.md` consommés par
l'évaluateur porté `evaluation/evaluate_engine.py` qui teste le moteur `engine/`.)

## 5. Fixtures et fichiers

| Fichier | Rôle |
|---|---|
| `evaluation/synthetic-patient-generator/` | Générateur de données + ground truth (easy/medium/hard) |
| `evaluation/evaluation_truth.py` | Calcul P/R/F1 + breakdown par méthode et source |
| `evaluation/evaluate_engine.py` | Évaluateur adapté au moteur `engine/` (`--level`, `--only`) |
| `evaluation/EVALUATION_GUIDE.md` | Guide pas à pas |

## 6. Règles

- **Données fictives uniquement**, seed reproductible.
- Le ground truth est **réservé à l'évaluation** et ne doit jamais être fourni à l'algo.
- Ne pas fusionner sans logique explicable.
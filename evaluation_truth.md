# Évaluation Ground Truth — Niveau `medium`

- Date : 2026-09-02 15:31
- Ground Truth : F:\GITHUB\test big data\synthetic-patient-generator\data\experiments\medium\ground_truth\identity_mapping.csv
- Data root : synthetic-patient-generator\data\experiments\medium
- Patients source : 1057

## Comparaison MVP (N1) vs Spark (N2)

| Métrique | MVP (Pandas) | Spark |
|---|---|---|
| Masters prédits | 500 | 500 |
| Groupes vérité | 500 | 500 |
| Vrais positifs (paires) | 727 | 727 |
| Faux positifs (fusion à tort) | 0 | 0 |
| Faux négatifs (non-fusion) | 0 | 0 |
| Precision (Pair Quality) | 1.000 | 1.000 |
| Recall (Pair Completeness) | 1.000 | 1.000 |
| F1 | 1.000 | 1.000 |

## Précision / Rappel par type de match

| Méthode | MVP (P/R/F1) | Spark (P/R/F1) |
|---|---|---|
| exact | 1.000/1.000/1.000 | 1.000/1.000/1.000 |

## Contribution par source (rappel)

> Rappel = fraction des paires de référence impliquant la source,
> correctement regroupées par l'algo.

| Source | MVP (R) | Spark (R) |
|---|---|---|
| pharmacy | 1.000 | 1.000 |
| consultation | 1.000 | 1.000 |
| imaging | 1.000 | 1.000 |

## Résumé

- MVP  : TP=727 FP=0 FN=0 | Precision=1.000 Recall=1.000 F1=1.000
- Spark: TP=727 FP=0 FN=0 | Precision=1.000 Recall=1.000 F1=1.000

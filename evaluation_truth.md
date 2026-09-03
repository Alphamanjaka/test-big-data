# Évaluation Ground Truth — Niveau `hard`

- Date : 2026-09-03 10:21
- Ground Truth : F:\GITHUB\test big data\synthetic-patient-generator\data\experiments\hard\ground_truth\identity_mapping.csv
- Data root : synthetic-patient-generator\data\experiments\hard
- Mode : MVP
- Patients source : 10669

## Comparaison MVP (N1) vs Spark (N2)

| Métrique | MVP (Pandas) | Spark |
|---|---|---|
| Masters prédits | 9023 | — |
| Groupes vérité | 5000 | — |
| Vrais positifs (paires) | 1868 | — |
| Faux positifs (fusion à tort) | 0 | — |
| Faux négatifs (non-fusion) | 5523 | — |
| Precision (Pair Quality) | 1.000 | — |
| Recall (Pair Completeness) | 0.253 | — |
| F1 | 0.403 | — |

## Précision / Rappel par type de match

| Méthode | MVP (P/R/F1) | Spark (P/R/F1) |
|---|---|---|
| exact | 1.000/0.746/0.855 | — |
| probabilistic | 1.000/0.741/0.851 | — |

## Contribution par source (rappel)

> Rappel = fraction des paires de référence impliquant la source,
> correctement regroupées par l'algo.

| Source | MVP (R) | Spark (R) |
|---|---|---|
| pharmacy | 0.255 | — |
| consultation | 0.251 | — |
| imaging | 0.252 | — |

## Résumé

- MVP  : TP=1868 FP=0 FN=5523 | Precision=1.000 Recall=0.253 F1=0.403
- Spark: —

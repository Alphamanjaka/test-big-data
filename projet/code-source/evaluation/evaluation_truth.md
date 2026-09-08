# Évaluation Ground Truth — Niveau `hard`

- Date : 2026-09-07 23:31
- Ground Truth : F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\evaluation\synthetic-patient-generator\data\experiments\hard\ground_truth\identity_mapping.csv
- Data root : F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\evaluation\synthetic-patient-generator\data\experiments\hard
- Mode : MVP + Spark
- Enregistrements : 1057

## Comparaison MVP (Pandas) vs Spark

| Métrique | MVP (Pandas) | Spark |
|---|---|---|
| Masters prédits | 869 | 869 |
| Groupes vérité | 500 | 500 |
| Vrais positifs (paires) | 209 | 209 |
| Faux positifs (fusion à tort) | 0 | 0 |
| Faux négatifs (non-fusion) | 518 | 518 |
| Precision (Pair Quality) | 1.000 | 1.000 |
| Recall (Pair Completeness) | 0.287 | 0.287 |
| F1 | 0.447 | 0.447 |

## Precision / Rappel / F1 par type de match

| Méthode | MVP | Spark |
|---|---|---|
| exact | 1.000/0.737/0.848 | 1.000/0.737/0.848 |
| probabilistic | 1.000/0.667/0.800 | 1.000/0.667/0.800 |

## Contribution par source (rappel)

> Rappel = fraction des paires de reference impliquant la source, correctement regroupees.

| Source | MVP | Spark |
|---|---|---|
| pharmacy | 0.299 | 0.299 |
| consultation | 0.286 | 0.286 |
| imaging | 0.276 | 0.276 |

- MVP  : TP=209 FP=0 FN=518 | Precision=1.000 Recall=0.287 F1=0.447
- Spark: TP=209 FP=0 FN=518 | Precision=1.000 Recall=0.287 F1=0.447
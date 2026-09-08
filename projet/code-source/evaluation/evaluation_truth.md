# Évaluation Ground Truth — Niveau `hard`

- Date : 2026-09-08 10:03
- Ground Truth : F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\evaluation\synthetic-patient-generator\data\experiments\hard\ground_truth\identity_mapping.csv
- Data root : F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\evaluation\synthetic-patient-generator\data\experiments\hard
- Mode : MVP + Spark
- Enregistrements : 1057

## Comparaison MVP (Pandas) vs Spark

| Métrique | MVP (Pandas) | Spark |
|---|---|---|
| Masters prédits | 804 | 804 |
| Groupes vérité | 500 | 500 |
| Vrais positifs (paires) | 307 | 307 |
| Faux positifs (fusion à tort) | 0 | 0 |
| Faux négatifs (non-fusion) | 420 | 420 |
| Precision (Pair Quality) | 1.000 | 1.000 |
| Recall (Pair Completeness) | 0.422 | 0.422 |
| F1 | 0.594 | 0.594 |

## Precision / Rappel / F1 par type de match

| Méthode | MVP | Spark |
|---|---|---|
| exact | 1.000/0.854/0.921 | 1.000/0.854/0.921 |
| probabilistic | 1.000/0.533/0.696 | 1.000/0.533/0.696 |

## Contribution par source (rappel)

> Rappel = fraction des paires de reference impliquant la source, correctement regroupees.

| Source | MVP | Spark |
|---|---|---|
| pharmacy | 0.422 | 0.422 |
| consultation | 0.422 | 0.422 |
| imaging | 0.423 | 0.423 |

- MVP  : TP=307 FP=0 FN=420 | Precision=1.000 Recall=0.422 F1=0.594
- Spark: TP=307 FP=0 FN=420 | Precision=1.000 Recall=0.422 F1=0.594
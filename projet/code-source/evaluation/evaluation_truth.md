# Évaluation par vérité terrain — jeu `hard`

- Date : 2026-09-30 12:08
- Vérité terrain : F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\evaluation\synthetic-patient-generator\data\experiments\hard\ground_truth\identity_mapping.csv
- Moteur : règle d'identité stricte (CIN, genre, date et ville de naissance identiques ; sans CIN, nom identique en plus)
- Fiches : 1057

| Métrique | Valeur |
|---|---|
| Patients maîtres prédits | 942 |
| Groupes de la vérité | 500 |
| Vrais positifs (paires) | 130 |
| Faux positifs (fusions à tort) | 0 |
| Faux négatifs (fusions manquées) | 597 |
| Précision | 1.000 |
| Rappel | 0.179 |
| F1 | 0.303 |

## Rappel par source

> Rappel = fraction des paires de référence impliquant la source, correctement regroupées.

| Source | Rappel |
|---|---|
| pharmacy | 0.181 |
| consultation | 0.175 |
| imaging | 0.180 |

Décisions : exact=115, new_master=942

VP=130 FP=0 FN=597 | Précision=1.000 Rappel=0.179 F1=0.303
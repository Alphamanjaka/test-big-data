# Évaluation Ground Truth — Guide pas à pas

Compare la déduplication (MVP N1 et/ou Spark N2) au regroupement de référence
(`identity_mapping.csv`) et produit précision / rappel / F1.

---

## 0. Prérequis (un seul shell)

```powershell
$env:JAVA_HOME='C:\Program Files\Java\jdk-25.0.2'   # obligatoire pour Spark
$env:PYTHONIOENCODING='utf-8'                        # pour les accents en console

# Vérifier le venv
& "F:\GITHUB\test_bigdata\.venv\Scripts\python.exe" --version
```

Ouvrir le projet :
```powershell
cd "F:\GITHUB\test_bigdata"
```

---

## 1. (Si besoin) Générer un dataset

Génère les 3 niveaux (easy / medium / hard) pour `--patients N` master patients
mêmes patients, mêmes sources, seul le taux de variation change.

```powershell
cd synthetic-patient-generator
& "F:\GITHUB\test_bigdata\.venv\Scripts\python.exe" -m generator.experiment_builder --patients 5000 --seed 42
cd ..
```

`--seed 42` rend la génération **reproductible** : même nombre de patients →
exactement les mêmes données à chaque exécution (idem Ground Truth).

---

## 2. Pointer la config sur le niveau à évaluer

Modifier `config/sources.json` → clé `data_root` :

```json
{
  "data_root": "synthetic-patient-generator/data/experiments/hard",
  ...
}
```

| Niveau visé | `data_root` |
|---|---|
| easy | `synthetic-patient-generator/data/experiments/easy` |
| medium | `synthetic-patient-generator/data/experiments/medium` |
| hard | `synthetic-patient-generator/data/experiments/hard` |

> ⚠️ Le niveau choisi (`--level`) doit correspondre au `data_root` de la config.
> L'évaluateur lit le ground_truth du `--level` **et** lance le pipeline sur le `data_root` courant.

---

## 3. Lancer l'évaluation

```powershell
& "F:\GITHUB\test_bigdata\.venv\Scripts\python.exe" evaluation_truth.py --level hard
```

Arguments :
- `--level easy|medium|hard` (défaut `medium`) — niveau à évaluer.
- `--only mvp|spark` — évaluer une seule implémentation (défaut : les deux).
- `--patients N` / `--seed S` — génèrent le dataset si la vérité est absente.

Le script écrit le rapport dans `evaluation_truth.md` (racine) et l'affiche.

---

## 4. Lire le rapport

`evaluation_truth.md` contient :

| Métrique | MVP (Pandas) | Spark |
|---|---|---|
| Vrais positifs (paires) TP | … | … |
| Faux positifs (fusion à tort) FP | … | … |
| Faux négatifs (non-fusion) FN | … | … |
| Precision (Pair Quality) | … | … |
| Recall (Pair Completeness) | … | … |
| **F1** | … | … |

Plus : breakdown par type de match (exact / probabilistic) et contribution par
source (recall).

### Interprétation
- **F1 = 1.000** → déduplication parfaite : chaque groupe prédit = groupe vérité.
- **FP > 0** → l'algo fusionne des patients qui sont en réalité différents.
- **FN > 0** → l'algo ne fusionne pas des patients qui sont en réalité les mêmes.
- Pour `hard` (50 % de variations), une baisse de F1 est attendue : c'est là que
  l'outil sert à diagnostiquer où l'algo se trompe.

---

## 5. (Option) Revenir au démo MVP

```powershell
# Remettre data_root = "data/raw" dans config/sources.json
python load_to_postgres.py
python run_pipeline.py
```

---

## Règles du projet rappelées
- Données **fictives** uniquement.
- Le `ground_truth` est **réservé à l'évaluation** : il ne doit jamais être fourni
  à l'algo de déduplication (règle traçabilité / explicabilité).
- Ne pas fusionner sans logique explicable.

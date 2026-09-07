# Consignes déduplication (moteur `engine/`)

Source : fusion des consignes d'entité-résolution de `test_bigdata` (MVP + Spark) appliquées au moteur porté.

## 1. Domaine

Travail sur `projet/code-source/engine/` : modèle canonique, nettoyage/standardisation, matching exact
puis probabiliste, master patient, identity map, parité Pandas/Spark.

## 2. Canonique & standardisation

- `engine/identity/canonical.py` : `CanonicalPatient`, `map_patient()`, `from_dict()`, `matching_key`.
- Respecter les helpers `_text`/`_normalized`/`_phone`/`_gender`/`_birth_date` (casse, accents,
  téléphones `+261…`→`0…`, dates multi-formats, genre `H/male/Homme/M`→`M`, `F/female/femme`→`F`).
- Tout champ ajouté au canonique doit être documenté et couvert par un test.

## 3. Matching

- **Clé** : `(nom normalisé, birth_date, phone)`.
- **Score pondéré** : nom 0.5 · date de naissance 0.3 · téléphone 0.2.
- **Seuil** : 0.80 (`MatchDecision`). Ne jamais fusionner en dessous du seuil (pas de logique arbitraire).
- **Exact** d'abord (téléphone/clé identiques), **probabiliste** ensuite avec **blocking** (`_MasterIndex`,
  candidats sur préfixe nom/date/tél) pour éviter l'O(n²).
- Sorties : `master_patient_id`, `match_method` (exact|probabilistic), `match_score` — toujours explicités.

## 4. Parité Pandas / Spark (règle forte)

- `engine/identity/matcher.py` (Pandas) et `engine/identity/spark_dedup.py` (driver-side) doivent produire
  des résultats **strictement identiques** sur les mêmes données.
- Toute évolution de la logique s'accompagne d'un test de parité (`tests/test_matcher.py`).
- Le Spark dédup travaille sur des **dicts** (`canonical_rows`, gère les dates `datetime.date`), pas sur
  des DataFrames cross-join : résolution séquentielle sur driver.

## 5. Cas de référence

- **Jean Rakoto** : pharmacy `Jean Rakoto/0341234567/1990-01-10` + consultation
  `Rakoto Jean/+261341234567/10/01/1990` + imaging `J. RAKOTO/034 123 4567/1990/01/10` → **1 master**.
- **Nirina** : score probabiliste 0.8 (variations) → fusion autorisée.
- Démo : 18 patients → 11 masters, 18 liens identity — identique MVP et Spark.

## 6. Règles métier

- Ne **jamais** fusionner sans logique explicable.
- Garder la chaîne `source → canonique → master patient` + identity map.
- Ne **jamais** fournir le ground_truth à l'algorithme (réservé à l'évaluation).
- Compatibilité Python 3.8 : `from __future__ import annotations` ; pas de dépendance > RapidFuzz/pandas.

## 7. Validation

```powershell
.venv\Scripts\python -m pytest tests/test_matcher.py -q      # 6 cas
.venv\Scripts\python evaluation\evaluate_engine.py --level hard
```

Référence concept : `documents/documentation/deduplication.md` · évaluation : `documents/documentation/evaluation.md`.
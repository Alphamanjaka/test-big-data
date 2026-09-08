# Module 1 : Finalisation du Pipeline RAW vers SILVER

## Objectif

Transformer les données brutes de la zone **RAW** en données propres et structurées dans la zone **SILVER**. À la fin de ce module, la table `datalake_silver.patient_fhir` doit contenir des données fiables, avec des valeurs normalisées et des doublons clairement identifiés.

**Fichier principal concerné :** `v1create_silver.py`

---

## Portée du MVP (Priorité Absolue)

L'objectif est d'avoir une première version fonctionnelle et fiable du pipeline.

### MVP - Étape 1 : Normalisation des Valeurs (Simple)

- **Problème :** Actuellement, le script normalise surtout les _types_ de données. Des valeurs comme le sexe (`gender`) peuvent exister sous différentes formes (`"M"`, `"H"`, `"male"`, `"homme"`).
- **Action à réaliser :**
  1.  Créer un dictionnaire de mapping simple pour les valeurs à normaliser.
      ```python
      # Exemple pour le genre
      GENDER_MAP = {
          "m": "male", "h": "male", "homme": "male",
          "f": "female", "femme": "female"
      }
      ```
  2.  Modifier le script `v1create_silver.py` pour appliquer cette normalisation. Utiliser une fonction `when/otherwise` ou une UDF (User Defined Function) Spark pour remplacer les anciennes valeurs par les nouvelles.

### MVP - Étape 2 : Identifier les Doublons de Patients (sans les fusionner)

- **Problème :** Le même patient peut exister plusieurs fois. Le MVP ne requiert pas la fusion, mais l'identification est cruciale.
- **Règle de détection :** Un patient est considéré comme un doublon s'il partage le même `(nom, date de naissance, genre)`.
- **Action à réaliser :**
  1.  Dans `v1create_silver.py`, après avoir uni les données de toutes les sources dans `df_entite`, utiliser une fonction de fenêtrage (`Window`) de Spark.
  2.  Partitionner les données par `(name, birth_date, gender)`.
  3.  Compter le nombre de lignes dans chaque partition.
  4.  Ajouter une nouvelle colonne booléenne, `is_duplicate`, qui sera `true` si le compte pour cette partition est supérieur à 1.

### MVP - Étape 3 : Assurer l'Idempotence et la Traçabilité

- **Problème :** Le pipeline doit pouvoir être relancé sans créer d'incohérences.
- **Action à réaliser :**
  1.  **Écrasement :** Confirmer que l'écriture dans la table Silver se fait bien en mode `overwrite`. Cela garantit que chaque exécution repart d'un état propre.
      ```python
      df_final.write.mode("overwrite").saveAsTable(table_cible)
      ```
  2.  **Traçabilité :** Vérifier que la colonne `_source_table` est bien présente dans la table finale. Elle est essentielle pour savoir d'où provient chaque enregistrement.

---

## Améliorations (Post-MVP / Tâches difficiles)

Ces tâches pourront être réalisées si le temps le permet ou dans une version future pour améliorer la robustesse du pipeline.

- **Déduplication Avancée (Fusion) :**
  - **Problème :** Les doublons sont identifiés mais pas fusionnés.
  - **Action :** Développer une stratégie de `merge` pour créer un "golden record" par patient, en choisissant les informations les plus complètes ou les plus récentes et en archivant les autres enregistrements.

- **Normalisation Étendue :**
  - **Problème :** Seuls quelques champs sont normalisés.
  - **Action :** Étendre la normalisation à d'autres champs (adresses, codes postaux, etc.) et mettre en place une gestion plus fine des valeurs manquantes (imputation).

## Validation

À la fin de ce module, une requête sur la table `datalake_silver.patient_fhir` doit permettre de voir les colonnes `gender` normalisées et la colonne `is_duplicate` correctement renseignée.

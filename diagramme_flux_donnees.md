# 🧬 Diagramme de Flux des Données - Plateforme Mon Memoire (Mermaid)

```mermaid
graph TD
    subgraph A[Sources Brutes & Entrée]
        A1(Base A) -->|Ingestion / Extraction| B;
        A2(Base B) -->|Ingestion / Extraction| B;
        A3(Base C) -->|Ingestion / Extraction| B;
    end

    subgraph B[Zone RAW / Bronze]
        B1("datalake/raw/{source}/{table}") -->|Données non modifiées - Immu| C;
    end

    subgraph C[Transformation SILVER / Argent Zone]
        C_Step1{Processus de Mapping FHIR & Normalisation}
        C_Step2{Moteur de Déduplication et MPI}
        B1 -->|Data + Métadonnées| C_Step1;
        C_Step1 --> C_Step2;
    end

    subgraph D[Zone GOLD / Or Zone]
        D_Processus{Enrichissement Analytique}
        C_Step2 -->|Data Silver| D_Input((Data Silver + Consent PostgreSQL));
        D_Input -->|Jointure & Agrégation Spark ETL| D_Processus;
        D_Processus -->|Joindre avec Statut de Consentement| E[datalake_gold.patient_events_gold];
    end

    subgraph G[Couche Gouvernance & Services API]
        direction LR
        G_Input(Requête Utilisateur/API Call) -->|1. Vérification Rôle RBAC| G1{Contrôleur d'Accès};
        G1 -->|2. Vérif Consentement Purpose-by-Purpose| G2{Vérificateur de Finalité};
        G2 -->|Validé & MasterID trouvé| G3{3. Lecture et Filtrage sur GOLD};
        G3 --> H[Service API / FastAPI Endpoints];
    end

    subgraph EVAL[Évaluation Ground Truth - latéral]
        direction LR
        GEN(Générateur de données synthétiques)
        GT[(Ground Truth identity_mapping.csv)]
        CMP{Comparateur P/R/F1}
        REP[evaluation_truth.md]
        GEN -->|jeux easy/medium/hard| A1;
        GEN -->|jeux easy/medium/hard| A2;
        GEN -->|jeux easy/medium/hard| A3;
        GEN --> GT;
        C_Step2 -->|décisions master_patient_id| CMP;
        GT -->|référence - jamais fournie au moteur| CMP;
        CMP --> REP;
    end

    %% FLUX PRINCIPAL
    E -->|Requête de Données Analytiques| G_Input;

    %% Notes d'Explicabilité et Sécurité
    style C_Step2 fill:#ccf,stroke:#333,stroke-width:2px
    style D_Processus fill:#cff,stroke:#333,stroke-width:2px
    style G1 fill:#fcc,stroke:#333,stroke-width:2px
    style G2 fill:#fcc,stroke:#333,stroke-width:2px
    style E fill:#ddc,stroke:#333,stroke-width:2px
    style CMP fill:#cfc,stroke:#333,stroke-width:2px

    %% Légende des Flux Critiques
    linkStyle 5 stroke:red,stroke-width:2px,color:red;
    linkStyle 9 stroke:blue,stroke-width:2px,color:blue;
    linkStyle 18 stroke:orange,stroke-width:2px,color:orange;

    subgraph Legend [Légende]
        LEG1(Flux de Données) -->|Circulation| LEG1b(( ));
        LEG2[Mécanisme de Contrôle] -->|Filtrage Obligatoire| LEG2b(( ));
        LEG3[Évaluation Ground Truth] -->|Comparaison| LEG3b(( ));
    end
```

# Explication Détaillée du Flux

Ce schéma modélise l'architecture Big Data Medallion (Bronze $\rightarrow$ Silver $\rightarrow$ Gold) avec les couches de gouvernance et l'évaluation ground-truth intégrées.

1.  **Sources (Entrée) :** trois sources hétérogènes génériques (`Base A`, `Base B`, `Base C`) de données
    fictives (modélisées dans le périmètre mémoire). La plateforme est **agnostique** : le nombre, le type
    (PostgreSQL, SQLite, …) et les noms des sources sont configurables via `provision/config/data_sources.json`.
2.  **RAW (Bronze Zone):** Les données sont chargées **brutes et inchangées** (`datalake/raw/...`). C'est la source de vérité non modifiée, essentielle pour l'audit.
3.  **SILVER (Argent Zone) - Le Maître Patient Index (MPI):**
    - Le moteur combine les données brutes avec un mapping FHIR.
    - La transformation clé est le **Moteur de Déduplication**, qui utilise des techniques d'Exact et de Probabilistic Matching pour créer l'`master_patient_id`. Chaque fusion est tracée (`match_method` / `score`).
4.  **GOLD (Or Zone):**
    - Ici, les données sont **agrégées et enrichies** avec le statut du consentement réel (via la jointure avec `datalake_gold.patient_consent_gold`). Seules les combinaisons de données dont la finalité est consentie peuvent être stockées comme "analyse utilisable".
5.  **Gouvernance & API (Couche d'Accès):**
    - C'est le point d'interception critique (`Contrôleur d'Accès`). Toute requête utilisateur doit passer par la vérification des **Rôles (RBAC)** et du **Consentement Purpose-by-Purpose**. Le refus d'accès est un mécanisme de protection fondamental.
    - **Audit:** Chaque étape de lecture ou de tentative d'accès génère un enregistrement immuable dans la table `access_audit`.
6.  **Évaluation Ground Truth (latérale - validation du moteur) :**
    - Le **générateur de données synthétiques** produit des jeux de référence `easy` / `medium` / `hard`
      ainsi que la **vérité de référence** (`identity_mapping.csv`).
    - Le **comparateur** mesure la **Precision / Recall / F1** des décisions du moteur (Pandas et Spark)
      contre cette vérité et écrit le rapport `evaluation_truth.md`.
    - **Règle d'explicabilité :** le ground truth n'est **jamais** fourni au moteur de déduplication ; il sert
      uniquement à mesurer la qualité du regroupement, en aval des décisions.
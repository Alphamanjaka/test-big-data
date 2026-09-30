# Guide Vagrant — VM Big Data (Hadoop / Hive / Spark)

Guide complet de démarrage, relance, (ré)initialisation et arrêt de la VM qui porte le pipeline ELT
Medallion (RAW → SILVER → GOLD) de la plateforme.

## 1. Vue d'ensemble

| Caractéristique | Valeur |
|---|---|
| Box | `ubuntu/focal64` |
| Hostname / VM | `datalake-vm` |
| IP privée | `192.168.56.10` |
| RAM / CPU | 8 Go / 4 CPU |
| Stack installée | Java 8, Hadoop 3.3.6, Hive 3.1.3, Spark 3.4.2 |
| Dossier synced | `projet/code-source/` (hôte) ↔ `/home/vagrant/datalake-final` (VM) |
| Ports forwardés | 9870 (HDFS UI), 9864 (Datanode), 8088 (YARN UI), 8042, 10000 (HiveServer2), 5000 (API) |

Emplacement : `Mon_Memoire/projet/code-source/provision/` (`Vagrantfile`, `bootstrap.sh`).

> Le provisioning (`bootstrap.sh`) est **idempotent** (marqueur `~/.provisioned`) : il installe la stack,
> les dépendances Python (`pyspark`, `sshtunnel`, `paramiko`, `rapidfuzz`, `flask`, ...), le driver JDBC
> `postgresql-42.7.3.jar` dans `$SPARK_HOME/jars/`, initialise le Metastore Derby et formate le NameNode.

### Stack complète et flux ELT

```mermaid
flowchart TB
    subgraph HOST["Hôte Windows (dev)"]
        VG["vagrant up / vagrant ssh<br/>bootstrap.sh — provisioning idempotent<br/>(Java 8 · Hadoop 3.3.6 · Hive 3.1.3 · Spark 3.4.2)"]
        CFG["provision/config/pipeline.yaml (commité, HDFS/Hive/Spark/API)<br/>+ data_sources.json (générateur synthétique, non committé)"]
        PG[("Générateur synthétique<br/>CSV — evaluation/synthetic-patient-generator<br/>pharmacy · consultation · imaging")]
    end

    subgraph VMX["VM datalake-vm — Ubuntu 20.04 · 8 Go / 4 CPU"]
        HDFS["Hadoop HDFS<br/>NameNode :9870 · DataNode · SecondaryNameNode"]
        YARN["YARN :8088<br/>ResourceManager + NodeManager"]
        SPARK["Spark 3.4.2<br/>pyspark — exécute le pipeline"]

        subgraph HIVE["Hive"]
            META["Metastore (Derby) :9083<br/>nohup hive --service metastore"]
            HS2["HiveServer2 :10000<br/>nohup hiveserver2"]
        end

        subgraph ELT["Pipeline ELT Medallion — run_pipeline.sh"]
            R0["[0/5] Générateur — ensure_generator_data.sh<br/>régénère les CSV (seed 42) s'ils manquent"]
            R1["[1/5] RAW — gen_extract_raw.py<br/>lit les CSV du générateur (type=csv)"]
            R2["[2/5] FHIR Mapping — gen_fhir_mapping.py"]
            R3["[3/5] SILVER — create_silver.py<br/>FHIR harmonisé + dédup (exact/proba — engine/)"]
            R4["[4/5] GOLD — create_gold.py<br/>patient_events_gold + patient_consent_gold"]
        end
    end

    API["API Flask :5000 — PySpark → Hive<br/>(guide-backend.md)"]
    FRONT["Frontend Next.js :3000<br/>(guide-frontend.md)"]

    VG --> HDFS
    VG --> YARN
    VG --> META --> HS2
    CFG --> R0
    PG --> R0
    SPARK --> R0
    R0 --> R1
    R1 --> R2
    R2 --> R3
    R3 --> R4
    SPARK --> R1
    SPARK --> R2
    SPARK --> R3
    SPARK --> R4
    R4 -->|"lecture Spark/Hive"| API --> FRONT
```

## 2. Avertissements importants

| Problème | Impact | Contournement |
|---|---|---|
| **Stockage NameNode dans `/tmp`** | Tout reboot efface le namespace HDFS | Re-formater le NameNode avant chaque démarrage post-reboot |
| **Données HDFS perdues après reboot** | RAW/SILVER/GOLD à refaire | Relancer le pipeline complet (`run_pipeline.sh`) |
| **CSV générateur manquants** | Sources du pipeline absentes | L'étape 0 les régénère (seed 42) ; sinon générer sur l'hôte (`guide-generateur-donnees.md`) |
| **vboxsf ne supporte pas les renames atomiques** | Spark ne peut pas écrire dans le partage | Warehouse Spark **toujours sur HDFS** — ne pas modifier `spark.sql.warehouse.dir` |
| **`pkill -f` tue la commande SSH elle-même** | Session coupée | `pkill -f 'hive' -u vagrant` (ciblé) |

## 3. Initialisation (une seule fois, après `vagrant up` la 1ʳᵉ fois)

```bash
# --- Sur Windows ---
cd F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\provision
vagrant up                # provisionne la VM (bootstrap.sh tourne automatiquement)
vagrant ssh               # connexion à la VM

# --- Dans la VM ---
source /etc/profile.d/bigdata.sh   # charge JAVA_HOME, HADOOP_HOME, etc.
```

**Vérification post-init** :
```bash
jps | sort               # doit montrer : NameNode, DataNode, SecondaryNameNode
hive --version            # doit afficher Hive 3.1.3
pyspark --version         # doit afficher Spark 3.4.2
```

> **Avant tout pipeline**, préparer la configuration ELT (non committée) :
> ```bash
> # Sur l'hôte
> cp provision/config/data_sources.example.json provision/config/data_sources.json
> # Pas d'édition requise : sources = CSV du générateur synthétique (seed 42).
> # Sources avancées MAVIS/MMT_DB : voir config/data_sources.mavis.example.json.
> ```
>
> `pipeline.yaml` (chemins HDFS, bases Hive, tables, mémoire Spark, tranches d'âge, port API) et
> `fhir_entities.json` (schéma FHIR + synonymes + mapping table→entité) sont **commités** : aucun
> copie ni édition requise pour un lancement par défaut. Seule `data_sources.json` est à créer.
> Le chemin `dir` des sources CSV utilise le token `{PROJECT_ROOT}` (résolu par `paths.expand_path`),
> ex. `{PROJECT_ROOT}/evaluation/synthetic-patient-generator/data/raw/pharmacy`.

## 4. Démarrage complet (après un reboot de la VM)

### Étape 1 — Démarrer la VM (sur Windows)
```bash
cd F:\MBDS\STAGE\PROJECT\Mon_Memoire\projet\code-source\provision
vagrant up
vagrant ssh
```

### Étape 2 — NE PAS reformater le NameNode
> Depuis le 30/09/2026, les données HDFS sont dans `/home/vagrant/hadoop-data` (`hadoop.tmp.dir`) et
> survivent au redémarrage. `hdfs namenode -format` **effacerait tout le lac** : à réserver à une VM
> neuve (le provisionnement le fait déjà une fois).

### Étape 3 — Démarrer Hadoop + YARN (ordre strict)
```bash
start-dfs.sh          # NameNode :9870, DataNode :9866
start-yarn.sh         # ResourceManager :8088, NodeManager
```
Vérifier les 5 processus : `jps | sort` → `NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager`.

### Étape 4 — Démarrer le Metastore + HiveServer2
> Double-fork `(nohup ... &)` pour que les processus survivent à la fermeture de la session SSH.
```bash
# Metastore (port :9083) — d'abord
(bash -c 'nohup hive --service metastore > /tmp/metastore.log 2>&1 &')
sleep 30    # attente obligatoire

# HiveServer2 (port :10000)
(bash -c 'nohup hiveserver2 > /tmp/hs2.log 2>&1 &')
sleep 30    # attente obligatoire
```
Vérification :
```bash
jps | grep RunJar     # 2 processus RunJar (metastore + HS2)
beeline -u jdbc:hive2://localhost:10000 -n vagrant --silent=true -e 'SHOW DATABASES;'
```

### Étape 5 — Données du générateur synthétique (automatique)
Le pipeline garantit ses données à l'**étape 0** (`ensure_generator_data.sh`) : si un CSV manque,
la source concernée est régénérée avec le seed fixe 42 (déterministe).
- Volume : réglable via `GENERATOR_PATIENTS` (défaut 500 patients maîtres).
- Sources : `evaluation/synthetic-patient-generator/data/raw/{pharmacy,consultation,imaging}/`.
- Générateur schématique : `GUIDE/guide-generateur-donnees.md`.

> **MMT_DB (PostgreSQL Laragon) et MAVIS (distant)** restent **optionnels** : à activer seulement avec
> `config/data_sources.mavis.example.json`. Le tunnel SSH MAVIS (`102.16.7.154:8090` → pg 5433 local)
> est géré par `gen_extract_raw.py` (`sshtunnel`). Sans ces sources, le pipeline tourne sur le générateur seul.

### Étape 6 — Lancer le pipeline ELT complet
```bash
# Dans la VM
cd ~/datalake-final

# Option A — mode simple (étape 0 = données générateur intégrées) :
bash provision/scripts/run_pipeline.sh
# Option B — arrière-plan :
nohup bash provision/scripts/run_pipeline.sh > /tmp/pipeline.log 2>&1 &
# Option C — pas-à-pas avec log (étape 0 automatique incluse) :
bash provision/scripts/ensure_generator_data.sh
/home/vagrant/api-venv/bin/python -m provision.scripts.ELT.gen_extract_raw 2>&1 | tee -a provision/logs/elt.log
/home/vagrant/api-venv/bin/python -m provision.scripts.ELT.gen_fhir_mapping 2>&1 | tee -a provision/logs/elt.log
/home/vagrant/api-venv/bin/python -m provision.scripts.ELT.create_silver 2>&1 | tee -a provision/logs/elt.log
/home/vagrant/api-venv/bin/python -m provision.scripts.ELT.create_gold  2>&1 | tee -a provision/logs/elt.log
```
Suivre : `tail -f ~/datalake-final/provision/logs/elt.log`.

**Drapeaux de reprise (run_pipeline.sh)** :
| Drapeau | Effet |
|---|---|
| *(aucun)* | Rechargement complet (comportement historique) |
| `--resume` | Reprend un run échoué à la 1ʳᵉ étape non terminée, sinon nouveau run **incrémental** (sources CSV inchangées **non ré-extraites**, cf. watermark) |
| `--full` | Purge + ré-extraction de tout |
| `--since YYYY-MM-DD` | Ré-extraction forcée à partir d'une date (nouvelle arrivée de données) |
| `--from <étape>` | Repart d'une étape nommée (`ensure_generator_data`, `gen_extract_raw`, `gen_fhir_mapping`, `create_silver`, `create_gold`) |
| `--dry-run` | Affiche le plan sans rien exécuter (aucun fichier d'état) |

L'état de chaque run est persisté dans `provision/metadata/pipeline_state.json` (non committé) :
`status=running` bloque tout double lancement (cron comme reprise manuelle).

**Durées typiques** (VM 8 Go / 4 CPU, 500 patients maîtres) :
| Étape | Durée approx. |
|---|---|
| [0/5] Données générateur (étape 0) | < 1 min (skip si présentes) |
| [1/5] Extraction RAW (CSV) | 1–2 min |
| [2/5] FHIR Mapping | < 1 min |
| [3/5] Transformation SILVER | 1–2 min |
| [4/5] Création GOLD | 5–8 min |

> `WARN NativeCodeLoader` / `WARN Utils: hostname resolves to loopback` = **warnings normaux**, pas des erreurs.

### Étape 6bis — Planification automatique (cron VM, optionnel)

Le pipeline peut tourner tout seul à **heure fixe** (quotidien/hebdo/mensuel) via une
vérification cron **chaque minute** (le déclenchement réel est décidé par le planificateur).

```bash
# Dans la VM (une seule fois, après que l'api-venv existe)
bash provision/scripts/scheduler/install_cron.sh
# → ajoute : * * * * * cd ~/datalake-final && $PYTHON -m provision.scripts.scheduler.scheduler --check
```

Configuration de la planification — fichier **non committé** `provision/config/schedule.yaml` :
```bash
# Sur l'hôte (ou directement sur la VM via le partage) :
cd ~/datalake-final
cp provision/config/schedule.example.yaml provision/config/schedule.yaml
```
Exemple (`schedule.yaml`) — heure dans le **fuseau de la VM (UTC+3)** :
```yaml
enabled: true
frequency: daily        # daily | weekly | monthly
time: "03:00"
day_of_week: 0          # 0=lundi .. 6=dimanche (si weekly)
day_of_month: 1         # 1..31 (si monthly, borné au dernier jour)
resume:
  mode: auto            # auto | since | full
  since: null           # date "YYYY-MM-DD" si mode: since
```

Semantics du mode `auto` : la phase d'extraction **ne rejoue pas les tables inchangées**
(empreinte sha256 + taille conservées dans `provision/metadata/watermark.json`) ; un run
précédent **échoué** est repris à la première étape non terminée (`pipeline_state.json`).

Diagnostic :
```bash
cd ~/datalake-final
/home/vagrant/api-venv/bin/python -m provision.scripts.scheduler.scheduler --status      # plan + état
/home/vagrant/api-venv/bin/python -m provision.scripts.scheduler.scheduler --dry-run    # simulation
tail -f provision/logs/scheduler.log          # trace des vérifications minute
```

> La planification se règle aussi depuis l'interface : page **Pipeline ELT** du frontend
> (API gouvernance `:8000`, endpoint `GET/PUT /pipeline/schedule`) — voir `guide-frontend.md`.

### Étape 7 — Valider les résultats
```sql
-- Via beeline (dans la VM)
beeline -u jdbc:hive2://localhost:10000 -n vagrant --silent=true --outputformat=tsv2 \
  -e "SELECT \`_source_table\`, COUNT(*) AS nb FROM datalake_silver.encounter_fhir GROUP BY \`_source_table\` ORDER BY nb DESC;"
beeline -u jdbc:hive2://localhost:10000 -n vagrant --silent=true --outputformat=tsv2 \
  -e "SELECT COUNT(*) AS events FROM datalake_gold.patient_events_gold;"
```
Référence du run consolidé (07/09/2026) : **SILVER patient = 214 lignes** (76 pharmacy + 76 consultation +
62 imaging), **145 masters**, **69 doublons** (`is_duplicate`, `match_method=exact`), GOLD
`patient_consent_gold` = 145 lignes. Depuis le branchement des tables d'événements du générateur,
SILVER contient aussi `encounter_fhir` (achats + consultations + examens) et GOLD alimente
`patient_events_gold`. Métadonnées : `cat provision/metadata/sync_metadata.json`.

### Étape 8 — Arrêt propre
```bash
# Dans la VM
pkill -f 'hive' -u vagrant    # tue metastores/HS2 seulement
sleep 3
stop-yarn.sh
stop-dfs.sh
exit
# Sur Windows
vagrant halt
```

## 5. Réinitialisation complète (reset total)

À utiliser si : repartir de zéro, données corrompues/incohérentes, `data_sources.json` modifié,
bases Hive obsolètes.

1. **Stopper les services** : `pkill -f 'hive' -u vagrant` ; `sleep 3` ; `stop-yarn.sh` ; `stop-dfs.sh`.
2. **Purger les bases Hive** :
   ```bash
   hive -e "DROP DATABASE IF EXISTS datalake_silver CASCADE;"
   hive -e "DROP DATABASE IF EXISTS datalake_gold CASCADE;"
   hive -e "DROP DATABASE IF EXISTS datalake_raw CASCADE;"
   ```
3. **Nettoyer le metastore Derby (optionnel)** :
   ```bash
   rm -rf ~/metastore_db && cd ~/hive && schematool -dbType derby -initSchema && cd ~
   ```
4. **Re-formater le NameNode** (réinitialisation volontaire : efface tout HDFS) :
   ```bash
   stop-yarn.sh; stop-dfs.sh
   rm -rf /home/vagrant/hadoop-data/dfs
   hdfs namenode -format -force -nonInteractive
   ```
5. **Relancer la pile complète** (époques 2–6 de la section 4) puis le pipeline.
6. **Vérifier** : `SHOW DATABASES` (bases recréées) + comptages.

## 6. Relance partielle (SILVER + GOLD uniquement)

Si l'extraction RAW est déjà faite (pas besoin de retélécharger) :
```bash
cd ~/datalake-final
/home/vagrant/api-venv/bin/python -m provision.scripts.ELT.create_silver
/home/vagrant/api-venv/bin/python -m provision.scripts.ELT.create_gold
```

## 7. Fichiers clés

| Fichier (dans `projet/code-source/provision/`) | Rôle |
|---|---|
| `bootstrap.sh` | Installation unique de la stack (idempotent via `~/.provisioned`) |
| `Vagrantfile` | Définition de la VM + synced folder + ports |
| `scripts/run_pipeline.sh` | Orchestrateur des 5 étapes ELT (arrêt sur erreur, reprise `--resume`) |
| `scripts/ensure_generator_data.sh` | Étape 0 : régénère les CSV du générateur (seed 42) si absents |
| `scripts/scheduler/install_cron.sh` | Pose le cron VM (vérification minute de la planification) |
| `scripts/scheduler/scheduler.py` | Planificateur : décide du lancement selon `schedule.yaml` |
| `scripts/utils/pipeline_state.py` | État de reprise du run (`pipeline_state.json`) |
| `scripts/utils/watermark.py` | Empreintes d'ingestion (`watermark.json`, anti-retraitement) |
| `config/schedule.example.yaml` | Template de la planification (→ `schedule.yaml`, **non committé**) |
| `scripts/ELT/gen_extract_raw.py` | Étape 1 : sources → parquet HDFS (postgres/sqlite/CSV) |
| `scripts/ELT/gen_fhir_mapping.py` | Étape 2 : colonnes → mapping FHIR |
| `scripts/ELT/create_silver.py` | Étape 3 : RAW → SILVER (FHIR harmonisé + dédup moteur `engine/`) |
| `scripts/ELT/create_gold.py` | Étape 4 : SILVER → GOLD (analytique + consentement) |
| `config/data_sources.json` | Sources (générateur synthétique par défaut) — **non committé** |
| `config/pipeline.yaml` | Configuration pipeline (HDFS, Hive, tables, Spark, API) — **commité**, tunable |
| `config/fhir_entities.json` | Schéma FHIR + synonymes + mapping table→entité — **commité**, tunable |
| `api/hive_api.py` | API Flask (voir `guide-backend.md`) |
| `test_startup.sh` | Health check Vagrant/Hive/API/métadonnées |

## 8. Ports

| Service | Port | Usage |
|---|---|---|
| HDFS NameNode UI | 9870 | Interface web Hadoop |
| YARN ResourceManager UI | 8088 | Interface web YARN |
| Hive Metastore | 9083 | Thrift metastore (Derby) |
| HiveServer2 | 10000 | JDBC/Beeline |
| Flask API | 5000 | API JSON (frontend) |
| PostgreSQL MMT_DB | 5432 | Optionnel (sources avancées — Laragon) |
| Tunnel MAVIS | 8090 (distant) | Optionnel (sources avancées) |

## 9. Dépannage rapide

| Symptôme | Cause probable | Correctif |
|---|---|---|
| `NameNode` refuse de démarrer | avant le 30/09/2026 : namespace dans `/tmp`, vidé au redémarrage | vérifier `hadoop.tmp.dir = /home/vagrant/hadoop-data` (`core-site.xml`) et `/tmp/start-dfs.log` ; reformater seulement en dernier recours (efface le lac) |
| Spark écrit sur vboxsf / erreurs de rename | warehouse sur partage | remettre `spark.sql.warehouse.dir = hdfs://localhost:9000/...` |
| `beeline` ne répond pas | HS2 pas (re)démarré | revoir étape 4 (metastore puis HS2, `sleep 30`) |
| SILVER explosé (nb lignes = carré) | mapping dynamique capture une clé intra-table (ex. `patient_uuid`) | exclure la colonne de jointure du mapping FHIR ; valider par `check_data.py` |
| Pipeline bloqué | `JAVA_HOME` mal défini (`\bin` en trop) | `_resolve_java_home()` normalise (déjà intégré) |

## 10. Suite logique

- Une fois le GOLD produit → **API Flask** : `GUIDE/guide-backend.md`.
- Pour le **frontend** : `GUIDE/guide-frontend.md`.
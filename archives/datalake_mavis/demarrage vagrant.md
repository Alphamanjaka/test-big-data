# Guide de démarrage, relance et réinitialisation — DataLake Mavis

> **Stack VM** : Ubuntu 20.04 | Java 8 | Hadoop 3.3.6 | Hive 3.1.3 | Spark 3.4.2  
> **VM** : `datalake-vm` (Vagrant/VirtualBox), IP 192.168.56.10, 8 Go RAM / 4 CPU  
> **Dossier partagé** : `F:/MBDS/STAGE/PROJECT/datalake_mavis` ↔ `/home/vagrant/datalake-mavis` (live-sync vboxsf)

---

## Avertissements importants

| Problème | Impact | Contournement |
|----------|--------|---------------|
| **Stockage NameNode dans `/tmp`** | Toute extinction/reboot de la VM **supprime le namespace HDFS** | Il faut reformater le NameNode avant chaque démarrage après un reboot |
| **Toutes les données HDFS sont perdues après reboot** | RAW, SILVER, GOLD à refaire | Relancer le pipeline complet (`run_pipeline.sh`) |
| **PostgreSQL (MMT_DB) sur l'hôte Windows** | N'est pas un service Windows — s'éteint au reboot | Le relancer manuellement via Laragon (ou ligne de commande) |
| **VirtualBox vboxsf ne supporte pas les renames atomiques** | Spark ne peut pas écrire dans le dossier partagé | Les scripts config spark.sql.warehouse.dir vers HDFS — ne pas changer cela |
| **`pkill -f` tue la commande SSH elle-même** | Pattern auto-matché → session coupée | Utiliser `pkill -f 'hive' -u vagrant` ou cibler le PID |

---

## 1. Initialisation (une seule fois, après `vagrant up` pour la première fois)

```bash
# --- Sur Windows ---
cd F:\MBDS\STAGE\PROJECT\datalake_mavis\provision
vagrant up                # provisionne la VM (bootstrap.sh tourne automatiquement)
vagrant ssh               # connexion à la VM

# --- Dans la VM ---
source /etc/profile.d/bigdata.sh   # charge JAVA_HOME, HADOOP_HOME, etc.
```

Le script `bootstrap.sh` (idempotent via marker `~/.provisioned`) installe :
- Java 8, Hadoop 3.3.6, Hive 3.1.3, Spark 3.4.2
- Dépendances Python : `pyspark`, `sshtunnel`, `paramiko`, `retrying`, `rapidfuzz`, `flask`, `pytz`
- Driver JDBC : `postgresql-42.7.3.jar` copié dans `$SPARK_HOME/jars/`
- Metastore Derby initialisée + configs Hive (metastore distante :9083, notification poll désactivé)
- NameNode formaté une première fois

**Vérification post-init** :
```bash
jps | sort               # doit montrer : NameNode, DataNode, SecondaryNameNode
hive --version            # doit afficher Hive 3.1.3
pyspark --version         # doit afficher Spark 3.4.2
```

---

## 2. Démarrage complet (après un reboot de la VM)

### Étape 1 — Démarrer la VM (sur Windows)
```bash
cd F:\MBDS\STAGE\PROJECT\datalake_mavis\provision
vagrant up
vagrant ssh
```

### Étape 2 — Re-formater le NameNode (obligatoire après chaque reboot)

> `/tmp/hadoop-vagrant/dfs/name` est vidé au reboot → le NameNode refuse de démarrer sans reformat.

```bash
hdfs namenode -format -force -nonInteractive
```

### Étape 3 — Démarrer Hadoop + YARN
```bash
start-dfs.sh          # NameNode :9870, DataNode :9866
start-yarn.sh         # ResourceManager :8088, NodeManager
```

Vérifier que les 5 processus tournent :
```bash
jps | sort
# Attendu : NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager
```

### Étape 4 — Démarrer le Metastore + HiveServer2

> Utiliser le double-fork `(nohup ... &)` pour que les processus survivent à la fermeture de la session SSH.

```bash
# Metastore (port :9083) — doit démarrer en premier
(noHUP_cmd="hive --service metastore"; nohup $noHUP_cmd > /tmp/metastore.log 2>&1 &)
# Ou via un script :
printf '#!/bin/bash\nnohup hive --service metastore > /tmp/metastore.log 2>&1 &\n' > /tmp/start_metastore.sh
bash /tmp/start_metastore.sh

sleep 30    # attente obligatoire

# HiveServer2 (port :10000)
printf '#!/bin/bash\nnohup hiveserver2 > /tmp/hs2.log 2>&1 &\n' > /tmp/start_hs2.sh
bash /tmp/start_hs2.sh

sleep 30    # attente obligatoire
```

Vérification :
```bash
# 2 processus RunJar doivent apparaître dans jps (metastore + HS2)
jps | grep RunJar

# Test beeline
beeline -u jdbc:hive2://localhost:10000 -n vagrant --silent=true -e 'SHOW DATABASES;'
# Attendu : datalake_gold, datalake_silver (si déjà créés), plus les bases Hive system
```

### Étape 5 — S'assurer que PostgreSQL (MMT_DB) tourne sur Windows

MMT_DB est une base PostgreSQL 18 sur l'hôte Windows (Laragon), **pas un service Windows**. Elle doit être relancée manuellement après chaque reboot de l'hôte.

```powershell
# Sur Windows (PowerShell) — depuis n'importe quel répertoire
# Option A : via Laragon GUI, activer PostgreSQL
# Option B : ligne de commande
& "C:\laragon\bin\postgresql\postgresql\bin\pg_ctl.exe" -D "C:\laragon\data\postgresql" -l "C:\laragon\data\postgresql\startup.log" start

# Vérification
$env:PGPASSWORD="<PASSWORD>"
& "C:\laragon\bin\postgresql\postgresql\bin\psql.exe" -U postgres -h 127.0.0.1 -d mmt_db -tAc "SELECT count(*) FROM gnuhealth_patient;"
# Attendu : 9791
```

### Étape 6 — Lancer le pipeline ELT complet

Le tunnel SSH vers MAVIS (`102.16.7.154:8090`) est géré automatiquement par `gen_extract_raw.py` via la lib `sshtunnel`.

```bash
# Dans la VM
cd ~/datalake-mavis

# Option A — Mode simple (exécute tout, affiche seulement le résultat final) :
bash provision/scripts/run_pipeline.sh

# Option B — Mode arrière-plan (libère le shell) :
nohup bash provision/scripts/run_pipeline.sh > /tmp/pipeline.log 2>&1 &

# Option C — Voir chaque commande en direct + sauvegarder dans le log :
/usr/bin/python3 -m provision.scripts.ELT.gen_extract_raw 2>&1 | tee -a provision/logs/elt.log
/usr/bin/python3 -m provision.scripts.ELT.gen_fhir_mapping 2>&1 | tee -a provision/logs/elt.log
/usr/bin/python3 -m provision.scripts.ELT.create_silver 2>&1 | tee -a provision/logs/elt.log
/usr/bin/python3 -m provision.scripts.ELT.create_gold 2>&1 | tee -a provision/logs/elt.log
```

Suivre la progression (si Option A ou B) :
```bash
tail -f ~/datalake-mavis/provision/logs/elt.log
```

Durées typiques (sur VM 4 CPU / 8 Go RAM) :
| Étape | Durée approx. |
|-------|---------------|
| [1/4] Extraction RAW (MAVIS) | 15-20 min |
| [1/4] Extraction RAW (MMT_DB) | < 1 min |
| [2/4] FHIR Mapping | 1-2 min |
| [3/4] Transformation SILVER | 1-2 min |
| [4/4] Création GOLD | 5-8 min |

**Console** : Les étapes Spark affichent des warnings `WARN NativeCodeLoader` et `WARN Utils: hostname resolves to loopback` — ce sont des warnings normaux, pas des erreurs.

### Étape 7 — Valider les résultats

```sql
-- Via beeline (dans la VM)
beeline -u jdbc:hive2://localhost:10000 -n vagrant --silent=true --outputformat=tsv2

-- Nombre de patients par source
SELECT `_source_table`, COUNT(*) AS nb
FROM datalake_silver.patient_fhir
GROUP BY `_source_table` ORDER BY nb DESC;
-- Attendu : ~65 000 lignes au total (MAVIS + MMT_DB)

-- Gender normalisé
SELECT gender, COUNT(*) FROM datalake_silver.patient_fhir GROUP BY gender;
-- Attendu : male/female/other + des NULLs

-- Doublons inter-sources
SELECT COUNT(*) FROM datalake_silver.patient_fhir WHERE is_duplicate = 1;
-- Attendu : ~24 000

-- GOLD
SELECT COUNT(*) FROM datalake_gold.patient_events_gold;

-- Métadonnées de synchronisation
cat ~/datalake-mavis/provision/metadata/sync_metadata.json
```

### Étape 8 — Arrêt propre

```bash
# Dans la VM
pkill -f 'hive' -u vagrant       # tue les métastores/HS2 ( éviter pkill -f hive sans -u)
sleep 3
stop-yarn.sh
stop-dfs.sh
exit

# Sur Windows
vagrant halt
```

---

## 3. Réinitialisation complète (reset total)

Utiliser cette procédure si :
- Vous voulez repartir de zéro
- Les données sont corrompues ou inconsistentes
- Vous avez changé `data_sources.json` et voulez tout refaire
- La base Hive contient des tables obsolètes avec des emplacements incorrects

### Étape 1 — Stopper tous les services (dans la VM)

```bash
pkill -f 'hive' -u vagrant
sleep 3
stop-yarn.sh
stop-dfs.sh
```

### Étape 2 — Purger les bases Hive du metastore

```bash
# Supprimer les bases datalake (les tables sur HDFS seront supprimées automatiquement)
hive -e "DROP DATABASE IF EXISTS datalake_silver CASCADE;"
hive -e "DROP DATABASE IF EXISTS datalake_gold CASCADE;"
hive -e "DROP DATABASE IF EXISTS datalake_raw CASCADE;"
hive -e "SHOW DATABASES;"
# Ne doivent plus apparaître : datalake_silver, datalake_gold, datalake_raw
```

### Étape 3 — Nettoyer le metastore Derby (optionnel, si corrompu)

```bash
# ATTENTION : supprime TOUTES les bases Hive (y compris les bases système)
rm -rf ~/metastore_db
cd ~/hive
schematool -dbType derby -initSchema
cd ~
```

### Étape 4 — Re-formater le NameNode

```bash
# Supprimer l'ancien namespace + data
rm -rf /tmp/hadoop-vagrant/dfs

# Re-formater
hdfs namenode -format -force -nonInteractive
```

### Étape 5 — Relancer la pile complète (comme Étape 2-6 de la section 2)

```bash
source /etc/profile.d/bigdata.sh
start-dfs.sh
start-yarn.sh
# Démarrer metastore + HS2 (voir section 2, étape 4)
# Relancer le pipeline complet
bash ~/datalake-mavis/provision/scripts/run_pipeline.sh
```

### Étape 6 — Vérifier

```bash
beeline -u jdbc:hive2://localhost:10000 -n vagrant --silent=true --outputformat=tsv2 \
  -e "SHOW DATABASES;"
# Datalake bases recréées

beeline -u jdbc:hive2://localhost:10000 -n vagrant --silent=true --outputformat=tsv2 \
  -f ~/datalake-mavis/provision/tmp_validation.sql
# Totaux identiques à un run précédent
```

---

## 4. Relance partielle (Silver + Gold uniquement)

Si l'extraction RAW est déjà faite (pas besoin de retélécharger les données) :

```bash
# Dans la VM
cd ~/datalake-mavis
python3 -m provision.scripts.ELT.create_silver && \
python3 -m provision.scripts.ELT.create_gold
# OU via run_pipeline.sh complet (l'étape 1/4 re-écrit les fichiers RAW de toutes façons)
```

---

## 5. Fichiers clés du projet

| Fichier | Rôle |
|---------|------|
| `provision/bootstrap.sh` | Installation unique de la stack (idempotent via `~/.provisioned`) |
| `provision/scripts/run_pipeline.sh` | Orchestrateur : lance les 4 étapes dans l'ordre, arrêt sur erreur |
| `provision/scripts/ELT/gen_extract_raw.py` | Étape 1 : JDBC → HDFS (RAW), gère le tunnel SSH automatiquement |
| `provision/scripts/ELT/gen_fhir_mapping.py` | Étape 2 : analyse les colonnes et génère le mapping FHIR |
| `provision/scripts/ELT/create_silver.py` | Étape 3 : RAW → SILVER (FHIR harmonisé, déduplique inter-sources) |
| `provision/scripts/ELT/create_gold.py` | Étape 4 : SILVER → GOLD (table analytique `patient_events_gold`) |
| `provision/config/data_sources.json` | Sources de données (MAVIS via SSH + MMT_DB local) |
| `provision/metadata/fhir_mapping.json` | Résultat de l'étape 2 (mapping colonnes → champs FHIR) |
| `provision/metadata/extract_raw_report.json` | Rapport d'extraction (colonnes par table) |
| `provision/metadata/sync_metadata.json` | Métadonnées de la dernière synchronisation |
| `provision/logs/elt.log` | Logs complets du pipeline |
| `provision/jars/postgresql-42.7.3.jar` | Driver JDBC pour PostgreSQL (Spark) |

---

## 6. Ports utilisés

| Service | Port | Usage |
|---------|------|-------|
| HDFS NameNode UI | 9870 | Interface web Hadoop |
| YARN ResourceManager UI | 8088 | Interface web YARN |
| Hive Metastore | 9083 | Thrift metastore (Derby embarqué) |
| HiveServer2 | 10000 | JDBC/Beeline client access |
| Flask API | 5000 | API JSON pour le frontend |
| PostgreSQL (MMT_DB) | 5432 | Base Windows (Laragon) |
| SSH Tunnel MAVIS | 8090 (remote) → 5433 (local) | Tunnel vers PostgreSQL MAVIS distant |

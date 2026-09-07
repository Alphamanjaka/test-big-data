#!/bin/bash
# Boot de la VM datalake (réutilisée) pour le run du pipeline data_lake_final
# reformat NameNode (obligatoire après poweroff : /tmp vidé) + services
set -e

export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export HADOOP_HOME=/home/vagrant/hadoop
export HIVE_HOME=/home/vagrant/hive
export SPARK_HOME=/home/vagrant/spark
export PATH=$JAVA_HOME/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$HIVE_HOME/bin:$SPARK_HOME/bin:$PATH

echo "=== [1/5] Reformat NameNode ==="
hdfs namenode -format -force -nonInteractive

echo "=== [2/5] start-dfs.sh + start-yarn.sh ==="
start-dfs.sh
start-yarn.sh
sleep 5
jps | sort

echo "=== [3/5] Metastore (thrift:9083) ==="
(nohup hive --service metastore > /tmp/metastore.log 2>&1 &)
sleep 30
jps | grep -c RunJar || true

echo "=== [4/5] HiveServer2 (:10000) ==="
(nohup hiveserver2 > /tmp/hs2.log 2>&1 &)
sleep 20

echo "=== [4bis] Purge des bases Hive obsolètes ==="
hive -e "DROP DATABASE IF EXISTS datalake_silver CASCADE;" || echo "warn drop silver"
hive -e "DROP DATABASE IF EXISTS datalake_gold CASCADE;" || echo "warn drop gold"
hive -e "DROP DATABASE IF EXISTS MAVIS CASCADE; DROP DATABASE IF EXISTS MMT_DB CASCADE; DROP DATABASE IF EXISTS CLINIQUE CASCADE;" || true

echo "=== [5/5] Deps engine (pandas + psycopg) dans api-venv ==="
/home/vagrant/api-venv/bin/pip install --quiet pandas psycopg[binary] || echo "pip install partiel/fail"

echo "=== FIN BOOT ==="
jps | sort
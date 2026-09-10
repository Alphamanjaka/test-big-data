#!/bin/bash
# =============================================================
# bootstrap.sh — Provisioning automatique de la VM datalake
# Stack : JAVA 8 | HADOOP 3.3.6 | HIVE 3.1.3 | SPARK 3.4.2
# (versions identiques à l'ancienne VM — voir old/commande.md)
# Idempotent : ne réinstalle pas si déjà provisionné.
# =============================================================
set -e

MARKER="/home/vagrant/.provisioned"
if [ -f "$MARKER" ]; then
    echo ">>> VM déjà provisionnée — skip bootstrap"
    exit 0
fi

HADOOP_VERSION="3.3.6"
HIVE_VERSION="3.1.3"
SPARK_VERSION="3.4.2"
APACHE="https://archive.apache.org/dist"

JAVA_HOME="/usr/lib/jvm/java-8-openjdk-amd64"
HADOOP_HOME="/home/vagrant/hadoop"
HIVE_HOME="/home/vagrant/hive"
SPARK_HOME="/home/vagrant/spark"

echo ">>> [1/8] Paquets système (Java 8, outils, Python)"
apt-get update -y
apt-get install -y openjdk-8-jdk openssh-server python3-pip python3-venv curl wget net-tools
update-alternatives --set java "$JAVA_HOME/jre/bin/java" 2>/dev/null || true

echo ">>> [2/8] SSH localhost sans mot de passe (requis par Hadoop)"
su - vagrant -c "ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa -q; cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys; ssh-keyscan -H localhost >> ~/.ssh/known_hosts 2>/dev/null"

echo ">>> [3/8] Téléchargement et installation de Hadoop ${HADOOP_VERSION}"
if [ ! -d "$HADOOP_HOME" ]; then
    wget -q "${APACHE}/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz" -O /tmp/hadoop.tar.gz
    tar -xzf /tmp/hadoop.tar.gz -C /home/vagrant
    mv "/home/vagrant/hadoop-${HADOOP_VERSION}" "$HADOOP_HOME"
fi

echo ">>> [4/8] Configuration Hadoop (pseudo-distribué, fs.defaultFS=hdfs://localhost:9000)"
cat > "$HADOOP_HOME/etc/hadoop/core-site.xml" <<EOF
<?xml version="1.0"?>
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://localhost:9000</value>
  </property>
  <!-- Impersonation : requis pour HiveServer2 -->
  <property>
    <name>hadoop.proxyuser.vagrant.hosts</name>
    <value>*</value>
  </property>
  <property>
    <name>hadoop.proxyuser.vagrant.groups</name>
    <value>*</value>
  </property>
</configuration>
EOF

cat > "$HADOOP_HOME/etc/hadoop/hdfs-site.xml" <<EOF
<?xml version="1.0"?>
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
</configuration>
EOF

cat > "$HADOOP_HOME/etc/hadoop/mapred-site.xml" <<EOF
<?xml version="1.0"?>
<configuration>
  <property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
  </property>
  <property>
    <name>yarn.app.mapreduce.am.env</name>
    <value>HADOOP_MAPRED_HOME=\${HADOOP_HOME}</value>
  </property>
  <property>
    <name>mapreduce.map.env</name>
    <value>HADOOP_MAPRED_HOME=\${HADOOP_HOME}</value>
  </property>
  <property>
    <name>mapreduce.reduce.env</name>
    <value>HADOOP_MAPRED_HOME=\${HADOOP_HOME}</value>
  </property>
</configuration>
EOF

cat > "$HADOOP_HOME/etc/hadoop/yarn-site.xml" <<EOF
<?xml version="1.0"?>
<configuration>
  <property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
  </property>
</configuration>
EOF

# JAVA_HOME pour Hadoop + users pour scripts start-*.sh lancés par vagrant
sed -i "s|^# export JAVA_HOME=.*|export JAVA_HOME=${JAVA_HOME}|" "$HADOOP_HOME/etc/hadoop/hadoop-env.sh"
grep -q "HDFS_NAMENODE_USER" "$HADOOP_HOME/etc/hadoop/hadoop-env.sh" || cat >> "$HADOOP_HOME/etc/hadoop/hadoop-env.sh" <<EOF
export HDFS_NAMENODE_USER=vagrant
export HDFS_DATANODE_USER=vagrant
export HDFS_SECONDARYNAMENODE_USER=vagrant
export YARN_RESOURCEMANAGER_USER=vagrant
export YARN_NODEMANAGER_USER=vagrant
EOF

chown -R vagrant:vagrant "$HADOOP_HOME"

echo ">>> [5/8] Téléchargement et installation de Hive ${HIVE_VERSION}"
if [ ! -d "$HIVE_HOME" ]; then
    wget -q "${APACHE}/hive/hive-${HIVE_VERSION}/apache-hive-${HIVE_VERSION}-bin.tar.gz" -O /tmp/hive.tar.gz
    tar -xzf /tmp/hive.tar.gz -C /home/vagrant
    mv "/home/vagrant/apache-hive-${HIVE_VERSION}-bin" "$HIVE_HOME"
    # Fix conflit guava Hive/Hadoop
    rm -f "$HIVE_HOME/lib/guava-"*.jar
    cp "$HADOOP_HOME/share/hadoop/hdfs/lib/guava-"*.jar "$HIVE_HOME/lib/"
fi
chown -R vagrant:vagrant "$HIVE_HOME"

# Metastore Derby (comme ancienne VM) — init une seule fois
su - vagrant -c "
export JAVA_HOME=${JAVA_HOME}
export HADOOP_HOME=${HADOOP_HOME}
export HIVE_HOME=${HIVE_HOME}
export PATH=\$HIVE_HOME/bin:\$PATH
if [ ! -d ~/metastore_db ]; then
    schematool -dbType derby -initSchema
fi
"

# Metastore DISTANTE pour tous les clients (HS2, Spark, CLI) :
# évite le conflit Derby XSDB6 (une seule connexion embarquée possible)
# + désactivation du notification poll (bug Hive 3.1.3 au premier démarrage)
cat > "$HIVE_HOME/conf/hive-site.xml" <<EOF
<?xml version="1.0"?>
<configuration>
  <property>
    <name>hive.metastore.uris</name>
    <value>thrift://localhost:9083</value>
  </property>
  <property>
    <name>hive.notification.event.poll.interval</name>
    <value>0s</value>
  </property>
</configuration>
EOF

echo ">>> [6/8] Téléchargement et installation de Spark ${SPARK_VERSION}"
if [ ! -d "$SPARK_HOME" ]; then
    wget -q "${APACHE}/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz" -O /tmp/spark.tgz
    tar -xzf /tmp/spark.tgz -C /home/vagrant
    mv "/home/vagrant/spark-${SPARK_VERSION}-bin-hadoop3" "$SPARK_HOME"
fi
chown -R vagrant:vagrant "$SPARK_HOME"
cp "$SPARK_HOME/conf/spark-env.sh.template" "$SPARK_HOME/conf/spark-env.sh"
cat >> "$SPARK_HOME/conf/spark-env.sh" <<EOF
export JAVA_HOME=${JAVA_HOME}
export HADOOP_HOME=${HADOOP_HOME}
export HIVE_HOME=${HIVE_HOME}
EOF
cat > "$SPARK_HOME/conf/spark-defaults.conf" <<EOF
spark.master               local[*]
spark.sql.catalogImplementation   hive
EOF
# Spark doit aussi connaître la metastore distante (thrift 9083)
cp "$HIVE_HOME/conf/hive-site.xml" "$SPARK_HOME/conf/"
# Driver JDBC PostgreSQL requis par gen_extract_raw.py (spark.jars)
cp /home/vagrant/datalake-final/provision/jars/postgresql-42.7.3.jar "$SPARK_HOME/jars/"

echo ">>> [7/8] Dépendances Python du pipeline (venv + packages API)"
# Virtualenv pour contourner le conflit pyOpenSSL/cryptography sur Ubuntu 20.04
if [ ! -d "/home/vagrant/api-venv" ]; then
    python3 -m venv /home/vagrant/api-venv
    chown -R vagrant:vagrant /home/vagrant/api-venv
fi
# Installer les dépendances dans le venv
su - vagrant -c "
source ~/api-venv/bin/activate
pip install --upgrade pip
pip install \
    pyspark==3.4.2 \
    sshtunnel \
    paramiko \
    retrying \
    rapidfuzz \
    flask \
    flask-cors \
    requests \
    pytz \
"
# Activer le venv dans .bashrc pour les sessions interactives
grep -q "api-venv/bin/activate" /home/vagrant/.bashrc || \
    echo 'source ~/api-venv/bin/activate' >> /home/vagrant/.bashrc

echo ">>> [8/8] Variables d'environnement + formatage NameNode"
cat > /etc/profile.d/bigdata.sh <<EOF
export JAVA_HOME=${JAVA_HOME}
export HADOOP_HOME=${HADOOP_HOME}
export HIVE_HOME=${HIVE_HOME}
export SPARK_HOME=${SPARK_HOME}
export PATH=\$JAVA_HOME/bin:\$HADOOP_HOME/bin:\$HADOOP_HOME/sbin:\$HIVE_HOME/bin:\$SPARK_HOME/bin:\$PATH
source ~/api-venv/bin/activate
EOF
chmod +x /etc/profile.d/bigdata.sh
grep -q bigdata.sh /home/vagrant/.bashrc || echo "source /etc/profile.d/bigdata.sh" >> /home/vagrant/.bashrc

# Formatage NameNode (une seule fois — protégé par le marker d'idempotence)
# Skip si le namenode est déjà en cours d'exécution
su - vagrant -c "
export JAVA_HOME=${JAVA_HOME} HADOOP_HOME=${HADOOP_HOME} PATH=\$HADOOP_HOME/bin:\$PATH
if ! pgrep -f 'NameNode' > /dev/null 2>&1; then
    hdfs namenode -format -force -nonInteractive
else
    echo '>>> NameNode already running — skip format'
fi
"

touch "$MARKER"
echo ">>> ✅ Bootstrap terminé. Prochaines étapes : start-dfs.sh, start-yarn.sh, hive metastore+hiveserver2"

from sshtunnel import SSHTunnelForwarder
import os
import json
import socket
import sqlite3
import paramiko
from pyspark.sql import SparkSession
import logging
import datetime
import decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
from retrying import retry
import time
import uuid
from ..utils.sync_utils import update_sync_metadata

# ============================================================
# CONFIGURATION DES LOGS
# ============================================================:
LOG_DIR = "/home/vagrant/datalake-mavis/provision/logs/extract"
os.makedirs(LOG_DIR, exist_ok=True)

date_str = datetime.datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"generate_fhir_mapping_{date_str}.log")

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

pg_to_hive = {
    "integer": "INT",
    "bigint": "BIGINT",
    "smallint": "SMALLINT",
    "character varying": "STRING",
    "varchar": "STRING",
    "text": "STRING",
    "timestamp without time zone": "TIMESTAMP",
    "timestamp": "TIMESTAMP",
    "date": "DATE",
    "boolean": "BOOLEAN",
    "numeric": "DECIMAL",
    "decimal": "DECIMAL",
    "double precision": "DOUBLE",
    "real": "FLOAT"
}

# Affinités SQLite -> types Hive
sqlite_to_hive = {
    "INT": "INT",
    "INTEGER": "INT",
    "BIGINT": "BIGINT",
    "SMALLINT": "SMALLINT",
    "TINYINT": "SMALLINT",
    "TEXT": "STRING",
    "VARCHAR": "STRING",
    "CHAR": "STRING",
    "CLOB": "STRING",
    "DATE": "DATE",
    "DATETIME": "TIMESTAMP",
    "TIMESTAMP": "TIMESTAMP",
    "REAL": "DOUBLE",
    "DOUBLE": "DOUBLE",
    "FLOAT": "DOUBLE",
    "NUMERIC": "DECIMAL",
    "DECIMAL": "DECIMAL",
    "BOOLEAN": "BOOLEAN",
}

# ============================================================
# JSON SERIALIZER
# ============================================================
def json_serial(obj):
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, uuid.UUID):
        return str(obj)
    return str(obj)

# ============================================================
# CREATION DU TUNNEL SSH
# ============================================================
@retry(stop_max_attempt_number=3, wait_fixed=5000)
def create_ssh_tunnel(ssh_config, remote_host="localhost", remote_port=5432, local_port=5433):
    """Crée et teste un tunnel SSH pour la base distante."""
    host, port, user = ssh_config["host"], ssh_config["port"], ssh_config["user"]
    password = ssh_config.get("password")

    try:
        # --- Test authentification SSH ---
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            host,
            port=port,
            username=user,
            password=password,
            timeout=60,
            allow_agent=False,
            look_for_keys=False
        )
        ssh.close()
        logger.info(f"SSH auth réussie pour {host}:{port}")

        # --- Création du tunnel ---
        tunnel = SSHTunnelForwarder(
            (host, port),
            ssh_username=user,
            ssh_password=password,
            remote_bind_address=(remote_host, remote_port),
            local_bind_address=('localhost', local_port)
        )
        tunnel.start()
        logger.info(f"Tunnel SSH actif: {remote_host}:{remote_port} → localhost:{local_port}")

        # --- Vérifie que le port local répond ---
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('localhost', local_port))
        sock.close()
        if result != 0:
            raise Exception(f"Tunnel échoué (code {result})")

        logger.info("Tunnel SSH opérationnel ✅")
        return tunnel, local_port

    except Exception as e:
        logger.error(f"Échec de création du tunnel SSH: {str(e)}")
        raise

# ============================================================
# DISCOVER POSTGRESQL
# ============================================================
@retry(stop_max_attempt_number=3, wait_fixed=5000)
def discover_postgres(source, spark, source_index):
    source_name = source["name"]
    logger.info(f"=== Début de la découverte pour {source_name} ===")

    db_cfg = source["db"]
    ssh_cfg = source.get("ssh")
    tables_info, failed_tables = [], []

    source_path = "/home/vagrant/datalake-mavis/provision/config/data_sources.json"
    cache_path = f"/home/vagrant/datalake-mavis/provision/metadata/extract/{source_name}_extract_raw_report.json"
    failed_tables_path = f"/home/vagrant/datalake-mavis/provision/metadata/extract/{source_name}_failed_tables.json"
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    tunnel = None
    try:
        # --- Mot de passe DB ---
        db_password = os.getenv(f"POSTGRES_PASSWORD_{source_name.upper()}", db_cfg.get("password"))
        if not db_password:
            raise ValueError(f"Mot de passe manquant pour {source_name}")

        # --- Tunnel SSH ou connexion directe ---
        jdbc_host, jdbc_port = db_cfg["host"], db_cfg["port"]
        if ssh_cfg:
            tunnel, local_port = create_ssh_tunnel(ssh_cfg, db_cfg["host"], db_cfg["port"])
            jdbc_host, jdbc_port = "localhost", local_port
            logger.info(f"[{source_name}] Connexion via SSH → localhost:{jdbc_port}")
        else:
            # Test rapide de port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((db_cfg["host"], db_cfg["port"]))
            sock.close()
            logger.info(f"Connexion directe OK à {db_cfg['host']}:{db_cfg['port']}")

        # --- JDBC URL ---
        url = f"jdbc:postgresql://{jdbc_host}:{jdbc_port}/{db_cfg['database']}?socketTimeout=900&connectTimeout=120&sslmode=disable"
        properties = {
            "user": db_cfg["user"],
            "password": db_password,
            "driver": "org.postgresql.Driver",
            "fetchsize": "100"
        }

        # --- Tables ---
        tables_query = """
            (SELECT table_name, table_type 
             FROM information_schema.tables 
             WHERE table_schema = 'public' 
               AND table_type IN ('BASE TABLE', 'VIEW')) t
        """
        df_tables = spark.read.jdbc(url=url, table=tables_query, properties=properties)
        tables = [{"table_name": r["table_name"], "table_type": r["table_type"]} for r in df_tables.collect()]
        logger.info(f"[{source_name}] {len(tables)} tables détectées")

        # --- Clés étrangères ---
        foreign_keys_query = """
            (SELECT
                tc.table_name,
                kcu.column_name AS fk_column,
                ccu.table_name AS referenced_table
             FROM information_schema.table_constraints AS tc
             JOIN information_schema.key_column_usage AS kcu
               ON tc.constraint_name = kcu.constraint_name
             JOIN information_schema.constraint_column_usage AS ccu
               ON ccu.constraint_name = tc.constraint_name
             WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public') t
        """
        df_fk = spark.read.jdbc(url=url, table=foreign_keys_query, properties=properties)
        foreign_keys = [r.asDict() for r in df_fk.collect()]
        logger.info(f"[{source_name}] {len(foreign_keys)} relations FK détectées")

        # --- Tables à inclure ---
        # On démarre de la liste explicite de la config, puis on ajoute la
        # main_table et les tables référencées par FK depuis celle-ci.
        # (anti-régression : conserve les tables configurées explicitement, ex. les 11 de MAVIS)
        main_table = source.get("main_table")
        tables_to_include = set(source.get("tables_to_include") or [])
        if main_table:
            tables_to_include.add(main_table)
            for fk in foreign_keys:
                if fk["table_name"] == main_table:
                    tables_to_include.add(fk["referenced_table"])
        logger.info(f"[{source_name}] Tables incluses: {tables_to_include}")

        # --- Mise à jour du JSON config ---
        with open(source_path, "r", encoding="utf-8-sig") as f:
            data_sources = json.load(f)
        for src in data_sources:
            if src.get("name") == source_name:
                src["tables_to_include"] = list(tables_to_include)
        with open(source_path, "w") as f:
            json.dump(data_sources, f, indent=2)

        # --- Exploration des tables ---
        for table_name in tables_to_include:
            try:
                logger.info(f"[{source_name}] Extraction table {table_name}")
                df_cols = spark.read.jdbc(
                    url=url,
                    table=f"(SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='{table_name}') t",
                    properties=properties
                )
                columns = [{"name": r["column_name"], "type": r["data_type"]} for r in df_cols.collect()]

                df_count = spark.read.jdbc(
                    url=url,
                    table=f"(SELECT COUNT(*) AS row_count FROM public.\"{table_name}\") t",
                    properties=properties
                )
                row_count = df_count.collect()[0]["row_count"]

                df_data = spark.read.jdbc(url=url, table=f'public."{table_name}"', properties=properties)
                sample_data = [row.asDict() for row in df_data.limit(5).collect()]

                # --- Écriture Parquet ---
                hdfs_path = f"hdfs://localhost:9000/datalake/raw/{source_name}/{table_name}"
                df_data.write.mode("overwrite").parquet(hdfs_path)
                logger.info(f"[{source_name}] Table {table_name} → {hdfs_path} OK")

                # --- Création de la base Hive si elle n'existe pas ---
                spark.sql(f"CREATE DATABASE IF NOT EXISTS {source_name}")

                # --- Création table Hive externe ---
                hive_table_name = f"{source_name}.{table_name}"
                cols_hive = []
                for col in columns:
                    pg_type = col['type'].lower()
                    hive_type = pg_to_hive.get(pg_type, "STRING")  # fallback sur STRING
                    cols_hive.append(f"{col['name']} {hive_type}")

                spark.sql(f"""
                    CREATE EXTERNAL TABLE IF NOT EXISTS {hive_table_name} (
                        {', '.join(cols_hive)}
                    )
                    STORED AS PARQUET
                    LOCATION '{hdfs_path}'
                """)
                
                logger.info(f"[{source_name}] Table Hive externe {hive_table_name} créée")

                tables_info.append({
                    "source_name": source_name,
                    "table_name": table_name,
                    "table_type": next(t["table_type"] for t in tables if t["table_name"] == table_name),
                    "columns": columns,
                    "row_count": row_count,
                    "sample_data": sample_data,
                    "hdfs_path": hdfs_path
                })
            except Exception as e:
                failed_tables.append({"table_name": table_name, "error": str(e)})
                logger.error(f"[{source_name}] Erreur table {table_name}: {str(e)}")

    except Exception as e:
        logger.error(f"[{source_name}] ERREUR GLOBALE: {str(e)}")
        tables_info.append({"source_name": source_name, "error": str(e)})

    finally:
        if tunnel:
            tunnel.stop()
            logger.info(f"[{source_name}] Tunnel SSH fermé")

    # --- Sauvegarde ---
    with open(cache_path, "w") as f:
        json.dump(tables_info, f, indent=2, default=json_serial)
    with open(failed_tables_path, "w") as f:
        json.dump(failed_tables, f, indent=2, default=json_serial)

    logger.info(f"[{source_name}] Terminé: {len(tables_info)} tables, {len(failed_tables)} échecs")
    return tables_info

# ============================================================
# DISCOVER SQLITE (source locale "CLINIQUE")
# ============================================================
def discover_sqlite(source, spark, source_index):
    """Extrait une base SQLite (fichier local, source type='sqlite') vers RAW/Hive.

    Lit le fichier .db via sqlite3 (stdlib), construit un DataFrame Spark et
    écrit le Parquet sur HDFS + crée la table Hive externe, avec le même format
    de rapport que discover_postgres (extract_raw_report).
    """
    source_name = source["name"]
    logger.info(f"=== Début de la découverte SQLite pour {source_name} ===")

    db_cfg = source["db"]
    db_path = db_cfg["file"]
    tables_info, failed_tables = [], []

    cache_path = f"/home/vagrant/datalake-mavis/provision/metadata/extract/{source_name}_extract_raw_report.json"
    failed_tables_path = f"/home/vagrant/datalake-mavis/provision/metadata/extract/{source_name}_failed_tables.json"
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)

    main_table = source.get("main_table")
    tables_to_include = set(source.get("tables_to_include") or [])
    if main_table:
        tables_to_include.add(main_table)

    try:
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Fichier SQLite introuvable: {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        for table_name in sorted(tables_to_include):
            try:
                logger.info(f"[{source_name}] Extraction table {table_name}")
                # Schéma
                cur.execute(f"PRAGMA table_info('{table_name}')")
                cols = [{"name": r["name"], "sqlite_type": r["type"].upper()} for r in cur.fetchall()]
                if not cols:
                    raise Exception(f"Table {table_name} absente ou vide")

                # Données
                cur.execute(f'SELECT * FROM "{table_name}"')
                rows = cur.fetchall()
                row_count = len(rows)

                hdfs_path = f"hdfs://localhost:9000/datalake/raw/{source_name}/{table_name}"

                if rows:
                    # Construire le DataFrame Spark
                    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, \
                        LongType, DoubleType, BooleanType, DateType, TimestampType, DecimalType

                    def spark_type(st):
                        st = st.upper()
                        if st in ("INT", "INTEGER", "SMALLINT", "TINYINT", "MEDIUMINT"):
                            return IntegerType()
                        if st == "BIGINT":
                            return LongType()
                        if st in ("REAL", "DOUBLE", "FLOAT"):
                            return DoubleType()
                        if st == "BOOLEAN":
                            return BooleanType()
                        if st in ("DATE",):
                            return DateType()
                        if st in ("DATETIME", "TIMESTAMP"):
                            return TimestampType()
                        if st in ("NUMERIC", "DECIMAL"):
                            return DecimalType(20, 4)
                        return StringType()

                    schema = StructType([
                        StructField(c["name"], spark_type(c["sqlite_type"]), True) for c in cols
                    ])
                    data = [tuple(r[c["name"]] for c in cols) for r in rows]
                    df = spark.createDataFrame(data, schema=schema)
                else:
                    # Table vide : créer un DataFrame vide avec le schéma
                    from pyspark.sql.types import StructType, StructField, StringType, IntegerType, \
                        LongType, DoubleType, BooleanType, DateType, TimestampType, DecimalType

                    def spark_type(st):
                        st = st.upper()
                        if st in ("INT", "INTEGER", "SMALLINT", "TINYINT", "MEDIUMINT"):
                            return IntegerType()
                        if st == "BIGINT":
                            return LongType()
                        if st in ("REAL", "DOUBLE", "FLOAT"):
                            return DoubleType()
                        if st == "BOOLEAN":
                            return BooleanType()
                        if st in ("DATE",):
                            return DateType()
                        if st in ("DATETIME", "TIMESTAMP"):
                            return TimestampType()
                        if st in ("NUMERIC", "DECIMAL"):
                            return DecimalType(20, 4)
                        return StringType()

                    schema = StructType([
                        StructField(c["name"], spark_type(c["sqlite_type"]), True) for c in cols
                    ])
                    df = spark.createDataFrame(spark.sparkContext.emptyRDD(), schema)

                df.write.mode("overwrite").parquet(hdfs_path)
                logger.info(f"[{source_name}] Table {table_name} → {hdfs_path} OK")

                # Création base + table Hive externe
                spark.sql(f"CREATE DATABASE IF NOT EXISTS {source_name}")
                cols_hive = [f'{c["name"]} {sqlite_to_hive.get(c["sqlite_type"], "STRING")}' for c in cols]
                spark.sql(f"""
                    CREATE EXTERNAL TABLE IF NOT EXISTS {source_name}.{table_name} (
                        {', '.join(cols_hive)}
                    )
                    STORED AS PARQUET
                    LOCATION '{hdfs_path}'
                """)
                logger.info(f"[{source_name}] Table Hive externe {source_name}.{table_name} créée")

                sample_data = [r.asDict() for r in df.limit(5).collect()]
                tables_info.append({
                    "source_name": source_name,
                    "table_name": table_name,
                    "table_type": "BASE TABLE",
                    "columns": [{"name": c["name"], "type": c["sqlite_type"].lower()} for c in cols],
                    "row_count": row_count,
                    "sample_data": sample_data,
                    "hdfs_path": hdfs_path
                })
            except Exception as e:
                failed_tables.append({"table_name": table_name, "error": str(e)})
                logger.error(f"[{source_name}] Erreur table {table_name}: {str(e)}")

        conn.close()
    except Exception as e:
        logger.error(f"[{source_name}] ERREUR GLOBALE: {str(e)}")
        tables_info.append({"source_name": source_name, "error": str(e)})

    with open(cache_path, "w") as f:
        json.dump(tables_info, f, indent=2, default=json_serial)
    with open(failed_tables_path, "w") as f:
        json.dump(failed_tables, f, indent=2, default=json_serial)

    logger.info(f"[{source_name}] Terminé: {len(tables_info)} tables, {len(failed_tables)} échecs")
    return tables_info

# ============================================================
# MAIN PIPELINE
# ============================================================
def main():
    start = time.time()
    spark = SparkSession.builder \
        .appName("DatalakeDiscoverPostgres") \
        .master("local[*]") \
        .config("spark.jars", ",".join([
            "/home/vagrant/spark/jars/postgresql-42.7.3.jar",
        ])) \
        .config("spark.executor.memory", "4g") \
        .config("spark.driver.memory", "2g") \
        .enableHiveSupport() \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    config_path = "/home/vagrant/datalake-mavis/provision/config/data_sources.json"
    with open(config_path, encoding="utf-8-sig") as f:
        sources = json.load(f)

    extract_raw_report = {}

    def dispatcher(src, index):
        stype = src.get("type")
        if stype == "sqlite":
            return discover_sqlite(src, spark, index)
        return discover_postgres(src, spark, index)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(dispatcher, src, i): src
            for i, src in enumerate(sources)
        }
        for future in as_completed(futures):
            src = futures[future]
            try:
                extract_raw_report[src["name"]] = future.result()
                print(f"✅ {src['name']} traité avec succès")
            except Exception as e:
                extract_raw_report[src["name"]] = [{"error": str(e)}]
                print(f"❌ Erreur {src['name']}: {str(e)}")

    output = "/home/vagrant/datalake-mavis/provision/metadata/extract_raw_report.json"
    with open(output, "w") as f:
        json.dump(extract_raw_report, f, indent=2, default=json_serial)

    elapsed = round(time.time() - start, 2)
    update_sync_metadata("RAW", status="ok")
    print(f"\n✅ Pipeline terminé en {elapsed}s — Rapport: {output}")
    spark.stop()

if __name__ == "__main__":
    main()

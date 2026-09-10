from sshtunnel import SSHTunnelForwarder
# ⚠️ DÉPRÉCIÉ — ancien pipeline ELT remplacé par les scripts ELT/ actifs.
import os
import json
import socket
import paramiko
from pyspark.sql import SparkSession
from sentence_transformers import SentenceTransformer, util
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
# ============================================================
logging.basicConfig(
    filename="/home/vagrant/datalake-mavis/provision/logs/gen_metadata.log",
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

        # # --- Clés étrangères ---
        # foreign_keys_query = """
        #     (SELECT
        #         tc.table_name,
        #         kcu.column_name AS fk_column,
        #         ccu.table_name AS referenced_table
        #      FROM information_schema.table_constraints AS tc
        #      JOIN information_schema.key_column_usage AS kcu
        #        ON tc.constraint_name = kcu.constraint_name
        #      JOIN information_schema.constraint_column_usage AS ccu
        #        ON ccu.constraint_name = tc.constraint_name
        #      WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public') t
        # """
        # df_fk = spark.read.jdbc(url=url, table=foreign_keys_query, properties=properties)
        # foreign_keys = [r.asDict() for r in df_fk.collect()]
        # logger.info(f"[{source_name}] {len(foreign_keys)} relations FK détectées")

        # # --- Tables à inclure ---
        main_table = source.get("main_table")
        tables_to_include = source.get("tables_to_include")
        # tables_to_include = set()
        # if main_table:
        #     tables_to_include.add(main_table)
        #     for fk in foreign_keys:
        #         if fk["table_name"] == main_table:
        #             tables_to_include.add(fk["referenced_table"])
        # logger.info(f"[{source_name}] Tables incluses: {tables_to_include}")

        # # --- Mise à jour du JSON config ---
        # with open(source_path, "r") as f:
        #     data_sources = json.load(f)
        # for src in data_sources:
        #     if src.get("name") == source_name:
        #         src["tables_to_include"] = list(tables_to_include)
        # with open(source_path, "w") as f:
        #     json.dump(data_sources, f, indent=2)

        # --- Nouvelle partie : FK filtrées pour main_table et tables_to_include ---
        tables_list = [main_table] + tables_to_include
        fk_query = f"""
            (SELECT
                tc.table_name,
                kcu.column_name AS fk_column,
                ccu.table_name AS referenced_table,
                ccu.column_name AS referenced_column
             FROM information_schema.table_constraints AS tc
             JOIN information_schema.key_column_usage AS kcu
               ON tc.constraint_name = kcu.constraint_name
             JOIN information_schema.constraint_column_usage AS ccu
               ON ccu.constraint_name = tc.constraint_name
             WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
               AND (tc.table_name IN ({','.join([f"'{t}'" for t in tables_list])})
                    OR ccu.table_name IN ({','.join([f"'{t}'" for t in tables_list])}))) t
        """
        df_fk = spark.read.jdbc(url=url, table=fk_query, properties=properties)
        foreign_keys = [r.asDict() for r in df_fk.collect()]
        logger.info(f"[{source_name}] {len(foreign_keys)} relations FK pertinentes détectées")
        
        # --- Exploration des tables ---
        for table_name in tables_to_include:
            try:
                logger.info(f"[{source_name}] Extraction table {table_name}")
                df_cols = spark.read.jdbc(
                    url=url,
                    table=f"(SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='public' AND table_name='{table_name}') t",
                    properties=properties
                )

                # --- Enrichissement colonnes avec FK ---
                columns = []
                for r in df_cols.collect():
                    col_name = r["column_name"]
                    col_type = r["data_type"]
                    fk_info = next(
                        (fk for fk in foreign_keys if fk["table_name"] == table_name and fk["fk_column"] == col_name),
                        None
                    )
                    if fk_info:
                        columns.append({
                            "name": col_name,
                            "type": col_type,
                            "fk": f'{fk_info["referenced_table"]}.{fk_info["referenced_column"]}'
                        })
                    else:
                        columns.append({"name": col_name, "type": col_type})

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
        .config("spark.executor.memory", "6g") \
        .config("spark.driver.memory", "3g") \
        .enableHiveSupport() \
        .getOrCreate()

    spark.sparkContext.setLogLevel("ERROR")

    config_path = "/home/vagrant/datalake-mavis/provision/config/data_sources.json"
    with open(config_path) as f:
        sources = json.load(f)

    extract_raw_report = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(discover_postgres, src, spark, i): src
            for i, src in enumerate(sources) if src["type"] == "postgres"
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

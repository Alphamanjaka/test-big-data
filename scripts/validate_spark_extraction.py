import json

import pandas as pd

from patient_platform.spark.csv_extractor import SparkCSVExtractor
from patient_platform.spark.session import get_or_create_session


def validate():
    with open("config/sources.json", encoding="utf-8") as handle:
        sources = json.load(handle)

    errors = []
    spark = get_or_create_session()
    total_lines = 0
    for system, paths in sources.items():
        spark_patients = SparkCSVExtractor(paths["patient_source"], system).extract()
        spark_business = SparkCSVExtractor(paths["business_source"], system).extract()
        pandas_patients = pd.read_csv(paths["patient_source"], dtype=str).fillna("")
        pandas_business = pd.read_csv(paths["business_source"], dtype=str).fillna("")

        spark_cols = set(spark_patients.columns) - {"source_system", "source_file"}
        pandas_cols = set(pandas_patients.columns)
        if spark_cols != pandas_cols:
            errors.append(f"{system}: colonnes divergentes Spark={spark_cols} / Pandas={pandas_cols}")

        spark_patient_count = spark_patients.count()
        if spark_patient_count != len(pandas_patients):
            errors.append(f"{system}: patients Spark={spark_patient_count} Pandas={len(pandas_patients)}")
        if spark_business.count() != len(pandas_business):
            errors.append(f"{system}: métier Spark={spark_business.count()} Pandas={len(pandas_business)}")

        meta = spark_patients.select("source_system").distinct().collect()
        if meta[0][0] != system:
            errors.append(f"{system}: source_system={meta[0][0]}")

        total_lines += spark_patient_count + spark_business.count()
        print(f"{system}: {spark_patient_count} patients + {spark_business.count()} métier, "
              f"colonnes={sorted(spark_cols)}")

    spark.stop()
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"VALIDATION OK — {total_lines} lignes extraites, cohérent avec Pandas")


if __name__ == "__main__":
    validate()
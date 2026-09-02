import pandas as pd

from patient_platform.config import load_sources
from patient_platform.extract.csv_extractor import CSVExtractor
from patient_platform.spark.csv_extractor import SparkCSVExtractor
from patient_platform.spark.session import get_or_create_session
from patient_platform.spark.transform import standardize_patients
from patient_platform.transform.canonical import standardize_patients as pandas_standardize

CANONICAL_FIELDS = ["source_system", "source_patient_id", "first_name", "last_name",
                    "full_name", "birth_date", "phone", "address", "source_file"]


def validate():
    sources = load_sources()

    errors = []
    spark = get_or_create_session()
    total = 0
    for system, paths in sources.items():
        spark_frame = standardize_patients(
            SparkCSVExtractor(paths["patient_source"], system).extract(), system)
        spark_pandas = spark_frame.select(*CANONICAL_FIELDS).toPandas()
        pandas_frame = CSVExtractor(paths["patient_source"], system).extract()
        expected = pd.DataFrame(
            [vars(patient) for patient in pandas_standardize(pandas_frame, system)])
        expected["birth_date"] = expected["birth_date"].apply(
            lambda value: value.isoformat() if value is not None else None)
        spark_pandas["birth_date"] = spark_pandas["birth_date"].apply(
            lambda value: value.isoformat() if value is not None else None)
        expected = expected.sort_values("source_patient_id").reset_index(drop=True)
        spark_pandas = spark_pandas.sort_values("source_patient_id").reset_index(drop=True)

        for field in CANONICAL_FIELDS:
            mismatch = (expected[field].astype(str) != spark_pandas[field].astype(str))
            if mismatch.any():
                for idx in expected[mismatch].index:
                    errors.append(
                        f"{system}:{expected.at[idx, 'source_patient_id']} "
                        f"{field}: MVP={expected.at[idx, field]!r} Spark={spark_pandas.at[idx, field]!r}")

        total += len(spark_pandas)
        print(f"{system}: {len(spark_pandas)} patients canoniques OK")

    spark.stop()
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"VALIDATION TRANSFORMATION OK — {total} patients identiques au MVP")


if __name__ == "__main__":
    validate()
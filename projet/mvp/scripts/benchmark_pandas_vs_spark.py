import time

import pandas as pd

from patient_platform.config import load_sources
from patient_platform.spark.csv_extractor import SparkCSVExtractor
from patient_platform.spark.session import get_or_create_session

N_ITERATIONS = 5


def benchmark():
    sources = load_sources()

    spark = get_or_create_session()
    results = []
    for system, paths in sources.items():
        pandas_patient = _bench_pandas(paths["patient_source"])
        spark_patient = _bench_spark_timed(SparkCSVExtractor(paths["patient_source"], system))
        results.append({
            "source": system,
            "pandas_rows": pandas_patient[1],
            "pandas_ms": pandas_patient[0],
            "spark_ms": spark_patient[0],
        })
    spark.stop()
    return results


def _bench_pandas(path):
    sample = pd.read_csv(path)
    start = time.perf_counter()
    for _ in range(N_ITERATIONS):
        pd.read_csv(path)
    return (time.perf_counter() - start) / N_ITERATIONS * 1000, len(sample)


def _bench_spark_timed(extractor):
    start = time.perf_counter()
    frame = extractor.extract()
    count = frame.count()
    return (time.perf_counter() - start) * 1000, count


if __name__ == "__main__":
    rows = benchmark()
    print(f"{'source':<14}{'lignes':>8}{'pandas_ms':>12}{'spark_ms':>12}{'ratio spark/panda':>18}")
    for row in rows:
        ratio = row["spark_ms"] / max(row["pandas_ms"], 0.001)
        print(f"{row['source']:<14}{row['pandas_rows']:>8}{row['pandas_ms']:>12.1f}{row['spark_ms']:>12.1f}{ratio:>18.1f}")
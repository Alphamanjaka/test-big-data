import json
import time

from patient_platform.spark.csv_extractor import SparkCSVExtractor
from patient_platform.spark.session import get_or_create_session


def benchmark():
    with open("config/sources.json", encoding="utf-8") as handle:
        sources = json.load(handle)

    extractor_bench = {}
    total_patients = 0
    total_business = 0
    spark = get_or_create_session()

    for system, paths in sources.items():
        patient_elapsed, patient_count = _bench_extract(SparkCSVExtractor(paths["patient_source"], system))
        business_elapsed, business_count = _bench_extract(SparkCSVExtractor(paths["business_source"], system))
        extractor_bench[system] = {
            "patient_rows": patient_count,
            "patient_extract_ms": round(patient_elapsed * 1000, 1),
            "business_rows": business_count,
            "business_extract_ms": round(business_elapsed * 1000, 1),
        }
        total_patients += patient_count
        total_business += business_count

    spark.stop()
    return extractor_bench, total_patients, total_business


def _bench_extract(extractor):
    start = time.perf_counter()
    frame = extractor.extract()
    count = frame.count()
    return time.perf_counter() - start, count


if __name__ == "__main__":
    bench, n_patients, n_business = benchmark()
    print(f"Total patients: {n_patients}")
    print(f"Total business : {n_business}")
    for system, values in bench.items():
        print(f"{system}: {values}")
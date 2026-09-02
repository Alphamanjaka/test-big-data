from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

from patient_platform.spark.extractor import SparkExtractor
from patient_platform.spark.session import get_or_create_session


class SparkCSVExtractor(SparkExtractor):
    """Reads a synthetic source CSV into a Spark DataFrame with source context."""

    def extract(self) -> DataFrame:
        if not self.file_path.exists():
            raise FileNotFoundError(f"Source file not found: {self.file_path}")
        spark = get_or_create_session()
        frame = spark.read.option("header", True).csv(str(self.file_path))
        frame = frame.withColumn("source_system", F.lit(self.source_system))
        return frame.withColumn("source_file", F.lit(self.file_path.name))
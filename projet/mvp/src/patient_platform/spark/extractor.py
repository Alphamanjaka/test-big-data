from abc import ABC, abstractmethod
from pathlib import Path

from pyspark.sql import DataFrame


class SparkExtractor(ABC):
    """Base contract for Spark source extractors."""

    def __init__(self, file_path: str | Path, source_system: str):
        self.file_path = Path(file_path)
        self.source_system = source_system

    @abstractmethod
    def extract(self) -> DataFrame:
        """Return the source rows as a Spark DataFrame."""
        raise NotImplementedError
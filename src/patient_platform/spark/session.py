import os
import shutil
import sys
from functools import lru_cache
from pathlib import Path

from pyspark.sql import SparkSession


def _resolve_java_home() -> Path:
    """Return a JAVA_HOME whose ``<root>/bin/java.exe`` exists.

    A trailing ``\\bin`` in JAVA_HOME (common on Windows) makes Spark build
    ``<root>\\bin\\bin\\java`` and fail with ``The system cannot find the
    path specified``, so it is normalised here before the JVM is started.
    """
    expected = os.environ.get("JAVA_HOME")
    if expected:
        root = Path(expected).resolve()
        if (root / "bin" / "java.exe").exists():
            return root
        if root.name == "bin" and root.joinpath("java.exe").exists():
            return root.parent
    discovered = shutil.which("java")
    if discovered:
        return Path(discovered).resolve().parent.parent
    raise RuntimeError("Java not found. Install a JDK and set JAVA_HOME.")


@lru_cache(maxsize=1)
def get_or_create_session(app_name: str = "patient-data-platform", master: str = "local[2]") -> SparkSession:
    """Create a shared local Spark session once per process."""
    os.environ["JAVA_HOME"] = str(_resolve_java_home())
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    return (
        SparkSession.builder
        .master(master)
        .appName(app_name)
        .config("spark.ui.enabled", "false")
        .config("spark.log.level", "WARN")
        .getOrCreate()
    )
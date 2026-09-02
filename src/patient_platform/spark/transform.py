from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, StringType

from patient_platform.transform.canonical import _birth_date, _phone, _text

_text_udf = F.udf(_text, StringType())
_phone_udf = F.udf(_phone, StringType())
_birth_date_udf = F.udf(_birth_date, DateType())


def _split_name(value: str, strip_dots: bool) -> tuple[str, str]:
    name = _full_name(value, strip_dots)
    parts = name.split(" ", 1)
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""
    return first, last


def _full_name(value: str, strip_dots: bool) -> str:
    return _text(value).replace(".", "") if strip_dots else _text(value)


def _first_name_udf(strip_dots: bool):
    return F.udf(lambda value: _split_name(value, strip_dots)[0], StringType())


def _last_name_udf(strip_dots: bool):
    return F.udf(lambda value: _split_name(value, strip_dots)[1], StringType())


def _full_name_udf(strip_dots: bool):
    return F.udf(lambda value: _full_name(value, strip_dots), StringType())


def map_patient(frame: DataFrame, source_system: str) -> DataFrame:
    """Map a source DataFrame to the canonical patient shape (Spark-native)."""
    if source_system == "pharmacy":
        mapped = (
            frame.withColumn("full_name", _text_udf(F.col("nom_complet")))
            .withColumn("first_name", _first_name_udf(False)(F.col("nom_complet")))
            .withColumn("last_name", _last_name_udf(False)(F.col("nom_complet")))
            .withColumn("source_patient_id", _text_udf(F.col("client_id")))
            .withColumn("phone", _phone_udf(F.col("telephone")))
            .withColumn("address", _text_udf(F.col("adresse")))
            .withColumn("birth_date", _birth_date_udf(F.col("naissance")))
        )
    elif source_system == "consultation":
        mapped = (
            frame.withColumn("first_name", _text_udf(F.col("prenom")))
            .withColumn("last_name", _text_udf(F.col("nom")))
            .withColumn("source_patient_id", _text_udf(F.col("patient_code")))
            .withColumn("phone", _phone_udf(F.col("phone_number")))
            .withColumn("address", F.lit(""))
            .withColumn("birth_date", _birth_date_udf(F.col("date_naiss")))
        )
        mapped = mapped.withColumn(
            "full_name",
            F.when(F.col("last_name") != "", F.concat_ws(" ", F.col("first_name"), F.col("last_name")))
            .otherwise(F.col("first_name")),
        )
    elif source_system == "imaging":
        mapped = (
            frame.withColumn("full_name", _full_name_udf(True)(F.col("patient_name")))
            .withColumn("first_name", _first_name_udf(True)(F.col("patient_name")))
            .withColumn("last_name", _last_name_udf(True)(F.col("patient_name")))
            .withColumn("source_patient_id", _text_udf(F.col("id_personne")))
            .withColumn("phone", _phone_udf(F.col("tel")))
            .withColumn("address", F.lit(""))
            .withColumn("birth_date", _birth_date_udf(F.col("dob")))
        )
    else:
        raise ValueError(f"Unsupported source system: {source_system}")

    return (
        mapped.withColumn("source_system", F.lit(source_system))
        .select(
            "source_system", "source_patient_id", "first_name", "last_name",
            "full_name", "birth_date", "phone", "address", "source_file",
        )
    )


def standardize_patients(frame: DataFrame, source_system: str) -> DataFrame:
    """Return the canonical DataFrame for a source, consistently with the MVP."""
    return map_patient(frame, source_system)
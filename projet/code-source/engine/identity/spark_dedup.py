"""
Déduplication v2 dans Spark : regroupement réparti par clé d'identité.

La règle stricte de `engine.identity.rules` est un regroupement par clé : Spark
la calcule fiche par fiche (UDF appelant `from_dict`, `identity_key` et
`master_id`, les mêmes fonctions que `matcher`), puis désigne la fiche
fondatrice de chaque clé par `row_number` (rang de source, puis identifiant
source). Rien n'est rapatrié sur le driver : le travail se répartit entre les
exécuteurs, et l'identifiant du patient maître, dérivé de la clé, ne demande
aucune numérotation globale.

`pyspark` n'est importé qu'à l'appel : le module reste importable (et la
fonction `_identity` testable) sans Spark.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Tuple

from engine.identity.canonical import from_dict
from engine.identity.rules import (
    EXPLANATION_CIN,
    EXPLANATION_FOUNDER,
    EXPLANATION_INCOMPLETE,
    EXPLANATION_NAME,
    identity_key,
    master_id,
)

# Ordre d'ingestion : la première source fournit la fiche fondatrice.
SOURCE_RANK = {"pharmacy": 0, "consultation": 1, "imaging": 2}


def _identity(source_system, source_patient_id, name, birth_date, cin, birth_city,
              gender) -> Tuple[Optional[str], str, str]:
    """(clé en texte ou None, identifiant du patient maître, règle 'cin' / 'nom' / '')."""
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()
    patient = from_dict({
        "source_system": source_system or "",
        "source_patient_id": source_patient_id or "",
        "full_name": name or "",
        "birth_date": birth_date if isinstance(birth_date, date) else (birth_date or ""),
        "cin": cin,
        "birth_city": birth_city or "",
        "address": "",
        "gender": gender or "",
    })
    key = identity_key(patient)
    return (
        "|".join(key) if key else None,
        master_id(key, patient.source_system, patient.source_patient_id),
        key[0] if key else "",
    )


def deduplicate_df(df, source_col="_source_system", id_col="source_patient_id", name_col="name",
                   birth_col="birth_date", cin_col="cin", city_col="birth_city", gender_col="gender"):
    """Décisions de déduplication d'un DataFrame de fiches patients.

    Retourne un DataFrame (source_col, id_col, master_patient_id, match_method,
    match_score, explanation) : une ligne par fiche, `new_master` pour la fiche
    fondatrice d'une identité ou une identité incomplète, `exact` sinon.
    """
    from pyspark.sql import Window
    from pyspark.sql import functions as F
    from pyspark.sql import types as T

    schema = T.StructType([
        T.StructField("key", T.StringType()),
        T.StructField("master_patient_id", T.StringType()),
        T.StructField("rule", T.StringType()),
    ])
    identity = F.udf(_identity, schema)
    rank = F.create_map(*[F.lit(x) for pair in SOURCE_RANK.items() for x in pair])

    keyed = df.select(
        F.col(source_col), F.col(id_col),
        identity(F.col(source_col), F.col(id_col), F.col(name_col), F.col(birth_col),
                 F.col(cin_col), F.col(city_col), F.col(gender_col)).alias("_identity"),
    ).select(
        source_col, id_col,
        F.col("_identity.key").alias("_key"),
        F.col("_identity.master_patient_id").alias("master_patient_id"),
        F.col("_identity.rule").alias("_rule"),
        F.coalesce(F.element_at(rank, F.col(source_col)), F.lit(len(SOURCE_RANK))).alias("_rank"),
    )
    order = Window.partitionBy("_key").orderBy("_rank", id_col)
    founder = F.col("_key").isNull() | (F.row_number().over(order) == 1)
    rule_text = F.when(F.col("_rule") == "cin", F.lit(EXPLANATION_CIN)).otherwise(F.lit(EXPLANATION_NAME))
    return keyed.select(
        source_col, id_col, "master_patient_id",
        F.when(founder, F.lit("new_master")).otherwise(F.lit("exact")).alias("match_method"),
        F.lit(1.0).alias("match_score"),
        F.when(F.col("_key").isNull(), F.lit(EXPLANATION_INCOMPLETE))
         .when(founder, F.concat(F.lit(EXPLANATION_FOUNDER + " ("), rule_text, F.lit(")")))
         .otherwise(rule_text).alias("explanation"),
    )

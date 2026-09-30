#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""age_tranches.py — tranches d'âge de la zone GOLD (pipeline.yaml → gold.age_tranches).

Chaque tranche couvre l'intervalle semi-ouvert [borne basse, borne basse de la
tranche suivante) ; la dernière s'arrête à sa borne haute, incluse. Les bornes
hautes des autres tranches ne servent qu'à la lecture du fichier : les appliquer
comme des bornes fermées laissait des âges sans tranche (4,25 ans tombait entre
« 1-4 ans » et « 5-14 ans »), classés « unknown ».

`label_for` est la référence Python (testable sans Spark) ; `tranche_column`
construit la même règle en expression Spark native, sans UDF Python.
"""

UNKNOWN = "unknown"


def intervals(tranches):
    """[(borne basse incluse, borne haute, borne haute incluse ?, libellé)], par borne basse."""
    ordered = sorted(tranches, key=lambda t: t[0])
    out = []
    for i, (low, high, label) in enumerate(ordered):
        if i + 1 < len(ordered):
            out.append((float(low), float(ordered[i + 1][0]), False, label))
        else:
            out.append((float(low), float(high), True, label))
    return out


def label_for(age, tranches):
    """Libellé de la tranche d'un âge en années (None ou hors bornes → « unknown »)."""
    if age is None:
        return UNKNOWN
    for low, high, closed, label in intervals(tranches):
        if low <= age and (age <= high if closed else age < high):
            return label
    return UNKNOWN


def tranche_column(age_col, tranches):
    """Même règle que `label_for`, en expression Spark (`CASE WHEN`) sur la colonne `age_col`."""
    from pyspark.sql import functions as F

    expr = None
    for low, high, closed, label in intervals(tranches):
        upper = age_col <= F.lit(high) if closed else age_col < F.lit(high)
        cond = (age_col >= F.lit(low)) & upper
        expr = F.when(cond, F.lit(label)) if expr is None else expr.when(cond, F.lit(label))
    return expr.otherwise(F.lit(UNKNOWN))

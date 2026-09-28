#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fhir_schema.py
==============
Charge le schéma FHIR et les synonymes depuis fhir_entities.json.
Les deux dicts (FHIR_FIELDS, FHIR_SYNONYMS) sont disponibles pour import.
"""

import json
import os

_FHIR_ENTITIES_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "config", "fhir_entities.json"
)

with open(_FHIR_ENTITIES_PATH, encoding="utf-8") as _f:
    _cfg = json.load(_f)

FHIR_FIELDS = {entity: data["fields"] for entity, data in _cfg["entities"].items()}
FHIR_SYNONYMS = _cfg.get("synonyms", {})

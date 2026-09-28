#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fhir_synonyms.py (compat)
--------------------------
Fichier de compatibilité. Les synonymes sont maintenant dans fhir_entities.json
et chargés par fhir_schema.py. Ce module ré-exporte FHIR_SYNONYMS pour ne pas
casser les imports existants.
"""
from .fhir_schema import FHIR_SYNONYMS  # noqa: F401

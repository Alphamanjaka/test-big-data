#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mock_data.py — Données fictives de gouvernance (backend)
==========================================================
Jeu de démonstration utilisé en fallback par `hive_api.py` lorsque les tables
SILVER/GOLD ne sont pas joignables (Spark/Hive indisponible ou table vide).
"""

# --- Gouvernance : indicateurs de déduplication (KPI SILVER/moteur) ---
MOCK_GOVERNANCE_DUPLICATES = {
    "total_patients": 65214,
    "total_masters": 62180,
    "duplicates": 3034,
    "duplicate_rate": 4.65,
    "by_method": {"exact": 1876, "probabilistic": 1158},
}

# --- Gouvernance : consentements (purpose-by-purpose) ---
# Les finalités reprennent exactement l'alphabet de
# `engine/governance/consent.py` (PURPOSES) : `validate_purpose` refuse toute
# autre valeur, donc un jeu de démonstration avec des finalités inventées
# afficherait un état de consentement que le moteur ne pourrait jamais produire.
MOCK_CONSENT = [
    {"master_patient_id": "PAT-0001", "name": "RAKOTO Jean",
     "purpose": "api_access", "granted": True, "recorded_at": "2025-09-01"},
    {"master_patient_id": "PAT-0002", "name": "ANDRIANARIVO Marie",
     "purpose": "research", "granted": True, "recorded_at": "2025-09-03"},
    {"master_patient_id": "PAT-0003", "name": "RABE Paul",
     "purpose": "analytics", "granted": True, "recorded_at": "2025-09-05"},
    {"master_patient_id": "PAT-0004", "name": "RASOA Liva",
     "purpose": "research", "granted": False, "recorded_at": "2025-09-08"},
    {"master_patient_id": "PAT-0005", "name": "RAZAFY Hery",
     "purpose": "analytics", "granted": True, "recorded_at": "2025-09-12"},
    {"master_patient_id": "PAT-0006", "name": "RAMA Vero",
     "purpose": "api_access", "granted": False, "recorded_at": "2025-09-15"},
]
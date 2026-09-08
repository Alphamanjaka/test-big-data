#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mock_data.py — Données fictives RMA (backend)
==============================================
Remplace les données fictives du frontend (visualisation_app/src/lib/mockData.ts).
Centralisées côté backend tant que les sources réelles ne couvrent pas ces
tableaux RMA dans la couche GOLD.
"""

# --- Tableau 5 : Diagnostics consultations externes (CIM-10) ---
MOCK_DIAGNOSTICS_HEATMAP = [
    {"diagnosis_code": "A09", "diagnosis": "Diarrhée et gastro-entérite",
     "age_0_28j": 12, "age_29_59j": 18, "age_2_11m": 85, "age_1_4a": 142,
     "age_5_14a": 67, "age_15_24a": 34, "age_25_59a": 56, "age_60plus": 23, "total": 437},
    {"diagnosis_code": "B54", "diagnosis": "Paludisme non confirmé",
     "age_0_28j": 5, "age_29_59j": 8, "age_2_11m": 62, "age_1_4a": 189,
     "age_5_14a": 134, "age_15_24a": 78, "age_25_59a": 95, "age_60plus": 12, "total": 583},
    {"diagnosis_code": "J18", "diagnosis": "Pneumonie",
     "age_0_28j": 22, "age_29_59j": 31, "age_2_11m": 74, "age_1_4a": 98,
     "age_5_14a": 45, "age_15_24a": 18, "age_25_59a": 42, "age_60plus": 35, "total": 365},
    {"diagnosis_code": "A08", "diagnosis": "Infection respiratoire aiguë",
     "age_0_28j": 15, "age_29_59j": 22, "age_2_11m": 56, "age_1_4a": 112,
     "age_5_14a": 89, "age_15_24a": 45, "age_25_59a": 67, "age_60plus": 28, "total": 434},
    {"diagnosis_code": "E46", "diagnosis": "Malnutrition protéino-calorique",
     "age_0_28j": 8, "age_29_59j": 14, "age_2_11m": 48, "age_1_4a": 76,
     "age_5_14a": 23, "age_15_24a": 5, "age_25_59a": 3, "age_60plus": 1, "total": 178},
    {"diagnosis_code": "B05", "diagnosis": "Rougeole",
     "age_0_28j": 2, "age_29_59j": 3, "age_2_11m": 28, "age_1_4a": 67,
     "age_5_14a": 42, "age_15_24a": 8, "age_25_59a": 4, "age_60plus": 0, "total": 154},
    {"diagnosis_code": "A16", "diagnosis": "Tuberculose",
     "age_0_28j": 0, "age_29_59j": 1, "age_2_11m": 3, "age_1_4a": 8,
     "age_5_14a": 12, "age_15_24a": 18, "age_25_59a": 45, "age_60plus": 15, "total": 102},
    {"diagnosis_code": "N39", "diagnosis": "Infection urinaire",
     "age_0_28j": 3, "age_29_59j": 5, "age_2_11m": 12, "age_1_4a": 18,
     "age_5_14a": 24, "age_15_24a": 56, "age_25_59a": 89, "age_60plus": 34, "total": 241},
    {"diagnosis_code": "K35", "diagnosis": "Appendicite aiguë",
     "age_0_28j": 0, "age_29_59j": 0, "age_2_11m": 2, "age_1_4a": 8,
     "age_5_14a": 15, "age_15_24a": 22, "age_25_59a": 31, "age_60plus": 9, "total": 87},
    {"diagnosis_code": "O80", "diagnosis": "Accouchement normal",
     "age_0_28j": 0, "age_29_59j": 0, "age_2_11m": 0, "age_1_4a": 0,
     "age_5_14a": 0, "age_15_24a": 45, "age_25_59a": 134, "age_60plus": 2, "total": 181},
    {"diagnosis_code": "I10", "diagnosis": "Hypertension artérielle",
     "age_0_28j": 0, "age_29_59j": 0, "age_2_11m": 0, "age_1_4a": 0,
     "age_5_14a": 2, "age_15_24a": 12, "age_25_59a": 98, "age_60plus": 67, "total": 179},
    {"diagnosis_code": "E11", "diagnosis": "Diabète sucré",
     "age_0_28j": 0, "age_29_59j": 0, "age_2_11m": 0, "age_1_4a": 0,
     "age_5_14a": 1, "age_15_24a": 8, "age_25_59a": 56, "age_60plus": 34, "total": 99},
    {"diagnosis_code": "L30", "diagnosis": "Dermatite",
     "age_0_28j": 6, "age_29_59j": 12, "age_2_11m": 34, "age_1_4a": 56,
     "age_5_14a": 38, "age_15_24a": 28, "age_25_59a": 45, "age_60plus": 18, "total": 237},
    {"diagnosis_code": "H66", "diagnosis": "Otite moyenne",
     "age_0_28j": 4, "age_29_59j": 8, "age_2_11m": 42, "age_1_4a": 78,
     "age_5_14a": 45, "age_15_24a": 12, "age_25_59a": 8, "age_60plus": 3, "total": 200},
    {"diagnosis_code": "A00", "diagnosis": "Choléra",
     "age_0_28j": 2, "age_29_59j": 3, "age_2_11m": 8, "age_1_4a": 15,
     "age_5_14a": 12, "age_15_24a": 18, "age_25_59a": 24, "age_60plus": 10, "total": 92},
]

# --- Tableau 9 : Morbidité et mortalité hospitalière ---
MOCK_MORTALITY = [
    {"service": "Médecine", "code": "J18", "diagnostic": "Pneumonie", "cas": 145, "deces": 18},
    {"service": "Médecine", "code": "B54", "diagnostic": "Paludisme grave", "cas": 89, "deces": 12},
    {"service": "Médecine", "code": "A09", "diagnostic": "Diarrhée sévère", "cas": 112, "deces": 8},
    {"service": "Médecine", "code": "E46", "diagnostic": "Malnutrition sévère", "cas": 67, "deces": 14},
    {"service": "Médecine", "code": "I63", "diagnostic": "Accident vasculaire cérébral", "cas": 34, "deces": 11},
    {"service": "Chirurgie", "code": "K35", "diagnostic": "Appendicite compliquée", "cas": 45, "deces": 2},
    {"service": "Chirurgie", "code": "S72", "diagnostic": "Fracture fémur", "cas": 38, "deces": 3},
    {"service": "Chirurgie", "code": "K40", "diagnostic": "Hernie étranglée", "cas": 22, "deces": 4},
    {"service": "Chirurgie", "code": "C18", "diagnostic": "Cancer colique", "cas": 12, "deces": 5},
    {"service": "Maternité", "code": "O14", "diagnostic": "Toxémie gravidique", "cas": 56, "deces": 6},
    {"service": "Maternité", "code": "O72", "diagnostic": "Hémorragie du post-partum", "cas": 34, "deces": 4},
    {"service": "Maternité", "code": "O86", "diagnostic": "Infection du post-partum", "cas": 28, "deces": 2},
    {"service": "Pédiatrie", "code": "J18", "diagnostic": "Pneumonie néonatale", "cas": 78, "deces": 9},
    {"service": "Pédiatrie", "code": "B54", "diagnostic": "Paludisme pédiatrique", "cas": 95, "deces": 7},
    {"service": "Pédiatrie", "code": "E46", "diagnostic": "Malnutrition infantile", "cas": 54, "deces": 11},
    {"service": "Pédiatrie", "code": "A09", "diagnostic": "Gastro-entérite aiguë", "cas": 88, "deces": 5},
]

# --- Tableaux 11 & 12 : Consultations prénatales & Maternité ---
MOCK_MATERNITE = [
    {"month": "Jan 2025", "total": 245, "accouchements": 178, "deces_maternels": 3, "live_births_total": 173},
    {"month": "Fév 2025", "total": 232, "accouchements": 165, "deces_maternels": 2, "live_births_total": 161},
    {"month": "Mar 2025", "total": 278, "accouchements": 192, "deces_maternels": 4, "live_births_total": 186},
    {"month": "Avr 2025", "total": 256, "accouchements": 183, "deces_maternels": 1, "live_births_total": 180},
    {"month": "Mai 2025", "total": 289, "accouchements": 201, "deces_maternels": 5, "live_births_total": 194},
    {"month": "Juin 2025", "total": 267, "accouchements": 188, "deces_maternels": 2, "live_births_total": 184},
    {"month": "Juil 2025", "total": 298, "accouchements": 215, "deces_maternels": 6, "live_births_total": 207},
    {"month": "Août 2025", "total": 275, "accouchements": 195, "deces_maternels": 3, "live_births_total": 190},
    {"month": "Sep 2025", "total": 310, "accouchements": 228, "deces_maternels": 7, "live_births_total": 219},
    {"month": "Oct 2025", "total": 285, "accouchements": 205, "deces_maternels": 4, "live_births_total": 199},
    {"month": "Nov 2025", "total": 302, "accouchements": 220, "deces_maternels": 5, "live_births_total": 213},
    {"month": "Déc 2025", "total": 268, "accouchements": 190, "deces_maternels": 3, "live_births_total": 185},
]

# --- Tableau 16 : Activité de laboratoire ---
MOCK_LABORATORY = [
    {"examen": "BK (Bacille de Koch)", "total": 456, "nouveaux": 89, "positifs": 67},
    {"examen": "BH (Bilan Hépatique)", "total": 782, "nouveaux": 134, "positifs": 156},
    {"examen": "Paludisme (Goutte épaisse)", "total": 1245, "nouveaux": 312, "positifs": 423},
    {"examen": "NFS (Numération Formule Sanguine)", "total": 2134, "nouveaux": 456, "positifs": 289},
    {"examen": "VIH (Sérologie)", "total": 890, "nouveaux": 198, "positifs": 45},
    {"examen": "Syphilis (VDRL/TPHA)", "total": 645, "nouveaux": 145, "positifs": 78},
    {"examen": "Hépatite B (AgHBs)", "total": 534, "nouveaux": 112, "positifs": 34},
    {"examen": "Hépatite C (Anti-VHC)", "total": 423, "nouveaux": 98, "positifs": 12},
    {"examen": "Glycémie", "total": 1567, "nouveaux": 345, "positifs": 234},
    {"examen": "Créatinine", "total": 987, "nouveaux": 212, "positifs": 145},
    {"examen": "Sérologie Toxoplasmose", "total": 345, "nouveaux": 78, "positifs": 23},
    {"examen": "Uroculture", "total": 678, "nouveaux": 156, "positifs": 89},
]

# --- Tableau 25 : Prise en charge Paludisme ---
MOCK_MALARIA = {
    "consultants_fievre": 2345,
    "tdr_effectues": 1876,
    "lames_effectuees": 432,
    "tdr_positifs": 867,
    "lames_positives": 234,
    "traites": 1045,
    "moustiquaires_distribuees": 3456,
    "prevention": {
        "enfants_0_5ans": 1234,
        "femmes_enceintes": 567,
        "population_generale": 1655,
    },
    "evolution_mensuelle": [
        {"mois": "Jan", "cas": 145, "traites": 128},
        {"mois": "Fév", "cas": 132, "traites": 118},
        {"mois": "Mar", "cas": 198, "traites": 175},
        {"mois": "Avr", "cas": 267, "traites": 234},
        {"mois": "Mai", "cas": 312, "traites": 278},
        {"mois": "Juin", "cas": 289, "traites": 256},
        {"mois": "Juil", "cas": 345, "traites": 301},
        {"mois": "Août", "cas": 298, "traites": 267},
        {"mois": "Sep", "cas": 234, "traites": 210},
        {"mois": "Oct", "cas": 189, "traites": 168},
        {"mois": "Nov", "cas": 156, "traites": 140},
        {"mois": "Déc", "cas": 123, "traites": 110},
    ],
}

# --- Dashboard : Admissions summary ---
MOCK_ADMISSIONS_SUMMARY = {
    "total_admissions": 4567,
    "mortalite_infantile": 3.2,
    "mortalite_maternelle": 0.85,
}

# --- Dashboard : Top diagnostics ---
MOCK_TOP_DIAGNOSTICS = [
    {"diagnosis_code": "B54", "diagnosis": "Paludisme", "total": 583},
    {"diagnosis_code": "A09", "diagnosis": "Diarrhée et gastro-entérite", "total": 437},
    {"diagnosis_code": "A08", "diagnosis": "Infection respiratoire aiguë", "total": 434},
    {"diagnosis_code": "J18", "diagnosis": "Pneumonie", "total": 365},
    {"diagnosis_code": "N39", "diagnosis": "Infection urinaire", "total": 241},
]

MOCK_LAST_SYNC = "2025-09-26T05:00:00"

# --- Gouvernance : indicateurs de déduplication (KPI SILVER/moteur) ---
MOCK_GOVERNANCE_DUPLICATES = {
    "total_patients": 65214,
    "total_masters": 62180,
    "duplicates": 3034,
    "duplicate_rate": 4.65,
    "by_method": {"exact": 1876, "probabilistic": 1158},
}

# --- Gouvernance : consentements (purpose-by-purpose) ---
MOCK_CONSENT = [
    {"master_patient_id": "PAT-0001", "name": "RAKOTO Jean",
     "purpose": "recherche", "granted": True, "recorded_at": "2025-09-01"},
    {"master_patient_id": "PAT-0002", "name": "ANDRIANARIVO Marie",
     "purpose": "recherche", "granted": True, "recorded_at": "2025-09-03"},
    {"master_patient_id": "PAT-0003", "name": "RABE Paul",
     "purpose": "qualite", "granted": True, "recorded_at": "2025-09-05"},
    {"master_patient_id": "PAT-0004", "name": "RASOA Liva",
     "purpose": "recherche", "granted": False, "recorded_at": "2025-09-08"},
    {"master_patient_id": "PAT-0005", "name": "RAZAFY Hery",
     "purpose": "reglementation", "granted": True, "recorded_at": "2025-09-12"},
    {"master_patient_id": "PAT-0006", "name": "RAMA Vero",
     "purpose": "qualite", "granted": False, "recorded_at": "2025-09-15"},
]

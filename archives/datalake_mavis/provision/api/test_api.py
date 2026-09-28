#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_api.py — Test des endpoints Flask API (hive_api.py)
========================================================
Usage :
  cd ~/datalake-mavis
  /usr/bin/python3 -m provision.api.test_api

Lanceur automatique :
  bash provision/scripts/test_api.sh
"""

import json
import sys
import time
import requests

BASE_URL = "http://localhost:5000"
PASS = "\033[92m✅ PASS\033[0m"
FAIL = "\033[91m❌ FAIL\033[0m"
SKIP = "\033[93m⏭️  SKIP\033[0m"

results = {"pass": 0, "fail": 0, "skip": 0}

def test(name, method, path, expected_status=200, params=None):
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            r = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            r = requests.post(url, json=params, timeout=30)
        else:
            print(f"  {SKIP} {name} — méthode inconnue: {method}")
            results["skip"] += 1
            return

        ok = r.status_code == expected_status
        status = PASS if ok else FAIL

        if ok:
            data = r.json()
            success = data.get("success", None)
            has_data = "data" in data
            detail = f"success={success}, has_data={has_data}"
        else:
            detail = f"status={r.status_code} (attendu {expected_status})"

        print(f"  {status} {name} — {detail}")
        if ok:
            results["pass"] += 1
        else:
            results["fail"] += 1

    except requests.exceptions.ConnectionError:
        print(f"  {FAIL} {name} — impossible de se connecter à {url}")
        results["fail"] += 1
    except Exception as e:
        print(f"  {FAIL} {name} — {e}")
        results["fail"] += 1

# ==========================================================
print("\n" + "=" * 60)
print("  TEST API FLASK — datalake_gold.patient_events_gold")
print("=" * 60 + "\n")

# 1. Dernière synchronisation
test("GET /rma/last_sync", "GET", "/rma/last_sync")

# 2. Admissions summary (sans filtre)
test("GET /rma/admissions_summary", "GET", "/rma/admissions_summary")

# 3. Admissions summary (avec filtre)
test("GET /rma/admissions_summary?start=2025-01-01&end=2025-12-31",
     "GET", "/rma/admissions_summary",
     params={"start": "2025-01-01", "end": "2025-12-31"})

# 4. Top diagnostics
test("GET /rma/top_diagnostics?limit=5", "GET", "/rma/top_diagnostics", params={"limit": 5})

# 5. Top diagnostics (avec filtre sexe)
test("GET /rma/top_diagnostics?sex=female&limit=3",
     "GET", "/rma/top_diagnostics",
     params={"sex": "female", "limit": 3})

# 6. Diagnostics heatmap
test("GET /rma/diagnostics_heatmap", "GET", "/rma/diagnostics_heatmap")

# 7. Diagnostics heatmap (limit 3)
test("GET /rma/diagnostics_heatmap?limit=3",
     "GET", "/rma/diagnostics_heatmap",
     params={"limit": 3})

# 8. Diagnostics list (page 1)
test("GET /rma/diagnostics_list?page=1&limit=10",
     "GET", "/rma/diagnostics_list",
     params={"page": 1, "limit": 10})

# 9. Mortality
test("GET /api/rma/mortality", "GET", "/api/rma/mortality")

# 10. Maternity
test("GET /api/rma/maternity", "GET", "/api/rma/maternity")

# 11. Laboratory (non disponible, attendu 200 avec data vide)
test("GET /api/rma/laboratory", "GET", "/api/rma/laboratory")

# 12. Malaria (non disponible, attendu 200 avec data vide)
test("GET /api/rma/malaria", "GET", "/api/rma/malaria")

# ==========================================================
print("\n" + "=" * 60)
total = results["pass"] + results["fail"] + results["skip"]
print(f"  RÉSULTAT : {results['pass']}/{total} PASS — {results['fail']} FAIL — {results['skip']} SKIP")
print("=" * 60 + "\n")

sys.exit(1 if results["fail"] > 0 else 0)

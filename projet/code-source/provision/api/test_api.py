#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_api.py — Test des endpoints Flask API (hive_api.py)
=========================================================
Usage :
  cd ~/datalake-final
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
print("  TEST API FLASK — indicateurs de gouvernance")
print("=" * 60 + "\n")

# 1. Gouvernance — KPIs de déduplication (SILVER patient + moteur)
test("GET /api/governance/duplicates", "GET", "/api/governance/duplicates")

# 2. Gouvernance — consentements purpose-by-purpose (GOLD)
test("GET /api/governance/consent", "GET", "/api/governance/consent")

# 3. Gouvernance — consentements avec limite
test("GET /api/governance/consent?limit=5", "GET", "/api/governance/consent", params={"limit": 5})

# ==========================================================
print("\n" + "=" * 60)
total = results["pass"] + results["fail"] + results["skip"]
print(f"  RÉSULTAT : {results['pass']}/{total} PASS — {results['fail']} FAIL — {results['skip']} SKIP")
print("=" * 60 + "\n")

sys.exit(1 if results["fail"] > 0 else 0)
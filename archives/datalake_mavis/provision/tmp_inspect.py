#!/usr/bin/env python3
import json
with open("/home/vagrant/datalake-mavis/provision/metadata/extract_raw_report.json") as f:
    r = json.load(f)
print("TYPE:", type(r).__name__)
if isinstance(r, list):
    print("LEN:", len(r))
    if r:
        print("FIRST:", json.dumps(r[0], indent=2, default=str)[:500])
elif isinstance(r, dict):
    print("KEYS:", list(r.keys())[:10])
    for k in list(r.keys())[:2]:
        print(f"\n--- {k} ---")
        v = r[k]
        print("TYPE:", type(v).__name__)
        if isinstance(v, list):
            print("LEN:", len(v))
            if v:
                print("FIRST:", json.dumps(v[0], indent=2, default=str)[:500])
        elif isinstance(v, dict):
            print("KEYS:", list(v.keys())[:5])

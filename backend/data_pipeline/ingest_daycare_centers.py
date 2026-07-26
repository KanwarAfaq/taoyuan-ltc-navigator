"""
ingest_daycare_centers.py

Cleans the raw CSV from 桃園資料開放平台
(桃園市日間照顧、小規模多機能服務提供單位名冊) and geocodes each
address so we have lat/lng for the map view later.

Usage:
    python ingest_daycare_centers.py raw_daycare.csv cleaned_daycare.json

Notes:
- Uses OpenStreetMap's Nominatim for geocoding because it's free and
  requires no API key. Nominatim's usage policy requires max 1 request/sec
  and a descriptive User-Agent — both are respected below. If we later need
  faster/more reliable geocoding, swap this for Google Geocoding API
  (paid, but much more accurate for Taiwan addresses).
- Re-run is idempotent: already-geocoded rows (matched by address) are
  cached to geocode_cache.json so we don't re-hit Nominatim on every run.
"""

import csv
import json
import sys
import time
import os
import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "taoyuan-ltc-navigator/0.1 (contact: replace-with-your-email@example.com)"
CACHE_PATH = os.path.join(os.path.dirname(__file__), "geocode_cache.json")


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def geocode(address, cache):
    if address in cache:
        return cache[address]

    # Bias search to Taiwan by appending country context
    query = f"桃園市 {address}, Taiwan"
    resp = requests.get(
        NOMINATIM_URL,
        params={"q": query, "format": "json", "limit": 1},
        headers={"User-Agent": USER_AGENT},
        timeout=10,
    )
    resp.raise_for_status()
    results = resp.json()

    if results:
        lat, lng = float(results[0]["lat"]), float(results[0]["lon"])
    else:
        lat, lng = None, None

    cache[address] = {"lat": lat, "lng": lng}
    save_cache(cache)
    time.sleep(1.1)  # respect Nominatim's 1 req/sec limit
    return cache[address]


def clean_row(row):
    # Column names come from the raw CSV headers — adjust here if the
    # portal changes its schema in a future yearly update.
    return {
        "source_seq": row.get("序號", "").strip(),
        "district": row.get("行政區", "").strip(),
        "org_type": row.get("單位性質", "").strip(),
        "name": row.get("服務單位", "").strip(),
        "address": row.get("地址", "").strip(),
        "phone": row.get("電話", "").strip(),
        "services": row.get("服務項目", "").strip(),
        "status": row.get("服務情形", "").strip(),
    }


def main():
    if len(sys.argv) != 3:
        print("Usage: python ingest_daycare_centers.py <input.csv> <output.json>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]
    cache = load_cache()

    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = [
            clean_row(r)
            for r in reader
            if r.get("序號", "").strip().isdigit()  # drops footer/note rows like "備註：..."
        ]

    print(f"Loaded {len(rows)} facilities. Geocoding addresses...")

    skipped = []
    for i, row in enumerate(rows, 1):
        if not row["address"]:
            skipped.append(row["name"])
            row["lat"], row["lng"] = None, None
            continue
        geo = geocode(row["address"], cache)
        row["lat"], row["lng"] = geo["lat"], geo["lng"]
        print(f"  [{i}/{len(rows)}] {row['name']} -> {geo['lat']}, {geo['lng']}")

    failed = [r["name"] for r in rows if r["lat"] is None]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Wrote {len(rows)} facilities to {output_path}")
    if skipped:
        print(f"Skipped (no address): {len(skipped)} -> {skipped}")
    if failed:
        print(f"Geocoding failed (needs manual lat/lng): {len(failed)} -> {failed}")


if __name__ == "__main__":
    main()

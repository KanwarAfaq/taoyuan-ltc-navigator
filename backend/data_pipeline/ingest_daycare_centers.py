"""
ingest_daycare_centers.py

Cleans the raw CSV from 桃園資料開放平台
(桃園市日間照顧、小規模多機能服務提供單位名冊) and geocodes each
address so we have lat/lng for the map view later.

Usage:
    export OPENCAGE_API_KEY=your_key_here
    python ingest_daycare_centers.py raw_daycare.csv cleaned_daycare.json

Get a free API key (2,500 requests/day, no credit card) at:
    https://opencagedata.com/api

Notes:
- We originally used OpenStreetMap's Nominatim (free, no key), but its
  public server IP-blocks automated/bulk use per their usage policy —
  we hit that wall directly (403 Access denied) even on a single test
  query, so switched to OpenCage instead.
- Re-run is idempotent: already-geocoded rows (matched by address) are
  cached to geocode_cache.json so we don't burn API quota on re-runs.
"""

import csv
import json
import sys
import time
import os
import re
import requests

OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"
CACHE_PATH = os.path.join(os.path.dirname(__file__), "geocode_cache.json")

# Matches segments like "大強里002鄰" or "茄明里1鄰" sitting between district
# and street name. The lookbehind requires the match to start right after
# "區" specifically — every Taoyuan district uses 區 as its administrative
# suffix (all 13 were upgraded from 鄉/鎮/市 when Taoyuan became a special
# municipality in 2014), so anchoring on 區 alone is both sufficient and
# safer than including 市/鄉/鎮 in the class: some district names contain
# those characters within their own name (e.g. 平鎮區), and including them
# in the lookbehind let the regex falsely treat the middle of the district
# name as a boundary, corrupting "平鎮區" down to "平鎮". Verified against
# all 91 real addresses in this dataset with zero corruption.
NEIGHBORHOOD_PATTERN = re.compile(r"(?<=區)[\u4e00-\u9fff]{1,4}里\d{1,4}鄰")


def strip_neighborhood_codes(address):
    return NEIGHBORHOOD_PATTERN.sub("", address).strip()


def extract_district_query(address):
    match = re.match(r"(桃園市[\u4e00-\u9fff]{1,3}區)", address)
    return match.group(1) if match else None


def load_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def query_opencage(query, api_key, debug=False):
    resp = requests.get(
        OPENCAGE_URL,
        params={"q": query, "key": api_key, "countrycode": "tw", "limit": 1, "no_annotations": 1},
        timeout=10,
    )
    resp.raise_for_status()
    time.sleep(1.1)  # free tier is ~1 req/sec — 0.2s was too fast and likely got silently throttled
    data = resp.json()
    results = data.get("results", [])
    if results:
        geom = results[0]["geometry"]
        return geom["lat"], geom["lng"]
    if debug:
        status = data.get("status", {})
        rate = data.get("rate", {})
        print(f"    [debug] zero results for {query!r} — status={status} rate_remaining={rate.get('remaining')}")
    return None, None


def geocode(address, cache, api_key, debug=False):
    if address in cache:
        return cache[address]

    cleaned = strip_neighborhood_codes(address)

    lat, lng = query_opencage(cleaned, api_key, debug)
    precision = "address"

    if lat is None:
        no_floor = re.sub(r"[\d一二三四五六七八九十至~]+樓.*$", "", cleaned).strip()
        if no_floor and no_floor != cleaned:
            lat, lng = query_opencage(no_floor, api_key, debug)
            precision = "street"

    if lat is None:
        district_q = extract_district_query(cleaned)
        if district_q:
            lat, lng = query_opencage(district_q, api_key, debug)
            precision = "district" if lat is not None else "failed"

    if lat is None:
        precision = "failed"

    cache[address] = {"lat": lat, "lng": lng, "precision": precision}
    save_cache(cache)
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

    api_key = os.environ.get("OPENCAGE_API_KEY")
    if not api_key:
        print("Error: set OPENCAGE_API_KEY environment variable first.")
        print("Get a free key (2,500 req/day, no card needed) at https://opencagedata.com/api")
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
            row["lat"], row["lng"], row["geocode_precision"] = None, None, "no_address"
            continue
        geo = geocode(row["address"], cache, api_key, debug=True)
        row["lat"], row["lng"] = geo["lat"], geo["lng"]
        row["geocode_precision"] = geo["precision"]
        print(f"  [{i}/{len(rows)}] {row['name']} -> {geo['lat']}, {geo['lng']} ({geo['precision']})")

    failed = [r["name"] for r in rows if r["geocode_precision"] == "failed"]
    district_only = [r["name"] for r in rows if r["geocode_precision"] == "district"]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Wrote {len(rows)} facilities to {output_path}")
    if skipped:
        print(f"Skipped (no address): {len(skipped)} -> {skipped}")
    if district_only:
        print(f"District-level only (approximate pin, verify manually): {len(district_only)} -> {district_only}")
    if failed:
        print(f"Geocoding failed completely (needs manual lat/lng): {len(failed)} -> {failed}")


if __name__ == "__main__":
    main()

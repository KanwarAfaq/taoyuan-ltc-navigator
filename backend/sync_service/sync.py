"""
sync.py — fetches the latest Taoyuan day care facility roster via headless
browser (the source portal is JS-rendered with no stable API — see
README for why), diffs it against what's already in Supabase, and upserts
only what changed. Never touches vacancy_status/vacancy_updated_at, which
belong to the admin panel.

I could not test the Playwright browser-automation step against the real
site (no browser + network-blocked domain in my environment) — this needs
to be verified by actually running it. If the download click fails, the
most likely fix is adjusting the text selector below to match whatever the
button's actual visible text is (inspect via browser devtools).
"""

import csv
import io
import os
import re
import time
from datetime import datetime, timezone

import requests
from playwright.async_api import async_playwright

from supabase_client import supabase

SOURCE_URL = "https://opendata.tycg.gov.tw/datalist/7e076556-a8f1-4449-b4de-4389954a25da"
OPENCAGE_URL = "https://api.opencagedata.com/geocode/v1/json"

NEIGHBORHOOD_PATTERN = re.compile(r"(?<=區)[\u4e00-\u9fff]{1,4}里\d{1,4}鄰")


def strip_neighborhood_codes(address):
    return NEIGHBORHOOD_PATTERN.sub("", address).strip()


def extract_district_query(address):
    match = re.match(r"(桃園市[\u4e00-\u9fff]{1,3}區)", address)
    return match.group(1) if match else None


def query_opencage(query, api_key):
    resp = requests.get(
        OPENCAGE_URL,
        params={"q": query, "key": api_key, "countrycode": "tw", "limit": 1, "no_annotations": 1},
        timeout=10,
    )
    resp.raise_for_status()
    time.sleep(1.1)
    results = resp.json().get("results", [])
    if results:
        geom = results[0]["geometry"]
        return geom["lat"], geom["lng"]
    return None, None


def geocode(address, api_key):
    cleaned = strip_neighborhood_codes(address)
    lat, lng = query_opencage(cleaned, api_key)
    precision = "address"

    if lat is None:
        no_floor = re.sub(r"[\d一二三四五六七八九十至~]+樓.*$", "", cleaned).strip()
        if no_floor and no_floor != cleaned:
            lat, lng = query_opencage(no_floor, api_key)
            precision = "street"

    if lat is None:
        district_q = extract_district_query(cleaned)
        if district_q:
            lat, lng = query_opencage(district_q, api_key)
            precision = "district" if lat is not None else "failed"

    if lat is None:
        precision = "failed"

    return lat, lng, precision


async def fetch_csv_via_browser() -> bytes:
    """
    Uses a headless browser to load the JS-rendered portal and click the
    CSV download button, capturing the downloaded file bytes. Matches the
    button by visible text rather than CSS selector/class, since text is
    far less likely to change across the portal's own updates.

    Uses Playwright's ASYNC API specifically (not sync) so this runs on
    FastAPI's own event loop on the main thread. The sync API launches a
    subprocess to talk to the browser driver, which only works reliably
    from the main thread + Proactor event loop on Windows -- FastAPI runs
    plain `def` endpoints in a worker thread, which breaks that and raises
    a bare NotImplementedError. The async API sidesteps this entirely.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(SOURCE_URL, wait_until="networkidle", timeout=30000)

        async with page.expect_download(timeout=30000) as download_info:
            # Adjust this text if the button's actual label differs --
            # inspect the live page in a real browser if this fails.
            await page.click("text=下載CSV")
        download = await download_info.value

        path = await download.path()
        with open(path, "rb") as f:
            data = f.read()

        await browser.close()
        return data


def parse_csv(raw_bytes: bytes):
    text = raw_bytes.decode("big5")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for r in reader:
        if not r.get("序號", "").strip().isdigit():
            continue  # drops footer/note rows
        rows.append({
            "source_seq": r.get("序號", "").strip(),
            "district": r.get("行政區", "").strip(),
            "org_type": r.get("單位性質", "").strip(),
            "name": r.get("服務單位", "").strip(),
            "address": r.get("地址", "").strip(),
            "phone": r.get("電話", "").strip(),
            "services": r.get("服務項目", "").strip(),
            "status": r.get("服務情形", "").strip(),
        })
    return rows


async def run_sync(opencage_api_key: str) -> dict:
    raw = await fetch_csv_via_browser()
    fresh_rows = parse_csv(raw)
    fresh_by_name = {r["name"]: r for r in fresh_rows}

    existing = supabase.table("facilities").select("*").execute().data
    existing_by_name = {r["name"]: r for r in existing}

    added, updated, unchanged, geocoded = 0, 0, 0, 0
    now = datetime.now(timezone.utc).isoformat()

    for name, fresh in fresh_by_name.items():
        existing_row = existing_by_name.get(name)

        if existing_row is None:
            # Brand new facility -- geocode it
            lat, lng, precision = geocode(fresh["address"], opencage_api_key)
            geocoded += 1
            supabase.table("facilities").insert({
                **fresh,
                "lat": lat, "lng": lng, "geocode_precision": precision,
                "source_still_listed": True, "last_synced_at": now,
            }).execute()
            added += 1
            continue

        address_changed = existing_row["address"] != fresh["address"]
        other_changed = any(existing_row.get(k) != fresh.get(k) for k in
                             ("district", "org_type", "phone", "services", "status"))

        if not address_changed and not other_changed:
            # Nothing changed -- just bump last_synced_at and re-list flag
            supabase.table("facilities").update({
                "source_still_listed": True, "last_synced_at": now,
            }).eq("id", existing_row["id"]).execute()
            unchanged += 1
            continue

        update_payload = {**fresh, "source_still_listed": True, "last_synced_at": now}
        if address_changed:
            lat, lng, precision = geocode(fresh["address"], opencage_api_key)
            geocoded += 1
            update_payload.update({"lat": lat, "lng": lng, "geocode_precision": precision})

        supabase.table("facilities").update(update_payload).eq("id", existing_row["id"]).execute()
        updated += 1

    # Anything in the DB that's no longer in the fresh fetch -- flag, don't delete
    removed = 0
    for name, existing_row in existing_by_name.items():
        if name not in fresh_by_name and existing_row.get("source_still_listed", True):
            supabase.table("facilities").update({
                "source_still_listed": False, "last_synced_at": now,
            }).eq("id", existing_row["id"]).execute()
            removed += 1

    return {
        "total_in_source": len(fresh_rows),
        "added": added,
        "updated": updated,
        "unchanged": unchanged,
        "flagged_removed": removed,
        "geocode_calls_used": geocoded,
        "synced_at": now,
    }

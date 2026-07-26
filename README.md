# 桃園長照導航 (Taoyuan LTC Navigator)

長照補助試算 + 日照中心媒合平台。Project #1 of the 4-project roadmap.

## Status

- [x] Week 1, Day 1 — Subsidy calculator wizard (frontend only, no backend yet)
- [x] Week 1, Day 2 — Facility data pipeline: raw CSV cleaned (91 facilities, 12 districts). Geocoding pending (see note below).
- [ ] Week 1, Day 3-5 — Geocode + Supabase import + FastAPI backend
- [ ] Week 2 — LINE Bot + matching endpoint + admin panel
- [ ] Week 3 — Reviews, map view, launch

## Stack

- **Frontend:** React 19 + Vite + Tailwind CSS v4
- **Backend (not yet built):** Python FastAPI + SQLModel + PostgreSQL (Supabase)
- **Auth (not yet built):** Supabase Auth / LINE Login
- **Deploy target:** Frontend → Vercel, Backend → Zeabur or Fly.io (Taipei region)

## What's built so far

`/frontend` — a 3-step wizard that estimates the monthly long-term care (長照 2.0/3.0)
subsidy quota based on:
1. Applicant identity (65+ elderly / 55+ Aboriginal / disability certificate holder)
2. CMS 需要等級 (2–8)
3. Household income category (一般戶 / 中低收入戶 / 低收入戶)

The subsidy math lives in `frontend/src/data/subsidyRules.js` as a config object,
not hardcoded into components — this matters because Taiwan is currently
phasing in 長照3.0, so these numbers will need updating. Check
`RULES_LAST_VERIFIED` in that file and re-verify against 1966.gov.tw before
relying on it for anything real.

**Important caveat baked into the UI on purpose:** the tool is explicit that
this is an estimate, not an official determination — actual CMS level is set
by a government care manager (照顧管理專員) after an in-home assessment. This
isn't just a legal-safety thing; giving families a confident-looking wrong
number is worse than not having the tool at all.

## Facility data pipeline (`backend/data_pipeline`)

**Data source:** [桃園市日間照顧、小規模多機能服務提供單位名冊](https://opendata.tycg.gov.tw/datalist/7e076556-a8f1-4449-b4de-4389954a25da)
— official Taoyuan City open data, maintained by 社會局, updated yearly
(last updated 2026-05-29 as of this writing). This is a live, city-specific
dataset, not the national PDF roster — better than the original roadmap
assumed.

**Usage:**
1. Download the CSV from the link above (click "下載CSV") — ⚠️ **it's Big5-encoded**, not UTF-8, which is normal for Taiwan government exports but will show as garbled text/mojibake if opened assuming UTF-8. Convert it first (see `raw_daycare.csv` in this folder, already converted) or the script will error.
2. `cd backend/data_pipeline && pip install -r requirements.txt`
3. `python ingest_daycare_centers.py raw_daycare.csv cleaned_daycare.json`
   (geocodes each address via OpenStreetMap Nominatim, ~1 sec/row —
   ~91 rows takes about 2 minutes)
4. Run `schema.sql` in the Supabase SQL Editor to create the `facilities` table
5. Import `cleaned_daycare.json` into that table (Supabase Table Editor →
   Insert → Import data from JSON, or a short Python script using the
   `supabase-py` client — we'll add that once the backend exists)

**Already done:** `raw_daycare.csv` (converted to UTF-8) and
`cleaned_daycare_no_geocode.json` (91 facilities, parsed and validated,
footer/note rows stripped) are already in this folder. **Geocoding is the
one step you need to run yourself** — Nominatim isn't reachable from
Claude's sandboxed environment, so run step 3 above locally to add lat/lng
to each row before importing to Supabase.

**Data snapshot (91 facilities across 12 districts):** 桃園21・中壢19・八德8・
楊梅7・平鎮6・龜山6・蘆竹6・大園5・龍潭5・大溪4・新屋2・觀音2. 86 currently
active (服務中), 5 not yet under contract (尚未特約) — worth deciding whether
to show those or filter them out in the matching UI.

**Known limitation:** Nominatim's free geocoder is decent for major roads
but sometimes fails on rural or newly-built addresses. The script logs any
rows it couldn't geocode so we can fix those by hand.

## Not yet built

- Facility data (day care centers, Taoyuan) — needs a real ingestion job,
  see "Next steps" below
- Supabase project / database schema
- FastAPI backend and `/match` endpoint
- LINE Login / LINE Bot
- Admin panel for care centers to update vacancy

## Next steps

1. Get this frontend running locally and pushed to GitHub (see root-level
   setup instructions from Claude in this conversation)
2. Confirm whether Taoyuan City publishes its own open-data JSON for day
   care centers (vs. relying on the national PDF roster) — Claude will
   check this in the next session
3. Stand up Supabase project, design `facilities` table
4. Build FastAPI `/match` endpoint

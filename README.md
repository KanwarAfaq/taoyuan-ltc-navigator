# 桃園長照導航 (Taoyuan LTC Navigator)

長照補助試算 + 日照中心媒合平台。Project #1 of the 4-project roadmap.

## Status

- [x] Week 1, Day 1 — Subsidy calculator wizard (frontend)
- [x] Week 1, Day 2 — Facility data pipeline: 91 facilities cleaned, geocoded, imported to Supabase
- [x] Week 1, Day 3-4 — FastAPI backend (`/match`, `/facilities/{id}`), verified against real Supabase data
- [x] Week 1, Day 5 — Frontend connected to backend: 4th wizard step (district picker) shows matched facilities
- [ ] Deploy (Vercel + Zeabur/Fly.io)
- [ ] Week 2 — LINE Bot + admin panel
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

## Backend API (`backend/app`)

FastAPI + the official `supabase-py` client, talking to Supabase over its
REST API (HTTPS, port 443) rather than a raw Postgres connection.

**Why this instead of a direct Postgres connection:** we originally built
this with SQLModel + a direct `postgresql://` connection string, but hit a
wall of environment-specific problems on Windows — Python 3.14/3.15
compatibility issues with SQLModel's Pydantic internals, `psycopg2` needing
a C compiler toolchain, and finally Supabase's direct-connection hostname
being IPv6-only (unroutable on most home networks). Switching to the
Supabase URL + anon key over HTTPS sidesteps all of that: it's just a web
request, which works everywhere, and dropping the ORM layer also
eliminates the SQLModel/Pydantic version-compatibility problems entirely.
The tradeoff: slightly less query flexibility (no arbitrary SQL), which is
fine for a matching endpoint like this — precision-based sorting is just
done in Python after fetching, which is trivial at ~100 rows.

**Endpoints:**
- `GET /health` — sanity check
- `GET /match?district=桃園&only_active=true&limit=50&offset=0` — main matching
  endpoint. Filters by district (exact match, e.g. `桃園`, `中壢`, `八德`) and
  active status (excludes `尚未特約` by default). Results are ordered by
  geocode precision — exact address matches first, then street-level, then
  district-level approximations last — so the most trustworthy pins surface
  first in the UI.
- `GET /facilities/{id}` — single facility detail, 404s if not found

**Setup:**
```bash
cd backend/app
pip install -r requirements.txt
cp .env.example .env
# Edit .env: Supabase dashboard -> Project Settings -> API
#   SUPABASE_URL = Project URL
#   SUPABASE_KEY = anon public key (safe to use here -- facilities table
#   only allows public SELECT via RLS, see schema.sql)
uvicorn main:app --reload --app-dir .
```
Then open http://127.0.0.1:8000/docs for interactive API docs.

**Verified:** app boots cleanly, `/health` responds, and `/match` fails
gracefully (clean 502, not a crash) when Supabase is unreachable -- tested
against a fake project since I don't have your real credentials. Not yet
tested against your actual Supabase data -- that's the next step.

## Frontend ↔ backend integration

The wizard now has a 4th step: after picking household type, the person
picks their district (行政區 dropdown), then sees the subsidy result
alongside real day care facilities in that district, pulled live from the
FastAPI `/match` endpoint.

**Config:** `frontend/.env.example` — copy to `.env`, set
`VITE_API_BASE_URL` (defaults to `http://127.0.0.1:8000`, matches local
`uvicorn` dev server). Update this once the backend is deployed somewhere.

**Error handling:** if the backend isn't reachable (e.g. you forgot to
start `uvicorn`), the UI shows a clear Chinese-language message rather
than a blank screen or console-only error — this matters since the
target audience isn't going to open dev tools to debug a fetch failure.

**Data honesty:** facilities with `district`-level (approximate) geocode
precision get a small caveat note in the UI (⚠ 約略位置...) rather than
being presented with the same confidence as exact-address matches — this
follows the same principle as the subsidy calculator's disclaimer: don't
show a confident-looking wrong answer.

**Not yet tested:** I verified the build compiles cleanly and the fetch
logic is correct, but I have not run this against your live backend +
Supabase end-to-end (I don't have a way to run your local `uvicorn`
server from here). That's the next verification step — see "What to do"
below.

## Auto-sync service (`backend/sync_service`)

A separate, small service whose only job is to periodically refresh
facility data from the government source and push changes into Supabase.
Deployed separately from the main API so a heavy dependency (headless
Chromium) doesn't slow down or bloat the service that needs to stay fast
for the LINE bot.

**Why headless browser instead of a simple HTTP request:** the source
portal (opendata.tycg.gov.tw) is JavaScript-rendered with no stable,
directly-fetchable API endpoint we could find — even the linked Swagger
docs URL is blocked by robots.txt. So this uses Playwright to actually
render the page and click the download button, matched by its visible
text ("下載CSV") rather than a CSS selector, since text survives page
redesigns better.

**⚠️ Not yet verified against the live site** — I can't run a browser or
reach that domain from my environment. Everything except the actual
browser-click-and-download step has been tested (CSV parsing against real
data, the add/update/unchanged diff logic, the auth-protected endpoint).
The browser step needs to be confirmed by actually running it. If the
click fails, inspect the live page in a real browser and check whether
the button's visible text still says exactly "下載CSV" — update the
`page.click("text=...")` line in `sync.py` if not.

**What it does on each sync:**
1. Downloads the current CSV via headless browser
2. Diffs every row against what's in Supabase (matched by facility name)
3. New facilities → geocoded (via OpenCage) and inserted
4. Changed facilities → updated; only re-geocoded if the *address* changed
   (saves API quota — a phone number update doesn't need a new geocode)
5. Unchanged facilities → just touched with a `last_synced_at` timestamp
6. Facilities that disappeared from the source → flagged
   `source_still_listed = false`, never hard-deleted (preserves any
   vacancy data tied to them)

**Setup:**
```bash
cd backend/sync_service
pip install -r requirements.txt
playwright install --with-deps chromium
cp .env.example .env
# Fill in: SUPABASE_URL, SUPABASE_KEY (service_role key, NOT anon --
# this service writes to the DB), OPENCAGE_API_KEY, SYNC_SECRET_TOKEN
# (make up a long random string yourself)
python -m uvicorn main:app --reload --app-dir .
```
Test locally first: `http://127.0.0.1:8000/sync?token=<your-token>`

**Deploy on Render** (as its own Web Service, separate from the main API):
- Root Directory: `backend/sync_service`
- Build Command: `pip install -r requirements.txt && playwright install --with-deps chromium`
- Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment Variables: same four as `.env` above
- Note: headless Chromium needs more memory than Render's free tier
  comfortably offers — this may need the paid tier if the free tier OOMs
  during the build or at runtime

**Schedule it:** [cron-job.org](https://cron-job.org) (free) → create a
job pinging `https://<your-render-url>/sync?token=<your-secret>` monthly
(matches how infrequently the source data itself actually updates).

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

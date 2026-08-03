import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and/or SUPABASE_KEY not set. Copy .env.example to "
        ".env and fill in your values from Supabase: Project Settings -> API."
    )

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Separate privileged client for the small number of endpoints that need
# to write (e.g. the facility vacancy self-update feature) -- the anon
# key above is read-only per our RLS policy, on purpose. This is optional
# because most of the app (reads, LINE bot, sync trigger auth) doesn't
# need it; endpoints that do check for it explicitly and fail clearly if
# it's missing, rather than the whole app refusing to start.
supabase_admin: Client = (
    create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else None
)

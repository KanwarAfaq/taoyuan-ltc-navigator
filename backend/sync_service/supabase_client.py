import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and/or SUPABASE_KEY not set. Copy .env.example to .env.")

# NOTE: this service writes to the database (insert/update), so it needs
# the "service_role" key, NOT the anon key used by the read-only main API.
# Get it from Supabase: Project Settings -> API -> service_role secret.
# NEVER expose this key to a frontend or commit it to git.
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

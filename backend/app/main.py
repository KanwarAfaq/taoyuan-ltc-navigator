from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from supabase_client import supabase
from models import Facility
from facilities_service import search_facilities
from line_bot import router as line_router
from admin_router import router as admin_router

import os

app = FastAPI(
    title="Taoyuan LTC Navigator API",
    description="桃園長照導航 — day care facility matching API",
    version="0.1.0",
)

# Vite's default dev port, plus any origins from the ALLOWED_ORIGINS env var
# (comma-separated) — set this in Vercel's Environment Variables to your
# deployed frontend URL once you have it, no code change needed.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
] + [origin.strip() for origin in os.environ.get("ALLOWED_ORIGINS", "").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["*"],
)

app.include_router(line_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/match", response_model=List[Facility])
def match_facilities(
    district: Optional[str] = Query(
        None, description="行政區, e.g. 桃園, 中壢, 八德 (exact match)"
    ),
    only_active: bool = Query(
        True, description="If true (default), only return 服務中 facilities — excludes 尚未特約"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    Core matching endpoint. Filters by district and active status, returns
    results ordered by geocode precision (exact address matches first, then
    street-level, then district-level approximations last) so the most
    trustworthy pins surface first.
    """
    try:
        return search_facilities(district=district, only_active=only_active, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase query failed: {e}")


@app.get("/facilities/{facility_id}", response_model=Facility)
def get_facility(facility_id: int):
    try:
        response = (
            supabase.table("facilities").select("*").eq("id", facility_id).execute()
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Supabase query failed: {e}")

    if not response.data:
        raise HTTPException(status_code=404, detail="Facility not found")
    return response.data[0]

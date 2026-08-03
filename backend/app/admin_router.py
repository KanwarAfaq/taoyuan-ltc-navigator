from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from supabase_client import supabase, supabase_admin

router = APIRouter()

VALID_VACANCY_STATUSES = {"available", "full", "unknown"}


class FacilityAdminView(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    vacancy_status: str
    vacancy_updated_at: Optional[datetime] = None


class VacancyUpdateRequest(BaseModel):
    vacancy_status: str


def _find_by_token(token: str) -> dict:
    result = supabase.table("facilities").select("*").eq("edit_token", token).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Invalid or unknown link")
    return result.data[0]


@router.get("/facilities/by-token/{token}", response_model=FacilityAdminView)
def get_facility_by_token(token: str):
    return _find_by_token(token)


@router.patch("/facilities/by-token/{token}", response_model=FacilityAdminView)
def update_vacancy_by_token(token: str, body: VacancyUpdateRequest):
    if body.vacancy_status not in VALID_VACANCY_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"vacancy_status must be one of {sorted(VALID_VACANCY_STATUSES)}",
        )
    if supabase_admin is None:
        raise HTTPException(
            status_code=500,
            detail="Server misconfigured: SUPABASE_SERVICE_KEY not set (needed for writes)",
        )

    # Confirms the token is real before attempting the write, so an
    # invalid link gives a clean 404 rather than a silent no-op update.
    _find_by_token(token)

    now = datetime.now(timezone.utc).isoformat()
    result = (
        supabase_admin.table("facilities")
        .update({"vacancy_status": body.vacancy_status, "vacancy_updated_at": now})
        .eq("edit_token", token)
        .execute()
    )
    return result.data[0]

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class Facility(BaseModel):
    id: int
    source_seq: Optional[str] = None
    district: str
    org_type: Optional[str] = None
    name: str
    address: str
    phone: Optional[str] = None
    services: Optional[str] = None
    status: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    geocode_precision: Optional[str] = None
    vacancy_status: str = "unknown"
    vacancy_updated_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

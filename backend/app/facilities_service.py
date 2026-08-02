from supabase_client import supabase

# Lower number = higher precision = shown first
PRECISION_RANK = {"address": 0, "street": 1, "district": 2}


def _precision_sort_key(facility: dict):
    return (PRECISION_RANK.get(facility.get("geocode_precision"), 3), facility.get("name") or "")


def search_facilities(district: str = None, only_active: bool = True, limit: int = 50, offset: int = 0):
    query = supabase.table("facilities").select("*")

    if district:
        query = query.eq("district", district)
    if only_active:
        query = query.eq("status", "服務中")

    response = query.execute()
    rows = sorted(response.data, key=_precision_sort_key)
    return rows[offset : offset + limit]

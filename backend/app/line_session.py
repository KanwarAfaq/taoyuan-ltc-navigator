from supabase_client import supabase


def get_session(line_user_id: str) -> dict:
    result = supabase.table("line_sessions").select("state").eq("line_user_id", line_user_id).execute()
    if result.data:
        return result.data[0]["state"]
    return {}


def set_session(line_user_id: str, state: dict):
    supabase.table("line_sessions").upsert({
        "line_user_id": line_user_id,
        "state": state,
    }).execute()


def clear_session(line_user_id: str):
    set_session(line_user_id, {})

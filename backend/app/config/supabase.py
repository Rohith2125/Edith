from supabase import create_client, Client
from app.config.settings import SUPABASE_URL, SUPABASE_KEY

def get_supabase() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL or SUPABASE_KEY is not set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

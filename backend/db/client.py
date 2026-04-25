from functools import lru_cache

from supabase import create_client, Client

from app.config import get_settings


@lru_cache(maxsize=1)
def get_client() -> Client:
    """Return a cached Supabase client (service-role key for server-side ops)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_key)

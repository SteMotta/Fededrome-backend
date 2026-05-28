from supabase import create_client, Client
from app.core.config import settings


def get_service_client() -> Client:
    """Client Supabase con service role key — bypassa RLS, usare solo lato server."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
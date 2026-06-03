from supabase import create_client, Client
from app.core.config import settings

# Singletons initialized once on module load
supabase_anon: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
supabase_service: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


def get_service_client() -> Client:
    """Client Supabase con service role key — bypassa RLS, usare solo lato server."""
    return supabase_service
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from app.services.supabase_client import supabase_anon

security = HTTPBearer()


def get_auth_client() -> Client:
    return supabase_anon


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials
    supabase = get_auth_client()
    try:
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(status_code=401, detail="Token non valido")
        return res.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
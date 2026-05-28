from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.schemas.user import ProfileUpdate
from app.services.supabase_client import get_service_client

router = APIRouter(prefix="/users", tags=["Users & Profiles"])


@router.get("/me")
async def get_my_profile(user=Depends(get_current_user)):
    """Ritorna il profilo completo dell'utente autenticato (con contatori)."""
    db = get_service_client()
    res = db.table("profiles").select("*").eq("id", user.id).single().execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Profilo non trovato")

    uid = user.id
    films = db.table("movie_logs").select("id", count="exact").eq("user_id", uid).execute()
    foll = db.table("followers").select("follower_id", count="exact").eq("following_id", uid).execute()
    fing = db.table("followers").select("following_id", count="exact").eq("follower_id", uid).execute()

    return {
        **res.data,
        "films_count": films.count or 0,
        "followers_count": foll.count or 0,
        "following_count": fing.count or 0,
    }


@router.put("/me")
async def update_my_profile(data: ProfileUpdate, user=Depends(get_current_user)):
    """Aggiorna il profilo dell'utente autenticato."""
    db = get_service_client()
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")

    if "username" in updates:
        existing = (
            db.table("profiles")
            .select("id")
            .eq("username", updates["username"])
            .execute()
        )
        if existing.data and existing.data[0]["id"] != user.id:
            raise HTTPException(status_code=409, detail="Username già in uso")

    res = db.table("profiles").update(updates).eq("id", user.id).execute()
    return res.data[0]


@router.get("/{username}")
async def get_public_profile(username: str):
    """Ritorna il profilo pubblico di un utente (con contatori)."""
    db = get_service_client()
    profile = (
        db.table("profiles")
        .select("id, username, bio, avatar_url, created_at")
        .eq("username", username)
        .single()
        .execute()
    )
    if not profile.data:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    uid = profile.data["id"]
    films = db.table("movie_logs").select("id", count="exact").eq("user_id", uid).execute()
    foll = db.table("followers").select("follower_id", count="exact").eq("following_id", uid).execute()
    fing = db.table("followers").select("following_id", count="exact").eq("follower_id", uid).execute()

    return {
        **profile.data,
        "films_count": films.count or 0,
        "followers_count": foll.count or 0,
        "following_count": fing.count or 0,
    }


@router.get("/{username}/logs")
async def get_user_logs(username: str, page: int = 1, page_size: int = 20):
    """Ritorna i log pubblici di un utente specifico."""
    db = get_service_client()
    profile = (
        db.table("profiles").select("id").eq("username", username).single().execute()
    )
    if not profile.data:
        raise HTTPException(status_code=404, detail="Utente non trovato")

    offset = (page - 1) * page_size
    res = (
        db.table("movie_logs")
        .select("*", count="exact")
        .eq("user_id", profile.data["id"])
        .order("watched_date", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )
    return {"results": res.data, "count": res.count, "page": page}
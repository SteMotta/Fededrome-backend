from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.supabase_client import get_service_client

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


class WatchlistAdd(BaseModel):
    tmdb_id: int


@router.get("/")
async def get_watchlist(user=Depends(get_current_user)):
    """Ritorna la watchlist dell'utente."""
    db = get_service_client()
    res = (
        db.table("watchlist")
        .select("*")
        .eq("user_id", user.id)
        .order("added_at", desc=True)
        .execute()
    )
    return res.data


@router.post("/", status_code=201)
async def add_to_watchlist(item: WatchlistAdd, user=Depends(get_current_user)):
    """Aggiunge un film alla watchlist."""
    db = get_service_client()
    try:
        res = (
            db.table("watchlist")
            .insert({"user_id": user.id, "tmdb_id": item.tmdb_id})
            .execute()
        )
        return res.data[0]
    except Exception:
        raise HTTPException(status_code=409, detail="Film già presente in watchlist")


@router.delete("/{tmdb_id}", status_code=204)
async def remove_from_watchlist(tmdb_id: int, user=Depends(get_current_user)):
    """Rimuove un film dalla watchlist."""
    db = get_service_client()
    db.table("watchlist").delete().eq("user_id", user.id).eq(
        "tmdb_id", tmdb_id
    ).execute()
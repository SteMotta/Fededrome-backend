from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from app.core.security import get_current_user
from app.schemas.movie import MovieLogCreate, MovieLogUpdate
from app.services.supabase_client import get_service_client
from app.services.tmdb_client import fetch_from_tmdb
from app.services.cache import get_or_set_cache
from datetime import date

router = APIRouter(prefix="/movies", tags=["Movies & Diary"])


@router.post("/log", status_code=201)
async def log_movie(log_data: MovieLogCreate, user=Depends(get_current_user)):
    """Aggiunge un film al diario dell'utente."""
    db = get_service_client()

    # Recupera snapshot generi e runtime da TMDB (con cache)
    genres_snapshot = []
    runtime_minutes = None
    try:
        movie = await get_or_set_cache(
            f"tmdb:movie:{log_data.tmdb_id}",
            lambda: fetch_from_tmdb(f"/movie/{log_data.tmdb_id}"),
        )
        genres_snapshot = movie.get("genres", [])
        runtime_minutes = movie.get("runtime")
    except Exception:
        pass

    res = (
        db.table("movie_logs")
        .insert(
            {
                "user_id": user.id,
                "tmdb_id": log_data.tmdb_id,
                "watched_date": str(log_data.watched_date),
                "rating": log_data.rating,
                "review": log_data.review,
                "liked": log_data.liked,
                "genres_snapshot": genres_snapshot,
                "runtime_minutes": runtime_minutes,
            }
        )
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=500, detail="Errore inserimento DB")
    return res.data[0]


@router.get("/diary")
async def get_diary(
    page: int = 1,
    page_size: int = 20,
    year: Optional[int] = None,
    user=Depends(get_current_user),
):
    """Ritorna il diario paginato dell'utente, arricchito con dati TMDB."""
    db = get_service_client()

    query = (
        db.table("movie_logs").select("*", count="exact").eq("user_id", user.id)
    )
    if year:
        query = query.gte("watched_date", f"{year}-01-01").lte(
            "watched_date", f"{year}-12-31"
        )

    offset = (page - 1) * page_size
    res = (
        query.order("watched_date", desc=True)
        .range(offset, offset + page_size - 1)
        .execute()
    )

    enriched = []
    for log in res.data:
        try:
            movie = await get_or_set_cache(
                f"tmdb:movie:{log['tmdb_id']}",
                lambda tmdb_id=log["tmdb_id"]: fetch_from_tmdb(f"/movie/{tmdb_id}"),
            )
            log["title"] = movie.get("title")
            log["poster_path"] = movie.get("poster_path")
            log["year"] = movie.get("release_date", "")[:4]
        except Exception:
            pass
        enriched.append(log)

    return {"results": enriched, "count": res.count, "page": page}


@router.put("/log/{log_id}")
async def update_log(
    log_id: str, data: MovieLogUpdate, user=Depends(get_current_user)
):
    """Modifica un log esistente dell'utente."""
    db = get_service_client()
    existing = (
        db.table("movie_logs").select("user_id").eq("id", log_id).execute()
    )
    if not existing.data or existing.data[0]["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    updates = {
        k: str(v) if isinstance(v, date) else v
        for k, v in data.model_dump().items()
        if v is not None
    }
    if not updates:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")

    res = db.table("movie_logs").update(updates).eq("id", log_id).execute()
    return res.data[0]


@router.delete("/log/{log_id}", status_code=204)
async def delete_log(log_id: str, user=Depends(get_current_user)):
    """Elimina un log dal diario dell'utente."""
    db = get_service_client()
    log = db.table("movie_logs").select("user_id").eq("id", log_id).execute()
    if not log.data or log.data[0]["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    db.table("movie_logs").delete().eq("id", log_id).execute()


@router.get("/log/{tmdb_id}")
async def get_log_for_movie(tmdb_id: int, user=Depends(get_current_user)):
    """Controlla se l'utente ha già loggato un determinato film e ne restituisce i dettagli."""
    db = get_service_client()
    res = (
        db.table("movie_logs")
        .select("*")
        .eq("user_id", user.id)
        .eq("tmdb_id", tmdb_id)
        .execute()
    )
    if res.data:
        return res.data[0]
    return None

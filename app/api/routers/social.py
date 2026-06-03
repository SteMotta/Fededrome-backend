from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.security import get_current_user
from app.services.supabase_client import get_service_client
from app.services.cache import get_or_set_cache
from app.services.tmdb_client import fetch_from_tmdb

router = APIRouter(prefix="/social", tags=["Social"])


class FollowRequest(BaseModel):
    target_user_id: str


@router.post("/follow", status_code=201)
async def follow_user(req: FollowRequest, user=Depends(get_current_user)):
    """Segui un utente."""
    if req.target_user_id == user.id:
        raise HTTPException(status_code=400, detail="Non puoi seguire te stesso")
    db = get_service_client()
    try:
        db.table("followers").insert(
            {"follower_id": user.id, "following_id": req.target_user_id}
        ).execute()
    except Exception:
        raise HTTPException(status_code=409, detail="Stai già seguendo questo utente")
    return {"status": "success"}


@router.delete("/follow/{target_user_id}", status_code=204)
async def unfollow_user(target_user_id: str, user=Depends(get_current_user)):
    """Smetti di seguire un utente."""
    db = get_service_client()
    db.table("followers").delete().eq("follower_id", user.id).eq(
        "following_id", target_user_id
    ).execute()


@router.get("/is-following/{target_user_id}")
async def check_is_following(target_user_id: str, user=Depends(get_current_user)):
    """Verifica se l'utente corrente segue l'utente target."""
    db = get_service_client()
    res = (
        db.table("followers")
        .select("follower_id")
        .eq("follower_id", user.id)
        .eq("following_id", target_user_id)
        .execute()
    )
    return {"is_following": len(res.data) > 0}


@router.get("/feed")
async def get_social_feed(page: int = 1, user=Depends(get_current_user)):
    """Ritorna il feed degli utenti seguiti, con dati TMDB arricchiti."""
    db = get_service_client()
    import asyncio
    
    follows_res = (
        db.table("followers")
        .select("following_id")
        .eq("follower_id", user.id)
        .execute()
    )
    followed_ids = [f["following_id"] for f in follows_res.data]

    if not followed_ids:
        return {"results": [], "count": 0}

    offset = (page - 1) * 20
    feed_res = (
        db.table("movie_logs")
        .select("*, profiles:user_id(username, avatar_url)", count="exact")
        .in_("user_id", followed_ids)
        .order("created_at", desc=True)
        .range(offset, offset + 19)
        .execute()
    )

    async def enrich_log(log):
        try:
            movie = await get_or_set_cache(
                f"tmdb:movie:{log['tmdb_id']}",
                lambda tmdb_id=log["tmdb_id"]: fetch_from_tmdb(f"/movie/{tmdb_id}"),
            )
            log["title"] = movie.get("title")
            log["poster_path"] = movie.get("poster_path")
        except Exception:
            pass
        return log

    enriched = await asyncio.gather(*(enrich_log(log) for log in feed_res.data))

    return {"results": enriched, "count": feed_res.count, "page": page}
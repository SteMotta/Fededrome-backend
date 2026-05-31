from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.security import get_current_user
from app.schemas.list import CustomListCreate, CustomListUpdate, CustomListMovieAdd
from app.services.supabase_client import get_service_client
from app.services.tmdb_client import fetch_from_tmdb
from app.services.cache import get_or_set_cache

router = APIRouter(prefix="/lists", tags=["Custom Lists"])


@router.post("/", status_code=201)
async def create_list(list_data: CustomListCreate, user=Depends(get_current_user)):
    """Crea una nuova lista personalizzata."""
    db = get_service_client()
    res = (
        db.table("custom_lists")
        .insert({
            "user_id": user.id,
            "name": list_data.name,
            "description": list_data.description,
            "is_public": list_data.is_public
        })
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=500, detail="Errore creazione lista")
    return res.data[0]


@router.get("/")
async def get_my_lists(user=Depends(get_current_user)):
    """Restituisce tutte le liste dell'utente."""
    db = get_service_client()
    res = (
        db.table("custom_lists")
        .select("*, custom_list_movies(tmdb_id)")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data


@router.get("/{list_id}")
async def get_list_details(list_id: int, user=Depends(get_current_user)):
    """Restituisce i dettagli della lista e i film contenuti."""
    db = get_service_client()
    
    # 1. Recupera i dettagli della lista
    list_res = db.table("custom_lists").select("*").eq("id", list_id).execute()
    if not list_res.data:
        raise HTTPException(status_code=404, detail="Lista non trovata")
    
    custom_list = list_res.data[0]
    if custom_list["user_id"] != user.id and not custom_list.get("is_public", False):
        raise HTTPException(status_code=403, detail="Non autorizzato")
    
    # 2. Recupera i film contenuti nella lista
    movies_res = (
        db.table("custom_list_movies")
        .select("*")
        .eq("list_id", list_id)
        .order("added_at", desc=True)
        .execute()
    )
    
    enriched = []
    for m in movies_res.data:
        try:
            movie = await get_or_set_cache(
                f"tmdb:movie:{m['tmdb_id']}",
                lambda tmdb_id=m["tmdb_id"]: fetch_from_tmdb(f"/movie/{tmdb_id}"),
            )
            m["title"] = movie.get("title")
            m["poster_path"] = movie.get("poster_path")
            m["year"] = movie.get("release_date", "")[:4]
        except Exception:
            pass
        enriched.append(m)
        
    custom_list["movies"] = enriched
    return custom_list


@router.put("/{list_id}")
async def update_list(list_id: int, data: CustomListUpdate, user=Depends(get_current_user)):
    """Modifica i dettagli della lista."""
    db = get_service_client()
    existing = db.table("custom_lists").select("user_id").eq("id", list_id).execute()
    if not existing.data or existing.data[0]["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nessun campo da aggiornare")

    res = db.table("custom_lists").update(updates).eq("id", list_id).execute()
    return res.data[0]


@router.delete("/{list_id}", status_code=204)
async def delete_list(list_id: int, user=Depends(get_current_user)):
    """Elimina una lista personalizzata."""
    db = get_service_client()
    existing = db.table("custom_lists").select("user_id").eq("id", list_id).execute()
    if not existing.data or existing.data[0]["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato")

    db.table("custom_lists").delete().eq("id", list_id).execute()


@router.post("/{list_id}/movies", status_code=201)
async def add_movie_to_list(list_id: int, data: CustomListMovieAdd, user=Depends(get_current_user)):
    """Aggiunge un film a una lista."""
    db = get_service_client()
    # Verifica proprietà lista
    existing = db.table("custom_lists").select("user_id").eq("id", list_id).execute()
    if not existing.data or existing.data[0]["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato")
        
    # Inserisce il film, ignorando i duplicati
    res = (
        db.table("custom_list_movies")
        .upsert({
            "list_id": list_id,
            "tmdb_id": data.tmdb_id
        }, on_conflict="list_id,tmdb_id")
        .execute()
    )
    return {"status": "added"}


@router.delete("/{list_id}/movies/{tmdb_id}", status_code=204)
async def remove_movie_from_list(list_id: int, tmdb_id: int, user=Depends(get_current_user)):
    """Rimuove un film da una lista."""
    db = get_service_client()
    # Verifica proprietà lista
    existing = db.table("custom_lists").select("user_id").eq("id", list_id).execute()
    if not existing.data or existing.data[0]["user_id"] != user.id:
        raise HTTPException(status_code=403, detail="Non autorizzato")
        
    db.table("custom_list_movies").delete().eq("list_id", list_id).eq("tmdb_id", tmdb_id).execute()


@router.get("/user/{username}")
async def get_user_public_lists(username: str, user=Depends(get_current_user)):
    """Restituisce le liste pubbliche di un utente specifico."""
    db = get_service_client()
    
    # Trova il profilo tramite username
    profile_res = db.table("profiles").select("id").eq("username", username).single().execute()
    if not profile_res.data:
        raise HTTPException(status_code=404, detail="Utente non trovato")
        
    target_user_id = profile_res.data["id"]
    
    # Recupera le liste pubbliche dell'utente
    res = (
        db.table("custom_lists")
        .select("*, custom_list_movies(tmdb_id)")
        .eq("user_id", target_user_id)
        .eq("is_public", True)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data

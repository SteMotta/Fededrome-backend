from fastapi import APIRouter, Query
from app.services.cache import get_or_set_cache
from app.core.config import settings
import httpx

router = APIRouter(prefix="/youtube", tags=["YouTube"])

async def search_frusciante_video(title: str, year: str, director: str) -> str | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = "https://www.googleapis.com/youtube/v3/search"
        
        # Costruiamo la query con il nome dello youtuber, Titolo e Anno.
        # Poiché rimuoviamo il channelId, aggiungere "Federico Frusciante" è vitale per non ricevere trailer casuali.
        q = f"Federico Frusciante {title}"
        if year:
            q += f" {year}"
            
        params = {
            "part": "snippet",
            "q": q,
            "key": settings.YOUTUBE_API_KEY,
            "type": "video",
            "maxResults": 1,
            "order": "relevance"
        }
        
        response = await client.get(url, params=params)
        
        try:
            response.raise_for_status()
            print(f"YouTube API Success: 200 OK\n{response.text}")
        except httpx.HTTPStatusError as e:
            print(f"YouTube API Error: {e.response.status_code} - {e.response.text}")
            return None
            
        data = response.json()
        
        if data.get("items") and len(data["items"]) > 0:
            return data["items"][0]["id"]["videoId"]
        # Ritorna un valore speciale per mettere in cache l'assenza del video ed evitare di consumare quota API inutilmente
        return "none"

@router.get("/frusciante")
async def get_frusciante_video(
    title: str = Query(..., description="Titolo del film"),
    year: str = Query("", description="Anno di uscita"),
    director: str = Query("", description="Nome del regista")
):
    """Cerca la recensione di Federico Frusciante per un film specifico."""
    result = await get_or_set_cache(
        f"youtube:frusciante:{title}:{year}:{director}",
        lambda: search_frusciante_video(title, year, director),
        ttl=86400 * 7, # Cache for 7 days
    )
    if result == "none":
        return None
    return result

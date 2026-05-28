import httpx
from app.core.config import settings

TMDB_BASE = "https://api.themoviedb.org/3"


async def fetch_from_tmdb(path: str, params: dict = None) -> dict:
    """Esegue una GET verso l'API TMDB con autenticazione automatica (v3 api_key o v4 Bearer token)."""
    if params is None:
        params = {}
    if "language" not in params:
        params["language"] = "it-IT"

    headers = {
        "Accept": "application/json",
    }

    # Rileva se si tratta di una chiave API v3 (32 caratteri esadecimali) o di un Bearer Token v4
    api_key = settings.TMDB_API_KEY.strip()
    is_v3_key = len(api_key) == 32 and all(c in "0123456789abcdefABCDEF" for c in api_key)

    if is_v3_key:
        params["api_key"] = api_key
    else:
        headers["Authorization"] = f"Bearer {api_key}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{TMDB_BASE}{path}", params=params, headers=headers
        )
        response.raise_for_status()
        return response.json()
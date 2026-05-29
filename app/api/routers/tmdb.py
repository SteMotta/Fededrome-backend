from fastapi import APIRouter, Query, Request
from app.services.cache import get_or_set_cache
from app.services.tmdb_client import fetch_from_tmdb
from app.core.limiter import limiter

router = APIRouter(prefix="/tmdb", tags=["TMDB Proxy"])


async def _fetch_movie_with_english_credits(movie_id: int):
    # Ottieni i dettagli del film e le keywords in Italiano
    movie_data = await fetch_from_tmdb(f"/movie/{movie_id}", {"append_to_response": "keywords"})
    # Ottieni i credits in Inglese per assicurare che i nomi siano Romanizzati (no Kanji/Cirillico)
    credits_data = await fetch_from_tmdb(f"/movie/{movie_id}/credits", {"language": "en-US"})
    movie_data["credits"] = credits_data
    return movie_data

@router.get("/movie/{movie_id}")
async def get_movie(movie_id: int):
    """Dettaglio singolo film con cache 24h."""
    return await get_or_set_cache(
        f"tmdb:movie_full_en_credits:{movie_id}",
        lambda: _fetch_movie_with_english_credits(movie_id),
        ttl=86400,
    )


@router.get("/search")
@limiter.limit("30/minute")
async def search_movie(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = 1,
):
    """Ricerca film — limite 30 richieste/minuto per IP."""
    return await get_or_set_cache(
        f"tmdb:search:{q}:{page}",
        lambda: fetch_from_tmdb("/search/multi", {"query": q, "page": page}),
        ttl=3600,
    )


@router.get("/search/person")
@limiter.limit("30/minute")
async def search_person(
    request: Request,
    q: str = Query(..., min_length=1),
    page: int = 1,
):
    """Ricerca persone (cast/crew) — limite 30 richieste/minuto per IP."""
    return await get_or_set_cache(
        f"tmdb:search_person_query:{q}:{page}",
        lambda: fetch_from_tmdb("/search/person", {"query": q, "page": page}),
        ttl=3600,
    )


@router.get("/trending")
async def trending_movies():
    """Film in tendenza del giorno con cache 1h."""
    return await get_or_set_cache(
        "tmdb:trending:day",
        lambda: fetch_from_tmdb("/trending/movie/day"),
        ttl=3600,
    )


@router.get("/movie/{movie_id}/credits")
async def get_movie_credits(movie_id: int):
    """Cast e crew del film con cache 24h."""
    return await get_or_set_cache(
        f"tmdb:credits_en:{movie_id}",
        lambda: fetch_from_tmdb(f"/movie/{movie_id}/credits", {"language": "en-US"}),
        ttl=86400,
    )


@router.get("/person/{person_id}")
async def get_person(person_id: int):
    """Dettagli anagrafici di un autore/regista con cache 24h."""
    return await get_or_set_cache(
        f"tmdb:person:{person_id}",
        lambda: fetch_from_tmdb(f"/person/{person_id}", {"language": "it-IT"}),
        ttl=86400,
    )


@router.get("/person/{person_id}/credits")
async def get_person_credits(person_id: int):
    """Filmografia (cast e crew) di un autore/regista con cache 24h."""
    return await get_or_set_cache(
        f"tmdb:person_credits:{person_id}",
        lambda: fetch_from_tmdb(f"/person/{person_id}/combined_credits", {"language": "it-IT"}),
        ttl=86400,
    )

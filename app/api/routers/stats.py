from fastapi import APIRouter, Depends
from app.core.security import get_current_user
from app.services.supabase_client import get_service_client
from collections import Counter

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/{user_id}")
async def get_user_stats(user_id: str, current_user=Depends(get_current_user)):
    """Ritorna le statistiche di visione di un utente (pubbliche)."""
    db = get_service_client()
    logs = (
        db.table("movie_logs")
        .select("rating, genres_snapshot, runtime_minutes, liked, watched_date")
        .eq("user_id", user_id)
        .execute()
    )

    total_movies = len(logs.data)
    total_runtime = sum((l.get("runtime_minutes") or 0) for l in logs.data)
    liked_count = sum(1 for l in logs.data if l.get("liked"))

    ratings = [l["rating"] for l in logs.data if l.get("rating") is not None]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0
    rating_distribution = dict(Counter(str(r) for r in ratings))

    genre_counter = Counter()
    for l in logs.data:
        for g in (l.get("genres_snapshot") or []):
            genre_counter[g["name"]] += 1

    # Film per anno
    year_counter = Counter()
    for l in logs.data:
        year = (l.get("watched_date") or "")[:4]
        if year:
            year_counter[year] += 1

    return {
        "total_movies": total_movies,
        "total_runtime_minutes": total_runtime,
        "total_runtime_hours": round(total_runtime / 60, 1),
        "liked_count": liked_count,
        "average_rating": avg_rating,
        "rating_distribution": rating_distribution,
        "top_genres": [
            {"genre": k, "count": v} for k, v in genre_counter.most_common(5)
        ],
        "films_per_year": dict(sorted(year_counter.items())),
    }
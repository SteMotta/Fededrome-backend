import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.api.routers import tmdb, movies, watchlist, stats, social, users, youtube

app = FastAPI(
    title="Fededrome API",
    version="1.0.0",
    docs_url="/docs" if settings.ENV == "development" else None,
    redoc_url=None,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — ristretto in produzione
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Routers
app.include_router(tmdb.router)
app.include_router(movies.router)
app.include_router(watchlist.router)
app.include_router(stats.router)
app.include_router(social.router)
app.include_router(users.router)
app.include_router(youtube.router)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "timestamp": time.time(), "env": settings.ENV}
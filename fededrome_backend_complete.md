# Fededrome — Backend & Infrastruttura: Guida Completa

> **Stack:** FastAPI · Python · Redis · Supabase Self-Hosted · Nginx · Docker · Digital Ocean

---

## Indice

### Parte 1 — Setup & Creazione Progetto

1. [Prerequisiti e Strumenti](#1-prerequisiti-e-strumenti)
2. [Creazione Progetto FastAPI](#2-creazione-progetto-fastapi)
3. [Struttura Completa del Progetto](#3-struttura-completa-del-progetto)
4. [File di Configurazione](#4-file-di-configurazione)

### Parte 2 — Codice Applicativo

5. [Core: Config, Security, Limiter](#5-core-config-security-limiter)
6. [Services: Supabase, Redis, TMDB](#6-services-supabase-redis-tmdb)
7. [Schemas Pydantic](#7-schemas-pydantic)
8. [Router: TMDB Proxy](#8-router-tmdb-proxy)
9. [Router: Movies & Diary](#9-router-movies--diary)
10. [Router: Watchlist](#10-router-watchlist)
11. [Router: Stats](#11-router-stats)
12. [Router: Social](#12-router-social)
13. [Router: Users & Profiles](#13-router-users--profiles)
14. [Main — Entry Point](#14-main--entry-point)

### Parte 3 — Database

15. [Schema SQL Completo](#15-schema-sql-completo)
16. [RLS Policies e Storage Bucket](#16-rls-policies-e-storage-bucket)

### Parte 4 — Infrastruttura

17. [Dockerfile](#17-dockerfile)
18. [Docker Compose Completo](#18-docker-compose-completo)
19. [Nginx Configuration](#19-nginx-configuration)
20. [Supabase Self-Hosted su Digital Ocean](#20-supabase-self-hosted-su-digital-ocean)
    - [20.1 Configurazione della Verifica Email e SMTP nel Self-Hosting (GoTrue)](#201-configurazione-della-verifica-email-e-smtp-nel-self-hosting-gotrue)
21. [Deploy Script e .dockerignore](#21-deploy-script-e-dockerignore)

### Parte 5 — Checklist

22. [Checklist Completa](#22-checklist-completa)

---

## PARTE 1 — SETUP & CREAZIONE PROGETTO

---

## 1. Prerequisiti e Strumenti

Prima di iniziare assicurarsi di avere installato sulla macchina di sviluppo:

| Strumento      | Versione minima | Verifica                 |
| -------------- | --------------- | ------------------------ |
| Python         | 3.11+           | `python --version`       |
| Docker Desktop | 24+             | `docker --version`       |
| Docker Compose | v2+             | `docker compose version` |
| Git            | qualsiasi       | `git --version`          |

Sul **droplet Digital Ocean** (Ubuntu 22.04 consigliato):

```bash
# Passo 1 — Aggiornare il sistema
sudo apt update && sudo apt upgrade -y

# Passo 2 — Installare Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Passo 3 — Verificare l'installazione
docker --version
docker compose version

# Passo 4 — Installare Certbot per SSL
sudo apt install -y certbot

# Passo 5 — Puntare il dominio api.fededrome.com all'IP del droplet
# (da fare nel pannello DNS del registrar, record A)
# Verificare: nslookup api.fededrome.com
```

---

## 2. Creazione Progetto FastAPI

Eseguire questi comandi in ordine sulla macchina di sviluppo:

```bash
# Passo 1 — Creare la cartella del progetto
mkdir fededrome-backend
cd fededrome-backend

# Passo 2 — Inizializzare git
git init
echo "venv/" >> .gitignore
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore

# Passo 3 — Creare l'ambiente virtuale Python
python -m venv venv

# Passo 4 — Attivare l'ambiente virtuale
# Linux / macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Passo 5 — Installare le dipendenze
pip install fastapi "uvicorn[standard]" httpx pydantic pydantic-settings \
            redis supabase python-multipart slowapi gunicorn

# Passo 6 — Congelare le dipendenze
pip freeze > requirements.txt

# Passo 7 — Creare la struttura delle cartelle
mkdir -p app/api/routers
mkdir -p app/core
mkdir -p app/services
mkdir -p app/schemas
mkdir -p nginx
touch app/__init__.py
touch app/api/__init__.py
touch app/api/routers/__init__.py
touch app/core/__init__.py
touch app/services/__init__.py
touch app/schemas/__init__.py

# Passo 8 — Copiare il file .env di esempio
cp .env.example .env
# (poi aprire .env e compilare i valori reali)
```

**`requirements.txt` finale:**

```txt
fastapi==0.103.1
uvicorn[standard]==0.23.2
httpx==0.25.0
pydantic==2.4.2
pydantic-settings==2.0.3
redis==5.0.1
supabase==2.0.2
python-multipart==0.0.6
slowapi==0.1.9
gunicorn==21.2.0
```

---

## 3. Struttura Completa del Progetto

```
fededrome-backend/
│
├── app/
│   ├── __init__.py
│   ├── main.py                        ← Entry point FastAPI
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                  ← Variabili d'ambiente (pydantic-settings)
│   │   ├── security.py                ← Validazione JWT Supabase
│   │   └── limiter.py                 ← Rate limiting (slowapi)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── tmdb.py                ← Proxy API TMDB (search, trending, dettaglio)
│   │       ├── movies.py              ← Log film, diario, modifica/elimina
│   │       ├── watchlist.py           ← Aggiungi/rimuovi dalla watchlist
│   │       ├── stats.py               ← Statistiche utente
│   │       ├── social.py              ← Follow/unfollow, feed attività
│   │       └── users.py               ← Profili pubblici, aggiornamento profilo
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── supabase_client.py         ← Client Supabase con service role
│   │   ├── cache.py                   ← Helper Redis get/set con TTL
│   │   └── tmdb_client.py             ← Fetch verso l'API TMDB
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── movie.py                   ← MovieLogCreate, MovieLogUpdate
│       └── user.py                    ← ProfileUpdate
│
├── nginx/
│   └── nginx.conf                     ← Reverse proxy + SSL
│
├── migrations/
│   ├── 01_schema.sql                  ← Tabelle principali (già in database.sql)
│   └── 02_rls_policies.sql            ← RLS + storage bucket avatar
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env                               ← NON committare mai
├── .env.example                       ← Committare questo
├── .gitignore
├── deploy.sh
└── requirements.txt
```

---

## 4. File di Configurazione

**`.env.example`**

```dotenv
# Supabase — ottenere dall'interfaccia Supabase dopo il deploy self-hosted
SUPABASE_URL=https://db.fededrome.com
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# TMDB — ottenere da https://developer.themoviedb.org (Bearer Token)
TMDB_API_KEY=your_tmdb_bearer_token_here

# Redis — usa il nome container Docker in produzione
REDIS_URL=redis://fededrome_redis:6379/0

# Applicazione
ENV=production
# Inserire le origini CORS come array JSON valido
ALLOWED_ORIGINS=["https://fededrome.com", "https://app.fededrome.com"]
```

**`.gitignore`**

```
# Python
__pycache__/
*.py[cod]
*.pyo
venv/
.venv/
*.egg-info/
dist/
.pytest_cache/

# Ambiente
.env
.env.local
.env.*.local

# Docker
*.log

# IDE
.vscode/
.idea/
```

---

## PARTE 2 — CODICE APPLICATIVO

---

## 5. Core: Config, Security, Limiter

**`app/core/config.py`**

```python
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Any


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    REDIS_URL: str
    TMDB_API_KEY: str
    ENV: str = "development"
    ALLOWED_ORIGINS: Any = ["http://localhost:3000"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    class Config:
        env_file = ".env"


settings = Settings()
```

**`app/core/security.py`**

```python
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from app.core.config import settings

security = HTTPBearer()


def get_auth_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
):
    token = credentials.credentials
    supabase = get_auth_client()
    try:
        res = supabase.auth.get_user(token)
        if not res.user:
            raise HTTPException(status_code=401, detail="Token non valido")
        return res.user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
```

**`app/core/limiter.py`**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

---

## 6. Services: Supabase, Redis, TMDB

**`app/services/supabase_client.py`**

```python
from supabase import create_client, Client
from app.core.config import settings


def get_service_client() -> Client:
    """Client Supabase con service role key — bypassa RLS, usare solo lato server."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
```

**`app/services/cache.py`**

```python
import json
import redis.asyncio as redis
from typing import Callable, Any
from app.core.config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def get_or_set_cache(key: str, fetch_func: Callable, ttl: int = 3600) -> Any:
    """Ritorna il valore dalla cache Redis; se assente lo calcola con fetch_func e lo salva."""
    cached = await redis_client.get(key)
    if cached:
        return json.loads(cached)

    data = await fetch_func()

    if data:
        await redis_client.setex(key, ttl, json.dumps(data))
    return data


async def invalidate_cache(key: str) -> None:
    """Elimina una chiave dalla cache."""
    await redis_client.delete(key)
```

**`app/services/tmdb_client.py`**

```python
import httpx
from app.core.config import settings

TMDB_BASE = "https://api.themoviedb.org/3"


async def fetch_from_tmdb(path: str, params: dict = None) -> dict:
    """Esegue una GET verso l'API TMDB con autenticazione Bearer."""
    if params is None:
        params = {}
    params["language"] = "it-IT"

    headers = {
        "Authorization": f"Bearer {settings.TMDB_API_KEY}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{TMDB_BASE}{path}", params=params, headers=headers
        )
        response.raise_for_status()
        return response.json()
```

---

## 7. Schemas Pydantic

**`app/schemas/movie.py`**

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class MovieLogCreate(BaseModel):
    tmdb_id: int
    watched_date: date
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    review: Optional[str] = ""
    liked: Optional[bool] = False


class MovieLogUpdate(BaseModel):
    watched_date: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    review: Optional[str] = None
    liked: Optional[bool] = None
```

**`app/schemas/user.py`**

```python
from pydantic import BaseModel
from typing import Optional


class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
```

---

## 8. Router: TMDB Proxy

```python
# app/api/routers/tmdb.py
from fastapi import APIRouter, Query, Request
from app.services.cache import get_or_set_cache
from app.services.tmdb_client import fetch_from_tmdb
from app.core.limiter import limiter

router = APIRouter(prefix="/tmdb", tags=["TMDB Proxy"])


@router.get("/movie/{movie_id}")
async def get_movie(movie_id: int):
    """Dettaglio singolo film con cache 24h."""
    return await get_or_set_cache(
        f"tmdb:movie:{movie_id}",
        lambda: fetch_from_tmdb(f"/movie/{movie_id}"),
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
        f"tmdb:credits:{movie_id}",
        lambda: fetch_from_tmdb(f"/movie/{movie_id}/credits"),
        ttl=86400,
    )
```

---

## 9. Router: Movies & Diary

```python
# app/api/routers/movies.py
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
```

---

## 10. Router: Watchlist

```python
# app/api/routers/watchlist.py
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
```

---

## 11. Router: Stats

```python
# app/api/routers/stats.py
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
```

---

## 12. Router: Social

> **Nota:** La tabella si chiama `followers` nel database, non `follows`.

```python
# app/api/routers/social.py
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


@router.get("/feed")
async def get_social_feed(page: int = 1, user=Depends(get_current_user)):
    """Ritorna il feed degli utenti seguiti, con dati TMDB arricchiti."""
    db = get_service_client()
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

    enriched = []
    for log in feed_res.data:
        try:
            movie = await get_or_set_cache(
                f"tmdb:movie:{log['tmdb_id']}",
                lambda tmdb_id=log["tmdb_id"]: fetch_from_tmdb(f"/movie/{tmdb_id}"),
            )
            log["title"] = movie.get("title")
            log["poster_path"] = movie.get("poster_path")
        except Exception:
            pass
        enriched.append(log)

    return {"results": enriched, "count": feed_res.count, "page": page}
```

---

## 13. Router: Users & Profiles

```python
# app/api/routers/users.py
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
```

---

## 14. Main — Entry Point

```python
# app/main.py
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.api.routers import tmdb, movies, watchlist, stats, social, users

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


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "timestamp": time.time(), "env": settings.ENV}
```

---

## PARTE 3 — DATABASE

---

## 15. Schema SQL Completo

Salvare come `migrations/01_schema.sql` ed eseguire per primo.

```sql
-- ─── Profiles ──────────────────────────────────────────────────────────────
CREATE TABLE public.profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username    TEXT UNIQUE NOT NULL,
    email       TEXT NOT NULL,
    bio         TEXT DEFAULT '',
    avatar_url  TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.profiles FROM anon, authenticated;

-- Creazione schema privato per funzioni di trigger interne (non esposte alle API REST)
CREATE SCHEMA IF NOT EXISTS private;

-- Trigger: crea profilo automaticamente alla registrazione
CREATE OR REPLACE FUNCTION private.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, username)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'username', split_part(NEW.email, '@', 1))
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION private.handle_new_user();

-- ─── Followers ─────────────────────────────────────────────────────────────
CREATE TABLE public.followers (
    follower_id  UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    following_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (follower_id, following_id)
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.followers FROM anon, authenticated;

-- ─── Movie Logs ────────────────────────────────────────────────────────────
CREATE TABLE public.movie_logs (
    id              BIGSERIAL PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tmdb_id         INTEGER NOT NULL,
    watched_date    DATE NOT NULL,
    rating          NUMERIC(2,1) CHECK (rating >= 0.5 AND rating <= 5.0),
    review          TEXT DEFAULT '',
    liked           BOOLEAN DEFAULT FALSE,
    genres_snapshot JSONB DEFAULT '[]',
    runtime_minutes SMALLINT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.movie_logs FROM anon, authenticated;

CREATE INDEX idx_logs_user_date ON public.movie_logs(user_id, watched_date DESC);
CREATE INDEX idx_logs_tmdb      ON public.movie_logs(tmdb_id);

-- Trigger: aggiorna updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql SET search_path = public;

CREATE TRIGGER movie_logs_updated_at
  BEFORE UPDATE ON public.movie_logs
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ─── Watchlist ─────────────────────────────────────────────────────────────
CREATE TABLE public.watchlist (
    user_id    UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    tmdb_id    INTEGER NOT NULL,
    added_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (user_id, tmdb_id)
);

-- Revoca l'accesso SELECT ad anon e authenticated per risolvere i warning di esposizione GraphQL
REVOKE SELECT ON public.watchlist FROM anon, authenticated;

CREATE INDEX idx_watchlist_user ON public.watchlist(user_id);
```

---

## 16. RLS Policies e Storage Bucket

Salvare come `migrations/02_rls_policies.sql` ed eseguire **dopo** lo schema.

```sql
-- ─── Abilita RLS su tutte le tabelle ───────────────────────────────────────
ALTER TABLE public.profiles    ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.followers   ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.movie_logs  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.watchlist   ENABLE ROW LEVEL SECURITY;

-- ─── Disabilita pg_graphql per proteggere la struttura del database ──────────
COMMENT ON TABLE public.profiles IS '@graphql(disable: true)';
COMMENT ON TABLE public.followers IS '@graphql(disable: true)';
COMMENT ON TABLE public.movie_logs IS '@graphql(disable: true)';
COMMENT ON TABLE public.watchlist IS '@graphql(disable: true)';

-- ─── Profiles ──────────────────────────────────────────────────────────────
CREATE POLICY "profiles_select_public"
  ON public.profiles FOR SELECT USING (true);

CREATE POLICY "profiles_update_own"
  ON public.profiles FOR UPDATE USING ((select auth.uid()) = id);

-- ─── Movie Logs ────────────────────────────────────────────────────────────
-- I log sono pubblici (come su Letterboxd)
CREATE POLICY "logs_select_public"
  ON public.movie_logs FOR SELECT USING (true);

CREATE POLICY "logs_insert_own"
  ON public.movie_logs FOR INSERT WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "logs_update_own"
  ON public.movie_logs FOR UPDATE USING ((select auth.uid()) = user_id);

CREATE POLICY "logs_delete_own"
  ON public.movie_logs FOR DELETE USING ((select auth.uid()) = user_id);

-- ─── Watchlist ─────────────────────────────────────────────────────────────
-- La watchlist è privata
CREATE POLICY "watchlist_select_own"
  ON public.watchlist FOR SELECT USING ((select auth.uid()) = user_id);

CREATE POLICY "watchlist_insert_own"
  ON public.watchlist FOR INSERT WITH CHECK ((select auth.uid()) = user_id);

CREATE POLICY "watchlist_delete_own"
  ON public.watchlist FOR DELETE USING ((select auth.uid()) = user_id);

-- ─── Followers ─────────────────────────────────────────────────────────────
CREATE POLICY "followers_select_public"
  ON public.followers FOR SELECT USING (true);

CREATE POLICY "followers_insert_own"
  ON public.followers FOR INSERT WITH CHECK ((select auth.uid()) = follower_id);

CREATE POLICY "followers_delete_own"
  ON public.followers FOR DELETE USING ((select auth.uid()) = follower_id);

-- ─── Storage: bucket avatar ────────────────────────────────────────────────
-- Nota: Essendo un bucket pubblico (public = true), gli oggetti sono accessibili
-- pubblicamente tramite URL diretto. Non è necessaria una policy SELECT di tipo broad,
-- il che previene l'enumerazione (listing) indesiderata dei file da parte dei client.
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT DO NOTHING;

CREATE POLICY "avatars_upload_own"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'avatars'
    AND (select auth.uid())::text = (storage.foldername(name))[1]
  );

CREATE POLICY "avatars_update_own"
  ON storage.objects FOR UPDATE
  USING (
    bucket_id = 'avatars'
    AND (select auth.uid())::text = (storage.foldername(name))[1]
  );
```

---

## PARTE 4 — INFRASTRUTTURA

---

## 17. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Dipendenze di sistema (rimosso curl per ottimizzare l'immagine)
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Dipendenze Python (separato dal COPY . . per sfruttare la cache Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn uvicorn

# Codice applicativo
COPY . .

EXPOSE 8000

# Produzione: 2 worker Gunicorn + Uvicorn worker class
# Corretto: rimosse le backslash non valide per la sintassi JSON di CMD e rimosso il flag --proxy-headers non supportato da Gunicorn
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "2", "--bind", "0.0.0.0:8000", "--forwarded-allow-ips", "*", "--access-logfile", "-", "--error-logfile", "-"]
```

---

## 18. Docker Compose Completo

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    container_name: fededrome_nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - nginx_logs:/var/log/nginx
    depends_on:
      fastapi:
        condition: service_healthy
    networks:
      - fededrome_network

  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fededrome_api
    restart: always
    env_file: .env
    environment:
      - REDIS_URL=redis://fededrome_redis:6379/0
    expose:
      - "8000"
    depends_on:
      redis:
        condition: service_healthy
    networks:
      - fededrome_network
    healthcheck:
      test:
        [
          "CMD",
          "python",
          "-c",
          "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')",
        ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 15s

  redis:
    image: redis:7-alpine
    container_name: fededrome_redis
    restart: always
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    expose:
      - "6379"
    volumes:
      - redis_data:/data
    networks:
      - fededrome_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
  nginx_logs:

networks:
  fededrome_network:
    driver: bridge
```

---

## 19. Nginx Configuration

```nginx
# nginx/nginx.conf

upstream fastapi_backend {
    server fastapi:8000;
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name api.fededrome.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.fededrome.com;

    # Certificati Let's Encrypt (generati con Certbot sul droplet)
    ssl_certificate     /etc/letsencrypt/live/api.fededrome.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.fededrome.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Proxy verso FastAPI
    location / {
        proxy_pass         http://fastapi_backend;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        proxy_connect_timeout 60s;
        proxy_send_timeout    60s;
        proxy_read_timeout    60s;

        # Upload avatar max 5MB
        client_max_body_size 5M;
    }

    # Health check: non loggato
    location /health {
        proxy_pass http://fastapi_backend/health;
        access_log off;
    }
}
```

---

## 20. Supabase Self-Hosted su Digital Ocean

Eseguire questi comandi direttamente sul droplet, in una cartella separata dal backend:

```bash
# Passo 1 — Clonare il repo ufficiale di Supabase
git clone --depth 1 https://github.com/supabase/supabase.git /opt/supabase
cd /opt/supabase/docker

# Passo 2 — Copiare il file .env di esempio
cp .env.example .env

# Passo 3 — Generare i secrets (eseguire ogni comando separatamente e salvare i valori)
echo "POSTGRES_PASSWORD: $(openssl rand -base64 32)"
echo "JWT_SECRET: $(openssl rand -base64 32)"

# Passo 4 — Aprire .env e compilare i valori
nano .env
```

Valori chiave da impostare nel `.env` di Supabase:

```dotenv
POSTGRES_PASSWORD=<valore generato>
JWT_SECRET=<valore generato, minimo 32 caratteri>

# Generare ANON_KEY e SERVICE_ROLE_KEY su https://supabase.com/docs/guides/self-hosting/docker#generate-api-keys
ANON_KEY=<jwt generato con payload role:anon>
SERVICE_ROLE_KEY=<jwt generato con payload role:service_role>

SITE_URL=https://fededrome.com
API_EXTERNAL_URL=https://db.fededrome.com
SUPABASE_PUBLIC_URL=https://db.fededrome.com

# Email & SMTP (Configurazione standard per l'invio delle email di conferma)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=<sendgrid_api_key>
SMTP_SENDER_EMAIL=noreply@fededrome.com
```

### 20.1 Configurazione della Verifica Email e SMTP nel Self-Hosting (GoTrue)

Nel setup self-hosted su VPS, la verifica dell'email non viene controllata dal file `config.toml` della CLI locale, ma viene gestita direttamente dalle **variabili d'ambiente del container GoTrue (l'Auth service di Supabase)** all'interno del file `.env` di Supabase situato sulla VPS.

Se desideri attivare e testare in produzione il flusso di verifica dell'email che abbiamo integrato nell'applicazione Flutter:

1. **Disabilita l'auto-conferma**: Assicurati che nel file `.env` la seguente variabile sia impostata su `false` (costringendo gli utenti a cliccare sul link di verifica prima di poter fare l'accesso):
   ```dotenv
   GOTRUE_MAILER_AUTOCONFIRM=false
   ```

2. **Configura le variabili SMTP di GoTrue**:
   Assicurati di inserire i parametri di connessione del tuo provider SMTP reale (es. *Resend*, *SendGrid* o *Brevo*) all'interno delle configurazioni di GoTrue:
   ```dotenv
   GOTRUE_SMTP_HOST=smtp.sendgrid.net
   GOTRUE_SMTP_PORT=587
   GOTRUE_SMTP_USER=apikey
   GOTRUE_SMTP_PASS=<tua_api_key_smtp>
   GOTRUE_SMTP_ADMIN_EMAIL=noreply@fededrome.com
   GOTRUE_SMTP_SENDER_NAME="Fededrome"
   ```

3. **Configura gli URL di Reindirizzamento (Redirect per l'App Mobile)**:
   Per consentire al link di verifica contenuto nell'email di riportare correttamente l'utente dentro l'applicazione mobile dopo aver confermato l'account, imposta i parametri di redirect inserendo anche lo schema custom dei Deep Link dell'app Flutter:
   ```dotenv
   GOTRUE_SITE_URL=https://fededrome.com
   # Aggiungi lo schema custom di Flutter (es. fededrome://*) all'allow-list dei redirect
   GOTRUE_URI_ALLOW_LIST=https://fededrome.com/*,fededrome://*
   ```


```bash
# Passo 5 — Avviare Supabase
docker compose up -d

# Passo 6 — Attendere che tutti i container siano healthy (~30 secondi)
docker compose ps

# Passo 7 — Applicare le migration SQL
docker exec -i supabase-db psql -U postgres -d postgres \
  < /path/to/fededrome-backend/migrations/01_schema.sql

docker exec -i supabase-db psql -U postgres -d postgres \
  < /path/to/fededrome-backend/migrations/02_rls_policies.sql

# Passo 8 — Verificare le tabelle
docker exec -it supabase-db psql -U postgres -d postgres \
  -c "\dt public.*"
```

---

## 21. Deploy Script e .dockerignore

**`.dockerignore`**

```
__pycache__/
*.py[cod]
*.pyo
.env
.env.*
!.env.example
venv/
.venv/
.git/
.gitignore
*.md
tests/
.pytest_cache/
*.egg-info/
dist/
nginx/
migrations/
```

**`deploy.sh`** — da eseguire sul droplet per ogni aggiornamento:

```bash
#!/bin/bash
# deploy.sh

set -e

echo "🚀 Fededrome Deploy — $(date)"

# Pull dell'ultimo codice dal repository
git pull origin main

# Rebuild dell'immagine FastAPI
docker compose build --no-cache fastapi

# Riavvio con downtime quasi-nullo (near-zero-downtime)
# --no-deps: non ricrea Redis e Nginx se non cambiati
docker compose up -d --no-deps fastapi

# Ricarica Nginx per ri-risolvere l'IP del nuovo container FastAPI ed evitare errori 502
docker compose exec nginx nginx -s reload 2>/dev/null || true

# Pulizia immagini non più usate
docker image prune -f

echo "✅ Deploy completato"
docker compose ps
```

```bash
# Rendere eseguibile una sola volta
chmod +x deploy.sh
```

**Prima messa in produzione** (solo la prima volta):

```bash
# Passo 1 — Ottenere il certificato SSL con Certbot
sudo certbot certonly --standalone -d api.fededrome.com

# Passo 2 — Copiare il repository sul droplet
git clone https://github.com/tuo-repo/fededrome-backend.git /opt/fededrome-backend
cd /opt/fededrome-backend

# Passo 3 — Creare il file .env
cp .env.example .env
nano .env  # compilare con i valori reali

# Passo 4 — Avviare tutti i container
docker compose up -d

# Passo 5 — Verificare i log
docker compose logs -f fastapi
```

---

## PARTE 5 — CHECKLIST

---

## 22. Checklist Completa

### Setup Iniziale

- [ ] Python 3.11+ e Docker installati sulla macchina di sviluppo
- [ ] Droplet Digital Ocean creato (Ubuntu 22.04, min 2GB RAM)
- [ ] Docker installato sul droplet
- [ ] Dominio `api.fededrome.com` punta all'IP del droplet (record DNS A)

### Codice Backend

- [ ] Ambiente virtuale creato e dipendenze installate
- [ ] Struttura cartelle creata con tutti i `__init__.py`
- [ ] `.env` compilato da `.env.example`
- [ ] `app/core/config.py` — Settings con tutti i campi
- [ ] `app/core/security.py` — validazione JWT
- [ ] `app/core/limiter.py` — rate limiter
- [ ] `app/services/` — tutti e tre i service file
- [ ] `app/schemas/` — movie.py e user.py
- [ ] `app/api/routers/` — tutti e 6 i router (tmdb, movies, watchlist, stats, social, users)
- [ ] `app/main.py` — tutti i router inclusi, CORS ristretto

### Database

- [ ] `migrations/01_schema.sql` eseguito su Supabase
- [ ] `migrations/02_rls_policies.sql` eseguito su Supabase
- [ ] Storage bucket `avatars` creato e verificato

### Infrastruttura

- [ ] `Dockerfile` presente
- [ ] `docker-compose.yml` con healthcheck Redis e FastAPI
- [ ] `nginx/nginx.conf` presente
- [ ] `.dockerignore` presente
- [ ] `deploy.sh` presente con `chmod +x`

### Supabase Self-Hosted

- [ ] Repo Supabase clonato in `/opt/supabase`
- [ ] Secrets generati con `openssl rand`
- [ ] `.env` Supabase compilato (SMTP incluso)
- [ ] `docker compose up -d` eseguito e tutti i container healthy
- [ ] Migration SQL applicata e tabelle verificate

### Primo Deploy

- [ ] Certificato SSL ottenuto con Certbot
- [ ] Repository clonato sul droplet
- [ ] `.env` compilato sul droplet
- [ ] `docker compose up -d` eseguito
- [ ] `GET https://api.fededrome.com/health` risponde `{"status": "ok"}`

## 23. Sviluppo e Deploy Locale con Docker Desktop & Supabase CLI

Per testare l'applicazione in locale prima del deploy sul server DigitalOcean, utilizzeremo **Docker Desktop** e la **Supabase CLI** ufficiale. Questo approccio permette di avere un'istanza locale identica a quella di produzione, senza dipendere da server esterni e con migrations applicate automaticamente all'avvio.

### 23.1 Setup e Avvio di Supabase CLI

Supabase CLI permette di avviare l'intera suite di servizi Supabase (Database Postgres, Auth, Storage, Studio) in locale tramite Docker.

#### Passo 1 — Installare Supabase CLI

A seconda del sistema operativo, installare la CLI:

- **Windows (tramite Scoop o NPM)**:

  ```powershell
  # Con Scoop:
  scoop bucket add supabase https://github.com/supabase/scoop-bucket.git
  scoop install supabase

  # Oppure con NPM (globale):
  npm install -g supabase-cli
  ```

- **macOS / Linux (tramite Homebrew)**:
  ```bash
  brew install supabase/tap/supabase
  ```

#### Passo 2 — Inizializzare il progetto Supabase locale

Eseguire il comando nella cartella principale del backend:

```bash
supabase init
```

Questo comando creerà una cartella `supabase/` contenente la configurazione del progetto.

#### Passo 3 — Configurare l'Autenticazione Google (OAuth) nel Setup Locale

Dopo aver inizializzato il progetto, apri il file `supabase/config.toml` generato dalla CLI e individua la sezione relativa a Google per abilitare il login locale. Inserisci le tue credenziali OAuth (ottenute dalla Google Cloud Console):

```toml
[auth.external.google]
enabled = true
client_id = "env(GOOGLE_CLIENT_ID)"
secret = "env(GOOGLE_CLIENT_SECRET)"
# Assicurati di aggiungere questo URI di reindirizzamento nella Google Cloud Console per i test in locale:
# http://localhost:54321/auth/v1/callback
```

*Nota: Affinché la funzione `env()` funzioni, assicurati di aver definito le variabili `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` all'interno del file `.env` che si trova nella stessa cartella da cui esegui i comandi della Supabase CLI.*

#### Passo 4 — Aggiungere le Migration al Setup Locale

Per fare in modo che Supabase applichi automaticamente le nostre tabelle e le politiche RLS all'avvio, creiamo i file di migrazione copiando i nostri file SQL:

```bash
# Creare le cartelle se non esistono
mkdir -p supabase/migrations

# Copiare gli script SQL rinominandoli con un timestamp/sequenza ordinata
cp migrations/01_schema.sql supabase/migrations/20260524000001_schema.sql
cp migrations/02_rls_policies.sql supabase/migrations/20260524000002_rls_policies.sql
```

#### Passo 5 — Avviare la suite locale di Supabase

Assicurarsi che **Docker Desktop** sia attivo e funzionante, quindi avviare lo stack:

```bash
supabase start
```

_Nota: Il primo avvio richiederà qualche minuto per scaricare le immagini Docker._

Al termine dell'avvio, il terminale mostrerà i dettagli di configurazione e le chiavi API:

```text
Started supabase local development setup.

         API URL: http://localhost:54321
          DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
      Studio URL: http://localhost:54323
    Inbucket URL: http://localhost:54324
        anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

_Salvare e copiare queste chiavi per il passo successivo._

---

### 23.2 Configurazione del file `.env.local`

Creare o modificare il file `.env.local` nella cartella principale del backend (accanto a `.env`).
Dal momento che FastAPI gira all'interno di un container Docker ed ha bisogno di comunicare con la suite Supabase che risiede sulla macchina host (esposta sulle porte Docker mappate), utilizzeremo l'host speciale `host.docker.internal` per l'indirizzo IP.

```dotenv
# .env

# Supabase Local CLI — Indirizzo visibile all'interno della rete Docker
# (Utilizza host.docker.internal per riferirsi alla macchina host locale dal container)
SUPABASE_URL=http://host.docker.internal:54321
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key_here

# TMDB API — Bearer Token di sviluppo
TMDB_API_KEY=your_tmdb_bearer_token_here

# URL di Redis interno alla rete Docker locale (connessione da container a container)
REDIS_URL=redis://fededrome_redis_local:6379/0

# Configurazione applicazione
ENV=development
# Inserire le origini CORS come array JSON valido
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:54321", "http://10.0.2.2"]
```

---

### 23.3 Creazione del `docker-compose.local.yml`

Creare o aggiornare `docker-compose.local.yml` nella root del progetto.
Per consentire al container di FastAPI (`fededrome_api_local`) di risolvere correttamente l'indirizzo `host.docker.internal` per comunicare con Supabase CLI, aggiungiamo la configurazione `extra_hosts`:

```yaml
# docker-compose.local.yml
services:
  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: fededrome_api_local
    restart: always
    env_file: .env
    ports:
      - "8000:8000" # Espone FastAPI direttamente sulla macchina host
    volumes:
      - .:/app # Monta il codice sorgente per abilitare l'hot-reload locale
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      redis:
        condition: service_healthy
    extra_hosts:
      - "host.docker.internal:host-gateway" # Permette l'accesso ai servizi dell'host (Supabase CLI)
    networks:
      - fededrome_local_network

  redis:
    image: redis:7-alpine
    container_name: fededrome_redis_local
    restart: always
    ports:
      - "6379:6379" # Espone Redis se si desidera collegarsi con una GUI (es. Redis Insight)
    volumes:
      - redis_local_data:/data
    networks:
      - fededrome_local_network
    healthcheck:
      test: [ "CMD", "redis-cli", "ping" ]
      interval: 5s
      timeout: 3s
      retries: 3

volumes:
  redis_local_data:

networks:
  fededrome_local_network:
    driver: bridge
```

---

### 23.4 Comandi per la Gestione dello Stack Locale

#### Gestione Supabase CLI Locale:

```bash
# Avviare Supabase (se spento)
supabase start

# Fermare i servizi Supabase locali (senza perdere i dati delle tabelle)
supabase stop

# Resettare completamente il database locale riapplicando tutte le migrations da zero
supabase db reset

# Mostrare lo stato e gli URL dei servizi locali
supabase status
```

#### Gestione Backend FastAPI & Redis (Docker Compose):

```bash
# 1. Avviare lo stack backend locale in background
docker compose -f docker-compose.local.yml up -d

# 2. Verificare che i container siano attivi e "healthy"
docker compose -f docker-compose.local.yml ps

# 3. Visualizzare i log di FastAPI in tempo reale (per vedere errori o print)
docker compose -f docker-compose.local.yml logs -f fastapi

# 4. Spegnere lo stack locale senza perdere i dati della cache di Redis
docker compose -f docker-compose.local.yml down

# 5. Spegnere lo stack locale CANCELLANDO la cache di Redis (pulizia totale)
docker compose -f docker-compose.local.yml down -v

# 6. Forzare il rebuild dell'immagine locale (necessario SOLO se aggiungi nuove librerie in requirements.txt o modifichi il Dockerfile)
docker compose -f docker-compose.local.yml up -d --build fastapi
```

### 23.5 Verifica del Funzionamento Locale

Una volta avviato tutto con successo, puoi validare lo stack:

- **Supabase Studio (Dashboard locale)**: Accedi a `http://localhost:54323`. Avrai a disposizione la dashboard web completa per consultare il database locale, l'auth dei profili e visualizzare i bucket del vostro storage.

- **FastAPI Health Check**: Accedi a `http://localhost:8000/health`. Dovrebbe risponde `{"status": "ok", "env": "development"}`.

- **Documentazione Interattiva (Swagger)**: Accedi a `http://localhost:8000/docs`. In modalità development, FastAPI sblocca la pagina interattiva dove puoi testare manualmente le rotte della cache di TMDB, i log e le funzioni social prima di connetterci l'app Flutter.

- **Inbucket (Servizio Email locale)**: Accedi a `http://localhost:54324` per vedere e validare le email inviate da Supabase (es. email di conferma registrazione o cambio password).

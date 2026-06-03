from fastapi import APIRouter, Query
from app.services.cache import get_or_set_cache
from app.services.tmdb_client import fetch_from_tmdb
from app.core.config import settings
import httpx
import random
import datetime
import re
import html

router = APIRouter(prefix="/youtube", tags=["YouTube"])

MOVIES_POOL = [
    {"title": "Videodrome", "year": "1983", "director": "David Cronenberg", "tmdb_id": 431},
    {"title": "La Cosa", "year": "1982", "director": "John Carpenter", "tmdb_id": 1091},
    {"title": "Shining", "year": "1980", "director": "Stanley Kubrick", "tmdb_id": 694},
    {"title": "Pulp Fiction", "year": "1994", "director": "Quentin Tarantino", "tmdb_id": 680},
    {"title": "Suspiria", "year": "1977", "director": "Dario Argento", "tmdb_id": 11902},
    {"title": "Mulholland Drive", "year": "2001", "director": "David Lynch", "tmdb_id": 834},
    {"title": "Blade Runner", "year": "1982", "director": "Ridley Scott", "tmdb_id": 78},
    {"title": "Taxi Driver", "year": "1976", "director": "Martin Scorsese", "tmdb_id": 103},
    {"title": "Alien", "year": "1979", "director": "Ridley Scott", "tmdb_id": 348},
    {"title": "Il Cavaliere Oscuro", "year": "2008", "director": "Christopher Nolan", "tmdb_id": 155},
    {"title": "Apocalypse Now", "year": "1979", "director": "Francis Ford Coppola", "tmdb_id": 28},
    {"title": "Non aprite quella porta", "year": "1974", "director": "Tobe Hooper", "tmdb_id": 940},
    {"title": "Psyco", "year": "1960", "director": "Alfred Hitchcock", "tmdb_id": 539},
    {"title": "Zombi", "year": "1978", "director": "George A. Romero", "tmdb_id": 923},
    {"title": "Dellamorte Dellamore", "year": "1994", "director": "Michele Soavi", "tmdb_id": 21590},
    {"title": "Profondo Rosso", "year": "1975", "director": "Dario Argento", "tmdb_id": 10982},
    {"title": "Eraserhead", "year": "1977", "director": "David Lynch", "tmdb_id": 985},
    {"title": "Halloween", "year": "1978", "director": "John Carpenter", "tmdb_id": 948},
    {"title": "1997: Fuga da New York", "year": "1981", "director": "John Carpenter", "tmdb_id": 1103},
    {"title": "Grosso guaio a China Town", "year": "1986", "director": "John Carpenter", "tmdb_id": 9026},
    {"title": "Il seme della follia", "year": "1994", "director": "John Carpenter", "tmdb_id": 9053},
    {"title": "RoboCop", "year": "1987", "director": "Paul Verhoeven", "tmdb_id": 5996},
    {"title": "Atto di forza", "year": "1990", "director": "Paul Verhoeven", "tmdb_id": 861},
    {"title": "Starship Troopers", "year": "1997", "director": "Paul Verhoeven", "tmdb_id": 563},
    {"title": "The Matrix", "year": "1999", "director": "Wachowskis", "tmdb_id": 603},
    {"title": "Fight Club", "year": "1999", "director": "David Fincher", "tmdb_id": 550},
    {"title": "Seven", "year": "1995", "director": "David Fincher", "tmdb_id": 807},
    {"title": "Zodiac", "year": "2007", "director": "David Fincher", "tmdb_id": 194},
    {"title": "Interstellar", "year": "2014", "director": "Christopher Nolan", "tmdb_id": 157336},
    {"title": "Inception", "year": "2010", "director": "Christopher Nolan", "tmdb_id": 27205},
    {"title": "Whiplash", "year": "2014", "director": "Damien Chazelle", "tmdb_id": 244786},
    {"title": "Joker", "year": "2019", "director": "Todd Phillips", "tmdb_id": 475557},
    {"title": "The Irishman", "year": "2019", "director": "Martin Scorsese", "tmdb_id": 398978},
    {"title": "Quei bravi ragazzi", "year": "1990", "director": "Martin Scorsese", "tmdb_id": 769},
    {"title": "C'era una volta a... Hollywood", "year": "2019", "director": "Quentin Tarantino", "tmdb_id": 466272},
    {"title": "Bastardi senza gloria", "year": "2009", "director": "Quentin Tarantino", "tmdb_id": 16869},
    {"title": "Django Unchained", "year": "2012", "director": "Quentin Tarantino", "tmdb_id": 68718},
    {"title": "Kill Bill: Volume 1", "year": "2003", "director": "Quentin Tarantino", "tmdb_id": 24},
    {"title": "Le iene", "year": "1992", "director": "Quentin Tarantino", "tmdb_id": 500},
]

FALLBACK_MONOGRAPHS = [
    {
        "videoId": "yhu0BwmsojA",
        "title": "John Carpenter",
        "originalTitle": "MONOGRAFIA - John Carpenter",
        "description": "Monografia dedicata a John Carpenter, il maestro dell'horror e della fantascienza.",
        "thumbnailUrl": "https://img.youtube.com/vi/yhu0BwmsojA/0.jpg"
    },
    {
        "videoId": "8eK-aFjW2y0",
        "title": "David Cronenberg",
        "originalTitle": "MONOGRAFIA - David Cronenberg",
        "description": "Monografia dedicata a David Cronenberg, il re del body horror.",
        "thumbnailUrl": "https://img.youtube.com/vi/8eK-aFjW2y0/0.jpg"
    },
    {
        "videoId": "uY34Qh6KqYI",
        "title": "Stanley Kubrick",
        "originalTitle": "MONOGRAFIA - Stanley Kubrick",
        "description": "Monografia dedicata a Stanley Kubrick, perfezionista assoluto del cinema.",
        "thumbnailUrl": "https://img.youtube.com/vi/uY34Qh6KqYI/0.jpg"
    },
    {
        "videoId": "1v07VpA3cMs",
        "title": "Dario Argento",
        "originalTitle": "MONOGRAFIA - Dario Argento",
        "description": "Monografia dedicata a Dario Argento, il maestro del brivido italiano.",
        "thumbnailUrl": "https://img.youtube.com/vi/1v07VpA3cMs/0.jpg"
    },
    {
        "videoId": "_7z0wQn88bM",
        "title": "David Lynch",
        "originalTitle": "MONOGRAFIA - David Lynch",
        "description": "Monografia dedicata a David Lynch, l'architetto dell'inconscio.",
        "thumbnailUrl": "https://img.youtube.com/vi/_7z0wQn88bM/0.jpg"
    },
    {
        "videoId": "3K-wQ-v5iQ8",
        "title": "George A. Romero",
        "originalTitle": "MONOGRAFIA - George A. Romero",
        "description": "Monografia dedicata a George A. Romero, il padre degli zombie.",
        "thumbnailUrl": "https://img.youtube.com/vi/3K-wQ-v5iQ8/0.jpg"
    }
]

async def search_frusciante_video(title: str, year: str, director: str) -> str | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = "https://www.googleapis.com/youtube/v3/search"
        q = f"Federico Frusciante {title}"
        if year:
            q += f" {year}"
            
        params = {
            "part": "snippet",
            "q": q,
            "key": settings.YOUTUBE_API_KEY,
            "type": "video",
            "maxResults": 15,  # Aumentato per consentire il filtraggio client-side del canale
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
        raw_items = data.get("items", [])
        
        if not raw_items:
            return "none"
            
        # Filtriamo gli items client-side per assicurarci che appartengano al canale di Federico Frusciante
        # Canale ufficiale: UCeiW1AdgyfDyW5wPLjZqH2Q
        frusciante_channel_id = "UCeiW1AdgyfDyW5wPLjZqH2Q"
        items = [
            item for item in raw_items 
            if item["snippet"].get("channelId") == frusciante_channel_id
        ]
        
        if not items:
            # Fallback a tutti i risultati se nessun video appartiene al canale ufficiale
            items = raw_items

        if not year:
            # Se non c'è l'anno, restituiamo il primo risultato per compatibilità
            return items[0]["id"]["videoId"]
            
        # Pulisce e normalizza i titoli per il confronto
        # Rimuove spazi e punteggiatura per un confronto flessibile (es. "old boy" -> "oldboy")
        def normalize(t: str) -> str:
            return re.sub(r'[^a-z0-9]', '', t.lower())
            
        main_title_norm = normalize(title.split(':')[0].split('-')[0].split('–')[0].strip())
        
        fallback_item = None
        for item in items:
            video_title = html.unescape(item["snippet"]["title"]).lower()
            video_title_norm = normalize(video_title)
            video_id = item["id"]["videoId"]
            
            # Estrae tutti gli anni a 4 cifre presenti nel titolo del video
            years_in_title = re.findall(r'\b\d{4}\b', video_title)
            
            # Verifica corrispondenza normalizzata
            title_matches = main_title_norm in video_title_norm
            
            if not title_matches:
                continue
                
            if not years_in_title:
                # Se non ci sono anni nel titolo ma il titolo corrisponde, lo teniamo come fallback
                if fallback_item is None:
                    fallback_item = video_id
                continue
                
            # Se l'anno cercato è presente nel titolo, abbiamo un match esatto!
            if year in years_in_title:
                return video_id
                
        # Se non abbiamo trovato un match esatto ma abbiamo un fallback senza anno nel titolo, lo usiamo
        if fallback_item:
            return fallback_item
            
        # Se tutti i video trovati avevano un anno diverso, non restituiamo nulla
        return "none"

@router.get("/frusciante")
async def get_frusciante_video(
    title: str = Query(..., description="Titolo del film"),
    year: str = Query("", description="Anno di uscita"),
    director: str = Query("", description="Nome del regista")
):
    """Cerca la recensione di Federico Frusciante per un film specifico."""
    result = await get_or_set_cache(
        f"youtube:frusciante:{title}:{year}",
        lambda: search_frusciante_video(title, year, director),
        ttl=86400 * 7, # Cache for 7 days
    )
    if result == "none":
        return None
    return result

# Pool di parole chiave comuni per la ricerca casuale giornaliera
KEYWORDS_POOL = [
    "di", "del", "il", "un", "recensione", "minirece", "regia", 
    "film", "cinema", "anni", "storia", "scelta", "richiesta", 
    "horror", "thriller", "commedia", "fantascienza", "cult"
]

def parse_video_title(title: str):
    # Rimuove prefissi comuni usati nei video di Frusciante
    t = re.sub(r'^(Patreon|Minirece|Minirecensione|Recensione|Monografia)\s*:\s*', '', title, flags=re.IGNORECASE)
    # Pattern standard: "Titolo" (Anno) di Nome Regista
    match = re.search(r'(?:"|“|”)?([^"“”…\(\)]+?)(?:"|“|”)?\s*\((\d{4})\)\s+di\s+([A-Za-zÀ-ÿ\s\.\-\&\’\']+)', t, flags=re.IGNORECASE)
    if match:
        movie_title = match.group(1).strip()
        year = match.group(2).strip()
        director = match.group(3).split('-')[0].split('–')[0].strip()
        return movie_title, year, director
    return None

@router.get("/review-of-the-day")
async def get_review_of_the_day():
    """Ritorna la recensione di Federico Frusciante del giorno, estratta in modo completamente
    dinamico e casuale dal suo canale YouTube ufficiale."""
    today = datetime.date.today()
    cache_key = f"youtube:review_of_the_day:{today}"
    
    async def fetch_review():
        # Usa il seed del giorno per garantire che il film rimanga lo stesso per tutta la giornata
        today_seed = today.year * 1000 + today.timetuple().tm_yday
        random.seed(today_seed)
        
        # 1. Tenta la ricerca dinamica da YouTube
        async with httpx.AsyncClient(timeout=10.0) as client:
            items = []
            # Prova fino a 5 parole chiave diverse usando il seed deterministico
            shuffled_keywords = list(KEYWORDS_POOL)
            random.shuffle(shuffled_keywords)
            
            for keyword in shuffled_keywords[:5]:
                try:
                    url = "https://www.googleapis.com/youtube/v3/search"
                    # Rimuoviamo channelId e aggiungiamo "Federico Frusciante" alla query di ricerca
                    params = {
                        "part": "snippet",
                        "q": f"Federico Frusciante {keyword}",
                        "key": settings.YOUTUBE_API_KEY,
                        "type": "video",
                        "maxResults": 50,
                        "order": "relevance"
                    }
                    res = await client.get(url, params=params)
                    if res.status_code == 200:
                        raw_items = res.json().get("items", [])
                        # Filtriamo client-side per channelId del canale ufficiale di Federico Frusciante
                        frusciante_channel_id = "UCeiW1AdgyfDyW5wPLjZqH2Q"
                        items = [
                            item for item in raw_items 
                            if item["snippet"].get("channelId") == frusciante_channel_id
                        ]
                        if items:
                            break
                except Exception as e:
                    print(f"Errore ricerca YouTube per keyword '{keyword}': {e}")
                    
            # 2. Se abbiamo dei video, cerchiamo il primo che si adatta al pattern e ha riscontro su TMDB
            if items:
                random.shuffle(items) # Mescola i video trovati usando il seed del giorno
                
                for item in items:
                    title = item["snippet"]["title"]
                    video_id = item["id"]["videoId"]
                    parsed = parse_video_title(title)
                    
                    if parsed:
                        m_title, m_year, m_director = parsed
                        
                        # Cerca su TMDB per avere poster, backdrop e ID preciso
                        try:
                            tmdb_url = "https://api.themoviedb.org/3/search/movie"
                            res_tmdb = await client.get(tmdb_url, params={
                                "api_key": settings.TMDB_API_KEY,
                                "query": m_title,
                                "primary_release_year": m_year,  # Filtro stretto sull'anno per evitare discrepanze
                                "language": "it-IT"
                            })
                            results = res_tmdb.json().get("results", [])
                            if not results:
                                # Riprova senza l'anno per tolleranza
                                res_tmdb = await client.get(tmdb_url, params={
                                    "api_key": settings.TMDB_API_KEY,
                                    "query": m_title,
                                    "language": "it-IT"
                                })
                                results = res_tmdb.json().get("results", [])
                                
                            if results:
                                # Cerca la corrispondenza esatta dell'anno per evitare falsi positivi (es. Old 2021 vs Old Boy 2003)
                                matched_movie = None
                                for movie in results:
                                    release_date = movie.get("release_date", "")
                                    if release_date and m_year in release_date:
                                        matched_movie = movie
                                        break
                                
                                # Se non c'è corrispondenza esatta dell'anno, usiamo il primo risultato come fallback
                                if not matched_movie:
                                    matched_movie = results[0]
                                    
                                return {
                                    "tmdb_id": matched_movie["id"],
                                    "title": matched_movie["title"],
                                    "poster_path": matched_movie.get("poster_path"),
                                    "backdrop_path": matched_movie.get("backdrop_path"),
                                    "year": m_year,
                                    "director": m_director,
                                    "video_id": video_id
                                }
                        except Exception as e:
                            print(f"Errore ricerca TMDB per '{m_title}': {e}")
                            
        # 3. FALLBACK: Se non abbiamo trovato nulla (es. limiti API o nessun match), usiamo il pool statico
        today_idx = random.randint(0, len(MOVIES_POOL) - 1)
        movie = MOVIES_POOL[today_idx]
        
        # Arricchisce i dettagli da TMDB
        try:
            tmdb_data = await get_or_set_cache(
                f"tmdb:movie:{movie['tmdb_id']}",
                lambda: fetch_from_tmdb(f"/movie/{movie['tmdb_id']}"),
                ttl=86400 * 7
            )
        except Exception:
            tmdb_data = {}
            
        video_id = await get_or_set_cache(
            f"youtube:frusciante:{movie['title']}:{movie['year']}",
            lambda: search_frusciante_video(movie['title'], movie['year'], movie['director']),
            ttl=86400 * 7
        )
        if video_id == "none":
            video_id = None
            
        return {
            "tmdb_id": movie["tmdb_id"],
            "title": tmdb_data.get("title") or movie["title"],
            "poster_path": tmdb_data.get("poster_path"),
            "backdrop_path": tmdb_data.get("backdrop_path"),
            "year": movie["year"],
            "director": movie["director"],
            "video_id": video_id
        }

    # Memorizza in cache l'intera risposta giornaliera per 24 ore
    return await get_or_set_cache(cache_key, fetch_review, ttl=86400)

async def fetch_playlist_items(playlist_id: str) -> list:
    async with httpx.AsyncClient(timeout=10.0) as client:
        url = "https://www.googleapis.com/youtube/v3/playlistItems"
        params = {
            "part": "snippet",
            "playlistId": playlist_id,
            "maxResults": 50,
            "key": settings.YOUTUBE_API_KEY,
        }
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", [])
        
        videos = []
        for item in items:
            snippet = item.get("snippet", {})
            video_id = snippet.get("resourceId", {}).get("videoId")
            title = snippet.get("title", "")
            description = snippet.get("description", "")
            thumbnails = snippet.get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxres", {}).get("url") or
                thumbnails.get("standard", {}).get("url") or
                thumbnails.get("high", {}).get("url") or
                thumbnails.get("medium", {}).get("url") or
                thumbnails.get("default", {}).get("url")
            )
            
            clean_title = clean_author_name(title)
            
            videos.append({
                "videoId": video_id,
                "title": clean_title,
                "originalTitle": title,
                "description": description,
                "thumbnailUrl": thumbnail_url,
            })
        return videos

def clean_author_name(title: str) -> str:
    # 1. Rimuovi prefissi insensibili al maiuscolo/minuscolo
    t = re.sub(
        r'^(le\s+recensioni|le\s+monografie|le\s+monografia|la\s+monografia)\s+(di|del|al|dal)\s+frusciante\s*[:\-]\s*',
        '',
        title,
        flags=re.IGNORECASE
    )
    t = re.sub(
        r'^(le\s+recensioni|le\s+monografie|le\s+monografia|la\s+monografia)\s+(di|del|al|dal)\s+frusciante\s+',
        '',
        t,
        flags=re.IGNORECASE
    )
    
    # Casi speciali
    if "mamoru oshii" in title.lower():
        return "Mamoru Oshii"
    if "lars von trier" in title.lower():
        return "Lars Von Trier"
        
    # Rimuovi indicazioni tra parentesi
    t = re.sub(r'\s*\([^)]*\)', '', t)
    
    # Rimuovi indicazioni di parte
    t = re.sub(r'\s*-\s*parte\s+\d+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*parte\s+\d+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*pt\.?\s*[ivx\d]+', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*1a\s+parte', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*2a\s+parte', '', t, flags=re.IGNORECASE)
    
    # Rimuovi date o mesi
    t = re.sub(r'\s*\b(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)\s+\d{4}\b', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\b\d{4}\b', '', t)
    
    return t.strip()

async def find_person_tmdb_id(name: str) -> int | None:
    clean_name = clean_author_name(name)
    
    NAME_OVERRIDES = {
        # Registi in coppia
        "coen bros": "Joel Coen",
        "fratelli coen": "Joel Coen",
        "sorelle wachowski": "Lana Wachowski",
        "wachowski sisters": "Lana Wachowski",
        "wachowskis": "Lana Wachowski",
        "the wachowskis": "Lana Wachowski",
        "fratelli dardenne": "Jean-Pierre Dardenne",
        "fratelli russo": "Anthony Russo",
        "russo brothers": "Anthony Russo",
        "fratelli taviani": "Paolo Taviani",
        # Cognomi singoli o nomi abbreviati
        "tarantino": "Quentin Tarantino",
        "carpenter": "John Carpenter",
        "landis": "John Landis",
        "nolan": "Christopher Nolan",
        "burton": "Tim Burton",
        "fulci": "Lucio Fulci",
        "raimi": "Sam Raimi",
        "zombie": "Rob Zombie",
        "cronenberg": "David Cronenberg",
        "argento": "Dario Argento",
        "leone": "Sergio Leone",
        "yuzna e gordon": "Brian Yuzna"
    }
    
    search_query = NAME_OVERRIDES.get(clean_name.lower(), clean_name)
    
    if not search_query or search_query.lower() in ["scifi 2000"]:
        return None
        
    try:
        # Cerca la persona su TMDB
        result = await get_or_set_cache(
            f"tmdb:search_person:{search_query}",
            lambda: fetch_from_tmdb("/search/person", {"query": search_query}),
            ttl=86400 * 30 # Cache per 30 giorni
        )
        results = result.get("results", [])
        if results:
            return results[0]["id"]
    except Exception as e:
        print(f"Errore ricerca persona {search_query} su TMDB: {e}")
    return None

@router.get("/monograph-of-the-week")
async def get_monograph_of_the_week():
    """Ritorna la monografia della settimana, deterministica dalla playlist di YouTube."""
    playlist_id = "PLEeHU6DkJp3B-djwCkfBjMkQIIMfMuuAp"
    
    try:
        videos = await get_or_set_cache(
            f"youtube:playlist:{playlist_id}",
            lambda: fetch_playlist_items(playlist_id),
            ttl=86400 * 7 # Cache per 7 giorni
        )
    except Exception as e:
        print(f"Errore caricamento playlist YouTube: {e}. Utilizzo fallback.")
        videos = FALLBACK_MONOGRAPHS
        
    if not videos:
        videos = FALLBACK_MONOGRAPHS
        
    today = datetime.date.today()
    year, week_num, _ = today.isocalendar()
    week_seed = year * 100 + week_num
    
    random.seed(week_seed)
    chosen_idx = random.randint(0, len(videos) - 1)
    chosen = videos[chosen_idx]
    
    # Trova l'ID TMDB dell'autore
    person_id = await find_person_tmdb_id(chosen["title"])
    
    return {
        **chosen,
        "tmdb_person_id": person_id
    }

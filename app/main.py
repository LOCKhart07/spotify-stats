import os
import logging
from functools import wraps
from typing import List, Callable

from dotenv import load_dotenv
from fastapi import FastAPI, Query, APIRouter, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import redis

from .service import (
    fetch_spotify_top_artists,
    fetch_spotify_top_tracks,
    fetch_spotify_top_genres,
)
from .models import Track, Artist, PongResponse, Genre

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 1 day in seconds
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

app = FastAPI(title="Spotify Stats API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://portfolio.lockhart.in",
        "https://portfolio-jenslee.netlify.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


router = APIRouter(prefix="/spotify-stats/api")


def redis_cache(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Get parameters for cache key
            limit = kwargs.get("limit", 10)
            page = kwargs.get("page", 1)
            time_range = kwargs.get("period", "short_term")

            # Create a unique cache key based on function name and parameters
            cache_key = f"{func.__name__}_{limit}_{page}_{time_range}"

            cached_data = redis_client.get(cache_key)
            if cached_data:
                return eval(cached_data)

            result = func(*args, **kwargs)

            # Only cache if result is not None or an empty list
            if result is not None and result != []:
                redis_client.setex(cache_key, CACHE_TTL, str(result))

            return result
        except Exception as e:
            logger.error(f"Error in redis_cache: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    return wrapper


def verify_authorization(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            authorization = kwargs.get("authorization")
            if not authorization:
                raise HTTPException(
                    status_code=401, detail="Authorization header is required"
                )
            if authorization != f"Bearer {BEARER_TOKEN}":
                raise HTTPException(
                    status_code=403, detail="Invalid authorization token"
                )
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in verify_authorization: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error")

    return wrapper


@router.get("/top-tracks", response_model=List[Track])
@verify_authorization
@redis_cache
def top_tracks(
    limit: int = Query(10, ge=1, le=50),
    page: int = Query(1, ge=1),
    time_range: str = Query("short_term", regex="^(short_term|medium_term|long_term)$"),
    authorization: str = Header(None),
):
    try:
        return fetch_spotify_top_tracks(limit=limit, time_range=time_range, page=page)
    except Exception as e:
        logger.error(f"Error fetching top tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch top tracks")


@router.get("/top-artists", response_model=List[Artist])
@verify_authorization
@redis_cache
def top_artists(
    limit: int = Query(10, ge=1, le=50),
    page: int = Query(1, ge=1),
    time_range: str = Query("short_term", regex="^(short_term|medium_term|long_term)$"),
    authorization: str = Header(None),
):
    try:
        return fetch_spotify_top_artists(limit=limit, time_range=time_range, page=page)
    except Exception as e:
        logger.error(f"Error fetching top artists: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch top artists")


@router.get("/top-genres", response_model=List[Genre])
@verify_authorization
@redis_cache
def top_genres(
    time_range: str = Query("short_term", regex="^(short_term|medium_term|long_term)$"),
    authorization: str = Header(None),
):
    try:
        return fetch_spotify_top_genres(time_range=time_range)
    except Exception as e:
        logger.error(f"Error fetching top tracks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch top tracks")


@app.get("/ping", response_model=PongResponse)
def ping():
    return PongResponse(message="pong")


app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)

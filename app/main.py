import redis
import os
from fastapi import FastAPI, Query, APIRouter, HTTPException, Header
from typing import List, Callable
from functools import wraps

from dotenv import load_dotenv
from .service import (
    fetch_lastfm_top_tracks,
    fetch_lastfm_top_artists,
    fetch_lastfm_top_tags,
)
from .models import (
    Track,
    Artist,
    Tag,
    PongResponse,
)

# Load environment variables from .env file
load_dotenv()

# Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 1 day in seconds

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
# Redis Setup
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# FastAPI App
app = FastAPI()

# Create a router
router = APIRouter(prefix="/spotify-stats/api")


def redis_cache(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get parameters for cache key
        limit = kwargs.get("limit", 10)
        page = kwargs.get("page", 1)
        period = kwargs.get("period", "overall")

        # Create a unique cache key based on function name and parameters
        cache_key = f"{func.__name__}_{limit}_{page}_{period}"

        cached_data = redis_client.get(cache_key)
        if cached_data:
            return eval(cached_data)

        result = func(*args, **kwargs)
        redis_client.setex(cache_key, CACHE_TTL, str(result))
        return result

    return wrapper


def verify_authorization(authorization: str):
    if authorization != f"Bearer {BEARER_TOKEN}":
        raise HTTPException(status_code=403, detail="Unauthorized")


@router.get("/top-tracks", response_model=List[Track])
@redis_cache
def top_tracks(
    limit: int = Query(10),
    page: int = Query(1),
    period: str = Query("overall"),
    authorization: str = Header(None),
):
    verify_authorization(authorization)
    return fetch_lastfm_top_tracks(limit=limit, period=period, page=page)


@router.get(
    "/top-artists", response_model=List[Artist]
)  # Changed endpoint and response model
@redis_cache
def top_artists(  # Renamed function
    limit: int = Query(10),
    page: int = Query(1),
    period: str = Query("overall"),
    authorization: str = Header(None),
):
    verify_authorization(authorization)
    offset = (page - 1) * limit  # Calculate the offset for pagination
    return {
        "artists": fetch_lastfm_top_artists(limit=limit, period=period, page=page)
    }  # Changed to fetch artists


@router.get("/top-tags", response_model=List[Tag])
@redis_cache
def top_tags(
    limit: int = Query(10),
    page: int = Query(1),
    period: str = Query("overall"),
    authorization: str = Header(None),
):
    verify_authorization(authorization)
    return fetch_lastfm_top_tags(limit=limit, period=period, page=page)


# Keep the ping endpoint outside the router
@app.get("/ping", response_model=PongResponse)
def ping():
    return PongResponse(message="pong")


# Include the router in the main app
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)

import redis
import os
from fastapi import FastAPI
from typing import List
import os

from dotenv import load_dotenv
from service import (
    fetch_lastfm_top_tracks,
    fetch_lastfm_top_genres,
)  # Importing functions from the new service module
from models import (
    Track,
    GenreResponse,
    PongResponse,
)  # Importing models from the new models module

# Load environment variables from .env file
load_dotenv()

# Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 1 day in seconds
# Redis Setup
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# FastAPI App
app = FastAPI()
from fastapi import Query


@app.get("/top-tracks", response_model=List[Track])
def top_tracks(limit: int = Query(10)):
    cache_key = f"top_tracks_{limit}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return eval(cached_data)

    tracks = fetch_lastfm_top_tracks(limit=limit)
    redis_client.setex(cache_key, CACHE_TTL, str(tracks))
    return tracks


@app.get("/top-genres", response_model=GenreResponse)
def top_genres(limit: int = Query(10)):
    cache_key = f"top_genres_{limit}"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return {"genres": eval(cached_data)}

    genres = fetch_lastfm_top_genres(limit=limit)
    redis_client.setex(cache_key, CACHE_TTL, str(genres))
    return {"genres": genres}


@app.get("/ping", response_model=PongResponse)
def ping():
    return PongResponse(message="pong")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)

import redis
import requests
import time
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List
import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 1 day in seconds
SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
# Redis Setup
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# FastAPI App
app = FastAPI()


class Track(BaseModel):
    name: str
    artist: str
    url: str


class GenreResponse(BaseModel):
    genres: List[str]


def get_spotify_access_token():
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    print(response.json())
    return response.json().get("access_token")


def fetch_spotify_top_tracks():
    access_token = get_spotify_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/top/tracks?time_range=short_term&limit=10"
    response = requests.get(url, headers=headers)
    data = response.json()
    print(data)
    tracks = [
        {
            "name": t["name"],
            "artist": t["artists"][0]["name"],
            "url": t["external_urls"]["spotify"],
        }
        for t in data.get("items", [])
    ]
    return tracks


def fetch_spotify_top_genres():
    access_token = get_spotify_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}
    url = "https://api.spotify.com/v1/me/top/artists?time_range=short_term&limit=10"
    response = requests.get(url, headers=headers)
    data = response.json()
    genres = list(
        set(
            genre
            for artist in data.get("items", [])
            for genre in artist.get("genres", [])
        )
    )
    return genres


@app.get("/top-tracks", response_model=List[Track])
def top_tracks():
    cache_key = "top_tracks"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return eval(cached_data)

    tracks = fetch_spotify_top_tracks()
    redis_client.setex(cache_key, CACHE_TTL, str(tracks))
    return tracks


@app.get("/top-genres", response_model=GenreResponse)
def top_genres():
    cache_key = "top_genres"
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return {"genres": eval(cached_data)}

    genres = fetch_spotify_top_genres()
    redis_client.setex(cache_key, CACHE_TTL, str(genres))
    return {"genres": genres}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

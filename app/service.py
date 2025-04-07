import requests
import os
from typing import List
from .models import Track, Artist, Genre

from dotenv import load_dotenv
import redis

load_dotenv()

SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


# Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400))  # 1 day in seconds

BEARER_TOKEN = os.getenv("BEARER_TOKEN")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def get_spotify_access_token():
    # Check if the access token is cached
    cached_token = redis_client.get("spotify_access_token")
    if cached_token:
        return cached_token

    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to get Spotify access token: {response.json()}")

    access_token = response.json().get("access_token")

    # Cache the access token with a TTL (e.g., 3600 seconds)
    redis_client.setex("spotify_access_token", 3500, access_token)

    return access_token


def fetch_spotify_data(endpoint: str, time_range: str, limit: int, page: int):
    access_token = get_spotify_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    params = {
        "time_range": time_range,
        "limit": limit,
        "offset": (page - 1) * limit,
    }
    url = f"https://api.spotify.com/v1/me/top/{endpoint}"
    response = requests.get(url, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data from Spotify: {response.json()}")
    return response.json()


def fetch_spotify_top_tracks(
    limit: int, time_range: str = "short_term", page: int = 1
) -> List[Track]:
    data = fetch_spotify_data("tracks", time_range, limit, page)
    tracks = [
        {
            "name": t["name"],
            "artist": t["artists"][0]["name"],
            "url": t["external_urls"]["spotify"],
            "image": t["album"]["images"][1]["url"] if t["album"]["images"] else None,
        }
        for t in data.get("items", [])
    ]
    return tracks


def fetch_spotify_top_artists(
    limit: int, time_range: str = "short_term", page: int = 1
) -> List[Artist]:
    data = fetch_spotify_data("artists", time_range, limit, page)
    artists = [
        {
            "name": artist["name"],
            "url": artist["external_urls"]["spotify"],
            "image": artist["images"][1]["url"] if artist["images"] else None,
            "genres": artist.get("genres", []),
        }
        for artist in data.get("items", [])
    ]
    return artists


def fetch_spotify_top_genres(
    time_range: str = "short_term",
) -> List[Genre]:
    data = fetch_spotify_data("artists", time_range, 50, 1)
    genres = []
    genre_count = {}
    for artist in data.get("items", []):
        for genre in artist.get("genres", []):
            if genre in genre_count:
                genre_count[genre] += 1
            else:
                genre_count[genre] = 1

    # Sort genres by count, maintaining the current order in case of a tie
    sorted_genres = sorted(
        genre_count.items(), key=lambda x: (-x[1], list(genre_count.keys()).index(x[0]))
    )

    genres = [{"name": genre} for genre, _ in sorted_genres]
    return genres

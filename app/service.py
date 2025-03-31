import requests
import os
from typing import List
from .models import Track, Artist

from dotenv import load_dotenv

load_dotenv()

SPOTIFY_REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")


def get_spotify_access_token():
    url = "https://accounts.spotify.com/api/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": SPOTIFY_REFRESH_TOKEN,
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")


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
    return response.json()


def fetch_spotify_top_tracks(
    limit: int, time_range: str = "short_term", page: int = 1
) -> List[Track]:
    data = fetch_spotify_data("tracks", time_range, limit, page)
    print(data)
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
    genres = list(
        set(
            genre
            for artist in data.get("items", [])
            for genre in artist.get("genres", [])
        )
    )
    return genres

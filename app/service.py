import requests
import os

from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")


def fetch_lastfm_top_tracks(limit: int):
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.gettoptracks",
        "user": LASTFM_USERNAME,  # Use the provided username
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": limit,  # Use the provided limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    tracks = [
        {
            "name": t["name"],
            "artist": t["artist"]["name"],
            "url": t["url"],
        }
        for t in data.get("toptracks", {}).get("track", [])
    ]
    return tracks


def fetch_lastfm_top_genres(limit: int):
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "user.gettopartists",
        "user": LASTFM_USERNAME,  # Use the provided username
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": limit,  # Use the provided limit
    }
    response = requests.get(url, params=params)
    data = response.json()
    genres = list(
        set(
            genre
            for artist in data.get("topartists", {}).get("artist", [])
            for genre in artist.get("tags", {}).get("tag", [])
        )
    )
    return genres

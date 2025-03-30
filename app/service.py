import requests
import os

from dotenv import load_dotenv

load_dotenv()

LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")
LASTFM_USERNAME = os.getenv("LASTFM_USERNAME")

BASE_URL = "http://ws.audioscrobbler.com/2.0/"
HEADERS = {
    "User-Agent": "SpotifyStatsCache/1.0 (https://lockhart.in/spotify-stats.api)"
}


def fetch_lastfm_data(method: str, limit: int, period: str = "overall", page: int = 1):
    params = {
        "method": method,
        "user": LASTFM_USERNAME,
        "api_key": LASTFM_API_KEY,
        "format": "json",
        "limit": limit,
        "period": period,
        "page": page,
    }
    response = requests.get(BASE_URL, params=params, headers=HEADERS)
    return response.json()


def fetch_lastfm_top_tracks(limit: int, period: str = "overall", page: int = 1):
    data = fetch_lastfm_data("user.gettoptracks", limit, period, page)
    tracks = [
        {
            "name": t["name"],
            "artist": t["artist"]["name"],
            "url": t["url"],
        }
        for t in data.get("toptracks", {}).get("track", [])
    ]
    return tracks


def fetch_lastfm_top_artists(limit: int, period: str = "overall", page: int = 1):
    data = fetch_lastfm_data("user.gettopartists", limit, period, page)
    artists = [
        {
            "name": artist["name"],
            "url": artist["url"],
            "image": artist.get("image", [{}])[0].get("#text", ""),
        }
        for artist in data.get("topartists", {}).get("artist", [])
    ]
    return artists


def fetch_lastfm_top_tags(limit: int, period: str = "overall", page: int = 1):
    data = fetch_lastfm_data("user.gettoptags", limit, period, page)
    tags = [tag["name"] for tag in data.get("toptags", {}).get("tag", [])]
    return tags

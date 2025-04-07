from pydantic import BaseModel
from typing import List, Optional


class Track(BaseModel):
    name: str
    artist: str
    url: str
    image: Optional[str] = None


class Genre(BaseModel):
    name: str


class Artist(BaseModel):
    name: str
    url: str
    image: Optional[str] = None
    genres: List[str] = []


class PongResponse(BaseModel):
    message: str

from pydantic import BaseModel
from typing import List, Optional


class Track(BaseModel):
    name: str
    artist: str
    url: str
    image: Optional[str] = None


class Artist(BaseModel):
    name: str
    url: str
    image: str  # Optional image URL


class PongResponse(BaseModel):
    message: str

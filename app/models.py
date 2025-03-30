from pydantic import BaseModel
from typing import List


class Track(BaseModel):
    name: str
    artist: str
    url: str


class Artist(BaseModel):
    name: str
    url: str
    image: str  # Optional image URL


class Tag(BaseModel):
    name: str


class PongResponse(BaseModel):
    message: str

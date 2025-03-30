from pydantic import BaseModel
from typing import List


class Track(BaseModel):
    name: str
    artist: str
    url: str


class GenreResponse(BaseModel):
    genres: List[str]


class PongResponse(BaseModel):
    message: str

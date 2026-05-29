from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class MovieLogCreate(BaseModel):
    tmdb_id: int
    watched_date: date
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    review: Optional[str] = ""
    liked: Optional[bool] = False
    is_rewatch: Optional[bool] = False


class MovieLogUpdate(BaseModel):
    watched_date: Optional[date] = None
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    review: Optional[str] = None
    liked: Optional[bool] = None
    is_rewatch: Optional[bool] = None
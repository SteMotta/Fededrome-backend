from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CustomListCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    is_public: Optional[bool] = False


class CustomListUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None


class CustomListResponse(BaseModel):
    id: int
    user_id: str
    name: str
    description: str
    is_public: bool = False
    created_at: datetime
    updated_at: datetime


class CustomListMovieAdd(BaseModel):
    tmdb_id: int

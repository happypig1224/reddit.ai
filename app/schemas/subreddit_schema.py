"""
Subreddit DTO & VO Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class SubredditVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    badge: str
    minKarma: int
    dailyLimit: int
    todaySent: int
    isEnabled: bool
    description: str


class SubredditCreateDTO(BaseModel):
    name: str = Field(..., min_length=2, max_length=64)
    badge: str = Field("新手友好", max_length=32)
    minKarma: int = Field(0, ge=0)
    dailyLimit: int = Field(2, ge=1, le=10)
    description: str = Field("", max_length=255)

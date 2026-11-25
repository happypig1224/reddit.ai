"""
Template DTO & VO Schemas
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class TemplateVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tone: str
    templateText: str
    isActive: bool
    usageCount: int
    lastUsedAt: Optional[str] = None
    isCoolingDown: bool = False


class TemplateCreateDTO(BaseModel):
    tone: str = Field(..., max_length=32)
    templateText: str = Field(..., min_length=8, max_length=2000)

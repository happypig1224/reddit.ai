"""
Risk Control DTO & VO Schemas
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class RiskSettingsVO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    minDelayMinutes: int
    maxDelayMinutes: int
    maxDailyCommentsPerAccount: int
    maxDailyCommentsPerSub: int
    circuitBreakerActive: bool
    circuitBreakerReason: Optional[str] = None
    sensitiveKeywords: List[str]


class RiskSettingsUpdateDTO(BaseModel):
    minDelayMinutes: int = Field(..., ge=1, le=60)
    maxDelayMinutes: int = Field(..., ge=2, le=120)
    maxDailyCommentsPerAccount: int = Field(..., ge=1, le=20)
    maxDailyCommentsPerSub: int = Field(..., ge=1, le=10)
    sensitiveKeywords: List[str] = Field(default_factory=list)


class CircuitBreakerDTO(BaseModel):
    action: str = Field(..., pattern="^(TRIP|RESET)$")
    reason: Optional[str] = Field(None, max_length=255)

"""
Risk Setting Model
"""

from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import Integer, Boolean, String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class RiskSetting(Base):
    __tablename__ = "risk_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    min_delay_minutes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_delay_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_daily_comments_per_account: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_daily_comments_per_sub: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    circuit_breaker_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    circuit_breaker_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sensitive_keywords: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


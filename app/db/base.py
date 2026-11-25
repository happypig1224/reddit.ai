"""
SQLAlchemy 2.0 Base Class
"""

from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from app.core.config import now_utc


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=now_utc, 
        server_default=func.now(), 
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=now_utc, 
        server_default=func.now(), 
        onupdate=func.now(), 
        nullable=False
    )

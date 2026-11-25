"""
Comment Template Model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class CommentTemplate(Base, TimestampMixin):
    __tablename__ = "comment_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tone: Mapped[str] = mapped_column(String(32), default="真诚经验", nullable=False, index=True)
    template_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)


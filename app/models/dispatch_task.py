"""
Dispatch Task Model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config import now_utc
from app.db.base import Base


class DispatchTask(Base):
    __tablename__ = "dispatch_tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("accounts.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    candidate_post_id: Mapped[int] = mapped_column(Integer, nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    final_comment_text: Mapped[str] = mapped_column(Text, nullable=False)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=600, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        Enum("QUEUED", "EXECUTING", "SUCCESS", "FAILED", "CANCELLED", name="dispatch_status_enum"),
        default="QUEUED",
        nullable=False
    )
    reddit_comment_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, nullable=False)

    account = relationship("Account", backref="dispatch_tasks")

"""
Audit Log Model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.core.config import now_utc
from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_username: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subreddit: Mapped[str] = mapped_column(String(64), nullable=False)
    reddit_post_id: Mapped[str] = mapped_column(String(32), nullable=False)
    post_title: Mapped[str] = mapped_column(String(512), nullable=False)
    reddit_comment_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    comment_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    delay_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("SUCCESS", "SKIPPED", "RATE_LIMITED", "INTERCEPTED", "ERROR", name="audit_status_enum"),
        default="SUCCESS",
        nullable=False
    )
    shadowban_status: Mapped[str] = mapped_column(
        Enum("PENDING", "VERIFIED_PUBLIC", "SHADOWBANNED", "DELETED", name="shadowban_status_enum"),
        default="PENDING",
        nullable=False,
        index=True
    )
    shadowban_checked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=now_utc, 
        nullable=False, 
        index=True
    )

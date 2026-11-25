"""
Candidate Post Model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Text, Numeric, Enum, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.config import now_utc
from app.db.base import Base


class CandidatePost(Base):
    __tablename__ = "candidate_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reddit_post_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    subreddit_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    permalink: Mapped[str] = mapped_column(String(512), nullable=False)
    selftext: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    num_comments: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    upvote_ratio: Mapped[float] = mapped_column(Numeric(4, 3), default=1.000, nullable=False)
    match_keyword: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    recommended_score: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    recommended_reason: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    draft_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("PENDING", "APPROVED", "SKIPPED", "DISPATCHED", name="candidate_status_enum"),
        default="PENDING",
        nullable=False
    )
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc, nullable=False)
    post_created_utc: Mapped[datetime] = mapped_column(DateTime, nullable=False)

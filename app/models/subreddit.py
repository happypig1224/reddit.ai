"""
Subreddit Model
"""

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class Subreddit(Base, TimestampMixin):
    __tablename__ = "subreddits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    badge: Mapped[str] = mapped_column(String(32), default="新手友好", nullable=False)
    min_karma: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    today_sent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)


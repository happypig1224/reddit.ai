"""
Account Model
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin
from app.core.crypto import encrypt_secret, decrypt_secret


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(String(64), nullable=False)
    _client_secret: Mapped[str] = mapped_column("client_secret", String(128), nullable=False)

    stage: Mapped[str] = mapped_column(
        Enum("STAGE_1", "STAGE_2", "STAGE_3", "STAGE_4", name="account_stage_enum"),
        default="STAGE_2",
        nullable=False
    )
    created_days_ago: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    comment_karma: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    link_karma: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_sent_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_limit: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    proxy_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_cooling_down: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cooldown_until: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(
        Enum("HEALTHY", "RATE_LIMITED", "RESTRICTED", "BANNED", name="account_status_enum"),
        default="HEALTHY",
        nullable=False,
        index=True
    )

    @property
    def client_secret(self) -> str:
        return decrypt_secret(self._client_secret)

    @client_secret.setter
    def client_secret(self, raw_secret: str) -> None:
        self._client_secret = encrypt_secret(raw_secret)


"""
Application Core Configuration
Using Pydantic Settings
"""

import os
from typing import List
from datetime import datetime, timezone
from pydantic_settings import BaseSettings


def now_utc() -> datetime:
    """获取标准 UTC 时间 (去除 tzinfo 兼容 MySQL DATETIME 物理列)"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Reddit Karma Pilot Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # 数据库配置
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "root")
    DB_NAME: str = os.getenv("DB_NAME", "reddit_karma_pilot")

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"

    # 服务运行端口 (设为 8001 避免与本地其它项目如 8000 端口产生物理冲突)
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", "8001"))
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    # 对称加密密钥 (Fernet / AES-256)
    # 生产环境必须由环境变量 ENCRYPTION_SECRET_KEY 提供
    ENCRYPTION_SECRET_KEY: str = os.getenv(
        "ENCRYPTION_SECRET_KEY", 
        "UjZfdm5VUk9zYmF2WmxSZlFfTjFwQzNScWRyM2FzZGY="  # 32-byte urlsafe base64 default for dev
    )


settings = Settings()

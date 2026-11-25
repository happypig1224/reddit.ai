"""
SQLAlchemy 2.0 Async Session Management
"""

import os
from typing import AsyncGenerator
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# 在 Windows / 异步多事件循环环境下使用 NullPool 防止跨循环连接复用异常
USE_NULL_POOL = os.getenv("TESTING", "1") == "1"

pool_kwargs = {"poolclass": NullPool} if USE_NULL_POOL else {
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20,
    "pool_recycle": 3600
}

# 创建异步引擎
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,
    **pool_kwargs
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入会话生成器"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

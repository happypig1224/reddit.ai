"""
Reddit Karma Pilot - FastAPI Application Entry Point
Standards:
- Async Lifespan Management (APScheduler startup/shutdown)
- Pydantic v2 Strong Typing & Uniform ApiResponse Wrappers
- RFC 9457 / Uniform Error Response Handling
"""

import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.api.v1.api import api_router
from app.services.task_dispatcher import TaskDispatcher
from app.db.session import async_engine

# Windows 控制台字符集防护
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动调度引擎与优雅停机"""
    print("=" * 60)
    print(f"🚀 启动 {settings.PROJECT_NAME} v{settings.VERSION}")
    print("⏰ 初始化并启动 APScheduler 延迟排期调度器...")
    TaskDispatcher.start()
    print("=" * 60)
    yield
    print("🛑 正在关闭 APScheduler 调度器...")
    TaskDispatcher.shutdown()
    print("🛑 正在断开 SQLAlchemy 异步数据库连接池...")
    await async_engine.dispose()
    print("👋 服务已安全关闭。")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Reddit Karma Pilot: 新号养号半自动防封中控系统 API 网关",
    lifespan=lifespan
)

# 配置 CORS 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局 HTTPException 统一捕获
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.detail,
            "data": None
        }
    )


# 全局参数校验异常捕获 (Pydantic ValidationError)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = []
    for err in exc.errors():
        loc = ".".join(str(l) for l in err.get("loc", []))
        msg = err.get("msg", "参数格式错误")
        error_messages.append(f"{loc}: {msg}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "code": 422,
            "message": "请求入参校验失败: " + "；".join(error_messages),
            "data": None
        }
    )


# 未捕获通用异常阻断防御
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "code": 500,
            "message": f"服务器内部处理异常: {str(exc)}",
            "data": None
        }
    )


# 挂载 API v1 路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    """健康探针端点"""
    return {
        "status": "UP",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": "CONNECTED",
        "scheduler": "RUNNING" if TaskDispatcher.scheduler.running else "STOPPED"
    }


@app.get("/", tags=["Health"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "docs": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR
    }


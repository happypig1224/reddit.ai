"""
API v1 Router Registration
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    workbench,
    accounts,
    subreddits,
    templates,
    risk_control,
    logs
)

api_router = APIRouter()

api_router.include_router(workbench.router, prefix="/workbench", tags=["Workbench"])
api_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(subreddits.router, prefix="/subreddits", tags=["Subreddits"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(risk_control.router, prefix="/risk-control", tags=["Risk Control"])
api_router.include_router(logs.router, prefix="/logs", tags=["Logs"])


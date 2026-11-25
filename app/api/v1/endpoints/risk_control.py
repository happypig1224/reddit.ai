"""
Risk Control Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import now_utc
from app.db.session import get_db
from app.models.risk_setting import RiskSetting
from app.schemas.response import ApiResponse
from app.schemas.risk_schema import RiskSettingsVO, RiskSettingsUpdateDTO, CircuitBreakerDTO

router = APIRouter()


@router.get("/settings", response_model=ApiResponse[RiskSettingsVO])
async def get_risk_settings(db: AsyncSession = Depends(get_db)):
    """获取风控与 429 熔断全局配置"""
    res = await db.execute(select(RiskSetting).where(RiskSetting.id == 1))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="风控配置未初始化")

    return ApiResponse.success(data=RiskSettingsVO(
        minDelayMinutes=s.min_delay_minutes,
        maxDelayMinutes=s.max_delay_minutes,
        maxDailyCommentsPerAccount=s.max_daily_comments_per_account,
        maxDailyCommentsPerSub=s.max_daily_comments_per_sub,
        circuitBreakerActive=s.circuit_breaker_active,
        circuitBreakerReason=s.circuit_breaker_reason,
        sensitiveKeywords=s.sensitive_keywords or []
    ))


@router.put("/settings", response_model=ApiResponse[RiskSettingsVO])
async def update_risk_settings(dto: RiskSettingsUpdateDTO, db: AsyncSession = Depends(get_db)):
    """更新风控全局参数与敏感词字典"""
    if dto.minDelayMinutes >= dto.maxDelayMinutes:
        raise HTTPException(status_code=400, detail="最小延迟时间必须小于最大延迟时间")

    res = await db.execute(select(RiskSetting).where(RiskSetting.id == 1))
    s = res.scalar_one_or_none()
    if not s:
        s = RiskSetting(id=1)
        db.add(s)

    s.min_delay_minutes = dto.minDelayMinutes
    s.max_delay_minutes = dto.maxDelayMinutes
    s.max_daily_comments_per_account = dto.maxDailyCommentsPerAccount
    s.max_daily_comments_per_sub = dto.maxDailyCommentsPerSub
    s.sensitive_keywords = dto.sensitiveKeywords
    s.updated_at = now_utc()

    await db.commit()
    await db.refresh(s)

    return ApiResponse.success(
        data=RiskSettingsVO(
            minDelayMinutes=s.min_delay_minutes,
            maxDelayMinutes=s.max_delay_minutes,
            maxDailyCommentsPerAccount=s.max_daily_comments_per_account,
            maxDailyCommentsPerSub=s.max_daily_comments_per_sub,
            circuitBreakerActive=s.circuit_breaker_active,
            circuitBreakerReason=s.circuit_breaker_reason,
            sensitiveKeywords=s.sensitive_keywords or []
        ),
        message="全局风控参数已更新保存"
    )


@router.post("/circuit-breaker", response_model=ApiResponse[RiskSettingsVO])
async def toggle_circuit_breaker(dto: CircuitBreakerDTO, db: AsyncSession = Depends(get_db)):
    """触发 (TRIP) 或解除 (RESET) 429 紧急熔断断路器"""
    res = await db.execute(select(RiskSetting).where(RiskSetting.id == 1))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="风控配置未初始化")

    if dto.action == "TRIP":
        s.circuit_breaker_active = True
        s.circuit_breaker_reason = dto.reason or "人工手动挂起全局外发"
        msg = f"已触发紧急 429 熔断，所有外发调度已挂起！原因: {s.circuit_breaker_reason}"
    else:
        s.circuit_breaker_active = False
        s.circuit_breaker_reason = None
        msg = "熔断保护已解除，恢复正常延迟排期外发"

    s.updated_at = now_utc()
    await db.commit()
    await db.refresh(s)

    return ApiResponse.success(
        data=RiskSettingsVO(
            minDelayMinutes=s.min_delay_minutes,
            maxDelayMinutes=s.max_delay_minutes,
            maxDailyCommentsPerAccount=s.max_daily_comments_per_account,
            maxDailyCommentsPerSub=s.max_daily_comments_per_sub,
            circuitBreakerActive=s.circuit_breaker_active,
            circuitBreakerReason=s.circuit_breaker_reason,
            sensitiveKeywords=s.sensitive_keywords or []
        ),
        message=msg
    )

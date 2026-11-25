"""
Accounts Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import now_utc
from app.db.session import get_db
from app.models.account import Account
from app.schemas.response import ApiResponse
from app.schemas.account_schema import AccountVO, AccountStageUpdateDTO, AccountHandshakeVO, AccountCreateDTO
from app.services.praw_pool import PrawClientPool

router = APIRouter()

STAGE_LIMITS = {
    "STAGE_1": 0,
    "STAGE_2": 5,
    "STAGE_3": 8,
    "STAGE_4": 10
}


@router.get("", response_model=ApiResponse[List[AccountVO]])
async def get_accounts(db: AsyncSession = Depends(get_db)):
    """获取所有养号账号矩阵及其实时运行态"""
    result = await db.execute(select(Account).order_by(Account.id.asc()))
    accounts = result.scalars().all()

    now = now_utc()
    vo_list = []
    for acc in accounts:
        cooldown_sec = 0
        if acc.is_cooling_down and acc.cooldown_until:
            rem = int((acc.cooldown_until - now).total_seconds())
            cooldown_sec = max(rem, 0)

        vo_list.append(AccountVO(
            id=acc.id,
            username=acc.username,
            clientId=acc.client_id,
            stage=acc.stage,
            createdDaysAgo=acc.created_days_ago,
            commentKarma=acc.comment_karma,
            linkKarma=acc.link_karma,
            dailySentCount=acc.daily_sent_count,
            dailyLimit=acc.daily_limit,
            proxyUrl=acc.proxy_url,
            isCoolingDown=acc.is_cooling_down and cooldown_sec > 0,
            cooldownRemainingSeconds=cooldown_sec,
            status=acc.status
        ))
    return ApiResponse.success(data=vo_list)


@router.patch("/{id}/stage", response_model=ApiResponse[AccountVO])
async def update_account_stage(
    id: int, 
    dto: AccountStageUpdateDTO, 
    db: AsyncSession = Depends(get_db)
):
    """切换账号生命周期阶段 (自动同步更新安全发帖硬上限)"""
    res = await db.execute(select(Account).where(Account.id == id))
    acc = res.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")

    acc.stage = dto.stage
    acc.daily_limit = STAGE_LIMITS.get(dto.stage, 5)
    await db.commit()
    await db.refresh(acc)

    return ApiResponse.success(
        data=AccountVO(
            id=acc.id,
            username=acc.username,
            clientId=acc.client_id,
            stage=acc.stage,
            createdDaysAgo=acc.created_days_ago,
            commentKarma=acc.comment_karma,
            linkKarma=acc.link_karma,
            dailySentCount=acc.daily_sent_count,
            dailyLimit=acc.daily_limit,
            proxyUrl=acc.proxy_url,
            isCoolingDown=acc.is_cooling_down,
            cooldownRemainingSeconds=0,
            status=acc.status
        ),
        message=f"账号已平滑切换至 {dto.stage}，每日硬上限调整为 {acc.daily_limit} 条"
    )


@router.post("/{id}/test-handshake", response_model=ApiResponse[AccountHandshakeVO])
async def test_account_handshake(id: int, db: AsyncSession = Depends(get_db)):
    """测试账号 API 连通性与 PRAW OAuth 握手"""
    res = await db.execute(select(Account).where(Account.id == id))
    acc = res.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")

    success, info = PrawClientPool.test_handshake(acc)
    vo = AccountHandshakeVO(
        username=info["username"],
        commentKarma=info["commentKarma"],
        linkKarma=info["linkKarma"],
        isSuspended=info["isSuspended"],
        hasVerifiedEmail=info["hasVerifiedEmail"],
        latencyMs=info["latencyMs"],
        message=info["message"],
        createdDaysAgo=info.get("createdDaysAgo")
    )
    if not success:
        return ApiResponse.error(message=info["message"], data=vo)
    
    # 握手成功时，自动从真实 Reddit API 校准同步账龄与 Karma
    if info.get("createdDaysAgo"):
        acc.created_days_ago = info["createdDaysAgo"]
    acc.comment_karma = info["commentKarma"]
    acc.link_karma = info["linkKarma"]
    await db.commit()
    
    return ApiResponse.success(data=vo, message="握手验证通过")


@router.post("", response_model=ApiResponse[AccountVO])
async def create_account(
    dto: AccountCreateDTO,
    db: AsyncSession = Depends(get_db)
):
    """绑定并录入新的 Reddit 账号凭据 (物理落盘)"""
    formatted_username = dto.username.strip()
    if not formatted_username.startswith("u/"):
        formatted_username = f"u/{formatted_username}"

    # 检查用户名是否已存在
    existing = await db.execute(select(Account).where(Account.username == formatted_username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"账号 {formatted_username} 已存在，不可重复录入")

    # 根据账龄计算阶段
    if dto.createdDaysAgo <= 3:
        stage = "STAGE_1"
        limit = 0
    elif dto.createdDaysAgo <= 7:
        stage = "STAGE_2"
        limit = 5
    elif dto.createdDaysAgo <= 14:
        stage = "STAGE_3"
        limit = 8
    else:
        stage = "STAGE_4"
        limit = 10

    c_id = (dto.clientId or "semi_auto_client").strip()
    c_sec = (dto.clientSecret or "semi_auto_secret").strip()

    new_acc = Account(
        username=formatted_username,
        client_id=c_id,
        stage=stage,
        created_days_ago=dto.createdDaysAgo,
        comment_karma=0,
        link_karma=0,
        daily_sent_count=0,
        daily_limit=limit,
        proxy_url=dto.proxyUrl.strip() if dto.proxyUrl else None,
        is_cooling_down=False,
        status="HEALTHY"
    )
    new_acc.client_secret = c_sec

    db.add(new_acc)
    await db.commit()
    await db.refresh(new_acc)

    return ApiResponse.success(
        data=AccountVO(
            id=new_acc.id,
            username=new_acc.username,
            clientId=new_acc.client_id,
            stage=new_acc.stage,
            createdDaysAgo=new_acc.created_days_ago,
            commentKarma=new_acc.comment_karma,
            linkKarma=new_acc.link_karma,
            dailySentCount=new_acc.daily_sent_count,
            dailyLimit=new_acc.daily_limit,
            proxyUrl=new_acc.proxy_url,
            isCoolingDown=False,
            cooldownRemainingSeconds=0,
            status=new_acc.status
        ),
        message="Reddit 账号绑定成功"
    )


@router.delete("/{id}", response_model=ApiResponse[bool])
async def delete_account(id: int, db: AsyncSession = Depends(get_db)):
    """解除绑定并删除 Reddit 账号"""
    res = await db.execute(select(Account).where(Account.id == id))
    acc = res.scalar_one_or_none()
    if not acc:
        raise HTTPException(status_code=404, detail="账号不存在")

    await db.delete(acc)
    await db.commit()
    return ApiResponse.success(data=True, message=f"账号 {acc.username} 已解除绑定并删除")

"""
Subreddits Endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.subreddit import Subreddit
from app.schemas.response import ApiResponse
from app.schemas.subreddit_schema import SubredditVO, SubredditCreateDTO
from app.services.feed_crawler import FeedCrawlerService

router = APIRouter()


@router.get("", response_model=ApiResponse[List[SubredditVO]])
async def get_subreddits(db: AsyncSession = Depends(get_db)):
    """获取所有受监控的 Subreddit 社区列表"""
    result = await db.execute(select(Subreddit).order_by(Subreddit.id.asc()))
    subs = result.scalars().all()
    vo_list = [
        SubredditVO(
            id=s.id,
            name=s.name,
            badge=s.badge,
            minKarma=s.min_karma,
            dailyLimit=s.daily_limit,
            todaySent=s.today_sent,
            isEnabled=s.is_enabled,
            description=s.description
        )
        for s in subs
    ]
    return ApiResponse.success(data=vo_list)


@router.post("", response_model=ApiResponse[SubredditVO])
async def create_subreddit(dto: SubredditCreateDTO, db: AsyncSession = Depends(get_db)):
    """新增目标社区"""
    clean_name = dto.name.strip()
    if not clean_name.startswith("r/"):
        clean_name = f"r/{clean_name}"

    existing = await db.execute(select(Subreddit).where(Subreddit.name == clean_name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"社区 {clean_name} 已存在于社区池中")

    new_sub = Subreddit(
        name=clean_name,
        badge=dto.badge,
        min_karma=dto.minKarma,
        daily_limit=dto.dailyLimit,
        description=dto.description
    )
    db.add(new_sub)
    await db.commit()
    await db.refresh(new_sub)

    return ApiResponse.success(
        data=SubredditVO(
            id=new_sub.id,
            name=new_sub.name,
            badge=new_sub.badge,
            minKarma=new_sub.min_karma,
            dailyLimit=new_sub.daily_limit,
            todaySent=new_sub.today_sent,
            isEnabled=new_sub.is_enabled,
            description=new_sub.description
        ),
        message=f"已成功添加社区 {clean_name}"
    )


@router.put("/{id}/toggle", response_model=ApiResponse[SubredditVO])
async def toggle_subreddit(id: int, db: AsyncSession = Depends(get_db)):
    """切换社区监听状态 (启用/停用)"""
    res = await db.execute(select(Subreddit).where(Subreddit.id == id))
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="社区不存在")

    sub.is_enabled = not sub.is_enabled
    await db.commit()
    await db.refresh(sub)

    state_desc = "启用监听" if sub.is_enabled else "暂停监听"
    return ApiResponse.success(
        data=SubredditVO(
            id=sub.id,
            name=sub.name,
            badge=sub.badge,
            minKarma=sub.min_karma,
            dailyLimit=sub.daily_limit,
            todaySent=sub.today_sent,
            isEnabled=sub.is_enabled,
            description=sub.description
        ),
        message=f"社区 {sub.name} 已切换为 {state_desc}"
    )


@router.post("/{id}/scan-now", response_model=ApiResponse[List[dict]])
async def scan_subreddit_now(id: int, db: AsyncSession = Depends(get_db)):
    """即时触发单版巡检抓取"""
    res = await db.execute(select(Subreddit).where(Subreddit.id == id))
    sub = res.scalar_one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="社区不存在")

    items = await FeedCrawlerService.scan_single_subreddit(sub.name)
    return ApiResponse.success(data=items, message=f"已完成对 {sub.name} 的即时巡检，抓取入库 {len(items)} 篇待审贴")


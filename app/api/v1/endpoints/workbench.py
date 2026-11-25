"""
Workbench Endpoints (HITL Review & Dispatch)
"""

from typing import List, Optional, Dict, Any
import asyncio
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import now_utc
from app.db.session import get_db
from app.models.candidate_post import CandidatePost
from app.models.account import Account
from app.models.dispatch_task import DispatchTask
from app.models.risk_setting import RiskSetting
from app.schemas.response import ApiResponse
from app.schemas.workbench_schema import CandidatePostVO, WorkbenchActionDTO, WorkbenchActionResultVO
from app.core.security import validate_comment_safety
from app.services.task_dispatcher import TaskDispatcher
from app.services.de_ai_generator import DeAIEngine

router = APIRouter()


def _format_time_ago(dt: datetime) -> str:
    diff = now_utc() - dt
    total_seconds = int(diff.total_seconds())
    if total_seconds < 60:
        return "刚刚"
    if total_seconds < 3600:
        return f"{total_seconds // 60}m ago"
    if total_seconds < 86400:
        return f"{total_seconds // 3600}h ago"
    return f"{total_seconds // 86400}d ago"


@router.get("/candidates", response_model=ApiResponse[List[CandidatePostVO]])
async def get_candidates(
    status: str = Query("PENDING", description="PENDING | ALL"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取候选待审帖子列表"""
    query = select(CandidatePost)
    if status != "ALL":
        query = query.where(CandidatePost.status == status)
    query = query.order_by(desc(CandidatePost.recommended_score), desc(CandidatePost.fetched_at)).limit(limit)

    result = await db.execute(query)
    posts = result.scalars().all()

    vo_list = [
        CandidatePostVO(
            id=p.id,
            redditPostId=p.reddit_post_id,
            subreddit=p.subreddit_name,
            title=p.title,
            content=p.selftext,
            permalink=p.permalink if p.permalink and p.permalink.startswith('http') else (f"https://reddit.com{p.permalink}" if p.permalink else f"https://reddit.com/{p.subreddit_name}/comments/{p.reddit_post_id}"),
            score=p.score,
            numComments=p.num_comments,
            upvoteRatio=float(p.upvote_ratio),
            matchKeyword=p.match_keyword,
            recommendedScore=p.recommended_score,
            recommendedReason=p.recommended_reason,
            draftComment=p.draft_comment,
            drafts=DeAIEngine.parse_drafts(p.draft_comment, p.title),
            createdAgo=_format_time_ago(p.post_created_utc),
            status=p.status
        )
        for p in posts
    ]
    return ApiResponse.success(data=vo_list)


@router.post("/candidates/{id}/action", response_model=ApiResponse[WorkbenchActionResultVO])
async def handle_candidate_action(
    id: int,
    dto: WorkbenchActionDTO,
    db: AsyncSession = Depends(get_db)
):
    """人工单键批复或跳过 (HITL 核心入口)"""
    post_res = await db.execute(select(CandidatePost).where(CandidatePost.id == id))
    post = post_res.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="候选帖子不存在")

    if dto.action == "SKIP":
        post.status = "SKIPPED"
        await db.commit()
        return ApiResponse.success(
            data=WorkbenchActionResultVO(actionResult="SKIPPED"),
            message="帖子已标记跳过"
        )

    if dto.action == "MANUAL_SENT":
        account = None
        if dto.accountId:
            acc_res = await db.execute(select(Account).where(Account.id == dto.accountId))
            account = acc_res.scalar_one_or_none()
        
        if not account:
            first_acc_res = await db.execute(select(Account).order_by(Account.id.asc()))
            account = first_acc_res.scalars().first()

        if not account:
            account = Account(
                username="reddit_user",
                stage="STAGE_4",
                daily_limit=999,
                daily_sent_count=0
            )
            db.add(account)
            await db.flush()

        post.status = "DISPATCHED"
        account.daily_sent_count += 1
        now = now_utc()

        # 记录到审计日志
        from app.models.audit_log import AuditLog
        audit = AuditLog(
            account_username=account.username,
            subreddit=post.subreddit_name,
            reddit_post_id=post.reddit_post_id,
            post_title=post.title,
            comment_snippet=(dto.finalComment or post.draft_comment or "")[:200],
            delay_seconds=0,
            status="SUCCESS",
            shadowban_status="VERIFIED_PUBLIC",
            created_at=now
        )
        db.add(audit)
        await db.commit()

        return ApiResponse.success(
            data=WorkbenchActionResultVO(
                accountId=account.id,
                delaySeconds=0,
                todaySentAfter=account.daily_sent_count,
                todayLimit=account.daily_limit,
                actionResult="MANUAL_SENT"
            ),
            message=f"已成功记录发送"
        )

    if dto.action == "APPROVE":
        if not dto.accountId:
            raise HTTPException(status_code=400, detail="批复外发必须指定执行账号")
        if not dto.finalComment or not dto.finalComment.strip():
            raise HTTPException(status_code=400, detail="评论内容不能为空")

        # 1. 检查断路器
        risk_res = await db.execute(select(RiskSetting).where(RiskSetting.id == 1))
        risk_setting = risk_res.scalar_one_or_none()
        if risk_setting and risk_setting.circuit_breaker_active:
            raise HTTPException(
                status_code=400, 
                detail=f"全局 429 断路器处于熔断保护中，禁止排期新任务！({risk_setting.circuit_breaker_reason})"
            )

        # 2. 检查账号健康与阶段额度
        acc_res = await db.execute(select(Account).where(Account.id == dto.accountId))
        account = acc_res.scalar_one_or_none()
        if not account:
            raise HTTPException(status_code=404, detail="指定的执行账号不存在")

        if account.stage == "STAGE_1":
            raise HTTPException(status_code=400, detail="该账号处于 STAGE_1 (冷启动潜伏期)，当日发帖配额为 0，严禁外发！")

        if account.daily_sent_count >= account.daily_limit:
            raise HTTPException(
                status_code=400, 
                detail=f"该账号今日已发 {account.daily_sent_count} 条，已达阶段上限 ({account.daily_limit} 条)！"
            )

        # 3. 静态风控拦截 (外链、联系方式、敏感词)
        custom_blacklist = risk_setting.sensitive_keywords if risk_setting else []
        is_safe, reason = validate_comment_safety(dto.finalComment, custom_blacklist)
        if not is_safe:
            raise HTTPException(status_code=400, detail=reason)

        # 4. 排入 APScheduler 随机延迟队列
        min_m = risk_setting.min_delay_minutes if risk_setting else 5
        max_m = risk_setting.max_delay_minutes if risk_setting else 30
        task_id, scheduled_at, delay_seconds = TaskDispatcher.schedule_comment(
            account_id=account.id,
            candidate_post_id=post.id,
            text=dto.finalComment,
            custom_delay_minutes=dto.customDelayMinutes,
            min_delay_m=min_m,
            max_delay_m=max_m
        )

        # 5. 写入 dispatch_tasks 表
        dispatch_task = DispatchTask(
            id=task_id,
            account_id=account.id,
            candidate_post_id=post.id,
            final_comment_text=dto.finalComment,
            delay_seconds=delay_seconds,
            scheduled_at=scheduled_at,
            status="QUEUED"
        )
        db.add(dispatch_task)
        post.status = "APPROVED"
        await db.commit()

        return ApiResponse.success(
            data=WorkbenchActionResultVO(
                taskId=task_id,
                accountId=account.id,
                delaySeconds=delay_seconds,
                scheduledAt=scheduled_at.isoformat(),
                todaySentAfter=account.daily_sent_count,
                todayLimit=account.daily_limit,
                actionResult="APPROVED"
            ),
            message=f"任务已安全排入调度队列，将在 {delay_seconds // 60} 分钟后触发外发"
        )

    raise HTTPException(status_code=400, detail="不支持的操作类型")


@router.post("/custom-drafts")
async def generate_custom_drafts(
    payload: Dict[str, Any]
):
    """根据输入的自定义帖子标题或 URL，使用去AI味规范实时生成3套高赞英文评论"""
    title = (payload.get("title") or "").strip()
    url = (payload.get("url") or "").strip()
    sub = (payload.get("subreddit") or "AskReddit").strip()
    
    if not title and not url:
        raise HTTPException(status_code=400, detail="请至少提供帖子标题或 Reddit 链接")

    target_title = title or (url.split("/comments/")[-1].replace("/", " ").replace("_", " ") if "/comments/" in url else url)
    drafts = DeAIEngine.generate_contextual_drafts(target_title, sub)
    target_url = url if url.startswith("http") else (f"https://reddit.com/{sub}" if not sub.startswith("r/") else f"https://reddit.com/{sub}")
    
    return ApiResponse.success(data={
        "title": target_title,
        "url": target_url,
        "subreddit": sub if sub.startswith("r/") else f"r/{sub}",
        "drafts": drafts
    })


@router.post("/refresh")
@router.post("/scan")
async def refresh_workbench_posts(db: AsyncSession = Depends(get_db)):
    """并发巡检目标社区并抓取最新热帖"""
    from app.services.feed_crawler import FeedCrawlerService
    targets = ["r/AskReddit", "r/NoStupidQuestions", "r/mildlyinteresting", "r/CasualConversation"]
    
    # 并发抓取各社区
    results = await asyncio.gather(
        *[FeedCrawlerService.scan_single_subreddit(sub) for sub in targets],
        return_exceptions=True
    )
    
    total_new = 0
    for r in results:
        if isinstance(r, list):
            total_new += len(r)

    return ApiResponse.success(
        data={"newCount": total_new},
        message=f"已成功完成热帖巡检，新增 {total_new} 篇讨论"
    )

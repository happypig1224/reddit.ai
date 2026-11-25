"""
Audit Logs Endpoints
"""

import io
import csv
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import now_utc
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.schemas.response import ApiResponse
from app.schemas.log_schema import AuditLogVO, ProbeResultVO
from app.services.shadowban_probe import ShadowbanProbeService

router = APIRouter()


@router.get("", response_model=ApiResponse[List[AuditLogVO]])
async def get_logs(
    status: str = Query("ALL", description="ALL | SUCCESS | SKIPPED | RATE_LIMITED | INTERCEPTED | ERROR"),
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """分页拉取系统审计与外发流水"""
    offset = (page - 1) * pageSize
    query = select(AuditLog)
    if status != "ALL":
        query = query.where(AuditLog.status == status)

    query = query.order_by(desc(AuditLog.id)).offset(offset).limit(pageSize)
    res = await db.execute(query)
    logs = res.scalars().all()

    vo_list = [
        AuditLogVO(
            id=l.id,
            accountUsername=l.account_username,
            subreddit=l.subreddit,
            redditPostId=l.reddit_post_id,
            postTitle=l.post_title,
            redditCommentId=l.reddit_comment_id,
            commentSnippet=l.comment_snippet,
            delaySeconds=l.delay_seconds,
            status=l.status,
            shadowbanStatus=l.shadowban_status,
            shadowbanCheckedAt=l.shadowban_checked_at.isoformat() if l.shadowban_checked_at else None,
            createdAt=l.created_at.isoformat()
        )
        for l in logs
    ]
    return ApiResponse.success(data=vo_list)


@router.post("/{id}/probe-shadowban", response_model=ApiResponse[ProbeResultVO])
async def probe_shadowban(id: int, db: AsyncSession = Depends(get_db)):
    """对特定评论触发一次公开匿名存活探针探测"""
    res = await db.execute(select(AuditLog).where(AuditLog.id == id))
    log_item = res.scalar_one_or_none()
    if not log_item:
        raise HTTPException(status_code=404, detail="审计日志记录不存在")

    old_status = log_item.shadowban_status
    new_status, msg = await ShadowbanProbeService.probe_comment(
        subreddit=log_item.subreddit,
        post_id=log_item.reddit_post_id,
        comment_id=log_item.reddit_comment_id or ""
    )

    log_item.shadowban_status = new_status
    log_item.shadowban_checked_at = now_utc()
    await db.commit()

    return ApiResponse.success(
        data=ProbeResultVO(
            logId=log_item.id,
            redditCommentId=log_item.reddit_comment_id,
            previousStatus=old_status,
            newStatus=new_status,
            message=msg
        ),
        message=f"探针探测完成: {new_status} - {msg}"
    )


@router.get("/export")
async def export_logs_csv(db: AsyncSession = Depends(get_db)):
    """导出 CSV 审计日志文件"""
    res = await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(500))
    logs = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "ID", "Account", "Subreddit", "Post ID", "Post Title", 
        "Comment ID", "Comment Snippet", "Delay(s)", "Status", "Shadowban", "Created At"
    ])

    for l in logs:
        writer.writerow([
            l.id, l.account_username, l.subreddit, l.reddit_post_id, l.post_title,
            l.reddit_comment_id or "", l.comment_snippet, l.delay_seconds, l.status,
            l.shadowban_status, l.created_at.isoformat()
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reddit_karma_pilot_audit_logs.csv"}
    )


@router.delete("", response_model=ApiResponse[bool])
async def clear_logs(db: AsyncSession = Depends(get_db)):
    """物理清空审计流水日志"""
    from sqlalchemy import delete
    await db.execute(delete(AuditLog))
    await db.commit()
    return ApiResponse.success(data=True, message="审计日志已物理清空")

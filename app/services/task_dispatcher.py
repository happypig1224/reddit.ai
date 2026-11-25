"""
APScheduler-based Delayed Task Dispatcher
Standards:
- 5~30 minutes random jitter to defeat timing correlation detection
- Circuit-breaker check prior to execution
- Atomic database audit log write
"""

import uuid
import random
from datetime import datetime, timedelta, timezone
from typing import Tuple, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select, update
from app.core.config import now_utc
from app.db.session import AsyncSessionLocal
from app.models.account import Account
from app.models.candidate_post import CandidatePost
from app.models.dispatch_task import DispatchTask
from app.models.audit_log import AuditLog
from app.models.risk_setting import RiskSetting
from app.services.praw_pool import PrawClientPool
from app.services.shadowban_probe import ShadowbanProbeService


class TaskDispatcher:
    scheduler = AsyncIOScheduler(timezone=timezone.utc)

    @classmethod
    def start(cls):
        if not cls.scheduler.running:
            cls.scheduler.start()

    @classmethod
    def shutdown(cls):
        if cls.scheduler.running:
            cls.scheduler.shutdown()

    @classmethod
    def schedule_comment(
        cls, 
        account_id: int, 
        candidate_post_id: int, 
        text: str, 
        custom_delay_minutes: Optional[int] = None,
        min_delay_m: int = 5,
        max_delay_m: int = 30
    ) -> Tuple[str, datetime, int]:
        """
        排入随机延迟任务队列
        Returns: (taskId, scheduledAt, delaySeconds)
        """
        if custom_delay_minutes is not None and custom_delay_minutes > 0:
            delay_seconds = custom_delay_minutes * 60
        else:
            delay_seconds = random.randint(min_delay_m * 60, max_delay_m * 60)

        scheduled_at_utc = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        scheduled_at_naive = scheduled_at_utc.replace(tzinfo=None)
        task_id = f"task_{uuid.uuid4().hex[:12]}"

        cls.scheduler.add_job(
            cls._execute_delayed_comment_job,
            trigger="date",
            run_date=scheduled_at_utc,
            args=[task_id],
            id=task_id,
            replace_existing=True,
            misfire_grace_time=3600
        )

        return task_id, scheduled_at_naive, delay_seconds

    @classmethod
    async def _execute_delayed_comment_job(cls, task_id: str):
        """到达预定时间后触发的实际发帖与审计"""
        try:
            async with AsyncSessionLocal() as session:
                # 1. 查询任务
                result = await session.execute(select(DispatchTask).where(DispatchTask.id == task_id))
                task = result.scalar_one_or_none()
                if not task or task.status != "QUEUED":
                    return

                now = now_utc()

                # 2. 检查 429 熔断断路器状态
                risk_res = await session.execute(select(RiskSetting).where(RiskSetting.id == 1))
                risk_setting = risk_res.scalar_one_or_none()
                if risk_setting and risk_setting.circuit_breaker_active:
                    task.status = "CANCELLED"
                    task.error_message = f"因 429 断路器熔断被系统拦截: {risk_setting.circuit_breaker_reason}"
                    task.executed_at = now
                    await session.commit()
                    return

                # 3. 加载账号与帖子信息
                acc_res = await session.execute(select(Account).where(Account.id == task.account_id))
                account = acc_res.scalar_one_or_none()
                post_res = await session.execute(select(CandidatePost).where(CandidatePost.id == task.candidate_post_id))
                post = post_res.scalar_one_or_none()

                if not account or not post:
                    task.status = "FAILED"
                    task.error_message = "关联的账号或帖子不存在"
                    task.executed_at = now
                    await session.commit()
                    return

                task.status = "EXECUTING"
                await session.commit()

                # 4. 执行发帖动作
                generated_comment_id = f"t1_{uuid.uuid4().hex[:7]}"
                execution_success = True
                error_msg = None

                try:
                    if not (account.client_id.startswith("client_id_") or "mock" in account.client_id.lower()):
                        # 真实 PRAW 调用
                        client = PrawClientPool.get_client(account)
                        submission = client.submission(id=post.reddit_post_id.replace("t3_", ""))
                        new_comment = submission.reply(task.final_comment_text)
                        generated_comment_id = new_comment.fullname
                except Exception as e:
                    execution_success = False
                    error_msg = str(e)

                # 5. 更新任务状态与账号计数
                task.executed_at = now
                if execution_success:
                    task.status = "SUCCESS"
                    task.reddit_comment_id = generated_comment_id
                    account.daily_sent_count += 1
                    account.is_cooling_down = True
                    account.cooldown_until = now + timedelta(minutes=random.randint(15, 30))
                    post.status = "DISPATCHED"

                    # 6. 写入审计日志
                    audit = AuditLog(
                        account_username=account.username,
                        subreddit=post.subreddit_name,
                        reddit_post_id=post.reddit_post_id,
                        post_title=post.title,
                        reddit_comment_id=generated_comment_id,
                        comment_snippet=task.final_comment_text[:200] + ("..." if len(task.final_comment_text) > 200 else ""),
                        delay_seconds=task.delay_seconds,
                        status="SUCCESS",
                        shadowban_status="PENDING",
                        created_at=now
                    )
                    session.add(audit)
                else:
                    task.status = "FAILED"
                    task.error_message = error_msg
                    audit = AuditLog(
                        account_username=account.username,
                        subreddit=post.subreddit_name,
                        reddit_post_id=post.reddit_post_id,
                        post_title=post.title,
                        comment_snippet=task.final_comment_text[:200],
                        delay_seconds=task.delay_seconds,
                        status="ERROR",
                        shadowban_status="PENDING",
                        created_at=now
                    )
                    session.add(audit)

                await session.commit()
        except Exception as err:
            import logging
            logging.getLogger("task_dispatcher").error(f"执行延迟排期任务失败 ({task_id}): {err}")

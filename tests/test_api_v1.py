"""
Reddit Karma Pilot - FastAPI Endpoints & Anti-Ban Security Automated Test Suite
Standards:
- Fullstack QA Architect: Zero False Green, Hermetic Testing
- Enterprise Code Reviewer: P0~P3 Security Gates, Boundary Interception
- Schema Architect: Strict Pydantic v2 Contract Validation
"""

import pytest
import httpx
from datetime import timedelta
from sqlalchemy import select, delete
from app.main import app
from app.core.config import now_utc
from app.db.session import AsyncSessionLocal
from app.models.account import Account
from app.models.candidate_post import CandidatePost
from app.models.audit_log import AuditLog
from app.models.comment_template import CommentTemplate
from app.models.risk_setting import RiskSetting


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def fixtures():
    """Hermetic 测试脚手架：提供隔离的测试账号、候选帖与日志，并在测试完成后物理清理"""
    from sqlalchemy import update
    async with AsyncSessionLocal() as session:
        # 保证断路器在测试开始前处于复位状态
        await session.execute(update(RiskSetting).where(RiskSetting.id == 1).values(circuit_breaker_active=False, circuit_breaker_reason=None))
        await session.commit()
        acc1 = Account(
            username="u/HermeticTester1",
            client_id="mock_client_id_test1",
            stage="STAGE_2",
            created_days_ago=5,
            comment_karma=46,
            link_karma=2,
            daily_sent_count=0,
            daily_limit=5,
            is_cooling_down=False,
            status="HEALTHY"
        )
        acc1.client_secret = "test_secret_1"

        acc2 = Account(
            username="u/HermeticTester2",
            client_id="mock_client_id_test2",
            stage="STAGE_1",
            created_days_ago=2,
            comment_karma=0,
            link_karma=0,
            daily_sent_count=0,
            daily_limit=0,
            is_cooling_down=False,
            status="HEALTHY"
        )
        acc2.client_secret = "test_secret_2"

        post1 = CandidatePost(
            reddit_post_id="t3_hermetic_post_1",
            subreddit_name="r/webdev",
            title="Best way to handle simple contact forms without backend in 2026?",
            author="u/FrontendBuilder",
            permalink="https://reddit.com/r/webdev/comments/test1",
            selftext="Building a static landing page without backend.",
            score=42,
            num_comments=8,
            upvote_ratio=0.94,
            match_keyword="best way",
            recommended_score=95,
            recommended_reason="高求助意图",
            draft_comment="从工程维护的角度来看，前期保持架构轻量、避免过度设计通常是最稳妥的做法。",
            status="PENDING",
            post_created_utc=now_utc()
        )

        post2 = CandidatePost(
            reddit_post_id="t3_hermetic_post_2",
            subreddit_name="r/AskReddit",
            title="What is a small everyday habit that surprisingly changed your productivity?",
            author="u/LifeHacker_42",
            permalink="https://reddit.com/r/AskReddit/comments/test2",
            selftext="Looking for compound habits.",
            score=128,
            num_comments=24,
            upvote_ratio=0.96,
            match_keyword="looking for",
            recommended_score=88,
            recommended_reason="生活通用求助",
            draft_comment="每晚睡前把第二天最重要的三件事写在纸上，第二天直接执行。",
            status="PENDING",
            post_created_utc=now_utc()
        )

        log1 = AuditLog(
            account_username="u/HermeticTester1",
            subreddit="r/webdev",
            reddit_post_id="t3_hermetic_post_1",
            post_title="Best way to handle simple contact forms without backend in 2026?",
            reddit_comment_id="t1_hermetic_comment_1",
            comment_snippet="测试审计日志内容...",
            delay_seconds=600,
            status="SUCCESS",
            shadowban_status="PENDING",
            created_at=now_utc()
        )

        session.add_all([acc1, acc2, post1, post2, log1])
        await session.commit()
        await session.refresh(acc1)
        await session.refresh(acc2)
        await session.refresh(post1)
        await session.refresh(post2)
        await session.refresh(log1)

        data = {
            "acc1": acc1,
            "acc2": acc2,
            "post1": post1,
            "post2": post2,
            "log1": log1
        }

    yield data

    # 物理恢复干净环境，杜绝测试残留
    async with AsyncSessionLocal() as session:
        await session.execute(update(RiskSetting).where(RiskSetting.id == 1).values(circuit_breaker_active=False, circuit_breaker_reason=None))
        await session.execute(delete(AuditLog).where(AuditLog.account_username.in_(["u/HermeticTester1", "u/HermeticTester2"])))
        await session.execute(delete(CandidatePost).where(CandidatePost.reddit_post_id.in_(["t3_hermetic_post_1", "t3_hermetic_post_2"])))
        await session.execute(delete(Account).where(Account.username.in_(["u/HermeticTester1", "u/HermeticTester2", "u/NewTestUser"])))
        await session.commit()


# ----------------------------------------------------------------------
# 1. 基础架构与健康检查探针 (Health & Root)
# ----------------------------------------------------------------------
@pytest.mark.anyio
async def test_health_check_endpoint(client):
    """验证健康检查探针返回 UP 及各子系统健康状态"""
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UP"
    assert data["database"] == "CONNECTED"
    assert data["scheduler"] in ["RUNNING", "STOPPED"]


@pytest.mark.anyio
async def test_root_endpoint(client):
    """验证根路径服务信息索引"""
    resp = await client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "/docs" in data["docs"]
    assert data["api_v1"] == "/api/v1"


# ----------------------------------------------------------------------
# 2. 账号矩阵与生命周期 (Accounts & Lifecycle CRUD)
# ----------------------------------------------------------------------
@pytest.mark.anyio
async def test_accounts_crud_and_credential_sanitization(client, fixtures):
    """
    断言账号列表拉取正常，且凭据严格脱敏:
    任何 API 响应绝对禁止将 client_secret 明文或加密哈希泄露给前端客户端
    """
    resp = await client.get("/api/v1/accounts")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    accounts = body["data"]
    assert len(accounts) >= 2

    for acc in accounts:
        assert "client_secret" not in acc
        assert "_client_secret" not in acc
        assert "password" not in acc
        assert acc["username"].startswith("u/")


@pytest.mark.anyio
async def test_account_creation_and_deletion(client):
    """断言新账号录入物理落盘与解绑删除"""
    create_payload = {
        "username": "NewTestUser",
        "clientId": "client_new_test_123",
        "clientSecret": "secret_new_test_abc",
        "createdDaysAgo": 6,
        "proxyUrl": "socks5://127.0.0.1:10808"
    }
    create_resp = await client.post("/api/v1/accounts", json=create_payload)
    assert create_resp.status_code == 200
    created = create_resp.json()["data"]
    assert created["username"] == "u/NewTestUser"
    assert created["stage"] == "STAGE_2"
    assert created["dailyLimit"] == 5
    acc_id = created["id"]

    # 删除该账号
    del_resp = await client.delete(f"/api/v1/accounts/{acc_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"] is True


@pytest.mark.anyio
async def test_accounts_stage_transition_and_daily_limit_sync(client, fixtures):
    """
    断言账号阶段切换 (STAGE_2 -> STAGE_3):
    系统必须自动同步将其单日安全发帖硬上限从 5 条提升至 8 条
    """
    acc_id = fixtures["acc1"].id
    patch_resp = await client.patch(
        f"/api/v1/accounts/{acc_id}/stage",
        json={"stage": "STAGE_3"}
    )
    assert patch_resp.status_code == 200
    acc = patch_resp.json()["data"]
    assert acc["stage"] == "STAGE_3"
    assert acc["dailyLimit"] == 8, "切换至 STAGE_3 后 dailyLimit 必须自动同步为 8"


@pytest.mark.anyio
async def test_accounts_praw_handshake_endpoint(client, fixtures):
    """断言账号 API 连通性测试握手接口能够正常返回延迟与存活状态"""
    acc_id = fixtures["acc1"].id
    resp = await client.post(f"/api/v1/accounts/{acc_id}/test-handshake")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["username"] == "u/HermeticTester1"
    assert "latencyMs" in data
    assert data["isSuspended"] is False


# ----------------------------------------------------------------------
# 3. 审核工作台与风控拦截核心防线 (Workbench & Anti-Ban Interception)
# ----------------------------------------------------------------------
@pytest.mark.anyio
async def test_workbench_get_candidates(client, fixtures):
    """断言工作台待审候选帖子能够按推荐意图分降序拉取"""
    resp = await client.get("/api/v1/workbench/candidates?status=PENDING&limit=10")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    posts = body["data"]
    assert len(posts) >= 2
    # 验证按推荐意图分排序
    scores = [p["recommendedScore"] for p in posts]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.anyio
async def test_security_intercept_external_url(client, fixtures):
    """
    【风控红线 1】外链强阻断断言:
    提交包含 https:// 或 www. 的评论内容时，后端必须阻断并返回 400
    """
    post_id = fixtures["post1"].id
    acc_id = fixtures["acc1"].id
    unsafe_payload = {
        "action": "APPROVE",
        "accountId": acc_id,
        "finalComment": "Check out this great tool here: https://reddit-pilot-tool.xyz/signup for easy setup."
    }
    resp = await client.post(f"/api/v1/workbench/candidates/{post_id}/action", json=unsafe_payload)
    assert resp.status_code == 400
    body = resp.json()
    assert "外部链接" in body["message"] or "URL" in body["message"]


@pytest.mark.anyio
async def test_security_intercept_private_contact(client, fixtures):
    """
    【风控红线 2】私域联系方式强阻断断言:
    提交包含微信、Telegram、WhatsApp、加v 的评论内容时，后端必须阻断并返回 400
    """
    post_id = fixtures["post1"].id
    acc_id = fixtures["acc1"].id
    unsafe_payload = {
        "action": "APPROVE",
        "accountId": acc_id,
        "finalComment": "我也遇到了同样问题，可以加我微信交流细节: wx_pilot_9999"
    }
    resp = await client.post(f"/api/v1/workbench/candidates/{post_id}/action", json=unsafe_payload)
    assert resp.status_code == 400
    body = resp.json()
    assert "私域联系方式" in body["message"]


@pytest.mark.anyio
async def test_security_intercept_stage_1_zero_quota(client, fixtures):
    """
    【风控红线 3】新号阶段硬限制断言:
    账号处于 STAGE_1 (冷启动潜伏期，配额=0)，尝试为其排期外发必须被直接拦截
    """
    post_id = fixtures["post1"].id
    acc2_id = fixtures["acc2"].id
    unsafe_payload = {
        "action": "APPROVE",
        "accountId": acc2_id,
        "finalComment": "针对这个问题，前期保持架构轻量、避免过度设计通常是最稳妥的做法。"
    }
    resp = await client.post(f"/api/v1/workbench/candidates/{post_id}/action", json=unsafe_payload)
    assert resp.status_code == 400
    body = resp.json()
    assert "STAGE_1" in body["message"] or "配额为 0" in body["message"]


@pytest.mark.anyio
async def test_security_intercept_circuit_breaker(client, fixtures):
    """
    【风控红线 4】429 紧急断路器熔断断言:
    当触发 TRIP 熔断后，全局任何排期提交必须被拦截；RESET 解除后恢复正常
    """
    post_id = fixtures["post1"].id
    acc_id = fixtures["acc1"].id

    # 1. 触发断路器 TRIP
    trip_resp = await client.post(
        "/api/v1/risk-control/circuit-breaker",
        json={"action": "TRIP", "reason": "测试自动化断路器拦截"}
    )
    assert trip_resp.status_code == 200
    assert trip_resp.json()["data"]["circuitBreakerActive"] is True

    # 2. 尝试批复排期，断言被 400 拦截
    approve_resp = await client.post(
        f"/api/v1/workbench/candidates/{post_id}/action",
        json={
            "action": "APPROVE",
            "accountId": acc_id,
            "finalComment": "前期保持轻量架构是最稳妥的做法，无需过度设计。"
        }
    )
    assert approve_resp.status_code == 400
    assert "断路器处于熔断保护中" in approve_resp.json()["message"]

    # 3. 环境物理复原: 解除熔断 RESET
    reset_resp = await client.post(
        "/api/v1/risk-control/circuit-breaker",
        json={"action": "RESET"}
    )
    assert reset_resp.status_code == 200
    assert reset_resp.json()["data"]["circuitBreakerActive"] is False


@pytest.mark.anyio
async def test_workbench_approve_success_scheduling(client, fixtures):
    """
    【标准成功闭环】人工批复通过排期:
    合规评论内容正常排入 APScheduler，返回带随机延迟的 taskId，延迟在 5~30 分钟范围内
    """
    post_id = fixtures["post1"].id
    acc_id = fixtures["acc1"].id
    valid_payload = {
        "action": "APPROVE",
        "accountId": acc_id,
        "finalComment": "我之前也遇到过类似问题，后来发现像 Cloudflare Workers 会更稳定一点，免去维护服务器的麻烦。",
        "customDelayMinutes": 15
    }
    resp = await client.post(f"/api/v1/workbench/candidates/{post_id}/action", json=valid_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 200
    data = body["data"]
    assert data["actionResult"] == "APPROVED"
    assert data["taskId"].startswith("task_")
    assert data["delaySeconds"] == 15 * 60
    assert "scheduledAt" in data


# ----------------------------------------------------------------------
# 4. 社区池、模板库与审计流水 (Subreddits, Templates & Logs)
# ----------------------------------------------------------------------
@pytest.mark.anyio
async def test_subreddits_list_and_toggle(client):
    """断言社区池列表查询与单键切换监听状态"""
    resp = await client.get("/api/v1/subreddits")
    assert resp.status_code == 200
    subreddits = resp.json()["data"]
    assert len(subreddits) >= 5

    sub = subreddits[0]
    initial_enabled = sub["isEnabled"]

    # 切换状态
    toggle_resp = await client.put(f"/api/v1/subreddits/{sub['id']}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["data"]["isEnabled"] != initial_enabled

    # 还原状态
    restore_resp = await client.put(f"/api/v1/subreddits/{sub['id']}/toggle")
    assert restore_resp.status_code == 200
    assert restore_resp.json()["data"]["isEnabled"] == initial_enabled


@pytest.mark.anyio
async def test_templates_cooldown_detection(client):
    """断言模板查询能够正确识别 24 小时内的冷却状态"""
    async with AsyncSessionLocal() as session:
        tpl = CommentTemplate(
            tone="经验分享",
            template_text="测试冷却状态模板",
            is_active=True,
            usage_count=5,
            last_used_at=now_utc() - timedelta(hours=2)
        )
        session.add(tpl)
        await session.commit()
        await session.refresh(tpl)
        tpl_id = tpl.id

    resp = await client.get("/api/v1/templates")
    assert resp.status_code == 200
    templates = resp.json()["data"]
    found = [t for t in templates if t["id"] == tpl_id]
    assert len(found) == 1
    assert found[0]["isCoolingDown"] is True

    # 清理测试模板
    async with AsyncSessionLocal() as session:
        await session.execute(delete(CommentTemplate).where(CommentTemplate.id == tpl_id))
        await session.commit()


@pytest.mark.anyio
async def test_audit_logs_and_shadowban_probe(client, fixtures):
    """断言审计流水拉取以及人工单键探针探测"""
    log_id = fixtures["log1"].id

    log_resp = await client.get("/api/v1/logs?page=1&pageSize=10")
    assert log_resp.status_code == 200
    logs = log_resp.json()["data"]
    assert len(logs) > 0

    # 触发匿名存活探针探测
    probe_resp = await client.post(f"/api/v1/logs/{log_id}/probe-shadowban")
    assert probe_resp.status_code == 200
    probe_data = probe_resp.json()["data"]
    assert probe_data["logId"] == log_id
    assert probe_data["newStatus"] in ["VERIFIED_PUBLIC", "PENDING", "SHADOWBANNED", "SUSPENDED"]


@pytest.mark.anyio
async def test_manual_account_creation_without_client_credentials(client):
    """测试玩法一：无需提供 clientId 和 clientSecret，直接录入新号"""
    payload = {
        "username": "DryBridgeTestUser",
        "createdDaysAgo": 5
    }
    resp = await client.post("/api/v1/accounts", json=payload)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["username"] == "u/DryBridgeTestUser"
    assert data["stage"] == "STAGE_2"
    assert data["dailyLimit"] == 5
    account_id = data["id"]

    # 验证获取所有账号包含该新号
    get_resp = await client.get("/api/v1/accounts")
    assert get_resp.status_code == 200
    accs = get_resp.json()["data"]
    assert any(a["id"] == account_id for a in accs)

    # 清理创建的账号
    del_resp = await client.delete(f"/api/v1/accounts/{account_id}")
    assert del_resp.status_code == 200


@pytest.mark.anyio
async def test_manual_sent_workflow_and_audit_logging(client, fixtures):
    """测试玩法一：一键复制后标记 MANUAL_SENT，直接完成并写入审计日志，不调用 PRAW"""
    acc = fixtures["acc1"]
    initial_sent = acc.daily_sent_count

    # 抓取候选帖
    post_res = await client.get("/api/v1/workbench/candidates?status=PENDING")
    assert post_res.status_code == 200
    candidates = post_res.json()["data"]
    assert len(candidates) > 0
    candidate = candidates[0]

    # 执行 MANUAL_SENT
    action_payload = {
        "action": "MANUAL_SENT",
        "accountId": acc.id,
        "finalComment": "This is a natural human reply tested in manual mode."
    }
    action_resp = await client.post(f"/api/v1/workbench/candidates/{candidate['id']}/action", json=action_payload)
    assert action_resp.status_code == 200
    body = action_resp.json()
    assert body["code"] == 200
    res_data = body["data"]
    assert res_data["actionResult"] == "MANUAL_SENT"
    assert res_data["todaySentAfter"] == initial_sent + 1

    # 验证日志记录
    logs_resp = await client.get("/api/v1/logs?limit=5")
    assert logs_resp.status_code == 200
    logs = logs_resp.json()["data"]
    assert len(logs) > 0
    latest_log = logs[0]
    assert latest_log["accountUsername"] == acc.username
    assert latest_log["delaySeconds"] == 0
    assert latest_log["status"] == "SUCCESS"
    assert latest_log["shadowbanStatus"] == "VERIFIED_PUBLIC"


"""
Reddit Karma Pilot - Database Baseline & Migration Automated Test Suite
Standards:
- Fullstack QA Architect: Zero False Green, Hermetic Environment, Deterministic Verification
- Enterprise Code Reviewer: Integrity, Index Coverage, Zero Data Loss
"""

import os
import json
import pytest
import pymysql

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_NAME = os.getenv("DB_NAME", "reddit_karma_pilot")


@pytest.fixture(scope="session")
def db_conn():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    yield conn
    conn.close()


# ----------------------------------------------------------------------
# Gate 1: 结构完备性与字符集校对 (Schema & Charset Gate)
# ----------------------------------------------------------------------
def test_all_tables_exist(db_conn):
    """验证 8 张核心表物理存在"""
    expected_tables = {
        "accounts",
        "subreddits",
        "candidate_posts",
        "comment_templates",
        "dispatch_tasks",
        "audit_logs",
        "risk_settings",
        "schema_version"
    }
    with db_conn.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = {list(row.values())[0] for row in cursor.fetchall()}
    
    missing = expected_tables - tables
    assert not missing, f"物理数据库缺失核心表: {missing}"


def test_tables_charset_and_collation(db_conn):
    """验证所有业务表均为 utf8mb4 及 utf8mb4_unicode_ci"""
    with db_conn.cursor() as cursor:
        cursor.execute("""
            SELECT table_name, table_collation 
            FROM information_schema.tables 
            WHERE table_schema = %s AND table_type = 'BASE TABLE';
        """, (DB_NAME,))
        rows = cursor.fetchall()

    for row in rows:
        t_name = row["TABLE_NAME"]
        collation = row["TABLE_COLLATION"]
        assert "utf8mb4" in collation.lower(), f"表 {t_name} 未使用 utf8mb4 字符集: {collation}"


# ----------------------------------------------------------------------
# Gate 2: UTF8MB4 国际化 Emoji 与多字节无损存储 (Emoji & Fidelity Gate)
# ----------------------------------------------------------------------
def test_utf8mb4_emoji_storage_fidelity(db_conn):
    """
    断言 4 字节原生 Emoji、特殊日韩泰多语言字符无截断、无乱码写入
    Reddit 帖子与评论中高频出现 Emoji (如 🚀, 🔥, 🤖, 💬, 💡)
    """
    test_emoji_text = "测试 Emoji 真实存储: 🚀 🔥 🤖 💬 💡 | 特殊字符: § ¶ © ® ™ 日本語 テスト 한국어"
    with db_conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO comment_templates (tone, template_text, is_active)
            VALUES ('真诚经验', %s, 0);
        """, (test_emoji_text,))
        inserted_id = cursor.lastrowid
        db_conn.commit()

        cursor.execute("SELECT template_text FROM comment_templates WHERE id = %s;", (inserted_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row["template_text"] == test_emoji_text, "Emoji 或特殊字符在写入 MySQL 后被截断或变异！"

        # 环境物理归零：清理测试脏数据
        cursor.execute("DELETE FROM comment_templates WHERE id = %s;", (inserted_id,))
        db_conn.commit()


# ----------------------------------------------------------------------
# Gate 3: 唯一性约束与主键防重 (Uniqueness & Primary Key Gate)
# ----------------------------------------------------------------------
def test_uk_accounts_username_enforced(db_conn):
    """断言账号表用户名唯一约束 uk_username 必须物理生效"""
    with db_conn.cursor() as cursor:
        cursor.execute("DELETE FROM accounts WHERE username = 'u/UniqueTestUser';")
        cursor.execute("""
            INSERT INTO accounts (username, client_id, client_secret)
            VALUES ('u/UniqueTestUser', 'cid_unique_1', 'sec_unique_1');
        """)
        db_conn.commit()

        with pytest.raises(pymysql.err.IntegrityError) as exc_info:
            cursor.execute("""
                INSERT INTO accounts (username, client_id, client_secret)
                VALUES ('u/UniqueTestUser', 'cid_unique_2', 'sec_unique_2');
            """)
        assert "Duplicate entry" in str(exc_info.value)
        cursor.execute("DELETE FROM accounts WHERE username = 'u/UniqueTestUser';")
        db_conn.commit()


def test_uk_subreddits_name_enforced(db_conn):
    """断言目标社区池社区名唯一约束 uk_name 必须物理生效"""
    with db_conn.cursor() as cursor:
        with pytest.raises(pymysql.err.IntegrityError) as exc_info:
            cursor.execute("""
                INSERT INTO subreddits (name, badge)
                VALUES ('r/AskReddit', '测试重复');
            """)
        assert "Duplicate entry" in str(exc_info.value)
    db_conn.rollback()


def test_uk_candidate_posts_reddit_post_id_enforced(db_conn):
    """断言待审候选帖原生 Reddit Post ID 唯一约束 uk_reddit_post_id 必须物理生效"""
    with db_conn.cursor() as cursor:
        cursor.execute("DELETE FROM candidate_posts WHERE reddit_post_id = 't3_unique_test_1';")
        cursor.execute("""
            INSERT INTO candidate_posts 
            (reddit_post_id, subreddit_name, title, permalink, post_created_utc)
            VALUES ('t3_unique_test_1', 'r/AskReddit', '重复测试原帖', 'https://reddit.com', NOW());
        """)
        db_conn.commit()

        with pytest.raises(pymysql.err.IntegrityError) as exc_info:
            cursor.execute("""
                INSERT INTO candidate_posts 
                (reddit_post_id, subreddit_name, title, permalink, post_created_utc)
                VALUES ('t3_unique_test_1', 'r/AskReddit', '重复测试2', 'https://reddit.com', NOW());
            """)
        assert "Duplicate entry" in str(exc_info.value)
        cursor.execute("DELETE FROM candidate_posts WHERE reddit_post_id = 't3_unique_test_1';")
        db_conn.commit()


# ----------------------------------------------------------------------
# Gate 4: 外键级联防孤儿任务 (Foreign Key Cascade Gate)
# ----------------------------------------------------------------------
def test_dispatch_tasks_foreign_key_cascade(db_conn):
    """
    断言 dispatch_tasks 对 accounts(id) 的外键级联删除 (ON DELETE CASCADE)
    当账号注销/删除时，必须物理级联清除其未执行/执行中的排期任务，严禁孤儿任务长期悬挂
    """
    with db_conn.cursor() as cursor:
        cursor.execute("""
            INSERT INTO accounts (username, client_id, client_secret, stage)
            VALUES ('u/temp_cascade_tester', 'cid_cascade', 'sec_cascade', 'STAGE_2');
        """)
        temp_acc_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO candidate_posts 
            (reddit_post_id, subreddit_name, title, permalink, post_created_utc)
            VALUES ('t3_temp_cascade_post', 'r/AskReddit', 'temp cascade post', 'https://reddit.com', NOW());
        """)
        temp_post_id = cursor.lastrowid

        task_id = "test_task_cascade_001"
        cursor.execute("""
            INSERT INTO dispatch_tasks 
            (id, account_id, candidate_post_id, final_comment_text, delay_seconds, scheduled_at, status)
            VALUES (%s, %s, %s, '测试级联评论', 300, NOW() + INTERVAL 5 MINUTE, 'QUEUED');
        """, (task_id, temp_acc_id, temp_post_id))
        db_conn.commit()

        cursor.execute("SELECT id FROM dispatch_tasks WHERE id = %s;", (task_id,))
        assert cursor.fetchone() is not None

        cursor.execute("DELETE FROM accounts WHERE id = %s;", (temp_acc_id,))
        cursor.execute("DELETE FROM candidate_posts WHERE id = %s;", (temp_post_id,))
        db_conn.commit()

        cursor.execute("SELECT id FROM dispatch_tasks WHERE id = %s;", (task_id,))
        assert cursor.fetchone() is None, "账号删除后关联排期任务未被级联删除，产生了孤儿任务！"


# ----------------------------------------------------------------------
# Gate 5: ENUM 非法边界阻断 (ENUM Boundary & Strict SQL Mode)
# ----------------------------------------------------------------------
def test_accounts_stage_enum_validation(db_conn):
    """断言非法养号阶段 (如 STAGE_INVALID) 无法绕过数据库物理校验"""
    with db_conn.cursor() as cursor:
        with pytest.raises(Exception):
            cursor.execute("""
                INSERT INTO accounts (username, client_id, client_secret, stage)
                VALUES ('u/bad_enum_user', 'cid', 'sec', 'STAGE_INVALID');
            """)
    db_conn.rollback()


# ----------------------------------------------------------------------
# Gate 6: 高频查询索引覆盖率与执行计划审计 (Index Coverage & EXPLAIN Gate)
# ----------------------------------------------------------------------
def test_workbench_candidate_query_index_efficiency(db_conn):
    """
    审核工作台高频核心查询 EXPLAIN 探查:
    SELECT * FROM candidate_posts WHERE status = 'PENDING' ORDER BY recommended_score DESC LIMIT 20;
    断言: 必须命中复合索引 idx_status_score，严禁出现性能杀手 Using filesort！
    """
    with db_conn.cursor() as cursor:
        cursor.execute("""
            EXPLAIN SELECT id, reddit_post_id, subreddit_name, recommended_score, status 
            FROM candidate_posts 
            WHERE status = 'PENDING' 
            ORDER BY recommended_score DESC 
            LIMIT 20;
        """)
        plan = cursor.fetchall()[0]
        used_key = plan.get("key") or plan.get("KEY")
        extra = plan.get("Extra") or plan.get("extra") or ""

        assert used_key == "idx_status_score", f"工作台待审贴未命中 idx_status_score，实际使用: {used_key}"
        assert "Using filesort" not in extra, f"工作台待审贴高频查询触发了文件临时排序 (Using filesort): {extra}"


def test_shadowban_probe_worker_index_efficiency(db_conn):
    """
    存活探针后台工作者定时扫描待探测评论:
    SELECT id, subreddit, reddit_post_id, reddit_comment_id 
    FROM audit_logs 
    WHERE shadowban_status = 'PENDING' 
    ORDER BY created_at ASC 
    LIMIT 10;
    断言: 必须命中复合索引 idx_shadowban_probe，消除 filesort
    """
    with db_conn.cursor() as cursor:
        cursor.execute("""
            EXPLAIN SELECT id, subreddit, reddit_post_id, reddit_comment_id 
            FROM audit_logs 
            WHERE shadowban_status = 'PENDING' 
            ORDER BY created_at ASC 
            LIMIT 10;
        """)
        plan = cursor.fetchall()[0]
        used_key = plan.get("key") or plan.get("KEY")
        extra = plan.get("Extra") or plan.get("extra") or ""

        assert used_key == "idx_shadowban_probe", f"探针工作者扫描未命中 idx_shadowban_probe，实际使用: {used_key}"
        assert "Using filesort" not in extra, f"探针工作者扫描触发了 filesort: {extra}"


def test_audit_logs_status_filtered_index_efficiency(db_conn):
    """
    审计流水分页按状态过滤:
    SELECT id, account_username, reddit_post_id 
    FROM audit_logs 
    WHERE status = 'SUCCESS' 
    ORDER BY created_at DESC 
    LIMIT 20;
    断言: 必须命中复合索引 idx_status_created
    """
    with db_conn.cursor() as cursor:
        cursor.execute("""
            EXPLAIN SELECT id, account_username, reddit_post_id 
            FROM audit_logs 
            WHERE status = 'SUCCESS' 
            ORDER BY created_at DESC 
            LIMIT 20;
        """)
        plan = cursor.fetchall()[0]
        used_key = plan.get("key") or plan.get("KEY")
        extra = plan.get("Extra") or plan.get("extra") or ""

        assert used_key == "idx_status_created", f"状态过滤流水分页未命中 idx_status_created，实际使用: {used_key}"
        assert "Using filesort" not in extra, f"状态过滤流水分页触发了 filesort: {extra}"


def test_subreddits_enabled_index_efficiency(db_conn):
    """
    定时抓取监听活跃社区查询:
    SELECT id, name, min_karma, daily_limit FROM subreddits WHERE is_enabled = 1;
    断言: 必须命中 idx_is_enabled 索引
    """
    with db_conn.cursor() as cursor:
        cursor.execute("""
            EXPLAIN SELECT id, name, min_karma, daily_limit 
            FROM subreddits 
            WHERE is_enabled = 1;
        """)
        plan = cursor.fetchall()[0]
        used_key = plan.get("key") or plan.get("KEY")
        assert used_key == "idx_is_enabled", f"社区监听池未命中 idx_is_enabled，实际使用: {used_key}"


# ----------------------------------------------------------------------
# Gate 7: 风控配置与敏感词合规性 (Risk Control Baseline)
# ----------------------------------------------------------------------
def test_risk_settings_integrity(db_conn):
    """验证全局风控表默认参数满足防封物理红线"""
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT * FROM risk_settings WHERE id = 1;")
        settings = cursor.fetchone()
        assert settings is not None, "缺少 ID=1 的默认风控配置记录！"

        # 1. 验证随机延迟区间 (5~30分钟)
        assert settings["min_delay_minutes"] >= 5, "最小随机延迟不得低于 5 分钟！"
        assert settings["max_delay_minutes"] <= 60, "最大随机延迟设置过长！"
        assert settings["min_delay_minutes"] < settings["max_delay_minutes"], "最小延迟必须小于最大延迟！"

        # 2. 验证单账号单日上限 (新号不得超过 5 条)
        assert settings["max_daily_comments_per_account"] <= 5, "新号阶段单日发帖上限严禁超过 5 条！"

        # 3. 验证敏感词 JSON
        keywords_json = settings["sensitive_keywords"]
        if isinstance(keywords_json, str):
            keywords = json.loads(keywords_json)
        else:
            keywords = keywords_json
        
        assert isinstance(keywords, list), "sensitive_keywords 必须为 JSON 数组"
        must_have = {"http://", "https://", "t.me", "wa.me", "微信", "whatsapp", "telegram"}
        assert must_have.issubset(set(keywords)), f"风控词库缺少核心外链/私域阻断词: {must_have - set(keywords)}"


# ----------------------------------------------------------------------
# Gate 8: 迁移版本历史完整性与幂等性 (Migration Baseline)
# ----------------------------------------------------------------------
def test_migration_version_integrity(db_conn):
    """断言 schema_version 记录了当前已发布版本且均为成功状态"""
    with db_conn.cursor() as cursor:
        cursor.execute("SELECT version, description, success, checksum FROM schema_version ORDER BY installed_rank ASC;")
        rows = cursor.fetchall()

    versions = [r["version"] for r in rows]
    assert "1.0.0" in versions
    assert "1.0.1" in versions
    assert "1.0.2" in versions

    for r in rows:
        assert r["success"] == 1, f"版本 {r['version']} 执行状态异常！"
        assert r["checksum"] is not None, f"版本 {r['version']} 缺失 SHA256 防篡改校验和！"

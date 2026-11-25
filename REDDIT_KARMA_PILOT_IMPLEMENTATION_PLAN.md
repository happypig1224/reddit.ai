# 📘 Reddit Karma Pilot · 系统落地实施技术方案书

> **系统名称**：Reddit Karma Pilot（新号养号半自动工具）  
> **文档密级**：内部技术交付与实施指南  
> **技术栈架构**：**Python 3.11+ (FastAPI) + MySQL 8.0 + PRAW 7.7+ + APScheduler + Vue 3 (前端中控)**  
> **架构设计准则**：安全第一（Anti-Ban）、人机协同（Human-in-the-Loop）、物理隔离（Per-Account Isolation）

---

## 目录
1. [系统总体技术架构](#一-系统总体技术架构)
2. [MySQL 数据库表结构设计 (DDL)](#二-mysql-数据库表结构设计-ddl)
3. [RESTful API 接口规范设计](#三-restful-api-接口规范设计)
4. [Python 后端工程骨架与核心模块实现](#四-python-后端工程骨架与核心模块实现)
5. [安全与风控核心链路保障](#五-安全与风控核心链路保障)
6. [部署运维与上线检查清单](#六-部署运维与上线检查清单)

---

## 一、 系统总体技术架构

系统专用于低频、高存活率的真人养号场景，禁止无人值守批量灌水。后端采用轻量单体架构，API 与服务层之间使用 Pydantic 类型约束。

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Web 表现层：Vue 3 + Vite + Element Plus              │
│       [候选审核工作台]  [账号阶段配置]  [目标社区池]  [模板库]  [风控限频]      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / RESTful API (JSON)
┌───────────────────────────────────▼────────────────────────────────────┐
│                  API 网关与接入层：FastAPI (Python 3.11+)               │
│          Pydantic v2 请求参数校验 / 全局异常捕获 / 跨域中间件 (CORS)     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│  FeedCrawlerService  │  │  DraftSynthesizer    │  │  RiskController      │
│  PRAW 轮询 New/Rising│  │  模板槽位注入/外链拦截│  │  429 断路器/频率漏桶 │
└──────────┬───────────┘  └──────────┬───────────┘  └──────────┬───────────┘
           │                         │                         │
           └─────────────────────────┼─────────────────────────┘
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│              异步排期调度层：APScheduler (AsyncIOScheduler)            │
│       5~30 分钟安全随机抖动延迟 / 账号执行互斥队列 / 定时 Shadowban 存活探测      │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┴───────────────────────────────┐
    ▼                                                               ▼
┌─────────────────────────────────────────┐     ┌──────────────────────────────────┐
│   PRAW 实例连接池 (Per-Account Session) │     │   持久化存储层：MySQL 8.0        │
│   独立 Script OAuth / 独立 Socks5 代理  │     │   InnoDB / utf8mb4 / 连接池      │
└─────────────────────────────────────────┘     └──────────────────────────────────┘
```

### 核心技术选型一览表

| 分层 | 组件 / 选型 | 版本要求 | 选型理由与架构考量 |
|:---|:---|:---|:---|
| **Web 前端** | Vue 3 + Element Plus + Pinia | Node 18+ / Vite 8 | 已交付完整可视化中控，具备零AI味、高密度专业中台质感。 |
| **API 框架** | FastAPI + Uvicorn | Python 3.11+ / FastAPI 0.115+ | 原生异步高性能、自动化 OpenAPI (Swagger) 契约、Pydantic v2 参数强校验。 |
| **ORM / 驱动** | SQLAlchemy 2.0 (AsyncIO) + aiomysql | SQLAlchemy 2.0+ | 纯异步非阻塞数据库访问，连接池弹性伸缩，支持复杂状态机事务。 |
| **关系型数据库**| MySQL (InnoDB) | MySQL 8.0.x+ | 字符集采用 `utf8mb4`，完整存储 Reddit 原生 Emoji、特殊多语言排版字符。 |
| **Reddit 客户端**| PRAW (Python Reddit API Wrapper) | 7.7.1+ | 官方推荐 Python 库，完整封装 OAuth 2.0 Token 自动刷新与速率配额握手。 |
| **任务调度** | APScheduler | 3.10+ | 支持以秒为精度的动态单次排期（`date` trigger），精确控制随机防风控延迟。 |

---

## 二、 MySQL 数据库表结构设计 (DDL)

> 字符集全部强制指定为 `utf8mb4`，排序规则指定为 `utf8mb4_unicode_ci`，防止由于 Reddit 帖子标题/评论含有 Emoji 或特殊字符导致写入失败。

```sql
-- 创建专用数据库
CREATE DATABASE IF NOT EXISTS `reddit_karma_pilot`
DEFAULT CHARACTER SET utf8mb4
DEFAULT COLLATE utf8mb4_unicode_ci;

USE `reddit_karma_pilot`;

-- --------------------------------------------------------
-- 1. 账号与生命周期表 (accounts)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `accounts`;
CREATE TABLE `accounts` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '账号主键ID',
  `username` VARCHAR(64) NOT NULL COMMENT 'Reddit 用户名 (如 u/CosmicVoyager_99)',
  `client_id` VARCHAR(64) NOT NULL COMMENT 'Reddit OAuth Script 应用 Client ID',
  `client_secret` VARCHAR(128) NOT NULL COMMENT 'Reddit OAuth Client Secret (加密存储)',
  `stage` ENUM('STAGE_1', 'STAGE_2', 'STAGE_3', 'STAGE_4') NOT NULL DEFAULT 'STAGE_2' COMMENT '当前养号阶段',
  `created_days_ago` INT UNSIGNED NOT NULL DEFAULT 5 COMMENT '账号注册天数',
  `comment_karma` INT NOT NULL DEFAULT 0 COMMENT '当前 Comment Karma',
  `link_karma` INT NOT NULL DEFAULT 0 COMMENT '当前 Link Karma',
  `daily_sent_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '今日已发评论数',
  `daily_limit` INT UNSIGNED NOT NULL DEFAULT 5 COMMENT '今日发送上限',
  `proxy_url` VARCHAR(255) DEFAULT NULL COMMENT '专属代理节点 (如 socks5://user:pass@host:port)',
  `is_cooling_down` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否处于冷却中 (0:就绪, 1:冷却中)',
  `cooldown_until` DATETIME DEFAULT NULL COMMENT '冷却结束时间戳',
  `status` ENUM('HEALTHY', 'RATE_LIMITED', 'RESTRICTED', 'BANNED') NOT NULL DEFAULT 'HEALTHY' COMMENT '健康状态',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Reddit 养号账号矩阵表';

-- --------------------------------------------------------
-- 2. 目标社区池表 (subreddits)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `subreddits`;
CREATE TABLE `subreddits` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '社区主键ID',
  `name` VARCHAR(64) NOT NULL COMMENT '社区代号 (如 r/AskReddit)',
  `badge` VARCHAR(32) NOT NULL DEFAULT '新手友好' COMMENT '分类标签',
  `min_karma` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '准入最低 Karma 门槛',
  `daily_limit` INT UNSIGNED NOT NULL DEFAULT 2 COMMENT '单日安全评论上限',
  `today_sent` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '今日在该社区已发数量',
  `is_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用监听 (1:启用, 0:停用)',
  `description` VARCHAR(255) DEFAULT '' COMMENT '社区规则与讨论方向说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_is_enabled` (`is_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='目标 Subreddit 社区池表';

-- --------------------------------------------------------
-- 3. 候选待审帖子表 (candidate_posts)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `candidate_posts`;
CREATE TABLE `candidate_posts` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `reddit_post_id` VARCHAR(32) NOT NULL COMMENT 'Reddit 原生帖子 ID (如 t3_1h8abcd)',
  `subreddit_name` VARCHAR(64) NOT NULL COMMENT '所属社区',
  `title` VARCHAR(512) NOT NULL COMMENT '帖子标题',
  `author` VARCHAR(64) DEFAULT NULL COMMENT '发帖者',
  `permalink` VARCHAR(512) NOT NULL COMMENT '帖子完整 URL',
  `selftext` TEXT DEFAULT NULL COMMENT '帖子正文快照',
  `score` INT NOT NULL DEFAULT 0 COMMENT 'Reddit 点赞数',
  `num_comments` INT NOT NULL DEFAULT 0 COMMENT '现有评论数',
  `upvote_ratio` DECIMAL(4,3) NOT NULL DEFAULT 1.000 COMMENT '赞同比例',
  `match_keyword` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '命中的求助信号词',
  `recommended_score` INT UNSIGNED NOT NULL DEFAULT 80 COMMENT '系统计算的推荐分 (0~100)',
  `recommended_reason` VARCHAR(255) DEFAULT '' COMMENT '推荐理由',
  `status` ENUM('PENDING', 'APPROVED', 'SKIPPED', 'DISPATCHED') NOT NULL DEFAULT 'PENDING' COMMENT '待审状态',
  `fetched_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取入库时间',
  `post_created_utc` DATETIME NOT NULL COMMENT '帖子在 Reddit 的发布时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_reddit_post_id` (`reddit_post_id`),
  KEY `idx_status_score` (`status`, `recommended_score` DESC),
  KEY `idx_subreddit` (`subreddit_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='候选待审帖子表';

-- --------------------------------------------------------
-- 4. 评论模板库表 (comment_templates)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `comment_templates`;
CREATE TABLE `comment_templates` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `tone` VARCHAR(32) NOT NULL DEFAULT '真诚经验' COMMENT '语气分类 (真诚经验/轻度建议/专业探讨/求稳中立)',
  `template_text` TEXT NOT NULL COMMENT '模板主体内容 (支持 {keyword} 占位符)',
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `usage_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '累计引用次数',
  `last_used_at` DATETIME DEFAULT NULL COMMENT '最近一次引用时间 (24h去重计算基准)',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_tone` (`tone`),
  KEY `idx_last_used_at` (`last_used_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='评论模板库表';

-- --------------------------------------------------------
-- 5. 待排期任务队列流水表 (dispatch_tasks)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `dispatch_tasks`;
CREATE TABLE `dispatch_tasks` (
  `id` VARCHAR(64) NOT NULL COMMENT '任务唯一流水号 (UUID)',
  `account_id` BIGINT UNSIGNED NOT NULL COMMENT '关联执行账号 ID',
  `candidate_post_id` BIGINT UNSIGNED NOT NULL COMMENT '关联候选帖子 ID',
  `template_id` BIGINT UNSIGNED DEFAULT NULL COMMENT '关联模板 ID',
  `final_comment_text` TEXT NOT NULL COMMENT '人工确认的外发评论正文',
  `delay_seconds` INT UNSIGNED NOT NULL DEFAULT 600 COMMENT '随机安全延迟秒数 (300~1800)',
  `scheduled_at` DATETIME NOT NULL COMMENT '计划实际触发时间 (当前时间 + delay_seconds)',
  `status` ENUM('QUEUED', 'EXECUTING', 'SUCCESS', 'FAILED', 'CANCELLED') NOT NULL DEFAULT 'QUEUED' COMMENT '任务状态',
  `reddit_comment_id` VARCHAR(32) DEFAULT NULL COMMENT '成功发出的 Reddit 评论 Fullname (如 t1_xxx)',
  `error_message` VARCHAR(512) DEFAULT NULL COMMENT '失败异常信息',
  `executed_at` DATETIME DEFAULT NULL COMMENT '真实触发执行时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_account_status` (`account_id`, `status`),
  KEY `idx_scheduled_at` (`scheduled_at`, `status`),
  CONSTRAINT `fk_dispatch_account` FOREIGN KEY (`account_id`) REFERENCES `accounts` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='发帖异步调度排期表';

-- --------------------------------------------------------
-- 6. 全生命周期审计与存活日志表 (audit_logs)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `audit_logs`;
CREATE TABLE `audit_logs` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `account_username` VARCHAR(64) NOT NULL COMMENT '执行用户名',
  `subreddit` VARCHAR(64) NOT NULL COMMENT '目标社区',
  `reddit_post_id` VARCHAR(32) NOT NULL COMMENT '目标帖子 ID',
  `post_title` VARCHAR(512) NOT NULL COMMENT '帖子标题',
  `reddit_comment_id` VARCHAR(32) DEFAULT NULL COMMENT '发出的评论 ID',
  `comment_snippet` TEXT NOT NULL COMMENT '评论摘要快照',
  `delay_seconds` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '经历的安全排队延迟 (秒)',
  `status` ENUM('SUCCESS', 'SKIPPED', 'RATE_LIMITED', 'INTERCEPTED', 'ERROR') NOT NULL DEFAULT 'SUCCESS',
  `shadowban_status` ENUM('PENDING', 'VERIFIED_PUBLIC', 'SHADOWBANNED', 'DELETED') NOT NULL DEFAULT 'PENDING' COMMENT '公开存活状态',
  `shadowban_checked_at` DATETIME DEFAULT NULL COMMENT '最近一次存活探针探测时间',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  PRIMARY KEY (`id`),
  KEY `idx_created_at` (`created_at` DESC),
  KEY `idx_account` (`account_username`),
  KEY `idx_shadowban` (`shadowban_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作与审计全量日志表';

-- --------------------------------------------------------
-- 7. 风控参数与断路器全局配置表 (risk_settings)
-- --------------------------------------------------------
DROP TABLE IF EXISTS `risk_settings`;
CREATE TABLE `risk_settings` (
  `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `min_delay_minutes` INT UNSIGNED NOT NULL DEFAULT 5 COMMENT '单次发帖最小随机延迟 (分钟)',
  `max_delay_minutes` INT UNSIGNED NOT NULL DEFAULT 30 COMMENT '单次发帖最大随机延迟 (分钟)',
  `max_daily_comments_per_account` INT UNSIGNED NOT NULL DEFAULT 5 COMMENT '单账号单日硬上限',
  `max_daily_comments_per_sub` INT UNSIGNED NOT NULL DEFAULT 2 COMMENT '同社区单日硬上限',
  `circuit_breaker_active` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '429 断路器状态 (1:触发熔断, 0:正常)',
  `circuit_breaker_reason` VARCHAR(255) DEFAULT NULL COMMENT '断路触发原因',
  `sensitive_keywords` JSON NOT NULL COMMENT '违禁词/敏感特征列表 (JSON 数组格式)',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='风控规则与断路器配置表';

-- 初始化默认风控配置
INSERT INTO `risk_settings` 
(`id`, `min_delay_minutes`, `max_delay_minutes`, `max_daily_comments_per_account`, `max_daily_comments_per_sub`, `circuit_breaker_active`, `sensitive_keywords`) 
VALUES 
(1, 5, 30, 5, 2, 0, '["http://", "https://", "t.me", "wa.me", "wechat", "微信", "whatsapp", "telegram", "contact us", "buy now", "discount"]')
ON DUPLICATE KEY UPDATE `id`=1;
```

---

## 三、 RESTful API 接口规范设计

所有 API 挂载于 `/api/v1` 命名空间下，数据统一返回格式：
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 1. 审核工作台模块 (Workbench)

#### 1.1 获取今日待审核候选帖子列表
- **Endpoint**: `GET /api/v1/workbench/candidates`
- **Query Params**:
  - `status`: `PENDING` (默认) | `ALL`
  - `limit`: `20`
- **Response Example**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 101,
      "redditPostId": "t3_1h8x9p",
      "subreddit": "r/webdev",
      "title": "Best way to handle simple contact forms without backend in 2026?",
      "content": "Building a static landing page. Don't want a heavy backend server just for email forwarding. What's the go-to solution?",
      "score": 42,
      "numComments": 8,
      "upvoteRatio": 0.94,
      "matchKeyword": "best way",
      "recommendedScore": 95,
      "recommendedReason": "低评论基数、高问答求助意图，适宜破冰回复",
      "createdAgo": "45m ago",
      "draftComment": "我之前也遇到过类似问题，后来发现像 Formspree 或者 Cloudflare Workers 会更稳定一点，免去维护服务器的麻烦。"
    }
  ]
}
```

#### 1.2 人工单键批复或跳过 (HITL 核心入口)
- **Endpoint**: `POST /api/v1/workbench/candidates/{id}/action`
- **Request Body**:
```json
{
  "action": "APPROVE", // APPROVE (批复排期) | SKIP (跳过)
  "accountId": 1,
  "finalComment": "我之前也遇到过类似问题，后来发现像 Cloudflare Workers 会更稳定一点。",
  "customDelayMinutes": null // 为空时由系统在 5~30 分钟内随机生成
}
```
- **Response Example**:
```json
{
  "code": 200,
  "message": "任务已安全排入调度队列",
  "data": {
    "taskId": "task_8f7b2c9d",
    "accountId": 1,
    "delaySeconds": 780,
    "scheduledAt": "2026-11-05T18:02:15Z",
    "todaySentAfter": 3,
    "todayLimit": 5
  }
}
```

---

### 2. 账号与生命周期模块 (Accounts)

#### 2.1 获取账号列表与当前运行态
- **Endpoint**: `GET /api/v1/accounts`
- **Response Example**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": 1,
      "username": "u/CosmicVoyager_99",
      "clientId": "app_oauth_xxxx9182",
      "stage": "STAGE_2",
      "createdDaysAgo": 5,
      "commentKarma": 46,
      "linkKarma": 2,
      "dailySentCount": 2,
      "dailyLimit": 5,
      "isCoolingDown": true,
      "cooldownRemainingSeconds": 480,
      "status": "HEALTHY"
    }
  ]
}
```

#### 2.2 切换账号生命周期阶段
- **Endpoint**: `PATCH /api/v1/accounts/{id}/stage`
- **Request Body**:
```json
{
  "stage": "STAGE_3" // STAGE_1 | STAGE_2 | STAGE_3 | STAGE_4
}
```

#### 2.3 测试账号 API 连通性握手 (PRAW Handshake)
- **Endpoint**: `POST /api/v1/accounts/{id}/test-handshake`
- **Response Example**:
```json
{
  "code": 200,
  "message": "OAuth 握手成功",
  "data": {
    "username": "u/CosmicVoyager_99",
    "commentKarma": 46,
    "linkKarma": 2,
    "isSuspended": false,
    "hasVerifiedEmail": true
  }
}
```

---

### 3. 目标社区池模块 (Subreddits)

- `GET /api/v1/subreddits`: 获取社区列表及其当日发出量、监控状态；
- `POST /api/v1/subreddits`: 新增目标社区（入参校验并自动清洗 `r/` 字符）；
- `PUT /api/v1/subreddits/{id}/toggle`: 切换开启/暂停监听；
- `POST /api/v1/subreddits/{id}/scan-now`: 触发即时单版抓取巡检。

---

### 4. 评论模板库模块 (Templates)

- `GET /api/v1/templates`: 获取模板列表，带 24 小时内是否使用过的冷却标记；
- `POST /api/v1/templates`: 新增评论模板（校验是否含外链或微信号）；
- `DELETE /api/v1/templates/{id}`: 删除停用模板。

---

### 5. 风控治理与 429 熔断模块 (Risk Control)

#### 5.1 获取与更新风控全局参数
- **Endpoint**: `GET /api/v1/risk-control/settings`
- **Endpoint**: `PUT /api/v1/risk-control/settings`
- **Request Body**:
```json
{
  "minDelayMinutes": 5,
  "maxDelayMinutes": 30,
  "maxDailyCommentsPerAccount": 5,
  "sensitiveKeywords": ["http://", "https://", "t.me", "wa.me", "微信", "tg"]
}
```

#### 5.2 触发或解除 429 熔断保护
- **Endpoint**: `POST /api/v1/risk-control/circuit-breaker`
- **Request Body**:
```json
{
  "action": "TRIP", // TRIP (手动触发熔断保护) | RESET (解除熔断并恢复发信)
  "reason": "检测到上游响应异常，人工挂起排期任务"
}
```

---

### 6. 执行与审计日志模块 (Audit Logs)

- `GET /api/v1/logs?status=ALL&page=1&pageSize=20`: 分页拉取操作全流水；
- `POST /api/v1/logs/{id}/probe-shadowban`: 手动对指定评论触发一次匿名公开存活探测；
- `GET /api/v1/logs/export`: 导出 CSV 审计日志文件。

---

## 四、 Python 后端工程骨架与核心模块实现

### 1. 推荐工程目录树

```
reddit-pilot-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 主程序入口与中间件
│   ├── core/
│   │   ├── config.py            # 读取环境变量与数据库连接配置
│   │   └── security.py          # 敏感词过滤正则与外链校验工具
│   ├── db/
│   │   ├── session.py           # SQLAlchemy 异步引擎与 SessionLocal
│   │   └── base_class.py        # 声明性 Base
│   ├── models/                  # SQLAlchemy 数据库映射实体 (对应 DDL)
│   │   ├── account.py
│   │   ├── subreddit.py
│   │   ├── candidate_post.py
│   │   ├── comment_template.py
│   │   ├── dispatch_task.py
│   │   └── audit_log.py
│   ├── schemas/                 # Pydantic v2 请求与响应定义
│   │   ├── candidate_schema.py
│   │   └── account_schema.py
│   ├── services/                # 核心业务逻辑实现
│   │   ├── praw_pool.py         # PRAW 实例管理与代理挂载
│   │   ├── feed_crawler.py      # 定时 New/Rising 监听与意图打分
│   │   ├── task_dispatcher.py   # APScheduler 延迟排期与真实外发
│   │   └── shadowban_probe.py   # 匿名公开端点存活探针
│   └── api/
│       └── v1/
│           ├── api.py           # 集中路由分发
│           ├── endpoints/
│           │   ├── workbench.py
│           │   ├── accounts.py
│           │   ├── subreddits.py
│           │   ├── templates.py
│           │   ├── risk_control.py
│           │   └── logs.py
├── requirements.txt             # 依赖声明
├── start_backend.py             # 快速启动引导脚本
└── .env                         # 数据库密码与加密密钥配置
```

### 2. 核心模块代码骨架

#### (1) `app/core/security.py` —— 静态风控与外链强拦截
```python
import re
from typing import Tuple, List

URL_PATTERN = re.compile(r'(https?://|www\.|\.com|\.org|\.io|\.xyz)', re.IGNORECASE)
CONTACT_PATTERN = re.compile(r'(t\.me|wa\.me|wechat|微信|whatsapp|telegram|v信|加v)', re.IGNORECASE)

def validate_comment_safety(text: str, custom_blacklist: List[str]) -> Tuple[bool, str]:
    """静态风控校验：坚决阻断外链、联系方式及营销词汇"""
    if URL_PATTERN.search(text):
        return False, "拦截原因：评论内容严禁包含任何外部链接 (URL)！"
    
    if CONTACT_PATTERN.search(text):
        return False, "拦截原因：评论内容严禁包含私域联系方式 (微信/Telegram/WhatsApp)！"
    
    for kw in custom_blacklist:
        if kw.lower() in text.lower():
            return False, f"拦截原因：命中了风控黑名单关键词 '{kw}'"
            
    if len(text.strip()) < 8:
        return False, "拦截原因：评论过短，容易被判定为 Low Effort Spam。"
        
    return True, "安全合规"
```

#### (2) `app/services/praw_pool.py` —— PRAW 独立 Script 实例管理
```python
import praw
from app.models.account import Account

class PrawClientPool:
    """每个 Reddit 账号独享独立的 PRAW 实例，保证凭据与 User-Agent 隔离"""
    _instances = {}

    @classmethod
    def get_client(cls, account: Account) -> praw.Reddit:
        if account.id in cls._instances:
            return cls._instances[account.id]

        reddit = praw.Reddit(
            client_id=account.client_id,
            client_secret=account.client_secret,
            user_agent=f"desktop:reddit-karma-pilot:v1.0.0 (by /u/{account.username})",
            requestor_kwargs={"proxies": {"https": account.proxy_url, "http": account.proxy_url}} if account.proxy_url else {}
        )
        # 设置为只读模式或绑定刷新 Token
        cls._instances[account.id] = reddit
        return reddit
```

#### (3) `app/services/task_dispatcher.py` —— APScheduler 随机防风控排期引擎
```python
import random
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.db.session import AsyncSessionLocal
from app.services.praw_pool import PrawClientPool

scheduler = AsyncIOScheduler()

async def execute_delayed_comment(task_id: str, account_id: int, reddit_post_id: str, text: str):
    """到达计划时间后执行的真实发帖动作"""
    async with AsyncSessionLocal() as session:
        # 1. 检查断路器是否被触发
        # 2. 调用 PRAW 发帖
        # 3. 记录 audit_logs 表
        # 4. 注册 15 分钟后的 Shadowban 探针任务
        pass

def schedule_comment_task(account_id: int, post_id: str, text: str, min_delay_m=5, max_delay_m=30) -> Tuple[str, datetime, int]:
    """生成带随机防风控延迟的任务排期"""
    delay_seconds = random.randint(min_delay_m * 60, max_delay_m * 60)
    scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    scheduler.add_job(
        execute_delayed_comment,
        trigger="date",
        run_date=scheduled_at,
        args=[task_id, account_id, post_id, text],
        id=task_id
    )
    return task_id, scheduled_at, delay_seconds
```

---

## 五、 安全与风控核心链路保障

| 维度 | 潜在封号隐患 | 系统物理防御手段 |
|:---|:---|:---|
| **设备指纹** | 浏览器同机指纹关联 | 每个账号配置独立的 `proxy_url`，后端 PRAW 请求直接经由隔离隧道发出，无共享 Cookie 串扰。 |
| **高频触发** | 机器连续发帖触发 429 | **双重漏斗频控**：单日硬上限（新号仅 2~5 条）+ 强制 5~30 分钟随机抖动延迟，杜绝秒级连发。 |
| **文本指纹** | 重复模板被 Spam 过滤器捕获 | 数据库对已使用模板记录 `last_used_at`，**24 小时内相同模板直接锁定去重**；支持占位符动态扰动。 |
| **隐形封禁** | 被版主/机器人 Shadowban 无感知 | 发帖 15 分钟后由 `ShadowbanProbeService` 经**未登录独立 IP** 请求帖子公开接口，实时捕获 `[removed]` 状态。 |
| **上游熔断** | 出现 429 时持续请求导致永久封禁 | 一旦捕获 Reddit HTTP 429，立即触发 `circuit_breaker_active = 1`，挂起调度队列并锁定外发。 |

---

## 六、 部署运维与上线检查清单

### 1. 部署依赖要求
```bash
# 安装 Python 3.11 核心依赖
pip install fastapi uvicorn[standard] sqlalchemy[asyncio] aiomysql pymysql praw apscheduler pydantic-settings
```

### 2. 数据库快速初始化
```bash
# 导入建表脚本
mysql -u root -p < init_schema.sql
```

### 3. 上线运行前 5 步检查清单
- [ ] **数据库连接池验证**：确认 `aiomysql` 能正常连接 MySQL 8.0 并支持 `utf8mb4`；
- [ ] **Reddit Script 应用权限测试**：在 [Accounts 页面](file:///c:/Users/33046/Desktop/reddit.ai/frontend/src/views/Accounts.vue) 点击“测试握手”，确保返回 HTTP 200 及真实 Karma 分数；
- [ ] **风控黑名单确认**：确认 `risk_settings` 表中已涵盖常见外链与私域营销词；
- [ ] **冷启动配额确认**：新导入的账号必须严格设置在 `STAGE_1`（纯浏览）或 `STAGE_2`（2~5条/日），严禁一开始直接放开 10 条/日；
- [ ] **调度器保活**：生产环境下推荐使用 `systemd` 或 Docker 托管 FastAPI 守护进程，保障 APScheduler 异步延迟排期不掉线。

---
*文档归档位置：[`c:\Users\33046\Desktop\reddit.ai\REDDIT_KARMA_PILOT_IMPLEMENTATION_PLAN.md`](file:///c:/Users/33046/Desktop/reddit.ai/REDDIT_KARMA_PILOT_IMPLEMENTATION_PLAN.md)*

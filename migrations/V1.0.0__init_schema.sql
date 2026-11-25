-- ==============================================================================
-- Migration: V1.0.0__init_schema.sql
-- Description: Initialize core schema for Reddit Karma Pilot
-- Standard: Follows db-migration-manager skill guidelines (utf8mb4, zero-downtime)
-- ==============================================================================

-- 1. 账号与生命周期表 (accounts)
CREATE TABLE IF NOT EXISTS `accounts` (
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

-- 2. 目标社区池表 (subreddits)
CREATE TABLE IF NOT EXISTS `subreddits` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '社区主键ID',
  `name` VARCHAR(64) NOT NULL COMMENT '社区代号 (如 r/AskReddit)',
  `badge` VARCHAR(32) NOT NULL DEFAULT '新手友好' COMMENT '分类标签',
  `min_karma` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '准入最低 Karma 门槛',
  `daily_limit` INT UNSIGNED NOT NULL DEFAULT 2 COMMENT '单日安全评论上限',
  `today_sent` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '今日在该社区已发数量',
  `is_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用监听 (1:启用, 0:停用)',
  `description` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '社区规则与讨论方向说明',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_name` (`name`),
  KEY `idx_is_enabled` (`is_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='目标 Subreddit 社区池表';

-- 3. 候选待审帖子表 (candidate_posts)
CREATE TABLE IF NOT EXISTS `candidate_posts` (
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
  `recommended_reason` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '推荐理由',
  `draft_comment` TEXT DEFAULT NULL COMMENT '预生成高拟真去AI味草稿',
  `status` ENUM('PENDING', 'APPROVED', 'SKIPPED', 'DISPATCHED') NOT NULL DEFAULT 'PENDING' COMMENT '待审状态',
  `fetched_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '抓取入库时间',
  `post_created_utc` DATETIME NOT NULL COMMENT '帖子在 Reddit 的发布时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_reddit_post_id` (`reddit_post_id`),
  KEY `idx_status_score` (`status`, `recommended_score` DESC),
  KEY `idx_subreddit` (`subreddit_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='候选待审帖子表';

-- 4. 评论模板库表 (comment_templates)
CREATE TABLE IF NOT EXISTS `comment_templates` (
  `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `tone` VARCHAR(32) NOT NULL DEFAULT '真诚经验' COMMENT '语气分类 (真诚经验/实用建议/专业探讨/求稳中立)',
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

-- 5. 待排期任务队列流水表 (dispatch_tasks)
CREATE TABLE IF NOT EXISTS `dispatch_tasks` (
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

-- 6. 全生命周期审计与存活日志表 (audit_logs)
CREATE TABLE IF NOT EXISTS `audit_logs` (
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

-- 7. 风控参数与断路器全局配置表 (risk_settings)
CREATE TABLE IF NOT EXISTS `risk_settings` (
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

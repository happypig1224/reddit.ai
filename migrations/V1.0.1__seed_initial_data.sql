-- ==============================================================================
-- Migration: V1.0.1__seed_initial_data.sql
-- Description: Production seed: risk settings, recommended subreddits, clean templates
-- Standard: Compliant with db-migration-manager (No dummy test data in production)
-- ==============================================================================

-- 1. 初始化风控参数与断路器全局配置
INSERT INTO `risk_settings` 
(`id`, `min_delay_minutes`, `max_delay_minutes`, `max_daily_comments_per_account`, `max_daily_comments_per_sub`, `circuit_breaker_active`, `circuit_breaker_reason`, `sensitive_keywords`) 
VALUES 
(1, 5, 30, 5, 2, 0, NULL, '["http://", "https://", "t.me", "wa.me", "wechat", "微信", "whatsapp", "telegram", "contact us", "buy now", "discount", "promo", "v信", "加v"]')
ON DUPLICATE KEY UPDATE 
  `min_delay_minutes` = VALUES(`min_delay_minutes`),
  `max_delay_minutes` = VALUES(`max_delay_minutes`),
  `max_daily_comments_per_account` = VALUES(`max_daily_comments_per_account`),
  `max_daily_comments_per_sub` = VALUES(`max_daily_comments_per_sub`);

-- 2. 初始化初始推荐目标社区池 (干净生产默认社区)
INSERT INTO `subreddits` (`name`, `badge`, `min_karma`, `daily_limit`, `today_sent`, `is_enabled`, `description`) VALUES
('r/AskReddit', '新手友好', 0, 2, 0, 1, '高流量通用问答社区，适合分享真实生活经验破冰'),
('r/NoStupidQuestions', '新手友好', 0, 2, 0, 1, '友善互助生活常识问答，低门槛无压力'),
('r/mildlyinteresting', '休闲生活', 5, 2, 0, 1, '轻松图文互动跟帖，适合自然互动'),
('r/webdev', '技术垂直', 30, 1, 0, 1, 'Web 开发讨论社区，提供实际技术排查经验'),
('r/CasualConversation', '友好交流', 0, 2, 0, 1, '日常闲聊与经验分享社区，去商业化纯交流')
ON DUPLICATE KEY UPDATE 
  `badge` = VALUES(`badge`),
  `description` = VALUES(`description`);

-- 3. 初始化高拟真无AI味评论模板库
INSERT INTO `comment_templates` (`tone`, `template_text`, `is_active`, `usage_count`, `last_used_at`) VALUES
('真诚经验', '我之前在处理类似问题时也踩过坑，后来发现用精简架构比搭一整套复杂系统要稳得多，排查问题也方便。', 1, 0, NULL),
('实用建议', '如果只是早期验证或者轻量业务，官方免费额度一般完全够用了，没必要一上来就把链路搞太重。', 1, 0, NULL),
('中立对比', '主要看具体的使用场景和并发要求。如果追求轻量快速上线，方案 A 比较顺手；要是后续需要大量定制，方案 B 扩展性会好些。', 1, 0, NULL),
('求稳探讨', '好奇大家一般怎么评估这类工具的维护成本？我目前在看的几个方案各有优劣，还在权衡迁移代价。', 1, 0, NULL)
ON DUPLICATE KEY UPDATE 
  `template_text` = VALUES(`template_text`);

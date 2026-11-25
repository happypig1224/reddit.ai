# 🛡️ Reddit 自动化反作弊防御规约与词库参考

本文档作为 `reddit-karma-pilot` Skill 的底层风控参考手册，汇总海外黑产对抗、Reddit Spam 识别与 AutoModerator 过滤特征。

---

## 一、 静态风控强拦截规则集 (Hard Rules)

### 1. 链接与协议正则匹配
任何新号在破冰期（阶段 1 与阶段 2）一律禁止外链：
```regex
(https?:\/\/|www\.|\.com|\.org|\.net|\.io|\.xyz|\.ai|\.app|\.me|\.link|\.page)
```

### 2. 私域联系方式强拦截
```regex
(t\.me\/|wa\.me\/|telegram|whatsapp|wechat|weixin|discord\.gg|联系方式|微信|加微|v信|私信我|dm me for)
```

### 3. 硬广与促销关键词黑名单
```json
[
  "discount", "promo code", "coupon", "limited offer", "buy now", 
  "order here", "affiliate", "pricing", "sign up here", "check out my",
  "my service", "our company", "lowest price", "special deal"
]
```

---

## 二、 常用大版块 AutoModerator 准入要求矩阵 (2025/2026 实测)

| Subreddit | 讨论主题 | 最低 Comment Karma | 最低账号年龄 | 审核敏感点 |
|:---|:---|:---|:---|:---|
| **r/AskReddit** | 综合问答 | 0 (零门槛) | 0 | 标题必须是疑问句且不能包含自身答案 |
| **r/NoStupidQuestions** | 生活常识 | 0 | 0 | 友好氛围，禁争论 |
| **r/mildlyinteresting** | 趣味图文 | 0 | 0 | 评论需与图文强相关 |
| **r/webdev** | 技术与前端 | ≥ 10 | ≥ 7 天 | 严禁自我推销（Self-Promotion Rule） |
| **r/technology** | 科技新闻 | ≥ 20 | ≥ 14 天 | 政治与商业营销极度敏感 |
| **r/startups** | 创业商业 | ≥ 50 | ≥ 30 天 | 极度严格，需通过“9:1 贡献法则” |
| **r/SaaS** | 软件运营 | ≥ 30 | ≥ 14 天 | 频繁人工巡检，软广易被举报 |

---

## 三、 CQS (Contributor Quality Score) 评分恢复动作指南

如果账号被 Reddit 打上了 `Low` 或 `Lowest` 的 CQS 标签：
1. **停止一切发帖**：至少静默 48 小时；
2. **纯人类行为模拟**：
   - 手机端或指纹浏览器中正常滚动浏览；
   - 关注 5 个新版块；
   - 给 5~10 篇热门帖子点赞（Upvote）；
3. **安全回血评论**：
   - 只在 `r/AskReddit` 找生活类提问；
   - 提交 1~2 条纯个人真实感受回复；
   - 获得 3 个以上路人 Upvote 后，CQS 评分将在 3~7 天内自动恢复为 `Moderate` 或 `High`。

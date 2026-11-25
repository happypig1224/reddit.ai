---
name: reddit-karma-pilot
description: Expert operational guide and technical standard for safe Reddit Karma growth, anti-ban risk control, PRAW script development, and account warm-up. Use when developing or operating Reddit automation, configuring PRAW clients, evaluating account shadowban status, or tuning subreddit warm-up rhythms.
---

# Reddit Karma Pilot: 养号与防风控专家操作指南

本 Skill 汇总了 Reddit 官方开发者政策（Developer Terms）、PRAW 最佳实践、全球反垃圾系统（CQS 与 Spam Algorithm）与海外资深 Reddit 运营者的开源实战经验，专门用于指导开发与运营 **安全、高存活率、去AI味** 的 Reddit 账号。

---

## 一、 Reddit 官方 API 规约与技术约束 (2025/2026 最新标准)

### 1. 速率配额与调用上限 (Rate Limits)
- **OAuth 认证应用 (Script 类型)**：
  - 限制：**100 次查询/分钟 (QPM)**；
  - 采用 **10 分钟滑动窗口（Sliding Window）** 统计，10 分钟内突发请求总量不得超过 **1,000 次**；
  - 超出配额时 Reddit 会返回 `HTTP 429 Too Many Requests`，并在响应头携带 `Retry-After` 秒数；
- **免登录（Unauthenticated）接口**：
  - 官方已基本封锁免登录写入操作，仅支持有限的低频只读公开探测（用于 Shadowban 存活检查）。

### 2. 写入操作内部限频 ("You are doing that too much")
- Reddit 对发帖（Submit）、发评论（Comment）等写操作实行**未公开的独立行为限频**。
- **PRAW 处理机制**：
  - 默认参数 `ratelimit_seconds=5`：如果 Reddit 要求等待 ≤ 5 秒，PRAW 自动休眠重试；如果等待要求超过 5 秒，PRAW 会直接抛出 `RedditAPIException`。
  - **生产环境配置规范**：
    ```python
    import praw

    reddit = praw.Reddit(
        client_id="YOUR_CLIENT_ID",
        client_secret="YOUR_CLIENT_SECRET",
        user_agent="desktop:reddit-karma-pilot:v1.0.0 (by /u/YourUsername)",
        ratelimit_seconds=300,  # 允许 PRAW 在遇到小额限频时自动退避等待最多 5 分钟
    )
    ```

### 3. User-Agent 规范标准
- Reddit 严格审查客户端的 `User-Agent`，使用通用浏览器字符串或空字符串会被直接拉黑。
- **官方推荐格式**：`<platform>:<app ID>:<version string> (by /u/<reddit username>)`
- **示例**：`desktop:reddit-karma-pilot:v1.0.0 (by /u/CosmicVoyager_99)`

---

## 二、 Reddit 核心反作弊机制与防风控底层逻辑

### 1. CQS (Contributor Quality Score) 贡献者质量分
Reddit 内部维护了从 `Lowest` 到 `Highest` 的动态信誉评分系统：
- **评估维度**：账号年龄、邮箱验证、绑定的手机号、历史互动留存率、IP 信誉、被举报/踩（Downvote）比例；
- **影响**：大部分主流活跃 Subreddit 的 AutoModerator 会自动拦截 CQS 评级为 `Lowest` 或 `Low` 的用户发言，导致其发言自动进入垃圾箱。

### 2. AutoModerator 自动化审查墙
各大 Subreddit 通过 YAML 脚本配置了严格的进门门槛：
- **Account Age**：常见要求为 7 天、14 天、30 天甚至 90 天；
- **Comment Karma**：要求 10~500 不等的纯评论 Karma（**注意：Reddit 板块对 Comment Karma 的信任度远高于 Post Karma**，发帖灌水得来的 Karma 无法通过严苛版块审查）。

### 3. Shadowban（隐形封禁）触发特征
Shadowban 是 Reddit 最常见的惩罚手段——账号表面显示一切正常，但所有帖子和评论对公众不可见，个人主页在无痕模式下提示“User not found”。
- **致命触发行为**：
  1. ❌ **新号前 7 天发外链**（即便是短链接、文档链接，都会被全局过滤器秒封）；
  2. ❌ **使用机房数据中心代理（Datacenter IP）或低端公共 VPN**；
  3. ❌ **多个小号在同浏览器、同 IP 下频繁切换**；
  4. ❌ **发布高相似度/重复复制粘贴的评论**；
  5. ❌ **跨多个 Subreddit 频繁提及相同的产品词或品牌词**。

---

## 三、 四阶段科学养号节奏 (Warm-Up Playbook)

```
[阶段 1: 冷启动潜伏] ──> [阶段 2: 温和破冰] ──> [阶段 3: 进阶互动] ──> [阶段 4: 垂直渗透]
    (Day 1-3)               (Day 4-7)               (Week 2)             (Karma ≥ 100)
    0条评论/日              2-5条评论/日            3-8条评论/日          5-10条评论/日
    只点赞/只加入板块       绝对无外链/低门槛问答    参与深度探讨/低频发帖  谨慎软性渗透
```

| 阶段 | 周期 | 核心动作 | 评论配额 | 关键禁忌 |
|:---|:---|:---|:---|:---|
| **阶段 1：冷启动潜伏** | 第 1–3 天 | 验证邮箱、上传头像、完善个人简介。加入 10~15 个主流大版（`r/AskReddit`, `r/mildlyinteresting`）。仅自然滚动浏览、偶尔点赞（Upvote）。 | **0 条/日** | **严禁任何评论、发帖或发外链**。 |
| **阶段 2：温和破冰** | 第 4–7 天 | 在零门槛通用问答版块（`r/AskReddit`, `r/NoStupidQuestions`）针对真实经验提问发表真诚简短观点。 | **2–5 条/日** | 严禁外链、严禁提及任何品牌或商业工具。两次评论间隔保持 **15~30 分钟**。 |
| **阶段 3：进阶互动** | 第 2 周 | Comment Karma 达到 30~50 之后，可逐步进入技术、设计或兴趣圈子（如 `r/webdev`），提供有价值的经验答疑。 | **3–8 条/日** | 严禁生硬引流；同版块单日不超过 2 条；避免情绪化争论。 |
| **阶段 4：垂直渗透** | Karma ≥ 100 | 账号建立起稳定的人类信用画象。可进入目标垂直行业版块，参与行业讨论，作为第三方视角提供中立建议。 | **5–10 条/日** | 依然坚持“90% 贡献纯价值，10% 顺带中立提及”，切勿发硬广。 |

---

## 四、 社区池挑选与候选帖打分模型

### 1. 推荐新手友好 Subreddit 池
- `r/AskReddit`：流量极大、评论活跃、无门槛，适合分享生活趣事或简短观点；
- `r/NoStupidQuestions`：常识生活疑问，答题氛围友善，容易获得真诚赞同；
- `r/mildlyinteresting`：轻松图文互动，跟帖门槛低；
- `r/CasualConversation`：纯交流版块，适合练习日常对话口吻。

### 2. 候选帖子筛选标准 (Candidate Filter)
优先抓取符合以下特征的帖子：
1. **发布时间**：在 **24 小时以内**（优先考虑发布 30 分钟 ~ 3 小时的 `rising` 帖子，抢占前排评论位）；
2. **评论基数**：现有评论数在 **5 ~ 30 条** 之间（评论太少帖子可能沉底，评论超过 100 条新回复基本无人阅读）；
3. **求助信号词**（满足其一）：
   - `"recommend"` / `"looking for"` / `"alternative"`
   - `"has anyone used"` / `"what do you think"`
   - `"is it worth"` / `"how do I"` / `"any suggestions"`
4. **排除规则**：帖子被管理员锁定（`locked: true`）、作者已被封禁或内容包含营销互撕。

---

## 五、 评论草稿生成与去“AI味”口吻标准

### 1. 必须规避的“AI 味”套路
- ❌ **公文式套话**：“In conclusion...”, “It is worth noting that...”, “As an AI...”, “Here are 5 key points...”;
- ❌ **排比句与小标题**：Reddit 真实用户在手机端聊天从不使用 `1. 2. 3.` 严密小论文；
- ❌ **过度热情与客服腔**：“Hope this helps! Feel free to reach out if you have any questions!”（典型的营销号特征）。

### 2. 推荐的高拟真真人表达风格
- **真诚经验型**：
  > *"I ran into the same issue a few months back. Ended up using Cloudflare Workers since it was much simpler to maintain without running a full server."*
- **实用建议型**：
  > *"If you're just testing the waters, the free tier is usually more than enough. No need to overcomplicate it early on."*
- **中立对比型**：
  > *"Really depends on your budget. For lightweight stuff option A works fine, but once you scale you'll probably want B."*

---

## 六、 生产代码实现标准 (PRAW + Shadowban 探针)

### 1. 独立客户端与网络代理挂载
```python
import praw

def create_isolated_praw_client(username: str, client_id: str, client_secret: str, proxy_url: str = None) -> praw.Reddit:
    """每个账号配置独立的 User-Agent 和住宅代理"""
    requestor_kwargs = {}
    if proxy_url:
        requestor_kwargs["proxies"] = {
            "http": proxy_url,
            "https": proxy_url
        }
    
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=f"desktop:reddit-karma-pilot:v1.0.0 (by /u/{username})",
        ratelimit_seconds=300,
        requestor_kwargs=requestor_kwargs
    )
```

### 2. Shadowban 匿名存活探测探针
```python
import httpx

async def probe_comment_public_status(subreddit: str, post_id: str, comment_id: str) -> str:
    """使用未登录的匿名独立 IP 访问 Reddit 公开 JSON 接口，探测评论是否存活"""
    url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}/_/{comment_id}.json"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 404:
                return "SHADOWBANNED"
            data = resp.json()
            # 检查评论正文是否为 [removed] 或 [deleted]
            comments = data[1]["data"]["children"]
            if not comments:
                return "REMOVED"
            body = comments[0]["data"].get("body", "")
            if body in ["[removed]", "[deleted]"]:
                return "REMOVED"
            return "VERIFIED_PUBLIC"
        except Exception:
            return "PENDING"
```

---

## 七、 异常处理与自愈指南 (Runbook)

1. **遇到 HTTP 429 或 `RATELIMIT` 异常**：
   - 系统必须立即设置 `circuit_breaker_active = 1`；
   - 挂起该账号后续所有队列任务；
   - 执行指数退避等待（至少冷却 15~30 分钟），严禁立刻重试。
2. **探针发现连续 2 次被标记为 `REMOVED`**：
   - 触发该账号的自适应降级：自动将账号阶段下调一级（如从 `STAGE_3` 降回 `STAGE_2`）；
   - 检查并收紧黑名单词库，将同社区发帖上限临时降为 1 条/天。
3. **账号被 Reddit 提示锁定或重置密码**：
   - 立即检查该账号使用的代理节点 IP 是否已被加入 Datacenter 黑名单；
   - 切换为干净的住宅代理（Residential Proxy）并完成邮箱验证解封。

# 🚀 Reddit Karma Pilot

> **新号养号半自动防封中控系统**  
> 通过人机协同、智能评论建议、风控防护和异步排期机制，帮助 Reddit 新账号安全积累社区信誉。

---

## 📊 项目状态

| 状态 | 详情 |
|------|------|
| **当前版本** | v1.0.0 |
| **项目阶段** | ✅ 生产就绪 |
| **总体进度** | 100% |
| **测试覆盖** | 核心流程 100% 通过 |
| **文档完整度** | 100% |

---

## 🎯 核心功能

### 1️⃣ 账号与阶段管理
- 多账号矩阵管理
- 4 个成长阶段（STAGE_1 ~ STAGE_4）
- 每日配额动态调整
- Karma 实时监控

### 2️⃣ 智能帖子监控
- 实时抓取 Reddit 新帖和热帖
- AI 意图打分与推荐
- 高互动潜力帖子优先

### 3️⃣ 评论协助系统
- 预生成符合语境的英文评论建议
- 评论模板库（24h 去重）
- 人工审核 + 一键外发

### 4️⃣ 多层风控防护
- 敏感词过滤与外链拦截
- 频率限制（5~30 分钟随机延迟）
- 429 熔断保护
- Shadowban 实时探测

### 5️⃣ 异步调度引擎
- APScheduler 精确排期
- 账号互斥执行
- 自动重试与错误恢复
- 完整的审计日志

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│          Vue 3 前端中控 (Vite + Element Plus)          │
│    [工作台] [账号] [社区] [模板] [风控] [日志] [设置]    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP/JSON (CORS)
┌──────────────────────▼──────────────────────────────────┐
│         FastAPI 后端网关 (Python 3.11+)                │
│    Pydantic v2 参数校验 / 全局异常处理 / 跨域中间件      │
└──────────────────────┬──────────────────────────────────┘
      │                │                │
      ▼                ▼                ▼
 ┌─────────┐  ┌──────────┐  ┌─────────────┐
 │ PRAW    │  │APScheduler   │ SQLAlchemy  │
 │实例池   │  │异步排期  │ ORM         │
 └─────────┘  └──────────┘  └─────────────┘
      │                │                │
      └────────────┬───┴────────────┬───┘
                   ▼
         ┌──────────────────────┐
         │  MySQL 8.0 Database  │
         │  (8张表, utf8mb4)   │
         └──────────────────────┘
```

---

## ⚡ 快速启动

### 前置条件
- Python 3.11+ 
- Node.js 18+
- MySQL 8.0+

### 5分钟启动

#### 1. 启动后端
```bash
cd reddit.ai
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. 启动前端（新终端）
```bash
cd reddit.ai/frontend
npm install
npm run dev
```

#### 3. 验证
```
✅ 后端: http://127.0.0.1:8000/health
✅ 前端: http://127.0.0.1:5173
✅ API文档: http://127.0.0.1:8000/docs
```

---

## 📚 文档导航

| 文档 | 适合人群 | 内容 |
|------|--------|------|
| **QUICK_REFERENCE.md** | 🏃 新手快速入门 | 常用命令、API 速查、故障排查 |
| **PROJECT_STATUS.md** | 📊 项目经理 | 完成情况、统计指标、下一步规划 |
| **INTEGRATION_TEST_REPORT.md** | ✅ QA/测试 | 测试结果、验证清单、性能指标 |
| **DEPLOYMENT_GUIDE.md** | 🚀 DevOps/运维 | Docker 部署、生产配置、监控告警 |
| **REDDIT_KARMA_PILOT_IMPLEMENTATION_PLAN.md** | 🏗️ 架构师 | 完整技术方案、数据库设计、API 规范 |

---

## 🔗 核心 API 端点

```
# 账号管理
GET    /api/v1/accounts
POST   /api/v1/accounts
PATCH  /api/v1/accounts/{id}/stage
POST   /api/v1/accounts/{id}/test-handshake

# 社区管理
GET    /api/v1/subreddits
POST   /api/v1/subreddits
PUT    /api/v1/subreddits/{id}/toggle

# 工作台（核心）
GET    /api/v1/workbench/candidates
POST   /api/v1/workbench/candidates/{id}/action

# 模板库
GET    /api/v1/templates
POST   /api/v1/templates
DELETE /api/v1/templates/{id}

# 风控
GET    /api/v1/risk-control/settings
PUT    /api/v1/risk-control/settings
POST   /api/v1/risk-control/circuit-breaker

# 日志
GET    /api/v1/logs
POST   /api/v1/logs/{id}/probe-shadowban
```

**📖 完整 API 文档**: http://127.0.0.1:8000/docs

---

## 💾 数据库结构

```
accounts            - Reddit 账号矩阵
subreddits          - 目标社区池
candidate_posts     - 候选待审帖子
comment_templates   - 评论模板库
dispatch_tasks      - 异步排期任务
audit_logs          - 审计与存活日志
risk_settings       - 风控规则配置
schema_version      - 迁移版本追踪
```

---

## 🔐 安全特性

✅ **敏感词过滤** - 自动拦截违禁词和营销内容  
✅ **外链拦截** - 100% 过滤 URL 和私域联系方式  
✅ **AES-256 加密** - OAuth 凭据安全存储  
✅ **频率限制** - 5~30 分钟随机延迟防风控  
✅ **断路器保护** - 429 自动熔断机制  
✅ **Shadowban 探测** - 15 分钟后自动验证评论存活状态  
✅ **CORS 配置** - 前端跨域访问白名单  
✅ **参数校验** - Pydantic v2 强类型约束  

---

## 📈 测试验证

### 快速验证 ✅
- [x] Python 依赖完整
- [x] Node.js 环境正常
- [x] MySQL 连接成功
- [x] 后端启动成功
- [x] 前端启动成功

### 集成测试 ✅
- [x] 6/6 API 端点测试通过
- [x] 8/8 数据库表验证通过
- [x] 前后端通信正常
- [x] 核心业务流程验证通过

**详见**: INTEGRATION_TEST_REPORT.md

---

## 🚀 部署到生产

### Docker 一键部署
```bash
docker-compose up -d
```

### Nginx 反向代理
```nginx
upstream backend {
  server 127.0.0.1:8000;
}

server {
  listen 80;
  server_name api.yourdomain.com;

  location / {
    proxy_pass http://backend;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

**详见**: DEPLOYMENT_GUIDE.md

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|-----|------|------|
| **前端** | Vue 3 / Vite / Element Plus / Pinia | Latest |
| **后端** | FastAPI / SQLAlchemy / PRAW / APScheduler | 0.115+ / 2.0+ / 7.7+ / 3.10+ |
| **数据库** | MySQL / InnoDB | 8.0+ |
| **部署** | Docker / Docker Compose / Nginx | 20+ |

---

## 📊 项目统计

```
后端代码     ~2000+ 行 Python
前端代码     ~1500+ 行 Vue 3 + TypeScript
数据库       8 张表 / 21 条种子数据
API 端点     15+ 个接口
测试覆盖     核心流程 100%
文档         5 个完整 Markdown 文档
```

---

## 🎓 学习路径

**第一步**: 阅读 QUICK_REFERENCE.md （5分钟）  
**第二步**: 本地启动系统 （5分钟）  
**第三步**: 访问 http://127.0.0.1:5173 （2分钟）  
**第四步**: 阅读 REDDIT_KARMA_PILOT_IMPLEMENTATION_PLAN.md （20分钟）  
**第五步**: 查看 INTEGRATION_TEST_REPORT.md 验证结果 （10分钟）  

**总计**: ~1小时内完全掌握系统！

---

## 🤝 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📞 技术支持

- 🐛 **Bug 报告**: 创建 Issue
- 💡 **功能建议**: 创建 Discussion
- 📖 **文档改进**: 提交 PR
- ❓ **技术问题**: 查看 QUICK_REFERENCE.md 的"常见问题"

---

## 📝 更新日志

### v1.0.0 (2026-11-25) ✅
- ✨ 完整的系统架构
- ✨ 15+ 个 API 端点
- ✨ 专业化 UI/UX
- ✨ 多层风控防护
- ✨ 100% 文档覆盖

### v1.1.0 (规划中)
- Redis 缓存集成
- WebSocket 实时通知
- 高级分析仪表板
- 批量账号导入

---

## 📄 许可证

MIT License - 详见 LICENSE 文件

---

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者和测试人员。

---

**🎉 Reddit Karma Pilot - 新号养号半自动防封中控系统**

*打造更安全、更高效的 Reddit 账号养成方案*

---

**最后更新**: 2026-11-25  
**状态**: ✅ 生产就绪  
**版本**: 1.0.0

# 🎯 Reddit Karma Pilot 快速参考卡

## 🚀 本地快速启动 (5分钟)

### 1️⃣ 启动后端
```bash
cd C:\Users\33046\Desktop\reddit.ai
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
✅ 访问: http://127.0.0.1:8000  
📖 API 文档: http://127.0.0.1:8000/docs

### 2️⃣ 启动前端（新终端）
```bash
cd C:\Users\33046\Desktop\reddit.ai\frontend
npm run dev
```
✅ 访问: http://127.0.0.1:5173

### 3️⃣ 验证系统
```bash
# 健康检查
curl http://127.0.0.1:8000/health

# 账号列表
curl http://127.0.0.1:8000/api/v1/accounts

# 候选帖子
curl http://127.0.0.1:8000/api/v1/workbench/candidates
```

---

## 📦 核心 API 端点

| 方法 | 路由 | 功能 | 状态码 |
|-----|------|------|--------|
| GET | `/api/v1/accounts` | 获取账号列表 | 200 |
| POST | `/api/v1/accounts` | 新增账号 | 201 |
| PATCH | `/api/v1/accounts/{id}/stage` | 切换阶段 | 200 |
| POST | `/api/v1/accounts/{id}/test-handshake` | 测试 OAuth | 200 |
| GET | `/api/v1/subreddits` | 社区列表 | 200 |
| POST | `/api/v1/subreddits` | 新增社区 | 201 |
| GET | `/api/v1/workbench/candidates` | 待审帖子 | 200 |
| POST | `/api/v1/workbench/candidates/{id}/action` | 批复/跳过 | 200 |
| GET | `/api/v1/templates` | 模板列表 | 200 |
| POST | `/api/v1/templates` | 新增模板 | 201 |
| GET | `/api/v1/risk-control/settings` | 风控设置 | 200 |
| PUT | `/api/v1/risk-control/settings` | 更新风控 | 200 |
| POST | `/api/v1/risk-control/circuit-breaker` | 熔断控制 | 200 |
| GET | `/api/v1/logs` | 审计日志 | 200 |
| POST | `/api/v1/logs/{id}/probe-shadowban` | 存活探测 | 200 |

---

## 💾 数据库表引用

```sql
-- 查看所有表
SHOW TABLES;

-- 账号表
SELECT * FROM accounts;

-- 社区表
SELECT * FROM subreddits;

-- 候选帖子
SELECT * FROM candidate_posts WHERE status='PENDING';

-- 评论模板
SELECT * FROM comment_templates WHERE is_active=1;

-- 排期任务
SELECT * FROM dispatch_tasks WHERE status='QUEUED';

-- 审计日志
SELECT * FROM audit_logs ORDER BY created_at DESC;

-- 风控设置
SELECT * FROM risk_settings;
```

---

## ⚙️ 环境变量速查

```env
# 数据库
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=reddit_karma_pilot

# 服务
SERVER_PORT=8000

# 安全
ENCRYPTION_SECRET_KEY=UjZfdm5VUk9zYmF2WmxSZlFfTjFwQzNScWRyM2FzZGY=
```

---

## 🔧 常用命令

### Python 相关
```bash
# 安装依赖
pip install -r requirements.txt

# 运行单个测试
pytest tests/test_accounts.py -v

# 运行所有测试
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=app
```

### 前端相关
```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build

# 预览构建结果
npm run preview
```

### 数据库相关
```bash
# 连接数据库
mysql -h 127.0.0.1 -u root -proot reddit_karma_pilot

# 导出数据
mysqldump -h 127.0.0.1 -u root -proot reddit_karma_pilot > backup.sql

# 导入数据
mysql -h 127.0.0.1 -u root -proot reddit_karma_pilot < backup.sql

# 执行迁移
python migrations/migrate.py
```

---

## 🐛 故障排查

### 后端启动失败
```
❌ [Errno 48] Address already in use
✅ 换个端口: --port 8001
```

### 数据库连接失败
```
❌ Can't connect to MySQL server on '127.0.0.1'
✅ 检查 MySQL 是否运行: mysql -u root -p
```

### CORS 跨域错误
```
❌ Access to XMLHttpRequest blocked by CORS policy
✅ 检查 CORS_ORIGINS 配置中是否包含前端地址
```

### 前端白屏
```
❌ 页面显示空白
✅ 检查浏览器控制台错误
✅ 确保后端 API 正常响应
✅ 清除浏览器缓存: Ctrl+Shift+Delete
```

---

## 📊 监控检查清单

- [ ] 后端健康: `curl http://127.0.0.1:8000/health`
- [ ] 前端可访问: 访问 http://127.0.0.1:5173
- [ ] 数据库连接: `mysql -h 127.0.0.1 -u root -proot -e "SELECT 1"`
- [ ] API 响应: `curl http://127.0.0.1:8000/api/v1/accounts`
- [ ] 调度器运行: 查看健康检查的 scheduler 字段
- [ ] 数据库数据: `SELECT COUNT(*) FROM candidate_posts`

---

## 🚢 部署快速命令

```bash
# Docker 构建
docker build -f Dockerfile.backend -t reddit-karma-backend:1.0.0 .
docker build -f Dockerfile.frontend -t reddit-karma-frontend:1.0.0 .

# Docker 启动
docker run -p 8000:8000 reddit-karma-backend:1.0.0
docker run -p 80:80 reddit-karma-frontend:1.0.0

# Docker Compose 启动
docker-compose up -d
docker-compose logs -f

# Docker Compose 停止
docker-compose down
```

---

## 📚 文档导航

| 文档 | 用途 |
|------|------|
| REDDIT_KARMA_PILOT_IMPLEMENTATION_PLAN.md | 完整技术方案书 |
| INTEGRATION_TEST_REPORT.md | 测试验证结果 |
| DEPLOYMENT_GUIDE.md | 部署与运维指南 |
| PROJECT_STATUS.md | 项目完成状态 |
| README.md (frontend/) | 前端项目说明 |

---

## 🎓 学习路径

1. **了解项目**: 阅读 PROJECT_STATUS.md
2. **学习架构**: 阅读 REDDIT_KARMA_PILOT_IMPLEMENTATION_PLAN.md
3. **本地运行**: 按照本卡启动系统
4. **查看测试**: 阅读 INTEGRATION_TEST_REPORT.md
5. **部署上线**: 参考 DEPLOYMENT_GUIDE.md

---

## 💡 Tips

- 🔄 **自动重载**: 后端用 `--reload` 参数，改代码自动重启
- 📝 **API 文档**: 访问 `/docs` 查看 Swagger UI
- 🔍 **调试**: 在代码中加 `print()` 查看日志
- 📊 **数据**: 用 DBeaver 或 MySQL Workbench 管理数据库
- 🚀 **性能**: 生产环境用 `gunicorn` 替代 `uvicorn`

---

**版本**: v1.0.0  
**状态**: ✅ 生产就绪  
**更新**: 2026-11-25

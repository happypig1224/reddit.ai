# 🚀 Reddit Karma Pilot 快速启动指南

## 本地开发环境启动

### 前提条件
- Python 3.11+ ✅
- Node.js 18+ ✅
- MySQL 8.0+ ✅
- Git ✅

### 一键启动脚本

#### Windows (PowerShell)
```powershell
# 1. 启动后端
cd C:\Users\33046\Desktop\reddit.ai
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 新开 PowerShell 窗口

# 2. 启动前端
cd C:\Users\33046\Desktop\reddit.ai\frontend
npm run dev
```

#### 验证服务
```
✅ 后端: http://127.0.0.1:8000/health
✅ 前端: http://127.0.0.1:5173
✅ 数据库: 127.0.0.1:3306
```

---

## 📦 部署到生产环境

### Docker 部署

#### 1. 创建 Dockerfile (后端)
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY app/ ./app/
COPY migrations/ ./migrations/

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. 创建 Dockerfile (前端)
```dockerfile
FROM node:24-alpine as builder
WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Docker Compose 编排
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
      MYSQL_DATABASE: reddit_karma_pilot
    volumes:
      - mysql_data:/var/lib/mysql
      - ./migrations:/docker-entrypoint-initdb.d
    ports:
      - "3306:3306"

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    environment:
      DB_HOST: mysql
      DB_USER: root
      DB_PASSWORD: ${DB_PASSWORD}
      DB_NAME: reddit_karma_pilot
      ENCRYPTION_SECRET_KEY: ${ENCRYPTION_SECRET_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - mysql

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mysql_data:
```

### 启动生产环境
```bash
# 创建 .env 文件
cat > .env << EOF
DB_PASSWORD=your_secure_password
ENCRYPTION_SECRET_KEY=your_base64_encoded_key
EOF

# 启动所有服务
docker-compose up -d

# 检查状态
docker-compose ps
docker-compose logs -f backend
```

---

## ⚙️ 环境配置

### 后端环境变量 (.env)
```env
# 数据库配置
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=secure_password_here
DB_NAME=reddit_karma_pilot

# 服务配置
SERVER_PORT=8000

# 安全配置
ENCRYPTION_SECRET_KEY=UjZfdm5VUk9zYmF2WmxSZlFfTjFwQzNScWRyM2FzZGY=

# Reddit OAuth
# (需从 Reddit 开发者控制台获取)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
```

### 前端环境变量 (.env.production)
```env
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_API_TIMEOUT=30000
```

---

## 🔐 安全检查清单

- [ ] 修改 MySQL root 密码
- [ ] 生成新的 ENCRYPTION_SECRET_KEY
- [ ] 配置 Redis 密码（如使用）
- [ ] 启用 HTTPS/SSL
- [ ] 配置 CORS 白名单（生产域名）
- [ ] 设置 API 速率限制
- [ ] 启用数据库备份
- [ ] 配置日志收集
- [ ] 设置监控告警
- [ ] 配置日志轮转

---

## 📊 监控与维护

### 健康检查端点
```
GET /health
```

**响应示例**:
```json
{
  "status": "UP",
  "service": "Reddit Karma Pilot Backend",
  "version": "1.0.0",
  "database": "CONNECTED",
  "scheduler": "RUNNING"
}
```

### 常用运维命令

```bash
# 查看日志
docker-compose logs -f backend

# 重启服务
docker-compose restart backend

# 执行数据库备份
mysqldump -h 127.0.0.1 -u root -p reddit_karma_pilot > backup.sql

# 恢复数据库
mysql -h 127.0.0.1 -u root -p reddit_karma_pilot < backup.sql

# 查看 API 文档
http://your_domain/docs  # Swagger UI
http://your_domain/redoc # ReDoc

# 查看 APScheduler 日志
docker-compose logs backend | grep APScheduler
```

---

## 🐛 常见问题

### 问题 1: 端口被占用
```
ERROR: [WinError 10013] 以一种访问权限不允许的方式做了一个套接字的尝试
```

**解决方案**:
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 杀死进程
taskkill /PID <PID> /F

# 或更换端口
uvicorn app.main:app --port 8001
```

### 问题 2: 数据库连接失败
```
ERROR: (pymysql.err.OperationalError) (2003, "Can't connect to MySQL server")
```

**解决方案**:
```bash
# 检查 MySQL 是否运行
mysql -h 127.0.0.1 -u root -p -e "SELECT 1;"

# 检查连接字符串
# 确保 DB_HOST, DB_PORT, DB_USER, DB_PASSWORD 正确
```

### 问题 3: CORS 跨域错误
```
Access to XMLHttpRequest blocked by CORS policy
```

**解决方案**:
```python
# 检查 app/core/config.py 中的 CORS_ORIGINS
# 确保前端地址在允许列表中
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
```

---

## 📈 性能优化

### 数据库优化
```sql
-- 分析表
ANALYZE TABLE accounts;
ANALYZE TABLE candidate_posts;

-- 检查索引
SHOW INDEXES FROM accounts;

-- 更新统计信息
OPTIMIZE TABLE accounts;
```

### 应用层优化
```python
# 在 app/core/config.py 中配置连接池
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 10
DB_POOL_PRE_PING = True
```

### 前端优化
```bash
# 生产构建（带资源优化）
npm run build

# 分析构建大小
npm run build -- --report
```

---

## 📞 支持与反馈

- 🐛 **Bug 报告**: 创建 Issue
- 💡 **功能建议**: 创建讨论
- 📖 **文档改进**: 提交 PR
- ❓ **技术问题**: 查看 REDDIT_KARMA_PILOT_IMPLEMENTATION_PLAN.md

---

**项目状态**: ✅ 生产就绪  
**最后更新**: 2026-11-25  
**下一版本**: v1.0.1 (预计 2026-12-15)

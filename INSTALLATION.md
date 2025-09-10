# AI Crawler Assistant - 安装和部署指南

## 🚀 快速开始

### 前置要求

- **Docker & Docker Compose**: 确保已安装最新版本
- **OpenAI API Key**: 获取GPT-4 API访问权限
- **系统要求**: 至少4GB内存，推荐8GB

### 1. 环境准备

```bash
# 克隆项目
git clone <your-repo-url>
cd crawler-assistant

# 设置环境变量
cp env.example .env
```

### 2. 配置环境变量

编辑 `.env` 文件，设置以下关键配置：

```bash
# 必需配置
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置（Docker环境无需修改）
DATABASE_URL=mysql+aiomysql://crawler_user:crawler_password@db:3306/crawler_db
REDIS_URL=redis://redis:6379/0

# 可选配置
DEBUG=false
LOG_LEVEL=INFO
BROWSER_HEADLESS=true
MAX_CONCURRENT_SESSIONS=5
```

### 3. 一键启动

```bash
# 使用启动脚本（推荐）
chmod +x scripts/start.sh
./scripts/start.sh

# 或手动启动
docker-compose up -d
```

### 4. 验证安装

访问以下地址验证服务：

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **任务监控**: http://localhost:5555 (Flower)

## 📋 详细部署说明

### Docker Compose 服务

```yaml
services:
  app:         # 主应用服务 (端口8000)
  db:          # MySQL数据库 (端口3306)
  redis:       # Redis缓存 (端口6379)
  worker:      # Celery后台任务处理器
  flower:      # 任务监控面板 (端口5555)
```

### 开发环境安装

如果需要本地开发环境：

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 安装浏览器
playwright install chromium

# 启动数据库（使用Docker）
docker-compose up -d db redis

# 运行数据库迁移
alembic upgrade head

# 启动应用
python main.py
```

### 生产环境部署

#### 选项1: Docker Compose + Nginx

```bash
# 启动包含Nginx的完整生产环境
docker-compose --profile production up -d
```

#### 选项2: Kubernetes部署

```bash
# 构建镜像
docker build -t crawler-assistant:latest .

# 部署到Kubernetes
kubectl apply -f k8s/
```

#### 选项3: 云服务部署

支持部署到以下云平台：
- 阿里云 ECS + RDS
- 腾讯云 CVM + TencentDB
- AWS EC2 + RDS
- Azure VM + PostgreSQL

## 🔧 配置说明

### 应用配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `API_HOST` | API服务地址 | 0.0.0.0 |
| `API_PORT` | API服务端口 | 8000 |
| `DEBUG` | 调试模式 | false |
| `SECRET_KEY` | 应用密钥 | 随机生成 |

### AI配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `OPENAI_API_KEY` | OpenAI API密钥 | 必需 |
| `OPENAI_MODEL` | 使用的模型 | gpt-4-vision-preview |

### 浏览器配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `BROWSER_HEADLESS` | 无头模式 | true |
| `BROWSER_TIMEOUT` | 超时时间(ms) | 30000 |
| `ENABLE_STEALTH_MODE` | 隐身模式 | true |
| `HUMAN_BEHAVIOR_SIMULATION` | 人类行为模拟 | true |

### 性能配置

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_CONCURRENT_SESSIONS` | 最大并发会话 | 5 |
| `MAX_PAGES_PER_SESSION` | 每会话最大页数 | 100 |
| `REQUEST_DELAY_MIN` | 最小请求延迟(秒) | 1 |
| `REQUEST_DELAY_MAX` | 最大请求延迟(秒) | 3 |

## 🔍 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看日志
docker-compose logs app

# 常见原因和解决方案
# - 端口被占用: 修改docker-compose.yml中的端口映射
# - 内存不足: 增加Docker内存限制
# - 环境变量未设置: 检查.env文件
```

#### 2. OpenAI API调用失败

```bash
# 测试API连接
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models

# 常见问题
# - API密钥无效: 检查OpenAI账户
# - 配额用完: 检查API使用情况
# - 网络问题: 检查防火墙设置
```

#### 3. 浏览器启动失败

```bash
# 重新安装浏览器
docker-compose exec app python -m playwright install chromium

# 检查系统资源
docker stats

# 增加内存限制
# 修改docker-compose.yml中的内存配置
```

#### 4. 数据库连接问题

```bash
# 检查数据库状态
docker-compose ps db

# 检查连接
docker-compose exec db mysql -u crawler_user -pcrawler_password -e "SELECT 1;"

# 重置数据库
docker-compose down -v
docker-compose up -d
```

### 日志分析

```bash
# 查看应用日志
docker-compose logs -f app

# 查看特定时间的日志
docker-compose logs --since "2024-01-01T00:00:00" app

# 查看错误日志
docker-compose logs app | grep ERROR

# 实时监控
tail -f logs/app.log
```

### 性能优化

#### 1. 数据库优化

```sql
-- 清理旧数据
CALL cleanup_old_data();

-- 查看统计信息
CALL get_crawl_statistics();

-- 重建索引
ANALYZE TABLE job_sites, jobs, crawl_sessions;
```

#### 2. 内存优化

```bash
# 调整Docker内存限制
# 编辑docker-compose.yml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 2G
```

#### 3. 并发控制

```bash
# 减少并发会话数
echo "MAX_CONCURRENT_SESSIONS=3" >> .env

# 增加请求延迟
echo "REQUEST_DELAY_MAX=5" >> .env
```

## 📊 监控和维护

### 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 详细状态检查
curl http://localhost:8000/api/v1/health/status

# 数据库健康检查  
docker-compose exec db mysqladmin ping -u crawler_user -pcrawler_password
```

### 备份和恢复

```bash
# 数据库备份
docker-compose exec db mysqldump -u crawler_user -pcrawler_password crawler_db > backup.sql

# 数据库恢复
docker-compose exec -T db mysql -u crawler_user -pcrawler_password crawler_db < backup.sql

# 文件备份
tar -czf exports_backup.tar.gz exports/ screenshots/
```

### 更新部署

```bash
# 拉取最新代码
git pull origin main

# 重新构建并部署
docker-compose build
docker-compose down
docker-compose up -d

# 运行数据库迁移（如果有）
docker-compose exec app alembic upgrade head
```

## 🆘 获取帮助

- **文档**: 查看 `/docs` 目录下的详细文档
- **Issues**: 在GitHub上提交问题
- **邮件支持**: support@example.com
- **社区**: 加入我们的微信群或Discord

## 📝 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE) 文件。


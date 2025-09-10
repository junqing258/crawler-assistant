# AI Crawler Assistant

🤖 智能化的招聘网站爬虫工具，使用 AI 技术自动识别页面结构并提取职位信息。

## 🌟 特性

- **🧠 AI 驱动**: 使用 GPT-4 自动分析页面结构，生成准确的 CSS 选择器
- **🌐 自适应**: 支持不同招聘网站的自动适配，无需手动配置
- **🔍 智能提取**: 自动识别职位标题、公司名称、地点、描述等关键信息
- **🔄 分页处理**: 智能处理各种分页模式，支持"下一页"、"加载更多"等
- **🛡️ 反爬虫**: 使用 browser-use 模拟真实用户行为，绕过反爬虫检测
- **📊 数据质量**: 内置数据清洗和验证机制，确保数据准确性
- **⚡ 高性能**: 支持并发爬取，异步处理，提高效率
- **📈 监控**: 完整的性能监控和日志系统

## 🏗️ 系统架构

```
┌─────────────────────────────────────┐
│           用户接口层                │
├─────────────────────────────────────┤
│           API网关层                 │
├─────────────────────────────────────┤
│         核心业务层                  │
│  ┌─────────────┬─────────────────┐   │
│  │ AI分析模块  │  爬虫引擎       │   │
│  │             │                 │   │
│  │ 页面分析    │  Browser-use    │   │
│  │ 选择器生成  │  数据提取       │   │
│  │ 智能验证    │  分页处理       │   │
│  └─────────────┴─────────────────┘   │
├─────────────────────────────────────┤
│         数据存储层                  │
│  ┌─────────────┬─────────────────┐   │
│  │ PostgreSQL  │     Redis       │   │
│  │             │                 │   │
│  │ 结构化数据  │   缓存&会话     │   │
│  └─────────────┴─────────────────┘   │
└─────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- OpenAI API Key

### 1. 克隆项目

```bash
git clone https://github.com/your-username/ai-crawler-assistant.git
cd ai-crawler-assistant
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
vim .env
```

在 `.env` 文件中配置：

```env
# OpenAI配置
OPENAI_API_KEY=your_openai_api_key_here

# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/crawler_db
REDIS_URL=redis://localhost:6379

# 应用配置
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true

# Browser-use配置
BROWSER_HEADLESS=true
BROWSER_TIMEOUT=30000

# 代理配置（可选）
PROXY_ENABLED=false
PROXY_LIST=proxy1:port1,proxy2:port2
```

### 3. 启动服务

```bash
# 使用Docker Compose启动所有服务
docker-compose up -d

# 或者本地开发模式
python -m pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 验证安装

```bash
# 检查API健康状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

## 📖 使用指南

### 基本使用流程

#### 1. 分析页面结构

```python
import requests

# 提交要分析的招聘页面URL
response = requests.post("http://localhost:8000/api/v1/analyze-url", json={
    "url": "https://example-job-site.com/jobs",
    "options": {
        "wait_time": 3,  # 等待页面加载时间(秒)
        "include_screenshots": true  # 是否包含截图
    }
})

selectors = response.json()
print(selectors)
```

**返回示例**:

```json
{
  "selectors": {
    "jobList": ".jobs-container",
    "jobItem": ".job-card",
    "jobTitle": "h3.job-title a",
    "jobLink": "h3.job-title a",
    "companyName": ".company-name",
    "publishedAt": ".publish-date",
    "location": ".job-location",
    "jobDescription": ".job-summary",
    "nextPage": ".pagination .next-page"
  },
  "confidence_score": 0.95,
  "validation_details": {
    "single_page_accuracy": 0.98,
    "multi_page_stability": 0.92,
    "data_completeness": 0.94
  }
}
```

#### 2. 启动爬虫任务

```python
# 使用生成的选择器启动爬虫
response = requests.post("http://localhost:8000/api/v1/start-crawling", json={
    "url": "https://example-job-site.com/jobs",
    "selectors": selectors["selectors"],
    "options": {
        "max_pages": 10,  # 最大爬取页数
        "delay_between_pages": 2,  # 页面间延迟(秒)
        "export_format": "json",  # 导出格式: json, csv, excel
        "data_filters": {
            "location": ["北京", "上海"],  # 地点过滤
            "keywords": ["Python", "AI"]  # 关键词过滤
        }
    }
})

session_info = response.json()
session_id = session_info["session_id"]
```

#### 3. 监控爬取进度

```python
import time

while True:
    # 查询爬取状态
    status = requests.get(f"http://localhost:8000/api/v1/crawl-status/{session_id}")
    status_data = status.json()

    print(f"状态: {status_data['status']}")
    print(f"已爬取页面: {status_data['progress']['pages_crawled']}")
    print(f"发现职位: {status_data['progress']['jobs_found']}")

    if status_data["status"] in ["completed", "failed"]:
        break

    time.sleep(5)  # 每5秒检查一次
```

#### 4. 下载爬取结果

```python
if status_data["status"] == "completed":
    # 下载结果文件
    download_url = status_data["export_url"]
    file_response = requests.get(f"http://localhost:8000{download_url}")

    with open("jobs_data.json", "wb") as f:
        f.write(file_response.content)

    print("数据下载完成!")
```

### 高级用法

#### 自定义选择器配置

如果 AI 生成的选择器需要调整，可以手动修改：

```python
# 手动调整选择器
custom_selectors = {
    "jobList": "div.search-results",  # 修改职位列表容器
    "jobItem": ".job-item",
    "jobTitle": ".job-title h3",      # 更精确的标题选择器
    "jobLink": ".job-title a",
    "companyName": ".company span",
    "publishedAt": ".posted-date",
    "location": ".location-info",
    "jobDescription": ".job-desc",
    "nextPage": "a[aria-label*='下一页']"  # 支持aria-label
}

# 使用自定义选择器启动爬虫
response = requests.post("http://localhost:8000/api/v1/start-crawling", json={
    "url": url,
    "selectors": custom_selectors,
    "options": crawl_options
})
```

#### 批量网站爬取

```python
# 批量处理多个网站
websites = [
    "https://jobs.site1.com/search",
    "https://jobs.site2.com/listings",
    "https://careers.site3.com/openings"
]

crawl_sessions = []

for url in websites:
    # 1. 分析每个网站
    analysis = requests.post("http://localhost:8000/api/v1/analyze-url",
                           json={"url": url})

    if analysis.json()["confidence_score"] > 0.8:
        # 2. 启动爬虫
        crawl_response = requests.post("http://localhost:8000/api/v1/start-crawling",
                                     json={
                                         "url": url,
                                         "selectors": analysis.json()["selectors"]
                                     })
        crawl_sessions.append(crawl_response.json()["session_id"])

# 3. 监控所有任务
# ... 监控逻辑
```

## 🔧 配置选项

### AI 分析配置

```python
analyze_options = {
    "ai_model": "gpt-4-vision-preview",  # AI模型选择
    "confidence_threshold": 0.8,         # 置信度阈值
    "max_analysis_time": 60,            # 最大分析时间(秒)
    "include_visual_analysis": true,     # 是否包含视觉分析
    "fallback_to_heuristics": true      # 是否回退到启发式方法
}
```

### 爬虫配置

```python
crawl_options = {
    "max_pages": 50,                    # 最大爬取页数
    "max_jobs": 1000,                   # 最大职位数量
    "delay_between_pages": (1, 3),      # 页面间随机延迟
    "timeout": 30,                      # 页面超时时间
    "retry_count": 3,                   # 重试次数
    "export_format": "json",            # 导出格式
    "data_quality_threshold": 0.7,      # 数据质量阈值
    "enable_screenshots": false,        # 是否保存截图
    "proxy_rotation": true,             # 是否轮换代理
    "user_agent_rotation": true         # 是否轮换User-Agent
}
```

### 反爬虫配置

```python
anti_detection_config = {
    "stealth_mode": true,               # 启用隐身模式
    "human_behavior_simulation": true,  # 模拟人类行为
    "random_delays": {                  # 随机延迟配置
        "page_load": (2, 5),
        "scroll": (1, 3),
        "click": (0.5, 1.5)
    },
    "proxy_settings": {                 # 代理设置
        "enabled": true,
        "rotation_interval": 10,        # 轮换间隔(页面数)
        "health_check": true
    }
}
```

## 📊 数据格式

### 标准输出格式

```json
{
  "metadata": {
    "crawl_session_id": "uuid-string",
    "source_url": "https://example.com/jobs",
    "crawl_timestamp": "2025-01-01T00:00:00Z",
    "total_pages": 5,
    "total_jobs": 125,
    "data_quality_score": 0.92
  },
  "jobs": [
    {
      "id": "job-uuid",
      "title": "高级Python开发工程师",
      "company": "科技创新公司",
      "location": "北京市朝阳区",
      "published_at": "2025-01-01",
      "description": "负责后端系统开发...",
      "link": "https://example.com/job/12345",
      "salary_range": "20k-35k",
      "experience_level": "3-5年",
      "job_type": "全职",
      "skills_required": ["Python", "Django", "MySQL", "Redis"],
      "remote_option": false,
      "data_quality_score": 0.95,
      "extracted_at": "2025-01-01T00:05:23Z"
    }
  ],
  "pagination_info": {
    "current_page": 5,
    "total_pages": 5,
    "has_next": false,
    "next_page_url": null
  },
  "extraction_stats": {
    "success_rate": 0.94,
    "failed_extractions": 8,
    "duplicate_jobs": 3,
    "data_quality_issues": 5
  }
}
```

## 🛠️ 开发指南

### 项目结构

```
crawler-assistant/
├── app/
│   ├── api/                    # API路由
│   ├── core/                   # 核心业务逻辑
│   │   ├── ai/                 # AI分析模块
│   │   ├── crawler/            # 爬虫引擎
│   │   ├── browser/            # Browser-use集成
│   │   └── data/               # 数据处理
│   ├── models/                 # 数据模型
│   ├── utils/                  # 工具函数
│   └── tests/                  # 测试代码
├── docs/                       # 项目文档
├── scripts/                    # 部署脚本
├── docker-compose.yml          # Docker编排
├── requirements.txt            # Python依赖
└── README.md
```

### 本地开发

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装开发依赖
pip install -r requirements-dev.txt

# 安装pre-commit钩子
pre-commit install

# 运行测试
pytest

# 运行测试并显示详细信息
pytest -v

# 运行特定测试文件
pytest tests/test_basic.py -v

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term

# 运行测试时显示打印输出
pytest -s

# 运行失败时停止
pytest -x

# 代码格式化
black .
isort .

# 类型检查
mypy app/
```

### 添加新的选择器策略

```python
# app/core/ai/selector_strategies.py

class CustomSelectorStrategy(BaseSelectorStrategy):
    """自定义选择器生成策略"""

    def generate_job_list_selector(self, dom_tree, analysis) -> str:
        # 实现你的选择器生成逻辑
        pass

    def validate_selector(self, selector: str, dom_tree) -> float:
        # 实现选择器验证逻辑
        pass

# 注册策略
SelectorStrategyRegistry.register("custom", CustomSelectorStrategy)
```

## 🚨 故障排除

### 常见问题

#### 1. OpenAI API 调用失败

```bash
# 检查API密钥
echo $OPENAI_API_KEY

# 测试API连接
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

#### 2. 浏览器启动失败

```bash
# 安装浏览器依赖
playwright install chromium

# 检查Chrome是否可用
google-chrome --version
```

#### 3. 选择器准确率低

- 检查目标网站的页面结构是否发生变化
- 尝试降低`confidence_threshold`
- 手动调整生成的选择器
- 启用`fallback_to_heuristics`选项

#### 4. 性能问题

```python
# 调整并发设置
crawl_options = {
    "max_concurrent_pages": 3,  # 减少并发数
    "delay_between_requests": 2,  # 增加延迟
    "enable_resource_blocking": true  # 阻止不必要资源
}
```

### 日志分析

```bash
# 查看应用日志
docker-compose logs -f api

# 查看特定会话日志
grep "session_id=xxx" /var/log/crawler-assistant/app.log

# 查看错误日志
tail -f /var/log/crawler-assistant/error.log
```

## 🤝 贡献指南

我们欢迎社区贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 贡献流程

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交修改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- [browser-use](https://github.com/gregpr07/browser-use) - 强大的浏览器自动化工具
- [OpenAI](https://openai.com/) - GPT-4 AI 模型支持
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的 Web 框架
- [Playwright](https://playwright.dev/) - 可靠的浏览器自动化

## 📞 支持

- 📧 邮箱: support@example.com
- 💬 微信群: [扫码加入](qr-code-link)
- 📚 文档: [在线文档](https://docs.example.com)
- 🐛 问题反馈: [GitHub Issues](https://github.com/your-username/ai-crawler-assistant/issues)

---

<div align="center">
  <p>如果这个项目对你有帮助，请给它一个 ⭐️</p>
  <p>Made with ❤️ by the AI Crawler Team</p>
</div>

# AI Crawler Assistant - 技术实现规格

## 1. 系统架构概述

### 1.1 核心技术栈
- **后端框架**: FastAPI (Python 3.11+)
- **AI集成**: OpenAI GPT-4, LangChain
- **浏览器自动化**: browser-use + Playwright
- **数据库**: PostgreSQL + Redis
- **任务队列**: Celery + Redis
- **容器化**: Docker + Docker Compose

### 1.2 系统分层
```
┌─────────────────────────────────────┐
│           API Gateway Layer        │
├─────────────────────────────────────┤
│         Core Business Layer        │
├─────────────────────────────────────┤
│       Browser Automation Layer     │
├─────────────────────────────────────┤
│         Data Storage Layer         │
└─────────────────────────────────────┘
```

## 2. AI选择器提取系统

### 2.1 页面分析流程

#### 阶段1: 页面加载和预处理
```python
async def analyze_page(url: str) -> AnalysisResult:
    # 1. 使用browser-use加载页面
    browser_agent = BrowserAgent()
    page_data = await browser_agent.load_page(url)
    
    # 2. 等待JavaScript渲染完成
    await page_data.wait_for_load_state("networkidle")
    
    # 3. 获取HTML和截图
    html_content = await page_data.content()
    screenshot = await page_data.screenshot()
    
    # 4. 提取DOM结构
    dom_tree = BeautifulSoup(html_content, 'html.parser')
    
    return AnalysisResult(html=html_content, screenshot=screenshot, dom=dom_tree)
```

#### 阶段2: AI驱动的结构分析
```python
class PageStructureAnalyzer:
    def __init__(self):
        self.openai_client = OpenAI()
        self.vision_model = "gpt-4-vision-preview"
    
    async def analyze_structure(self, analysis_result: AnalysisResult) -> StructureAnalysis:
        # 构建分析提示
        prompt = self._build_analysis_prompt(analysis_result)
        
        # 调用GPT-4 Vision API
        response = await self.openai_client.chat.completions.create(
            model=self.vision_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": analysis_result.screenshot}}
                    ]
                }
            ]
        )
        
        # 解析AI响应
        return self._parse_structure_response(response.choices[0].message.content)
```

### 2.2 选择器生成算法

#### CSS选择器生成策略
```python
class SelectorGenerator:
    def generate_job_list_selector(self, dom_tree, ai_analysis) -> str:
        # 1. 基于AI分析的语义理解
        semantic_candidates = ai_analysis.job_list_containers
        
        # 2. 启发式规则
        heuristic_candidates = self._find_by_heuristics(dom_tree)
        
        # 3. 视觉布局分析
        visual_candidates = self._find_by_visual_patterns(dom_tree)
        
        # 4. 权重计算和选择
        best_selector = self._calculate_best_selector(
            semantic_candidates, 
            heuristic_candidates, 
            visual_candidates
        )
        
        return best_selector
    
    def _find_by_heuristics(self, dom_tree) -> List[str]:
        """基于启发式规则查找候选选择器"""
        candidates = []
        
        # 常见的职位列表容器模式
        job_list_patterns = [
            'div[class*="job"]',
            'ul[class*="job"], ol[class*="job"]',
            'div[class*="listing"]',
            'div[class*="search-result"]',
            'section[class*="job"]'
        ]
        
        for pattern in job_list_patterns:
            elements = dom_tree.select(pattern)
            if elements:
                candidates.extend([self._generate_selector(el) for el in elements])
        
        return candidates
```

## 3. Browser-use集成实现

### 3.1 浏览器代理配置
```python
from browser_use import Agent
from browser_use.browser import Browser, BrowserConfig

class CrawlerBrowserAgent:
    def __init__(self):
        self.browser_config = BrowserConfig(
            headless=True,
            chrome_instance_path=None,
            disable_security=True,
            extra_chromium_args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
            ]
        )
        
    async def create_extraction_agent(self, selectors: Dict[str, str]) -> Agent:
        """创建专门的数据提取代理"""
        
        task_description = f"""
        你是一个专业的网页数据提取专家。你的任务是从招聘网站提取职位信息。

        提取目标:
        1. 职位列表容器: {selectors.get('jobList', '需要识别')}
        2. 单个职位项: {selectors.get('jobItem', '需要识别')}
        3. 职位标题: {selectors.get('jobTitle', '需要识别')}
        4. 公司名称: {selectors.get('companyName', '需要识别')}
        5. 发布时间: {selectors.get('publishedAt', '需要识别')}
        6. 工作地点: {selectors.get('location', '需要识别')}
        7. 职位描述: {selectors.get('jobDescription', '需要识别')}
        8. 下一页: {selectors.get('nextPage', '需要识别')}

        请按照以下JSON格式返回提取的数据:
        {{
            "jobs": [
                {{
                    "title": "职位标题",
                    "company": "公司名称",
                    "location": "工作地点",
                    "published_at": "发布时间",
                    "description": "职位描述",
                    "link": "职位链接"
                }}
            ],
            "has_next_page": true/false,
            "next_page_url": "下一页URL"
        }}
        """
        
        agent = Agent(
            task=task_description,
            llm=self._get_llm_config(),
            browser=Browser(config=self.browser_config)
        )
        
        return agent
```

### 3.2 智能分页处理
```python
class PaginationHandler:
    async def handle_pagination(self, agent: Agent, next_page_selector: str) -> bool:
        """智能处理分页逻辑"""
        
        pagination_task = f"""
        请检查页面是否有下一页，并导航到下一页。
        
        下一页选择器提示: {next_page_selector}
        
        常见的下一页模式:
        1. "下一页"、"Next"、">"等文本按钮
        2. 页码按钮 (如 2, 3, 4...)
        3. "加载更多"、"Load More"按钮
        4. 无限滚动 (需要滚动到底部)
        
        如果找到下一页，请点击并等待页面加载完成。
        如果没有下一页，请返回 "NO_MORE_PAGES"。
        """
        
        try:
            result = await agent.run(pagination_task)
            return "NO_MORE_PAGES" not in result.strip().upper()
        except Exception as e:
            logger.error(f"分页处理失败: {e}")
            return False
```

### 3.3 反爬虫策略
```python
class AntiDetectionManager:
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        ]
        
        self.behavior_patterns = [
            {"scroll_delay": (1, 3), "click_delay": (0.5, 1.5)},
            {"scroll_delay": (2, 4), "click_delay": (1, 2)},
        ]
    
    async def apply_stealth_measures(self, page):
        """应用隐身措施"""
        
        # 1. 随机User-Agent
        await page.set_extra_http_headers({
            'User-Agent': random.choice(self.user_agents)
        })
        
        # 2. 移除webdriver标识
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
        """)
        
        # 3. 随机屏幕分辨率
        viewport_sizes = [(1920, 1080), (1366, 768), (1536, 864)]
        width, height = random.choice(viewport_sizes)
        await page.set_viewport_size({"width": width, "height": height})
        
        # 4. 模拟人类行为延迟
        behavior = random.choice(self.behavior_patterns)
        self.current_behavior = behavior
    
    async def simulate_human_behavior(self, page):
        """模拟人类浏览行为"""
        
        # 随机滚动
        scroll_delay = random.uniform(*self.current_behavior["scroll_delay"])
        await page.evaluate(f"""
            window.scrollTo({{
                top: Math.random() * document.body.scrollHeight * 0.3,
                behavior: 'smooth'
            }});
        """)
        await asyncio.sleep(scroll_delay)
        
        # 随机鼠标移动
        await page.mouse.move(
            random.randint(100, 800),
            random.randint(100, 600)
        )
```

## 4. 数据处理和验证

### 4.1 数据清洗管道
```python
class DataCleaningPipeline:
    def __init__(self):
        self.nlp = spacy.load("zh_core_web_sm")
    
    async def clean_job_data(self, raw_jobs: List[Dict]) -> List[JobData]:
        """清洗和标准化职位数据"""
        cleaned_jobs = []
        
        for job in raw_jobs:
            try:
                cleaned_job = JobData(
                    title=self._clean_title(job.get('title', '')),
                    company=self._clean_company_name(job.get('company', '')),
                    location=self._normalize_location(job.get('location', '')),
                    published_at=self._parse_date(job.get('published_at', '')),
                    description=self._clean_description(job.get('description', '')),
                    link=self._validate_url(job.get('link', '')),
                    skills=self._extract_skills(job.get('description', ''))
                )
                
                # 数据质量评分
                cleaned_job.quality_score = self._calculate_quality_score(cleaned_job)
                
                if cleaned_job.quality_score >= 0.7:  # 质量阈值
                    cleaned_jobs.append(cleaned_job)
                    
            except Exception as e:
                logger.warning(f"清洗职位数据失败: {e}")
                continue
        
        return cleaned_jobs
    
    def _extract_skills(self, description: str) -> List[str]:
        """从职位描述中提取技能关键词"""
        doc = self.nlp(description)
        
        # 技能关键词词典
        skill_keywords = {
            'programming': ['Python', 'Java', 'JavaScript', 'C++', 'Go', 'Rust'],
            'frameworks': ['Django', 'Flask', 'React', 'Vue', 'Angular', 'Spring'],
            'databases': ['MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'Oracle'],
            'cloud': ['AWS', 'Azure', '阿里云', '腾讯云', 'Docker', 'Kubernetes']
        }
        
        extracted_skills = []
        text_upper = description.upper()
        
        for category, skills in skill_keywords.items():
            for skill in skills:
                if skill.upper() in text_upper:
                    extracted_skills.append(skill)
        
        return list(set(extracted_skills))
```

### 4.2 选择器验证系统
```python
class SelectorValidator:
    async def validate_selectors(self, url: str, selectors: Dict[str, str]) -> ValidationResult:
        """验证选择器的准确性和稳定性"""
        
        validation_result = ValidationResult()
        
        # 1. 单页面验证
        single_page_result = await self._validate_single_page(url, selectors)
        validation_result.single_page_accuracy = single_page_result.accuracy
        
        # 2. 多页面稳定性测试
        multi_page_result = await self._validate_multiple_pages(url, selectors)
        validation_result.multi_page_stability = multi_page_result.stability
        
        # 3. 数据完整性检查
        completeness_result = await self._check_data_completeness(url, selectors)
        validation_result.data_completeness = completeness_result.completeness
        
        # 4. 计算综合评分
        validation_result.overall_score = (
            validation_result.single_page_accuracy * 0.4 +
            validation_result.multi_page_stability * 0.4 +
            validation_result.data_completeness * 0.2
        )
        
        return validation_result
    
    async def _validate_single_page(self, url: str, selectors: Dict) -> SinglePageResult:
        """单页面验证"""
        browser_agent = CrawlerBrowserAgent()
        agent = await browser_agent.create_extraction_agent(selectors)
        
        try:
            # 提取数据
            extraction_result = await agent.run(f"请访问 {url} 并提取职位数据")
            extracted_data = json.loads(extraction_result)
            
            # 计算准确性
            accuracy = self._calculate_extraction_accuracy(extracted_data)
            
            return SinglePageResult(accuracy=accuracy, data=extracted_data)
            
        except Exception as e:
            logger.error(f"单页面验证失败: {e}")
            return SinglePageResult(accuracy=0.0, error=str(e))
```

## 5. API设计

### 5.1 核心API端点
```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI(title="AI Crawler Assistant API", version="1.0.0")

class AnalyzeUrlRequest(BaseModel):
    url: str
    options: Optional[Dict] = {}

class StartCrawlingRequest(BaseModel):
    url: str
    selectors: Dict[str, str]
    options: CrawlOptions

@app.post("/api/v1/analyze-url")
async def analyze_url(request: AnalyzeUrlRequest):
    """分析URL并生成选择器配置"""
    
    # 1. 页面分析
    analyzer = PageStructureAnalyzer()
    analysis_result = await analyzer.analyze_page(request.url)
    
    # 2. 选择器生成
    selector_generator = SelectorGenerator()
    selectors = await selector_generator.generate_selectors(analysis_result)
    
    # 3. 验证选择器
    validator = SelectorValidator()
    validation_result = await validator.validate_selectors(request.url, selectors)
    
    return {
        "selectors": selectors,
        "confidence_score": validation_result.overall_score,
        "validation_details": validation_result.dict(),
        "suggestions": selector_generator.get_optimization_suggestions()
    }

@app.post("/api/v1/start-crawling")
async def start_crawling(request: StartCrawlingRequest, background_tasks: BackgroundTasks):
    """启动爬虫任务"""
    
    # 创建爬虫会话
    session = CrawlSession(
        url=request.url,
        selectors=request.selectors,
        options=request.options
    )
    
    # 后台异步执行爬虫任务
    background_tasks.add_task(execute_crawling_task, session)
    
    return {
        "session_id": session.id,
        "status": "started",
        "estimated_duration": session.estimate_duration()
    }

@app.get("/api/v1/crawl-status/{session_id}")
async def get_crawl_status(session_id: str):
    """获取爬虫任务状态"""
    
    session = await CrawlSession.get(session_id)
    
    return {
        "session_id": session_id,
        "status": session.status,
        "progress": {
            "pages_crawled": session.pages_crawled,
            "jobs_found": session.jobs_found,
            "current_page": session.current_page_url
        },
        "errors": session.get_recent_errors(),
        "estimated_remaining": session.estimate_remaining_time()
    }
```

## 6. 部署和运维

### 6.1 Docker配置
```dockerfile
# Dockerfile
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器
RUN playwright install chromium

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 6.2 Docker Compose配置
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/crawler_db
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./exports:/app/exports
      - ./screenshots:/app/screenshots

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=crawler_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  worker:
    build: .
    command: celery -A crawler_app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/crawler_db
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./exports:/app/exports
      - ./screenshots:/app/screenshots

volumes:
  postgres_data:
  redis_data:
```

## 7. 性能优化和监控

### 7.1 性能监控
```python
import time
import psutil
from prometheus_client import Counter, Histogram, Gauge

# 性能指标
extraction_requests = Counter('extraction_requests_total', 'Total extraction requests')
extraction_duration = Histogram('extraction_duration_seconds', 'Time spent on extraction')
browser_sessions = Gauge('active_browser_sessions', 'Number of active browser sessions')
memory_usage = Gauge('memory_usage_bytes', 'Memory usage in bytes')

class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
    
    async def track_extraction_performance(self, func):
        """性能追踪装饰器"""
        extraction_requests.inc()
        
        start_time = time.time()
        try:
            result = await func()
            return result
        finally:
            duration = time.time() - start_time
            extraction_duration.observe(duration)
    
    async def monitor_system_resources(self):
        """监控系统资源使用"""
        while True:
            # 内存使用
            memory_info = psutil.virtual_memory()
            memory_usage.set(memory_info.used)
            
            # 浏览器会话数
            active_sessions = await self.count_active_browser_sessions()
            browser_sessions.set(active_sessions)
            
            await asyncio.sleep(30)  # 每30秒更新一次
```

这个技术规格文档提供了完整的实现指南，包括：

1. **系统架构**: 清晰的分层设计和技术栈选择
2. **AI选择器提取**: 详细的算法实现和代码示例
3. **Browser-use集成**: 完整的浏览器自动化方案
4. **数据处理**: 数据清洗、验证和质量控制
5. **API设计**: RESTful API接口规范
6. **部署方案**: Docker容器化和编排配置
7. **性能监控**: 系统性能和资源监控机制

这个架构设计确保了系统的可扩展性、稳定性和智能化水平，能够满足不同招聘网站的爬取需求。

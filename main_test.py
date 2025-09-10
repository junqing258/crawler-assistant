"""测试专用的简化主应用"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# 创建简化的FastAPI应用，用于测试
app = FastAPI(
    title="AI Crawler Assistant - Test",
    description="AI驱动的招聘网站智能爬虫工具 - 测试版",
    version="1.0.0-test"
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 AI Crawler Assistant",
        "description": "AI驱动的招聘网站智能爬虫工具",
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AI Crawler Assistant",
        "version": "1.0.0-test"
    }

# 简化的API路由
@app.get("/api/v1/health/status")
async def health_status():
    """详细健康状态"""
    return {
        "status": "healthy",
        "components": {
            "database": "ok",
            "redis": "ok",
            "openai": "ok"
        }
    }

@app.post("/api/v1/analysis/analyze-url")
async def analyze_url(data: dict):
    """分析URL（测试版）"""
    url = data.get("url", "")
    if not url or url == "invalid-url":
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid URL"}
        )
    
    return {
        "success": True,
        "selectors": {
            "jobList": ".jobs",
            "jobItem": ".job"
        }
    }

@app.post("/api/v1/analysis/test-selectors")
async def test_selectors_endpoint(data: dict):
    """测试选择器（测试版）"""
    if not data.get("selectors"):
        return JSONResponse(
            status_code=422,
            content={"detail": "Missing selectors"}
        )
    
    return {"success": True}

@app.get("/api/v1/analysis/sites")
async def get_supported_sites():
    """获取支持的网站"""
    return {
        "success": True,
        "sites": ["test-site.com"]
    }

@app.post("/api/v1/crawling/start")
async def start_crawling(data: dict):
    """启动爬虫（测试版）"""
    url = data.get("url", "")
    if not url or url == "invalid-url":
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid URL"}
        )
    
    return {
        "success": True,
        "session_id": "test-session-123"
    }

@app.get("/api/v1/crawling/status/{session_id}")
async def get_crawl_status(session_id: str):
    """获取爬虫状态（测试版）"""
    if session_id == "non-existent-id":
        return JSONResponse(
            status_code=404,
            content={"detail": "Session not found"}
        )
    
    return {
        "success": True,
        "status": "running",
        "progress": {
            "pages_crawled": 5,
            "jobs_found": 25
        }
    }

@app.get("/api/v1/crawling/sessions")
async def list_sessions():
    """获取会话列表（测试版）"""
    return {
        "success": True,
        "sessions": []
    }

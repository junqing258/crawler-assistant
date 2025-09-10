"""API测试"""

import asyncio
import os

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# 设置测试环境变量，避免数据库连接问题
os.environ.update({
    "DATABASE_URL": "sqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379",
    "OPENAI_API_KEY": "test-key",
    "CELERY_BROKER_URL": "redis://localhost:6379",
    "CELERY_RESULT_BACKEND": "redis://localhost:6379"
})

try:
    from main_test import app  # 使用测试版应用
except ImportError as e:
    pytest.skip(f"无法导入测试应用: {e}", allow_module_level=True)


class TestHealthAPI:
    """健康检查API测试"""
    
    def test_root_endpoint(self):
        """测试根端点"""
        with TestClient(app) as client:
            response = client.get("/")
            assert response.status_code == 200
            assert "AI Crawler Assistant" in response.json()["message"]
    
    def test_health_endpoint(self):
        """测试健康检查端点"""
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "healthy"
    
    def test_health_status_endpoint(self):
        """测试详细健康状态端点"""
        with TestClient(app) as client:
            response = client.get("/api/v1/health/status")
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "components" in data


class TestAnalysisAPI:
    """页面分析API测试"""
    
    def test_analyze_url_invalid_request(self):
        """测试无效URL分析请求"""
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/analysis/analyze-url",
                json={"url": "invalid-url"}
            )
            assert response.status_code == 422  # 验证错误
    
    def test_test_selectors_invalid_request(self):
        """测试无效选择器测试请求"""
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/analysis/test-selectors",
                json={
                    "url": "https://example.com",
                    "selectors": {}  # 缺少必需字段
                }
            )
            assert response.status_code == 422  # 验证错误
    
    def test_get_supported_sites(self):
        """测试获取支持网站列表"""
        with TestClient(app) as client:
            response = client.get("/api/v1/analysis/sites")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "sites" in data


class TestCrawlingAPI:
    """爬虫任务API测试"""
    
    def test_start_crawling_invalid_request(self):
        """测试无效爬虫启动请求"""
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/crawling/start",
                json={"url": "invalid-url"}
            )
            assert response.status_code == 422  # 验证错误
    
    def test_get_crawl_status_not_found(self):
        """测试查询不存在的爬虫状态"""
        with TestClient(app) as client:
            response = client.get("/api/v1/crawling/status/non-existent-id")
            assert response.status_code == 404
    
    def test_list_sessions(self):
        """测试获取会话列表"""
        with TestClient(app) as client:
            response = client.get("/api/v1/crawling/sessions")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "sessions" in data


@pytest.mark.asyncio
class TestAsyncAPI:
    """异步API测试"""
    
    async def test_analyze_url_with_mock(self):
        """使用模拟数据测试URL分析"""
        # 这里可以添加更复杂的异步测试
        # 例如模拟OpenAI API响应等
        pass
    
    async def test_crawling_workflow(self):
        """测试完整的爬虫工作流程"""
        # 这里可以添加端到端的工作流程测试
        pass


if __name__ == "__main__":
    pytest.main([__file__])


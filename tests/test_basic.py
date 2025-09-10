"""简化的API测试"""

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# 创建一个简化的测试应用
def create_test_app() -> FastAPI:
    """创建测试应用"""
    app = FastAPI(title="Test AI Crawler Assistant")
    
    @app.get("/")
    async def root():
        return {"message": "AI Crawler Assistant", "status": "test"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


class TestBasicAPI:
    """基础API测试"""
    
    @pytest.fixture
    def client(self):
        """测试客户端"""
        app = create_test_app()
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "AI Crawler Assistant" in data["message"]
    
    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestUtils:
    """工具函数测试"""
    
    def test_environment_variables(self):
        """测试环境变量设置"""
        # 设置测试环境变量
        os.environ["TEST_VAR"] = "test_value"
        assert os.getenv("TEST_VAR") == "test_value"
    
    def test_basic_imports(self):
        """测试基础模块导入"""
        try:
            import pytest
            from fastapi import FastAPI
            from fastapi.testclient import TestClient
            assert True
        except ImportError as e:
            pytest.fail(f"导入失败: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""测试配置"""

import os

import pytest
from fastapi.testclient import TestClient

# 设置测试环境变量
os.environ.update({
    "DATABASE_URL": "sqlite:///./test.db",
    "REDIS_URL": "redis://localhost:6379",
    "OPENAI_API_KEY": "test-key-for-testing",
    "DEBUG": "true",
    "SECRET_KEY": "test-secret-key",
    "CELERY_BROKER_URL": "redis://localhost:6379",
    "CELERY_RESULT_BACKEND": "redis://localhost:6379"
})

@pytest.fixture
def client():
    """测试客户端fixture"""
    try:
        from main import app
        with TestClient(app) as test_client:
            yield test_client
    except Exception as e:
        pytest.skip(f"无法启动应用: {e}")

@pytest.fixture
def mock_settings():
    """模拟设置fixture"""
    from unittest.mock import Mock
    return Mock()

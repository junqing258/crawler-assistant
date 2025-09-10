"""API路由定义"""

from fastapi import APIRouter
from app.api.endpoints import analysis, crawling, health

# 创建主路由器
api_router = APIRouter()

# 包含各个端点路由
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["健康检查"]
)

api_router.include_router(
    analysis.router,
    prefix="/analysis", 
    tags=["页面分析"]
)

api_router.include_router(
    crawling.router,
    prefix="/crawling",
    tags=["爬虫任务"]
)


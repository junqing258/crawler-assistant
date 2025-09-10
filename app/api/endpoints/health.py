"""健康检查端点"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_async_db, db_manager
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
async def health_status(db: AsyncSession = Depends(get_async_db)):
    """详细的健康检查"""
    
    status = {
        "status": "healthy",
        "components": {}
    }
    
    # 检查数据库连接
    try:
        db_status = await db_manager.check_connection()
        status["components"]["database"] = {
            "status": "healthy" if db_status else "unhealthy",
            "details": "PostgreSQL connection"
        }
    except Exception as e:
        status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 检查Redis连接
    try:
        redis_status = await db_manager.check_redis_connection()
        status["components"]["redis"] = {
            "status": "healthy" if redis_status else "unhealthy",
            "details": "Redis connection"
        }
    except Exception as e:
        status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 检查整体状态
    unhealthy_components = [
        name for name, component in status["components"].items()
        if component["status"] == "unhealthy"
    ]
    
    if unhealthy_components:
        status["status"] = "unhealthy"
        status["unhealthy_components"] = unhealthy_components
    
    return status


@router.get("/ping")
async def ping():
    """简单的ping检查"""
    return {"message": "pong"}


@router.get("/version")
async def version():
    """版本信息"""
    return {
        "service": "AI Crawler Assistant",
        "version": "1.0.0",
        "description": "AI驱动的招聘网站智能爬虫工具"
    }


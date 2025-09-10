"""AI Crawler Assistant 主应用"""

import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv
# env
from app.config import settings
from app.database import startup_database, shutdown_database
from app.api.routes import api_router
from app.utils.logging_config import setup_logging

# 加载环境变量
load_dotenv()
# 设置日志
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("启动 AI Crawler Assistant...")
    
    try:
        # 初始化数据库
        await startup_database()
        logger.info("数据库初始化完成")
        
        # 创建必要的目录
        import os
        os.makedirs(settings.upload_dir, exist_ok=True)
        os.makedirs(settings.export_dir, exist_ok=True)
        os.makedirs(settings.screenshot_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        logger.info("目录结构创建完成")
        
        logger.info("应用启动完成")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        sys.exit(1)
    
    yield  # 应用运行期间
    
    # 关闭时清理
    logger.info("正在关闭 AI Crawler Assistant...")
    
    try:
        await shutdown_database()
        logger.info("数据库连接已关闭")
        
    except Exception as e:
        logger.error(f"应用关闭异常: {e}")
    
    logger.info("应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="AI Crawler Assistant",
    description="AI驱动的招聘网站智能爬虫工具",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "message": str(exc) if settings.debug else "服务暂时不可用",
            "path": str(request.url.path)
        }
    )


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AI Crawler Assistant",
        "version": "1.0.0"
    }


# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 AI Crawler Assistant",
        "description": "AI驱动的招聘网站智能爬虫工具",
        "docs": "/docs",
        "api_prefix": "/api/v1"
    }


# 包含API路由
app.include_router(api_router, prefix="/api/v1")

# 静态文件服务（用于导出文件下载）
app.mount("/exports", StaticFiles(directory=settings.export_dir), name="exports")
app.mount("/screenshots", StaticFiles(directory=settings.screenshot_dir), name="screenshots")


if __name__ == "__main__":
    # 直接运行应用
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
        access_log=True
    )


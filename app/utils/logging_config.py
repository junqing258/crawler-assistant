"""日志配置"""

import logging
import logging.handlers
import sys
from pathlib import Path
from app.config import settings


def setup_logging():
    """设置日志配置"""
    
    # 创建日志目录
    log_dir = Path(settings.log_file_path).parent
    log_dir.mkdir(exist_ok=True)
    
    # 设置日志级别
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # 创建根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除已有的处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=settings.log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("playwright").setLevel(logging.WARNING)
    
    logging.info("日志配置完成")


class RequestLoggerMiddleware:
    """请求日志中间件"""
    
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("requests")
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # 记录请求信息
            method = scope["method"]
            path = scope["path"]
            client = scope.get("client", ["unknown", 0])
            
            self.logger.info(f"{method} {path} - Client: {client[0]}:{client[1]}")
        
        await self.app(scope, receive, send)


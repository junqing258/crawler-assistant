"""配置管理模块"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")
    secret_key: str = Field(default="your-secret-key-change-this", env="SECRET_KEY")
    
    # 数据库配置
    database_url: str = Field(env="DATABASE_URL")
    redis_url: str = Field(env="REDIS_URL")
    
    # OpenAI配置
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4-vision-preview", env="OPENAI_MODEL")
    openai_base_url: str = Field(default="https://api.openai.com/v1", env="OPENAI_BASE_URL")
    
    # Browser配置
    browser_headless: bool = Field(default=True, env="BROWSER_HEADLESS")
    browser_timeout: int = Field(default=30000, env="BROWSER_TIMEOUT")
    browser_viewport_width: int = Field(default=1920, env="BROWSER_VIEWPORT_WIDTH")
    browser_viewport_height: int = Field(default=1080, env="BROWSER_VIEWPORT_HEIGHT")
    
    # 代理配置
    proxy_enabled: bool = Field(default=False, env="PROXY_ENABLED")
    proxy_list: Optional[str] = Field(default=None, env="PROXY_LIST")
    
    # 反爬虫配置
    enable_stealth_mode: bool = Field(default=True, env="ENABLE_STEALTH_MODE")
    human_behavior_simulation: bool = Field(default=True, env="HUMAN_BEHAVIOR_SIMULATION")
    user_agent_rotation: bool = Field(default=True, env="USER_AGENT_ROTATION")
    
    # Celery配置
    celery_broker_url: str = Field(env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(env="CELERY_RESULT_BACKEND")
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file_path: str = Field(default="logs/app.log", env="LOG_FILE_PATH")
    
    # 存储配置
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    export_dir: str = Field(default="exports", env="EXPORT_DIR")
    screenshot_dir: str = Field(default="screenshots", env="SCREENSHOT_DIR")
    
    # 性能配置
    max_concurrent_sessions: int = Field(default=5, env="MAX_CONCURRENT_SESSIONS")
    max_pages_per_session: int = Field(default=100, env="MAX_PAGES_PER_SESSION")
    request_delay_min: int = Field(default=1, env="REQUEST_DELAY_MIN")
    request_delay_max: int = Field(default=3, env="REQUEST_DELAY_MAX")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def proxy_list_parsed(self) -> List[str]:
        """解析代理列表"""
        if not self.proxy_list:
            return []
        return [proxy.strip() for proxy in self.proxy_list.split(",")]
    
    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return self.database_url
    
    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        return self.redis_url


# 全局配置实例
settings = Settings()


class BrowserConfig:
    """浏览器配置类"""
    
    def __init__(self):
        self.headless = settings.browser_headless
        self.timeout = settings.browser_timeout
        self.viewport = {
            "width": settings.browser_viewport_width,
            "height": settings.browser_viewport_height
        }
        self.stealth_mode = settings.enable_stealth_mode
        
    def get_launch_options(self) -> dict:
        """获取浏览器启动选项"""
        options = {
            "headless": self.headless,
            "viewport": self.viewport,
            "args": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-extensions",
                "--disable-plugins",
                "--disable-images",  # 禁用图片加载以提高性能
                "--disable-javascript",  # 可选：禁用JS（如果不需要）
            ]
        }
        
        if self.stealth_mode:
            options["args"].extend([
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            ])
            
        return options


class CrawlConfig:
    """爬虫配置类"""
    
    def __init__(self):
        self.max_pages = settings.max_pages_per_session
        self.delay_min = settings.request_delay_min
        self.delay_max = settings.request_delay_max
        self.timeout = settings.browser_timeout
        
    def get_random_delay(self) -> tuple:
        """获取随机延迟范围"""
        return (self.delay_min, self.delay_max)


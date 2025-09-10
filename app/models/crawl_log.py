"""爬取日志模型"""

from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, JSON
from .base import GUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import BaseModel


class LogLevel(PyEnum):
    """日志级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorType(PyEnum):
    """错误类型枚举"""
    NETWORK_ERROR = "network_error"
    SELECTOR_ERROR = "selector_error"
    PARSING_ERROR = "parsing_error"
    TIMEOUT_ERROR = "timeout_error"
    ANTI_BOT_ERROR = "anti_bot_error"
    VALIDATION_ERROR = "validation_error"
    UNKNOWN_ERROR = "unknown_error"


class CrawlLog(BaseModel):
    """爬取日志模型"""
    
    __tablename__ = "crawl_logs"
    
    session_id = Column(GUID(), ForeignKey("crawl_sessions.id"), nullable=False, comment="会话ID")
    
    log_level = Column(Enum(LogLevel), nullable=False, comment="日志级别")
    message = Column(Text, nullable=False, comment="日志消息")
    page_url = Column(Text, comment="页面URL")
    error_type = Column(Enum(ErrorType), comment="错误类型")
    stack_trace = Column(Text, comment="堆栈跟踪")
    screenshot_path = Column(String(500), comment="截图路径")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, comment="时间戳")
    context_data = Column(JSON, comment="上下文数据")
    
    # 关系
    session = relationship("CrawlSession", back_populates="logs")
    
    def __repr__(self) -> str:
        return f"<CrawlLog(level={self.log_level.value}, session_id={self.session_id})>"
    
    @property
    def is_error(self) -> bool:
        """是否为错误日志"""
        return self.log_level in [LogLevel.ERROR, LogLevel.CRITICAL]
    
    @property
    def is_warning(self) -> bool:
        """是否为警告日志"""
        return self.log_level == LogLevel.WARNING
    
    def categorize_error(self) -> Optional[str]:
        """分类错误"""
        if not self.is_error:
            return None
        
        if self.error_type:
            return self.error_type.value
        
        # 基于消息内容推断错误类型
        message_lower = self.message.lower()
        
        if "timeout" in message_lower:
            return ErrorType.TIMEOUT_ERROR.value
        elif "selector" in message_lower or "element not found" in message_lower:
            return ErrorType.SELECTOR_ERROR.value
        elif "network" in message_lower or "connection" in message_lower:
            return ErrorType.NETWORK_ERROR.value
        elif "captcha" in message_lower or "robot" in message_lower:
            return ErrorType.ANTI_BOT_ERROR.value
        elif "parse" in message_lower or "parsing" in message_lower:
            return ErrorType.PARSING_ERROR.value
        else:
            return ErrorType.UNKNOWN_ERROR.value
    
    def extract_insights(self) -> Dict[str, Any]:
        """提取日志洞察"""
        insights = {
            "timestamp": self.timestamp.isoformat(),
            "level": self.log_level.value,
            "category": self.categorize_error(),
            "has_screenshot": bool(self.screenshot_path),
            "page_url": self.page_url
        }
        
        # 添加上下文数据
        if self.context_data:
            insights["context"] = self.context_data
        
        return insights
    
    @classmethod
    def create_info_log(cls, session_id: str, message: str, page_url: str = None, 
                       context_data: Dict = None) -> "CrawlLog":
        """创建信息日志"""
        return cls(
            session_id=session_id,
            log_level=LogLevel.INFO,
            message=message,
            page_url=page_url,
            context_data=context_data
        )
    
    @classmethod
    def create_error_log(cls, session_id: str, message: str, error_type: ErrorType = None,
                        page_url: str = None, stack_trace: str = None,
                        screenshot_path: str = None, context_data: Dict = None) -> "CrawlLog":
        """创建错误日志"""
        return cls(
            session_id=session_id,
            log_level=LogLevel.ERROR,
            message=message,
            error_type=error_type,
            page_url=page_url,
            stack_trace=stack_trace,
            screenshot_path=screenshot_path,
            context_data=context_data
        )
    
    @classmethod
    def create_warning_log(cls, session_id: str, message: str, page_url: str = None,
                          context_data: Dict = None) -> "CrawlLog":
        """创建警告日志"""
        return cls(
            session_id=session_id,
            log_level=LogLevel.WARNING,
            message=message,
            page_url=page_url,
            context_data=context_data
        )


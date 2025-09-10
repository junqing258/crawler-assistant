"""爬取会话模型"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Enum
from .base import GUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import BaseModel


class SessionStatus(PyEnum):
    """会话状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CrawlSession(BaseModel):
    """爬取会话模型"""
    
    __tablename__ = "crawl_sessions"
    
    site_id = Column(GUID(), ForeignKey("job_sites.id"), nullable=False, comment="网站ID")
    selector_config_id = Column(GUID(), ForeignKey("selector_configs.id"), nullable=False, comment="选择器配置ID")
    
    start_url = Column(Text, nullable=False, comment="起始URL")
    status = Column(Enum(SessionStatus), default=SessionStatus.PENDING, comment="会话状态")
    
    # 进度信息
    total_pages = Column(Integer, default=0, comment="总页数")
    pages_crawled = Column(Integer, default=0, comment="已爬取页数")
    jobs_found = Column(Integer, default=0, comment="发现的职位数")
    jobs_saved = Column(Integer, default=0, comment="保存的职位数")
    errors_count = Column(Integer, default=0, comment="错误次数")
    
    # 时间信息
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    duration_seconds = Column(Integer, comment="持续时间(秒)")
    
    # 配置信息
    user_agent = Column(String(500), comment="User-Agent")
    proxy_used = Column(String(200), comment="使用的代理")
    notes = Column(Text, comment="备注")
    
    # 关系
    site = relationship("JobSite", back_populates="crawl_sessions")
    selector_config = relationship("SelectorConfig", back_populates="crawl_sessions")
    jobs = relationship("Job", back_populates="crawl_session")
    logs = relationship("CrawlLog", back_populates="session")
    
    def __repr__(self) -> str:
        return f"<CrawlSession(id={self.id}, status={self.status.value})>"
    
    @property
    def is_running(self) -> bool:
        """是否正在运行"""
        return self.status == SessionStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status in [SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED]
    
    def start_session(self) -> None:
        """启动会话"""
        self.status = SessionStatus.RUNNING
        self.started_at = datetime.utcnow()
    
    def complete_session(self, success: bool = True) -> None:
        """完成会话"""
        self.status = SessionStatus.COMPLETED if success else SessionStatus.FAILED
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = int(duration.total_seconds())
    
    def cancel_session(self) -> None:
        """取消会话"""
        self.status = SessionStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.duration_seconds = int(duration.total_seconds())
    
    def update_progress(self, pages_crawled: int = None, jobs_found: int = None, 
                       jobs_saved: int = None, errors_count: int = None) -> None:
        """更新进度"""
        if pages_crawled is not None:
            self.pages_crawled = pages_crawled
        if jobs_found is not None:
            self.jobs_found = jobs_found
        if jobs_saved is not None:
            self.jobs_saved = jobs_saved
        if errors_count is not None:
            self.errors_count = errors_count
    
    def calculate_success_rate(self) -> float:
        """计算成功率"""
        if self.jobs_found == 0:
            return 0.0
        return self.jobs_saved / self.jobs_found
    
    def estimate_remaining_time(self) -> Optional[int]:
        """估算剩余时间(秒)"""
        if not self.started_at or self.pages_crawled == 0 or self.total_pages <= self.pages_crawled:
            return None
        
        elapsed = datetime.utcnow() - self.started_at
        avg_time_per_page = elapsed.total_seconds() / self.pages_crawled
        remaining_pages = self.total_pages - self.pages_crawled
        
        return int(avg_time_per_page * remaining_pages)
    
    def get_progress_percentage(self) -> float:
        """获取进度百分比"""
        if self.total_pages == 0:
            return 0.0
        return min(self.pages_crawled / self.total_pages * 100, 100.0)
    
    def generate_report(self) -> Dict[str, Any]:
        """生成会话报告"""
        duration_str = ""
        if self.duration_seconds:
            duration = timedelta(seconds=self.duration_seconds)
            duration_str = str(duration)
        
        return {
            "session_id": str(self.id),
            "status": self.status.value,
            "start_url": self.start_url,
            "progress": {
                "total_pages": self.total_pages,
                "pages_crawled": self.pages_crawled,
                "jobs_found": self.jobs_found,
                "jobs_saved": self.jobs_saved,
                "errors_count": self.errors_count,
                "success_rate": self.calculate_success_rate(),
                "progress_percentage": self.get_progress_percentage()
            },
            "timing": {
                "started_at": self.started_at.isoformat() if self.started_at else None,
                "completed_at": self.completed_at.isoformat() if self.completed_at else None,
                "duration": duration_str,
                "estimated_remaining": self.estimate_remaining_time()
            },
            "configuration": {
                "user_agent": self.user_agent,
                "proxy_used": self.proxy_used
            }
        }


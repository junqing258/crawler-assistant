"""招聘网站模型"""

from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from .base import BaseModel


class JobSite(BaseModel):
    """招聘网站模型"""
    
    __tablename__ = "job_sites"
    
    name = Column(String(200), nullable=False, comment="网站名称")
    base_url = Column(String(500), nullable=False, comment="基础URL")
    domain = Column(String(200), nullable=False, unique=True, comment="域名")
    site_type = Column(String(50), comment="网站类型")
    language = Column(String(10), default="zh", comment="语言")
    country = Column(String(10), default="CN", comment="国家")
    is_active = Column(Boolean, default=True, comment="是否激活")
    description = Column(Text, comment="网站描述")
    
    # 关系
    selector_configs = relationship("SelectorConfig", back_populates="site")
    jobs = relationship("Job", back_populates="site")
    crawl_sessions = relationship("CrawlSession", back_populates="site")
    ai_analyses = relationship("AIAnalysisResult", back_populates="site")
    
    def __repr__(self) -> str:
        return f"<JobSite(name='{self.name}', domain='{self.domain}')>"
    
    @property
    def is_chinese_site(self) -> bool:
        """是否为中文网站"""
        return self.language == "zh"
    
    def validate_url(self, url: str) -> bool:
        """验证URL是否属于此网站"""
        return self.domain in url


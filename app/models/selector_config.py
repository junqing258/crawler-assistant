"""选择器配置模型"""

import json
from typing import Dict, Any, Optional
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, ForeignKey, JSON
from .base import GUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class SelectorConfig(BaseModel):
    """选择器配置模型"""
    
    __tablename__ = "selector_configs"
    
    site_id = Column(GUID(), ForeignKey("job_sites.id"), nullable=False, comment="网站ID")
    version = Column(String(20), nullable=False, comment="版本号")
    selectors = Column(JSON, nullable=False, comment="选择器配置JSON")
    confidence_score = Column(Float, default=0.0, comment="置信度评分")
    validation_status = Column(String(20), default="pending", comment="验证状态")
    test_count = Column(Integer, default=0, comment="测试次数")
    success_rate = Column(Float, default=0.0, comment="成功率")
    created_by = Column(String(100), comment="创建者")
    is_active = Column(Boolean, default=True, comment="是否激活")
    notes = Column(Text, comment="备注")
    
    # 关系
    site = relationship("JobSite", back_populates="selector_configs")
    crawl_sessions = relationship("CrawlSession", back_populates="selector_config")
    
    def __repr__(self) -> str:
        return f"<SelectorConfig(site_id={self.site_id}, version='{self.version}')>"
    
    @property
    def selectors_dict(self) -> Dict[str, str]:
        """获取选择器字典"""
        if isinstance(self.selectors, dict):
            return self.selectors
        return json.loads(self.selectors) if self.selectors else {}
    
    @selectors_dict.setter
    def selectors_dict(self, value: Dict[str, str]) -> None:
        """设置选择器字典"""
        self.selectors = value
    
    def get_selector(self, key: str) -> Optional[str]:
        """获取指定的选择器"""
        return self.selectors_dict.get(key)
    
    def validate_selectors(self) -> bool:
        """验证选择器配置的完整性"""
        required_selectors = [
            "jobList", "jobItem", "jobTitle", "jobLink", 
            "companyName", "publishedAt", "location", "jobDescription"
        ]
        
        selectors = self.selectors_dict
        return all(key in selectors and selectors[key] for key in required_selectors)
    
    def update_success_rate(self, success_count: int, total_count: int) -> None:
        """更新成功率"""
        if total_count > 0:
            self.success_rate = success_count / total_count
            self.test_count = total_count
    
    def get_validation_report(self) -> Dict[str, Any]:
        """获取验证报告"""
        return {
            "version": self.version,
            "confidence_score": self.confidence_score,
            "validation_status": self.validation_status,
            "success_rate": self.success_rate,
            "test_count": self.test_count,
            "is_valid": self.validate_selectors(),
            "last_updated": self.updated_at.isoformat() if self.updated_at else None
        }


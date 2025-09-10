"""职位信息模型"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from .base import GUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class Job(BaseModel):
    """职位信息模型"""
    
    __tablename__ = "jobs"
    
    site_id = Column(GUID(), ForeignKey("job_sites.id"), nullable=False, comment="网站ID")
    crawl_session_id = Column(GUID(), ForeignKey("crawl_sessions.id"), nullable=False, comment="爬取会话ID")
    
    # 基础职位信息
    title = Column(String(500), nullable=False, comment="职位标题")
    company_name = Column(String(200), nullable=False, comment="公司名称")
    job_link = Column(Text, comment="职位链接")
    location = Column(String(200), comment="工作地点")
    published_at = Column(DateTime, comment="发布时间")
    job_description = Column(Text, comment="职位描述")
    
    # 扩展信息
    salary_range = Column(String(100), comment="薪资范围")
    job_type = Column(String(50), comment="工作类型")
    experience_level = Column(String(50), comment="经验要求")
    education_level = Column(String(50), comment="学历要求")
    skills_required = Column(JSON, comment="技能要求")
    remote_option = Column(Boolean, default=False, comment="是否支持远程")
    
    # 数据质量和元数据
    raw_data = Column(JSON, comment="原始数据JSON")
    extracted_at = Column(DateTime, default=datetime.utcnow, comment="提取时间")
    data_quality_score = Column(Float, default=0.0, comment="数据质量评分")
    
    # 关系
    site = relationship("JobSite", back_populates="jobs")
    crawl_session = relationship("CrawlSession", back_populates="jobs")
    
    def __repr__(self) -> str:
        return f"<Job(title='{self.title}', company='{self.company_name}')>"
    
    @property
    def is_high_quality(self) -> bool:
        """是否为高质量数据"""
        return self.data_quality_score >= 0.8
    
    @property
    def skills_list(self) -> List[str]:
        """获取技能列表"""
        return self.skills_required or []
    
    def calculate_quality_score(self) -> float:
        """计算数据质量评分"""
        score = 0.0
        total_weight = 0.0
        
        # 必需字段权重
        required_fields = {
            'title': 0.3,
            'company_name': 0.2,
            'location': 0.1,
            'job_description': 0.2,
            'published_at': 0.1,
            'job_link': 0.1
        }
        
        for field, weight in required_fields.items():
            value = getattr(self, field)
            total_weight += weight
            
            if value:
                if isinstance(value, str) and len(value.strip()) > 0:
                    score += weight
                elif isinstance(value, datetime):
                    score += weight
                elif value:  # 其他非空值
                    score += weight
        
        # 额外信息加分
        bonus_fields = ['salary_range', 'job_type', 'experience_level', 'skills_required']
        bonus_weight = 0.1
        bonus_count = 0
        
        for field in bonus_fields:
            value = getattr(self, field)
            if value:
                if isinstance(value, list) and len(value) > 0:
                    bonus_count += 1
                elif isinstance(value, str) and len(value.strip()) > 0:
                    bonus_count += 1
        
        bonus_score = (bonus_count / len(bonus_fields)) * bonus_weight
        final_score = (score / total_weight) + bonus_score
        
        return min(final_score, 1.0)  # 确保不超过1.0
    
    def update_quality_score(self) -> None:
        """更新质量评分"""
        self.data_quality_score = self.calculate_quality_score()
    
    def clean_description(self) -> str:
        """清理职位描述"""
        if not self.job_description:
            return ""
        
        # 移除多余的空白字符
        cleaned = " ".join(self.job_description.split())
        
        # 移除HTML标签（如果有）
        import re
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        return cleaned.strip()
    
    def extract_salary_info(self) -> Dict[str, Optional[float]]:
        """提取薪资信息"""
        if not self.salary_range:
            return {"min_salary": None, "max_salary": None, "currency": None}
        
        import re
        
        # 匹配不同的薪资格式
        patterns = [
            r'(\d+)-(\d+)k',  # 20-30k
            r'(\d+)k-(\d+)k',  # 20k-30k
            r'(\d+)-(\d+)万',  # 20-30万
            r'(\d+)万-(\d+)万',  # 20万-30万
        ]
        
        for pattern in patterns:
            match = re.search(pattern, self.salary_range.lower())
            if match:
                min_sal, max_sal = match.groups()
                
                # 转换为月薪（千元）
                if 'k' in pattern:
                    return {
                        "min_salary": float(min_sal),
                        "max_salary": float(max_sal),
                        "currency": "CNY"
                    }
                elif '万' in pattern:
                    return {
                        "min_salary": float(min_sal) * 10,
                        "max_salary": float(max_sal) * 10,
                        "currency": "CNY"
                    }
        
        return {"min_salary": None, "max_salary": None, "currency": None}
    
    def to_export_dict(self) -> Dict[str, Any]:
        """转换为导出格式的字典"""
        salary_info = self.extract_salary_info()
        
        return {
            "id": str(self.id),
            "title": self.title,
            "company": self.company_name,
            "location": self.location,
            "description": self.clean_description(),
            "job_link": self.job_link,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "salary_range": self.salary_range,
            "min_salary": salary_info["min_salary"],
            "max_salary": salary_info["max_salary"],
            "job_type": self.job_type,
            "experience_level": self.experience_level,
            "education_level": self.education_level,
            "skills": self.skills_list,
            "remote_option": self.remote_option,
            "quality_score": self.data_quality_score,
            "extracted_at": self.extracted_at.isoformat() if self.extracted_at else None
        }


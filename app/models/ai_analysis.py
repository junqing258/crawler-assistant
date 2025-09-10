"""AI分析结果模型"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON
from .base import GUID
from sqlalchemy.orm import relationship
from .base import BaseModel


class AIAnalysisResult(BaseModel):
    """AI分析结果模型"""

    __tablename__ = "ai_analysis_results"

    site_id = Column(GUID(), ForeignKey("job_sites.id"), nullable=False, comment="网站ID")

    url_analyzed = Column(Text, nullable=False, comment="分析的URL")
    html_snapshot = Column(Text, comment="HTML快照")
    screenshot_path = Column(String(500), comment="截图路径")
    ai_model_used = Column(String(100), comment="使用的AI模型")
    confidence_score = Column(Float, default=0.0, comment="置信度评分")
    detected_elements = Column(JSON, comment="检测到的元素JSON")
    suggested_selectors = Column(JSON, comment="建议的选择器JSON")
    analysis_notes = Column(Text, comment="分析备注")
    processing_time_ms = Column(Integer, comment="处理时间(毫秒)")
    analyzed_at = Column(DateTime, default=datetime.utcnow, comment="分析时间")

    # 关系
    site = relationship("JobSite", back_populates="ai_analyses")

    def __repr__(self) -> str:
        return f"<AIAnalysisResult(site_id={self.site_id}, confidence={self.confidence_score})>"

    @property
    def detected_elements_dict(self) -> Dict[str, Any]:
        """获取检测元素字典"""
        return self.detected_elements or {}

    @property
    def suggested_selectors_dict(self) -> Dict[str, str]:
        """获取建议选择器字典"""
        return self.suggested_selectors or {}

    @property
    def is_high_confidence(self) -> bool:
        """是否为高置信度分析"""
        return self.confidence_score >= 0.8

    def validate_analysis(self) -> Dict[str, Any]:
        """验证分析结果"""
        required_selectors = [
            "jobList", "jobItem", "jobTitle", "jobLink",
            "companyName", "publishedAt", "location"
        ]

        selectors = self.suggested_selectors_dict
        missing_selectors = [
            sel for sel in required_selectors if sel not in selectors]

        validation_result = {
            "is_valid": len(missing_selectors) == 0,
            "missing_selectors": missing_selectors,
            "confidence_score": self.confidence_score,
            "total_selectors": len(selectors),
            "required_selectors": len(required_selectors)
        }

        return validation_result

    def compare_with_manual(self, manual_selectors: Dict[str, str]) -> Dict[str, Any]:
        """与手动选择器比较"""
        ai_selectors = self.suggested_selectors_dict
        comparison = {
            "matches": {},
            "differences": {},
            "accuracy": 0.0
        }

        total_selectors = len(manual_selectors)
        matches = 0

        for key, manual_sel in manual_selectors.items():
            ai_sel = ai_selectors.get(key)

            if ai_sel == manual_sel:
                comparison["matches"][key] = ai_sel
                matches += 1
            else:
                comparison["differences"][key] = {
                    "manual": manual_sel,
                    "ai": ai_sel
                }

        comparison["accuracy"] = matches / \
            total_selectors if total_selectors > 0 else 0.0

        return comparison

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            "processing_time_ms": self.processing_time_ms,
            "confidence_score": self.confidence_score,
            "model_used": self.ai_model_used,
            "analysis_timestamp": self.analyzed_at.isoformat() if self.analyzed_at else None,
            "has_screenshot": bool(self.screenshot_path),
            "html_size_chars": len(self.html_snapshot) if self.html_snapshot else 0,
            "detected_elements_count": len(self.detected_elements_dict),
            "suggested_selectors_count": len(self.suggested_selectors_dict)
        }

    def generate_selector_config(self, version: str = "1.0.0") -> Dict[str, Any]:
        """生成选择器配置"""
        return {
            "version": version,
            "generated_at": datetime.utcnow().isoformat(),
            "ai_model": self.ai_model_used,
            "confidence_score": self.confidence_score,
            "selectors": self.suggested_selectors_dict,
            "validation": self.validate_analysis(),
            "source_analysis_id": str(self.id)
        }

    def get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        suggestions = []

        # 基于置信度给出建议
        if self.confidence_score < 0.7:
            suggestions.append({
                "type": "confidence",
                "message": "置信度较低，建议手动验证选择器",
                "priority": "high"
            })

        # 检查缺失的选择器
        validation = self.validate_analysis()
        if validation["missing_selectors"]:
            suggestions.append({
                "type": "completeness",
                "message": f"缺失选择器: {', '.join(validation['missing_selectors'])}",
                "priority": "high"
            })

        # 基于处理时间给出建议
        if self.processing_time_ms and self.processing_time_ms > 10000:  # 10秒
            suggestions.append({
                "type": "performance",
                "message": "分析时间较长，建议优化页面结构",
                "priority": "medium"
            })

        return suggestions

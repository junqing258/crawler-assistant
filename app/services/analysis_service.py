"""页面分析服务"""

import time
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.ai.page_analyzer import PageAnalyzer
from app.core.ai.selector_generator import SelectorGenerator
from app.core.browser.browser_controller import BrowserController
from app.models.job_site import JobSite
from app.models.ai_analysis import AIAnalysisResult
from app.models.selector_config import SelectorConfig as SelectorConfigModel
import logging

logger = logging.getLogger(__name__)


class AnalysisService:
    """页面分析服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.page_analyzer = PageAnalyzer()
        self.selector_generator = SelectorGenerator()
    
    async def analyze_page(self, url: str, options: Dict[str, Any], 
                          session_id: str) -> Dict[str, Any]:
        """分析页面并生成选择器"""
        try:
            # 1. 创建或获取网站记录
            site = await self._get_or_create_site(url)
            
            # 2. 使用浏览器加载页面
            browser_controller = BrowserController()
            
            try:
                # 初始化浏览器
                if not await browser_controller.initialize(session_id):
                    return {"success": False, "error": "浏览器初始化失败"}
                
                # 加载页面
                page_result = await browser_controller.load_page(
                    url=url, 
                    wait_for_load=True, 
                    take_screenshot=options.get("include_screenshots", False)
                )
                
                if not page_result.success:
                    return {"success": False, "error": page_result.error_message}
                
                # 3. AI分析页面结构
                ai_analysis = await self.page_analyzer.analyze_page_structure(
                    url=url,
                    html_content=page_result.html_content,
                    screenshot=None  # 暂时不使用截图
                )
                
                # 4. 生成选择器
                selectors = await self.selector_generator.generate_selectors(
                    ai_analysis=ai_analysis,
                    html_content=page_result.html_content
                )
                
                # 5. 验证选择器
                validation_result = await self.page_analyzer.validate_selectors(
                    selectors=selectors,
                    html_content=page_result.html_content
                )
                
                # 6. 生成优化建议
                suggestions = self._generate_suggestions(
                    ai_analysis, validation_result, selectors
                )
                
                analysis_data = {
                    "site_id": site.id,
                    "url": url,
                    "ai_analysis": ai_analysis,
                    "page_result": page_result,
                    "validation_result": validation_result
                }
                
                return {
                    "success": True,
                    "selectors": selectors,
                    "confidence_score": ai_analysis.confidence_score,
                    "validation_details": validation_result,
                    "suggestions": suggestions,
                    "analysis_data": analysis_data
                }
                
            finally:
                await browser_controller.cleanup()
        
        except Exception as e:
            logger.error(f"页面分析失败: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    async def _get_or_create_site(self, url: str) -> JobSite:
        """获取或创建网站记录"""
        try:
            # 解析URL获取域名
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()
            
            # 查询是否已存在
            stmt = select(JobSite).where(JobSite.domain == domain)
            result = await self.db.execute(stmt)
            site = result.scalar_one_or_none()
            
            if not site:
                # 创建新的网站记录
                site_name = self._generate_site_name(domain)
                site = JobSite(
                    name=site_name,
                    base_url=f"{parsed_url.scheme}://{parsed_url.netloc}",
                    domain=domain,
                    site_type="招聘网站",
                    language="zh" if any(ch in domain for ch in ['cn', 'com.cn', 'zhaopin', 'zhipin', 'liepin']) else "en"
                )
                
                self.db.add(site)
                await self.db.commit()
                await self.db.refresh(site)
                
                logger.info(f"创建新网站记录: {site_name} ({domain})")
            
            return site
            
        except Exception as e:
            logger.error(f"获取/创建网站记录失败: {e}")
            raise
    
    def _generate_site_name(self, domain: str) -> str:
        """根据域名生成网站名称"""
        domain_mappings = {
            'zhaopin.com': '智联招聘',
            '51job.com': '前程无忧',
            'zhipin.com': 'BOSS直聘',
            'liepin.com': '猎聘网',
            'lagou.com': '拉勾网',
            'jobui.com': '职友集',
            'indeed.com': 'Indeed',
            'linkedin.com': 'LinkedIn',
            'glassdoor.com': 'Glassdoor'
        }
        
        return domain_mappings.get(domain, domain.replace('www.', '').title())
    
    def _generate_suggestions(self, ai_analysis, validation_result, selectors) -> list:
        """生成优化建议"""
        suggestions = []
        
        # 基于置信度的建议
        if ai_analysis.confidence_score < 0.7:
            suggestions.append("AI分析置信度较低，建议手动验证选择器准确性")
        
        # 基于验证结果的建议
        if validation_result["overall_score"] < 0.8:
            suggestions.append("选择器验证评分较低，建议调整部分选择器")
        
        # 检查必需选择器
        required_selectors = ["jobList", "jobItem", "jobTitle", "companyName"]
        missing_required = [key for key in required_selectors if not selectors.get(key)]
        
        if missing_required:
            suggestions.append(f"缺少必需的选择器: {', '.join(missing_required)}")
        
        # 检查选择器质量
        for key, result in validation_result.get("selector_results", {}).items():
            if not result["valid"]:
                suggestions.append(f"{key}选择器需要调整，当前未找到匹配元素")
            elif result["count"] > 100:
                suggestions.append(f"{key}选择器匹配元素过多({result['count']}个)，建议增加限定条件")
        
        return suggestions
    
    async def save_analysis_result(self, analysis_data: Dict[str, Any], session_id: str):
        """保存分析结果到数据库"""
        try:
            ai_analysis = analysis_data["ai_analysis"]
            page_result = analysis_data["page_result"]
            
            # 创建AI分析结果记录
            ai_result = AIAnalysisResult(
                site_id=analysis_data["site_id"],
                url_analyzed=analysis_data["url"],
                html_snapshot=page_result.html_content[:50000],  # 限制长度
                screenshot_path=page_result.screenshot_path,
                ai_model_used="gpt-4-vision-preview",
                confidence_score=ai_analysis.confidence_score,
                detected_elements=ai_analysis.detected_elements,
                suggested_selectors=ai_analysis.recommended_selectors,
                analysis_notes=ai_analysis.analysis_notes,
                processing_time_ms=ai_analysis.processing_time_ms
            )
            
            self.db.add(ai_result)
            await self.db.commit()
            
            logger.info(f"分析结果已保存: {session_id}")
            
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}", exc_info=True)
    
    async def create_selector_config(self, site_id: str, selectors: Dict[str, str],
                                   confidence_score: float, validation_result: Dict[str, Any],
                                   version: str = "1.0.0") -> SelectorConfigModel:
        """创建选择器配置"""
        try:
            config = SelectorConfigModel(
                site_id=site_id,
                version=version,
                selectors=selectors,
                confidence_score=confidence_score,
                validation_status="validated" if validation_result["overall_score"] >= 0.8 else "needs_review",
                success_rate=validation_result["overall_score"],
                created_by="ai_analysis"
            )
            
            self.db.add(config)
            await self.db.commit()
            await self.db.refresh(config)
            
            return config
            
        except Exception as e:
            logger.error(f"创建选择器配置失败: {e}")
            raise


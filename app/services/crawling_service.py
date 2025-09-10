"""爬虫服务"""

import json
import os
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.job_site import JobSite
from app.models.crawl_session import CrawlSession, SessionStatus
from app.models.job import Job
from app.models.crawl_log import CrawlLog
from app.models.selector_config import SelectorConfig
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class CrawlingService:
    """爬虫服务"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_crawl_session(self, url: str, selectors: Dict[str, str],
                                 options: Dict[str, Any], session_id: str) -> CrawlSession:
        """创建爬虫会话"""
        try:
            # 获取或创建网站记录
            site = await self._get_or_create_site(url)
            
            # 获取或创建选择器配置
            selector_config = await self._get_or_create_selector_config(
                site.id, selectors
            )
            
            # 创建爬虫会话
            session = CrawlSession(
                id=session_id,
                site_id=site.id,
                selector_config_id=selector_config.id,
                start_url=url,
                status=SessionStatus.PENDING,
                total_pages=options.get("max_pages", 10)
            )
            
            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)
            
            logger.info(f"创建爬虫会话: {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"创建爬虫会话失败: {e}")
            await self.db.rollback()
            raise
    
    async def save_crawl_results(self, session_id: str, jobs: List[Dict[str, Any]],
                               crawl_result: Any) -> None:
        """保存爬取结果"""
        try:
            # 获取会话
            stmt = select(CrawlSession).where(CrawlSession.id == session_id)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                raise ValueError(f"会话不存在: {session_id}")
            
            # 保存职位数据
            saved_jobs = 0
            for job_data in jobs:
                job = Job(
                    site_id=session.site_id,
                    crawl_session_id=session.id,
                    title=job_data.get("title", ""),
                    company_name=job_data.get("company", ""),
                    job_link=job_data.get("link", ""),
                    location=job_data.get("location", ""),
                    job_description=job_data.get("description", ""),
                    published_at=self._parse_date(job_data.get("published_at")),
                    raw_data=job_data
                )
                
                # 计算数据质量评分
                job.update_quality_score()
                
                # 只保存质量评分达标的职位
                if job.data_quality_score >= 0.5:  # 质量阈值
                    self.db.add(job)
                    saved_jobs += 1
            
            # 更新会话状态
            session.complete_session(success=True)
            session.pages_crawled = crawl_result.pages_crawled
            session.jobs_found = len(jobs)
            session.jobs_saved = saved_jobs
            session.errors_count = len(crawl_result.errors)
            
            await self.db.commit()
            
            logger.info(f"保存爬取结果: {session_id}, 职位数: {saved_jobs}")
            
        except Exception as e:
            logger.error(f"保存爬取结果失败: {e}")
            await self.db.rollback()
            raise
    
    async def handle_crawl_failure(self, session_id: str, errors: List[str]) -> None:
        """处理爬取失败"""
        try:
            # 获取会话
            stmt = select(CrawlSession).where(CrawlSession.id == session_id)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                # 更新会话状态
                session.complete_session(success=False)
                session.errors_count = len(errors)
                
                # 记录错误日志
                for error in errors:
                    log = CrawlLog.create_error_log(
                        session_id=session_id,
                        message=error
                    )
                    self.db.add(log)
                
                await self.db.commit()
                
                logger.info(f"记录爬取失败: {session_id}")
            
        except Exception as e:
            logger.error(f"处理爬取失败异常: {e}")
            await self.db.rollback()
    
    async def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        try:
            stmt = select(CrawlSession).where(CrawlSession.id == session_id)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                return None
            
            # 获取最近的错误日志
            log_stmt = select(CrawlLog).where(
                CrawlLog.session_id == session_id,
                CrawlLog.log_level == "error"
            ).order_by(CrawlLog.timestamp.desc()).limit(5)
            
            log_result = await self.db.execute(log_stmt)
            error_logs = log_result.scalars().all()
            
            return {
                "status": session.status.value,
                "progress": {
                    "pages_crawled": session.pages_crawled,
                    "jobs_found": session.jobs_found,
                    "jobs_saved": session.jobs_saved,
                    "errors_count": session.errors_count,
                    "success_rate": session.calculate_success_rate()
                },
                "errors": [log.message for log in error_logs],
                "estimated_remaining": session.estimate_remaining_time()
            }
            
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}")
            return None
    
    async def cancel_session(self, session_id: str) -> None:
        """取消会话"""
        try:
            stmt = select(CrawlSession).where(CrawlSession.id == session_id)
            result = await self.db.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                session.cancel_session()
                await self.db.commit()
                
                logger.info(f"取消会话: {session_id}")
        
        except Exception as e:
            logger.error(f"取消会话失败: {e}")
            await self.db.rollback()
    
    async def list_sessions(self, limit: int = 20, offset: int = 0,
                          status: Optional[str] = None) -> Dict[str, Any]:
        """获取会话列表"""
        try:
            # 构建查询
            stmt = select(CrawlSession)
            
            if status:
                stmt = stmt.where(CrawlSession.status == status)
            
            # 获取总数
            count_stmt = select(func.count(CrawlSession.id))
            if status:
                count_stmt = count_stmt.where(CrawlSession.status == status)
            
            count_result = await self.db.execute(count_stmt)
            total = count_result.scalar()
            
            # 获取分页数据
            stmt = stmt.order_by(CrawlSession.created_at.desc()).offset(offset).limit(limit)
            result = await self.db.execute(stmt)
            sessions = result.scalars().all()
            
            session_list = []
            for session in sessions:
                session_data = session.generate_report()
                session_list.append(session_data)
            
            return {
                "sessions": session_list,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"获取会话列表失败: {e}")
            return {"sessions": [], "total": 0}
    
    async def export_session_data(self, session_id: str, format: str) -> Dict[str, Any]:
        """导出会话数据"""
        try:
            # 获取会话数据
            stmt = select(Job).where(Job.crawl_session_id == session_id)
            result = await self.db.execute(stmt)
            jobs = result.scalars().all()
            
            if not jobs:
                return {"success": False, "error": "没有数据可导出"}
            
            # 转换为导出格式
            export_data = [job.to_export_dict() for job in jobs]
            
            # 创建导出文件
            export_dir = settings.export_dir
            os.makedirs(export_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs_{session_id}_{timestamp}.{format}"
            file_path = os.path.join(export_dir, filename)
            
            if format == "json":
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            elif format == "csv":
                df = pd.DataFrame(export_data)
                df.to_csv(file_path, index=False, encoding='utf-8')
            
            elif format == "excel":
                df = pd.DataFrame(export_data)
                df.to_excel(file_path, index=False, engine='openpyxl')
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            return {
                "success": True,
                "export_url": f"/exports/{filename}",
                "file_size": file_size,
                "record_count": len(export_data)
            }
            
        except Exception as e:
            logger.error(f"导出数据失败: {e}")
            return {"success": False, "error": str(e)}
    
    async def _get_or_create_site(self, url: str) -> JobSite:
        """获取或创建网站记录"""
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
                site_type="招聘网站"
            )
            
            self.db.add(site)
            await self.db.flush()
        
        return site
    
    async def _get_or_create_selector_config(self, site_id: str,
                                           selectors: Dict[str, str]) -> SelectorConfig:
        """获取或创建选择器配置"""
        # 查询是否已有相同的选择器配置
        stmt = select(SelectorConfig).where(
            SelectorConfig.site_id == site_id,
            SelectorConfig.is_active == True
        ).order_by(SelectorConfig.created_at.desc())
        
        result = await self.db.execute(stmt)
        existing_config = result.scalar_one_or_none()
        
        # 如果存在且选择器相同，直接使用
        if existing_config and existing_config.selectors_dict == selectors:
            return existing_config
        
        # 创建新的选择器配置
        config = SelectorConfig(
            site_id=site_id,
            version="1.0.0",
            selectors=selectors,
            confidence_score=0.8,  # 默认置信度
            validation_status="pending"
        )
        
        self.db.add(config)
        await self.db.flush()
        
        return config
    
    def _generate_site_name(self, domain: str) -> str:
        """生成网站名称"""
        domain_mappings = {
            'zhaopin.com': '智联招聘',
            '51job.com': '前程无忧',
            'zhipin.com': 'BOSS直聘',
            'liepin.com': '猎聘网',
            'lagou.com': '拉勾网'
        }
        
        return domain_mappings.get(domain, domain.replace('www.', '').title())
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        try:
            # 常见日期格式
            formats = [
                "%Y-%m-%d",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt)
                except ValueError:
                    continue
            
            # 如果都失败了，返回None
            return None
            
        except Exception:
            return None


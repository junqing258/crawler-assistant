"""爬虫任务端点"""

import uuid
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.api.schemas import (
    StartCrawlingRequest, StartCrawlingResponse,
    CrawlStatusResponse, CrawlResultResponse, ErrorResponse
)
from app.services.crawling_service import CrawlingService
from app.core.browser.browser_controller import BrowserController
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储活动的爬虫会话
active_sessions: Dict[str, Dict[str, Any]] = {}


@router.post("/start", response_model=StartCrawlingResponse)
async def start_crawling(
    request: StartCrawlingRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """启动爬虫任务"""
    
    session_id = str(uuid.uuid4())
    
    try:
        logger.info(f"启动爬虫任务: {request.url}")
        
        # 创建爬虫服务
        crawling_service = CrawlingService(db)
        
        # 创建爬虫会话记录
        session = await crawling_service.create_crawl_session(
            url=str(request.url),
            selectors=request.selectors.dict(),
            options=request.options.dict(),
            session_id=session_id
        )
        
        # 添加到活动会话
        active_sessions[session_id] = {
            "status": "starting",
            "session": session,
            "start_time": asyncio.get_event_loop().time()
        }
        
        # 后台执行爬虫任务
        background_tasks.add_task(
            execute_crawling_task,
            session_id,
            str(request.url),
            request.selectors.dict(),
            request.options.dict(),
            db
        )
        
        return StartCrawlingResponse(
            session_id=session_id,
            status="started",
            estimated_duration=request.options.max_pages * 5,  # 估算每页5秒
            message="爬虫任务已启动"
        )
        
    except Exception as e:
        logger.error(f"启动爬虫任务失败: {e}", exc_info=True)
        
        # 清理失败的会话
        if session_id in active_sessions:
            del active_sessions[session_id]
        
        raise HTTPException(
            status_code=500,
            detail=f"启动爬虫任务失败: {str(e)}"
        )


@router.get("/status/{session_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """获取爬虫任务状态"""
    
    try:
        # 检查活动会话
        if session_id not in active_sessions:
            # 从数据库查询历史会话
            crawling_service = CrawlingService(db)
            session_data = await crawling_service.get_session_status(session_id)
            
            if not session_data:
                raise HTTPException(
                    status_code=404,
                    detail=f"会话未找到: {session_id}"
                )
            
            return CrawlStatusResponse(
                session_id=session_id,
                status=session_data["status"],
                progress=session_data["progress"],
                summary=session_data.get("summary"),
                export_url=session_data.get("export_url"),
                errors=session_data.get("errors", []),
                estimated_remaining=session_data.get("estimated_remaining"),
                message="状态查询完成"
            )
        
        # 活动会话状态
        session_info = active_sessions[session_id]
        
        # 计算预估剩余时间
        elapsed = asyncio.get_event_loop().time() - session_info["start_time"]
        estimated_remaining = max(0, session_info.get("estimated_duration", 0) - elapsed)
        
        return CrawlStatusResponse(
            session_id=session_id,
            status=session_info["status"],
            progress=session_info.get("progress", {
                "pages_crawled": 0,
                "jobs_found": 0,
                "jobs_saved": 0,
                "current_page_url": None,
                "errors_count": 0,
                "success_rate": 0.0
            }),
            summary=session_info.get("summary"),
            export_url=session_info.get("export_url"),
            errors=session_info.get("errors", []),
            estimated_remaining=int(estimated_remaining),
            message="状态查询完成"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询爬虫状态失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询状态失败: {str(e)}"
        )


@router.post("/stop/{session_id}")
async def stop_crawling(
    session_id: str,
    db: AsyncSession = Depends(get_async_db)
):
    """停止爬虫任务"""
    
    try:
        if session_id in active_sessions:
            # 标记会话为取消状态
            active_sessions[session_id]["status"] = "cancelling"
            
            # 更新数据库记录
            crawling_service = CrawlingService(db)
            await crawling_service.cancel_session(session_id)
            
            return {
                "success": True,
                "message": f"爬虫任务已停止: {session_id}"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"活动会话未找到: {session_id}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止爬虫任务失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"停止任务失败: {str(e)}"
        )


@router.get("/sessions")
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db)
):
    """获取爬虫会话列表"""
    
    try:
        crawling_service = CrawlingService(db)
        sessions = await crawling_service.list_sessions(
            limit=limit,
            offset=offset,
            status=status
        )
        
        return {
            "success": True,
            "sessions": sessions["sessions"],
            "total": sessions["total"],
            "limit": limit,
            "offset": offset,
            "message": "会话列表查询完成"
        }
        
    except Exception as e:
        logger.error(f"查询会话列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询会话列表失败: {str(e)}"
        )


@router.get("/export/{session_id}")
async def export_results(
    session_id: str,
    format: str = "json",
    db: AsyncSession = Depends(get_async_db)
):
    """导出爬取结果"""
    
    try:
        if format not in ["json", "csv", "excel"]:
            raise HTTPException(
                status_code=400,
                detail="不支持的导出格式，支持: json, csv, excel"
            )
        
        crawling_service = CrawlingService(db)
        export_result = await crawling_service.export_session_data(
            session_id=session_id,
            format=format
        )
        
        if not export_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=export_result["error"]
            )
        
        return {
            "success": True,
            "export_url": export_result["export_url"],
            "file_size": export_result["file_size"],
            "record_count": export_result["record_count"],
            "message": "数据导出完成"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出结果失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"导出失败: {str(e)}"
        )


async def execute_crawling_task(
    session_id: str,
    url: str,
    selectors: Dict[str, str],
    options: Dict[str, Any],
    db: AsyncSession
):
    """执行爬虫任务（后台任务）"""
    
    try:
        logger.info(f"开始执行爬虫任务: {session_id}")
        
        # 更新会话状态
        if session_id in active_sessions:
            active_sessions[session_id]["status"] = "running"
        
        # 创建浏览器控制器
        browser_controller = BrowserController()
        
        try:
            # 初始化浏览器
            if not await browser_controller.initialize(session_id):
                raise Exception("浏览器初始化失败")
            
            # 执行爬取
            crawl_result = await browser_controller.crawl_jobs(
                url=url,
                selectors=selectors,
                max_pages=options.get("max_pages", 10)
            )
            
            # 创建爬虫服务处理结果
            crawling_service = CrawlingService(db)
            
            if crawl_result.success:
                # 保存爬取结果
                await crawling_service.save_crawl_results(
                    session_id=session_id,
                    jobs=crawl_result.jobs,
                    crawl_result=crawl_result
                )
                
                # 更新会话状态
                if session_id in active_sessions:
                    active_sessions[session_id].update({
                        "status": "completed",
                        "progress": {
                            "pages_crawled": crawl_result.pages_crawled,
                            "jobs_found": len(crawl_result.jobs),
                            "jobs_saved": len(crawl_result.jobs),
                            "errors_count": len(crawl_result.errors),
                            "success_rate": 1.0 if crawl_result.success else 0.0
                        }
                    })
                
                logger.info(f"爬虫任务完成: {session_id}, 获取 {len(crawl_result.jobs)} 个职位")
            else:
                # 处理失败情况
                await crawling_service.handle_crawl_failure(
                    session_id=session_id,
                    errors=crawl_result.errors
                )
                
                if session_id in active_sessions:
                    active_sessions[session_id].update({
                        "status": "failed",
                        "errors": crawl_result.errors
                    })
                
                logger.error(f"爬虫任务失败: {session_id}, 错误: {crawl_result.errors}")
        
        finally:
            # 清理浏览器资源
            await browser_controller.cleanup()
    
    except Exception as e:
        logger.error(f"执行爬虫任务异常: {e}", exc_info=True)
        
        # 更新失败状态
        if session_id in active_sessions:
            active_sessions[session_id].update({
                "status": "failed",
                "errors": [str(e)]
            })
        
        # 在数据库中记录失败
        try:
            crawling_service = CrawlingService(db)
            await crawling_service.handle_crawl_failure(
                session_id=session_id,
                errors=[str(e)]
            )
        except Exception as db_error:
            logger.error(f"记录爬虫失败状态时出错: {db_error}")
    
    finally:
        # 从活动会话中移除（延迟移除，给状态查询一些时间）
        await asyncio.sleep(300)  # 5分钟后移除
        if session_id in active_sessions:
            del active_sessions[session_id]


"""页面分析端点"""

import time
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.api.schemas import (
    AnalyzeUrlRequest, AnalysisResponse, TestSelectorsRequest, 
    TestSelectorsResponse, ErrorResponse
)
from app.core.ai.page_analyzer import PageAnalyzer
from app.core.ai.selector_generator import SelectorGenerator
from app.core.browser.browser_controller import BrowserController
from app.models.ai_analysis import AIAnalysisResult
from app.models.job_site import JobSite
from app.models.selector_config import SelectorConfig
from app.services.analysis_service import AnalysisService
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/analyze-url", response_model=AnalysisResponse)
async def analyze_url(
    request: AnalyzeUrlRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db)
):
    """分析URL并生成选择器配置"""
    
    start_time = time.time()
    session_id = str(uuid.uuid4())
    
    try:
        logger.info(f"开始分析URL: {request.url}")
        
        # 创建分析服务
        analysis_service = AnalysisService(db)
        
        # 执行页面分析
        result = await analysis_service.analyze_page(
            url=str(request.url),
            options=request.options,
            session_id=session_id
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"页面分析失败: {result['error']}"
            )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # 构建响应
        response = AnalysisResponse(
            selectors=result["selectors"],
            confidence_score=result["confidence_score"],
            validation_details=result["validation_details"],
            suggestions=result["suggestions"],
            processing_time_ms=processing_time,
            message="页面分析完成"
        )
        
        # 后台保存分析结果
        background_tasks.add_task(
            analysis_service.save_analysis_result,
            result["analysis_data"],
            session_id
        )
        
        logger.info(f"URL分析完成: {request.url}, 耗时: {processing_time}ms")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"URL分析异常: {e}", exc_info=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"分析过程发生异常: {str(e)}"
        )


@router.post("/test-selectors", response_model=TestSelectorsResponse)
async def test_selectors(request: TestSelectorsRequest):
    """测试选择器有效性"""
    
    try:
        logger.info(f"开始测试选择器: {request.url}")
        
        # 创建浏览器控制器
        session_id = str(uuid.uuid4())
        browser_controller = BrowserController()
        
        try:
            # 初始化浏览器
            if not await browser_controller.initialize(session_id):
                raise HTTPException(
                    status_code=500,
                    detail="浏览器初始化失败"
                )
            
            # 测试选择器
            test_result = await browser_controller.test_selectors(
                url=str(request.url),
                selectors=request.selectors.dict()
            )
            
            if not test_result["success"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"选择器测试失败: {test_result['error']}"
                )
            
            # 生成优化建议
            suggestions = []
            for key, result in test_result["results"].items():
                if not result["valid"]:
                    suggestions.append(f"{key}选择器无效，未找到匹配元素")
                elif result["count"] > 100:
                    suggestions.append(f"{key}选择器匹配元素过多({result['count']}个)，建议增加限定条件")
                elif result["count"] == 0:
                    suggestions.append(f"{key}选择器未匹配任何元素，需要调整")
            
            response = TestSelectorsResponse(
                overall_score=test_result["overall_score"],
                results={
                    key: {
                        "selector": result["selector"],
                        "valid": result["valid"],
                        "count": result["count"],
                        "sample_text": result.get("sample_text", ""),
                        "error": result.get("error")
                    }
                    for key, result in test_result["results"].items()
                },
                page_url=str(request.url),
                suggestions=suggestions,
                message="选择器测试完成"
            )
            
            logger.info(f"选择器测试完成: {request.url}")
            return response
            
        finally:
            # 清理浏览器资源
            await browser_controller.cleanup()
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"选择器测试异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"测试过程发生异常: {str(e)}"
        )


@router.get("/history")
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_async_db)
):
    """获取分析历史"""
    
    try:
        # 这里应该从数据库查询历史记录
        # 暂时返回示例数据
        return {
            "success": True,
            "data": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "message": "历史记录查询完成"
        }
        
    except Exception as e:
        logger.error(f"查询分析历史异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询历史记录失败: {str(e)}"
        )


@router.get("/sites")
async def get_supported_sites(db: AsyncSession = Depends(get_async_db)):
    """获取支持的网站列表"""
    
    try:
        # 从数据库查询已配置的网站
        # 暂时返回示例数据
        supported_sites = [
            {
                "name": "智联招聘",
                "domain": "zhaopin.com",
                "status": "supported",
                "confidence": 0.95
            },
            {
                "name": "前程无忧",
                "domain": "51job.com", 
                "status": "supported",
                "confidence": 0.92
            },
            {
                "name": "BOSS直聘",
                "domain": "zhipin.com",
                "status": "supported", 
                "confidence": 0.90
            }
        ]
        
        return {
            "success": True,
            "sites": supported_sites,
            "total": len(supported_sites),
            "message": "支持网站列表查询完成"
        }
        
    except Exception as e:
        logger.error(f"查询支持网站异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询支持网站失败: {str(e)}"
        )


@router.get("/selector-templates")
async def get_selector_templates():
    """获取选择器模板"""
    
    try:
        templates = {
            "智联招聘": {
                "domain": "zhaopin.com",
                "selectors": {
                    "jobList": ".positionlist",
                    "jobItem": ".position-card",
                    "jobTitle": ".position-title a",
                    "jobLink": ".position-title a",
                    "companyName": ".company-name",
                    "publishedAt": ".publish-time",
                    "location": ".position-location",
                    "jobDescription": ".position-summary",
                    "nextPage": ".pager-next"
                }
            },
            "前程无忧": {
                "domain": "51job.com",
                "selectors": {
                    "jobList": ".j_joblist",
                    "jobItem": ".j_joblist_item",
                    "jobTitle": ".job-title a",
                    "jobLink": ".job-title a",
                    "companyName": ".comp-name",
                    "publishedAt": ".job-time",
                    "location": ".job-area",
                    "jobDescription": ".job-desc",
                    "nextPage": ".next"
                }
            }
        }
        
        return {
            "success": True,
            "templates": templates,
            "message": "选择器模板查询完成"
        }
        
    except Exception as e:
        logger.error(f"查询选择器模板异常: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"查询选择器模板失败: {str(e)}"
        )


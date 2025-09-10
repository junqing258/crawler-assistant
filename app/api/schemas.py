"""API数据模式定义"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, validator


# 基础响应模式
class BaseResponse(BaseModel):
    """基础响应模式"""
    success: bool
    message: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseResponse):
    """错误响应模式"""
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# 页面分析相关模式
class AnalyzeUrlRequest(BaseModel):
    """分析URL请求"""
    url: HttpUrl = Field(..., description="要分析的招聘页面URL")
    options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="分析选项")
    
    @validator('url')
    def validate_url(cls, v):
        """验证URL格式"""
        url_str = str(v)
        if not any(domain in url_str for domain in ['job', 'career', 'work', 'recruit', 'zhipin', 'liepin']):
            # 这里只是提醒，不强制限制
            pass
        return v


class SelectorConfig(BaseModel):
    """选择器配置"""
    jobList: str = Field(..., description="职位列表容器选择器")
    jobItem: str = Field(..., description="单个职位项选择器")
    jobTitle: str = Field(..., description="职位标题选择器")
    jobLink: str = Field(..., description="职位链接选择器")
    companyName: str = Field(..., description="公司名称选择器")
    publishedAt: str = Field(..., description="发布时间选择器")
    location: str = Field(..., description="工作地点选择器")
    jobDescription: str = Field(..., description="职位描述选择器")
    nextPage: Optional[str] = Field(None, description="下一页选择器")


class AnalysisResponse(BaseResponse):
    """分析响应"""
    success: bool = True
    selectors: SelectorConfig
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="置信度评分")
    validation_details: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    processing_time_ms: int = Field(..., description="处理时间(毫秒)")


# 爬虫任务相关模式
class CrawlOptions(BaseModel):
    """爬虫选项"""
    max_pages: int = Field(10, ge=1, le=100, description="最大爬取页数")
    delay_between_pages: float = Field(2.0, ge=0.5, le=10.0, description="页面间延迟(秒)")
    export_format: str = Field("json", pattern="^(json|csv|excel)$", description="导出格式")
    data_filters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="数据过滤器")
    enable_screenshots: bool = Field(False, description="是否启用截图")
    quality_threshold: float = Field(0.7, ge=0.0, le=1.0, description="数据质量阈值")


class StartCrawlingRequest(BaseModel):
    """开始爬取请求"""
    url: HttpUrl = Field(..., description="起始URL")
    selectors: SelectorConfig = Field(..., description="选择器配置")
    options: CrawlOptions = Field(default_factory=CrawlOptions, description="爬取选项")


class JobData(BaseModel):
    """职位数据"""
    id: Optional[str] = None
    title: str = Field(..., description="职位标题")
    company: str = Field(..., description="公司名称")
    location: Optional[str] = Field(None, description="工作地点")
    description: Optional[str] = Field(None, description="职位描述")
    job_link: Optional[str] = Field(None, description="职位链接")
    published_at: Optional[str] = Field(None, description="发布时间")
    salary_range: Optional[str] = Field(None, description="薪资范围")
    job_type: Optional[str] = Field(None, description="工作类型")
    experience_level: Optional[str] = Field(None, description="经验要求")
    skills: List[str] = Field(default_factory=list, description="技能要求")
    remote_option: bool = Field(False, description="是否支持远程")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="数据质量评分")
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class CrawlProgress(BaseModel):
    """爬取进度"""
    pages_crawled: int = Field(0, description="已爬取页数")
    jobs_found: int = Field(0, description="发现的职位数")
    jobs_saved: int = Field(0, description="保存的职位数")
    current_page_url: Optional[str] = Field(None, description="当前页面URL")
    errors_count: int = Field(0, description="错误次数")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="成功率")


class CrawlSummary(BaseModel):
    """爬取摘要"""
    companies: List[str] = Field(default_factory=list, description="公司列表")
    locations: List[str] = Field(default_factory=list, description="地点列表")
    job_types: List[str] = Field(default_factory=list, description="工作类型列表")
    skill_tags: List[str] = Field(default_factory=list, description="技能标签")
    salary_ranges: List[str] = Field(default_factory=list, description="薪资范围")


class StartCrawlingResponse(BaseResponse):
    """开始爬取响应"""
    success: bool = True
    session_id: str = Field(..., description="会话ID")
    status: str = Field("started", description="任务状态")
    estimated_duration: Optional[int] = Field(None, description="预估持续时间(秒)")


class CrawlStatusResponse(BaseResponse):
    """爬取状态响应"""
    success: bool = True
    session_id: str = Field(..., description="会话ID")
    status: str = Field(..., description="任务状态")
    progress: CrawlProgress = Field(..., description="进度信息")
    summary: Optional[CrawlSummary] = Field(None, description="爬取摘要")
    export_url: Optional[str] = Field(None, description="导出文件URL")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    estimated_remaining: Optional[int] = Field(None, description="预估剩余时间(秒)")


class CrawlResultResponse(BaseResponse):
    """爬取结果响应"""
    success: bool = True
    session_id: str = Field(..., description="会话ID")
    total_jobs: int = Field(..., description="总职位数")
    pages_crawled: int = Field(..., description="已爬取页数")
    processing_time: float = Field(..., description="处理时间(秒)")
    export_urls: Dict[str, str] = Field(default_factory=dict, description="导出文件URLs")
    summary: CrawlSummary = Field(..., description="爬取摘要")
    data_quality: Dict[str, Any] = Field(default_factory=dict, description="数据质量报告")


# 测试相关模式
class TestSelectorsRequest(BaseModel):
    """测试选择器请求"""
    url: HttpUrl = Field(..., description="测试页面URL")
    selectors: SelectorConfig = Field(..., description="选择器配置")


class SelectorTestResult(BaseModel):
    """选择器测试结果"""
    selector: str = Field(..., description="选择器")
    valid: bool = Field(..., description="是否有效")
    count: int = Field(..., description="匹配元素数量")
    sample_text: str = Field("", description="示例文本")
    error: Optional[str] = Field(None, description="错误信息")


class TestSelectorsResponse(BaseResponse):
    """测试选择器响应"""
    success: bool = True
    overall_score: float = Field(..., ge=0.0, le=1.0, description="整体评分")
    results: Dict[str, SelectorTestResult] = Field(..., description="测试结果")
    page_url: str = Field(..., description="测试页面URL")
    suggestions: List[str] = Field(default_factory=list, description="优化建议")


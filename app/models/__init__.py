"""数据模型模块"""

from .base import Base
from .job_site import JobSite
from .selector_config import SelectorConfig
from .job import Job
from .crawl_session import CrawlSession
from .crawl_log import CrawlLog
from .ai_analysis import AIAnalysisResult

__all__ = [
    "Base",
    "JobSite",
    "SelectorConfig", 
    "Job",
    "CrawlSession",
    "CrawlLog",
    "AIAnalysisResult"
]


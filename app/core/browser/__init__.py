"""Browser-use集成模块"""

from .browser_controller import BrowserController
from .crawler_agent import CrawlerAgent  
from .anti_detection import AntiDetectionManager

__all__ = [
    "BrowserController",
    "CrawlerAgent",
    "AntiDetectionManager"
]


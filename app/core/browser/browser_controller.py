"""Browser控制器"""

import asyncio
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from pathlib import Path

from browser_use import Agent, Browser, BrowserConfig
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

from app.config import settings, BrowserConfig as AppBrowserConfig
from app.core.browser.anti_detection import AntiDetectionManager
from app.core.browser.crawler_agent import CrawlerAgent
import logging

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """爬取结果"""
    success: bool
    jobs: List[Dict[str, Any]]
    pages_crawled: int
    total_pages: Optional[int]
    errors: List[str]
    next_page_url: Optional[str]
    has_next_page: bool
    processing_time: float


@dataclass
class PageLoadResult:
    """页面加载结果"""
    success: bool
    html_content: str
    screenshot_path: Optional[str]
    url: str
    load_time: float
    error_message: Optional[str] = None


class BrowserController:
    """Browser控制器"""
    
    def __init__(self):
        self.browser_config = AppBrowserConfig()
        self.anti_detection = AntiDetectionManager()
        self.browser: Optional[Browser] = None
        self.current_page: Optional[Page] = None
        self.session_id: Optional[str] = None
        
    async def initialize(self, session_id: str) -> bool:
        """初始化浏览器"""
        try:
            self.session_id = session_id
            
            # 创建browser-use配置
            config = BrowserConfig(
                headless=self.browser_config.headless,
                chrome_instance_path=None,
                disable_security=True,
                extra_chromium_args=self.browser_config.get_launch_options()["args"]
            )
            
            # 创建浏览器实例
            self.browser = Browser(config=config)
            
            logger.info(f"浏览器初始化成功 - Session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            return False
    
    async def load_page(self, url: str, wait_for_load: bool = True, 
                       take_screenshot: bool = False) -> PageLoadResult:
        """加载页面"""
        start_time = time.time()
        
        try:
            if not self.browser:
                raise Exception("浏览器未初始化")
            
            # 创建新页面
            page = await self.browser.new_page()
            self.current_page = page
            
            # 应用反检测措施
            await self.anti_detection.apply_stealth_measures(page)
            
            # 导航到URL
            logger.info(f"正在加载页面: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面加载完成
            if wait_for_load:
                await self._wait_for_page_load(page)
            
            # 模拟人类行为
            await self.anti_detection.simulate_human_behavior(page)
            
            # 获取页面内容
            html_content = await page.content()
            
            # 截图（如果需要）
            screenshot_path = None
            if take_screenshot:
                screenshot_path = await self._take_screenshot(page, url)
            
            load_time = time.time() - start_time
            
            logger.info(f"页面加载成功: {url}, 耗时: {load_time:.2f}s")
            
            return PageLoadResult(
                success=True,
                html_content=html_content,
                screenshot_path=screenshot_path,
                url=url,
                load_time=load_time
            )
            
        except Exception as e:
            load_time = time.time() - start_time
            error_msg = f"页面加载失败: {str(e)}"
            logger.error(error_msg)
            
            return PageLoadResult(
                success=False,
                html_content="",
                screenshot_path=None,
                url=url,
                load_time=load_time,
                error_message=error_msg
            )
    
    async def crawl_jobs(self, url: str, selectors: Dict[str, str], 
                        max_pages: int = 10) -> CrawlResult:
        """爬取职位信息"""
        start_time = time.time()
        all_jobs = []
        pages_crawled = 0
        errors = []
        current_url = url
        
        try:
            # 创建爬虫代理
            crawler_agent = CrawlerAgent(self.browser)
            
            while pages_crawled < max_pages and current_url:
                try:
                    logger.info(f"开始爬取第 {pages_crawled + 1} 页: {current_url}")
                    
                    # 导航到当前页面
                    page_result = await self.load_page(current_url, wait_for_load=True)
                    
                    if not page_result.success:
                        errors.append(f"页面 {pages_crawled + 1} 加载失败: {page_result.error_message}")
                        break
                    
                    # 提取职位数据
                    extraction_result = await crawler_agent.extract_jobs(
                        self.current_page, selectors
                    )
                    
                    if extraction_result["success"]:
                        jobs = extraction_result["jobs"]
                        all_jobs.extend(jobs)
                        pages_crawled += 1
                        
                        logger.info(f"第 {pages_crawled} 页提取到 {len(jobs)} 个职位")
                        
                        # 检查是否有下一页
                        next_page_result = await crawler_agent.find_next_page(
                            self.current_page, selectors.get("nextPage", "")
                        )
                        
                        if next_page_result["has_next"]:
                            current_url = next_page_result["next_url"]
                            # 随机延迟
                            delay = random.uniform(
                                settings.request_delay_min, 
                                settings.request_delay_max
                            )
                            await asyncio.sleep(delay)
                        else:
                            logger.info("没有更多页面，爬取完成")
                            break
                    else:
                        error_msg = f"第 {pages_crawled + 1} 页数据提取失败: {extraction_result.get('error', '未知错误')}"
                        errors.append(error_msg)
                        logger.error(error_msg)
                        break
                        
                except Exception as e:
                    error_msg = f"第 {pages_crawled + 1} 页处理异常: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    break
            
            processing_time = time.time() - start_time
            
            return CrawlResult(
                success=len(all_jobs) > 0,
                jobs=all_jobs,
                pages_crawled=pages_crawled,
                total_pages=None,  # 无法预知总页数
                errors=errors,
                next_page_url=current_url if pages_crawled < max_pages else None,
                has_next_page=current_url is not None and pages_crawled < max_pages,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"爬取过程发生异常: {str(e)}"
            logger.error(error_msg)
            
            return CrawlResult(
                success=False,
                jobs=all_jobs,
                pages_crawled=pages_crawled,
                total_pages=None,
                errors=errors + [error_msg],
                next_page_url=None,
                has_next_page=False,
                processing_time=processing_time
            )
    
    async def _wait_for_page_load(self, page: Page) -> None:
        """等待页面加载完成"""
        try:
            # 等待网络空闲
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # 等待常见的加载指示器消失
            loading_selectors = [
                ".loading", ".spinner", ".loader", "[data-loading]",
                ".loading-indicator", ".progress", ".skeleton"
            ]
            
            for selector in loading_selectors:
                try:
                    await page.wait_for_selector(
                        selector, 
                        state="hidden", 
                        timeout=5000
                    )
                except PlaywrightTimeoutError:
                    continue  # 如果没有这个加载器，继续下一个
            
            # 额外等待时间确保动态内容加载
            await asyncio.sleep(2)
            
        except PlaywrightTimeoutError:
            logger.warning("页面加载等待超时，继续执行")
        except Exception as e:
            logger.warning(f"页面加载等待异常: {e}")
    
    async def _take_screenshot(self, page: Page, url: str) -> str:
        """截取页面截图"""
        try:
            # 创建截图目录
            screenshot_dir = Path(settings.screenshot_dir)
            screenshot_dir.mkdir(exist_ok=True)
            
            # 生成截图文件名
            timestamp = int(time.time())
            domain = url.split("//")[1].split("/")[0].replace(".", "_")
            filename = f"{domain}_{timestamp}.png"
            screenshot_path = screenshot_dir / filename
            
            # 截图
            await page.screenshot(
                path=str(screenshot_path),
                full_page=True,
                type="png"
            )
            
            return str(screenshot_path)
            
        except Exception as e:
            logger.error(f"截图失败: {e}")
            return None
    
    async def test_selectors(self, url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """测试选择器有效性"""
        try:
            # 加载页面
            page_result = await self.load_page(url, wait_for_load=True)
            
            if not page_result.success:
                return {
                    "success": False,
                    "error": page_result.error_message,
                    "results": {}
                }
            
            # 创建爬虫代理测试
            crawler_agent = CrawlerAgent(self.browser)
            
            # 测试每个选择器
            test_results = {}
            
            for key, selector in selectors.items():
                try:
                    elements = await self.current_page.query_selector_all(selector)
                    test_results[key] = {
                        "valid": len(elements) > 0,
                        "count": len(elements),
                        "selector": selector,
                        "sample_text": elements[0].inner_text()[:100] if elements else ""
                    }
                except Exception as e:
                    test_results[key] = {
                        "valid": False,
                        "count": 0,
                        "selector": selector,
                        "error": str(e)
                    }
            
            # 计算整体评分
            valid_count = sum(1 for result in test_results.values() if result["valid"])
            overall_score = valid_count / len(selectors) if selectors else 0
            
            return {
                "success": True,
                "overall_score": overall_score,
                "results": test_results,
                "page_url": url
            }
            
        except Exception as e:
            logger.error(f"选择器测试失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": {}
            }
    
    async def handle_anti_bot_challenge(self, page: Page) -> bool:
        """处理反爬虫挑战"""
        try:
            # 检测常见的反爬虫页面
            challenge_indicators = [
                "captcha", "robot", "verify", "protection",
                "cloudflare", "please wait", "checking browser"
            ]
            
            page_content = await page.content()
            page_text = page_content.lower()
            
            for indicator in challenge_indicators:
                if indicator in page_text:
                    logger.warning(f"检测到反爬虫挑战: {indicator}")
                    
                    # 尝试等待挑战完成
                    await asyncio.sleep(5)
                    
                    # 检查是否已经通过
                    new_content = await page.content()
                    if len(new_content) > len(page_content) * 1.5:
                        logger.info("反爬虫挑战可能已通过")
                        return True
                    
                    return False
            
            return True  # 没有检测到挑战
            
        except Exception as e:
            logger.error(f"反爬虫挑战处理失败: {e}")
            return False
    
    async def cleanup(self) -> None:
        """清理资源"""
        try:
            if self.current_page:
                await self.current_page.close()
                self.current_page = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            logger.info(f"浏览器会话清理完成 - Session: {self.session_id}")
            
        except Exception as e:
            logger.error(f"浏览器清理失败: {e}")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup()


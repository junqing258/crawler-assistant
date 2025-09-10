"""反检测管理器"""

import random
import asyncio
from typing import List, Dict, Any
from playwright.async_api import Page
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AntiDetectionManager:
    """反检测管理器"""
    
    def __init__(self):
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0"
        ]
        
        self.viewport_sizes = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
            {"width": 1440, "height": 900},
            {"width": 1600, "height": 900}
        ]
        
        self.behavior_patterns = [
            {"scroll_delay": (1, 3), "click_delay": (0.5, 1.5), "type_delay": (0.1, 0.3)},
            {"scroll_delay": (2, 4), "click_delay": (1, 2), "type_delay": (0.2, 0.4)},
            {"scroll_delay": (1.5, 2.5), "click_delay": (0.8, 1.8), "type_delay": (0.15, 0.35)}
        ]
        
        self.current_behavior = random.choice(self.behavior_patterns)
    
    async def apply_stealth_measures(self, page: Page) -> None:
        """应用隐身措施"""
        try:
            # 1. 设置随机User-Agent
            if settings.user_agent_rotation:
                user_agent = random.choice(self.user_agents)
                await page.set_extra_http_headers({
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                })
            
            # 2. 设置随机视口大小
            viewport = random.choice(self.viewport_sizes)
            await page.set_viewport_size(viewport)
            
            # 3. 移除webdriver标识
            await page.add_init_script("""
                // 移除webdriver属性
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // 修改plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // 修改languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['zh-CN', 'zh', 'en'],
                });
                
                // 修改platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'Win32',
                });
                
                // 修改chrome对象
                window.chrome = {
                    runtime: {},
                };
                
                // 修改权限查询
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Cypress.denied }) :
                        originalQuery(parameters)
                );
            """)
            
            # 4. 设置随机时区
            timezones = ['Asia/Shanghai', 'Asia/Beijing', 'Asia/Hong_Kong']
            timezone = random.choice(timezones)
            await page.emulate_timezone(timezone)
            
            # 5. 设置随机地理位置
            locations = [
                {"latitude": 39.9042, "longitude": 116.4074},  # 北京
                {"latitude": 31.2304, "longitude": 121.4737},  # 上海
                {"latitude": 22.3193, "longitude": 114.1694},  # 香港
            ]
            location = random.choice(locations)
            await page.set_geolocation(location)
            
            logger.debug("反检测措施应用完成")
            
        except Exception as e:
            logger.error(f"应用反检测措施失败: {e}")
    
    async def simulate_human_behavior(self, page: Page) -> None:
        """模拟人类浏览行为"""
        try:
            if not settings.human_behavior_simulation:
                return
            
            # 1. 随机滚动
            await self._random_scroll(page)
            
            # 2. 随机鼠标移动
            await self._random_mouse_movement(page)
            
            # 3. 随机停顿
            delay = random.uniform(*self.current_behavior["scroll_delay"])
            await asyncio.sleep(delay)
            
            logger.debug("人类行为模拟完成")
            
        except Exception as e:
            logger.error(f"人类行为模拟失败: {e}")
    
    async def _random_scroll(self, page: Page) -> None:
        """随机滚动页面"""
        try:
            # 获取页面高度
            page_height = await page.evaluate("document.body.scrollHeight")
            viewport_height = await page.evaluate("window.innerHeight")
            
            if page_height <= viewport_height:
                return  # 页面太短，不需要滚动
            
            # 随机滚动次数
            scroll_count = random.randint(2, 5)
            
            for _ in range(scroll_count):
                # 随机滚动距离（页面高度的10%-30%）
                scroll_distance = random.randint(
                    int(page_height * 0.1),
                    int(page_height * 0.3)
                )
                
                # 平滑滚动
                await page.evaluate(f"""
                    window.scrollBy({{
                        top: {scroll_distance},
                        behavior: 'smooth'
                    }});
                """)
                
                # 滚动间隔
                delay = random.uniform(0.5, 2.0)
                await asyncio.sleep(delay)
            
            # 滚动回顶部
            await page.evaluate("window.scrollTo({top: 0, behavior: 'smooth'})")
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.warning(f"随机滚动失败: {e}")
    
    async def _random_mouse_movement(self, page: Page) -> None:
        """随机鼠标移动"""
        try:
            # 获取视口尺寸
            viewport = page.viewport_size
            if not viewport:
                return
            
            # 随机移动次数
            move_count = random.randint(2, 4)
            
            for _ in range(move_count):
                # 随机坐标
                x = random.randint(100, viewport["width"] - 100)
                y = random.randint(100, viewport["height"] - 100)
                
                # 移动鼠标
                await page.mouse.move(x, y)
                
                # 随机停顿
                delay = random.uniform(0.3, 0.8)
                await asyncio.sleep(delay)
        
        except Exception as e:
            logger.warning(f"随机鼠标移动失败: {e}")
    
    async def smart_click(self, page: Page, selector: str) -> bool:
        """智能点击（带人类行为模拟）"""
        try:
            # 等待元素可见
            await page.wait_for_selector(selector, state="visible", timeout=10000)
            
            # 滚动到元素位置
            await page.hover(selector)
            
            # 随机延迟
            delay = random.uniform(*self.current_behavior["click_delay"])
            await asyncio.sleep(delay)
            
            # 点击
            await page.click(selector)
            
            # 点击后延迟
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            return True
            
        except Exception as e:
            logger.error(f"智能点击失败 {selector}: {e}")
            return False
    
    async def smart_type(self, page: Page, selector: str, text: str) -> bool:
        """智能输入（带人类行为模拟）"""
        try:
            # 点击输入框
            await page.click(selector)
            
            # 清空现有内容
            await page.fill(selector, "")
            
            # 模拟逐字符输入
            for char in text:
                await page.type(selector, char)
                delay = random.uniform(*self.current_behavior["type_delay"])
                await asyncio.sleep(delay)
            
            return True
            
        except Exception as e:
            logger.error(f"智能输入失败 {selector}: {e}")
            return False
    
    async def handle_popups(self, page: Page) -> None:
        """处理弹窗和模态框"""
        try:
            # 常见的弹窗选择器
            popup_selectors = [
                '[role="dialog"]',
                '.modal',
                '.popup',
                '.overlay',
                '[data-modal]',
                '.cookie-banner',
                '.notification',
                '.alert'
            ]
            
            for selector in popup_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        # 查找关闭按钮
                        close_selectors = [
                            f'{selector} .close',
                            f'{selector} [aria-label="close"]',
                            f'{selector} [aria-label="Close"]',
                            f'{selector} [aria-label="关闭"]',
                            f'{selector} .btn-close',
                            f'{selector} button[type="button"]'
                        ]
                        
                        for close_selector in close_selectors:
                            close_button = await page.query_selector(close_selector)
                            if close_button:
                                await self.smart_click(page, close_selector)
                                logger.info(f"关闭弹窗: {selector}")
                                break
                        
                        # 如果没有关闭按钮，尝试按ESC键
                        else:
                            await page.keyboard.press("Escape")
                            logger.info(f"使用ESC关闭弹窗: {selector}")
                        
                        await asyncio.sleep(1)  # 等待弹窗关闭
                        
                except Exception:
                    continue  # 继续检查下一个弹窗
            
        except Exception as e:
            logger.warning(f"处理弹窗失败: {e}")
    
    async def wait_for_stable_page(self, page: Page, timeout: int = 10000) -> bool:
        """等待页面稳定（没有新的网络请求）"""
        try:
            # 等待网络空闲
            await page.wait_for_load_state("networkidle", timeout=timeout)
            
            # 额外等待，确保动态内容加载完成
            await asyncio.sleep(2)
            
            return True
            
        except Exception as e:
            logger.warning(f"等待页面稳定超时: {e}")
            return False
    
    def update_behavior_pattern(self) -> None:
        """更新行为模式"""
        self.current_behavior = random.choice(self.behavior_patterns)
        logger.debug("行为模式已更新")
    
    async def detect_bot_detection(self, page: Page) -> Dict[str, Any]:
        """检测反爬虫机制"""
        detection_result = {
            "detected": False,
            "type": None,
            "confidence": 0.0,
            "indicators": []
        }
        
        try:
            page_content = await page.content()
            page_text = page_content.lower()
            
            # 检测常见的反爬虫指标
            bot_indicators = {
                "captcha": ["captcha", "recaptcha", "hcaptcha"],
                "cloudflare": ["cloudflare", "checking your browser", "ddos protection"],
                "rate_limit": ["too many requests", "rate limit", "slow down"],
                "access_denied": ["access denied", "forbidden", "blocked"],
                "human_verification": ["human verification", "verify you are human"]
            }
            
            detected_indicators = []
            
            for detection_type, keywords in bot_indicators.items():
                for keyword in keywords:
                    if keyword in page_text:
                        detected_indicators.append({
                            "type": detection_type,
                            "keyword": keyword
                        })
            
            if detected_indicators:
                detection_result.update({
                    "detected": True,
                    "type": detected_indicators[0]["type"],
                    "confidence": min(len(detected_indicators) * 0.3, 1.0),
                    "indicators": detected_indicators
                })
            
            return detection_result
            
        except Exception as e:
            logger.error(f"反爬虫检测失败: {e}")
            return detection_result


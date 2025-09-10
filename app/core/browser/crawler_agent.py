"""爬虫代理"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from playwright.async_api import Page
from browser_use import Agent, Browser
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class CrawlerAgent:
    """爬虫代理"""
    
    def __init__(self, browser: Browser):
        self.browser = browser
        
    async def extract_jobs(self, page: Page, selectors: Dict[str, str]) -> Dict[str, Any]:
        """提取职位信息"""
        try:
            logger.info("开始提取职位信息")
            
            # 等待页面加载完成
            await self._wait_for_content_load(page)
            
            # 检查职位列表是否存在
            job_list_selector = selectors.get("jobList", "")
            if not job_list_selector:
                return {"success": False, "error": "缺少职位列表选择器", "jobs": []}
            
            job_list_elements = await page.query_selector_all(job_list_selector)
            if not job_list_elements:
                return {"success": False, "error": f"未找到职位列表: {job_list_selector}", "jobs": []}
            
            # 提取职位项
            job_item_selector = selectors.get("jobItem", "")
            if not job_item_selector:
                return {"success": False, "error": "缺少职位项选择器", "jobs": []}
            
            # 在职位列表中查找职位项
            jobs = []
            for job_list in job_list_elements:
                job_items = await job_list.query_selector_all(job_item_selector)
                
                for job_item in job_items:
                    job_data = await self._extract_single_job(job_item, selectors, page)
                    if job_data:
                        jobs.append(job_data)
            
            logger.info(f"成功提取 {len(jobs)} 个职位")
            
            return {
                "success": True,
                "jobs": jobs,
                "count": len(jobs)
            }
            
        except Exception as e:
            logger.error(f"职位信息提取失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "jobs": []
            }
    
    async def _extract_single_job(self, job_element, selectors: Dict[str, str], page: Page) -> Optional[Dict[str, Any]]:
        """提取单个职位信息"""
        try:
            job_data = {}
            
            # 提取各个字段
            field_mapping = {
                "title": "jobTitle",
                "company": "companyName", 
                "location": "location",
                "published_at": "publishedAt",
                "description": "jobDescription",
                "link": "jobLink"
            }
            
            for field, selector_key in field_mapping.items():
                selector = selectors.get(selector_key, "")
                if selector:
                    value = await self._extract_field_value(job_element, selector, field, page)
                    job_data[field] = value
            
            # 验证必需字段
            if not job_data.get("title") and not job_data.get("company"):
                return None  # 跳过无效的职位项
            
            # 处理链接
            if job_data.get("link"):
                job_data["link"] = await self._normalize_url(job_data["link"], page.url)
            
            # 添加原始数据
            job_data["raw_html"] = await job_element.inner_html()
            
            return job_data
            
        except Exception as e:
            logger.warning(f"提取单个职位失败: {e}")
            return None
    
    async def _extract_field_value(self, job_element, selector: str, field_type: str, page: Page) -> str:
        """提取字段值"""
        try:
            # 在职位元素内查找
            element = await job_element.query_selector(selector)
            
            if not element:
                return ""
            
            # 根据字段类型提取内容
            if field_type == "link":
                # 提取href属性
                href = await element.get_attribute("href")
                return href or ""
            else:
                # 提取文本内容
                text = await element.inner_text()
                return text.strip() if text else ""
                
        except Exception as e:
            logger.warning(f"字段提取失败 {field_type}[{selector}]: {e}")
            return ""
    
    async def _normalize_url(self, url: str, base_url: str) -> str:
        """标准化URL"""
        try:
            if not url:
                return ""
            
            # 如果是完整URL，直接返回
            if url.startswith(("http://", "https://")):
                return url
            
            # 如果是相对URL，拼接基础URL
            return urljoin(base_url, url)
            
        except Exception as e:
            logger.warning(f"URL标准化失败: {e}")
            return url
    
    async def find_next_page(self, page: Page, next_page_selector: str) -> Dict[str, Any]:
        """查找下一页"""
        try:
            if not next_page_selector:
                return {"has_next": False, "next_url": None, "error": "缺少下一页选择器"}
            
            # 查找下一页元素
            next_elements = await page.query_selector_all(next_page_selector)
            
            if not next_elements:
                # 尝试常见的下一页选择器
                fallback_selectors = [
                    'a[aria-label*="next"]',
                    'a[aria-label*="下一页"]',
                    '.next:not(.disabled)',
                    '[data-page="next"]',
                    'a:has-text("Next")',
                    'a:has-text("下一页")',
                    'a:has-text(">")'
                ]
                
                for fallback in fallback_selectors:
                    next_elements = await page.query_selector_all(fallback)
                    if next_elements:
                        break
            
            if not next_elements:
                return {"has_next": False, "next_url": None, "error": "未找到下一页元素"}
            
            # 选择第一个可用的下一页元素
            next_element = None
            for element in next_elements:
                # 检查元素是否可点击（不是disabled状态）
                is_disabled = await element.get_attribute("disabled")
                class_attr = await element.get_attribute("class") or ""
                
                if not is_disabled and "disabled" not in class_attr.lower():
                    next_element = element
                    break
            
            if not next_element:
                return {"has_next": False, "next_url": None, "error": "下一页元素不可用"}
            
            # 获取下一页URL
            href = await next_element.get_attribute("href")
            
            if href:
                # 有href属性，直接获取URL
                next_url = await self._normalize_url(href, page.url)
                return {"has_next": True, "next_url": next_url}
            else:
                # 没有href，尝试点击触发导航
                try:
                    # 监听导航事件
                    navigation_promise = page.wait_for_navigation(timeout=10000)
                    
                    # 点击下一页
                    await next_element.click()
                    
                    # 等待导航完成
                    await navigation_promise
                    
                    return {"has_next": True, "next_url": page.url}
                    
                except Exception as e:
                    logger.warning(f"点击下一页失败: {e}")
                    return {"has_next": False, "next_url": None, "error": f"点击下一页失败: {e}"}
            
        except Exception as e:
            logger.error(f"查找下一页失败: {e}")
            return {"has_next": False, "next_url": None, "error": str(e)}
    
    async def _wait_for_content_load(self, page: Page) -> None:
        """等待内容加载完成"""
        try:
            # 等待网络空闲
            await page.wait_for_load_state("networkidle", timeout=15000)
            
            # 等待常见的加载指示器消失
            loading_selectors = [
                ".loading", ".spinner", ".loader", "[data-loading]",
                ".skeleton", ".placeholder", ".loading-indicator"
            ]
            
            for selector in loading_selectors:
                try:
                    await page.wait_for_selector(selector, state="hidden", timeout=3000)
                except:
                    continue
            
            # 额外等待，确保动态内容渲染
            await asyncio.sleep(1)
            
        except Exception as e:
            logger.warning(f"等待内容加载失败: {e}")
    
    async def validate_page_structure(self, page: Page, selectors: Dict[str, str]) -> Dict[str, Any]:
        """验证页面结构"""
        validation_result = {
            "valid": False,
            "selectors": {},
            "errors": []
        }
        
        try:
            required_selectors = ["jobList", "jobItem", "jobTitle"]
            
            for key in required_selectors:
                selector = selectors.get(key, "")
                if not selector:
                    validation_result["errors"].append(f"缺少必需选择器: {key}")
                    continue
                
                elements = await page.query_selector_all(selector)
                validation_result["selectors"][key] = {
                    "selector": selector,
                    "found": len(elements),
                    "valid": len(elements) > 0
                }
                
                if len(elements) == 0:
                    validation_result["errors"].append(f"选择器无效: {key}[{selector}]")
            
            # 检查职位项数量是否合理
            job_items = validation_result["selectors"].get("jobItem", {}).get("found", 0)
            if job_items == 0:
                validation_result["errors"].append("未找到任何职位项")
            elif job_items > 200:
                validation_result["errors"].append(f"职位项数量异常: {job_items}")
            
            validation_result["valid"] = len(validation_result["errors"]) == 0
            
            return validation_result
            
        except Exception as e:
            validation_result["errors"].append(f"验证过程出错: {e}")
            return validation_result
    
    async def extract_page_metadata(self, page: Page) -> Dict[str, Any]:
        """提取页面元数据"""
        try:
            metadata = {
                "url": page.url,
                "title": await page.title(),
                "meta_description": "",
                "total_links": 0,
                "total_images": 0,
                "page_size": 0
            }
            
            # 获取meta描述
            meta_desc = await page.query_selector('meta[name="description"]')
            if meta_desc:
                metadata["meta_description"] = await meta_desc.get_attribute("content") or ""
            
            # 统计链接和图片数量
            links = await page.query_selector_all("a")
            images = await page.query_selector_all("img")
            
            metadata["total_links"] = len(links)
            metadata["total_images"] = len(images)
            
            # 获取页面大小
            content = await page.content()
            metadata["page_size"] = len(content)
            
            return metadata
            
        except Exception as e:
            logger.warning(f"提取页面元数据失败: {e}")
            return {}


"""页面分析器"""

import base64
import json
import logging
import time
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Dict, Optional, Tuple

from bs4 import BeautifulSoup
from openai import AsyncOpenAI

from app.config import settings
from app.core.ai.prompt_templates import PromptTemplates

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """分析结果数据类"""
    html_content: str
    screenshot_base64: Optional[str]
    dom_tree: BeautifulSoup
    url: str
    processing_time_ms: int


@dataclass
class AIAnalysisResponse:
    """AI分析响应数据类"""
    confidence_score: float
    detected_elements: Dict[str, Any]
    recommended_selectors: Dict[str, str]
    analysis_notes: str
    processing_time_ms: int


class PageAnalyzer:
    """页面分析器"""

    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=settings.openai_api_key, base_url=settings.openai_base_url)
        self.model = settings.openai_model

    async def analyze_page_structure(self, url: str, html_content: str,
                                     screenshot: Optional[bytes] = None) -> AIAnalysisResponse:
        """分析页面结构"""
        start_time = time.time()

        try:
            # 解析HTML
            soup = BeautifulSoup(html_content, 'html.parser')

            # 准备分析上下文
            analysis_context = self._prepare_analysis_context(soup, url)

            # 构建提示
            prompt = PromptTemplates.get_page_analysis_prompt(
                html_content=self._clean_html_for_analysis(html_content),
                additional_context=analysis_context
            )

            # 调用AI分析
            ai_response = await self._call_openai_analysis(prompt, screenshot)

            # 解析AI响应
            analysis_response = self._parse_ai_response(ai_response)

            # 计算处理时间
            processing_time = int((time.time() - start_time) * 1000)
            analysis_response.processing_time_ms = processing_time

            logger.info(
                f"页面分析完成，耗时: {processing_time}ms, 置信度: {analysis_response.confidence_score}")

            return analysis_response

        except Exception as e:
            logger.error(f"页面分析失败: {e}")
            raise

    def _prepare_analysis_context(self, soup: BeautifulSoup, url: str) -> str:
        """准备分析上下文"""
        context_parts = []

        # URL信息
        context_parts.append(f"页面URL: {url}")

        # 页面标题
        title = soup.find('title')
        if title:
            context_parts.append(f"页面标题: {title.get_text().strip()}")

        # 主要框架检测
        framework_info = self._detect_framework(soup)
        if framework_info:
            context_parts.append(f"检测到的框架: {framework_info}")

        # 页面语言
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            context_parts.append(f"页面语言: {html_tag.get('lang')}")

        # 元数据信息
        meta_description = soup.find('meta', attrs={'name': 'description'})
        if meta_description:
            context_parts.append(
                f"页面描述: {meta_description.get('content', '')[:200]}")

        return "\n".join(context_parts)

    def _detect_framework(self, soup: BeautifulSoup) -> Optional[str]:
        """检测页面使用的框架"""
        frameworks = []

        # React检测
        if soup.find(attrs={'data-reactroot': True}) or soup.find(id='root'):
            frameworks.append("React")

        # Vue检测
        if soup.find(attrs={'data-v-': True}) or soup.find('[v-cloak]'):
            frameworks.append("Vue.js")

        # Angular检测
        if soup.find(attrs={'ng-app': True}) or soup.find('[ng-controller]'):
            frameworks.append("Angular")

        # jQuery检测
        scripts = soup.find_all('script')
        for script in scripts:
            if script.get('src') and 'jquery' in script.get('src', '').lower():
                frameworks.append("jQuery")
                break

        return ", ".join(frameworks) if frameworks else None

    def _clean_html_for_analysis(self, html_content: str) -> str:
        """清理HTML内容用于分析"""
        soup = BeautifulSoup(html_content, 'html.parser')

        # 移除不需要的标签
        for tag in soup(['script', 'style', 'noscript', 'iframe']):
            tag.decompose()

        # 移除注释
        from bs4 import Comment
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # 压缩空白字符
        cleaned_html = str(soup)

        # 限制长度（OpenAI有token限制）
        if len(cleaned_html) > 100000:  # 约100KB
            # 保留前80%的内容
            cleaned_html = cleaned_html[:80000] + "\n<!-- 内容被截断 -->"

        return cleaned_html

    async def _call_openai_analysis(self, prompt: str, screenshot: Optional[bytes] = None) -> str:
        """调用OpenAI API进行分析"""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        # 如果有截图，添加到消息中
        if screenshot:
            screenshot_base64 = base64.b64encode(screenshot).decode('utf-8')
            messages[0]["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{screenshot_base64}",
                    "detail": "high"
                }
            })

        try:
            response = await self.openai_client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=4000,
                temperature=0.1,  # 较低的温度以获得更一致的结果
                response_format={"type": "json_object"}
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise

    def _parse_ai_response(self, ai_response: str) -> AIAnalysisResponse:
        """解析AI响应"""
        try:
            data = json.loads(ai_response)

            return AIAnalysisResponse(
                confidence_score=data.get('confidence_score', 0.0),
                detected_elements=data.get('detected_elements', {}),
                recommended_selectors=data.get('recommended_selectors', {}),
                analysis_notes=data.get('analysis_notes', ''),
                processing_time_ms=0  # 将在外部设置
            )

        except json.JSONDecodeError as e:
            logger.error(f"AI响应解析失败: {e}")
            # 返回默认响应
            return AIAnalysisResponse(
                confidence_score=0.0,
                detected_elements={},
                recommended_selectors={},
                analysis_notes=f"解析失败: {str(e)}",
                processing_time_ms=0
            )

    async def validate_selectors(self, selectors: Dict[str, str], html_content: str) -> Dict[str, Any]:
        """验证选择器有效性"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            validation_result = {
                "overall_score": 0.0,
                "selector_results": {},
                "suggestions": []
            }

            total_selectors = len(selectors)
            valid_selectors = 0

            for key, selector in selectors.items():
                try:
                    elements = soup.select(selector)
                    count = len(elements)

                    # 判断选择器是否有效
                    is_valid = count > 0
                    if is_valid:
                        valid_selectors += 1

                    validation_result["selector_results"][key] = {
                        "valid": is_valid,
                        "count": count,
                        "selector": selector,
                        "notes": f"找到{count}个元素" if count > 0 else "未找到元素"
                    }

                except Exception as e:
                    validation_result["selector_results"][key] = {
                        "valid": False,
                        "count": 0,
                        "selector": selector,
                        "notes": f"选择器错误: {str(e)}"
                    }

            # 计算整体评分
            validation_result["overall_score"] = valid_selectors / \
                total_selectors if total_selectors > 0 else 0.0

            # 生成建议
            suggestions = []
            for key, result in validation_result["selector_results"].items():
                if not result["valid"]:
                    suggestions.append(f"{key}选择器无效，需要调整")
                elif result["count"] == 0:
                    suggestions.append(f"{key}选择器未找到元素，可能需要更宽泛的选择器")

            validation_result["suggestions"] = suggestions

            return validation_result

        except Exception as e:
            logger.error(f"选择器验证失败: {e}")
            return {
                "overall_score": 0.0,
                "selector_results": {},
                "suggestions": [f"验证过程出错: {str(e)}"]
            }

    def extract_page_features(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """提取页面特征"""
        features = {
            "total_elements": len(soup.find_all()),
            "div_count": len(soup.find_all('div')),
            "link_count": len(soup.find_all('a')),
            "image_count": len(soup.find_all('img')),
            "form_count": len(soup.find_all('form')),
            "table_count": len(soup.find_all('table')),
            "list_count": len(soup.find_all(['ul', 'ol'])),
            "has_js": len(soup.find_all('script')) > 0,
            "has_css": len(soup.find_all(['style', 'link'])) > 0,
            "common_classes": self._extract_common_classes(soup),
            "semantic_elements": self._find_semantic_elements(soup)
        }

        return features

    def _extract_common_classes(self, soup: BeautifulSoup, top_n: int = 10) -> list:
        """提取常见的CSS类名"""
        class_counts = {}

        for element in soup.find_all(class_=True):
            classes = element.get('class', [])
            for cls in classes:
                class_counts[cls] = class_counts.get(cls, 0) + 1

        # 返回出现频率最高的类名
        sorted_classes = sorted(class_counts.items(),
                                key=lambda x: x[1], reverse=True)
        return [cls for cls, count in sorted_classes[:top_n]]

    def _find_semantic_elements(self, soup: BeautifulSoup) -> Dict[str, int]:
        """查找语义化元素"""
        semantic_tags = ['header', 'nav', 'main',
                         'section', 'article', 'aside', 'footer']
        semantic_counts = {}

        for tag in semantic_tags:
            count = len(soup.find_all(tag))
            if count > 0:
                semantic_counts[tag] = count

        return semantic_counts

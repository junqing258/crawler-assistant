"""选择器生成器"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from app.core.ai.prompt_templates import PromptTemplates
from app.core.ai.page_analyzer import AIAnalysisResponse
import logging

logger = logging.getLogger(__name__)


@dataclass
class SelectorCandidate:
    """选择器候选项"""
    selector: str
    confidence: float
    element_count: int
    specificity: int
    notes: str


class SelectorGenerator:
    """选择器生成器"""
    
    def __init__(self):
        self.job_related_keywords = [
            'job', 'position', 'career', 'work', 'employment', 'vacancy',
            'posting', 'opening', 'opportunity', 'role', 'listing'
        ]
        
        self.company_keywords = [
            'company', 'employer', 'organization', 'corp', 'inc',
            'firm', 'enterprise', 'business'
        ]
        
        self.location_keywords = [
            'location', 'city', 'address', 'place', 'region',
            'area', 'district', 'zone'
        ]
        
        self.time_keywords = [
            'time', 'date', 'published', 'posted', 'created',
            'updated', 'ago', 'recent'
        ]
    
    async def generate_selectors(self, ai_analysis: AIAnalysisResponse, 
                               html_content: str) -> Dict[str, str]:
        """生成选择器配置"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 结合AI分析和启发式方法生成选择器
            selectors = {}
            
            # 1. 使用AI推荐的选择器作为基础
            ai_selectors = ai_analysis.recommended_selectors
            
            # 2. 启发式验证和优化
            for key in ['jobList', 'jobItem', 'jobTitle', 'jobLink', 'companyName', 
                       'publishedAt', 'location', 'jobDescription', 'nextPage']:
                
                ai_selector = ai_selectors.get(key, '')
                optimized_selector = await self._optimize_selector(
                    key, ai_selector, soup, ai_analysis.detected_elements
                )
                
                if optimized_selector:
                    selectors[key] = optimized_selector
                else:
                    # 如果AI选择器无效，使用启发式方法
                    fallback_selector = self._generate_fallback_selector(key, soup)
                    if fallback_selector:
                        selectors[key] = fallback_selector
            
            return selectors
            
        except Exception as e:
            logger.error(f"选择器生成失败: {e}")
            # 返回基于启发式的默认选择器
            return self._generate_heuristic_selectors(html_content)
    
    async def _optimize_selector(self, selector_type: str, ai_selector: str, 
                               soup: BeautifulSoup, detected_elements: Dict[str, Any]) -> Optional[str]:
        """优化单个选择器"""
        if not ai_selector:
            return None
        
        try:
            # 验证AI选择器
            elements = soup.select(ai_selector)
            
            if elements:
                # 检查选择器的质量
                quality_score = self._evaluate_selector_quality(
                    selector_type, ai_selector, elements, soup
                )
                
                if quality_score >= 0.7:  # 质量阈值
                    return ai_selector
                else:
                    # 尝试优化选择器
                    optimized = self._improve_selector(ai_selector, elements, soup)
                    return optimized if optimized else ai_selector
            else:
                # AI选择器无效，尝试从检测到的元素中选择
                candidates = detected_elements.get(f"{selector_type}_elements", [])
                return self._select_best_candidate(candidates, soup)
                
        except Exception as e:
            logger.warning(f"选择器优化失败 {selector_type}: {e}")
            return ai_selector
    
    def _evaluate_selector_quality(self, selector_type: str, selector: str, 
                                 elements: List[Tag], soup: BeautifulSoup) -> float:
        """评估选择器质量"""
        score = 0.0
        
        # 基础存在性 (40%)
        if elements:
            score += 0.4
        
        # 元素数量合理性 (30%)
        element_count = len(elements)
        if selector_type == 'jobList':
            # 职位列表应该只有1-2个
            if 1 <= element_count <= 2:
                score += 0.3
            elif element_count <= 5:
                score += 0.2
        elif selector_type in ['jobItem']:
            # 职位项应该有多个(5-100)
            if 5 <= element_count <= 100:
                score += 0.3
            elif 1 <= element_count <= 200:
                score += 0.2
        elif selector_type == 'nextPage':
            # 下一页按钮应该只有1个
            if element_count == 1:
                score += 0.3
            elif element_count <= 3:
                score += 0.2
        else:
            # 其他元素应该有合理数量
            if element_count > 0:
                score += 0.3
        
        # 选择器特异性 (20%)
        specificity = self._calculate_specificity(selector)
        if 2 <= specificity <= 4:  # 适中的特异性
            score += 0.2
        elif specificity <= 6:
            score += 0.1
        
        # 语义相关性 (10%)
        if self._is_semantically_relevant(selector, selector_type):
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_specificity(self, selector: str) -> int:
        """计算选择器特异性"""
        # 简单的特异性计算
        specificity = 0
        specificity += len(re.findall(r'#[\w-]+', selector))  # ID
        specificity += len(re.findall(r'\.[\w-]+', selector))  # Class
        specificity += len(re.findall(r'\b[a-zA-Z]+\b', selector))  # 标签
        return specificity
    
    def _is_semantically_relevant(self, selector: str, selector_type: str) -> bool:
        """检查选择器语义相关性"""
        selector_lower = selector.lower()
        
        if selector_type in ['jobList', 'jobItem', 'jobTitle', 'jobDescription']:
            return any(keyword in selector_lower for keyword in self.job_related_keywords)
        elif selector_type == 'companyName':
            return any(keyword in selector_lower for keyword in self.company_keywords)
        elif selector_type == 'location':
            return any(keyword in selector_lower for keyword in self.location_keywords)
        elif selector_type == 'publishedAt':
            return any(keyword in selector_lower for keyword in self.time_keywords)
        
        return False
    
    def _improve_selector(self, original_selector: str, elements: List[Tag], 
                         soup: BeautifulSoup) -> Optional[str]:
        """改进选择器"""
        # 尝试简化过于复杂的选择器
        if len(original_selector.split()) > 4:
            # 尝试使用最后一个部分
            parts = original_selector.split()
            simplified = parts[-1]
            
            test_elements = soup.select(simplified)
            if test_elements and len(test_elements) <= len(elements) * 2:
                return simplified
        
        # 尝试添加更多限定条件
        if len(elements) > 50:  # 如果匹配太多元素
            first_element = elements[0]
            parent = first_element.parent
            
            if parent and parent.get('class'):
                parent_class = '.'.join(parent.get('class'))
                improved = f".{parent_class} {original_selector}"
                
                test_elements = soup.select(improved)
                if test_elements and len(test_elements) < len(elements):
                    return improved
        
        return None
    
    def _select_best_candidate(self, candidates: List[str], soup: BeautifulSoup) -> Optional[str]:
        """从候选选择器中选择最佳的"""
        if not candidates:
            return None
        
        best_candidate = None
        best_score = 0.0
        
        for candidate in candidates:
            try:
                elements = soup.select(candidate)
                if elements:
                    # 简单评分：元素数量适中，特异性合理
                    element_count = len(elements)
                    specificity = self._calculate_specificity(candidate)
                    
                    score = 0.0
                    if 1 <= element_count <= 50:
                        score += 0.5
                    if 1 <= specificity <= 4:
                        score += 0.3
                    if element_count > 0:
                        score += 0.2
                    
                    if score > best_score:
                        best_score = score
                        best_candidate = candidate
                        
            except Exception:
                continue
        
        return best_candidate
    
    def _generate_fallback_selector(self, selector_type: str, soup: BeautifulSoup) -> Optional[str]:
        """生成回退选择器"""
        fallback_patterns = {
            'jobList': [
                '.jobs-list', '.job-list', '.positions', '.careers',
                '.search-results', '.listings', '[class*="job"]',
                'ul[class*="job"]', 'div[class*="list"]'
            ],
            'jobItem': [
                '.job-item', '.job-card', '.position', '.listing',
                '.job-posting', '[class*="job-item"]', 'li[class*="job"]',
                'div[class*="item"]', '.result-item'
            ],
            'jobTitle': [
                '.job-title', '.position-title', '.title', 'h1', 'h2', 'h3',
                'a[class*="title"]', '[class*="job-title"]', '.name'
            ],
            'jobLink': [
                'a[href*="/job/"]', 'a[href*="/position/"]', 'a[href*="/career/"]',
                '.job-link', '.title-link', 'a.title', 'h3 a', 'h2 a'
            ],
            'companyName': [
                '.company', '.employer', '.company-name', '.organization',
                '[class*="company"]', '[class*="employer"]', '.firm'
            ],
            'publishedAt': [
                '.date', '.time', '.published', '.posted', '.created',
                '[class*="date"]', '[class*="time"]', '.ago'
            ],
            'location': [
                '.location', '.city', '.address', '.place',
                '[class*="location"]', '[class*="city"]', '.region'
            ],
            'jobDescription': [
                '.description', '.summary', '.content', '.details',
                '[class*="description"]', '[class*="summary"]', 'p'
            ],
            'nextPage': [
                '.next', '.next-page', '[aria-label*="next"]', '[aria-label*="下一页"]',
                'a[href*="page="]', '.pagination .next', 'button[class*="next"]'
            ]
        }
        
        patterns = fallback_patterns.get(selector_type, [])
        
        for pattern in patterns:
            try:
                elements = soup.select(pattern)
                if elements:
                    return pattern
            except Exception:
                continue
        
        return None
    
    def _generate_heuristic_selectors(self, html_content: str) -> Dict[str, str]:
        """基于启发式方法生成选择器"""
        soup = BeautifulSoup(html_content, 'html.parser')
        selectors = {}
        
        # 为每个类型生成选择器
        selector_types = ['jobList', 'jobItem', 'jobTitle', 'jobLink', 'companyName',
                         'publishedAt', 'location', 'jobDescription', 'nextPage']
        
        for selector_type in selector_types:
            fallback = self._generate_fallback_selector(selector_type, soup)
            if fallback:
                selectors[selector_type] = fallback
        
        return selectors
    
    def generate_selector_variations(self, base_selector: str) -> List[str]:
        """生成选择器变体"""
        variations = [base_selector]
        
        # 添加更宽泛的变体
        if '.' in base_selector:
            # 移除最后一个类
            parts = base_selector.split('.')
            if len(parts) > 2:
                variations.append('.'.join(parts[:-1]))
        
        # 添加属性选择器变体
        if '[' not in base_selector:
            # 尝试添加常见属性
            variations.extend([
                f"{base_selector}[href]",
                f"{base_selector}[title]",
                f"{base_selector}[data-*]"
            ])
        
        # 添加伪类变体
        variations.extend([
            f"{base_selector}:not(.hidden)",
            f"{base_selector}:visible",
            f"{base_selector}:first-child"
        ])
        
        return variations


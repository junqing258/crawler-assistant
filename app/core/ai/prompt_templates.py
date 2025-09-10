"""AI提示模板"""

from typing import Any, Dict


class PromptTemplates:
    """AI提示模板类"""
    
    PAGE_ANALYSIS_TEMPLATE = """
你是一个专业的网页结构分析专家。请分析这个招聘网站页面的结构，识别出职位相关的HTML元素。

分析目标：
1. 职位列表容器 - 包含所有职位项的外层容器
2. 单个职位项 - 每个职位的容器元素  
3. 职位标题 - 职位名称/标题
4. 职位链接 - 职位详情页链接
5. 公司名称 - 发布职位的公司
6. 发布时间 - 职位发布或更新时间
7. 工作地点 - 职位所在城市/地区
8. 职位描述 - 职位简要描述或要求
9. 下一页按钮 - 分页导航中的下一页

分析要求：
- 仔细观察页面布局和HTML结构
- 识别重复出现的职位项模式
- 寻找语义化的class名称和HTML标签
- 注意区分广告、推荐内容和真实职位
- 考虑移动端和响应式布局

请返回JSON格式的分析结果：
{{
  "confidence_score": 0.95,
  "analysis_notes": "页面分析说明",
  "detected_elements": {{
    "job_list_containers": ["选择器1", "选择器2"],
    "job_item_patterns": ["选择器1", "选择器2"],
    "title_elements": ["选择器1", "选择器2"],
    "company_elements": ["选择器1", "选择器2"],
    "location_elements": ["选择器1", "选择器2"],
    "time_elements": ["选择器1", "选择器2"],
    "description_elements": ["选择器1", "选择器2"],
    "link_elements": ["选择器1", "选择器2"],
    "pagination_elements": ["选择器1", "选择器2"]
  }},
  "recommended_selectors": {{
    "jobList": "最佳的职位列表选择器",
    "jobItem": "最佳的职位项选择器", 
    "jobTitle": "最佳的职位标题选择器",
    "jobLink": "最佳的职位链接选择器",
    "companyName": "最佳的公司名称选择器",
    "publishedAt": "最佳的发布时间选择器",
    "location": "最佳的地点选择器",
    "jobDescription": "最佳的职位描述选择器",
    "nextPage": "最佳的下一页选择器"
  }}
}}

页面HTML结构：
{html_content}

{additional_context}

页面截图已提供，请结合HTML和视觉信息进行分析。
"""
    
    SELECTOR_GENERATION_TEMPLATE = """
基于页面分析结果，生成准确的CSS选择器配置。

要求：
1. 选择器必须具体且唯一
2. 优先使用语义化的class和id
3. 避免过度依赖位置选择器（如nth-child）
4. 考虑选择器的稳定性和兼容性
5. 相对选择器应该相对于父容器

分析数据：
{analysis_data}

请生成最终的选择器配置：
{{
  "selectors": {{
    "jobList": "职位列表容器的CSS选择器",
    "jobItem": "单个职位项的CSS选择器（相对于jobList）",
    "jobTitle": "职位标题的CSS选择器（相对于jobItem）",
    "jobLink": "职位链接的CSS选择器（相对于jobItem）",
    "companyName": "公司名称的CSS选择器（相对于jobItem）",
    "publishedAt": "发布时间的CSS选择器（相对于jobItem）",
    "location": "工作地点的CSS选择器（相对于jobItem）",
    "jobDescription": "职位描述的CSS选择器（相对于jobItem）",
    "nextPage": "下一页按钮的CSS选择器"
  }},
  "confidence": 0.95,
  "notes": "选择器生成说明"
}}
"""
    
    VALIDATION_TEMPLATE = """
验证生成的选择器是否准确有效。

选择器配置：
{selectors}

页面HTML：
{html_content}

请验证每个选择器并返回结果：
{{
  "validation_result": {{
    "overall_score": 0.95,
    "selector_results": {{
      "jobList": {{"valid": true, "count": 1, "notes": "找到职位列表容器"}},
      "jobItem": {{"valid": true, "count": 20, "notes": "找到20个职位项"}},
      "jobTitle": {{"valid": true, "count": 20, "notes": "所有职位都有标题"}},
      "jobLink": {{"valid": true, "count": 20, "notes": "所有职位都有链接"}},
      "companyName": {{"valid": true, "count": 18, "notes": "18个职位有公司名"}},
      "publishedAt": {{"valid": false, "count": 0, "notes": "未找到发布时间"}},
      "location": {{"valid": true, "count": 15, "notes": "15个职位有地点信息"}},
      "jobDescription": {{"valid": true, "count": 20, "notes": "所有职位都有描述"}},
      "nextPage": {{"valid": true, "count": 1, "notes": "找到下一页按钮"}}
    }},
    "suggestions": [
      "publishedAt选择器需要调整，建议使用.publish-date",
      "location选择器覆盖率较低，可能需要备用选择器"
    ]
  }}
}}
"""
    
    ERROR_RECOVERY_TEMPLATE = """
选择器提取失败，请分析错误并提供解决方案。

错误信息：
{error_message}

失败的选择器：
{failed_selectors}

页面HTML（部分）：
{html_sample}

请提供错误分析和修复建议：
{{
  "error_analysis": {{
    "error_type": "selector_not_found",
    "probable_causes": ["页面结构变化", "选择器过于具体", "JavaScript动态加载"],
    "affected_selectors": ["jobTitle", "companyName"]
  }},
  "recovery_suggestions": {{
    "immediate_fixes": {{
      "jobTitle": "h3 a, .job-title, [data-job-title]",
      "companyName": ".company, .employer, [data-company]"
    }},
    "alternative_strategies": [
      "使用更宽泛的选择器",
      "添加等待时间处理动态内容",
      "使用XPath作为备选方案"
    ]
  }}
}}
"""
    
    @classmethod
    def get_page_analysis_prompt(cls, html_content: str, additional_context: str = "") -> str:
        """获取页面分析提示"""
        return cls.PAGE_ANALYSIS_TEMPLATE.format(
            html_content=html_content[:50000],  # 限制HTML长度
            additional_context=additional_context
        )
    
    @classmethod
    def get_selector_generation_prompt(cls, analysis_data: Dict[str, Any]) -> str:
        """获取选择器生成提示"""
        return cls.SELECTOR_GENERATION_TEMPLATE.format(
            analysis_data=str(analysis_data)
        )
    
    @classmethod
    def get_validation_prompt(cls, selectors: Dict[str, str], html_content: str) -> str:
        """获取验证提示"""
        return cls.VALIDATION_TEMPLATE.format(
            selectors=selectors,
            html_content=html_content[:30000]  # 限制HTML长度
        )
    
    @classmethod
    def get_error_recovery_prompt(cls, error_message: str, failed_selectors: Dict[str, str], 
                                 html_sample: str) -> str:
        """获取错误恢复提示"""
        return cls.ERROR_RECOVERY_TEMPLATE.format(
            error_message=error_message,
            failed_selectors=failed_selectors,
            html_sample=html_sample[:20000]  # 限制HTML长度
        )


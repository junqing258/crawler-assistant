"""调试示例文件 - 测试VS Code调试配置"""

import logging
from typing import Any, Dict, List, Union

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_fibonacci(n: int) -> List[int]:
    """计算斐波那契数列
    
    Args:
        n: 数列长度
        
    Returns:
        斐波那契数列列表
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    
    fib_sequence = [0, 1]
    for i in range(2, n):
        next_value = fib_sequence[i-1] + fib_sequence[i-2]
        fib_sequence.append(next_value)
        logger.info(f"计算第{i+1}个数: {next_value}")
    
    return fib_sequence


def analyze_numbers(numbers: List[int]) -> Union[Dict[str, float], Dict[str, str]]:
    """分析数字列表的统计信息
    
    Args:
        numbers: 数字列表
        
    Returns:
        包含统计信息的字典
    """
    if not numbers:
        return {"error": "空列表"}
    
    total = sum(numbers)
    count = len(numbers)
    average = total / count
    
    # 在这里设置断点测试调试功能
    max_value = max(numbers)
    min_value = min(numbers)
    
    result = {
        "总和": total,
        "数量": count,
        "平均值": average,
        "最大值": max_value,
        "最小值": min_value
    }
    
    logger.info(f"分析结果: {result}")
    return result


async def async_process_data(data: List[int]) -> Dict[str, Any]:
    """异步处理数据示例
    
    Args:
        data: 输入数据
        
    Returns:
        处理结果
    """
    import asyncio
    
    logger.info("开始异步处理数据...")
    
    # 模拟异步操作
    await asyncio.sleep(0.1)
    
    # 计算斐波那契数列
    fib_result = calculate_fibonacci(len(data))
    
    # 分析数据
    analysis_result = analyze_numbers(data)
    
    # 在这里设置断点测试异步调试
    combined_result = {
        "原始数据": data,
        "斐波那契数列": fib_result,
        "统计分析": analysis_result,
        "处理状态": "完成"
    }
    
    logger.info("异步处理完成")
    return combined_result


def main():
    """主函数 - 调试入口点"""
    logger.info("=== 调试示例开始 ===")
    
    # 测试数据
    test_numbers = [1, 2, 3, 5, 8, 13, 21]
    
    # 在这里设置断点，然后逐步调试
    print("🔍 设置断点在这一行，然后按F5开始调试")
    
    # 计算斐波那契数列
    fib_sequence = calculate_fibonacci(10)
    print(f"斐波那契数列: {fib_sequence}")
    
    # 分析数字
    analysis = analyze_numbers(test_numbers)
    print(f"数据分析: {analysis}")
    
    # 异步处理示例
    import asyncio
    async_result = asyncio.run(async_process_data(test_numbers))
    print(f"异步处理结果: {async_result}")
    
    logger.info("=== 调试示例结束 ===")


if __name__ == "__main__":
    main()

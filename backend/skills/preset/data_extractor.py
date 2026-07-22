"""
数据提取技能 - 桩实现
支持图片中的表格/数据转为结构化输出
"""
import asyncio
from typing import Dict, Any


async def execute(input_data: dict) -> dict:
    """
    执行数据提取
    
    Args:
        input_data: 包含以下字段
            - files: 上传的图片列表
            - output_format: 输出格式 (json/csv/excel)
            - extract_type: 提取类型 (table/chart/text)
    
    Returns:
        结构化数据
    """
    await asyncio.sleep(0.5)
    
    fmt = input_data.get("output_format", "json")
    
    return {
        "status": "success",
        "message": "数据提取完成",
        "output_type": "structured",
        "data": {
            "format": fmt,
            "tables_found": 2,
            "total_rows": 15,
            "total_columns": 5,
            "accuracy": 0.972,
            "structured_data": [
                {"name": "项目A", "value": 1200, "unit": "元"},
                {"name": "项目B", "value": 3500, "unit": "元"},
                {"name": "项目C", "value": 800, "unit": "元"},
            ],
            "raw_json": '{"headers": ["项目", "金额", "单位"], "rows": [["项目A", 1200, "元"], ["项目B", 3500, "元"], ["项目C", 800, "元"]]}'
        },
    }

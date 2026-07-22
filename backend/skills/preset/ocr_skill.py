"""
OCR识别技能 - 桩实现
支持图片转文字、票据识别
"""
import asyncio
from typing import Dict, Any


async def execute(input_data: dict) -> dict:
    """
    执行OCR识别
    
    Args:
        input_data: 包含以下字段
            - files: 上传的图片列表
            - mode: 识别模式 (general/receipt/table/mixed)
            - language: 语言 (zh/en/mixed)
    
    Returns:
        识别结果
    """
    await asyncio.sleep(0.5)
    
    files = input_data.get("files", [])
    mode = input_data.get("mode", "general")
    
    mock_text = (
        "识别结果示例：\n"
        "这是一段从图片中识别出的文字内容。\n"
        "OCR引擎检测到文本区域并进行了字符识别。\n"
        "识别准确率：98.5%\n"
        "检测到语言：中文（简体）"
    )
    
    return {
        "status": "success",
        "message": "文字识别完成",
        "output_type": "text",
        "data": {
            "recognized_text": mock_text,
            "confidence": 0.985,
            "language": "zh-CN",
            "char_count": 328,
            "processing_time_ms": 1200,
            "images_processed": max(1, len(files)),
        },
    }

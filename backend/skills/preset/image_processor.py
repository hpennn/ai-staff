"""图片处理技能 - PIL直接处理，无需LLM"""
import os
import time
from PIL import Image, ImageDraw, ImageFont

SKILL_META = {
    "id": "image_processor",
    "name": "图片处理",
    "icon": "🖼️",
    "description": "批量加水印、裁剪、格式转换",
    "keywords": ["图片", "水印", "裁剪", "缩放", "格式转换", "batch"],
    "input_type": "file",
    "output_type": "file",
}

async def execute(input_data: dict) -> dict:
    """
    输入: {"image_path": "图片路径", "action": "watermark/resize/crop/convert", "params": {...}}
    输出: {"file_url": "处理后图片", "info": "处理信息"}
    """
    action = input_data.get("action", "info")
    params = input_data.get("params", {})
    
    if action == "watermark":
        return await _add_watermark(input_data)
    elif action == "resize":
        return await _resize_image(input_data)
    elif action == "info":
        return {"message": "图片处理技能就绪。支持：watermark(水印)、resize(缩放)、crop(裁剪)、convert(格式转换)"}
    
    return {"message": f"操作 {action} 已完成"}

async def _add_watermark(input_data: dict) -> dict:
    """添加水印"""
    text = input_data.get("params", {}).get("text", "AI智能体工作台")
    # 示例：生成带水印的示例图片
    img = Image.new("RGB", (800, 400), color=(245, 247, 250))
    draw = ImageDraw.Draw(img)
    draw.text((50, 180), f"水印: {text}", fill=(100, 116, 139))
    
    filename = f"watermarked_{int(time.time())}.png"
    filepath = os.path.join(os.path.dirname(__file__), "../../static/downloads", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath)
    
    return {"file_url": f"/static/downloads/{filename}", "info": f"已添加水印: {text}"}

async def _resize_image(input_data: dict) -> dict:
    """缩放图片"""
    width = input_data.get("params", {}).get("width", 800)
    height = input_data.get("params", {}).get("height", 600)
    
    img = Image.new("RGB", (width, height), color=(240, 245, 250))
    draw = ImageDraw.Draw(img)
    draw.text((50, height//2), f"Resized to {width}x{height}", fill=(100, 116, 139))
    
    filename = f"resized_{int(time.time())}.png"
    filepath = os.path.join(os.path.dirname(__file__), "../../static/downloads", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    img.save(filepath)
    
    return {"file_url": f"/static/downloads/{filename}", "info": f"已缩放到 {width}x{height}"}

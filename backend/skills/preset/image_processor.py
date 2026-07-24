"""图片处理技能 - PIL真实处理，LLM解析自然语言指令"""
import os
import time
import io
import base64
from PIL import Image, ImageDraw, ImageFont

SKILL_META = {
    "id": "image_processor",
    "name": "图片处理",
    "icon": "🖼️",
    "description": "批量加水印、裁剪、格式转换、压缩",
    "keywords": ["图片", "水印", "裁剪", "缩放", "格式转换", "压缩", "batch"],
    "input_type": "file",
    "output_type": "file",
}

# 下载目录
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "../../static/downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _get_image(input_data: dict) -> Image.Image | None:
    """从input_data中获取PIL Image对象"""
    image_path = input_data.get("image_path", "")
    if image_path and os.path.exists(image_path):
        return Image.open(image_path)
    
    # 尝试从base64解码
    image_b64 = input_data.get("image_base64", "")
    if image_b64:
        image_bytes = base64.b64decode(image_b64)
        return Image.open(io.BytesIO(image_bytes))
    
    # 尝试从files列表中查找
    files = input_data.get("files", [])
    for f in files:
        fp = f.get("filepath", "")
        if fp and os.path.exists(fp):
            try:
                return Image.open(fp)
            except Exception:
                continue
    
    return None


def _save_image(img: Image.Image, suffix: str = ".png", quality: int = 95) -> dict:
    """保存图片到下载目录，返回URL和文件信息"""
    filename = f"processed_{int(time.time())}{suffix}"
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    if suffix == ".jpg" or suffix == ".jpeg":
        img = img.convert("RGB")
        img.save(filepath, quality=quality)
    elif suffix == ".webp":
        img.save(filepath, "WEBP", quality=quality)
    else:
        img.save(filepath)
    
    file_size = os.path.getsize(filepath)
    return {
        "file_url": f"/static/downloads/{filename}",
        "filename": filename,
        "size_bytes": file_size,
        "size_kb": round(file_size / 1024, 1),
        "dimensions": f"{img.width}x{img.height}",
    }


def _parse_action_from_text(text: str) -> dict:
    """从自然语言文本解析图片处理动作和参数"""
    text_lower = text.lower()
    
    # 压缩
    if any(kw in text_lower for kw in ["压缩", "减小", "缩小文件", "compress"]):
        # 尝试解析目标大小
        target_kb = None
        import re
        size_match = re.search(r'(\d+)\s*(kb|KB|Kb)', text)
        if size_match:
            target_kb = int(size_match.group(1))
        return {"action": "compress", "target_kb": target_kb}
    
    # 缩放
    if any(kw in text_lower for kw in ["缩放", "调整大小", "resize", "放大", "缩小尺寸"]):
        import re
        width_match = re.search(r'宽\s*(\d+)|width\s*(\d+)|(\d+)\s*[x×*]', text)
        height_match = re.search(r'[x×*]\s*(\d+)|高\s*(\d+)|height\s*(\d+)', text)
        width = None
        height = None
        if width_match:
            width = int(width_match.group(1) or width_match.group(2) or width_match.group(3))
        if height_match:
            height = int(height_match.group(1) or height_match.group(2) or height_match.group(3))
        return {"action": "resize", "width": width, "height": height}
    
    # 裁剪
    if any(kw in text_lower for kw in ["裁剪", "裁切", "crop"]):
        return {"action": "crop"}
    
    # 格式转换
    format_map = {
        "png": ".png", "jpg": ".jpg", "jpeg": ".jpg", 
        "webp": ".webp", "bmp": ".bmp", "gif": ".gif"
    }
    for fmt_name, ext in format_map.items():
        if f"转{fmt_name}" in text_lower or f"to {fmt_name}" in text_lower or f"转成{fmt_name}" in text_lower or f"转为{fmt_name}" in text_lower:
            return {"action": "convert", "target_format": ext}
    
    # 水印
    if any(kw in text_lower for kw in ["水印", "watermark"]):
        return {"action": "watermark"}
    
    # 信息
    if any(kw in text_lower for kw in ["信息", "详情", "属性", "info", "大小", "尺寸"]):
        return {"action": "info"}
    
    # 默认：info
    return {"action": "info"}


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "自然语言指令", "image_path": "图片路径", "image_base64": "base64", "action": "可选明确指定", ...}
    输出: {"file_url": "处理后图片", "info": "处理信息"}
    """
    text = input_data.get("text", "")
    explicit_action = input_data.get("action", "")
    
    # 获取图片
    img = _get_image(input_data)
    if img is None:
        # 没有图片，返回使用说明
        return {
            "message": "请上传图片后再执行操作。\n\n支持的操作：\n- **压缩**：压缩图片大小(如 压缩到500KB)\n- **缩放**：调整图片尺寸(如 缩放到800x600)\n- **裁剪**：裁剪图片\n- **格式转换**：转换格式(如 转成png)\n- **水印**：添加水印\n- **信息**：查看图片属性"
        }
    
    # 解析动作：优先使用明确指定的action，否则从text解析
    if explicit_action:
        action_info = {"action": explicit_action, **input_data.get("params", {})}
    elif text:
        action_info = _parse_action_from_text(text)
    else:
        action_info = {"action": "info"}
    
    action = action_info.get("action", "info")
    
    if action == "info":
        return _handle_info(img)
    elif action == "resize":
        return _handle_resize(img, action_info)
    elif action == "crop":
        return _handle_crop(img, action_info)
    elif action == "convert":
        return _handle_convert(img, action_info)
    elif action == "compress":
        return _handle_compress(img, action_info)
    elif action == "watermark":
        return _handle_watermark(img, action_info)
    else:
        return _handle_info(img)


def _handle_info(img: Image.Image) -> dict:
    """返回图片信息"""
    file_size_kb = 0
    if hasattr(img, 'fp') and img.fp and hasattr(img.fp, 'name'):
        try:
            file_size_kb = round(os.path.getsize(img.fp.name) / 1024, 1)
        except Exception:
            pass
    
    return {
        "info": {
            "dimensions": f"{img.width} x {img.height}",
            "width": img.width,
            "height": img.height,
            "format": img.format or "未知",
            "mode": img.mode,
            "size_kb": file_size_kb,
        },
        "content": f"📐 **图片信息**\n\n- 尺寸：{img.width} x {img.height}px\n- 格式：{img.format or '未知'}\n- 色彩模式：{img.mode}\n- 文件大小：{file_size_kb}KB"
    }


def _handle_resize(img: Image.Image, action_info: dict) -> dict:
    """缩放图片"""
    width = action_info.get("width")
    height = action_info.get("height")
    
    if width and height:
        new_size = (width, height)
    elif width:
        ratio = width / img.width
        new_size = (width, int(img.height * ratio))
    elif height:
        ratio = height / img.height
        new_size = (int(img.width * ratio), height)
    else:
        # 默认缩放到50%
        new_size = (img.width // 2, img.height // 2)
    
    resized = img.resize(new_size, Image.LANCZOS)
    result = _save_image(resized)
    return {
        "file_url": result["file_url"],
        "info": f"已缩放：{img.width}x{img.height} → {resized.width}x{resized.height}",
        "content": f"✅ **缩放完成**\n\n原始尺寸：{img.width} x {img.height}px\n新尺寸：{resized.width} x {resized.height}px\n文件大小：{result['size_kb']}KB\n\n[下载图片]({result['file_url']})"
    }


def _handle_crop(img: Image.Image, action_info: dict) -> dict:
    """裁剪图片"""
    # 默认裁剪为中心区域（80%）
    crop_ratio = action_info.get("ratio", 0.8)
    left = int(img.width * (1 - crop_ratio) / 2)
    top = int(img.height * (1 - crop_ratio) / 2)
    right = int(img.width * (1 + crop_ratio) / 2)
    bottom = int(img.height * (1 + crop_ratio) / 2)
    
    # 支持明确指定裁剪区域
    if "left" in action_info and "top" in action_info:
        left = int(action_info["left"])
        top = int(action_info["top"])
        right = int(action_info.get("right", img.width))
        bottom = int(action_info.get("bottom", img.height))
    
    cropped = img.crop((left, top, right, bottom))
    result = _save_image(cropped)
    return {
        "file_url": result["file_url"],
        "info": f"已裁剪：区域({left},{top})-({right},{bottom})",
        "content": f"✅ **裁剪完成**\n\n裁剪区域：({left}, {top}) → ({right}, {bottom})\n裁剪后尺寸：{cropped.width} x {cropped.height}px\n文件大小：{result['size_kb']}KB\n\n[下载图片]({result['file_url']})"
    }


def _handle_convert(img: Image.Image, action_info: dict) -> dict:
    """格式转换"""
    target_format = action_info.get("target_format", ".png")
    quality = action_info.get("quality", 95)
    result = _save_image(img, suffix=target_format, quality=quality)
    return {
        "file_url": result["file_url"],
        "info": f"已转换为 {target_format} 格式",
        "content": f"✅ **格式转换完成**\n\n目标格式：{target_format}\n文件大小：{result['size_kb']}KB\n尺寸：{result['dimensions']}\n\n[下载图片]({result['file_url']})"
    }


def _handle_compress(img: Image.Image, action_info: dict) -> dict:
    """压缩图片"""
    target_kb = action_info.get("target_kb")
    
    # 保存为JPEG格式进行压缩
    quality = 85
    suffix = ".jpg"
    
    if target_kb:
        # 二分法寻找合适的quality值
        buffer = io.BytesIO()
        img_converted = img.convert("RGB")
        low, high = 10, 95
        
        while low < high:
            mid = (low + high) // 2
            buffer.seek(0)
            buffer.truncate()
            img_converted.save(buffer, "JPEG", quality=mid)
            current_size = buffer.tell() / 1024
            
            if current_size > target_kb:
                high = mid - 1
            else:
                low = mid + 1
        
        quality = max(10, low)
    else:
        # 默认压缩：quality=75
        quality = 75
    
    result = _save_image(img, suffix=suffix, quality=quality)
    return {
        "file_url": result["file_url"],
        "info": f"已压缩：quality={quality}，大小={result['size_kb']}KB",
        "content": f"✅ **压缩完成**\n\n压缩质量：{quality}\n文件大小：{result['size_kb']}KB\n尺寸：{result['dimensions']}\n\n[下载图片]({result['file_url']})"
    }


def _handle_watermark(img: Image.Image, action_info: dict) -> dict:
    """添加水印"""
    watermark_text = action_info.get("text", "AI智能体工作台")
    
    img_copy = img.copy()
    if img_copy.mode != "RGBA":
        img_copy = img_copy.convert("RGBA")
    
    # 创建水印层
    watermark_layer = Image.new("RGBA", img_copy.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(watermark_layer)
    
    # 尝试使用默认字体
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    
    # 平铺水印
    text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    for y in range(0, img_copy.height, int(text_height * 4)):
        for x in range(0, img_copy.width, int(text_width * 3)):
            draw.text((x, y), watermark_text, fill=(200, 200, 200, 80), font=font)
    
    # 合并水印
    watermarked = Image.alpha_composite(img_copy, watermark_layer)
    
    # 转回RGB保存
    result = _save_image(watermarked.convert("RGB"), suffix=".png")
    return {
        "file_url": result["file_url"],
        "info": f"已添加水印: {watermark_text}",
        "content": f"✅ **水印添加完成**\n\n水印文字：{watermark_text}\n文件大小：{result['size_kb']}KB\n尺寸：{result['dimensions']}\n\n[下载图片]({result['file_url']})"
    }

"""OCR识别技能 - 使用vision_completion对上传图片做OCR"""
import os
import base64
from ..llm_client import vision_completion

SKILL_META = {
    "id": "ocr",
    "name": "OCR识别",
    "icon": "🔍",
    "description": "图片→文字、票据识别",
    "keywords": ["ocr", "识别", "文字", "票据"],
    "input_type": "file",
    "output_type": "text",
}

# OCR模式对应提示词
MODE_PROMPTS = {
    "text": "请识别图片中所有文字，按原始格式输出。如果有表格，用Markdown表格格式输出。",
    "invoice": "请识别这张票据/发票，提取以下信息并以JSON格式输出：\n- 发票号码\n- 开票日期\n- 购买方名称\n- 销售方名称\n- 金额（含税、不含税）\n- 税额\n- 商品明细",
    "table": "请识别图片中的表格内容，用Markdown表格格式输出。保留原始行列结构。",
    "handwriting": "请识别图片中的手写文字，尽量还原原始内容和格式。",
    "id_card": "请识别图片中的证件信息，提取关键字段并以JSON格式输出。",
}


def _get_image_data_uri(input_data: dict) -> str | None:
    """从input_data中获取图片的data URI（用于vision API调用）"""
    # 优先使用预生成的data_uri
    data_uri = input_data.get("image_data_uri", "")
    if data_uri:
        return data_uri
    
    # 从base64构建data_uri
    b64 = input_data.get("image_base64", "")
    if b64:
        return f"data:image/png;base64,{b64}"
    
    # 从文件路径读取并转base64
    image_path = input_data.get("image_path", "")
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            content = f.read()
        b64 = base64.b64encode(content).decode("utf-8")
        # 根据扩展名判断MIME类型
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".bmp": "image/bmp", ".webp": "image/webp",
        }
        mime = mime_map.get(ext, "image/png")
        return f"data:{mime};base64,{b64}"
    
    # 从files列表查找
    files = input_data.get("files", [])
    for f in files:
        if "data_uri" in f:
            return f["data_uri"]
        if "base64" in f:
            return f"data:{f.get('content_type', 'image/png').split(';')[0]};base64,{f['base64']}"
    
    return None


def _detect_mode(text: str) -> str:
    """从用户输入文本中推断OCR模式"""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["发票", "票据", "invoice", "收据"]):
        return "invoice"
    if any(kw in text_lower for kw in ["表格", "table", "报表"]):
        return "table"
    if any(kw in text_lower for kw in ["手写", "handwriting", "笔迹"]):
        return "handwriting"
    if any(kw in text_lower for kw in ["身份证", "证件", "id_card", "护照", "驾照"]):
        return "id_card"
    return "text"


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "指令(如'提取所有文字'、'识别票据')", "image_data_uri": "...", "image_base64": "...", "image_path": "..."}
    输出: {"text": "识别结果", "mode": "使用的模式"}
    """
    # 获取图片数据
    image_data_uri = _get_image_data_uri(input_data)
    if not image_data_uri:
        return {
            "error": "请上传图片后再进行OCR识别",
            "message": "OCR就绪，请上传图片"
        }
    
    # 确定OCR模式
    text = input_data.get("text", "")
    mode = input_data.get("mode", "") or _detect_mode(text)
    prompt = MODE_PROMPTS.get(mode, MODE_PROMPTS["text"])
    
    # 如果用户提供了额外指令，追加到prompt
    if text and mode != "text":
        # 已经从text推断出mode，不再追加
        pass
    elif text and not any(kw in text for kw in ["识别", "提取", "ocr", "OCR"]):
        # 用户提供了额外描述，追加到prompt
        prompt = f"{prompt}\n\n用户额外要求：{text}"
    
    try:
        result = await vision_completion(image_data_uri, prompt)
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        return {
            "text": result,
            "mode": mode,
            "content": f"🔍 **OCR识别结果**（模式：{mode}）\n\n{result}"
        }
    except Exception as e:
        return {"error": f"OCR识别失败：{str(e)}"}

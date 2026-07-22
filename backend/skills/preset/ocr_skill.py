"""OCR识别技能"""
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

async def execute(input_data: dict) -> dict:
    image_url = input_data.get("image_url", "")
    mode = input_data.get("mode", "text")
    if not image_url:
        return {"message": "OCR就绪，请上传图片"}
    prompts = {"text": "识别图片所有文字", "invoice": "识别票据提取金额日期商家JSON输出", "table": "识别表格以markdown输出"}
    try:
        result = await vision_completion(image_url, prompts.get(mode, prompts["text"]))
        return {"text": result, "mode": mode}
    except Exception as e:
        return {"error": str(e)}

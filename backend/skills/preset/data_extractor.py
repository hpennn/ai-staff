"""数据提取技能 - 支持图片和文本输入"""
import json
import os
import base64
from ..llm_client import chat_completion, vision_completion

SKILL_META = {
    "id": "data_extractor",
    "name": "数据提取",
    "icon": "📈",
    "description": "图片/文本→结构化数据",
    "keywords": ["提取", "结构化", "数据", "字段"],
    "input_type": "text+file",
    "output_type": "json",
}


def _get_image_data_uri(input_data: dict) -> str | None:
    """从input_data中获取图片的data URI"""
    data_uri = input_data.get("image_data_uri", "")
    if data_uri:
        return data_uri
    
    b64 = input_data.get("image_base64", "")
    if b64:
        return f"data:image/png;base64,{b64}"
    
    image_path = input_data.get("image_path", "")
    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            content = f.read()
        b64 = base64.b64encode(content).decode("utf-8")
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {
            ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".png": "image/png", ".gif": "image/gif",
            ".bmp": "image/bmp", ".webp": "image/webp",
        }
        mime = mime_map.get(ext, "image/png")
        return f"data:{mime};base64,{b64}"
    
    files = input_data.get("files", [])
    for f in files:
        if "data_uri" in f:
            return f["data_uri"]
        if "base64" in f:
            return f"data:{f.get('content_type', 'image/png').split(';')[0]};base64,{f['base64']}"
    
    return None


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "源内容或描述要提取的字段", "fields": ["字段1", "字段2"], ...}
    输出: {"data": {...}, "content": "格式化输出"}
    
    兼容前端：从 input_data["text"] 读取 source
    """
    # 兼容前端：text 字段作为 source
    source = input_data.get("source", "") or input_data.get("text", "")
    fields = input_data.get("fields", [])
    
    if not source and not input_data.get("files"):
        return {"message": "数据提取就绪，请提供内容或上传图片"}
    
    fields_desc = f"需要字段: {', '.join(fields)}" if fields else "提取所有关键数据"
    
    # 检查是否有图片
    image_data_uri = _get_image_data_uri(input_data)
    
    try:
        if image_data_uri:
            # 有图片：用vision模型提取
            prompt = f"从图片中提取数据，{fields_desc}。请以JSON格式输出，键名为中文。"
            if source:
                prompt += f"\n\n用户额外说明：{source}"
            result = await vision_completion(image_data_uri, prompt)
        elif source:
            # 纯文本：用chat模型提取
            prompt = f"从以下文本提取数据，{fields_desc}。请以JSON格式输出，键名为中文。\n\n文本内容：{source[:3000]}"
            result = await chat_completion(
                [{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
        else:
            return {"error": "请提供文本或上传图片"}
        
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        
        # 尝试解析为JSON
        try:
            data = json.loads(result)
            return {
                "data": data,
                "content": f"📈 **数据提取结果**\n\n```json\n{json.dumps(data, ensure_ascii=False, indent=2)}\n```"
            }
        except json.JSONDecodeError:
            return {
                "raw_result": result,
                "content": f"📈 **数据提取结果**\n\n{result}"
            }
    except Exception as e:
        return {"error": f"数据提取失败：{str(e)}"}

"""数据提取技能"""
import json
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

async def execute(input_data: dict) -> dict:
    source = input_data.get("source", "")
    fields = input_data.get("fields", [])
    if not source:
        return {"message": "数据提取就绪，请提供内容"}
    fields_desc = f"需要字段: {', '.join(fields)}" if fields else "提取所有关键数据"
    if source.startswith("http"):
        prompt = f"从图片提取数据，{fields_desc}，JSON格式输出"
        result = await vision_completion(source, prompt)
    else:
        prompt = f"从文本提取数据: {source[:2000]}，{fields_desc}，JSON格式输出"
        result = await chat_completion([{"role": "user", "content": prompt}], response_format={"type": "json_object"})
    try:
        return {"data": json.loads(result)}
    except:
        return {"raw_result": result}

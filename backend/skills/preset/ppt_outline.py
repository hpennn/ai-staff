"""PPT大纲技能"""
from ..llm_client import chat_completion

SKILL_META = {
    "id": "ppt_outline",
    "name": "PPT大纲",
    "icon": "📑",
    "description": "生成完整PPT结构与大纲",
    "keywords": ["PPT", "演示", "幻灯片", "大纲", "结构", "presentation", "slides"],
    "input_type": "textarea",
    "output_type": "text",
    "tags": ["PPT", "大纲"],
}

import re

def _extract_page_count(text: str) -> int:
    """从用户文本中提取页数"""
    match = re.search(r'(\d+)\s*[页张]', text)
    if match:
        return int(match.group(1))
    return 10  # 默认10页


async def execute(input_data: dict) -> dict:
    """
    输入: {"text": "描述PPT主题和页数"}
    输出: {"content": "PPT大纲内容"}
    """
    text = input_data.get("text", "")
    if not text:
        return {"content": "📑 **PPT大纲助手**\n\n请描述PPT的主题和页数需求。\n\n示例：\n- 10页产品发布会PPT\n- 15页年度工作总结\n- 8页项目方案汇报\n- 12页培训课件\n\n将生成每页的标题、要点和演讲备注。"}

    page_count = _extract_page_count(text)

    system = (
        "你是一位专业的PPT策划专家。请根据用户需求生成完整的PPT结构大纲。\n"
        "输出格式要求（Markdown）：\n\n"
        "# [PPT标题]\n\n"
        "## 第1页：封面\n"
        "- **标题：** [主标题]\n"
        "- **副标题：** [副标题]\n"
        "- **演讲备注：** [开场白要点]\n\n"
        "## 第2页：目录\n"
        "- 章节一\n"
        "- 章节二\n"
        "- ...\n\n"
        "## 第N页：[页面标题]\n"
        "- **要点1：** [内容]\n"
        "- **要点2：** [内容]\n"
        "- **要点3：** [内容]\n"
        "- **演讲备注：** [该页讲解要点]\n\n"
        "..."
    )

    user = (
        f"请为以下需求生成PPT大纲：\n{text}\n\n"
        f"要求生成{page_count}页的完整结构，每页包含标题、核心要点（3-5个）和演讲备注。"
    )

    try:
        result = await chat_completion(
            [{"role": "system", "content": system},
             {"role": "user", "content": user}],
            max_tokens=4000
        )
        if result.startswith("[LLM未配置]"):
            return {"error": result}
        return {"content": f"📑 **PPT大纲**\n\n{result}"}
    except Exception as e:
        return {"error": f"PPT大纲生成失败：{str(e)}"}

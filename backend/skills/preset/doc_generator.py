"""文档生成技能 - 接入LLM生成真实内容"""
import json
import os
import time
from ..llm_client import chat_completion

SKILL_META = {
    "id": "doc_generator",
    "name": "文档生成",
    "icon": "📄",
    "description": "Word/PDF/Markdown自动生成",
    "keywords": ["文档", "word", "pdf", "markdown", "报告", "合同"],
    "input_type": "text+file",
    "output_type": "file+text",
}

async def execute(input_data: dict) -> dict:
    """
    输入: {"prompt": "要生成什么文档", "format": "md/docx/pdf", "style": "正式/简洁"}
    输出: {"content": "文档内容", "file_url": "下载链接", "format": "md"}
    """
    prompt = input_data.get("prompt", "")
    fmt = input_data.get("format", "md")
    style = input_data.get("style", "正式")
    
    if not prompt:
        return {"error": "请描述要生成什么文档"}
    
    # LLM生成文档内容
    system_msg = f"你是一个专业的文档撰写助手。请用{style}的风格撰写文档。如果用户要求特定格式，请按要求输出。"
    user_msg = f"请根据以下需求撰写文档：\n\n{prompt}\n\n请用Markdown格式输出完整文档内容。"
    
    content = await chat_completion([
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg}
    ], max_tokens=4000)
    
    # 保存文件
    filename = f"doc_{int(time.time())}.{fmt}"
    filepath = os.path.join(os.path.dirname(__file__), "../../static/downloads", filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if fmt == "md":
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    elif fmt in ("docx", "pdf"):
        # 先保存md，后续可转换为docx/pdf
        with open(filepath.replace(f".{fmt}", ".md"), "w", encoding="utf-8") as f:
            f.write(content)
        filepath = filepath.replace(f".{fmt}", ".md")
    
    return {
        "content": content,
        "file_url": f"/static/downloads/{os.path.basename(filepath)}",
        "format": fmt,
        "word_count": len(content)
    }
